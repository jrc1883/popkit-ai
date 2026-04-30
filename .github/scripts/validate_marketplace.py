#!/usr/bin/env python3
"""
Validate PopKit marketplace release metadata.

Checks the install-facing marketplace files, package plugin manifests, and
universal package manifests stay version-aligned.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

EXPECTED_PLUGINS = ["popkit-core", "popkit-dev", "popkit-ops", "popkit-research"]
REPOSITORY_URL = "https://github.com/jrc1883/popkit-ai"


def load_json(path: Path) -> dict:
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        raise ValueError(f"failed to read {path}: {exc}") from exc


def read_yaml_field(path: Path, field: str) -> str | None:
    pattern = re.compile(rf"^{re.escape(field)}:\s*(.+?)\s*$")
    for line in path.read_text(encoding="utf-8").splitlines():
        match = pattern.match(line)
        if match:
            return match.group(1).strip().strip("'\"")
    return None


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate_marketplace(path: Path, errors: list[str]) -> str | None:
    marketplace = load_json(path)
    version = marketplace.get("metadata", {}).get("version")
    plugins = marketplace.get("plugins", [])
    actual_plugins = [plugin.get("name") for plugin in plugins]

    missing = sorted(set(EXPECTED_PLUGINS) - set(actual_plugins))
    extra = sorted(set(actual_plugins) - set(EXPECTED_PLUGINS))
    require(not missing, f"{path}: missing plugins {missing}", errors)
    require(not extra, f"{path}: unexpected plugins {extra}", errors)
    require(bool(version), f"{path}: missing metadata.version", errors)

    for plugin in plugins:
        name = plugin.get("name", "<unknown>")
        require(
            plugin.get("version") == version,
            f"{path}: {name} version {plugin.get('version')} != marketplace {version}",
            errors,
        )
        require(
            plugin.get("repository") == REPOSITORY_URL,
            f"{path}: {name} repository should be {REPOSITORY_URL}",
            errors,
        )

    return version


def validate_package_manifests(version: str, errors: list[str]) -> None:
    for plugin_name in EXPECTED_PLUGINS:
        plugin_json = Path("packages") / plugin_name / ".claude-plugin" / "plugin.json"
        package_yaml = Path("packages") / plugin_name / "popkit-package.yaml"

        plugin_manifest = load_json(plugin_json)
        require(
            plugin_manifest.get("version") == version,
            f"{plugin_json}: version {plugin_manifest.get('version')} != {version}",
            errors,
        )
        require(
            plugin_manifest.get("repository") == REPOSITORY_URL,
            f"{plugin_json}: repository should be {REPOSITORY_URL}",
            errors,
        )

        yaml_version = read_yaml_field(package_yaml, "version")
        yaml_repository = read_yaml_field(package_yaml, "repository")
        require(
            yaml_version == version, f"{package_yaml}: version {yaml_version} != {version}", errors
        )
        require(
            yaml_repository == REPOSITORY_URL,
            f"{package_yaml}: repository should be {REPOSITORY_URL}",
            errors,
        )


def main() -> int:
    errors: list[str] = []
    versions = []

    for path in [Path(".claude-plugin/marketplace.json"), Path("marketplace.json")]:
        versions.append(validate_marketplace(path, errors))

    require(
        len(set(versions)) == 1,
        f"marketplace versions differ: {versions}",
        errors,
    )

    if versions[0]:
        validate_package_manifests(versions[0], errors)

    if errors:
        print("Marketplace validation failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(f"All {len(EXPECTED_PLUGINS)} plugins listed in both marketplace files")
    print(f"Marketplace version: {versions[0]}")
    print(f"Repository URL: {REPOSITORY_URL}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
