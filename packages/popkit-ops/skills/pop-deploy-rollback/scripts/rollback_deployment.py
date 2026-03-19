#!/usr/bin/env python3
"""
Deployment Rollback Script.

Roll back deployments to previous versions with verification and incident reporting.

Usage:
    python rollback_deployment.py --dir DIR --action ACTION [--target TARGET] [--version VERSION]

Actions:
    assess      - Assess current deployment state and find rollback target
    investigate - Gather diagnostic info about failed deployment
    rollback    - Execute the rollback
    verify      - Verify rollback was successful
    report      - Generate incident report

Output:
    JSON object with rollback results
"""

import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


def _get_plugin_data_dir(project_dir: Path) -> Path:
    """Get plugin data directory (CLAUDE_PLUGIN_DATA or fallback)."""
    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA")
    if plugin_data:
        return Path(plugin_data)
    return project_dir / ".claude" / "popkit"


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


def load_deploy_config(project_dir: Path) -> dict[str, Any]:
    """Load deploy.json from plugin data directory."""
    config_file = _get_plugin_data_dir(project_dir) / "deploy.json"

    if not config_file.exists():
        return {
            "success": False,
            "error": "deploy.json not found. Run /popkit-ops:deploy init first.",
        }

    try:
        config = json.loads(config_file.read_text())
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"Invalid JSON in deploy.json: {e}"}

    return {"success": True, "config": config, "config_path": str(config_file)}


def get_deployment_history(config: dict[str, Any], target: str) -> list[dict[str, Any]]:
    """Get deployment history for a specific target."""
    history = config.get("history", [])
    return [r for r in history if r.get("target") == target]


def get_last_successful(config: dict[str, Any], target: str) -> dict[str, Any] | None:
    """Get the last successful deployment for a target."""
    for record in get_deployment_history(config, target):
        if record.get("status") == "success":
            return record
    return None


def get_last_failed(config: dict[str, Any], target: str) -> dict[str, Any] | None:
    """Get the most recent failed deployment for a target."""
    for record in get_deployment_history(config, target):
        if record.get("status") == "failed":
            return record
    return None


# ---------------------------------------------------------------------------
# Assess
# ---------------------------------------------------------------------------


def assess_situation(
    project_dir: Path, config: dict[str, Any], target: str | None
) -> dict[str, Any]:
    """Assess current deployment state and determine rollback target."""
    targets = config.get("targets", {})

    # Determine target
    if target:
        if target not in targets:
            return {"success": False, "error": f"Target '{target}' not found in config"}
        deploy_target = target
    else:
        # Use primary target
        deploy_target = None
        for name, t in targets.items():
            if t.get("primary", False):
                deploy_target = name
                break
        if not deploy_target:
            for name, t in targets.items():
                if t.get("enabled", False):
                    deploy_target = name
                    break

    if not deploy_target:
        return {"success": False, "error": "No deployment target available"}

    history = get_deployment_history(config, deploy_target)
    last_success = get_last_successful(config, deploy_target)
    last_failed = get_last_failed(config, deploy_target)

    # Determine current state
    current_version = None
    current_status = None
    if history:
        current_version = history[0].get("version")
        current_status = history[0].get("status")

    rollback_target = None
    if last_success:
        # If current is failed, rollback to last success
        if (
            current_status == "failed"
            and last_success.get("version") != current_version
        ):
            rollback_target = last_success
        # If current is success, find the one before
        elif current_status == "success" and len(history) > 1:
            for record in history[1:]:
                if record.get("status") == "success":
                    rollback_target = record
                    break

    return {
        "success": True,
        "target": deploy_target,
        "current_version": current_version,
        "current_status": current_status,
        "rollback_version": rollback_target.get("version") if rollback_target else None,
        "rollback_commit": rollback_target.get("commit_sha")
        if rollback_target
        else None,
        "rollback_timestamp": rollback_target.get("timestamp")
        if rollback_target
        else None,
        "total_deployments": len(history),
        "last_failed": {
            "version": last_failed.get("version"),
            "timestamp": last_failed.get("timestamp"),
            "error": last_failed.get("error"),
        }
        if last_failed
        else None,
        "can_rollback": rollback_target is not None,
    }


