"""
Plugin structure validator for PopKit plugin testing.

Validates overall plugin structure, required files, and configuration integrity.
"""

import json
from pathlib import Path
from typing import Any, Dict, List


def validate_plugin_structure(plugin_root: Path) -> Dict[str, Any]:
    """
    Validate plugin directory structure and required files.

    Args:
        plugin_root: Path to plugin root directory

    Returns:
        Validation result dictionary
    """
    result = {
        "valid": False,
        "plugin_root": str(plugin_root),
        "required_files": {},
        "required_dirs": {},
        "plugin_json": {},
        "hooks_json": {},
        "agent_config": {},
        "errors": [],
        "warnings": [],
    }

    if not plugin_root.exists():
        result["errors"].append(f"Plugin root not found: {plugin_root}")
        return result

    # Check required files (modular architecture - only plugin.json is truly required)
    required_files = {
        ".claude-plugin/plugin.json": ("required", "Plugin manifest"),
        "README.md": ("required", "Plugin documentation"),
    }

    optional_files = {
        "hooks/hooks.json": "Hooks configuration",
        "agents/config.json": "Agent configuration (legacy - not needed in modular architecture)",
    }

    for file_path, (requirement, description) in required_files.items():
        full_path = plugin_root / file_path
        exists = full_path.exists()

        result["required_files"][file_path] = {
            "exists": exists,
            "description": description,
            "required": True,
        }

        if not exists:
            result["errors"].append(f"Required file missing: {file_path}")

    # Check optional files
    for file_path, description in optional_files.items():
        full_path = plugin_root / file_path
        exists = full_path.exists()

        result["required_files"][file_path] = {
            "exists": exists,
            "description": description,
            "required": False,
        }

        # Don't error on missing optional files

    # Check optional directories (all component directories are optional in modular architecture)
    optional_dirs = {
        ".claude-plugin": ("required", "Plugin manifest directory"),
        "skills": ("optional", "Skills directory"),
        "commands": ("optional", "Commands directory"),
        "agents": ("optional", "Agents directory"),
        "hooks": ("optional", "Hooks directory"),
    }

    for dir_path, (requirement, description) in optional_dirs.items():
        full_path = plugin_root / dir_path
        exists = full_path.exists() and full_path.is_dir()

        result["required_dirs"][dir_path] = {
            "exists": exists,
            "description": description,
            "required": requirement == "required",
        }

        if not exists and requirement == "required":
            result["errors"].append(f"Required directory missing: {dir_path}")
        elif not exists and requirement == "optional":
            # This is fine - not all plugins need all directories
            pass

    # Validate plugin.json
    plugin_json_path = plugin_root / ".claude-plugin" / "plugin.json"
    if plugin_json_path.exists():
        try:
            plugin_json = json.loads(plugin_json_path.read_text())
            result["plugin_json"] = validate_plugin_json(plugin_json)

            if not result["plugin_json"]["valid"]:
                result["errors"].extend(result["plugin_json"]["errors"])

        except json.JSONDecodeError as e:
            result["errors"].append(f"Invalid JSON in plugin.json: {e}")

    # Validate hooks.json
    hooks_json_path = plugin_root / "hooks" / "hooks.json"
    if hooks_json_path.exists():
        try:
            hooks_json = json.loads(hooks_json_path.read_text())
            result["hooks_json"] = validate_hooks_json(hooks_json, plugin_root / "hooks")

            if not result["hooks_json"]["valid"]:
                result["errors"].extend(result["hooks_json"]["errors"])

        except json.JSONDecodeError as e:
            result["errors"].append(f"Invalid JSON in hooks.json: {e}")

    # Validate agents/config.json (optional in modular architecture)
    # In modular architecture, each plugin has agent markdown files, not a centralized config
    agent_config_path = plugin_root / "agents" / "config.json"
    if agent_config_path.exists():
        result["warnings"].append(
            "Found agents/config.json (legacy structure). Modular plugins use agent markdown files instead."
        )
        try:
            agent_config = json.loads(agent_config_path.read_text())
            result["agent_config"] = validate_agent_config(agent_config, plugin_root / "agents")

            if not result["agent_config"]["valid"]:
                result["warnings"].extend(result["agent_config"]["errors"])

        except json.JSONDecodeError as e:
            result["warnings"].append(f"Invalid JSON in agents/config.json: {e}")
    else:
        # This is expected in modular architecture - agents are discovered from markdown files
        result["agent_config"] = {
            "valid": True,
            "note": "Using modular architecture - agents discovered from markdown files",
        }

    # Overall validity
    result["valid"] = len(result["errors"]) == 0

    return result


