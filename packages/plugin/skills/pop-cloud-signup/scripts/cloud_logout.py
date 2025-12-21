#!/usr/bin/env python3
"""
PopKit Cloud Logout Helper

Removes cloud configuration and provides cleanup instructions.
Used by /popkit:cloud logout command.
"""

import platform
import sys
from pathlib import Path

# Import from cloud_auth
sys.path.insert(0, str(Path(__file__).parent))
from cloud_auth import CONFIG_PATH, remove_config, check_existing_config


def get_logout_instructions() -> str:
    """
    Get OS-specific instructions for unsetting POPKIT_API_KEY.

    Returns:
        Formatted instructions string
    """
    os_type = platform.system()

    if os_type == "Windows":
        return """
To complete logout, unset your environment variable:

Windows PowerShell:
  Remove-Item Env:POPKIT_API_KEY

Windows CMD:
  set POPKIT_API_KEY=

To remove from system permanently:
  [System.Environment]::SetEnvironmentVariable('POPKIT_API_KEY', $null, 'User')
"""
    elif os_type == "Darwin":
        return """
To complete logout, unset your environment variable:

macOS (zsh):
  unset POPKIT_API_KEY

To remove from shell config:
  # Edit ~/.zshrc and remove the POPKIT_API_KEY line
  # Then restart your terminal
"""
    else:  # Linux
        return """
To complete logout, unset your environment variable:

Linux (bash):
  unset POPKIT_API_KEY

To remove from shell config:
  # Edit ~/.bashrc and remove the POPKIT_API_KEY line
  # Then restart your terminal
"""


def logout() -> dict:
    """
    Logout from PopKit Cloud.

    Returns:
        Dict with logout status and instructions
    """
    # Check if logged in
    existing_config = check_existing_config()

    if not existing_config:
        return {
            "was_logged_in": False,
            "message": "Not logged in to PopKit Cloud",
            "suggestion": "Nothing to do."
        }

    # Remove config
    was_removed = remove_config()

    return {
        "was_logged_in": True,
        "config_removed": was_removed,
        "config_path": str(CONFIG_PATH),
        "instructions": get_logout_instructions(),
        "fallback_info": """
Power Mode will now use:
  1. Local Redis (if Docker running)
  2. File-based fallback (if not)

To login again: /popkit:cloud login
"""
    }


def format_logout_output(result: dict) -> str:
    """
    Format logout result for display.

    Args:
        result: Dict from logout()

    Returns:
        Formatted output string
    """
    if not result['was_logged_in']:
        return f"""
{result['message']}

You are not currently connected to PopKit Cloud.

To login: /popkit:cloud login
To signup: /popkit:cloud signup
"""

    output = f"""
Logged out from PopKit Cloud

Removed: {result['config_path']}
{result['instructions']}
{result['fallback_info']}
"""
    return output


# CLI interface
if __name__ == "__main__":
    result = logout()
    print(format_logout_output(result))

    sys.exit(0)
