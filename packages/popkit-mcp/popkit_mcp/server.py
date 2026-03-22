#!/usr/bin/env python3
"""
PopKit MCP Server

Standalone MCP server that exposes PopKit skills, agents, and commands
as MCP tools, resources, and prompts. Any MCP-compatible tool (Cursor,
Codex, Copilot, etc.) can connect to this server to use PopKit.

MCP Tools:
    popkit/run_skill     - Invoke any PopKit skill by name
    popkit/spawn_agent   - Start an agent with a task
    popkit/power_mode    - Orchestrate multi-agent workflows
    popkit/get_context   - Retrieve project context
    popkit/health_check  - System status and diagnostics

MCP Resources:
    popkit://skills/{package}/{name}  - Skill definitions
    popkit://agents/{package}/{name}  - Agent definitions
    popkit://skills                   - Skills listing
    popkit://agents                   - Agents listing

MCP Prompts:
    agent/{name}  - Agent system prompt with task input
    skill/{name}  - Skill workflow prompt with args input

Usage:
    python server.py                          # stdio transport (default)
    python server.py --transport sse          # SSE transport
    python server.py --transport streamable-http --port 8080

Part of the PopKit v2.0 provider-agnostic architecture.
"""

import argparse
import os
from pathlib import Path
from typing import Dict, Optional

from mcp.server.fastmcp import FastMCP

from .prompts import (
    build_agent_prompt,
    build_skill_prompt,
)
from .resources import (
    build_agent_list_resource,
    build_skill_list_resource,
    get_agent_resource_content,
    get_agent_resource_uri,
    get_skill_resource_content,
    get_skill_resource_uri,
)
from .tool_registry import (
    AgentDefinition,
    SkillDefinition,
    build_registry,
)

# =============================================================================
# Server Setup
# =============================================================================


def _resolve_packages_dir() -> Path:
    """Resolve the PopKit packages directory.

    Resolution order:
    1. POPKIT_PACKAGES env var
    2. POPKIT_HOME/packages
    3. Sibling to this package (development mode)
    """
    # Explicit override
    pkg_env = os.environ.get("POPKIT_PACKAGES")
    if pkg_env:
        return Path(pkg_env)

    # POPKIT_HOME
    home_env = os.environ.get("POPKIT_HOME")
    if home_env:
        return Path(home_env) / "packages"

    # Development mode: sibling packages
    dev_packages = Path(__file__).parent.parent
    if (dev_packages / "popkit-core").is_dir():
        return dev_packages

    # Platform default
    try:
        from popkit_shared.utils.home import get_popkit_packages_dir

        return get_popkit_packages_dir()
    except ImportError:
        return Path.home() / ".popkit" / "packages"


