#!/usr/bin/env python3
"""
Validate plugin.json for required fields.
Usage: python validate_plugin.py <plugin_json_path> <plugin_name>
"""

import json
import sys

if len(sys.argv) != 3:
    print("Usage: python validate_plugin.py <plugin_json_path> <plugin_name>")
    sys.exit(1)

plugin_json = sys.argv[1]
plugin_name = sys.argv[2]

try:
    with open(plugin_json) as f:
        plugin = json.load(f)
except Exception as e:
    print(f"Error: Failed to read {plugin_json}: {e}")
    sys.exit(1)

required_fields = ["name", "version", "description"]
missing = [f for f in required_fields if f not in plugin]

if missing:
    print(f"Error: Missing required fields in {plugin_name}: {missing}")
    sys.exit(1)

print(f"✓ {plugin['name']} v{plugin['version']}")
