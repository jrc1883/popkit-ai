#!/usr/bin/env python3
"""
PopKit Cloud Authentication Helper

Handles signup, login, and configuration management for PopKit Cloud.
Used by the pop-cloud-signup skill.
"""

import json
import os
import platform
import stat
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Dict, Tuple


# Constants
CLOUD_URL = "https://api.thehouseofdeals.com/v1"
CONFIG_PATH = Path.home() / ".claude" / "popkit" / "cloud-config.json"


class CloudAuthError(Exception):
    """Base exception for cloud authentication errors."""
    pass


class EmailExistsError(CloudAuthError):
    """Email already registered."""
    pass


class InvalidCredentialsError(CloudAuthError):
    """Invalid email or password."""
    pass


class NetworkError(CloudAuthError):
    """Network connectivity error."""
    pass


def check_existing_config() -> Optional[Dict]:
    """
    Check if cloud config already exists.

    Returns:
        Dict with existing config if found, None otherwise
    """
    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None
    return None


def signup(email: str, password: str, name: str = "PopKit User") -> Dict:
    """
    Create a new PopKit Cloud account.

    Args:
        email: User email address
        password: User password (min 8 characters)
        name: User display name

    Returns:
        Dict containing:
            - apiKey: Generated API key
            - userId: User ID
            - tier: Account tier (free/pro/team)
            - email: User email

    Raises:
        EmailExistsError: If email is already registered
        InvalidCredentialsError: If email/password format is invalid
        NetworkError: If cannot connect to cloud
        CloudAuthError: For other API errors
    """
    url = f"{CLOUD_URL}/auth/signup"

    data = json.dumps({
        "email": email,
        "password": password,
        "name": name
    }).encode('utf-8')

    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'PopKit-Plugin/0.2.5'
    }

    request = urllib.request.Request(url, data=data, headers=headers, method='POST')

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))

            return {
                'apiKey': result['apiKey'],
                'userId': result['user']['id'],
                'tier': result['user']['tier'],
                'email': result['user']['email']
            }

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        try:
            error_data = json.loads(error_body)
            error_message = error_data.get('error', {}).get('message', 'Unknown error')
        except json.JSONDecodeError:
            error_message = error_body

        if e.code == 409:
            raise EmailExistsError(f"Email already registered: {email}")
        elif e.code == 400:
            raise InvalidCredentialsError(error_message)
        else:
            raise CloudAuthError(f"API error {e.code}: {error_message}")

    except urllib.error.URLError as e:
        raise NetworkError(f"Cannot connect to PopKit Cloud: {e.reason}")


def login(email: str, password: str) -> Dict:
    """
    Login to existing PopKit Cloud account.

    Args:
        email: User email address
        password: User password

    Returns:
        Dict containing apiKey, userId, tier, email

    Raises:
        InvalidCredentialsError: If credentials are invalid
        NetworkError: If cannot connect to cloud
    """
    url = f"{CLOUD_URL}/auth/login"

    data = json.dumps({
        "email": email,
        "password": password
    }).encode('utf-8')

    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'PopKit-Plugin/0.2.5'
    }

    request = urllib.request.Request(url, data=data, headers=headers, method='POST')

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))

            return {
                'apiKey': result['apiKey'],
                'userId': result['user']['id'],
                'tier': result['user']['tier'],
                'email': result['user']['email']
            }

    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        try:
            error_data = json.loads(error_body)
            error_message = error_data.get('error', {}).get('message', 'Invalid credentials')
        except json.JSONDecodeError:
            error_message = error_body

        if e.code in (401, 403):
            raise InvalidCredentialsError("Invalid email or password")
        else:
            raise CloudAuthError(f"API error {e.code}: {error_message}")

    except urllib.error.URLError as e:
        raise NetworkError(f"Cannot connect to PopKit Cloud: {e.reason}")


def save_config(api_key: str, user_id: str, tier: str, email: str) -> None:
    """
    Save cloud configuration to local file.

    Args:
        api_key: API key
        user_id: User ID
        tier: Account tier
        email: User email

    Security:
        - Sets file permissions to 600 (owner read/write only)
        - Creates parent directories if needed
    """
    # Create directory if needed
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Prepare config
    from datetime import datetime
    config = {
        "apiKey": api_key,
        "userId": user_id,
        "email": email,
        "tier": tier,
        "configuredAt": datetime.now().isoformat(),
        "lastVerified": datetime.now().isoformat()
    }

    # Write config
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config, f, indent=2)

    # Set secure permissions (owner read/write only)
    if platform.system() != "Windows":
        os.chmod(CONFIG_PATH, stat.S_IRUSR | stat.S_IWUSR)  # 600


def remove_config() -> bool:
    """
    Remove cloud configuration file.

    Returns:
        True if file was removed, False if it didn't exist
    """
    if CONFIG_PATH.exists():
        CONFIG_PATH.unlink()
        return True
    return False


