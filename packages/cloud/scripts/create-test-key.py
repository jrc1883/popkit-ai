#!/usr/bin/env python3
"""
Create a test API key in Upstash Redis.

Usage:
    python create-test-key.py
"""

import json
import urllib.request
import urllib.error
import secrets
from datetime import datetime

# Upstash credentials
UPSTASH_URL = "https://light-whale-26554.upstash.io"
UPSTASH_TOKEN = "AWe6AAIncDI0ZDBjNGJmOTA0ZGY0YTMxODEwY2ViMzBmZGY4YWU3ZXAyMjY1NTQ"


def upstash_command(*args):
    """Execute a Redis command via Upstash REST API."""
    url = UPSTASH_URL
    headers = {
        "Authorization": f"Bearer {UPSTASH_TOKEN}",
        "Content-Type": "application/json",
    }

    # Upstash REST API expects array of command parts
    data = json.dumps(args).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method="POST")

    with urllib.request.urlopen(request) as response:
        return json.loads(response.read().decode("utf-8"))


def create_api_key(user_id: str, tier: str = "pro", name: str = "Test Key"):
    """Create a new API key."""
    # Generate random key
    random_part = secrets.token_hex(24)
    api_key = f"pk_live_{random_part}"

    key_data = {
        "id": secrets.token_hex(16),
        "userId": user_id,
        "tier": tier,
        "name": name,
        "createdAt": datetime.now().isoformat(),
    }

    # Store in Redis hash
    result = upstash_command("HSET", "popkit:keys", api_key, json.dumps(key_data))

    return api_key, key_data, result


if __name__ == "__main__":
    print("Creating test API key...")
    print("=" * 50)

    # Create a test user ID
    user_id = "user_test_" + secrets.token_hex(8)

    api_key, key_data, result = create_api_key(
        user_id=user_id,
        tier="pro",
        name="PopKit Test Key"
    )

    print(f"\nAPI Key Created!")
    print(f"\n  API Key: {api_key}")
    print(f"  User ID: {key_data['userId']}")
    print(f"  Tier: {key_data['tier']}")
    print(f"  Created: {key_data['createdAt']}")
    print(f"\nRedis result: {result}")

    print("\n" + "=" * 50)
    print("\nTo use this key, set the environment variable:")
    print(f"\n  export POPKIT_API_KEY={api_key}")
    print("\nOr on Windows PowerShell:")
    print(f"\n  $env:POPKIT_API_KEY = \"{api_key}\"")
    print("\n" + "=" * 50)