# ---------------------------------------------------------------------------
# Investigate
# ---------------------------------------------------------------------------


def investigate_failure(
    project_dir: Path, config: dict[str, Any], target: str
) -> dict[str, Any]:
    """Gather diagnostic information about a failed deployment."""
    diagnostics = []

    # Check deployment history for error details
    last_failed = get_last_failed(config, target)
    if last_failed:
        diagnostics.append(
            {
                "source": "deployment_history",
                "data": {
                    "version": last_failed.get("version"),
                    "timestamp": last_failed.get("timestamp"),
                    "error": last_failed.get("error"),
                    "duration_ms": last_failed.get("duration_ms"),
                },
            }
        )

    # Check git log for recent changes
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "-10"],
            capture_output=True,
            text=True,
            cwd=str(project_dir),
            timeout=10,
        )
        if result.returncode == 0:
            diagnostics.append(
                {
                    "source": "git_log",
                    "data": {"recent_commits": result.stdout.strip().splitlines()},
                }
            )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass  # Git unavailable; skip git log diagnostics

    # Check Docker logs if docker target
    if target == "docker":
        target_config = config.get("targets", {}).get("docker", {}).get("config", {})
        image_name = target_config.get("image_name", "app")
        try:
            result = subprocess.run(
                ["docker", "logs", "--tail", "50", image_name],
                capture_output=True,
                text=True,
                cwd=str(project_dir),
                timeout=15,
            )
            if result.returncode == 0:
                diagnostics.append(
                    {
                        "source": "docker_logs",
                        "data": {"logs": result.stdout.strip()[-2000:]},
                    }
                )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass  # Docker unavailable; skip container log diagnostics

    return {
        "success": True,
        "target": target,
        "diagnostics": diagnostics,
        "diagnostic_count": len(diagnostics),
    }


# ---------------------------------------------------------------------------
# Rollback execution
# ---------------------------------------------------------------------------


def execute_docker_rollback(
    project_dir: Path,
    config: dict[str, Any],
    target_config: dict[str, Any],
    rollback_version: str,
    dry_run: bool,
) -> dict[str, Any]:
    """Execute Docker rollback."""
    docker_config = target_config.get("config", {})
    image_name = docker_config.get("image_name", config.get("project_name", "app"))
    registry = docker_config.get("registry", "ghcr.io")
    full_image = f"{registry}/{image_name}:{rollback_version}"

    steps = [
        {
            "step": "pull_previous",
            "command": f"docker pull {full_image}",
            "description": f"Pull previous image {full_image}",
        },
        {
            "step": "stop_current",
            "command": "docker compose down",
            "description": "Stop current deployment",
        },
        {
            "step": "start_previous",
            "command": "docker compose up -d",
            "description": f"Start rollback version {rollback_version}",
        },
    ]

    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "steps": steps,
            "message": f"Would roll back to {full_image}",
        }

    executed_steps = []
    for step in steps:
        step_start = time.time()
        try:
            result = subprocess.run(
                step["command"].split(),
                capture_output=True,
                text=True,
                cwd=str(project_dir),
                timeout=300,
            )
            duration = time.time() - step_start
            executed_steps.append(
                {
                    **step,
                    "status": "success" if result.returncode == 0 else "failed",
                    "duration_s": round(duration, 1),
                    "exit_code": result.returncode,
                    "stderr": result.stderr[:500] if result.returncode != 0 else None,
                }
            )
            if result.returncode != 0:
                return {
                    "success": False,
                    "dry_run": False,
                    "steps": executed_steps,
                    "error": f"Rollback step '{step['step']}' failed: {result.stderr[:200]}",
                }
        except subprocess.TimeoutExpired:
            executed_steps.append({**step, "status": "timeout", "duration_s": 300})
            return {
                "success": False,
                "dry_run": False,
                "steps": executed_steps,
                "error": f"Rollback step '{step['step']}' timed out",
            }
        except FileNotFoundError:
            executed_steps.append(
                {**step, "status": "failed", "error": "Command not found"}
            )
            return {
                "success": False,
                "dry_run": False,
                "steps": executed_steps,
                "error": "Docker not installed or not in PATH",
            }

    return {
        "success": True,
        "dry_run": False,
        "steps": executed_steps,
        "image": full_image,
    }


