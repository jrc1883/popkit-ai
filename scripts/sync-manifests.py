#!/usr/bin/env python3
"""
Sync Manifests Script

Keeps popkit-package.yaml and .claude-plugin/plugin.json in sync.
When popkit-package.yaml is the source of truth, this script updates
plugin.json with matching version/description fields.

Can also sync the other direction (plugin.json → popkit-package.yaml)
for backward compatibility during migration.

Usage:
    python scripts/sync-manifests.py                    # yaml → json (default)
    python scripts/sync-manifests.py --direction json   # json → yaml
    python scripts/sync-manifests.py --check            # verify sync (CI mode)
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

PACKAGES_DIR = Path(__file__).parent.parent / "packages"

PACKAGE_NAMES = ["popkit-core", "popkit-dev", "popkit-ops", "popkit-research"]


def load_yaml_manifest(package_dir: Path) -> dict:
    """Load popkit-package.yaml from a package directory."""
    yaml_path = package_dir / "popkit-package.yaml"
    if not yaml_path.exists():
        return {}
    with open(yaml_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_plugin_json(package_dir: Path) -> dict:
    """Load .claude-plugin/plugin.json from a package directory."""
    json_path = package_dir / ".claude-plugin" / "plugin.json"
    if not json_path.exists():
        return {}
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_plugin_json(package_dir: Path, data: dict) -> None:
    """Save .claude-plugin/plugin.json."""
    json_path = package_dir / ".claude-plugin" / "plugin.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def save_yaml_manifest(package_dir: Path, data: dict) -> None:
    """Save popkit-package.yaml."""
    yaml_path = package_dir / "popkit-package.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def sync_yaml_to_json(package_dir: Path) -> bool:
    """Sync popkit-package.yaml → plugin.json.

    Returns True if changes were made.
    """
    manifest = load_yaml_manifest(package_dir)
    plugin = load_plugin_json(package_dir)

    if not manifest or not plugin:
        return False

    changed = False

    # Sync version
    if manifest.get("version") and manifest["version"] != plugin.get("version"):
        plugin["version"] = manifest["version"]
        changed = True

    # Sync description
    if manifest.get("description") and manifest["description"] != plugin.get("description"):
        plugin["description"] = manifest["description"]
        changed = True

    # Sync name
    if manifest.get("name") and manifest["name"] != plugin.get("name"):
        plugin["name"] = manifest["name"]
        changed = True

    if changed:
        save_plugin_json(package_dir, plugin)

    return changed


def sync_json_to_yaml(package_dir: Path) -> bool:
    """Sync plugin.json → popkit-package.yaml.

    Returns True if changes were made.
    """
    plugin = load_plugin_json(package_dir)
    manifest = load_yaml_manifest(package_dir)

    if not plugin or not manifest:
        return False

    changed = False

    if plugin.get("version") and plugin["version"] != manifest.get("version"):
        manifest["version"] = plugin["version"]
        changed = True

    if plugin.get("description") and plugin["description"] != manifest.get("description"):
        manifest["description"] = plugin["description"]
        changed = True

    if changed:
        save_yaml_manifest(package_dir, manifest)

    return changed


def check_sync(package_dir: Path) -> list[str]:
    """Check if manifests are in sync. Returns list of mismatches."""
    manifest = load_yaml_manifest(package_dir)
    plugin = load_plugin_json(package_dir)

    mismatches = []

    if not manifest:
        mismatches.append(f"{package_dir.name}: missing popkit-package.yaml")
        return mismatches

    if not plugin:
        mismatches.append(f"{package_dir.name}: missing plugin.json")
        return mismatches

    if manifest.get("version") != plugin.get("version"):
        mismatches.append(
            f"{package_dir.name}: version mismatch "
            f"(yaml={manifest.get('version')}, json={plugin.get('version')})"
        )

    return mismatches


def main():
    parser = argparse.ArgumentParser(description="Sync PopKit manifests")
    parser.add_argument(
        "--direction",
        choices=["yaml", "json"],
        default="yaml",
        help="Source of truth: 'yaml' syncs yaml→json, 'json' syncs json→yaml (default: yaml)",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check sync status without making changes (CI mode)",
    )
    args = parser.parse_args()

    if args.check:
        all_mismatches = []
        for name in PACKAGE_NAMES:
            pkg_dir = PACKAGES_DIR / name
            mismatches = check_sync(pkg_dir)
            all_mismatches.extend(mismatches)

        if all_mismatches:
            print("Manifest sync check FAILED:")
            for m in all_mismatches:
                print(f"  - {m}")
            return 1
        else:
            print("All manifests in sync.")
            return 0

    sync_fn = sync_yaml_to_json if args.direction == "yaml" else sync_json_to_yaml

    for name in PACKAGE_NAMES:
        pkg_dir = PACKAGES_DIR / name
        if sync_fn(pkg_dir):
            print(f"  Updated: {name}")
        else:
            print(f"  OK: {name}")

    print("Sync complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
