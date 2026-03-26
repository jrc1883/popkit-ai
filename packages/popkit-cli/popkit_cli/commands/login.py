"""
PopKit Login Command

Authenticates with PopKit Cloud and stores API key securely.

Usage:
    popkit login                    # Interactive email/password login
    popkit login --key pk_live_xxx  # Direct API key entry
"""

import argparse
import getpass
import json
import os
import stat
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_API_URL = "https://api.thehouseofdeals.com"
CONFIG_DIR = Path.home() / ".popkit"
CONFIG_FILE = CONFIG_DIR / "cloud-config.json"


def get_config_path() -> Path:
    """Get the config file path, creating the directory if needed."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return CONFIG_FILE


def save_config(api_key: str, email: str = "", api_url: str = DEFAULT_API_URL) -> Path:
    """Save API key and config to disk with restrictive permissions."""
    config_path = get_config_path()

    config = {
        "api_key": api_key,
        "email": email,
        "api_url": api_url,
    }

    config_path.write_text(json.dumps(config, indent=2))

    # Set restrictive permissions (user-only read/write)
    try:
        os.chmod(config_path, stat.S_IRUSR | stat.S_IWUSR)
    except OSError:
        pass  # Windows may not support chmod the same way

    return config_path


def load_config() -> dict | None:
    """Load saved config from disk. Returns None if not found."""
    # Check primary location
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            pass

    # Check legacy location
    legacy = Path.home() / ".claude" / "popkit" / "cloud-config.json"
    if legacy.exists():
        try:
            return json.loads(legacy.read_text())
        except (json.JSONDecodeError, OSError):
            pass

    return None


def get_api_key() -> str | None:
    """Get API key from env var or config file.

    Resolution order:
    1. POPKIT_API_KEY env var (for CI/advanced users)
    2. ~/.popkit/cloud-config.json (primary)
    3. ~/.claude/popkit/cloud-config.json (legacy)
    """
    # 1. Environment variable
    env_key = os.environ.get("POPKIT_API_KEY", "")
    if env_key:
        return env_key

    # 2. Config file
    config = load_config()
    if config and config.get("api_key"):
        return config["api_key"]

    return None


def run_login(args: argparse.Namespace) -> int:
    """Execute the login command."""
    api_url = os.environ.get("POPKIT_API_URL", DEFAULT_API_URL)

    # Direct key entry
    if args.key:
        config_path = save_config(api_key=args.key, api_url=api_url)
        print(f"API key saved to {config_path}")
        print("You can now use PopKit Cloud features.")
        return 0

    # Interactive login
    print("PopKit Cloud Login")
    print("=" * 40)

    email = input("Email: ").strip()
    if not email:
        print("Error: Email is required", file=sys.stderr)
        return 1

    password = getpass.getpass("Password: ")
    if not password:
        print("Error: Password is required", file=sys.stderr)
        return 1

    print("Logging in...")

    try:
        req = Request(
            f"{api_url}/v1/auth/login",
            data=json.dumps({"email": email, "password": password}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        session_token = data.get("sessionToken", "")

        # Now fetch the user's API keys using the session token
        keys_req = Request(
            f"{api_url}/v1/account/keys",
            headers={
                "Authorization": f"Bearer {session_token}",
                "Content-Type": "application/json",
            },
        )

        with urlopen(keys_req, timeout=10) as resp:
            keys_data = json.loads(resp.read().decode())

        keys = keys_data.get("keys", [])
        if not keys:
            print("No API keys found. Creating one...")
            create_req = Request(
                f"{api_url}/v1/account/keys",
                data=json.dumps({"name": "PopKit CLI"}).encode(),
                headers={
                    "Authorization": f"Bearer {session_token}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urlopen(create_req, timeout=10) as resp:
                key_data = json.loads(resp.read().decode())
            api_key = key_data.get("key", "")
        else:
            api_key = keys[0].get("key", "")

        if not api_key:
            print("Error: Could not retrieve API key", file=sys.stderr)
            return 1

        config_path = save_config(api_key=api_key, email=email, api_url=api_url)

        print()
        print("Logged in successfully!")
        print(f"Config saved to: {config_path}")
        print()
        print("Your PopKit Cloud features are now active.")
        print("No need to set environment variables or edit MCP configs.")
        return 0

    except HTTPError as e:
        body = e.read().decode()
        try:
            error = json.loads(body).get("error", body)
        except json.JSONDecodeError:
            error = body
        print(f"Login failed: {error}", file=sys.stderr)
        return 1
    except URLError as e:
        print(f"Connection failed: {e.reason}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
