#!/usr/bin/env python3
"""
PopKit MCP Prompts

Exposes agent system prompts as MCP prompts, allowing MCP clients
to use PopKit agents as prompt templates.

Part of the PopKit v2.0 MCP server.
"""

from typing import List

from .tool_registry import AgentDefinition


def build_agent_prompt(agent: AgentDefinition, task: str = "") -> str:
    """Build a complete agent prompt from an agent definition.

    Combines the agent's AGENT.md content with a task description
    to create a prompt that any LLM can execute.

    Args:
        agent: Agent definition with system prompt content
        task: User's task description

    Returns:
        Complete prompt string
    """
    parts = []

    # System context from AGENT.md
    parts.append(f"# Agent: {agent.name}")
    parts.append(f"Package: {agent.package}")
    parts.append(f"Tier: {agent.tier}")

    if agent.tools:
        parts.append(f"Available tools: {', '.join(agent.tools)}")

    parts.append("")
    parts.append("## Agent Instructions")
    parts.append("")
    parts.append(agent.content)

    if task:
        parts.append("")
        parts.append("## Task")
        parts.append("")
        parts.append(task)

    return "\n".join(parts)


def build_skill_prompt(skill_name: str, skill_content: str, args: str = "") -> str:
    """Build a prompt for executing a skill.

    Args:
        skill_name: Name of the skill
        skill_content: Full SKILL.md content
        args: Optional arguments for the skill

    Returns:
        Complete prompt string
    """
    parts = [
        f"# Execute Skill: {skill_name}",
        "",
        "Follow the workflow defined below to complete this skill.",
        "",
        skill_content,
    ]

    if args:
        parts.extend(["", "## Arguments", "", args])

    return "\n".join(parts)


def get_agent_prompt_args(agent: AgentDefinition) -> List[dict]:
    """Get the prompt arguments for an agent.

    Args:
        agent: Agent definition

    Returns:
        List of prompt argument descriptors
    """
    return [
        {
            "name": "task",
            "description": f"The task to assign to the {agent.name} agent",
            "required": True,
        }
    ]


def get_skill_prompt_args(skill_name: str) -> List[dict]:
    """Get the prompt arguments for a skill.

    Args:
        skill_name: Name of the skill

    Returns:
        List of prompt argument descriptors
    """
    return [
        {
            "name": "args",
            "description": f"Arguments to pass to the {skill_name} skill",
            "required": False,
        }
    ]
