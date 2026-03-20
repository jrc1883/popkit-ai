#!/usr/bin/env python3
"""
Deployment Validation Script.

Run pre-deployment validation checks and generate readiness report.

Usage:
    python validate_deployment.py --dir DIR --action ACTION [--scope SCOPE] [--target TARGET]

Actions:
    load-config  - Load deploy.json and report current state
    validate     - Run validation checks

Output:
    JSON object with validation results and readiness score
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Check result helpers
# ---------------------------------------------------------------------------

PASS = "pass"
WARN = "warn"
FAIL = "fail"
SKIP = "skip"


def check_result(
    name: str,
    status: str,
    message: str,
    blocking: bool = False,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Create a standardized check result."""
    result = {
        "name": name,
        "status": status,
        "message": message,
        "blocking": blocking,
    }
    if details:
        result["details"] = details
    return result


# ---------------------------------------------------------------------------
# Configuration checks
# ---------------------------------------------------------------------------


def load_deploy_config(project_dir: Path) -> dict[str, Any]:
    """Load and validate deploy.json."""
    config_file = project_dir / ".claude" / "popkit" / "deploy.json"

    if not config_file.exists():
        return {
            "success": False,
            "error": "deploy.json not found. Run /popkit-ops:deploy init first.",
            "config_path": str(config_file),
        }

    try:
        config = json.loads(config_file.read_text())
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Invalid JSON in deploy.json: {e}",
            "config_path": str(config_file),
        }

    enabled_targets = [
        name
        for name, target in config.get("targets", {}).items()
        if target.get("enabled", False)
    ]

    primary_target = None
    for name, target in config.get("targets", {}).items():
        if target.get("primary", False):
            primary_target = name
            break

    return {
        "success": True,
        "config_path": str(config_file),
        "project_name": config.get("project_name", "unknown"),
        "enabled_targets": enabled_targets,
        "primary_target": primary_target,
        "ci_provider": config.get("ci", {}).get("provider"),
        "history_count": len(config.get("history", [])),
        "config": config,
    }


# ---------------------------------------------------------------------------
# Validation checks
# ---------------------------------------------------------------------------


def check_config_valid(project_dir: Path, config: dict[str, Any]) -> dict[str, Any]:
    """Validate deploy.json structure and required fields."""
    required_fields = ["version", "project_name", "targets"]
    missing = [f for f in required_fields if f not in config]

    if missing:
        return check_result(
            "config_valid",
            FAIL,
            f"Missing required fields: {', '.join(missing)}",
            blocking=True,
        )

    # Check version
    if config.get("version") != "1.0":
        return check_result(
            "config_valid",
            WARN,
            f"Unknown config version: {config.get('version')}",
        )

    # Check at least one target enabled
    enabled = [
        n for n, t in config.get("targets", {}).items() if t.get("enabled", False)
    ]
    if not enabled:
        return check_result(
            "config_valid",
            FAIL,
            "No deployment targets enabled",
            blocking=True,
        )

    return check_result(
        "config_valid",
        PASS,
        f"Config valid ({len(enabled)} targets enabled)",
    )


def check_target_config(config: dict[str, Any], target: str | None) -> dict[str, Any]:
    """Validate target-specific configuration."""
    targets = config.get("targets", {})

    if target and target not in targets:
        return check_result(
            "target_config",
            FAIL,
            f"Target '{target}' not found in config",
            blocking=True,
        )

    check_targets = (
        [target]
        if target
        else [n for n, t in targets.items() if t.get("enabled", False)]
    )

    issues = []
    for t in check_targets:
        target_config = targets.get(t, {})
        if not target_config.get("enabled", False):
            issues.append(f"{t}: not enabled")
        if not target_config.get("config"):
            issues.append(f"{t}: missing config section")

    if issues:
        return check_result(
            "target_config",
            WARN,
            f"Target config issues: {'; '.join(issues)}",
            details={"issues": issues},
        )

    return check_result(
        "target_config",
        PASS,
        f"Target config valid ({len(check_targets)} targets checked)",
    )


