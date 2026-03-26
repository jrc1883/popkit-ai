#!/usr/bin/env python3
"""
PopKit MCP Server

Standalone MCP server that exposes PopKit skills, agents, and commands
as MCP tools, resources, and prompts. Any MCP-compatible tool (Cursor,
Codex, Copilot, etc.) can connect to this server to use PopKit.

MCP Tools:
    popkit/run_skill        - Return skill prompt for LLM interpretation
    popkit/execute_skill    - Run skill workflow server-side
    popkit/spawn_agent      - Start an agent with a task
    popkit/power_mode       - Orchestrate multi-agent workflows
    popkit/get_context      - Retrieve project context
    popkit/health_check     - System status and diagnostics
    popkit/validate_command - Validate a shell command for safety
    popkit/reload           - Reload package registry from disk

Usage:
    python -m popkit_mcp.server                                    # stdio (default)
    python -m popkit_mcp.server --transport sse --port 8080        # SSE
    python -m popkit_mcp.server --transport streamable-http        # streamable HTTP

Part of the PopKit v2.0 provider-agnostic architecture.
"""

import argparse
import logging
import os
import signal
from pathlib import Path
from typing import Dict, List, Optional

from mcp.server.fastmcp import FastMCP

from .prompts import build_agent_prompt, build_skill_prompt
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

logger = logging.getLogger("popkit-mcp")

# =============================================================================
# Cloud Config Resolution
# =============================================================================

DEFAULT_API_URL = "https://api.thehouseofdeals.com"


def _resolve_cloud_config() -> tuple[str, str]:
    """Resolve API key and URL from env var or config file.

    Resolution order:
    1. POPKIT_API_KEY env var (for CI/advanced users)
    2. ~/.popkit/cloud-config.json (primary — written by `popkit login`)
    3. ~/.claude/popkit/cloud-config.json (legacy fallback)

    Returns:
        Tuple of (api_key, api_url). api_key may be empty if not configured.
    """
    import json

    # 1. Environment variable
    api_key = os.environ.get("POPKIT_API_KEY", "")
    api_url = os.environ.get("POPKIT_API_URL", DEFAULT_API_URL)
    if api_key:
        return api_key, api_url

    # 2. Config files
    config_paths = [
        Path.home() / ".popkit" / "cloud-config.json",
        Path.home() / ".claude" / "popkit" / "cloud-config.json",
    ]

    for config_path in config_paths:
        if config_path.exists():
            try:
                config = json.loads(config_path.read_text())
                key = config.get("api_key", "")
                url = config.get("api_url", DEFAULT_API_URL)
                if key:
                    return key, url
            except (json.JSONDecodeError, OSError):
                continue

    return "", api_url


# =============================================================================
# Content Cache
# =============================================================================


class ContentCache:
    """In-memory cache for file content with mtime-based invalidation."""

    def __init__(self):
        self._cache: Dict[str, tuple[float, str]] = {}  # path -> (mtime, content)

    def get(self, path: Path) -> Optional[str]:
        """Get cached content if file hasn't been modified."""
        key = str(path)
        if key in self._cache:
            cached_mtime, cached_content = self._cache[key]
            try:
                current_mtime = path.stat().st_mtime
                if current_mtime <= cached_mtime:
                    return cached_content
            except OSError as exc:
                logger.debug("ContentCache.get: stat failed for %s: %s", path, exc)
        return None

    def put(self, path: Path, content: str) -> None:
        """Cache content with current mtime."""
        try:
            mtime = path.stat().st_mtime
            self._cache[str(path)] = (mtime, content)
        except OSError as exc:
            logger.debug("ContentCache.put: stat failed for %s: %s", path, exc)

    def invalidate(self) -> None:
        """Clear the entire cache."""
        self._cache.clear()


# =============================================================================
# Server Setup
# =============================================================================


def _resolve_packages_dir() -> Path:
    """Resolve the PopKit packages directory.

    Resolution order:
    1. POPKIT_PACKAGES env var
    2. POPKIT_HOME/packages
    3. Sibling to this package (development mode)
    4. Platform default (~/.popkit/packages)
    """
    pkg_env = os.environ.get("POPKIT_PACKAGES")
    if pkg_env:
        return Path(pkg_env)

    home_env = os.environ.get("POPKIT_HOME")
    if home_env:
        return Path(home_env) / "packages"

    # Development mode: sibling packages
    dev_packages = Path(__file__).parent.parent
    if (dev_packages / "popkit-core").is_dir():
        return dev_packages

    try:
        from popkit_shared.utils.home import get_popkit_packages_dir

        return get_popkit_packages_dir()
    except ImportError:
        return Path.home() / ".popkit" / "packages"