def validate_plugin_json(plugin_json: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate plugin.json structure and required fields.

    Args:
        plugin_json: Parsed plugin.json content

    Returns:
        Validation result
    """
    result = {
        "valid": False,
        "has_required_fields": True,
        "version_valid": False,
        "errors": [],
        "warnings": [],
    }

    # Required fields
    required_fields = ["name", "version", "description"]

    for field in required_fields:
        if field not in plugin_json:
            result["errors"].append(f"Missing required field: {field}")
            result["has_required_fields"] = False

    # Validate version format (semver)
    if "version" in plugin_json:
        version = plugin_json["version"]
        import re

        if re.match(r"^\d+\.\d+\.\d+", version):
            result["version_valid"] = True
        else:
            result["errors"].append(f"Invalid version format: {version} (expected semver: X.Y.Z)")

    # Check for common optional fields
    optional_fields = ["author", "license", "repository", "keywords"]
    for field in optional_fields:
        if field not in plugin_json:
            result["warnings"].append(f"Optional field missing: {field}")

    result["valid"] = result["has_required_fields"] and result["version_valid"]

    return result


def validate_hooks_json(hooks_json: Dict[str, Any], hooks_dir: Path) -> Dict[str, Any]:
    """
    Validate hooks.json structure and hook file references.

    Args:
        hooks_json: Parsed hooks.json content
        hooks_dir: Path to hooks directory

    Returns:
        Validation result
    """
    result = {
        "valid": False,
        "has_hooks_field": False,
        "hook_files_exist": True,
        "hook_count": 0,
        "missing_files": [],
        "errors": [],
        "warnings": [],
    }

    # Check for hooks field
    if "hooks" not in hooks_json:
        result["errors"].append("Missing 'hooks' field")
        return result

    result["has_hooks_field"] = True
    hooks = hooks_json["hooks"]

    # Validate each hook type
    for hook_type, hook_matchers in hooks.items():
        if not isinstance(hook_matchers, list):
            result["errors"].append(f"Hook type '{hook_type}' should be a list")
            continue

        for matcher_config in hook_matchers:
            if "hooks" not in matcher_config:
                continue

            for hook_def in matcher_config["hooks"]:
                result["hook_count"] += 1

                if "command" not in hook_def:
                    result["errors"].append(f"Hook in {hook_type} missing 'command' field")
                    continue

                # Extract Python file from command
                command = hook_def["command"]
                # Look for .py file in command
                import re

                py_file_match = re.search(r"hooks/([a-z0-9_-]+\.py)", command)

                if py_file_match:
                    py_file = py_file_match.group(1)
                    hook_file_path = hooks_dir / py_file

                    if not hook_file_path.exists():
                        result["missing_files"].append(py_file)
                        result["hook_files_exist"] = False

    if result["missing_files"]:
        result["errors"].append(f"Hook files not found: {', '.join(result['missing_files'])}")

    result["valid"] = result["has_hooks_field"] and result["hook_files_exist"]

    return result


def validate_agent_config(agent_config: Dict[str, Any], agents_dir: Path) -> Dict[str, Any]:
    """
    Validate agents/config.json structure and agent file references.

    Args:
        agent_config: Parsed config.json content
        agents_dir: Path to agents directory

    Returns:
        Validation result
    """
    result = {
        "valid": False,
        "has_agents_field": False,
        "has_routing_field": False,
        "agent_files_exist": True,
        "agent_count": 0,
        "missing_files": [],
        "orphaned_files": [],
        "errors": [],
        "warnings": [],
    }

    # Check for required fields
    if "agents" not in agent_config:
        result["errors"].append("Missing 'agents' field")
    else:
        result["has_agents_field"] = True

    if "routing" not in agent_config:
        result["errors"].append("Missing 'routing' field")
    else:
        result["has_routing_field"] = True

    if not result["has_agents_field"]:
        return result

    # Get registered agents
    agents = agent_config["agents"]
    result["agent_count"] = len(agents)
    registered_agents = set(agents.keys())

    # Find agent definition files
    agent_files = set()
    for agent_file in agents_dir.rglob("*.md"):
        # Skip README files
        if agent_file.name == "README.md":
            continue

        agent_name = agent_file.stem
        agent_files.add(agent_name)

    # Check for missing and orphaned
    missing = registered_agents - agent_files
    orphaned = agent_files - registered_agents

    if missing:
        result["missing_files"] = sorted(list(missing))
        result["agent_files_exist"] = False
        result["errors"].append(f"Agent definitions missing: {', '.join(sorted(missing))}")

    if orphaned:
        result["orphaned_files"] = sorted(list(orphaned))
        result["warnings"].append(
            f"Orphaned agent files (not registered): {', '.join(sorted(orphaned))}"
        )

    result["valid"] = (
        result["has_agents_field"] and result["has_routing_field"] and result["agent_files_exist"]
    )

    return result


def find_orphaned_files(plugin_root: Path) -> Dict[str, List[str]]:
    """
    Find files that are not referenced by any configuration.

    Args:
        plugin_root: Path to plugin root

    Returns:
        Dictionary of orphaned files by type
    """
    orphaned = {"python_files": [], "markdown_files": [], "json_files": []}

    # This is a simplified implementation
    # A full implementation would cross-reference all config files

    # Find all Python files in hooks
    hooks_dir = plugin_root / "hooks"
    if hooks_dir.exists():
        all_py_files = set(f.name for f in hooks_dir.glob("*.py"))

        # Load hooks.json to see what's referenced
        hooks_json_path = hooks_dir / "hooks.json"
        if hooks_json_path.exists():
            try:
                hooks_json = json.loads(hooks_json_path.read_text())
                referenced_files = set()

                for hook_matchers in hooks_json.get("hooks", {}).values():
                    for matcher in hook_matchers:
                        for hook_def in matcher.get("hooks", []):
                            command = hook_def.get("command", "")
                            import re

                            py_match = re.search(r"([a-z0-9_-]+\.py)", command)
                            if py_match:
                                referenced_files.add(py_match.group(1))

                # Orphaned = all files - referenced files - test files
                test_files = {f for f in all_py_files if f.startswith("test_")}
                orphaned["python_files"] = sorted(
                    list(all_py_files - referenced_files - test_files)
                )

            except json.JSONDecodeError:
                # Best-effort fallback: ignore optional failure.
                pass

    return orphaned


def get_plugin_health_score(plugin_root: Path) -> Dict[str, Any]:
    """
    Calculate overall plugin health score based on structure validation.

    Args:
        plugin_root: Path to plugin root

    Returns:
        Health score and breakdown
    """
    validation = validate_plugin_structure(plugin_root)

    score = 100
    deductions = []

    # Deduct for missing required files (critical)
    for file_path, file_info in validation["required_files"].items():
        if not file_info["exists"]:
            score -= 20
            deductions.append(f"Missing required file: {file_path} (-20)")

    # Deduct for configuration errors (high)
    if validation["plugin_json"].get("errors"):
        score -= 10
        deductions.append("plugin.json errors (-10)")

    if validation["hooks_json"].get("errors"):
        score -= 10
        deductions.append("hooks.json errors (-10)")

    if validation["agent_config"].get("errors"):
        score -= 10
        deductions.append("agent config errors (-10)")

    # Deduct for warnings (medium)
    total_warnings = (
        len(validation.get("warnings", []))
        + len(validation["plugin_json"].get("warnings", []))
        + len(validation["hooks_json"].get("warnings", []))
        + len(validation["agent_config"].get("warnings", []))
    )

    if total_warnings > 0:
        warning_deduction = min(total_warnings * 2, 20)
        score -= warning_deduction
        deductions.append(f"{total_warnings} warnings (-{warning_deduction})")

    score = max(0, score)  # Don't go below 0

    return {
        "score": score,
        "grade": _score_to_grade(score),
        "deductions": deductions,
        "validation": validation,
    }


def _score_to_grade(score: int) -> str:
    """Convert numeric score to letter grade."""
    if score >= 95:
        return "A+"
    elif score >= 90:
        return "A"
    elif score >= 85:
        return "B+"
    elif score >= 80:
        return "B"
    elif score >= 75:
        return "C+"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"