def execute_npm_rollback(
    project_dir: Path,
    config: dict[str, Any],
    target_config: dict[str, Any],
    rollback_version: str,
    dry_run: bool,
) -> dict[str, Any]:
    """Execute npm rollback (deprecate and re-tag)."""
    npm_config = target_config.get("config", {})
    pkg_json = project_dir / "package.json"
    pkg_name = ""

    if pkg_json.exists():
        try:
            pkg = json.loads(pkg_json.read_text())
            pkg_name = pkg.get("name", "")
        except (json.JSONDecodeError, OSError):
            pass  # Corrupt package.json; proceed with empty pkg name

    tag = npm_config.get("tag", "latest")

    steps = [
        {
            "step": "retag",
            "command": f"npm dist-tag add {pkg_name}@{rollback_version} {tag}",
            "description": f"Point {tag} tag to {rollback_version}",
        },
    ]

    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "steps": steps,
            "message": f"Would point {tag} to {pkg_name}@{rollback_version}",
        }

    executed_steps = []
    for step in steps:
        try:
            result = subprocess.run(
                step["command"].split(),
                capture_output=True,
                text=True,
                cwd=str(project_dir),
                timeout=60,
            )
            executed_steps.append(
                {
                    **step,
                    "status": "success" if result.returncode == 0 else "failed",
                    "exit_code": result.returncode,
                    "stderr": result.stderr[:500] if result.returncode != 0 else None,
                }
            )
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            executed_steps.append({**step, "status": "failed", "error": str(e)})

    success = all(s.get("status") == "success" for s in executed_steps)
    return {
        "success": success,
        "dry_run": False,
        "steps": executed_steps,
    }


def execute_generic_rollback(
    target: str,
    rollback_version: str,
    dry_run: bool,
) -> dict[str, Any]:
    """Generic rollback stub for targets without specific implementation."""
    return {
        "success": True,
        "dry_run": dry_run,
        "steps": [
            {
                "step": "rollback",
                "description": f"Roll back {target} to {rollback_version}",
                "status": "manual",
                "message": f"Use platform-specific CLI to rollback {target}",
            }
        ],
        "message": f"Manual rollback required for {target} to {rollback_version}",
    }


def execute_rollback(
    project_dir: Path,
    config: dict[str, Any],
    target: str,
    rollback_version: str,
    dry_run: bool,
) -> dict[str, Any]:
    """Execute rollback for a specific target."""
    targets = config.get("targets", {})
    target_config = targets.get(target, {})

    rollback_funcs = {
        "docker": execute_docker_rollback,
        "npm": execute_npm_rollback,
    }

    func = rollback_funcs.get(target)
    if func:
        return func(project_dir, config, target_config, rollback_version, dry_run)
    else:
        return execute_generic_rollback(target, rollback_version, dry_run)


# ---------------------------------------------------------------------------
# Post-rollback verification
# ---------------------------------------------------------------------------


