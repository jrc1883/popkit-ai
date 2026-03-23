#!/usr/bin/env python3
"""
PopKit MCP Resources

Exposes AGENT.md and SKILL.md files as MCP resources, allowing
MCP clients to read agent/skill definitions and documentation.

Part of the PopKit v2.0 MCP server.
"""

from typing import List

from .tool_registry import AgentDefinition, SkillDefinition


def get_skill_resource_uri(skill: SkillDefinition) -> str:
    """Get the MCP resource URI for a skill.

    Args:
        skill: Skill definition

    Returns:
        Resource URI string (e.g., "popkit://skills/popkit-core/power-mode")
    """
    return f"popkit://skills/{skill.package}/{skill.name}"


def get_agent_resource_uri(agent: AgentDefinition) -> str:
    """Get the MCP resource URI for an agent.

    Args:
        agent: Agent definition

    Returns:
        Resource URI string (e.g., "popkit://agents/popkit-core/documentation-maintainer")
    """
    return f"popkit://agents/{agent.package}/{agent.name}"


def get_skill_resource_content(skill: SkillDefinition) -> str:
    """Get the full content of a skill's SKILL.md for MCP resource.

    Args:
        skill: Skill definition

    Returns:
        Full SKILL.md content
    """
    try:
        return skill.path.read_text(encoding="utf-8")
    except (IOError, UnicodeDecodeError):
        return f"# {skill.name}\n\n{skill.description}"


def get_agent_resource_content(agent: AgentDefinition) -> str:
    """Get the full content of an agent's AGENT.md for MCP resource.

    Args:
        agent: Agent definition

    Returns:
        Full AGENT.md content
    """
    try:
        return agent.path.read_text(encoding="utf-8")
    except (IOError, UnicodeDecodeError):
        return f"# {agent.name}\n\n{agent.description}"


def build_skill_list_resource(skills: List[SkillDefinition]) -> str:
    """Build a markdown resource listing all available skills.

    Args:
        skills: List of skill definitions

    Returns:
        Formatted markdown listing
    """
    lines = ["# PopKit Skills\n"]

    # Group by package
    by_package: dict[str, list[SkillDefinition]] = {}
    for skill in skills:
        by_package.setdefault(skill.package, []).append(skill)

    for package, pkg_skills in sorted(by_package.items()):
        lines.append(f"\n## {package}\n")
        for skill in sorted(pkg_skills, key=lambda s: s.name):
            desc = (
                skill.description[:100] + "..."
                if len(skill.description) > 100
                else skill.description
            )
            lines.append(f"- **{skill.name}**: {desc}")

    return "\n".join(lines)


def build_agent_list_resource(agents: List[AgentDefinition]) -> str:
    """Build a markdown resource listing all available agents.

    Args:
        agents: List of agent definitions

    Returns:
        Formatted markdown listing
    """
    lines = ["# PopKit Agents\n"]

    by_package: dict[str, list[AgentDefinition]] = {}
    for agent in agents:
        by_package.setdefault(agent.package, []).append(agent)

    for package, pkg_agents in sorted(by_package.items()):
        lines.append(f"\n## {package}\n")
        for agent in sorted(pkg_agents, key=lambda a: a.name):
            tier_badge = "[always-active]" if agent.tier == "always-active" else "[on-demand]"
            desc = (
                agent.description[:100] + "..."
                if len(agent.description) > 100
                else agent.description
            )
            lines.append(f"- **{agent.name}** {tier_badge}: {desc}")

    return "\n".join(lines)
