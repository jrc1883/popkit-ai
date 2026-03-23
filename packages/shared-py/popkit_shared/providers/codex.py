#!/usr/bin/env python3
"""
Codex CLI Provider Adapter

Integrates PopKit with OpenAI's Codex CLI via TOML-based MCP server
configuration and AGENTS.md generation. Codex supports MCP servers
natively through ~/.codex/config.toml with [mcp_servers.NAME] tables.

Part of the PopKit v2.0 provider-agnostic architecture.
"""

import shutil
import sys
from pathlib import Path
from typing import Any

from .base import ProviderAdapter, ProviderInfo, ToolMapping
from .tool_mapping import CODEX_MAPPINGS

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib  # type: ignore[import-not-found]
    except ImportError:
        import tomli as tomllib  # type: ignore[import-not-found, no-redef]


def _format_toml_value(value: Any) -> str:
    """Format a Python value as a TOML literal.

    Handles strings, booleans, integers, floats, lists, and dicts (inline tables).
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return str(value)
    if isinstance(value, str):
        # Escape backslashes and double quotes for TOML strings
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    if isinstance(value, list):
        items = ", ".join(_format_toml_value(v) for v in value)
        return f"[{items}]"
    if isinstance(value, dict):
        pairs = ", ".join(f"{k} = {_format_toml_value(v)}" for k, v in value.items())
        return "{" + pairs + "}"
    return str(value)


def _serialize_toml(data: dict[str, Any]) -> str:
    """Serialize a dict to TOML format.

    Handles top-level key-value pairs and nested tables (one level deep for
    mcp_servers.NAME style sections). Does not support deeply nested structures
    beyond two levels — sufficient for Codex config.toml.
    """
    lines: list[str] = []

    # Write top-level scalar values first
    for key, value in data.items():
        if not isinstance(value, dict):
            lines.append(f"{key} = {_format_toml_value(value)}")

    # Write top-level tables
    for key, value in data.items():
        if isinstance(value, dict):
            # Check if this is a table of tables (e.g., mcp_servers with sub-tables)
            has_subtables = any(isinstance(v, dict) for v in value.values())
            if has_subtables:
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, dict):
                        if lines:
                            lines.append("")
                        lines.append(f"[{key}.{sub_key}]")
                        for sk, sv in sub_value.items():
                            lines.append(f"{sk} = {_format_toml_value(sv)}")
                    else:
                        # Scalar under a parent that also has subtables
                        if lines:
                            lines.append("")
                        lines.append(f"[{key}]")
                        lines.append(f"{sub_key} = {_format_toml_value(sub_value)}")
            else:
                if lines:
                    lines.append("")
                lines.append(f"[{key}]")
                for sk, sv in value.items():
                    lines.append(f"{sk} = {_format_toml_value(sv)}")

    # Ensure trailing newline
    if lines:
        lines.append("")
    return "\n".join(lines)


class CodexAdapter(ProviderAdapter):
    """Codex CLI provider adapter.

    Generates TOML-based MCP server configuration for ~/.codex/config.toml
    and AGENTS.md files from PopKit agent definitions. Codex connects to
    PopKit through the PopKit MCP server.
    """

    @property
    def name(self) -> str:
        return "codex"

    @property
    def display_name(self) -> str:
        return "Codex CLI"

    def detect(self) -> ProviderInfo:
        """Detect Codex CLI installation.

        Checks for:
        1. ~/.codex/ directory existence
        2. 'codex' command on PATH
        """
        codex_home = Path.home() / ".codex"
        has_home_dir = codex_home.is_dir()

        has_binary = shutil.which("codex") is not None

        is_available = has_home_dir or has_binary

        return ProviderInfo(
            name=self.name,
            display_name=self.display_name,
            version=None,
            install_path=codex_home if has_home_dir else None,
            is_available=is_available,
        )

    def generate_config(self, package_dir: Path, output_dir: Path) -> list[Path]:
        """Generate Codex-specific configuration.

        Creates:
        1. TOML config snippet for ~/.codex/config.toml
        2. AGENTS.md from AGENT.md files found in the package

        Args:
            package_dir: Path to the PopKit package
            output_dir: Path to write generated configs

        Returns:
            List of generated file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        generated: list[Path] = []

        # Generate TOML config snippet
        toml_config = self._build_mcp_config()
        config_path = output_dir / "config.toml"
        with open(config_path, "w", encoding="utf-8") as f:
            f.write(_serialize_toml(toml_config))
        generated.append(config_path)

        # Generate AGENTS.md from AGENT.md files
        agents_md = self._generate_agents_md(package_dir, output_dir)
        if agents_md is not None:
            generated.append(agents_md)

        return generated

    def get_tool_mappings(self) -> list[ToolMapping]:
        """Get Codex CLI tool mappings."""
        return CODEX_MAPPINGS

    def install(self, package_dir: Path) -> bool:
        """Wire PopKit into Codex CLI by adding MCP server entry.

        Merges a [mcp_servers.popkit] section into ~/.codex/config.toml,
        preserving any existing configuration.

        Args:
            package_dir: Path to the PopKit package

        Returns:
            True if installation succeeded
        """
        codex_dir = Path.home() / ".codex"
        codex_dir.mkdir(parents=True, exist_ok=True)
        config_path = codex_dir / "config.toml"

        # Load existing config or start fresh
        existing: dict[str, Any] = {}
        if config_path.is_file():
            try:
                with open(config_path, "rb") as f:
                    existing = tomllib.loads(f.read().decode("utf-8"))
            except Exception:
                existing = {}

        # Ensure mcp_servers key exists
        if "mcp_servers" not in existing:
            existing["mcp_servers"] = {}

        # Add/update PopKit entry
        popkit_entry = self._build_mcp_config()
        existing["mcp_servers"]["popkit"] = popkit_entry["mcp_servers"]["popkit"]

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(_serialize_toml(existing))
            return True
        except OSError:
            return False

    def uninstall(self, package_name: str) -> bool:
        """Remove PopKit from Codex CLI's MCP configuration.

        Removes the [mcp_servers.popkit] section from ~/.codex/config.toml.

        Args:
            package_name: Name of the package to uninstall

        Returns:
            True if uninstallation succeeded
        """
        config_path = Path.home() / ".codex" / "config.toml"

        if not config_path.is_file():
            return False

        try:
            with open(config_path, "rb") as f:
                config = tomllib.loads(f.read().decode("utf-8"))
        except Exception:
            return False

        servers = config.get("mcp_servers", {})
        if "popkit" not in servers:
            return False

        del servers["popkit"]

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                f.write(_serialize_toml(config))
            return True
        except OSError:
            return False

    def _build_mcp_config(self) -> dict[str, Any]:
        """Build MCP server configuration for Codex CLI.

        Returns:
            Config dict with mcp_servers.popkit entry
        """
        from ..utils.home import get_popkit_home

        popkit_home = get_popkit_home()

        return {
            "mcp_servers": {
                "popkit": {
                    "command": "python3",
                    "args": ["-m", "popkit_mcp.server"],
                    "env": {"POPKIT_HOME": str(popkit_home)},
                    "startup_timeout_sec": 30,
                    "tool_timeout_sec": 120,
                    "enabled": True,
                }
            }
        }

    def _generate_agents_md(self, package_dir: Path, output_dir: Path) -> Path | None:
        """Generate AGENTS.md from AGENT.md files in the package.

        Scans the package for AGENT.md files and creates a unified AGENTS.md
        listing all agents with their descriptions and capabilities.

        Args:
            package_dir: Path to the PopKit package
            output_dir: Path to write the generated AGENTS.md

        Returns:
            Path to the generated AGENTS.md, or None if no agents found
        """
        agent_entries: list[dict[str, str]] = []

        for agent_md in sorted(package_dir.rglob("AGENT.md")):
            relative = agent_md.parent.relative_to(package_dir)
            agent_name = str(relative).replace("\\", "/")
            if agent_name == ".":
                agent_name = "root"

            try:
                content = agent_md.read_text(encoding="utf-8")
            except OSError:
                continue

            # Extract first line as description (strip heading markers)
            first_line = ""
            for line in content.splitlines():
                stripped = line.strip()
                if stripped:
                    first_line = stripped.lstrip("#").strip()
                    break

            agent_entries.append(
                {
                    "name": agent_name,
                    "description": first_line,
                    "content": content,
                }
            )

        if not agent_entries:
            return None

        # Build AGENTS.md
        sections: list[str] = [
            "# PopKit Agents",
            "",
            "Auto-generated agent definitions for Codex CLI.",
            "Do not edit manually — regenerate with: `popkit provider wire codex`",
            "",
            "## Available Agents",
            "",
        ]

        for entry in agent_entries:
            sections.append(f"### {entry['name']}")
            sections.append("")
            if entry["description"]:
                sections.append(f"**Description:** {entry['description']}")
                sections.append("")
            sections.append(entry["content"])
            sections.append("")
            sections.append("---")
            sections.append("")

        agents_md_path = output_dir / "AGENTS.md"
        with open(agents_md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(sections))

        return agents_md_path
