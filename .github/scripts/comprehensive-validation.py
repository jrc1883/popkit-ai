#!/usr/bin/env python3
"""
Comprehensive Plugin Validation for Claude Code Plugins

This script validates plugin.json, hooks.json, and marketplace.json against
official Claude Code specifications and JSON schemas.

Usage:
    python comprehensive-validation.py <plugin-dir>
    python comprehensive-validation.py --all packages/
    python comprehensive-validation.py --marketplace marketplace.json

Exit Codes:
    0 - All validations passed
    1 - Validation errors found
    2 - Script error (missing dependencies, etc.)
"""

import json
import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional
import argparse


class ValidationError:
    """Represents a validation error with severity and context."""

    def __init__(self, severity: str, message: str, file: str = None, line: int = None):
        self.severity = severity  # ERROR, WARNING, INFO
        self.message = message
        self.file = file
        self.line = line

    def __str__(self):
        location = (
            f"{self.file}:{self.line}" if self.file and self.line else self.file or ""
        )
        return (
            f"{self.severity}: {location} - {self.message}"
            if location
            else f"{self.severity}: {self.message}"
        )


class PluginValidator:
    """Comprehensive plugin validator with JSON schema support."""

    VALID_EVENTS = {
        "PreToolUse",
        "PostToolUse",
        "PermissionRequest",
        "UserPromptSubmit",
        "Notification",
        "Stop",
        "SubagentStop",
        "SessionStart",
        "SessionEnd",
        "PreCompact",
        "Setup",
    }

    VALID_LICENSES = {
        "MIT",
        "Apache-2.0",
        "GPL-3.0",
        "GPL-2.0",
        "ISC",
        "BSD-2-Clause",
        "BSD-3-Clause",
        "LGPL-3.0",
        "MPL-2.0",
        "UNLICENSED",
        "Proprietary",
    }

    HOOK_TYPES = {"command", "prompt", "agent"}

    def __init__(self, plugin_root: Path, schemas_dir: Path = None):
        self.plugin_root = Path(plugin_root)
        self.schemas_dir = schemas_dir or Path(__file__).parent.parent / "schemas"
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        self.info: List[ValidationError] = []

    def validate(
        self,
    ) -> Tuple[
        bool, List[ValidationError], List[ValidationError], List[ValidationError]
    ]:
        """Run all validations. Returns (passed, errors, warnings, info)."""
        self.validate_manifest()
        self.validate_structure()
        self.validate_hooks()
        self.validate_components()

        return len(self.errors) == 0, self.errors, self.warnings, self.info

    def validate_manifest(self):
        """Validate plugin.json manifest with comprehensive checks."""
        manifest_path = self.plugin_root / ".claude-plugin" / "plugin.json"

        if not manifest_path.exists():
            self.errors.append(
                ValidationError(
                    "ERROR", "Missing .claude-plugin/plugin.json", str(manifest_path)
                )
            )
            return

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            self.errors.append(
                ValidationError(
                    "ERROR", f"Invalid JSON: {e}", str(manifest_path), e.lineno
                )
            )
            return

        # Required field: name
        if "name" not in manifest:
            self.errors.append(
                ValidationError(
                    "ERROR", "Missing required field: name", str(manifest_path)
                )
            )
        elif not isinstance(manifest["name"], str) or not manifest["name"]:
            self.errors.append(
                ValidationError(
                    "ERROR", "Field 'name' must be non-empty string", str(manifest_path)
                )
            )
        elif not re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", manifest["name"]):
            self.errors.append(
                ValidationError(
                    "ERROR",
                    f"Field 'name' must be kebab-case: {manifest['name']}",
                    str(manifest_path),
                )
            )

        # Version validation
        if "version" in manifest:
            if not isinstance(manifest["version"], str):
                self.errors.append(
                    ValidationError(
                        "ERROR", "Field 'version' must be string", str(manifest_path)
                    )
                )
            elif not self._is_semver(manifest["version"]):
                self.errors.append(
                    ValidationError(
                        "ERROR",
                        f"Invalid semantic version: {manifest['version']}",
                        str(manifest_path),
                    )
                )

        # Repository field - CRITICAL CHECK
        if "repository" in manifest:
            repo = manifest["repository"]
            if not isinstance(repo, str):
                self.errors.append(
                    ValidationError(
                        "ERROR",
                        f"Field 'repository' must be string (not object). Found: {type(repo).__name__}",
                        str(manifest_path),
                    )
                )
                self.info.append(
                    ValidationError(
                        "INFO",
                        'Claude Code requires repository as string: "https://github.com/user/repo"',
                        str(manifest_path),
                    )
                )
            elif not repo.startswith("https://"):
                self.errors.append(
                    ValidationError(
                        "ERROR",
                        "Field 'repository' must be HTTPS URL",
                        str(manifest_path),
                    )
                )

        # Author validation
        if "author" in manifest:
            author = manifest["author"]
            if not isinstance(author, dict):
                self.errors.append(
                    ValidationError(
                        "ERROR",
                        "Field 'author' must be object with 'name' field",
                        str(manifest_path),
                    )
                )
            elif "name" not in author:
                self.errors.append(
                    ValidationError(
                        "ERROR",
                        "Field 'author.name' is required when author is present",
                        str(manifest_path),
                    )
                )

            if isinstance(author, dict) and "email" in author:
                if not self._is_valid_email(author["email"]):
                    self.errors.append(
                        ValidationError(
                            "ERROR",
                            f"Invalid email format: {author['email']}",
                            str(manifest_path),
                        )
                    )

        # License validation
        if "license" in manifest:
            if manifest["license"] not in self.VALID_LICENSES:
                self.warnings.append(
                    ValidationError(
                        "WARNING",
                        f"Unusual license identifier: {manifest['license']} (expected SPDX identifier)",
                        str(manifest_path),
                    )
                )

        # Homepage validation
        if "homepage" in manifest:
            if not isinstance(manifest["homepage"], str) or not manifest[
                "homepage"
            ].startswith("https://"):
                self.errors.append(
                    ValidationError(
                        "ERROR",
                        "Field 'homepage' must be HTTPS URL",
                        str(manifest_path),
                    )
                )

        # Keywords validation
        if "keywords" in manifest:
            if not isinstance(manifest["keywords"], list):
                self.errors.append(
                    ValidationError(
                        "ERROR", "Field 'keywords' must be array", str(manifest_path)
                    )
                )
            elif not all(isinstance(kw, str) for kw in manifest["keywords"]):
                self.errors.append(
                    ValidationError(
                        "ERROR", "All keywords must be strings", str(manifest_path)
                    )
                )

    def validate_structure(self):
        """Validate plugin directory structure."""
        # Check .claude-plugin/ only contains plugin.json
        claude_plugin_dir = self.plugin_root / ".claude-plugin"
        if claude_plugin_dir.exists():
            files = [f for f in claude_plugin_dir.iterdir() if f.is_file()]
            if len(files) > 1:
                self.errors.append(
                    ValidationError(
                        "ERROR",
                        f".claude-plugin/ should only contain plugin.json (found {len(files)} files)",
                        str(claude_plugin_dir),
                    )
                )
            elif len(files) == 1 and files[0].name != "plugin.json":
                self.errors.append(
                    ValidationError(
                        "ERROR",
                        f".claude-plugin/ must contain plugin.json (found {files[0].name})",
                        str(claude_plugin_dir),
                    )
                )

        # Validate path references in plugin.json
        manifest_path = self.plugin_root / ".claude-plugin" / "plugin.json"
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

                for field in [
                    "commands",
                    "agents",
                    "skills",
                    "hooks",
                    "mcpServers",
                    "lspServers",
                ]:
                    if field in manifest:
                        value = manifest[field]
                        paths = value if isinstance(value, list) else [value]

                        for path in paths:
                            if isinstance(path, str):
                                if not path.startswith("./"):
                                    self.errors.append(
                                        ValidationError(
                                            "ERROR",
                                            f"Path must start with './' - {field}: {path}",
                                            str(manifest_path),
                                        )
                                    )
                                if ".." in path:
                                    self.errors.append(
                                        ValidationError(
                                            "ERROR",
                                            f"No parent directory traversal allowed - {field}: {path}",
                                            str(manifest_path),
                                        )
                                    )
            except json.JSONDecodeError:
                pass  # Already reported in validate_manifest

    def validate_hooks(self):
        """Validate hooks.json structure and execution."""
        hooks_json = self.plugin_root / "hooks" / "hooks.json"
        if not hooks_json.exists():
            return  # Hooks are optional

        try:
            hooks = json.loads(hooks_json.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            self.errors.append(
                ValidationError(
                    "ERROR",
                    f"Invalid JSON in hooks.json: {e}",
                    str(hooks_json),
                    e.lineno,
                )
            )
            return

        if "hooks" not in hooks:
            self.errors.append(
                ValidationError(
                    "ERROR", "hooks.json missing 'hooks' root object", str(hooks_json)
                )
            )
            return

        # Validate event types and hook definitions
        for event, event_hooks in hooks["hooks"].items():
            if event not in self.VALID_EVENTS:
                self.errors.append(
                    ValidationError(
                        "ERROR", f"Invalid hook event type: {event}", str(hooks_json)
                    )
                )

            if not isinstance(event_hooks, list):
                self.errors.append(
                    ValidationError(
                        "ERROR",
                        f"Event '{event}' must contain array of hook matchers",
                        str(hooks_json),
                    )
                )
                continue

            for matcher_obj in event_hooks:
                if "hooks" not in matcher_obj:
                    self.errors.append(
                        ValidationError(
                            "ERROR",
                            f"Hook matcher for '{event}' missing 'hooks' array",
                            str(hooks_json),
                        )
                    )
                    continue

                for hook_def in matcher_obj.get("hooks", []):
                    if "type" not in hook_def:
                        self.errors.append(
                            ValidationError(
                                "ERROR",
                                "Hook definition missing 'type' field",
                                str(hooks_json),
                            )
                        )
                        continue

                    hook_type = hook_def["type"]
                    if hook_type not in self.HOOK_TYPES:
                        self.errors.append(
                            ValidationError(
                                "ERROR",
                                f"Invalid hook type: {hook_type} (expected: command, prompt, agent)",
                                str(hooks_json),
                            )
                        )

                    # Validate command hooks use ${CLAUDE_PLUGIN_ROOT}
                    if hook_type == "command" and "command" in hook_def:
                        cmd = hook_def["command"]
                        if "${CLAUDE_PLUGIN_ROOT}" not in cmd:
                            self.warnings.append(
                                ValidationError(
                                    "WARNING",
                                    f"Hook command should use ${{CLAUDE_PLUGIN_ROOT}}: {cmd}",
                                    str(hooks_json),
                                )
                            )

    def validate_components(self):
        """Validate commands, agents, skills directories."""
        # Validate commands
        commands_dir = self.plugin_root / "commands"
        if commands_dir.exists():
            for cmd_file in commands_dir.glob("*.md"):
                self._validate_markdown_frontmatter(cmd_file, ["description"])

        # Validate agents
        agents_dir = self.plugin_root / "agents"
        if agents_dir.exists():
            for agent_file in agents_dir.glob("*.md"):
                self._validate_markdown_frontmatter(agent_file, ["description"])

        # Validate skills
        skills_dir = self.plugin_root / "skills"
        if skills_dir.exists():
            for skill_dir in skills_dir.iterdir():
                if not skill_dir.is_dir():
                    continue

                skill_file = skill_dir / "SKILL.md"
                if not skill_file.exists():
                    self.errors.append(
                        ValidationError(
                            "ERROR",
                            f"Missing SKILL.md in {skill_dir.name}",
                            str(skill_dir),
                        )
                    )
                else:
                    self._validate_markdown_frontmatter(
                        skill_file, ["name", "description"]
                    )

    def _validate_markdown_frontmatter(self, path: Path, required_fields: List[str]):
        """Validate markdown file frontmatter."""
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            self.errors.append(
                ValidationError(
                    "ERROR", "File encoding error (expected UTF-8)", str(path)
                )
            )
            return

        if not content.startswith("---"):
            self.errors.append(
                ValidationError(
                    "ERROR", "Missing YAML frontmatter (must start with ---)", str(path)
                )
            )
            return

        # Extract YAML section
        try:
            end_idx = content.find("---", 3)
            if end_idx == -1:
                self.errors.append(
                    ValidationError(
                        "ERROR", "Invalid frontmatter (no closing ---)", str(path)
                    )
                )
                return

            yaml_str = content[3:end_idx].strip()

            # Simple field presence check (not full YAML parsing)
            for field in required_fields:
                if f"{field}:" not in yaml_str and f'"{field}":' not in yaml_str:
                    self.errors.append(
                        ValidationError(
                            "ERROR", f"Missing '{field}' in frontmatter", str(path)
                        )
                    )
        except Exception as e:
            self.errors.append(
                ValidationError("ERROR", f"Frontmatter parsing error: {e}", str(path))
            )

    @staticmethod
    def _is_semver(version: str) -> bool:
        """Check if version is semantic version."""
        pattern = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"
        return bool(re.match(pattern, version))

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        """Check if email format is valid."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))


def find_version_line_number(
    raw_lines: List[str], plugin_name: str, version_value: str
) -> Optional[int]:
    """
    Find the line number of a version field for a specific plugin in marketplace.json.

    Args:
        raw_lines: List of lines from the JSON file
        plugin_name: Name of the plugin to find
        version_value: Version string to locate

    Returns:
        Line number (1-indexed) or None if not found
    """
    in_plugin_block = False
    plugin_start_line = None

    for line_num, line in enumerate(raw_lines, start=1):
        # Check if we're entering the plugin block
        if f'"name": "{plugin_name}"' in line or f"'name': '{plugin_name}'" in line:
            in_plugin_block = True
            plugin_start_line = line_num
            continue

        # If we're in the plugin block, look for version field
        if in_plugin_block:
            # Check for version field (handle both single and double quotes, with/without spaces)
            if '"version"' in line or "'version'" in line:
                # Verify this is the correct version value
                if f'"{version_value}"' in line or f"'{version_value}'" in line:
                    return line_num

            # Exit plugin block if we hit the next plugin or end of plugins array
            if (
                '"name"' in line or "'name'" in line
            ) and line_num > plugin_start_line + 1:
                in_plugin_block = False
            if "}" in line and not any(
                c in line for c in ['"', "'"]
            ):  # Closing brace with no quotes
                in_plugin_block = False

    return None


def validate_marketplace(
    marketplace_path: Path, plugins_dir: Path
) -> Tuple[bool, List[ValidationError]]:
    """Validate marketplace.json against plugin.json files."""
    errors = []

    if not marketplace_path.exists():
        errors.append(
            ValidationError(
                "ERROR", "Marketplace file not found", str(marketplace_path)
            )
        )
        return False, errors

    # Read raw lines for line number tracking
    try:
        with open(marketplace_path, "r", encoding="utf-8") as f:
            raw_lines = f.readlines()
    except Exception as e:
        errors.append(
            ValidationError("ERROR", f"Failed to read file: {e}", str(marketplace_path))
        )
        return False, errors

    try:
        marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        errors.append(
            ValidationError(
                "ERROR", f"Invalid JSON: {e}", str(marketplace_path), e.lineno
            )
        )
        return False, errors

    if "plugins" not in marketplace:
        errors.append(
            ValidationError(
                "ERROR",
                "Missing 'plugins' array in marketplace.json",
                str(marketplace_path),
            )
        )
        return False, errors

    # Validate each plugin entry
    for plugin_entry in marketplace["plugins"]:
        name = plugin_entry.get("name")
        source = plugin_entry.get("source")

        if not name or not source:
            errors.append(
                ValidationError(
                    "ERROR",
                    "Plugin entry missing 'name' or 'source'",
                    str(marketplace_path),
                )
            )
            continue

        # Find corresponding plugin.json
        plugin_json_path = (
            plugins_dir / source.lstrip("./") / ".claude-plugin" / "plugin.json"
        )

        if not plugin_json_path.exists():
            errors.append(
                ValidationError(
                    "ERROR",
                    f"Plugin source path not found: {source}",
                    str(marketplace_path),
                )
            )
            continue

        try:
            plugin_json = json.loads(plugin_json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            errors.append(
                ValidationError(
                    "ERROR", f"Invalid plugin.json at {source}", str(marketplace_path)
                )
            )
            continue

        # Validate consistency
        if plugin_entry.get("name") != plugin_json.get("name"):
            errors.append(
                ValidationError(
                    "ERROR",
                    f"Name mismatch for {name}: marketplace='{plugin_entry.get('name')}' vs plugin.json='{plugin_json.get('name')}'",
                    str(marketplace_path),
                )
            )

        if plugin_entry.get("version") != plugin_json.get("version"):
            # Find the line number for this version field
            marketplace_version = plugin_entry.get("version")
            plugin_version = plugin_json.get("version")
            line_num = find_version_line_number(raw_lines, name, marketplace_version)

            errors.append(
                ValidationError(
                    "ERROR",
                    f"Version mismatch for {name}: '{marketplace_version}' → '{plugin_version}'",
                    str(marketplace_path),
                    line_num,
                )
            )

    return len(errors) == 0, errors


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive Claude Code plugin validation"
    )
    parser.add_argument("path", help="Plugin directory or marketplace.json")
    parser.add_argument(
        "--all", action="store_true", help="Validate all plugins in directory"
    )
    parser.add_argument(
        "--marketplace", action="store_true", help="Validate marketplace.json"
    )
    parser.add_argument("--json", action="store_true", help="Output JSON results")

    args = parser.parse_args()
    path = Path(args.path)

    all_errors = []
    all_warnings = []
    all_info = []

    if args.marketplace:
        passed, errors = validate_marketplace(path, path.parent)
        all_errors.extend(errors)
    elif args.all:
        # Validate all plugins in directory
        for plugin_dir in path.iterdir():
            if (
                plugin_dir.is_dir()
                and (plugin_dir / ".claude-plugin" / "plugin.json").exists()
            ):
                print(f"\nValidating {plugin_dir.name}...")
                validator = PluginValidator(plugin_dir)
                passed, errors, warnings, info = validator.validate()
                all_errors.extend(errors)
                all_warnings.extend(warnings)
                all_info.extend(info)
    else:
        # Validate single plugin
        validator = PluginValidator(path)
        passed, all_errors, all_warnings, all_info = validator.validate()

    # Output results
    for error in all_errors:
        print(f"\033[91m{error}\033[0m")  # Red

    for warning in all_warnings:
        print(f"\033[93m{warning}\033[0m")  # Yellow

    for info in all_info:
        print(f"\033[94m{info}\033[0m")  # Blue

    # Summary
    print(f"\n{'=' * 60}")
    print("Validation Summary:")
    print(f"  Errors:   {len(all_errors)}")
    print(f"  Warnings: {len(all_warnings)}")
    print(f"  Info:     {len(all_info)}")
    print(f"{'=' * 60}")

    if len(all_errors) > 0:
        print("\n\033[91mValidation FAILED\033[0m")
        sys.exit(1)
    else:
        print("\n\033[92mValidation PASSED\033[0m")
        sys.exit(0)


if __name__ == "__main__":
    main()