def check_git_status(project_dir: Path) -> dict[str, Any]:
    """Check for uncommitted changes."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=str(project_dir),
            timeout=30,
        )
        if result.returncode != 0:
            return check_result(
                "git_status",
                WARN,
                "Could not check git status",
            )

        changes = result.stdout.strip()
        if changes:
            change_count = len(changes.splitlines())
            return check_result(
                "git_status",
                WARN,
                f"{change_count} uncommitted changes found",
                details={"change_count": change_count},
            )

        return check_result("git_status", PASS, "Working directory clean")

    except (subprocess.TimeoutExpired, FileNotFoundError):
        return check_result(
            "git_status",
            SKIP,
            "Git not available",
        )


def check_build(project_dir: Path) -> dict[str, Any]:
    """Check if project builds successfully."""
    # Try common build commands
    build_commands = [
        (["npm", "run", "build"], "package.json"),
        (["python", "-m", "build"], "pyproject.toml"),
    ]

    for cmd, config_file in build_commands:
        if (project_dir / config_file).exists():
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=str(project_dir),
                    timeout=120,
                )
                if result.returncode == 0:
                    return check_result("build", PASS, f"Build succeeded ({cmd[0]})")
                else:
                    return check_result(
                        "build",
                        FAIL,
                        f"Build failed ({cmd[0]})",
                        blocking=True,
                        details={"stderr": result.stderr[:500]},
                    )
            except subprocess.TimeoutExpired:
                return check_result(
                    "build",
                    FAIL,
                    "Build timed out (120s)",
                    blocking=True,
                )
            except FileNotFoundError:
                continue

    return check_result("build", SKIP, "No recognized build system found")


def check_tests(project_dir: Path) -> dict[str, Any]:
    """Check if test suite passes."""
    test_commands = [
        (["npm", "test"], "package.json"),
        (["python", "-m", "pytest", "--tb=short", "-q"], "pyproject.toml"),
    ]

    for cmd, config_file in test_commands:
        if (project_dir / config_file).exists():
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    cwd=str(project_dir),
                    timeout=300,
                )
                if result.returncode == 0:
                    return check_result("tests", PASS, "Tests passed")
                else:
                    return check_result(
                        "tests",
                        FAIL,
                        "Test suite failed",
                        blocking=True,
                        details={"stdout": result.stdout[:500]},
                    )
            except subprocess.TimeoutExpired:
                return check_result(
                    "tests",
                    FAIL,
                    "Tests timed out (300s)",
                    blocking=True,
                )
            except FileNotFoundError:
                continue

    return check_result("tests", SKIP, "No recognized test framework found")


def check_dependencies(project_dir: Path) -> dict[str, Any]:
    """Check for dependency vulnerabilities."""
    # npm audit
    if (project_dir / "package.json").exists():
        try:
            result = subprocess.run(
                ["npm", "audit", "--json"],
                capture_output=True,
                text=True,
                cwd=str(project_dir),
                timeout=60,
            )
            try:
                audit = json.loads(result.stdout)
                vuln_count = audit.get("metadata", {}).get("vulnerabilities", {})
                critical = vuln_count.get("critical", 0)
                high = vuln_count.get("high", 0)
                moderate = vuln_count.get("moderate", 0)

                if critical > 0 or high > 0:
                    return check_result(
                        "dependencies",
                        WARN,
                        f"Vulnerabilities: {critical} critical, {high} high, {moderate} moderate",
                        details={
                            "critical": critical,
                            "high": high,
                            "moderate": moderate,
                        },
                    )
                elif moderate > 0:
                    return check_result(
                        "dependencies",
                        WARN,
                        f"{moderate} moderate vulnerabilities",
                        details={"moderate": moderate},
                    )
                else:
                    return check_result(
                        "dependencies", PASS, "No known vulnerabilities"
                    )
            except json.JSONDecodeError:
                if result.returncode == 0:
                    return check_result(
                        "dependencies", PASS, "No known vulnerabilities"
                    )
                return check_result(
                    "dependencies",
                    WARN,
                    "Could not parse audit results",
                )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return check_result("dependencies", SKIP, "npm audit not available")

    return check_result("dependencies", SKIP, "No dependency audit available")


def check_lockfile(project_dir: Path) -> dict[str, Any]:
    """Check that lock file exists and is up to date."""
    lockfiles = [
        ("package-lock.json", "package.json"),
        ("yarn.lock", "package.json"),
        ("pnpm-lock.yaml", "package.json"),
        ("poetry.lock", "pyproject.toml"),
    ]

    for lockfile, manifest in lockfiles:
        manifest_path = project_dir / manifest
        lockfile_path = project_dir / lockfile

        if manifest_path.exists():
            if lockfile_path.exists():
                # Check if lock file is newer than manifest
                if lockfile_path.stat().st_mtime >= manifest_path.stat().st_mtime:
                    return check_result(
                        "lockfile", PASS, f"{lockfile} present and up to date"
                    )
                else:
                    return check_result(
                        "lockfile",
                        WARN,
                        f"{lockfile} may be outdated (older than {manifest})",
                    )
            else:
                return check_result(
                    "lockfile",
                    WARN,
                    f"No lock file found for {manifest}",
                )

    return check_result("lockfile", SKIP, "No package manifest found")


def check_env_vars(project_dir: Path) -> dict[str, Any]:
    """Check environment variable documentation."""
    env_example = project_dir / ".env.example"
    env_file = project_dir / ".env"

    if not env_example.exists():
        if env_file.exists():
            return check_result(
                "env_vars",
                WARN,
                ".env exists but .env.example missing (secrets undocumented)",
            )
        return check_result("env_vars", PASS, "No environment variables needed")

    if not env_file.exists():
        return check_result(
            "env_vars",
            WARN,
            ".env.example exists but .env not found",
        )

    # Compare keys
    try:
        example_keys = set()
        for line in env_example.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                example_keys.add(line.split("=")[0].strip())

        env_keys = set()
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                env_keys.add(line.split("=")[0].strip())

        missing = example_keys - env_keys
        if missing:
            return check_result(
                "env_vars",
                WARN,
                f"Missing env vars: {', '.join(sorted(missing))}",
                details={"missing": sorted(missing)},
            )

        return check_result("env_vars", PASS, "All documented env vars present")

    except OSError:
        return check_result("env_vars", SKIP, "Could not read env files")


def check_dockerfile_lint(project_dir: Path) -> dict[str, Any]:
    """Check Dockerfile best practices."""
    dockerfile = project_dir / "Dockerfile"
    if not dockerfile.exists():
        return check_result("dockerfile_lint", SKIP, "No Dockerfile found")

    issues = []
    try:
        content = dockerfile.read_text()
        lines = content.splitlines()

        # Check for common issues
        has_user = False
        has_healthcheck = False
        uses_latest = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("USER"):
                has_user = True
            if stripped.startswith("HEALTHCHECK"):
                has_healthcheck = True
            if stripped.startswith("FROM") and ":latest" in stripped:
                uses_latest = True

        if not has_user:
            issues.append("No USER instruction (runs as root)")
        if not has_healthcheck:
            issues.append("No HEALTHCHECK instruction")
        if uses_latest:
            issues.append("Uses :latest tag (non-reproducible)")

        if issues:
            return check_result(
                "dockerfile_lint",
                WARN,
                f"{len(issues)} Dockerfile issues found",
                details={"issues": issues},
            )

        return check_result(
            "dockerfile_lint", PASS, "Dockerfile follows best practices"
        )

    except OSError:
        return check_result("dockerfile_lint", SKIP, "Could not read Dockerfile")


# ---------------------------------------------------------------------------
# Readiness scoring
# ---------------------------------------------------------------------------


def calculate_readiness(checks: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate overall readiness score and recommendation."""
    total = len(checks)
    passed = sum(1 for c in checks if c["status"] == PASS)
    warned = sum(1 for c in checks if c["status"] == WARN)
    failed = sum(1 for c in checks if c["status"] == FAIL)
    skipped = sum(1 for c in checks if c["status"] == SKIP)
    blocking_failures = sum(
        1 for c in checks if c["status"] == FAIL and c.get("blocking", False)
    )

    # Score calculation
    active_checks = total - skipped
    if active_checks == 0:
        score = 50  # No checks could run
    else:
        score = int((passed / active_checks) * 100)
        # Deduct for warnings
        score -= warned * 5
        # Deduct heavily for failures
        score -= failed * 20
        score = max(0, min(100, score))

    # Recommendation
    if blocking_failures > 0:
        recommendation = "NO-GO"
        reason = f"{blocking_failures} blocking failure(s) must be resolved"
    elif score >= 80:
        recommendation = "GO"
        reason = "All critical checks passed"
        if warned > 0:
            reason += f" ({warned} warning(s) to review)"
    elif score >= 60:
        recommendation = "CONDITIONAL"
        reason = "Non-blocking issues should be addressed"
    else:
        recommendation = "NO-GO"
        reason = "Significant issues detected"

    return {
        "score": score,
        "recommendation": recommendation,
        "reason": reason,
        "summary": {
            "total": total,
            "passed": passed,
            "warned": warned,
            "failed": failed,
            "skipped": skipped,
            "blocking_failures": blocking_failures,
        },
    }