def get_env_instructions(api_key: str) -> str:
    """
    Get environment variable setup instructions for the current OS.

    Args:
        api_key: API key to include in instructions

    Returns:
        Formatted instructions string
    """
    os_type = platform.system()

    if os_type == "Windows":
        return f"""
Windows PowerShell:
  # Add to $PROFILE for persistence
  $env:POPKIT_API_KEY = "{api_key}"

  # Or set system environment variable:
  [System.Environment]::SetEnvironmentVariable('POPKIT_API_KEY', '{api_key}', 'User')

Windows CMD:
  set POPKIT_API_KEY={api_key}
"""
    elif os_type == "Darwin":
        return f"""
macOS (zsh):
  # Add to ~/.zshrc for persistence
  echo 'export POPKIT_API_KEY="{api_key}"' >> ~/.zshrc

  # For current session:
  export POPKIT_API_KEY="{api_key}"
"""
    else:  # Linux
        return f"""
Linux (bash):
  # Add to ~/.bashrc for persistence
  echo 'export POPKIT_API_KEY="{api_key}"' >> ~/.bashrc

  # For current session:
  export POPKIT_API_KEY="{api_key}"
"""


def test_connection(api_key: str) -> Tuple[bool, Optional[str]]:
    """
    Test if API key works by calling health endpoint.

    Args:
        api_key: API key to test

    Returns:
        Tuple of (success, error_message)
        - (True, None) if connection successful
        - (False, error_message) if connection failed
    """
    url = f"{CLOUD_URL}/health"

    headers = {
        'Authorization': f'Bearer {api_key}',
        'User-Agent': 'PopKit-Plugin/0.2.5'
    }

    request = urllib.request.Request(url, headers=headers, method='GET')

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            result = json.loads(response.read().decode('utf-8'))
            if result.get('status') == 'ok':
                return (True, None)
            else:
                return (False, "Health check returned unexpected status")

    except urllib.error.HTTPError as e:
        if e.code == 401:
            return (False, "Invalid API key")
        else:
            return (False, f"API error {e.code}")

    except urllib.error.URLError as e:
        return (False, f"Network error: {e.reason}")
    except Exception as e:
        return (False, str(e))


# CLI interface for testing
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python cloud_auth.py signup <email> <password>")
        print("  python cloud_auth.py login <email> <password>")
        print("  python cloud_auth.py test <api_key>")
        print("  python cloud_auth.py remove")
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "signup":
            if len(sys.argv) < 4:
                print("Usage: python cloud_auth.py signup <email> <password>")
                sys.exit(1)

            email = sys.argv[2]
            password = sys.argv[3]

            print(f"Signing up with email: {email}")
            result = signup(email, password)

            print(f"✓ Account created!")
            print(f"  User ID: {result['userId']}")
            print(f"  Tier: {result['tier']}")
            print(f"  API Key: {result['apiKey'][:12]}...{result['apiKey'][-4:]}")

            # Save config
            save_config(result['apiKey'], result['userId'], result['tier'], result['email'])
            print(f"\n✓ Configuration saved to {CONFIG_PATH}")

        elif command == "login":
            if len(sys.argv) < 4:
                print("Usage: python cloud_auth.py login <email> <password>")
                sys.exit(1)

            email = sys.argv[2]
            password = sys.argv[3]

            print(f"Logging in as: {email}")
            result = login(email, password)

            print(f"✓ Logged in!")
            print(f"  User ID: {result['userId']}")
            print(f"  Tier: {result['tier']}")
            print(f"  API Key: {result['apiKey'][:12]}...{result['apiKey'][-4:]}")

            # Save config
            save_config(result['apiKey'], result['userId'], result['tier'], result['email'])
            print(f"\n✓ Configuration saved to {CONFIG_PATH}")

        elif command == "test":
            if len(sys.argv) < 3:
                print("Usage: python cloud_auth.py test <api_key>")
                sys.exit(1)

            api_key = sys.argv[2]

            print(f"Testing API key: {api_key[:12]}...{api_key[-4:]}")
            success, error = test_connection(api_key)

            if success:
                print("✓ Connection successful!")
            else:
                print(f"✗ Connection failed: {error}")
                sys.exit(1)

        elif command == "remove":
            if remove_config():
                print(f"✓ Removed {CONFIG_PATH}")
            else:
                print(f"No config found at {CONFIG_PATH}")

        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

    except EmailExistsError as e:
        print(f"✗ Error: {e}")
        print("\nTry logging in instead: python cloud_auth.py login <email> <password>")
        sys.exit(1)

    except InvalidCredentialsError as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

    except NetworkError as e:
        print(f"✗ Network Error: {e}")
        print("\nCheck your internet connection and try again.")
        sys.exit(1)

    except CloudAuthError as e:
        print(f"✗ Error: {e}")
        sys.exit(1)
