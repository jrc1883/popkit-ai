#!/usr/bin/env python3
"""
Deployment Execution Script.

Execute deployments to target environments with dry-run support.

Usage:
    python execute_deployment.py --dir DIR --action ACTION [--target TARGET] [--mode MODE] [--version VERSION]

Actions:
    prepare  - Load config, identify target, prepare deployment plan
    execute  - Execute the deployment
    verify   - Run post-deployment health checks

Output:
    JSON object with deployment results and metrics
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


def get_current_version(project_dir: Path) -> str | None:
    """Detect current project version."""
    # package.json
    pkg_json = project_dir / "package.json"
    if pkg_json.exists():
        try:
            pkg = json.loads(pkg_json.read_text())
            return pkg.get("version")
        except (json.JSONDecodeError, OSError):
            pass  # Corrupt or unreadable package.json; try other sources

    # pyproject.toml
    pyproject = project_dir / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text()
            for line in content.splitlines():
                if line.strip().startswith("version") and "=" in line:
                    return line.split("=")[1].strip().strip('"').strip("'")
        except OSError:
            pass  # Unreadable pyproject.toml; try git tag next

    # Git tag
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True,
            text=True,
            cwd=str(project_dir),
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass  # Git unavailable or timed out; no version detected

    return None


def get_git_sha(project_dir: Path) -> str | None:
    """Get current git commit SHA."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(project_dir),
            timeout=10,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass  # Git unavailable or timed out; no SHA available
    return None


def get_last_deployment(config: dict[str, Any], target: str) -> dict[str, Any] | None:
    """Get the last successful deployment for a target."""
    history = config.get("history", [])
    for record in history:
        if record.get("target") == target and record.get("status") == "success":
            return record
    return None


# ---------------------------------------------------------------------------
# Deployment preparation
# ---------------------------------------------------------------------------


def prepare_deployment(
    project_dir: Path, config: dict[str, Any], target: str | None
) -> dict[str, Any]:
    """Prepare deployment plan."""
    targets = config.get("targets", {})

    # Determine target
    if target:
        if target not in targets:
            return {
                "success": False,
                "error": f"Target '{target}' not found in config",
            }
        deploy_target = target
    else:
        # Use primary target
        deploy_target = None
        for name, t in targets.items():
            if t.get("primary", False):
                deploy_target = name
                break
        if not deploy_target:
            # Use first enabled target
            for name, t in targets.items():
                if t.get("enabled", False):
                    deploy_target = name
                    break

    if not deploy_target:
        return {"success": False, "error": "No deployment target available"}

    target_config = targets[deploy_target]
    version = get_current_version(project_dir)
    commit_sha = get_git_sha(project_dir)
    last_deploy = get_last_deployment(config, deploy_target)

    return {
        "success": True,
        "target": deploy_target,
        "target_config": target_config,
        "version": version,
        "commit_sha": commit_sha,
        "last_deployment": last_deploy,
        "rollback_version": last_deploy.get("version") if last_deploy else None,
        "project_name": config.get("project_name"),
        "ci_provider": config.get("ci", {}).get("provider"),
    }


# ---------------------------------------------------------------------------
# Deployment execution
# ---------------------------------------------------------------------------


def execute_docker_deploy(
    project_dir: Path,
    config: dict[str, Any],
    target_config: dict[str, Any],
    version: str,
    dry_run: bool,
) -> dict[str, Any]:
    """Execute Docker deployment."""
    docker_config = target_config.get("config", {})
    image_name = docker_config.get("image_name", config.get("project_name", "app"))
    registry = docker_config.get("registry", "ghcr.io")
    dockerfile = docker_config.get("dockerfile", "Dockerfile")
    build_context = docker_config.get("build_context", ".")

    full_image = f"{registry}/{image_name}"
    tags = docker_config.get("tags", ["latest"])
    resolved_tags = [t.replace("{{version}}", version or "latest") for t in tags]

    steps = []

    # Step 1: Build
    tag_args = []
    for tag in resolved_tags:
        tag_args.extend(["-t", f"{full_image}:{tag}"])

    build_cmd = ["docker", "build", "-f", dockerfile] + tag_args + [build_context]
    steps.append(
        {
            "step": "build",
            "command": " ".join(build_cmd),
            "description": f"Build image {full_image}",
        }
    )

    # Step 2: Push
    for tag in resolved_tags:
        push_cmd = ["docker", "push", f"{full_image}:{tag}"]
        steps.append(
            {
                "step": "push",
                "command": " ".join(push_cmd),
                "description": f"Push {full_image}:{tag}",
            }
        )

    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "steps": steps,
            "message": f"Would deploy {full_image} with tags: {', '.join(resolved_tags)}",
        }

    # Execute steps
    executed_steps = []
    for step in steps:
        step_start = time.time()
        try:
            result = subprocess.run(
                step["command"].split(),
                capture_output=True,
                text=True,
                cwd=str(project_dir),
                timeout=600,
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
                    "error": f"Step '{step['step']}' failed: {result.stderr[:200]}",
                }
        except subprocess.TimeoutExpired:
            executed_steps.append(
                {
                    **step,
                    "status": "timeout",
                    "duration_s": 600,
                }
            )
            return {
                "success": False,
                "dry_run": False,
                "steps": executed_steps,
                "error": f"Step '{step['step']}' timed out",
            }
        except FileNotFoundError:
            executed_steps.append(
                {
                    **step,
                    "status": "failed",
                    "error": "docker command not found",
                }
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
        "tags": resolved_tags,
    }