# ---------------------------------------------------------------------------
# Validation orchestrator
# ---------------------------------------------------------------------------


def run_validation(
    project_dir: Path,
    config: dict[str, Any],
    scope: str,
    target: str | None = None,
) -> dict[str, Any]:
    """Run all validation checks for the given scope."""
    checks = []

    # Quick checks (always run)
    checks.append(check_config_valid(project_dir, config))
    checks.append(check_target_config(config, target))
    checks.append(check_git_status(project_dir))

    if scope in ("standard", "full"):
        checks.append(check_build(project_dir))
        checks.append(check_tests(project_dir))
        checks.append(check_dependencies(project_dir))
        checks.append(check_lockfile(project_dir))
        checks.append(check_env_vars(project_dir))

    if scope == "full":
        checks.append(check_dockerfile_lint(project_dir))

    readiness = calculate_readiness(checks)

    return {
        "checks": checks,
        "readiness": readiness,
    }


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Validate deployment readiness")
    parser.add_argument("--dir", default=".", help="Project directory")
    parser.add_argument(
        "--action",
        required=True,
        choices=["load-config", "validate"],
        help="Action to perform",
    )
    parser.add_argument(
        "--scope",
        default="standard",
        choices=["quick", "standard", "full"],
        help="Validation scope",
    )
    parser.add_argument("--target", help="Specific target to validate")
    args = parser.parse_args()

    project_dir = Path(args.dir).resolve()

    if not project_dir.exists():
        print(
            json.dumps({"error": f"Directory not found: {project_dir}"}, indent=2),
            file=sys.stderr,
        )
        return 1

    if args.action == "load-config":
        result = load_deploy_config(project_dir)
        report = {
            "operation": "load_deploy_config",
            "directory": str(project_dir),
            "timestamp": datetime.now().isoformat(),
            **result,
        }
        print(json.dumps(report, indent=2))
        return 0 if result["success"] else 1

    elif args.action == "validate":
        config_result = load_deploy_config(project_dir)
        if not config_result["success"]:
            # Still run basic checks even without config
            checks = [
                check_result(
                    "config_valid",
                    FAIL,
                    config_result["error"],
                    blocking=True,
                ),
                check_git_status(project_dir),
            ]
            readiness = calculate_readiness(checks)
            report = {
                "operation": "validate_deployment",
                "success": False,
                "directory": str(project_dir),
                "timestamp": datetime.now().isoformat(),
                "scope": args.scope,
                "checks": checks,
                "readiness": readiness,
            }
            print(json.dumps(report, indent=2))
            return 1

        config = config_result["config"]
        result = run_validation(project_dir, config, args.scope, args.target)

        report = {
            "operation": "validate_deployment",
            "success": result["readiness"]["recommendation"] != "NO-GO",
            "directory": str(project_dir),
            "project_name": config.get("project_name"),
            "timestamp": datetime.now().isoformat(),
            "scope": args.scope,
            "target": args.target,
            **result,
        }
        print(json.dumps(report, indent=2))
        return 0 if report["success"] else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