def verify_rollback(
    project_dir: Path, config: dict[str, Any], target: str
) -> dict[str, Any]:
    """Verify that the rollback was successful."""
    checks = []

    if target == "docker":
        docker_config = config.get("targets", {}).get("docker", {}).get("config", {})
        image_name = docker_config.get("image_name", "app")

        try:
            result = subprocess.run(
                [
                    "docker",
                    "ps",
                    "--filter",
                    f"ancestor={image_name}",
                    "--format",
                    "{{.Status}}",
                ],
                capture_output=True,
                text=True,
                cwd=str(project_dir),
                timeout=30,
            )
            if result.returncode == 0 and result.stdout.strip():
                status = result.stdout.strip().splitlines()[0]
                is_healthy = "Up" in status
                checks.append(
                    {
                        "name": "container_status",
                        "status": "pass" if is_healthy else "fail",
                        "message": f"Container status: {status}",
                    }
                )
            else:
                checks.append(
                    {
                        "name": "container_status",
                        "status": "fail",
                        "message": "No running container found",
                    }
                )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            checks.append(
                {
                    "name": "container_status",
                    "status": "skip",
                    "message": "Docker not available for verification",
                }
            )

    elif target == "npm":
        npm_config = config.get("targets", {}).get("npm", {}).get("config", {})
        pkg_json = project_dir / "package.json"
        if pkg_json.exists():
            try:
                pkg = json.loads(pkg_json.read_text())
                pkg_name = pkg.get("name", "")
                result = subprocess.run(
                    ["npm", "view", pkg_name, "dist-tags", "--json"],
                    capture_output=True,
                    text=True,
                    cwd=str(project_dir),
                    timeout=30,
                )
                if result.returncode == 0:
                    checks.append(
                        {
                            "name": "dist_tags",
                            "status": "pass",
                            "message": f"Current dist-tags: {result.stdout.strip()}",
                        }
                    )
                else:
                    checks.append(
                        {
                            "name": "dist_tags",
                            "status": "warn",
                            "message": "Could not verify dist-tags",
                        }
                    )
            except (
                json.JSONDecodeError,
                OSError,
                subprocess.TimeoutExpired,
                FileNotFoundError,
            ):
                checks.append(
                    {
                        "name": "dist_tags",
                        "status": "skip",
                        "message": "Could not verify npm package",
                    }
                )

    if not checks:
        checks.append(
            {
                "name": "generic_verify",
                "status": "skip",
                "message": f"No automated verification for {target}",
            }
        )

    passed = sum(1 for c in checks if c["status"] == "pass")
    failed = sum(1 for c in checks if c["status"] == "fail")

    return {
        "checks": checks,
        "passed": passed,
        "failed": failed,
        "rollback_verified": failed == 0,
    }


# ---------------------------------------------------------------------------
# Incident report
# ---------------------------------------------------------------------------


def record_rollback(
    project_dir: Path,
    target: str,
    from_version: str | None,
    to_version: str,
    duration_ms: int,
    success: bool,
) -> bool:
    """Record rollback in deploy.json history."""
    config_file = project_dir / ".claude" / "popkit" / "deploy.json"

    try:
        config = json.loads(config_file.read_text())
    except (json.JSONDecodeError, OSError):
        return False

    record = {
        "timestamp": datetime.now().isoformat(),
        "target": target,
        "version": from_version or "unknown",
        "status": "rolled_back",
        "rollback_to": to_version,
        "duration_ms": duration_ms,
    }

    if "history" not in config:
        config["history"] = []
    config["history"].insert(0, record)
    config["history"] = config["history"][:50]

    try:
        config_file.write_text(json.dumps(config, indent=2))
        return True
    except OSError:
        return False


