#!/usr/bin/env python3
"""
Validate root marketplace.json contains all expected plugins.
Usage: python validate_marketplace.py
"""

import json
import sys

try:
    with open(".claude-plugin/marketplace.json") as f:
        marketplace = json.load(f)
except Exception as e:
    print(f"Error: Failed to read marketplace.json: {e}")
    sys.exit(1)

expected_plugins = ["popkit-core", "popkit-dev", "popkit-ops", "popkit-research"]
actual_plugins = [p["name"] for p in marketplace.get("plugins", [])]

missing = set(expected_plugins) - set(actual_plugins)
if missing:
    print(f"Error: Plugins missing from marketplace: {missing}")
    sys.exit(1)

print(f"✓ All {len(actual_plugins)} plugins listed in marketplace")
print(f"✓ Marketplace version: {marketplace.get('metadata', {}).get('version', 'unknown')}")