# =============================================================================
# Command Validation
# =============================================================================

# Patterns that are always dangerous
BLOCKED_PATTERNS = [
    "rm -rf /",
    "rm -rf ~",
    "mkfs.",
    "dd if=/dev/zero",
    ":(){:|:&};:",
    "chmod -R 777 /",
    "> /dev/sda",
    "mv / ",
]

# Commands that need caution
CAUTION_COMMANDS = [
    "rm",
    "rmdir",
    "git reset --hard",
    "git push --force",
    "git push -f",
    "git clean -f",
    "DROP TABLE",
    "DROP DATABASE",
    "TRUNCATE",
    "DELETE FROM",
    "sudo",
    "curl | sh",
    "curl | bash",
    "wget | sh",
    "chmod 777",
]


def _validate_command(command: str) -> dict:
    """Validate a shell command for safety.

    Returns:
        Dict with 'safe' bool, 'risk_level' str, and 'warnings' list
    """
    warnings = []
    risk_level = "safe"

    cmd_lower = command.lower().strip()

    # Check blocked patterns
    for pattern in BLOCKED_PATTERNS:
        if pattern in cmd_lower:
            return {
                "safe": False,
                "risk_level": "blocked",
                "warnings": [f"Blocked: contains dangerous pattern '{pattern}'"],
            }

    # Check caution commands
    for caution in CAUTION_COMMANDS:
        if caution.lower() in cmd_lower:
            warnings.append(f"Caution: uses '{caution}' which can be destructive")
            risk_level = "caution"

    # Check for piping to shell
    if "|" in command and any(sh in cmd_lower for sh in ["sh", "bash", "zsh"]):
        warnings.append("Caution: piping to shell can execute arbitrary code")
        risk_level = "caution"

    return {
        "safe": risk_level != "blocked",
        "risk_level": risk_level,
        "warnings": warnings,
    }


# =============================================================================
# Server Factory
# =============================================================================