def generate_incident_report(
    project_dir: Path,
    config: dict[str, Any],
    target: str,
    failed_version: str | None,
    rollback_version: str,
    duration_ms: int,
) -> dict[str, Any]:
    """Generate incident report markdown file."""
    incidents_dir = project_dir / ".claude" / "popkit" / "incidents"
    incidents_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now()
    filename = f"incident-{timestamp.strftime('%Y%m%d-%H%M%S')}.md"
    report_path = incidents_dir / filename

    last_failed = get_last_failed(config, target)
    error_msg = last_failed.get("error", "Unknown") if last_failed else "Unknown"

    report_content = f"""# Deployment Incident Report

## Summary
- **Date:** {timestamp.isoformat()}
- **Target:** {target}
- **Failed Version:** {failed_version or "unknown"}
- **Rolled Back To:** {rollback_version}
- **Rollback Duration:** {duration_ms}ms
- **Severity:** P2

## Timeline
- {timestamp.strftime("%H:%M:%S")} - Rollback initiated
- {timestamp.strftime("%H:%M:%S")} - Rollback completed ({duration_ms}ms)

## Failure Details
- **Error:** {error_msg}

## Root Cause
_To be filled during post-mortem._

## Impact
_To be filled during post-mortem._

## Action Items
- [ ] Investigate root cause of deployment failure
- [ ] Add regression test for the failure scenario
- [ ] Update deployment validation checks if needed
- [ ] Review deployment process for improvements
- [ ] Schedule post-mortem meeting
"""

    report_path.write_text(report_content)

    return {
        "success": True,
        "report_path": str(report_path),
        "filename": filename,
    }


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Roll back deployment")
    parser.add_argument("--dir", default=".", help="Project directory")
    parser.add_argument(
        "--action",
        required=True,
        choices=["assess", "investigate", "rollback", "verify", "report"],
        help="Action to perform",
    )
    parser.add_argument("--target", help="Deployment target")
    parser.add_argument("--version", help="Version to roll back to")
    parser.add_argument(
        "--dry-run", action="store_true", help="Simulate rollback without executing"
    )
    args = parser.parse_args()

    project_dir = Path(args.dir).resolve()

    if not project_dir.exists():
        print(
            json.dumps({"error": f"Directory not found: {project_dir}"}, indent=2),
            file=sys.stderr,
        )
        return 1

    config_result = load_deploy_config(project_dir)
    if not config_result["success"]:
        print(
            json.dumps(
                {
                    "operation": f"rollback_{args.action}",
                    "success": False,
                    "error": config_result["error"],
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1

    config = config_result["config"]

    # Determine target
    deploy_target = args.target
    if not deploy_target:
        for name, t in config.get("targets", {}).items():
            if t.get("primary", False):
                deploy_target = name
                break
        if not deploy_target:
            for name, t in config.get("targets", {}).items():
                if t.get("enabled", False):
                    deploy_target = name
                    break

    if not deploy_target:
        print(
            json.dumps(
                {
                    "operation": f"rollback_{args.action}",
                    "success": False,
                    "error": "No deployment target available",
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1

    if args.action == "assess":
        result = assess_situation(project_dir, config, deploy_target)
        report = {
            "operation": "assess_rollback",
            "directory": str(project_dir),
            "timestamp": datetime.now().isoformat(),
            **result,
        }
        print(json.dumps(report, indent=2))
        return 0 if result["success"] else 1

    elif args.action == "investigate":
        result = investigate_failure(project_dir, config, deploy_target)
        report = {
            "operation": "investigate_failure",
            "directory": str(project_dir),
            "timestamp": datetime.now().isoformat(),
            **result,
        }
        print(json.dumps(report, indent=2))
        return 0

    elif args.action == "rollback":
        assessment = assess_situation(project_dir, config, deploy_target)
        if not assessment["success"]:
            print(
                json.dumps(
                    {
                        "operation": "execute_rollback",
                        "success": False,
                        "error": assessment["error"],
                    },
                    indent=2,
                ),
                file=sys.stderr,
            )
            return 1

        rollback_version = args.version or assessment.get("rollback_version")
        if not rollback_version:
            print(
                json.dumps(
                    {
                        "operation": "execute_rollback",
                        "success": False,
                        "error": "No rollback version available. Specify --version.",
                    },
                    indent=2,
                ),
                file=sys.stderr,
            )
            return 1

        start_time = time.time()
        result = execute_rollback(
            project_dir, config, deploy_target, rollback_version, args.dry_run
        )
        duration_ms = int((time.time() - start_time) * 1000)

        # Record rollback in history
        if not args.dry_run:
            record_rollback(
                project_dir,
                target=deploy_target,
                from_version=assessment.get("current_version"),
                to_version=rollback_version,
                duration_ms=duration_ms,
                success=result["success"],
            )

        report = {
            "operation": "execute_rollback",
            "directory": str(project_dir),
            "timestamp": datetime.now().isoformat(),
            "target": deploy_target,
            "from_version": assessment.get("current_version"),
            "to_version": rollback_version,
            "duration_ms": duration_ms,
            **result,
        }
        print(json.dumps(report, indent=2))
        return 0 if result["success"] else 1

    elif args.action == "verify":
        result = verify_rollback(project_dir, config, deploy_target)
        report = {
            "operation": "verify_rollback",
            "directory": str(project_dir),
            "timestamp": datetime.now().isoformat(),
            "target": deploy_target,
            **result,
        }
        print(json.dumps(report, indent=2))
        return 0 if result["rollback_verified"] else 1

    elif args.action == "report":
        assessment = assess_situation(project_dir, config, deploy_target)
        rollback_version = args.version or assessment.get("rollback_version", "unknown")
        failed_version = assessment.get("current_version")

        result = generate_incident_report(
            project_dir,
            config,
            deploy_target,
            failed_version,
            rollback_version,
            duration_ms=0,
        )

        report = {
            "operation": "generate_incident_report",
            "directory": str(project_dir),
            "timestamp": datetime.now().isoformat(),
            "target": deploy_target,
            **result,
        }
        print(json.dumps(report, indent=2))
        return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
