#!/usr/bin/env python3
"""
Security Auditor Agent - PreToolUse Hook

Purpose: Block dangerous commands before execution when running security audits.
Scope: Agent-scoped (security-auditor only)
Trigger: PreToolUse
Once: false (runs on every tool use)

This hook prevents the security-auditor agent from accidentally executing
dangerous commands while performing security assessments.
"""

import json
import sys


# Dangerous commands that should be blocked during security audits
DANGEROUS_COMMANDS = [
    "rm -rf /",
    "dd if=/dev/zero",
    "mkfs.",
    ":(){ :|:& };:",  # Fork bomb
    "> /dev/sda",
    "mv / /dev/null",
    "chmod -R 777 /",
    "wget http://",  # Downloading arbitrary scripts
    "curl http://",  # Downloading arbitrary scripts
]

# Sensitive files that shouldn't be read during automated audits
PROTECTED_FILES = [
    ".env",
    "secrets.json",
    "credentials.json",
    "id_rsa",
    "id_ecdsa",
    "id_ed25519",
    ".ssh/",
    "aws_credentials",
]


def is_dangerous_bash_command(command):
    """Check if a bash command is dangerous."""
    command_lower = command.lower()

    for dangerous in DANGEROUS_COMMANDS:
        if dangerous.lower() in command_lower:
            return True, dangerous

    return False, None


def is_protected_file(file_path):
    """Check if a file path contains protected/sensitive files."""
    if not file_path:
        return False, None

    file_path_lower = file_path.lower()

    for protected in PROTECTED_FILES:
        if protected.lower() in file_path_lower:
            return True, protected

    return False, None


def handle_pre_tool_use(data):
    """
    Validate tool use before execution.

    Args:
        data: {
            "tool": "Bash" | "Read" | "Write" | etc.,
            "input": {...},
            "agent": "security-auditor"
        }

    Returns:
        {
            "decision": "allow" | "deny" | "ask",
            "message": "Optional explanation"
        }
    """
    tool = data.get("tool", "")
    tool_input = data.get("input", {})

    # Validate Bash commands
    if tool == "Bash":
        command = tool_input.get("command", "")

        is_dangerous, dangerous_pattern = is_dangerous_bash_command(command)
        if is_dangerous:
            return {
                "decision": "deny",
                "message": f"Security auditor blocked dangerous command: '{dangerous_pattern}' detected in: {command[:100]}",
            }

    # Validate file access
    if tool in ["Read", "Write", "Edit"]:
        file_path = tool_input.get("file_path", "")

        is_protected, protected_pattern = is_protected_file(file_path)
        if is_protected:
            return {
                "decision": "ask",
                "message": f"Security auditor detected access to protected file pattern '{protected_pattern}' in: {file_path}. Manual approval required.",
            }

    # Validate WebFetch (prevent SSRF)
    if tool == "WebFetch":
        url = tool_input.get("url", "")

        # Block localhost/internal IPs during automated audits
        internal_patterns = ["localhost", "127.0.0.1", "0.0.0.0", "192.168.", "10.", "172.16."]
        for pattern in internal_patterns:
            if pattern in url.lower():
                return {
                    "decision": "ask",
                    "message": f"Security auditor detected internal URL: {url}. This could be SSRF. Manual approval required.",
                }

    # Allow all other operations
    return {"decision": "allow"}


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
            "message": f"Hook error (allowing operation): {str(e)}",
        }
        print(json.dumps(error_result))
        sys.exit(0)
