#!/usr/bin/env python3
"""
Cursor Provider Adapter

Integrates PopKit with Cursor via MCP server configuration and .cursorrules
files. Cursor speaks MCP natively, so PopKit exposes tools through the
PopKit MCP server and generates Cursor-compatible rule files from AGENT.md.

Part of the PopKit v2.0 provider-agnostic architecture.
"""

import json
import shutil
from pathlib import Path
from typing import Any, Dict, List

from .base import ProviderAdapter, ProviderInfo, ToolMapping
from .tool_mapping import CURSOR_MAPPINGS


class CursorAdapter(ProviderAdapter):
    """Cursor provider adapter.

    Generates MCP server configuration for ~/.cursor/mcp.json and
    .cursorrules files from AGENT.md agent definitions. Cursor connects
    to PopKit through the PopKit MCP server.
    """

    @property
    def name(self) -> str:
        return "cursor"

    @property
    def display_name(self) -> str:
        return "Cursor"

    def detect(self) -> ProviderInfo:
        """Detect Cursor installation.

        Checks for:
        1. ~/.cursor/ directory existence
        2. .cursor/ in current working directory
        3. 'cursor' command on PATH
        """
        # Check for ~/.cursor/ directory
        cursor_home = Path.home() / ".cursor"
        has_home_dir = cursor_home.is_dir()

        # Check for .cursor/ in cwd
        has_local_dir = Path(".cursor").is_dir()

        # Check for cursor on PATH
        has_binary = shutil.which("cursor") is not None

        is_available = has_home_dir or has_local_dir or has_binary

        return ProviderInfo(
            name=self.name,
            display_name=self.display_name,
            version=None,
            install_path=cursor_home if has_home_dir else None,
            is_available=is_available,
        )

    def generate_config(self, package_dir: Path, output_dir: Path) -> List[Path]:
        """Generate Cursor-specific configuration.

        Creates:
        1. MCP server connection config for ~/.cursor/mcp.json
        2. .cursorrules files from AGENT.md files found in the package

        Args:
            package_dir: Path to the PopKit package
            output_dir: Path to write generated configs

        Returns:
            List of generated file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        generated: List[Path] = []

        # Generate MCP config
        mcp_config = self._build_mcp_config(package_dir)
        config_path = output_dir / "mcp-config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(mcp_config, f, indent=2)
        generated.append(config_path)

        # Generate .cursorrules from AGENT.md files
        rules_files = self._generate_cursorrules(package_dir, output_dir)
        generated.extend(rules_files)

        return generated

    def get_tool_mappings(self) -> List[ToolMapping]:
        """Get Cursor tool mappings."""
        return CURSOR_MAPPINGS

    def install(self, package_dir: Path) -> bool:
        """Wire PopKit into Cursor by adding MCP server entry.

        Merges a "popkit" entry into ~/.cursor/mcp.json, preserving
        any existing MCP server entries.

        Args:
            package_dir: Path to the PopKit package

        Returns:
            True if installation succeeded
        """
        cursor_dir = Path.home() / ".cursor"
        cursor_dir.mkdir(parents=True, exist_ok=True)
        mcp_json_path = cursor_dir / "mcp.json"

        # Load existing config or start fresh
        existing: Dict[str, Any] = {}
        if mcp_json_path.is_file():
            try:
                with open(mcp_json_path, "r", encoding="utf-8") as f:
                    existing = json.load(f)
            except (json.JSONDecodeError, IOError):
                existing = {}

        # Ensure mcpServers key exists
        if "mcpServers" not in existing:
            existing["mcpServers"] = {}

        # Add/update PopKit entry
        mcp_config = self._build_mcp_config(package_dir)
        existing["mcpServers"]["popkit"] = mcp_config["mcpServers"]["popkit"]

        try:
            with open(mcp_json_path, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2)
            return True
        except IOError:
            return False

    def uninstall(self, package_name: str) -> bool:
        """Remove PopKit from Cursor's MCP configuration.

        Removes the "popkit" entry from ~/.cursor/mcp.json.

        Args:
            package_name: Name of the package to uninstall

        Returns:
            True if uninstallation succeeded
        """
        mcp_json_path = Path.home() / ".cursor" / "mcp.json"

        if not mcp_json_path.is_file():
            return False

        try:
            with open(mcp_json_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except (json.JSONDecodeError, IOError):
            return False

        servers = config.get("mcpServers", {})
        if "popkit" not in servers:
            return False

        del servers["popkit"]

        try:
            with open(mcp_json_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            return True
        except IOError:
            return False

    def _build_mcp_config(self, package_dir: Path) -> Dict[str, Any]:
        """Build MCP server configuration for Cursor.

        Args:
            package_dir: Path to the PopKit package

        Returns:
            MCP configuration dict for ~/.cursor/mcp.json
        """
        from ..utils.home import get_popkit_home

        popkit_home = get_popkit_home()

        return {
            "mcpServers": {
                "popkit": {
                    "command": "python3",
                    "args": ["-m", "popkit_mcp.server"],
                    "env": {
                        "POPKIT_HOME": str(popkit_home),
                    },
                }
            }
        }

    def _generate_cursorrules(self, package_dir: Path, output_dir: Path) -> List[Path]:
        """Generate .cursorrules files from AGENT.md files.

        Scans the package for AGENT.md files and creates corresponding
        .cursorrules files with the agent's system prompt adapted for Cursor.

        Args:
            package_dir: Path to the PopKit package
            output_dir: Path to write generated rule files

        Returns:
            List of generated .cursorrules file paths
        """
        generated: List[Path] = []
        rules_dir = output_dir / "cursorrules"
        rules_dir.mkdir(parents=True, exist_ok=True)

        # Find all AGENT.md files in the package
        for agent_md in package_dir.rglob("AGENT.md"):
            # Derive a rule name from the parent directory
            relative = agent_md.parent.relative_to(package_dir)
            rule_name = str(relative).replace("/", "_").replace("\\", "_")
            if rule_name == ".":
                rule_name = "root"

            rule_path = rules_dir / f".cursorrules.{rule_name}"
            content = self._adapt_agent_md_for_cursor(agent_md)

            with open(rule_path, "w", encoding="utf-8") as f:
                f.write(content)

            generated.append(rule_path)

        return generated

    def _adapt_agent_md_for_cursor(self, agent_md_path: Path) -> str:
        """Read an AGENT.md and adapt its content for a .cursorrules file.

        Args:
            agent_md_path: Path to the AGENT.md file

        Returns:
            Content formatted as a Cursor rules file
        """
        try:
            content = agent_md_path.read_text(encoding="utf-8")
        except IOError:
            return ""

        # Wrap in a Cursor-compatible format with attribution
        header = (
            "# Cursor Rules — Generated by PopKit\n"
            f"# Source: {agent_md_path.name}\n"
            "#\n"
            "# This file was auto-generated from a PopKit agent definition.\n"
            "# Do not edit manually — regenerate with: popkit provider wire cursor\n"
            "\n"
        )

        return header + content
