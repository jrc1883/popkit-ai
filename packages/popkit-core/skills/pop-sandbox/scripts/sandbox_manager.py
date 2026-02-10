#!/usr/bin/env python3
"""
E2B Sandbox Manager for PopKit Native Swarm

Provides ephemeral, isolated environments for safe parallel code execution.
Essential for multi-agent swarms to avoid local file conflicts.

Usage:
    python sandbox_manager.py <action> [args...]

Actions:
    sandbox_create [template] [timeout]  - Create new sandbox
    sandbox_run_command <id> <cmd>       - Execute command in sandbox
    sandbox_write_file <id> <path> <content> - Write file to sandbox
    sandbox_read_file <id> <path>        - Read file from sandbox
    sandbox_list                         - List active sandboxes
    sandbox_kill <id>                    - Terminate sandbox
"""

import sys
import json
import os
from datetime import datetime

try:
    from e2b_code_interpreter import Sandbox
except ImportError:
    Sandbox = None

# Track active sandboxes - use cross-platform temp directory
if os.name == "nt":  # Windows
    STATE_FILE = os.path.join(
        os.environ.get("TEMP", "C:\\Temp"), "popkit_active_sandboxes.json"
    )
else:  # Unix/Linux/Mac
    STATE_FILE = "/tmp/popkit_active_sandboxes.json"