def create_server(packages_dir: Optional[Path] = None) -> FastMCP:
    """Create and configure the PopKit MCP server.

    Args:
        packages_dir: Path to PopKit packages. Auto-detected if None.

    Returns:
        Configured FastMCP server instance
    """
    if packages_dir is None:
        packages_dir = _resolve_packages_dir()

    # Build the registry
    registry = build_registry(packages_dir)
    skills = registry["skills"]
    agents = registry["agents"]
    counts = registry["counts"]

    # Create server
    mcp = FastMCP(
        "PopKit",
        instructions=(
            f"PopKit orchestration engine with {counts['skills']} skills, "
            f"{counts['agents']} agents, and {counts['commands']} commands. "
            "Use popkit/run_skill to execute skills, popkit/spawn_agent to "
            "start agents, and popkit/get_context for project information."
        ),
    )

    # Build lookup dicts
    skill_map: Dict[str, SkillDefinition] = {s.name: s for s in skills}
    agent_map: Dict[str, AgentDefinition] = {a.name: a for a in agents}

    # =========================================================================
    # MCP Tools
    # =========================================================================

    @mcp.tool()
    def run_skill(skill_name: str, args: str = "") -> str:
        """Invoke a PopKit skill by name.

        Skills are workflow-based automation definitions. Each skill
        contains a multi-step workflow with agent assignments,
        user decision points, and output handling.

        Args:
            skill_name: Name of the skill to run (e.g., "power-mode", "analyze-project")
            args: Optional arguments to pass to the skill

        Returns:
            Skill content and instructions for execution
        """
        skill = skill_map.get(skill_name)
        if not skill:
            available = ", ".join(sorted(skill_map.keys()))
            return f"Unknown skill: {skill_name}. Available skills: {available}"

        content = get_skill_resource_content(skill)
        return build_skill_prompt(skill_name, content, args)

    @mcp.tool()
    def spawn_agent(agent_name: str, task: str) -> str:
        """Start a PopKit agent with a specific task.

        Agents are specialized AI personas with defined tools, constraints,
        and behavior patterns. Each agent has a tier (always-active or on-demand)
        and a set of allowed/disallowed tools.

        Args:
            agent_name: Name of the agent (e.g., "documentation-maintainer", "bug-whisperer")
            task: Description of the task to assign

        Returns:
            Agent prompt with system instructions and task
        """
        agent = agent_map.get(agent_name)
        if not agent:
            available = ", ".join(sorted(agent_map.keys()))
            return f"Unknown agent: {agent_name}. Available agents: {available}"

        return build_agent_prompt(agent, task)

    @mcp.tool()
    def power_mode(task: str, agents_list: str = "") -> str:
        """Orchestrate a multi-agent workflow for complex tasks.

        Power Mode coordinates multiple agents working in parallel on
        different aspects of a complex task, with sync barriers and
        shared context.

        Args:
            task: Description of the complex task
            agents_list: Comma-separated agent names (auto-selected if empty)

        Returns:
            Orchestration instructions
        """
        # Get power mode skill if available
        power_skill = skill_map.get("power-mode")
        if power_skill:
            content = get_skill_resource_content(power_skill)
        else:
            content = "Power Mode skill not found. Using basic orchestration."

        selected_agents = []
        if agents_list:
            for name in agents_list.split(","):
                name = name.strip()
                if name in agent_map:
                    selected_agents.append(agent_map[name])

        parts = [
            "# PopKit Power Mode",
            "",
            f"**Task:** {task}",
            "",
        ]

        if selected_agents:
            parts.append("**Selected Agents:**")
            for agent in selected_agents:
                parts.append(f"- {agent.name} ({agent.tier}): {agent.description[:80]}")
            parts.append("")

        parts.append("## Workflow")
        parts.append("")
        parts.append(content)

        return "\n".join(parts)

    @mcp.tool()
    def get_context(context_type: str = "project") -> str:
        """Retrieve project or system context.

        Args:
            context_type: Type of context - "project" (project info),
                "skills" (available skills), "agents" (available agents),
                "all" (everything)

        Returns:
            Formatted context information
        """
        parts = []

        if context_type in ("project", "all"):
            parts.append("# PopKit Context")
            parts.append("")
            parts.append(f"- Packages directory: {packages_dir}")
            parts.append(f"- Skills: {counts['skills']}")
            parts.append(f"- Agents: {counts['agents']}")
            parts.append(f"- Commands: {counts['commands']}")
            parts.append("")

        if context_type in ("skills", "all"):
            parts.append(build_skill_list_resource(skills))
            parts.append("")

        if context_type in ("agents", "all"):
            parts.append(build_agent_list_resource(agents))
            parts.append("")

        if not parts:
            return f"Unknown context type: {context_type}. Use: project, skills, agents, all"

        return "\n".join(parts)

    @mcp.tool()
    def health_check() -> str:
        """Check PopKit system health and status.

        Returns system diagnostics including:
        - Installed packages and their versions
        - Available providers
        - Package integrity
        - MCP server status

        Returns:
            Formatted health report
        """
        lines = [
            "# PopKit Health Check",
            "",
            f"## Packages Directory: {packages_dir}",
            f"- Exists: {packages_dir.is_dir()}",
            "",
            "## Registry",
            f"- Skills: {counts['skills']}",
            f"- Agents: {counts['agents']}",
            f"- Commands: {counts['commands']}",
            "",
        ]

        # Check provider availability
        try:
            from popkit_shared.providers import detect_providers

            providers = detect_providers()
            lines.append("## Providers")
            for p in providers:
                status = "available" if p.is_available else "not available"
                lines.append(f"- {p.display_name}: {status}")
                if p.version:
                    lines.append(f"  Version: {p.version}")
        except ImportError:
            lines.append("## Providers")
            lines.append("- Provider detection not available (popkit_shared not installed)")

        lines.append("")
        lines.append("## Skill Details")
        by_package: dict[str, int] = {}
        for s in skills:
            by_package[s.package] = by_package.get(s.package, 0) + 1
        for pkg, count in sorted(by_package.items()):
            lines.append(f"- {pkg}: {count} skills")

        lines.append("")
        lines.append("## Agent Details")
        by_tier: dict[str, int] = {"always-active": 0, "on-demand": 0}
        for a in agents:
            by_tier[a.tier] = by_tier.get(a.tier, 0) + 1
        for tier, count in sorted(by_tier.items()):
            lines.append(f"- {tier}: {count} agents")

        return "\n".join(lines)

    # =========================================================================
    # MCP Resources
    # =========================================================================

    @mcp.resource("popkit://skills")
    def list_skills() -> str:
        """List all available PopKit skills."""
        return build_skill_list_resource(skills)

    @mcp.resource("popkit://agents")
    def list_agents() -> str:
        """List all available PopKit agents."""
        return build_agent_list_resource(agents)

    # Register individual skill and agent resources
    for skill in skills:
        # Capture skill in closure
        def _make_skill_resource(s: SkillDefinition):
            @mcp.resource(get_skill_resource_uri(s))
            def _resource() -> str:
                return get_skill_resource_content(s)

            return _resource

        _make_skill_resource(skill)

    for agent in agents:

        def _make_agent_resource(a: AgentDefinition):
            @mcp.resource(get_agent_resource_uri(a))
            def _resource() -> str:
                return get_agent_resource_content(a)

            return _resource

        _make_agent_resource(agent)

    # =========================================================================
    # MCP Prompts
    # =========================================================================

    for agent in agents:

        def _make_agent_prompt(a: AgentDefinition):
            @mcp.prompt(name=f"agent/{a.name}", description=a.description)
            def _prompt(task: str) -> str:
                return build_agent_prompt(a, task)

            return _prompt

        _make_agent_prompt(agent)

    for skill in skills:

        def _make_skill_prompt(s: SkillDefinition):
            @mcp.prompt(name=f"skill/{s.name}", description=s.description)
            def _prompt(args: str = "") -> str:
                content = get_skill_resource_content(s)
                return build_skill_prompt(s.name, content, args)

            return _prompt

        _make_skill_prompt(skill)

    return mcp


# =============================================================================
# Entry Point
# =============================================================================


def main():
    """Main entry point for the PopKit MCP server."""
    parser = argparse.ArgumentParser(description="PopKit MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="MCP transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for HTTP-based transports (default: 8080)",
    )
    parser.add_argument(
        "--packages",
        type=str,
        default=None,
        help="Path to PopKit packages directory",
    )

    args = parser.parse_args()

    packages_dir = Path(args.packages) if args.packages else None
    server = create_server(packages_dir)

    if args.transport == "stdio":
        server.run(transport="stdio")
    elif args.transport == "sse":
        server.run(transport="sse", port=args.port)
    else:
        server.run(transport="streamable-http", port=args.port)


if __name__ == "__main__":
    main()
