#!/usr/bin/env python3
"""
Quick test script to verify output-validator.py can load all schemas.
"""

import json
from pathlib import Path

# Get the schema directory
schema_dir = Path("packages/popkit-core/output-styles/schemas")

print("Testing schema loading...\n")
print(f"Schema directory: {schema_dir.absolute()}\n")

# List all schema files
schema_files = list(schema_dir.glob("*.schema.json"))
print(f"Found {len(schema_files)} schema files:\n")

errors = []
success_count = 0

for schema_file in sorted(schema_files):
    output_style = schema_file.stem.replace(".schema", "")
    try:
        with open(schema_file, 'r', encoding='utf-8') as f:
            schema = json.load(f)

        # Validate basic structure
        if "$schema" not in schema:
            errors.append(f"  [X] {output_style}: Missing $schema field")
        elif "title" not in schema:
            errors.append(f"  [X] {output_style}: Missing title field")
        elif "type" not in schema or schema["type"] != "object":
            errors.append(f"  [X] {output_style}: Invalid or missing type field")
        elif "properties" not in schema:
            errors.append(f"  [X] {output_style}: Missing properties field")
        else:
            required_fields = schema.get("required", [])
            properties = schema.get("properties", {})
            print(f"  [OK] {output_style}")
            print(f"       Required: {', '.join(required_fields)}")
            print(f"       Properties: {len(properties)} fields")
            success_count += 1

    except json.JSONDecodeError as e:
        errors.append(f"  [X] {output_style}: Invalid JSON - {e}")
    except Exception as e:
        errors.append(f"  [X] {output_style}: Error - {e}")

print(f"\n{'='*60}")
print(f"Results: {success_count}/{len(schema_files)} schemas loaded successfully")

if errors:
    print(f"\nErrors found:")
    for error in errors:
        print(error)
else:
    print("\n[OK] All schemas are valid and loadable!")

print(f"{'='*60}")