def create_server(packages_dir: Optional[Path] = None) -> FastMCP:
    """Create and configure the PopKit MCP server.

    Args:
        packages_dir: Path to PopKit packages. Auto-detected if None.

    Returns:
        Configured FastMCP server instance
    """
    if packages_dir is None:
        packages_dir = _resolve_packages_dir()

    # Build the registry (cached for lifetime of server)
    content_cache = ContentCache()

    if packages_dir.is_dir():
        registry = build_registry(packages_dir)
    else:
        logger.warning("Packages directory not found: %s", packages_dir)
        registry = {
            "skills": [],
            "agents": [],
            "commands": [],
            "counts": {"skills": 0, "agents": 0, "commands": 0, "total": 0},
        }

    skills: List[SkillDefinition] = registry["skills"]
    agents: List[AgentDefinition] = registry["agents"]
    counts: Dict = registry["counts"]

    # Create server with recommended production settings
    mcp = FastMCP(
        "PopKit",
        instructions=(
            f"PopKit orchestration engine with {counts['skills']} skills, "
            f"{counts['agents']} agents, and {counts['commands']} commands. "
            "Use run_skill to get skill prompts for LLM interpretation, "
            "execute_skill for server-side workflow execution, "
            "spawn_agent to start agents, and get_context for project info."
        ),
    )

    # Build lookup dicts
    skill_map: Dict[str, SkillDefinition] = {s.name: s for s in skills}
    agent_map: Dict[str, AgentDefinition] = {a.name: a for a in agents}

    # =========================================================================
    # Helper for cached content
    # =========================================================================

    def _get_skill_content(skill: SkillDefinition) -> str:
        """Get skill content with caching."""
        cached = content_cache.get(skill.path)
        if cached is not None:
            return cached
        content = get_skill_resource_content(skill)
        content_cache.put(skill.path, content)
        return content

    def _get_agent_content(agent: AgentDefinition) -> str:
        """Get agent content with caching."""
        cached = content_cache.get(agent.path)
        if cached is not None:
            return cached
        content = get_agent_resource_content(agent)
        content_cache.put(agent.path, content)
        return content

    # =========================================================================
    # MCP Tools
    # =========================================================================

    @mcp.tool()
    def run_skill(skill_name: str, args: str = "") -> str:
        """Return a PopKit skill's workflow as a prompt for the LLM to interpret.

        Use this when the connected LLM is capable of following multi-step
        workflows defined in markdown. The skill content includes workflow
        steps, agent assignments, and decision points.

        Args:
            skill_name: Name of the skill (e.g., "analyze-project", "code-review")
            args: Optional arguments to pass to the skill

        Returns:
            Skill content formatted as an executable prompt
        """
        try:
            skill = skill_map.get(skill_name)
            if not skill:
                available = ", ".join(sorted(skill_map.keys()))
                return f"Unknown skill: '{skill_name}'. Available skills: {available}"

            content = _get_skill_content(skill)
            return build_skill_prompt(skill_name, content, args)
        except Exception as e:
            logger.exception("Error in run_skill(%s)", skill_name)
            return f"Error loading skill '{skill_name}': {e}"

    @mcp.tool()
    def execute_skill(skill_name: str, args: str = "") -> str:
        """Execute a PopKit skill's workflow server-side.

        Use this when the connected tool cannot interpret workflow markdown.
        The server parses the workflow definition and returns structured
        step-by-step instructions with the current step to execute.

        Args:
            skill_name: Name of the skill to execute
            args: Optional arguments

        Returns:
            Structured workflow execution plan with steps
        """
        try:
            skill = skill_map.get(skill_name)
            if not skill:
                available = ", ".join(sorted(skill_map.keys()))
                return f"Unknown skill: '{skill_name}'. Available skills: {available}"

            # Parse the workflow from frontmatter
            content = _get_skill_content(skill)

            # Build execution plan from skill definition
            parts = [
                f"# Executing Skill: {skill_name}",
                f"Package: {skill.package}",
                "",
            ]

            if skill.inputs:
                parts.append("## Inputs")
                for inp in skill.inputs:
                    required = " (required)" if inp.get("required") else ""
                    parts.append(f"- {inp.get('field', 'unknown')}{required}")
                parts.append("")

            if skill.outputs:
                parts.append("## Expected Outputs")
                for out in skill.outputs:
                    parts.append(f"- {out.get('field', 'unknown')}: {out.get('type', 'any')}")
                parts.append("")

            if args:
                parts.append(f"## Arguments: {args}")
                parts.append("")

            parts.append("## Workflow Steps")
            parts.append("")
            parts.append(
                "Follow these steps in order. Each step describes what to do and what tool to use."
            )
            parts.append("")
            parts.append(content)

            return "\n".join(parts)
        except Exception as e:
            logger.exception("Error in execute_skill(%s)", skill_name)
            return f"Error executing skill '{skill_name}': {e}"

    @mcp.tool()
    def spawn_agent(agent_name: str, task: str) -> str:
        """Start a PopKit agent with a specific task.

        Returns the agent's system prompt and instructions combined
        with the task description. The connected LLM should adopt
        the agent's persona and constraints while executing the task.

        Args:
            agent_name: Name of the agent (e.g., "code-reviewer", "bug-whisperer")
            task: Description of the task to assign

        Returns:
            Agent prompt with system instructions and task
        """
        try:
            agent = agent_map.get(agent_name)
            if not agent:
                available = ", ".join(sorted(agent_map.keys()))
                return f"Unknown agent: '{agent_name}'. Available agents: {available}"

            return build_agent_prompt(agent, task)
        except Exception as e:
            logger.exception("Error in spawn_agent(%s)", agent_name)
            return f"Error spawning agent '{agent_name}': {e}"

    @mcp.tool()
    def power_mode(task: str, agents_list: str = "") -> str:
        """Orchestrate a multi-agent workflow for complex tasks.

        Coordinates multiple agents working on different aspects of a
        complex task with shared context and coordination.

        Args:
            task: Description of the complex task
            agents_list: Comma-separated agent names (auto-selected if empty)

        Returns:
            Orchestration instructions with agent assignments
        """
        try:
            power_skill = skill_map.get("power-mode")
            if power_skill:
                content = _get_skill_content(power_skill)
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
        except Exception as e:
            logger.exception("Error in power_mode")
            return f"Error in power mode: {e}"

    @mcp.tool()
    def get_context(context_type: str = "project") -> str:
        """Retrieve project or system context.

        Args:
            context_type: One of "project", "skills", "agents", "all"

        Returns:
            Formatted context information
        """
        try:
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
                return f"Unknown context type: '{context_type}'. Use: project, skills, agents, all"

            return "\n".join(parts)
        except Exception as e:
            logger.exception("Error in get_context")
            return f"Error getting context: {e}"

    @mcp.tool()
    def health_check() -> str:
        """Check PopKit system health and diagnostics.

        Returns:
            Formatted health report with package and provider status
        """
        try:
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

            # Provider availability
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
                lines.append("- Provider detection unavailable (popkit_shared not installed)")

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

            lines.append("")
            lines.append(f"## Cache: {len(content_cache._cache)} entries")

            return "\n".join(lines)
        except Exception as e:
            logger.exception("Error in health_check")
            return f"Error in health check: {e}"

    @mcp.tool()
    def validate_command(command: str) -> str:
        """Validate a shell command for safety before execution.

        Checks for dangerous patterns (rm -rf /, fork bombs, etc.)
        and flags commands that need caution (git push --force, sudo, etc.).

        Args:
            command: The shell command to validate

        Returns:
            Safety assessment with risk level and any warnings
        """
        try:
            result = _validate_command(command)
            parts = [f"## Command Validation: `{command[:100]}`", ""]

            if result["safe"]:
                if result["risk_level"] == "safe":
                    parts.append("**Status:** SAFE")
                else:
                    parts.append("**Status:** PROCEED WITH CAUTION")
            else:
                parts.append("**Status:** BLOCKED")

            parts.append(f"**Risk Level:** {result['risk_level']}")

            if result["warnings"]:
                parts.append("")
                parts.append("**Warnings:**")
                for w in result["warnings"]:
                    parts.append(f"- {w}")

            return "\n".join(parts)
        except Exception as e:
            return f"Error validating command: {e}"

    @mcp.tool()
    def reload() -> str:
        """Reload the PopKit package registry from disk.

        Use after installing new packages or modifying skill/agent definitions.

        Returns:
            Summary of reloaded registry
        """
        nonlocal skills, agents, counts, skill_map, agent_map

        try:
            content_cache.invalidate()

            if packages_dir.is_dir():
                new_registry = build_registry(packages_dir)
            else:
                return f"Packages directory not found: {packages_dir}"

            skills = new_registry["skills"]
            agents = new_registry["agents"]
            counts = new_registry["counts"]
            skill_map.clear()
            skill_map.update({s.name: s for s in skills})
            agent_map.clear()
            agent_map.update({a.name: a for a in agents})

            return (
                f"Registry reloaded: {counts['skills']} skills, "
                f"{counts['agents']} agents, {counts['commands']} commands"
            )
        except Exception as e:
            logger.exception("Error in reload")
            return f"Error reloading registry: {e}"

    # =========================================================================
    # MCP Gateway — Route to Backend MCP Servers
    # =========================================================================

    @mcp.tool()
    def list_mcp_servers() -> str:
        """List all backend MCP servers registered in PopKit Cloud.

        Shows the user's registered MCP servers that PopKit can route to.
        Servers are registered via the PopKit Cloud API.

        Returns:
            List of registered servers with names, descriptions, and tools
        """
        try:
            import json
            from urllib.request import Request, urlopen

            api_key, api_url = _resolve_cloud_config()

            if not api_key:
                return (
                    "No PopKit Cloud API key found. Run `popkit login` to authenticate, "
                    "or visit https://app.popkit.unjoe.me/signup/ to create an account."
                )

            req = Request(
                f"{api_url}/v1/mcp/servers",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )

            with urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())

            servers = data.get("servers", [])
            if not servers:
                return "No MCP servers registered. Use the PopKit Cloud API to register backend servers."

            lines = [f"## Registered MCP Servers ({len(servers)})", ""]
            for s in servers:
                tools = ", ".join(s.get("tools", [])) or "none listed"
                status = "enabled" if s.get("enabled", True) else "disabled"
                lines.append(f"### {s['name']} ({status})")
                lines.append(f"- **Description:** {s.get('description', 'N/A')}")
                lines.append(f"- **Command:** `{s.get('command', 'N/A')}`")
                lines.append(f"- **Tools:** {tools}")
                lines.append(f"- **ID:** {s['id']}")
                lines.append("")

            return "\n".join(lines)
        except Exception as e:
            logger.debug("Failed to list MCP servers: %s", e)
            return f"Could not fetch MCP servers: {e}"

    @mcp.tool()
    def route_to_server(server_name: str, action: str, params: str = "{}") -> str:
        """Route a request to a registered backend MCP server.

        PopKit acts as a gateway, forwarding requests to the appropriate
        backend MCP server. Use list_mcp_servers to see available servers.

        Args:
            server_name: Name of the registered server (e.g., "github", "playwright")
            action: The action/tool to invoke on the server (e.g., "list_prs", "screenshot")
            params: JSON string of parameters to pass to the tool

        Returns:
            Instructions for invoking the backend server's tool
        """
        try:
            import json
            from urllib.request import Request, urlopen

            api_key = os.environ.get("POPKIT_API_KEY", "")
            api_url = os.environ.get("POPKIT_API_URL", "https://api.thehouseofdeals.com")

            if not api_key:
                return "No POPKIT_API_KEY set. Cannot route to backend servers."

            # Fetch server config from cloud
            req = Request(
                f"{api_url}/v1/mcp/servers",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )

            with urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode())

            servers = data.get("servers", [])
            server = next((s for s in servers if s["name"] == server_name), None)

            if not server:
                available = ", ".join(s["name"] for s in servers)
                return f"Server '{server_name}' not found. Available: {available}"

            # Log the routing call to cloud analytics (fire-and-forget)
            import time

            start_time = time.time()
            try:
                log_req = Request(
                    f"{api_url}/v1/analytics/gateway",
                    data=json.dumps(
                        {
                            "server_name": server_name,
                            "server_id": server.get("id", ""),
                            "tool_name": action,
                            "latency_ms": int((time.time() - start_time) * 1000),
                            "success": True,
                        }
                    ).encode(),
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    method="POST",
                )
                urlopen(log_req, timeout=2)
            except Exception:  # noqa: S110
                pass  # Analytics logging is best-effort, never block routing

            # Return routing instructions for the LLM to execute
            lines = [
                f"## Route to {server_name}: {action}",
                "",
                f"**Server:** {server['name']}",
                f"**Command:** `{server.get('command', '')} {' '.join(server.get('args', []))}`",
                f"**Action:** {action}",
                f"**Parameters:** {params}",
                "",
                "To execute this, the host environment should invoke the backend MCP server ",
                f"with the tool `{action}` and the provided parameters.",
                "",
                f"Available tools on {server_name}: {', '.join(server.get('tools', []))}",
            ]

            return "\n".join(lines)
        except Exception as e:
            logger.debug("Failed to route to server: %s", e)
            return f"Routing error: {e}"

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

        def _make_skill_resource(s: SkillDefinition):
            @mcp.resource(get_skill_resource_uri(s))
            def _resource() -> str:
                return _get_skill_content(s)

            return _resource

        _make_skill_resource(skill)

    for agent in agents:

        def _make_agent_resource(a: AgentDefinition):
            @mcp.resource(get_agent_resource_uri(a))
            def _resource() -> str:
                return _get_agent_content(a)

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
                content = _get_skill_content(s)
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
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind for HTTP transports (default: 127.0.0.1)",
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
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )

    # Graceful shutdown handler
    def _shutdown(signum, frame):
        logger.info("Received signal %s, shutting down...", signum)
        raise SystemExit(0)

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    packages_dir = Path(args.packages) if args.packages else None
    logger.info("Starting PopKit MCP Server (transport=%s)", args.transport)

    server = create_server(packages_dir)

    if args.transport == "stdio":
        server.run(transport="stdio")
    elif args.transport == "sse":
        server.run(transport="sse", host=args.host, port=args.port)
    else:
        server.run(transport="streamable-http", host=args.host, port=args.port)


if __name__ == "__main__":
    main()