def execute_npm_deploy(
    project_dir: Path,
    config: dict[str, Any],
    target_config: dict[str, Any],
    version: str,
    dry_run: bool,
) -> dict[str, Any]:
    """Execute npm publish."""
    npm_config = target_config.get("config", {})
    registry = npm_config.get("registry", "https://registry.npmjs.org")
    access = npm_config.get("access", "public")
    tag = npm_config.get("tag", "latest")

    publish_cmd = [
        "npm",
        "publish",
        "--registry",
        registry,
        "--access",
        access,
        "--tag",
        tag,
    ]

    if dry_run:
        publish_cmd.append("--dry-run")

    steps = [
        {
            "step": "publish",
            "command": " ".join(publish_cmd),
            "description": f"Publish to {registry}",
        }
    ]

    if dry_run:
        return {
            "success": True,
            "dry_run": True,
            "steps": steps,
            "message": f"Would publish to {registry} with access={access}, tag={tag}",
        }

    try:
        result = subprocess.run(
            publish_cmd,
            capture_output=True,
            text=True,
            cwd=str(project_dir),
            timeout=120,
        )
        steps[0]["status"] = "success" if result.returncode == 0 else "failed"
        steps[0]["exit_code"] = result.returncode

        if result.returncode != 0:
            steps[0]["stderr"] = result.stderr[:500]
            return {
                "success": False,
                "dry_run": False,
                "steps": steps,
                "error": f"npm publish failed: {result.stderr[:200]}",
            }

        return {
            "success": True,
            "dry_run": False,
            "steps": steps,
            "registry": registry,
        }

    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        steps[0]["status"] = "failed"
        return {
            "success": False,
            "dry_run": False,
            "steps": steps,
            "error": str(e),
        }


def execute_generic_deploy(
    target: str,
    target_config: dict[str, Any],
    dry_run: bool,
) -> dict[str, Any]:
    """Generic deployment stub for targets without specific implementation."""
    return {
        "success": True,
        "dry_run": dry_run,
        "steps": [
            {
                "step": "deploy",
                "description": f"Deploy to {target}",
                "status": "skipped" if dry_run else "manual",
                "message": f"Use platform-specific CLI for {target} deployment",
            }
        ],
        "message": f"{'Would deploy' if dry_run else 'Deploy'} to {target} - use platform CLI",
    }


def execute_deployment(
    project_dir: Path,
    config: dict[str, Any],
    target: str,
    target_config: dict[str, Any],
    version: str | None,
    mode: str,
) -> dict[str, Any]:
    """Execute deployment for a specific target."""
    dry_run = mode == "dry_run"
    effective_version = version or "latest"

    deploy_funcs = {
        "docker": execute_docker_deploy,
        "npm": execute_npm_deploy,
    }

    func = deploy_funcs.get(target)
    if func:
        return func(project_dir, config, target_config, effective_version, dry_run)
    else:
        return execute_generic_deploy(target, target_config, dry_run)


# ---------------------------------------------------------------------------
# History management
# ---------------------------------------------------------------------------


def record_deployment(
    project_dir: Path,
    target: str,
    version: str | None,
    status: str,
    commit_sha: str | None,
    duration_ms: int,
    error: str | None = None,
) -> bool:
    """Record deployment result in deploy.json history."""
    config_file = project_dir / ".claude" / "popkit" / "deploy.json"

    try:
        config = json.loads(config_file.read_text())
    except (json.JSONDecodeError, OSError):
        return False

    record = {
        "timestamp": datetime.now().isoformat(),
        "target": target,
        "version": version or "unknown",
        "status": status,
        "commit_sha": commit_sha,
        "duration_ms": duration_ms,
    }
    if error:
        record["error"] = error

    if "history" not in config:
        config["history"] = []
    config["history"].insert(0, record)

    # Keep last 50 records
    config["history"] = config["history"][:50]

    try:
        config_file.write_text(json.dumps(config, indent=2))
        return True
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Post-deploy verification
# ---------------------------------------------------------------------------


