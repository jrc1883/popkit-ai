#!/usr/bin/env python3
"""PopKit Orchestration Validation Script"""

import os
import json
from pathlib import Path

def count_files(directory, pattern):
    """Count files matching pattern in directory."""
    if not os.path.exists(directory):
        return 0
    return len(list(Path(directory).rglob(pattern)))

def main():
    print("=== PopKit Orchestration Validation ===\n")

    # Test 1: Modular Plugin Hooks
    print("Test 1: Modular Plugin Hooks")
    print("-----------------------------")
    plugins = ["popkit-dev", "popkit-ops", "popkit-research", "popkit-core"]
    total_modular_hooks = 0

    for plugin in plugins:
        hooks_dir = f"packages/{plugin}/hooks"
        if os.path.exists(hooks_dir):
            count = count_files(hooks_dir, "*.py")
            print(f"[OK] {plugin}: {count} hooks")
            total_modular_hooks += count
        else:
            print(f"[FAIL] {plugin}: NO hooks directory")

    print(f"\nTotal modular plugin hooks: {total_modular_hooks}")
    print()

    # Test 2: Old Monolithic Plugin
    print("Test 2: Old Monolithic Plugin")
    print("------------------------------")
    old_hooks = count_files("packages/plugin/hooks", "*.py")
    print(f"[OK] plugin (monolithic): {old_hooks} hooks")
    print()

    # Test 3: Shared Python Package
    print("Test 3: Shared Python Package")
    print("------------------------------")
    shared_utils = count_files("packages/shared-py/popkit_shared/utils", "*.py")
    print(f"[OK] shared-py utilities: {shared_utils} modules")

    # Check if importable
    try:
        import popkit_shared
        print("[OK] popkit_shared is importable")
    except ImportError:
        print("[FAIL] popkit_shared NOT installed (run: pip install -e packages/shared-py)")
    print()

    # Test 4: Plugin Dependencies
    print("Test 4: Plugin Dependency Declarations")
    print("---------------------------------------")
    for plugin in plugins:
        plugin_json = f"packages/{plugin}/.claude-plugin/plugin.json"
        if os.path.exists(plugin_json):
            with open(plugin_json) as f:
                data = json.load(f)
                deps = data.get("dependencies", {})
                if deps:
                    print(f"[WARN] {plugin} declares dependencies (NOT SUPPORTED):")
                    for dep, version in deps.items():
                        print(f"    - {dep} {version}")
                else:
                    print(f"[OK] {plugin}: no dependencies")
    print()

    # Test 5: Skills Count
    print("Test 5: Skill Distribution")
    print("---------------------------")
    total_skills = 0
    for plugin in plugins:
        skills_dir = f"packages/{plugin}/skills"
        if os.path.exists(skills_dir):
            count = len([d for d in os.listdir(skills_dir)
                        if os.path.isdir(os.path.join(skills_dir, d))
                        and not d.startswith('_')])
            print(f"[OK] {plugin}: {count} skills")
            total_skills += count
    print(f"\nTotal skills: {total_skills}")
    print()

    # Summary
    print("=== CRITICAL FINDINGS ===\n")

    if total_modular_hooks == 0:
        print("[BLOCKER] Modular plugins have NO hooks!")
        print("   Orchestration CANNOT work without hooks.\n")
        print("   Options:")
        print("   A) Copy hooks to each plugin (25 hooks x 4 plugins)")
        print("   B) Use popkit-core as foundation with all hooks\n")
    else:
        print(f"[OK] Modular plugins have {total_modular_hooks} hooks\n")

    if any(os.path.exists(f"packages/{p}/.claude-plugin/plugin.json") and
           json.load(open(f"packages/{p}/.claude-plugin/plugin.json")).get("dependencies")
           for p in plugins):
        print("[BLOCKER] Plugins declare dependencies!")
        print("   Claude Code does NOT support plugin dependencies.")
        print("   Remove all 'dependencies' fields from plugin.json files.\n")

    print("Next steps:")
    print("1. Choose architecture: Option A (duplicate) or B (foundation)")
    print("2. pip install -e packages/shared-py")
    print("3. Remove dependency declarations")
    print("4. Add hooks to modular plugins")
    print("5. Restart Claude Code")

if __name__ == "__main__":
    main()
