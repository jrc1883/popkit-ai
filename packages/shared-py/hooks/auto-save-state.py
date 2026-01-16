#!/usr/bin/env python3
"""
Session Capture Skill - Stop Hook

Purpose: Auto-save session state when skill completes.
Scope: Skill-scoped (session-capture skill only)
Trigger: Stop
Once: true (runs only once at skill completion)

This hook automatically saves the session state to STATUS.json when the
session-capture skill completes, ensuring state is persisted.
"""

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_git_state(cwd):
    """Get current git state."""
    try:
        # Get current branch
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], cwd=cwd, text=True, stderr=subprocess.DEVNULL
        ).strip()

        # Get last commit
        last_commit = subprocess.check_output(
            ["git", "log", "-1", "--format=%h - %s"], cwd=cwd, text=True, stderr=subprocess.DEVNULL
        ).strip()

        # Count uncommitted files
        status_output = subprocess.check_output(
            ["git", "status", "--porcelain"], cwd=cwd, text=True, stderr=subprocess.DEVNULL
        )
        uncommitted_files = len(status_output.strip().split("\n")) if status_output.strip() else 0

        # Count staged files
        staged_output = subprocess.check_output(
            ["git", "diff", "--cached", "--name-only"],
            cwd=cwd,
            text=True,
            stderr=subprocess.DEVNULL,
        )
        staged_files = len(staged_output.strip().split("\n")) if staged_output.strip() else 0

        return {
            "branch": branch,
            "lastCommit": last_commit,
            "uncommittedFiles": uncommitted_files,
            "stagedFiles": staged_files,
        }

    except Exception as e:
        return {
            "branch": "unknown",
            "lastCommit": "unknown",
            "uncommittedFiles": 0,
            "stagedFiles": 0,
            "error": str(e),
        }


def get_project_name(cwd):
    """Get project name from directory or package.json."""
    cwd_path = Path(cwd)

    # Try package.json
    package_json = cwd_path / "package.json"
    if package_json.exists():
        try:
            with open(package_json) as f:
                data = json.load(f)
                return data.get("name", cwd_path.name)
        except:
            pass

    # Try pyproject.toml
    pyproject = cwd_path / "pyproject.toml"
    if pyproject.exists():
        try:
            with open(pyproject) as f:
                for line in f:
                    if line.startswith("name"):
                        return line.split("=")[1].strip().strip('"').strip("'")
        except:
            pass

    # Fall back to directory name
    return cwd_path.name


def save_status_json(cwd, data):
    """Save STATUS.json to .claude/ or project root."""
    cwd_path = Path(cwd)

    # Try .claude directory first
    claude_dir = cwd_path / ".claude"
    if claude_dir.exists() and claude_dir.is_dir():
        status_path = claude_dir / "STATUS.json"
    else:
        # Fall back to project root
        status_path = cwd_path / "STATUS.json"

    try:
        with open(status_path, "w") as f:
            json.dump(data, f, indent=2)

        return str(status_path), None

    except Exception as e:
        return None, str(e)


def handle_stop_hook(data):
    """
    Auto-save session state to STATUS.json.

    Args:
        data: {
            "skill": "session-capture",
            "context": {...}
        }

    Returns:
        {
            "decision": "allow",
            "message": "Optional status message"
        }
    """
    # Determine working directory
    cwd = os.getcwd()

    # Get git state
    git_state = get_git_state(cwd)

    # Get project name
    project_name = get_project_name(cwd)

    # Build STATUS.json content
    status_data = {
        "lastUpdate": datetime.utcnow().isoformat() + "Z",
        "project": project_name,
        "sessionType": "Captured",
        "git": git_state,
        "tasks": {"inProgress": [], "completed": [], "blocked": []},
        "services": {},
        "context": {
            "focusArea": "Session captured via auto-save hook",
            "blocker": None,
            "nextAction": "Resume session",
            "keyDecisions": [],
        },
        "projectData": {},
    }

    # Save STATUS.json
    status_path, error = save_status_json(cwd, status_data)

    if error:
        return {"decision": "allow", "message": f"Failed to save STATUS.json: {error}"}

    return {"decision": "allow", "message": f"Session state auto-saved to {status_path}"}


if __name__ == "__main__":
    try:
        # Read input from stdin
        data = json.loads(sys.stdin.read())

        # Process the hook
        result = handle_stop_hook(data)

        # Write output to stdout
        print(json.dumps(result))
        sys.exit(0)

    except Exception as e:
        # On error, allow the operation
        error_result = {"decision": "allow", "message": f"Hook error (state not saved): {str(e)}"}
        print(json.dumps(error_result))
        sys.exit(0)
