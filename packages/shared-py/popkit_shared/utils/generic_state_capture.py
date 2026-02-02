#!/usr/bin/env python3
"""
Generic State Capture for Any Project Type.

Captures project state for morning/nightly routines, adapting to
detected project type (Node.js, Python, Rust, Go, Ruby, Java, .NET).

Issue #69: Generic Workspace Routine Templates
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from .generic_project_detector import GenericProjectDetector, ProjectType

    HAS_PROJECT_DETECTOR = True
except ImportError:
    HAS_PROJECT_DETECTOR = False


def run_command(
    cmd: str | List[str], timeout: int = 30, cwd: Optional[Path] = None
) -> tuple[str, bool]:
    """
    Run a shell command and return output and success status.

    Args:
        cmd: Command string or list of arguments
        timeout: Command timeout in seconds
        cwd: Working directory

    Returns:
        (output, success) tuple
    """
    try:
        result = subprocess.run(
            cmd.split() if isinstance(cmd, str) else cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
        )
        return result.stdout.strip(), result.returncode == 0
    except subprocess.TimeoutExpired:
        return "Command timed out", False
    except Exception as e:
        return str(e), False


def gather_git_state(project_path: Path = None) -> Dict[str, Any]:
    """
    Gather current git repository state.

    Args:
        project_path: Path to project directory

    Returns:
        Git state dictionary with branch, commits, uncommitted files, etc.
    """
    if project_path is None:
        project_path = Path.cwd()

    state = {
        "branch": "",
        "lastCommit": "",
        "uncommittedFiles": 0,
        "stagedFiles": 0,
        "modifiedFiles": [],
        "untrackedFiles": [],
        "behindRemote": 0,
        "aheadRemote": 0,
        "stashCount": 0,
    }

    # Get current branch
    branch, ok = run_command("git branch --show-current", cwd=project_path)
    if ok:
        state["branch"] = branch

    # Get last commit
    commit, ok = run_command("git log -1 --format='%h - %s'", cwd=project_path)
    if ok:
        state["lastCommit"] = commit

    # Count uncommitted changes
    status, ok = run_command("git status --porcelain", cwd=project_path)
    if ok:
        lines = [line for line in status.split("\n") if line.strip()]
        state["uncommittedFiles"] = len(lines)

        for line in lines:
            if line.startswith("??"):
                state["untrackedFiles"].append(line[3:].strip())
            else:
                state["modifiedFiles"].append(line[3:].strip())

    # Count staged files
    staged, ok = run_command("git diff --cached --name-only", cwd=project_path)
    if ok:
        staged_files = [f for f in staged.split("\n") if f.strip()]
        state["stagedFiles"] = len(staged_files)

    # Check remote sync status
    fetch_output, _ = run_command("git fetch --dry-run", cwd=project_path)
    rev_list, ok = run_command("git rev-list --left-right --count HEAD...@{u}", cwd=project_path)
    if ok and "\t" in rev_list:
        ahead, behind = rev_list.split("\t")
        state["aheadRemote"] = int(ahead)
        state["behindRemote"] = int(behind)

    # Count stashes
    stash_list, ok = run_command("git stash list", cwd=project_path)
    if ok:
        state["stashCount"] = len([s for s in stash_list.split("\n") if s.strip()])

    return state


def gather_dependency_state(project_type: ProjectType, project_path: Path = None) -> Dict[str, Any]:
    """
    Check dependency health based on project type.

    Args:
        project_type: Detected project type with package manager info
        project_path: Path to project directory

    Returns:
        Dependency state dictionary
    """
    if project_path is None:
        project_path = Path.cwd()

    state = {
        "packageManager": project_type.package_manager,
        "installed": False,
        "outdatedCount": 0,
        "outdatedPackages": [],
    }

    if not project_type.check_installed:
        return state

    # Check if dependencies are installed
    output, ok = run_command(project_type.check_installed, timeout=10, cwd=project_path)
    state["installed"] = ok

    # Check for outdated dependencies
    if project_type.check_outdated:
        outdated, ok = run_command(project_type.check_outdated, timeout=30, cwd=project_path)
        if ok and outdated:
            # Parse output based on package manager
            if project_type.package_manager in ("npm", "pnpm", "yarn"):
                # npm/pnpm outdated format
                lines = [line for line in outdated.split("\n") if line.strip()]
                state["outdatedCount"] = max(0, len(lines) - 1)  # Exclude header
                state["outdatedPackages"] = lines[1:6]  # First 5 packages
            elif project_type.package_manager == "pip":
                # pip list --outdated format
                lines = [line for line in outdated.split("\n") if line.strip()]
                state["outdatedCount"] = max(0, len(lines) - 2)  # Exclude headers
                state["outdatedPackages"] = lines[2:7]  # First 5 packages
            else:
                # Generic: count non-empty lines
                lines = [line for line in outdated.split("\n") if line.strip()]
                state["outdatedCount"] = len(lines)
                state["outdatedPackages"] = lines[:5]

    return state


def check_service_running(port: int) -> bool:
    """
    Check if a service is running on a specific port.

    Args:
        port: Port number to check

    Returns:
        True if service is listening on port
    """
    import socket

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(1)
            result = sock.connect_ex(("127.0.0.1", port))
            return result == 0
    except Exception:
        return False


def gather_service_state(project_type: ProjectType, project_path: Path = None) -> Dict[str, Any]:
    """
    Check running services based on project type.

    Args:
        project_type: Detected project type with expected services
        project_path: Path to project directory (unused but kept for API consistency)

    Returns:
        Service state dictionary
    """
    state = {
        "expectedServices": [],
        "runningServices": [],
        "missingServices": [],
    }

    if not project_type.expected_services:
        return state

    for service in project_type.expected_services:
        service_info = {
            "name": service["name"],
            "port": service["port"],
            "description": service.get("description", ""),
        }
        state["expectedServices"].append(service_info)

        if check_service_running(service["port"]):
            state["runningServices"].append(service_info)
        else:
            state["missingServices"].append(service_info)

    return state


def gather_test_state(
    project_type: ProjectType, project_path: Path = None, skip_tests: bool = False
) -> Dict[str, Any]:
    """
    Check test framework and test status.

    Args:
        project_type: Detected project type with test framework
        project_path: Path to project directory
        skip_tests: If True, skip actually running tests

    Returns:
        Test state dictionary
    """
    if project_path is None:
        project_path = Path.cwd()

    state = {
        "testFramework": project_type.test_framework,
        "testsExist": False,
        "lastRunPassed": None,  # None = unknown, True/False = known status
    }

    if not project_type.test_framework:
        return state

    # Check if test files exist
    test_patterns = {
        "jest": "**/*.test.{js,ts,jsx,tsx}",
        "mocha": "test/**/*.js",
        "pytest": "**/*test*.py",
        "cargo test": "tests/**/*.rs",
        "go test": "**/*_test.go",
        "rspec": "spec/**/*_spec.rb",
        "JUnit": "**/*Test.java",
        "xUnit": "**/*Tests.cs",
    }

    pattern = test_patterns.get(project_type.test_framework)
    if pattern:
        test_files = list(project_path.glob(pattern))
        state["testsExist"] = len(test_files) > 0

    # Optionally run tests (expensive, usually skipped in quick mode)
    if not skip_tests and state["testsExist"]:
        # Build test command
        test_cmd = None
        if project_type.test_framework == "jest":
            test_cmd = f"{project_type.package_manager} test"
        elif project_type.test_framework == "pytest":
            test_cmd = "pytest --collect-only"  # Just check collection
        elif project_type.test_framework == "cargo test":
            test_cmd = "cargo test --no-run"  # Just build, don't run
        elif project_type.test_framework == "go test":
            test_cmd = "go test -run=^$ ./..."  # Run no tests, just compile

        if test_cmd:
            _, ok = run_command(test_cmd, timeout=60, cwd=project_path)
            state["lastRunPassed"] = ok

    return state


def gather_build_state(project_type: ProjectType, project_path: Path = None) -> Dict[str, Any]:
    """
    Check build tool and build status.

    Args:
        project_type: Detected project type with build tool
        project_path: Path to project directory

    Returns:
        Build state dictionary
    """
    if project_path is None:
        project_path = Path.cwd()

    state = {
        "buildTool": project_type.build_tool,
        "buildScriptExists": False,
    }

    if not project_type.build_tool:
        return state

    # Check if build script/command exists
    if project_type.primary_language in ("JavaScript", "TypeScript"):
        # Check package.json for build script
        package_json = project_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json, encoding="utf-8") as f:
                    pkg = json.load(f)
                    state["buildScriptExists"] = "build" in pkg.get("scripts", {})
            except Exception:
                pass
    elif project_type.build_tool:
        # Other languages: assume build tool exists if specified
        state["buildScriptExists"] = True

    return state


def capture_generic_project_state(
    project_path: str = ".", skip_tests: bool = False, skip_services: bool = False
) -> Dict[str, Any]:
    """
    Capture complete project state for any project type.

    This is the main entry point for generic state capture.

    Args:
        project_path: Path to project directory
        skip_tests: Skip test execution (faster)
        skip_services: Skip service checks

    Returns:
        Complete project state dictionary with:
        - projectType: Detected project type info
        - git: Git repository state
        - dependencies: Dependency health
        - services: Running services (if not skipped)
        - tests: Test framework and status (if not skipped)
        - build: Build tool and status
        - timestamp: Capture timestamp

    Example:
        >>> state = capture_generic_project_state()
        >>> print(f"Language: {state['projectType']['language']}")
        >>> print(f"Uncommitted files: {state['git']['uncommittedFiles']}")
        >>> print(f"Dependencies installed: {state['dependencies']['installed']}")
    """
    path = Path(project_path).resolve()

    # Detect project type
    if HAS_PROJECT_DETECTOR:
        detector = GenericProjectDetector(str(path))
        project_type = detector.detect()
    else:
        # Fallback: minimal state with just git
        return {
            "projectType": {"language": "Unknown", "packageManager": None},
            "git": gather_git_state(path),
            "dependencies": {"installed": False, "outdatedCount": 0},
            "services": {"runningServices": [], "missingServices": []},
            "tests": {"testsExist": False},
            "build": {"buildScriptExists": False},
            "timestamp": datetime.now().isoformat(),
        }

    # Gather all state
    state = {
        "projectType": {
            "language": project_type.primary_language,
            "packageManager": project_type.package_manager,
            "testFramework": project_type.test_framework,
            "buildTool": project_type.build_tool,
            "linter": project_type.linter,
            "formatter": project_type.formatter,
        },
        "git": gather_git_state(path),
        "dependencies": gather_dependency_state(project_type, path),
        "services": (gather_service_state(project_type, path) if not skip_services else {}),
        "tests": gather_test_state(project_type, path, skip_tests),
        "build": gather_build_state(project_type, path),
        "timestamp": datetime.now().isoformat(),
    }

    return state


# Convenience alias matching existing API
capture_project_state = capture_generic_project_state
