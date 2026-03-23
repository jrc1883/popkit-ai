#!/usr/bin/env python3
"""
GitHub Copilot Provider Adapter

Integrates PopKit with GitHub Copilot via MCP server configuration.
Copilot has two config surfaces:
  1. Copilot CLI global: ~/.copilot/mcp-config.json (root key: "mcpServers")
  2. VS Code per-project: .vscode/mcp.json (root key: "servers")

Both use stdio MCP transport but differ in their JSON root key.
Also generates copilot-instructions.md from AGENT.md agent definitions.

Part of the PopKit v2.0 provider-agnostic architecture.
"""

import json
import os
from pathlib import Path
from typing import Any

from .base import ProviderAdapter, ProviderInfo, ToolMapping
from .tool_mapping import COPILOT_MAPPINGS


class CopilotAdapter(ProviderAdapter):
    """GitHub Copilot provider adapter.

    Generates MCP server configuration for both Copilot CLI (~/.copilot/mcp-config.json)
    and VS Code (.vscode/mcp.json), plus copilot-instructions.md from AGENT.md
    agent definitions.
    """

    @property
    def name(self) -> str:
        return "copilot"

    @property
    def display_name(self) -> str:
        return "GitHub Copilot"

    def _get_copilot_home(self) -> Path:
        """Return the Copilot home directory, respecting COPILOT_HOME env var."""
        env_home = os.environ.get("COPILOT_HOME")
        if env_home:
            return Path(env_home)
        return Path.home() / ".copilot"

    def detect(self) -> ProviderInfo:
        """Detect GitHub Copilot installation.

        Checks for:
        1. ~/.copilot/ directory (or COPILOT_HOME override)
        2. .vscode/ directory in cwd (indicator of VS Code + Copilot)
        """
        copilot_home = self._get_copilot_home()
        has_copilot_dir = copilot_home.is_dir()

        # VS Code with potential Copilot — .vscode/ directory in cwd
        has_vscode_dir = Path(".vscode").is_dir()

        is_available = has_copilot_dir or has_vscode_dir

        return ProviderInfo(
            name=self.name,
            display_name=self.display_name,
            version=None,
            install_path=copilot_home if has_copilot_dir else None,
            is_available=is_available,
        )

    def generate_config(self, package_dir: Path, output_dir: Path) -> list[Path]:
        """Generate Copilot-specific configuration.

        Creates:
        1. mcp-config.json — Copilot CLI format (root key: "mcpServers")
        2. vscode-mcp.json — VS Code format (root key: "servers")
        3. copilot-instructions.md from AGENT.md files found in the package

        Args:
            package_dir: Path to the PopKit package
            output_dir: Path to write generated configs

        Returns:
            List of generated file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        generated: list[Path] = []

        # Generate Copilot CLI MCP config (mcpServers root key)
        copilot_config = self._build_copilot_cli_config(package_dir)
        copilot_config_path = output_dir / "mcp-config.json"
        with open(copilot_config_path, "w", encoding="utf-8") as f:
            json.dump(copilot_config, f, indent=2)
        generated.append(copilot_config_path)

        # Generate VS Code MCP config (servers root key)
        vscode_config = self._build_vscode_config(package_dir)
        vscode_config_path = output_dir / "vscode-mcp.json"
        with open(vscode_config_path, "w", encoding="utf-8") as f:
            json.dump(vscode_config, f, indent=2)
        generated.append(vscode_config_path)

        # Generate copilot-instructions.md from AGENT.md files
        instructions_files = self._generate_copilot_instructions(package_dir, output_dir)
        generated.extend(instructions_files)

        return generated

    def get_tool_mappings(self) -> list[ToolMapping]:
        """Get Copilot tool mappings."""
        return COPILOT_MAPPINGS

    def install(self, package_dir: Path) -> bool:
        """Wire PopKit into Copilot by adding MCP server entries.

        Merges a "popkit" entry into:
        1. ~/.copilot/mcp-config.json (Copilot CLI, root key: "mcpServers")
        2. .vscode/mcp.json (VS Code, root key: "servers") — only if .vscode/ exists

        Args:
            package_dir: Path to the PopKit package to install

        Returns:
            True if at least one config was written successfully
        """
        success = False

        # Install into Copilot CLI global config
        copilot_home = self._get_copilot_home()
        copilot_home.mkdir(parents=True, exist_ok=True)
        copilot_config_path = copilot_home / "mcp-config.json"

        if self._merge_mcp_entry(
            copilot_config_path,
            root_key="mcpServers",
            server_config=self._build_copilot_cli_config(package_dir),
            config_root_key="mcpServers",
        ):
            success = True

        # Install into VS Code per-project config (only if .vscode/ exists)
        vscode_dir = Path(".vscode")
        if vscode_dir.is_dir():
            vscode_mcp_path = vscode_dir / "mcp.json"
            if self._merge_mcp_entry(
                vscode_mcp_path,
                root_key="servers",
                server_config=self._build_vscode_config(package_dir),
                config_root_key="servers",
            ):
                success = True

        return success

    def uninstall(self, package_name: str) -> bool:
        """Remove PopKit from Copilot's MCP configuration.

        Removes the "popkit" entry from both:
        1. ~/.copilot/mcp-config.json (root key: "mcpServers")
        2. .vscode/mcp.json (root key: "servers")

        Args:
            package_name: Name of the package to uninstall

        Returns:
            True if at least one removal succeeded
        """
        success = False

        # Remove from Copilot CLI global config
        copilot_config_path = self._get_copilot_home() / "mcp-config.json"
        if self._remove_mcp_entry(copilot_config_path, root_key="mcpServers"):
            success = True

        # Remove from VS Code per-project config
        vscode_mcp_path = Path(".vscode") / "mcp.json"
        if self._remove_mcp_entry(vscode_mcp_path, root_key="servers"):
            success = True

        return success

    def _build_server_entry(self, package_dir: Path) -> dict[str, Any]:
        """Build the common MCP server entry for PopKit.

        Args:
            package_dir: Path to the PopKit package

        Returns:
            Server entry dict (shared between both config formats)
        """
        from ..utils.home import get_popkit_home

        popkit_home = get_popkit_home()

        return {
            "type": "stdio",
            "command": "python3",
            "args": ["-m", "popkit_mcp.server"],
            "env": {
                "POPKIT_HOME": str(popkit_home),
            },
        }

    def _build_copilot_cli_config(self, package_dir: Path) -> dict[str, Any]:
        """Build Copilot CLI MCP config (root key: mcpServers).

        Args:
            package_dir: Path to the PopKit package

        Returns:
            Config dict for ~/.copilot/mcp-config.json
        """
        return {
            "mcpServers": {
                "popkit": self._build_server_entry(package_dir),
            }
        }

    def _build_vscode_config(self, package_dir: Path) -> dict[str, Any]:
        """Build VS Code MCP config (root key: servers).

        Args:
            package_dir: Path to the PopKit package

        Returns:
            Config dict for .vscode/mcp.json
        """
        return {
            "servers": {
                "popkit": self._build_server_entry(package_dir),
            }
        }

    def _merge_mcp_entry(
        self,
        config_path: Path,
        root_key: str,
        server_config: dict[str, Any],
        config_root_key: str,
    ) -> bool:
        """Merge a popkit entry into an existing MCP config file.

        Args:
            config_path: Path to the JSON config file
            root_key: Root key to use in the config ("mcpServers" or "servers")
            server_config: Full config dict containing the popkit entry
            config_root_key: Key in server_config that holds the server entries

        Returns:
            True if write succeeded
        """
        existing: dict[str, Any] = {}
        if config_path.is_file():
            try:
                with open(config_path, encoding="utf-8") as f:
                    existing = json.load(f)
            except (OSError, json.JSONDecodeError):
                existing = {}

        if root_key not in existing:
            existing[root_key] = {}

        existing[root_key]["popkit"] = server_config[config_root_key]["popkit"]

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(existing, f, indent=2)
            return True
        except OSError:
            return False

    def _remove_mcp_entry(self, config_path: Path, root_key: str) -> bool:
        """Remove the popkit entry from an MCP config file.

        Args:
            config_path: Path to the JSON config file
            root_key: Root key in the config ("mcpServers" or "servers")

        Returns:
            True if removal succeeded
        """
        if not config_path.is_file():
            return False

        try:
            with open(config_path, encoding="utf-8") as f:
                config = json.load(f)
        except (OSError, json.JSONDecodeError):
            return False

        servers = config.get(root_key, {})
        if "popkit" not in servers:
            return False

        del servers["popkit"]

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
            return True
        except OSError:
            return False

    def _generate_copilot_instructions(self, package_dir: Path, output_dir: Path) -> list[Path]:
        """Generate copilot-instructions.md from AGENT.md files.

        Scans the package for AGENT.md files and creates a combined
        copilot-instructions.md with the agent system prompts adapted for Copilot.

        Args:
            package_dir: Path to the PopKit package
            output_dir: Path to write generated instruction files

        Returns:
            List of generated instruction file paths
        """
        generated: list[Path] = []

        # Find all AGENT.md files in the package
        agent_mds = sorted(package_dir.rglob("AGENT.md"))
        if not agent_mds:
            return generated

        instructions_path = output_dir / "copilot-instructions.md"
        sections: list[str] = [
            "# Copilot Instructions -- Generated by PopKit\n",
            "",
            "<!-- This file was auto-generated from PopKit agent definitions. -->",
            "<!-- Do not edit manually -- regenerate with: popkit provider wire copilot -->",
            "",
        ]

        for agent_md in agent_mds:
            content = self._adapt_agent_md(agent_md, package_dir)
            if content:
                sections.append(content)
                sections.append("")

        with open(instructions_path, "w", encoding="utf-8") as f:
            f.write("\n".join(sections))

        generated.append(instructions_path)
        return generated

    def _adapt_agent_md(self, agent_md_path: Path, package_dir: Path) -> str:
        """Read an AGENT.md and adapt its content for copilot-instructions.md.

        Args:
            agent_md_path: Path to the AGENT.md file
            package_dir: Path to the package root (for relative path computation)

        Returns:
            Content formatted as a section in copilot-instructions.md
        """
        try:
            content = agent_md_path.read_text(encoding="utf-8")
        except OSError:
            return ""

        # Derive a section name from the parent directory
        try:
            relative = agent_md_path.parent.relative_to(package_dir)
            section_name = str(relative).replace("\\", "/")
        except ValueError:
            section_name = agent_md_path.parent.name

        if section_name == ".":
            section_name = "root"

        header = f"## Agent: {section_name}\n"
        return header + "\n" + content