def load_state():
    """Load sandbox state from persistent storage."""
    if not os.path.exists(STATE_FILE):
        return {}
    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def save_state(state):
    """Save sandbox state to persistent storage."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True) if os.path.dirname(
        STATE_FILE
    ) else None
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def create_sandbox(template="base", timeout=300):
    """
    Create a new ephemeral E2B sandbox environment.

    Args:
        template: Environment template (default: "base" which uses E2B default)
        timeout: Sandbox timeout in seconds (default: 300)

    Returns:
        sandbox_id: Unique identifier for the created sandbox
    """
    if Sandbox is None:
        return {
            "error": "e2b-code-interpreter not installed. Run: pip install e2b-code-interpreter"
        }

    try:
        # Initialize E2B Sandbox with optional template
        sbx = Sandbox(
            template=template if template != "base" else None, timeout=timeout
        )

        state = load_state()
        state[sbx.sandbox_id] = {
            "id": sbx.sandbox_id,
            "template": template,
            "timeout": timeout,
            "created_at": datetime.utcnow().isoformat(),
            "alive": True,
        }
        save_state(state)

        return sbx.sandbox_id
    except Exception as e:
        return {"error": str(e)}


def run_command(sandbox_id, cmd, background=False):
    """
    Execute a shell command inside a sandbox.

    Args:
        sandbox_id: Target sandbox ID
        cmd: Shell command to execute
        background: If True, run without waiting for completion

    Returns:
        Dict with stdout, stderr, exit_code (or error)
    """
    if Sandbox is None:
        return {"error": "e2b-code-interpreter not installed"}

    try:
        sbx = Sandbox.connect(sandbox_id)
        if background:
            # Fire and forget - useful for long-running processes
            sbx.commands.run(cmd, background=True)
            return {"status": "started", "background": True}
        else:
            exec_result = sbx.commands.run(cmd)
            return {
                "stdout": exec_result.stdout,
                "stderr": exec_result.stderr,
                "exit_code": exec_result.exit_code,
            }
    except Exception as e:
        # Mark as potentially dead in state
        state = load_state()
        if sandbox_id in state:
            state[sandbox_id]["alive"] = False
            save_state(state)
        return {"error": str(e)}


def write_file(sandbox_id, path, content):
    """
    Write content to a file inside the sandbox.

    Args:
        sandbox_id: Target sandbox ID
        path: File path inside sandbox (e.g., "/home/user/app.py")
        content: Text content to write

    Returns:
        "Success" or error message
    """
    if Sandbox is None:
        return "Error: e2b-code-interpreter not installed"

    try:
        sbx = Sandbox.connect(sandbox_id)
        sbx.files.write(path, content)
        return "Success"
    except Exception as e:
        return f"Error: {str(e)}"


def read_file(sandbox_id, path):
    """
    Read content from a file inside the sandbox.

    Args:
        sandbox_id: Target sandbox ID
        path: File path inside sandbox

    Returns:
        File content or error message
    """
    if Sandbox is None:
        return {"error": "e2b-code-interpreter not installed"}

    try:
        sbx = Sandbox.connect(sandbox_id)
        content = sbx.files.read(path)
        return {"content": content, "path": path}
    except Exception as e:
        return {"error": str(e)}


def list_sandboxes():
    """
    List all active sandboxes managed by this session.

    Returns:
        JSON list of active sandboxes with their metadata
    """
    state = load_state()

    # Filter to only alive sandboxes and verify connectivity
    active = []
    updated_state = {}

    for sid, info in state.items():
        if info.get("alive", False):
            # Optionally verify sandbox is still running
            if Sandbox is not None:
                try:
                    Sandbox.connect(sid)  # Verify connectivity (throws if dead)
                    info["status"] = "connected"
                    active.append(info)
                    updated_state[sid] = info
                except Exception:
                    info["alive"] = False
                    info["status"] = "disconnected"
            else:
                active.append(info)
                updated_state[sid] = info

    save_state(updated_state)
    return active


def kill_sandbox(sandbox_id):
    """
    Terminate a specific sandbox.

    Args:
        sandbox_id: The sandbox ID to terminate

    Returns:
        Confirmation status
    """
    if Sandbox is None:
        return {"error": "e2b-code-interpreter not installed", "killed": False}

    try:
        sbx = Sandbox.connect(sandbox_id)
        sbx.kill()

        # Update state
        state = load_state()
        if sandbox_id in state:
            state[sandbox_id]["alive"] = False
            state[sandbox_id]["killed_at"] = datetime.utcnow().isoformat()
            save_state(state)

        return {"sandbox_id": sandbox_id, "killed": True}
    except Exception as e:
        # Still mark as dead in state
        state = load_state()
        if sandbox_id in state:
            state[sandbox_id]["alive"] = False
            save_state(state)
        return {"sandbox_id": sandbox_id, "killed": False, "error": str(e)}


def main():
    if len(sys.argv) < 2:
        print(
            json.dumps(
                {
                    "error": "No command provided",
                    "usage": "python sandbox_manager.py <action> [args...]",
                    "actions": [
                        "sandbox_create",
                        "sandbox_run_command",
                        "sandbox_write_file",
                        "sandbox_read_file",
                        "sandbox_list",
                        "sandbox_kill",
                    ],
                }
            )
        )
        return

    action = sys.argv[1]

    if action == "sandbox_create":
        template = sys.argv[2] if len(sys.argv) > 2 else "base"
        timeout = int(sys.argv[3]) if len(sys.argv) > 3 else 300
        result = create_sandbox(template, timeout)
        if isinstance(result, dict):
            print(json.dumps(result))
        else:
            print(json.dumps({"sandbox_id": result}))

    elif action == "sandbox_run_command":
        if len(sys.argv) < 4:
            print(
                json.dumps(
                    {"error": "Usage: sandbox_run_command <sandbox_id> <command>"}
                )
            )
            return
        sid = sys.argv[2]
        cmd = sys.argv[3]
        background = len(sys.argv) > 4 and sys.argv[4].lower() == "true"
        result = run_command(sid, cmd, background)
        print(json.dumps(result))

    elif action == "sandbox_write_file":
        if len(sys.argv) < 5:
            print(
                json.dumps(
                    {"error": "Usage: sandbox_write_file <sandbox_id> <path> <content>"}
                )
            )
            return
        sid = sys.argv[2]
        path = sys.argv[3]
        content = sys.argv[4]
        result = write_file(sid, path, content)
        print(json.dumps({"status": result}))

    elif action == "sandbox_read_file":
        if len(sys.argv) < 4:
            print(json.dumps({"error": "Usage: sandbox_read_file <sandbox_id> <path>"}))
            return
        sid = sys.argv[2]
        path = sys.argv[3]
        result = read_file(sid, path)
        print(json.dumps(result))

    elif action == "sandbox_list":
        result = list_sandboxes()
        print(json.dumps({"sandboxes": result, "count": len(result)}))

    elif action == "sandbox_kill":
        if len(sys.argv) < 3:
            print(json.dumps({"error": "Usage: sandbox_kill <sandbox_id>"}))
            return
        sid = sys.argv[2]
        result = kill_sandbox(sid)
        print(json.dumps(result))

    else:
        print(
            json.dumps(
                {
                    "error": f"Unknown action: {action}",
                    "available_actions": [
                        "sandbox_create",
                        "sandbox_run_command",
                        "sandbox_write_file",
                        "sandbox_read_file",
                        "sandbox_list",
                        "sandbox_kill",
                    ],
                }
            )
        )


if __name__ == "__main__":
    main()
