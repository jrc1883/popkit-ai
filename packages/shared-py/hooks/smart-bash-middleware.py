#!/usr/bin/env python3
"""
Smart Bash Middleware - PreToolUse Hook

Purpose: Detect dangerous bash commands and automatically add safety flags.
Scope: Global (all agents)
Trigger: PreToolUse
Once: false (runs on every Bash tool use)

This hook detects dangerous bash commands and automatically modifies them
to include safety flags (like --dry-run) while still requesting user consent.
Demonstrates the updatedInput feature of Claude Code 2.1.0.
"""

import json
import sys
import re


# Dangerous commands that should be protected
DANGEROUS_COMMANDS = [
    {
        "pattern": r"rm\s+-rf\s+/",
        "name": "rm -rf /",
        "description": "Recursive force delete from root",
        "severity": "critical"
    },
    {
        "pattern": r"git\s+push\s+--force",
        "name": "git push --force",
        "description": "Force push to remote repository",
        "severity": "high"
    },
    {
        "pattern": r"dd\s+if=",
        "name": "dd if=",
        "description": "Low-level disk operations",
        "severity": "critical"
    },
    {
        "pattern": r"mkfs\.",
        "name": "mkfs.",
        "description": "Format filesystem",
        "severity": "critical"
    },
    {
        "pattern": r":\(\)\{\s*:\|:&\s*\};:",
        "name": ":(){ :|:& };:",
        "description": "Fork bomb",
        "severity": "critical"
    },
    {
        "pattern": r">\s*/dev/sd[a-z]",
        "name": "> /dev/sd*",
        "description": "Direct write to disk device",
        "severity": "critical"
    },
    {
        "pattern": r"chmod\s+-R\s+777\s+/",
        "name": "chmod -R 777 /",
        "description": "Recursive permission change from root",
        "severity": "high"
    },
    {
        "pattern": r"npm\s+install\s+-g\s+.*\s+--unsafe-perm",
        "name": "npm install -g --unsafe-perm",
        "description": "Unsafe global npm install",
        "severity": "medium"
    }
]


def detect_dangerous_command(command):
    """
    Detect if a command contains dangerous patterns.

    Returns: (is_dangerous, match_info) where match_info is:
        {
            "pattern": str,
            "name": str,
            "description": str,
            "severity": str
        }
    """
    for danger in DANGEROUS_COMMANDS:
        if re.search(danger["pattern"], command):
            return True, danger

    return False, None


def add_safety_flags(command, danger_info):
    """
    Attempt to add safety flags to dangerous commands.

    Returns: (modified_command, was_modified)
    """
    # For git push --force, suggest --force-with-lease instead
    if "git push --force" in command:
        modified = command.replace("--force", "--force-with-lease --dry-run")
        return modified, True

    # For rm commands, add --dry-run if supported (GNU coreutils)
    if re.search(r"rm\s+-rf", command):
        # Can't easily add --dry-run to rm, so we'll just warn
        return command, False

    # For dd commands, add status=progress
    if "dd if=" in command:
        if "status=" not in command:
            modified = command + " status=progress"
            return modified, True
        return command, False

    # For chmod, we can't add safety flag, just warn
    if "chmod" in command:
        return command, False

    # Default: no modification
    return command, False


def handle_pre_tool_use(data):
    """
    Detect dangerous bash commands and request consent with safety modifications.

    Args:
        data: {
            "tool": "Bash" | other,
            "input": {
                "command": str,
                "description": str,
                ...
            }
        }

    Returns:
        {
            "decision": "allow" | "deny" | "ask",
            "message": "Explanation",
            "updatedInput": {  # Only if decision is "ask"
                "command": "Modified command",
                "description": "Modified description"
            }
        }
    """
    tool = data.get("tool", "")

    # Only process Bash commands
    if tool != "Bash":
        return {"decision": "allow"}

    tool_input = data.get("input", {})
    command = tool_input.get("command", "")
    description = tool_input.get("description", "")

    # Detect dangerous patterns
    is_dangerous, danger_info = detect_dangerous_command(command)

    if not is_dangerous:
        return {"decision": "allow"}

    # Critical severity commands should be denied outright
    if danger_info["severity"] == "critical":
        return {
            "decision": "deny",
            "message": f"CRITICAL: Dangerous command '{danger_info['name']}' detected - {danger_info['description']}. Command blocked for safety."
        }

    # For high/medium severity, try to add safety flags
    modified_command, was_modified = add_safety_flags(command, danger_info)

    if was_modified:
        # Use updatedInput to modify the command and request consent
        return {
            "decision": "ask",
            "message": f"Dangerous command '{danger_info['name']}' detected - {danger_info['description']}. Auto-added safety flags. Please review before proceeding.",
            "updatedInput": {
                "command": modified_command,
                "description": f"[PROTECTED] {description}" if description else "[PROTECTED] Dangerous command with safety flags"
            }
        }
    else:
        # Can't modify, just request consent
        return {
            "decision": "ask",
            "message": f"Dangerous command '{danger_info['name']}' detected - {danger_info['description']}. Manual approval required."
        }


if __name__ == "__main__":
    try:
        # Read input from stdin
        data = json.loads(sys.stdin.read())

        # Process the hook
        result = handle_pre_tool_use(data)

        # Write output to stdout
        print(json.dumps(result))
        sys.exit(0)

    except Exception as e:
        # On error, allow the operation but log the error
        error_result = {
            "decision": "allow",
            "message": f"Hook error (allowing operation): {str(e)}"
        }
        print(json.dumps(error_result))
        sys.exit(0)
