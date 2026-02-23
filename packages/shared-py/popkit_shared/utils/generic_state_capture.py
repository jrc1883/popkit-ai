#!/usr/bin/env python3
"""
Generic State Capture for Any Project Type.

Captures project state for morning/nightly routines, adapting to
detected project type (Node.js, Python, Rust, Go, Ruby, Java, .NET).

Issue #69: Generic Workspace Routine Templates
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from .subprocess_utils import run_command_simple

try:
    from .generic_project_detector import ProjectType
    from .project_config import get_project_type_with_cache

    HAS_PROJECT_DETECTOR = True
except ImportError:
    HAS_PROJECT_DETECTOR = False
    get_project_type_with_cache = None


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
        "last_commit": "",
        "uncommitted_files": 0,
        "staged_files": 0,
        "modified_files": [],
        "untracked_files": [],
        "behind_remote": 0,
        "ahead_remote": 0,
        "stashes": 0,
    }

    # Get current branch
    branch, ok = run_command_simple("git branch --show-current", cwd=project_path)
    if ok:
        state["branch"] = branch

    # Get last commit
    commit, ok = run_command_simple("git log -1 --format='%h - %s'", cwd=project_path)
    if ok:
        state["last_commit"] = commit

    # Count uncommitted changes
    status, ok = run_command_simple("git status --porcelain", cwd=project_path)
    if ok:
        lines = [line for line in status.split("\n") if line.strip()]
        state["uncommitted_files"] = len(lines)

        for line in lines:
            if line.startswith("??"):
                state["untracked_files"].append(line[3:].strip())
            else:
                state["modified_files"].append(line[3:].strip())

    # Count staged files
    staged, ok = run_command_simple("git diff --cached --name-only", cwd=project_path)
    if ok:
        staged_files = [f for f in staged.split("\n") if f.strip()]
        state["staged_files"] = len(staged_files)

    # Check remote sync status
    fetch_output, _ = run_command_simple("git fetch --dry-run", cwd=project_path)
    rev_list, ok = run_command_simple(
        "git rev-list --left-right --count HEAD...@{u}", cwd=project_path
    )
    if ok and "\t" in rev_list:
        ahead, behind = rev_list.split("\t")
        state["ahead_remote"] = int(ahead)
        state["behind_remote"] = int(behind)

    # Count stashes
    stash_list, ok = run_command_simple("git stash list", cwd=project_path)
    if ok:
        state["stashes"] = len([s for s in stash_list.split("\n") if s.strip()])

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
        "package_manager": project_type.package_manager,
        "installed": False,
        "outdated_count": 0,
        "outdated_packages": [],
    }

    if not project_type.check_installed:
        return state

    # Check if dependencies are installed
    output, ok = run_command_simple(project_type.check_installed, timeout=10, cwd=project_path)
    state["installed"] = ok

    # Check for outdated dependencies
    if project_type.check_outdated:
        outdated, ok = run_command_simple(project_type.check_outdated, timeout=30, cwd=project_path)
        if ok and outdated:
            # Parse output based on package manager
            if project_type.package_manager in ("npm", "pnpm", "yarn"):
                # npm/pnpm outdated format
                lines = [line for line in outdated.split("\n") if line.strip()]
                state["outdated_count"] = max(0, len(lines) - 1)  # Exclude header
                state["outdated_packages"] = lines[1:6]  # First 5 packages
            elif project_type.package_manager == "pip":
                # pip list --outdated format
                lines = [line for line in outdated.split("\n") if line.strip()]
                state["outdated_count"] = max(0, len(lines) - 2)  # Exclude headers
                state["outdated_packages"] = lines[2:7]  # First 5 packages
            else:
                # Generic: count non-empty lines
                lines = [line for line in outdated.split("\n") if line.strip()]
                state["outdated_count"] = len(lines)
                state["outdated_packages"] = lines[:5]

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
        project_path: Path to project directory

    Returns:
        Service state dictionary
    """
    if project_path is None:
        project_path = Path.cwd()

    state = {
        "expected_services": [],
        "running_services": [],
        "missing_services": [],
    }

    # Check for config overrides first
    try:
        from .project_config import ProjectConfig

        config_manager = ProjectConfig(str(project_path))
        override_services = config_manager.get_override("expected_services")

        # Use override if available, otherwise use project type defaults
        expected_services = (
            override_services if override_services else project_type.expected_services
        )
    except (ImportError, Exception):
        expected_services = project_type.expected_services

    if not expected_services:
        return state

    for service in expected_services:
        service_info = {
            "name": service["name"],
            "port": service["port"],
            "description": service.get("description", ""),
        }
        state["expected_services"].append(service_info)

        if check_service_running(service["port"]):
            state["running_services"].append(service_info)
        else:
            state["missing_services"].append(service_info)

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
        "test_framework": project_type.test_framework,
        "tests_exist": False,
        "last_run_passed": None,  # None = unknown, True/False = known status
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
        state["tests_exist"] = len(test_files) > 0

    # Optionally run tests (expensive, usually skipped in quick mode)
    if not skip_tests and state["tests_exist"]:
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
            _, ok = run_command_simple(test_cmd, timeout=60, cwd=project_path)
            state["last_run_passed"] = ok

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
        "build_tool": project_type.build_tool,
        "build_script_exists": False,
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
                    state["build_script_exists"] = "build" in pkg.get("scripts", {})
            except Exception:
                # Ignore errors reading package.json - build_script_exists defaults to False
                pass
    elif project_type.build_tool:
        # Other languages: assume build tool exists if specified
        state["build_script_exists"] = True

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

    # Detect project type with caching
    if HAS_PROJECT_DETECTOR and get_project_type_with_cache:
        project_type = get_project_type_with_cache(str(path))

        if not project_type:
            # Fallback: minimal state with just git
            print("[WARN] Project detection failed, using minimal state")
            return {
                "project_type": {"language": "Unknown", "package_manager": None},
                "git": gather_git_state(path),
                "dependencies": {"installed": False, "outdated_count": 0},
                "services": {"running_services": [], "missing_services": []},
                "tests": {"tests_exist": False},
                "build": {"build_script_exists": False},
                "timestamp": datetime.now().isoformat(),
            }
    else:
        # Fallback: minimal state with just git
        return {
            "project_type": {"language": "Unknown", "package_manager": None},
            "git": gather_git_state(path),
            "dependencies": {"installed": False, "outdated_count": 0},
            "services": {"running_services": [], "missing_services": []},
            "tests": {"tests_exist": False},
            "build": {"build_script_exists": False},
            "timestamp": datetime.now().isoformat(),
        }

    # Gather all state
    state = {
        "project_type": {
            "language": project_type.primary_language,
            "package_manager": project_type.package_manager,
            "test_framework": project_type.test_framework,
            "build_tool": project_type.build_tool,
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
