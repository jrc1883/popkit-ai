#!/usr/bin/env python3
"""
StopFailure Hook
Fires on API errors (rate limit, auth failure, server error, etc.).

Added in Claude Code 2.1.78. This hook captures session state before
the session terminates unexpectedly, so the next session can recover.

Responsibilities:
1. Read error info from the event payload (stdin JSON)
2. Auto-capture session state to STATUS.json
3. Write error entry to .claude/popkit/error-log.json (capped at 20)
4. Log: timestamp, error type, what was in progress, git branch

Design constraints:
- Must be FAST (< 3 seconds) -- session is terminating
- No network calls, no heavy computation
- Only git branch + STATUS.json snapshot
- stdlib only (json, sys, pathlib, datetime, subprocess)
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_git_branch():
    """Get current git branch name.

    Lightweight -- just the branch name, nothing else.
    """
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return ""


def get_git_last_commit():
    """Get the last commit hash and message."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%h - %s"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return ""


def capture_session_state(error_info, branch, last_commit):
    """Write/update STATUS.json with error context.

    Merges error info into existing STATUS.json so the next session
    knows what happened and where the previous session left off.
    """
    status_file = Path.cwd() / ".claude" / "STATUS.json"

    # Read existing status
    status = {}
    if status_file.exists():
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                status = json.load(f)
        except (json.JSONDecodeError, OSError):
            status = {}

    # Update git snapshot
    status["git"] = {
        "branch": branch,
        "lastCommit": last_commit,
    }

    # Mark the abnormal termination
    status["lastFailure"] = {
        "timestamp": datetime.now().isoformat() + "Z",
        "errorType": error_info.get(
            "error_type", error_info.get("errorType", "unknown")
        ),
        "errorMessage": error_info.get(
            "error_message", error_info.get("errorMessage", "")
        ),
        "recoverable": error_info.get("recoverable", True),
    }

    status["lastUpdate"] = datetime.now().isoformat() + "Z"
    status["terminatedAbnormally"] = True

    try:
        status_file.parent.mkdir(parents=True, exist_ok=True)
        with open(status_file, "w", encoding="utf-8") as f:
            json.dump(status, f, indent=2)
    except OSError as e:
        print(f"  Warning: failed to update STATUS.json: {e}", file=sys.stderr)


def write_error_log(entry):
    """Append error entry to .claude/popkit/error-log.json.

    Keeps the last 20 entries to avoid unbounded growth.
    """
    log_dir = Path.cwd() / ".claude" / "popkit"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "error-log.json"

    entries = []
    if log_file.exists():
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                entries = json.load(f)
        except (json.JSONDecodeError, OSError):
            entries = []

    entries.append(entry)

    # Cap at 20 entries
    if len(entries) > 20:
        entries = entries[-20:]

    try:
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)
    except OSError as e:
        print(f"  Warning: failed to write error log: {e}", file=sys.stderr)


def extract_error_type(input_data):
    """Extract a human-readable error type from the event payload.

    Claude Code 2.1.78 passes error details in the StopFailure payload.
    The exact shape may vary, so we try multiple fields.
    """
    # Try known field names
    for key in ["error_type", "errorType", "type", "code"]:
        val = input_data.get(key)
        if val:
            return str(val)

    # Try nested error object
    error_obj = input_data.get("error", {})
    if isinstance(error_obj, dict):
        for key in ["type", "code", "status"]:
            val = error_obj.get(key)
            if val:
                return str(val)

    return "unknown"


def extract_error_message(input_data):
    """Extract a human-readable error message from the event payload."""
    # Try known field names
    for key in ["error_message", "errorMessage", "message", "reason"]:
        val = input_data.get(key)
        if val:
            return str(val)

    # Try nested error object
    error_obj = input_data.get("error", {})
    if isinstance(error_obj, dict):
        for key in ["message", "reason", "description"]:
            val = error_obj.get(key)
            if val:
                return str(val)

    return ""


def extract_in_progress(input_data):
    """Extract what was in progress when the failure occurred.

    Checks STATUS.json currentTask and the event payload for context.
    """
    # Check event payload for tool/action context
    in_progress = []

    tool_name = input_data.get("tool_name") or input_data.get("toolName", "")
    if tool_name:
        in_progress.append(f"tool: {tool_name}")

    # Read STATUS.json for current task
    status_file = Path.cwd() / ".claude" / "STATUS.json"
    if status_file.exists():
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                status = json.load(f)
            current_task = status.get("currentTask") or status.get("current_task")
            if current_task:
                if isinstance(current_task, dict):
                    desc = current_task.get("description") or current_task.get(
                        "name", ""
                    )
                    if desc:
                        in_progress.append(f"task: {desc}")
                elif isinstance(current_task, str):
                    in_progress.append(f"task: {current_task}")
        except (json.JSONDecodeError, OSError):
            pass

    return "; ".join(in_progress) if in_progress else "unknown"


def main():
    """Main entry point -- JSON stdin/stdout protocol."""
    try:
        input_text = sys.stdin.read()
        input_data = json.loads(input_text) if input_text.strip() else {}

        # Extract error details
        error_type = extract_error_type(input_data)
        error_message = extract_error_message(input_data)
        in_progress = extract_in_progress(input_data)

        # Get git state
        branch = get_git_branch()
        last_commit = get_git_last_commit()

        # Auto-capture session state to STATUS.json
        capture_session_state(input_data, branch, last_commit)

        # Build error log entry
        error_entry = {
            "timestamp": datetime.now().isoformat() + "Z",
            "error_type": error_type,
            "error_message": error_message,
            "in_progress": in_progress,
            "git_branch": branch,
            "git_commit": last_commit,
            "raw_payload_keys": list(input_data.keys()) if input_data else [],
        }

        # Write to error log
        write_error_log(error_entry)

        # Log to stderr
        branch_info = f" on {branch}" if branch else ""
        print(
            f"  StopFailure: {error_type}{branch_info} - {error_message[:80]}",
            file=sys.stderr,
        )
        print(
            f"  In progress: {in_progress}",
            file=sys.stderr,
        )

        # Output JSON response
        response = {
            "status": "success",
            "message": f"Error state captured: {error_type}",
            "timestamp": datetime.now().isoformat(),
            "error_logged": True,
            "status_updated": True,
        }
        print(json.dumps(response))

    except json.JSONDecodeError:
        # Even with bad input, log what we can
        response = {
            "status": "success",
            "message": "StopFailure hook completed (no parseable input)",
            "timestamp": datetime.now().isoformat(),
        }
        print(json.dumps(response))
    except Exception as e:
        response = {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
        print(json.dumps(response))
        print(f"Error in stop-failure hook: {e}", file=sys.stderr)
        sys.exit(0)  # Never block on hook errors


if __name__ == "__main__":
    main()
