"""
Agent validator for modular plugin architecture.

Validates agent markdown files have proper frontmatter and structure
for semantic routing in Claude Code.
"""

import re
from pathlib import Path
from typing import Any

import yaml


def validate_agent_files(plugin_root: Path) -> dict[str, Any]:
    """
    Validate all agent markdown files in a plugin.

    Args:
        plugin_root: Path to plugin root directory

    Returns:
        Validation result with agent details
    """
    result = {"valid": True, "agent_count": 0, "agents": [], "errors": [], "warnings": []}

    agents_dir = plugin_root / "agents"
    if not agents_dir.exists():
        result["warnings"].append("No agents directory found (this is optional)")
        return result

    # Find all .md files in agents directory
    agent_files = list(agents_dir.glob("**/*.md"))

    if not agent_files:
        result["warnings"].append("No agent markdown files found")
        return result

    result["agent_count"] = len(agent_files)

    # Validate each agent file
    for agent_file in agent_files:
        agent_validation = validate_agent_file(agent_file)
        result["agents"].append(agent_validation)

        if not agent_validation["valid"]:
            result["valid"] = False
            result["errors"].extend(agent_validation["errors"])

    return result


def validate_agent_file(agent_file: Path) -> dict[str, Any]:
    """
    Validate a single agent markdown file.

    Args:
        agent_file: Path to agent markdown file

    Returns:
        Validation result for the agent
    """
    result = {
        "file": str(agent_file.name),
        "path": str(agent_file),
        "valid": False,
        "frontmatter": {},
        "errors": [],
        "warnings": [],
    }

    try:
        content = agent_file.read_text(encoding="utf-8")
    except Exception as e:
        result["errors"].append(f"Failed to read file: {e}")
        return result

    # Parse frontmatter
    frontmatter = parse_frontmatter(content)

    if not frontmatter:
        result["errors"].append("No YAML frontmatter found")
        return result

    result["frontmatter"] = frontmatter

    # Validate required fields
    required_fields = ["name", "description"]

    for field in required_fields:
        if field not in frontmatter:
            result["errors"].append(f"Missing required frontmatter field: {field}")
        elif not frontmatter[field] or not str(frontmatter[field]).strip():
            result["errors"].append(f"Frontmatter field '{field}' is empty")

    # Validate description quality (for semantic routing)
    if "description" in frontmatter:
        description = str(frontmatter["description"])

        if len(description) < 20:
            result["warnings"].append(
                f"Description is very short ({len(description)} chars). "
                "Longer descriptions improve semantic routing."
            )

        # Check for generic phrases
        generic_phrases = ["helper", "utility", "general purpose"]
        description_lower = description.lower()

        for phrase in generic_phrases:
            if phrase in description_lower:
                result["warnings"].append(
                    f"Description contains generic phrase '{phrase}'. "
                    "Be specific for better semantic routing."
                )

    # Validate tier directory structure
    tier_check = validate_tier_directory(agent_file)
    if not tier_check["valid"]:
        result["warnings"].append(tier_check["warning"])

    # All checks passed if no errors
    result["valid"] = len(result["errors"]) == 0

    return result


def parse_frontmatter(content: str) -> dict[str, Any]:
    """
    Parse YAML frontmatter from markdown content.

    Args:
        content: Markdown file content

    Returns:
        Parsed frontmatter dictionary
    """
    # Match YAML frontmatter (--- ... ---)
    pattern = r"^---\s*\n(.*?)\n---\s*\n"
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        return {}

    yaml_content = match.group(1)

    try:
        frontmatter = yaml.safe_load(yaml_content)
        return frontmatter if isinstance(frontmatter, dict) else {}
    except yaml.YAMLError:
        return {}


def validate_tier_directory(agent_file: Path) -> dict[str, Any]:
    """
    Validate that agent is in a proper tier directory.

    Args:
        agent_file: Path to agent file

    Returns:
        Validation result for tier structure
    """
    allowed_tiers = ["tier-1-always-active", "tier-2-on-demand", "feature-workflow"]

    # Get parent directory name
    parent = agent_file.parent.name

    if parent in allowed_tiers:
        return {"valid": True, "tier": parent}

    # Check if agent is in a subdirectory of a tier
    for part in agent_file.parts:
        if part in allowed_tiers:
            return {"valid": True, "tier": part}

    return {"valid": False, "warning": f"Agent not in standard tier directory. Found in: {parent}"}


def check_unique_agent_names(agent_files: list[Path]) -> dict[str, Any]:
    """
    Check for duplicate agent names across files.

    Args:
        agent_files: List of agent markdown files

    Returns:
        Validation result with duplicates
    """
    result = {"valid": True, "unique": True, "duplicates": [], "agent_names": set()}

    names_to_files = {}

    for agent_file in agent_files:
        try:
            content = agent_file.read_text(encoding="utf-8")
            frontmatter = parse_frontmatter(content)

            if "name" in frontmatter:
                agent_name = frontmatter["name"]

                if agent_name in names_to_files:
                    result["unique"] = False
                    result["duplicates"].append(
                        {"name": agent_name, "files": [names_to_files[agent_name], str(agent_file)]}
                    )
                else:
                    names_to_files[agent_name] = str(agent_file)
                    result["agent_names"].add(agent_name)

        except Exception:
            # Skip files that can't be read
            continue

    result["valid"] = result["unique"]

    return result
