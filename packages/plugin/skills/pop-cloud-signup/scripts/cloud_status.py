#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PopKit Cloud Status Checker

Gets cloud connection status, usage stats, and account information.
Used by /popkit:cloud status command.
"""

import json
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Dict

# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
    sys.stderr = codecs.getwriter("utf-8")(sys.stderr.buffer, "strict")

# Import from cloud_auth
sys.path.insert(0, str(Path(__file__).parent))
from cloud_auth import CONFIG_PATH, CLOUD_URL


def get_cloud_status() -> Dict:
    """
    Get complete cloud status including connection, account, and usage.

    Returns:
        Dict with status information:
        - connected: bool
        - account: Dict (if connected)
        - usage: Dict (if connected)
        - features: List[str] (if connected)
        - error: str (if not connected)
    """
    # Check for API key
    api_key = os.environ.get("POPKIT_API_KEY")

    if not api_key:
        # Check config file
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH, 'r') as f:
                    config = json.load(f)
                    api_key = config.get('apiKey')
            except (json.JSONDecodeError, IOError):
                pass

    if not api_key:
        return {
            "connected": False,
            "error": "Not configured",
            "message": "POPKIT_API_KEY not set and no config file found"
        }

    # Test connection
    url = f"{CLOUD_URL}/health"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'User-Agent': 'PopKit-Plugin/0.2.5'
    }

    request = urllib.request.Request(url, headers=headers, method='GET')

    try:
        import time
        start_time = time.time()

        with urllib.request.urlopen(request, timeout=10) as response:
            latency_ms = int((time.time() - start_time) * 1000)
            result = json.loads(response.read().decode('utf-8'))

            if result.get('status') == 'ok':
                # Get user info
                user = result.get('user', {})

                # Get usage stats
                usage = result.get('usage', {})

                return {
                    "connected": True,
                    "url": CLOUD_URL.replace('/v1', ''),
                    "latency_ms": latency_ms,
                    "account": {
                        "email": user.get('email', 'Unknown'),
                        "tier": user.get('tier', 'free'),
                        "user_id": user.get('id', 'Unknown')
                    },
                    "usage": {
                        "requests_today": usage.get('requestsToday', 0),
                        "limit": usage.get('limit', 100),
                        "remaining": usage.get('remaining', 100),
                        "resets_in_hours": usage.get('resetsInHours', 24)
                    },
                    "features": [
                        "Pattern sharing (collective learning)",
                        "Research knowledge base",
                        "Inter-agent messaging",
                        "Workflow persistence",
                        "Analytics"
                    ]
                }
            else:
                return {
                    "connected": False,
                    "error": "Unexpected response",
                    "message": "Health check returned unexpected status"
                }

    except urllib.error.HTTPError as e:
        if e.code == 401:
            error_msg = "Invalid API key"
        else:
            error_msg = f"API error {e.code}"

        return {
            "connected": False,
            "error": error_msg,
            "message": "Check your API key and try again"
        }

    except urllib.error.URLError as e:
        return {
            "connected": False,
            "error": "Network error",
            "message": f"Cannot connect to PopKit Cloud: {e.reason}"
        }

    except Exception as e:
        return {
            "connected": False,
            "error": "Unknown error",
            "message": str(e)
        }


def format_status_output(status: Dict, json_output: bool = False) -> str:
    """
    Format status information for display.

    Args:
        status: Status dict from get_cloud_status()
        json_output: If True, return JSON format

    Returns:
        Formatted status string
    """
    if json_output:
        return json.dumps(status, indent=2)

    if status['connected']:
        account = status['account']
        usage = status['usage']
        output = f"""PopKit Cloud Status
═══════════════════

Connection: ✓ Connected
URL: {status['url']}
Latency: {status['latency_ms']}ms

Account:
  Email: {account['email']}
  Tier: {account['tier'].capitalize()}
  User ID: {account['user_id']}

Usage Today:
  Requests: {usage['requests_today']} / {usage['limit']}
  Remaining: {usage['remaining']}
  Resets: in {usage['resets_in_hours']} hours

Available Features:
"""
        for feature in status['features']:
            output += f"  ✓ {feature}\n"

        if account['tier'] == 'free':
            output += """
Upgrade to Pro for:
  • 1,000 requests/day (10x more)
  • 24-hour session persistence
  • Priority support

Run /popkit:upgrade to see plans
"""
    else:
        output = f"""PopKit Cloud Status
═══════════════════

Connection: ✗ {status['error']}

{status['message']}

To enable cloud features:
  1. Sign up: /popkit:cloud signup
  2. Or login: /popkit:cloud login

Cloud Features (when connected):
  • Pattern sharing (learn from community)
  • Research knowledge base
  • Power Mode coordination
  • Workflow persistence
"""

    return output


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Check PopKit Cloud status")
    parser.add_argument('--json', action='store_true', help="Output as JSON")
    args = parser.parse_args()

    status = get_cloud_status()
    print(format_status_output(status, args.json))

    # Exit with code 1 if not connected
    sys.exit(0 if status['connected'] else 1)
