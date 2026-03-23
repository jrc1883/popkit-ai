#!/usr/bin/env python3
"""
PopKit Tool Registry

Scans PopKit packages for skills, agents, and commands, then registers
them as MCP tools. This is the bridge between PopKit's file-based
definitions and the MCP server's runtime tool registry.

Part of the PopKit v2.0 MCP server.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

import yaml


@dataclass
class SkillDefinition:
    """A PopKit skill parsed from SKILL.md."""

    name: str
    description: str
    package: str
    path: Path
    inputs: List[Dict[str, Any]] = field(default_factory=list)
    outputs: List[Dict[str, Any]] = field(default_factory=list)
    hooks: Dict[str, Any] = field(default_factory=dict)
    content: str = ""


@dataclass
class AgentDefinition:
    """A PopKit agent parsed from AGENT.md."""

    name: str
    description: str
    package: str
    path: Path
    tier: str = "on-demand"
    tools: List[str] = field(default_factory=list)
    model: str = "inherit"
    content: str = ""


@dataclass
class CommandDefinition:
    """A PopKit command parsed from a command .md file."""

    name: str
    description: str
    package: str
    path: Path
    argument_hint: str = ""
    content: str = ""


def _parse_frontmatter(file_path: Path) -> tuple[Dict[str, Any], str]:
    """Parse YAML frontmatter from a markdown file.

    Args:
        file_path: Path to the markdown file

    Returns:
        Tuple of (frontmatter dict, body content)
    """
    try:
        text = file_path.read_text(encoding="utf-8")
    except (IOError, UnicodeDecodeError):
        return {}, ""

    if not text.startswith("---"):
        return {}, text

    # Find closing ---
    end_idx = text.find("---", 3)
    if end_idx == -1:
        return {}, text

    frontmatter_str = text[3:end_idx].strip()
    body = text[end_idx + 3 :].strip()

    try:
        frontmatter = yaml.safe_load(frontmatter_str) or {}
    except yaml.YAMLError:
        return {}, text

    return frontmatter, body


def scan_skills(packages_dir: Path) -> List[SkillDefinition]:
    """Scan PopKit packages for skill definitions.

    Looks for SKILL.md files in packages/*/skills/*/SKILL.md

    Args:
        packages_dir: Path to the packages directory

    Returns:
        List of parsed SkillDefinition objects
    """
    skills = []

    for package_dir in _iter_package_dirs(packages_dir):
        package_name = package_dir.name
        skills_dir = package_dir / "skills"
        if not skills_dir.is_dir():
            continue

        for skill_dir in sorted(skills_dir.iterdir()):
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.is_file():
                continue

            fm, body = _parse_frontmatter(skill_file)
            if not fm.get("name"):
                continue

            skills.append(
                SkillDefinition(
                    name=fm["name"],
                    description=fm.get("description", ""),
                    package=package_name,
                    path=skill_file,
                    inputs=fm.get("inputs", []),
                    outputs=fm.get("outputs", []),
                    hooks=fm.get("hooks", {}),
                    content=body,
                )
            )

    return skills


def scan_agents(packages_dir: Path) -> List[AgentDefinition]:
    """Scan PopKit packages for agent definitions.

    Looks for AGENT.md files in packages/*/agents/*/*/AGENT.md

    Args:
        packages_dir: Path to the packages directory

    Returns:
        List of parsed AgentDefinition objects
    """
    agents = []

    for package_dir in _iter_package_dirs(packages_dir):
        package_name = package_dir.name
        agents_dir = package_dir / "agents"
        if not agents_dir.is_dir():
            continue

        # Agents are in tier directories: agents/tier-1-always-active/name/AGENT.md
        for tier_dir in sorted(agents_dir.iterdir()):
            if not tier_dir.is_dir():
                continue

            tier = "always-active" if "tier-1" in tier_dir.name else "on-demand"

            for agent_dir in sorted(tier_dir.iterdir()):
                agent_file = agent_dir / "AGENT.md"
                if not agent_file.is_file():
                    continue

                fm, body = _parse_frontmatter(agent_file)
                if not fm.get("name"):
                    continue

                agents.append(
                    AgentDefinition(
                        name=fm["name"],
                        description=fm.get("description", ""),
                        package=package_name,
                        path=agent_file,
                        tier=tier,
                        tools=fm.get("tools", []),
                        model=fm.get("model", "inherit"),
                        content=body,
                    )
                )

    return agents


def scan_commands(packages_dir: Path) -> List[CommandDefinition]:
    """Scan PopKit packages for command definitions.

    Looks for .md files in packages/*/commands/

    Args:
        packages_dir: Path to the packages directory

    Returns:
        List of parsed CommandDefinition objects
    """
    commands = []

    for package_dir in _iter_package_dirs(packages_dir):
        package_name = package_dir.name
        commands_dir = package_dir / "commands"
        if not commands_dir.is_dir():
            continue

        for cmd_file in sorted(commands_dir.glob("*.md")):
            fm, body = _parse_frontmatter(cmd_file)
            name = cmd_file.stem

            commands.append(
                CommandDefinition(
                    name=name,
                    description=fm.get("description", ""),
                    package=package_name,
                    path=cmd_file,
                    argument_hint=fm.get("argument-hint", ""),
                    content=body,
                )
            )

    return commands


def _iter_package_dirs(packages_dir: Path):
    """Iterate over PopKit package directories.

    Yields directories that look like PopKit packages (have .claude-plugin/
    or popkit-package.yaml).

    Args:
        packages_dir: Path to the packages directory
    """
    if not packages_dir.is_dir():
        return

    for entry in sorted(packages_dir.iterdir()):
        if not entry.is_dir():
            continue
        # Skip non-package directories
        if entry.name in ("docs", "shared-py", "popkit-mcp", "popkit-cli", "__pycache__"):
            continue
        # Check for package markers
        has_plugin_json = (entry / ".claude-plugin" / "plugin.json").is_file()
        has_manifest = (entry / "popkit-package.yaml").is_file()
        if has_plugin_json or has_manifest:
            yield entry


def build_registry(packages_dir: Path) -> Dict[str, Any]:
    """Build a complete registry of all PopKit tools.

    Args:
        packages_dir: Path to the packages directory

    Returns:
        Dict with skills, agents, commands lists and counts
    """
    skills = scan_skills(packages_dir)
    agents = scan_agents(packages_dir)
    commands = scan_commands(packages_dir)

    return {
        "skills": skills,
        "agents": agents,
        "commands": commands,
        "counts": {
            "skills": len(skills),
            "agents": len(agents),
            "commands": len(commands),
            "total": len(skills) + len(agents) + len(commands),
        },
    }