def verify_deployment(
    project_dir: Path,
    config: dict[str, Any],
    target: str,
    target_config: dict[str, Any],
) -> dict[str, Any]:
    """Run post-deployment health checks."""
    checks = []

    # Check Docker container health
    if target == "docker":
        docker_config = target_config.get("config", {})
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
                checks.append(
                    {
                        "name": "container_running",
                        "status": "pass",
                        "message": f"Container running: {result.stdout.strip()}",
                    }
                )
            else:
                checks.append(
                    {
                        "name": "container_running",
                        "status": "warn",
                        "message": "No running container found for image",
                    }
                )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            checks.append(
                {
                    "name": "container_running",
                    "status": "skip",
                    "message": "Docker not available for verification",
                }
            )

    # Check npm package published
    elif target == "npm":
        npm_config = target_config.get("config", {})
        pkg_json = project_dir / "package.json"
        if pkg_json.exists():
            try:
                pkg = json.loads(pkg_json.read_text())
                pkg_name = pkg.get("name", "")
                result = subprocess.run(
                    ["npm", "view", pkg_name, "version"],
                    capture_output=True,
                    text=True,
                    cwd=str(project_dir),
                    timeout=30,
                )
                if result.returncode == 0:
                    checks.append(
                        {
                            "name": "package_published",
                            "status": "pass",
                            "message": f"Published version: {result.stdout.strip()}",
                        }
                    )
                else:
                    checks.append(
                        {
                            "name": "package_published",
                            "status": "warn",
                            "message": "Could not verify package on registry",
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
                        "name": "package_published",
                        "status": "skip",
                        "message": "Could not verify package",
                    }
                )

    if not checks:
        checks.append(
            {
                "name": "generic_verify",
                "status": "skip",
                "message": f"No automated verification available for {target}",
            }
        )

    passed = sum(1 for c in checks if c["status"] == "pass")
    total = len(checks)

    return {
        "checks": checks,
        "passed": passed,
        "total": total,
        "healthy": passed == total
        or all(c["status"] in ("pass", "skip") for c in checks),
    }


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Execute deployment")
    parser.add_argument("--dir", default=".", help="Project directory")
    parser.add_argument(
        "--action",
        required=True,
        choices=["prepare", "execute", "verify"],
        help="Action to perform",
    )
    parser.add_argument("--target", help="Deployment target")
    parser.add_argument(
        "--mode",
        default="dry_run",
        choices=["dry_run", "deploy", "canary"],
        help="Deployment mode",
    )
    parser.add_argument("--version", help="Version to deploy")
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
                    "operation": f"deploy_{args.action}",
                    "success": False,
                    "error": config_result["error"],
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1

    config = config_result["config"]

    if args.action == "prepare":
        result = prepare_deployment(project_dir, config, args.target)
        report = {
            "operation": "prepare_deployment",
            "directory": str(project_dir),
            "timestamp": datetime.now().isoformat(),
            **result,
        }
        print(json.dumps(report, indent=2))
        return 0 if result["success"] else 1

    elif args.action == "execute":
        # Prepare first
        prep = prepare_deployment(project_dir, config, args.target)
        if not prep["success"]:
            print(
                json.dumps(
                    {
                        "operation": "execute_deployment",
                        "success": False,
                        "error": prep["error"],
                    },
                    indent=2,
                ),
                file=sys.stderr,
            )
            return 1

        target = prep["target"]
        target_config = prep["target_config"]
        version = args.version or prep.get("version")

        start_time = time.time()
        result = execute_deployment(
            project_dir, config, target, target_config, version, args.mode
        )
        duration_ms = int((time.time() - start_time) * 1000)

        # Record in history (only for non-dry-run)
        if args.mode != "dry_run":
            record_deployment(
                project_dir,
                target=target,
                version=version,
                status="success" if result["success"] else "failed",
                commit_sha=prep.get("commit_sha"),
                duration_ms=duration_ms,
                error=result.get("error"),
            )

        deployment_id = f"deploy-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        report = {
            "operation": "execute_deployment",
            "directory": str(project_dir),
            "timestamp": datetime.now().isoformat(),
            "deployment_id": deployment_id,
            "target": target,
            "version": version,
            "mode": args.mode,
            "duration_ms": duration_ms,
            "rollback_version": prep.get("rollback_version"),
            **result,
        }
        print(json.dumps(report, indent=2))
        return 0 if result["success"] else 1

    elif args.action == "verify":
        prep = prepare_deployment(project_dir, config, args.target)
        if not prep["success"]:
            print(
                json.dumps(
                    {
                        "operation": "verify_deployment",
                        "success": False,
                        "error": prep["error"],
                    },
                    indent=2,
                ),
                file=sys.stderr,
            )
            return 1

        target = prep["target"]
        target_config = prep["target_config"]
        result = verify_deployment(project_dir, config, target, target_config)

        report = {
            "operation": "verify_deployment",
            "directory": str(project_dir),
            "timestamp": datetime.now().isoformat(),
            "target": target,
            **result,
        }
        print(json.dumps(report, indent=2))
        return 0 if result["healthy"] else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
