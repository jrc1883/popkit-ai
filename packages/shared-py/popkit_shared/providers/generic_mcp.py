#!/usr/bin/env python3
"""
Generic MCP Provider Adapter

Universal fallback adapter that exposes PopKit through an MCP server.
Any tool that speaks MCP (Cursor, Codex, Copilot, etc.) can use PopKit
through this adapter without a dedicated integration.

Part of the PopKit v2.0 provider-agnostic architecture.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from .base import ProviderAdapter, ProviderInfo, ToolMapping
from .tool_mapping import GENERIC_MCP_MAPPINGS


class GenericMCPAdapter(ProviderAdapter):
    """Generic MCP provider adapter.

    Generates an MCP server configuration that any MCP-compatible tool
    can use. The PopKit MCP server (packages/popkit-mcp/) is the actual
    implementation; this adapter just generates the wiring config.
    """

    @property
    def name(self) -> str:
        return "generic-mcp"

    @property
    def display_name(self) -> str:
        return "MCP Server (Universal)"

    def detect(self) -> ProviderInfo:
        """MCP adapter is always available if Python is installed."""
        return ProviderInfo(
            name=self.name,
            display_name=self.display_name,
            version="1.0.0",
            install_path=None,
            is_available=True,
        )

    def generate_config(self, package_dir: Path, output_dir: Path) -> List[Path]:
        """Generate MCP server configuration.

        Creates a .mcp.json configuration that tools can import to
        connect to the PopKit MCP server.

        Args:
            package_dir: Path to the PopKit package
            output_dir: Path to write generated configs

        Returns:
            List of generated file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        # Determine the MCP server script path
        from ..utils.home import get_popkit_home

        popkit_home = get_popkit_home()
        mcp_server_path = popkit_home / "packages" / "popkit-mcp" / "server.py"

        # Generate .mcp.json for tools to import
        mcp_config = self._build_mcp_config(mcp_server_path, package_dir)
        config_path = output_dir / "mcp-config.json"

        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(mcp_config, f, indent=2)

        # Generate a startup script
        startup_path = output_dir / "start-mcp-server.sh"
        self._write_startup_script(startup_path, mcp_server_path)

        return [config_path, startup_path]

    def get_tool_mappings(self) -> List[ToolMapping]:
        """Get generic MCP tool mappings."""
        return GENERIC_MCP_MAPPINGS

    def install(self, package_dir: Path) -> bool:
        """Install package by registering it with the MCP server.

        The MCP server scans packages at startup, so installation just
        ensures the package is in the right location.

        Args:
            package_dir: Path to the PopKit package

        Returns:
            True if installation succeeded
        """
        from ..utils.home import get_popkit_packages_dir

        packages_dir = get_popkit_packages_dir()
        package_name = package_dir.name
        target = packages_dir / package_name

        if target.exists() and target.resolve() == package_dir.resolve():
            return True  # Already installed

        if target.is_symlink():
            target.unlink()

        try:
            target.symlink_to(package_dir, target_is_directory=True)
            return True
        except OSError:
            return False

    def uninstall(self, package_name: str) -> bool:
        """Uninstall package from MCP server.

        Args:
            package_name: Name of the package to uninstall

        Returns:
            True if uninstallation succeeded
        """
        from ..utils.home import get_popkit_packages_dir

        packages_dir = get_popkit_packages_dir()
        target = packages_dir / package_name

        if target.is_symlink():
            target.unlink()
            return True

        return False

    def _build_mcp_config(self, server_path: Path, package_dir: Path) -> Dict[str, Any]:
        """Build MCP configuration for tool import.

        Args:
            server_path: Path to the MCP server script
            package_dir: Path to the PopKit package

        Returns:
            MCP configuration dict
        """
        return {
            "mcpServers": {
                "popkit": {
                    "command": "python3",
                    "args": [str(server_path)],
                    "env": {
                        "POPKIT_HOME": str(server_path.parent.parent.parent),
                    },
                }
            }
        }

    def _write_startup_script(self, path: Path, server_path: Path) -> None:
        """Write a shell script to start the MCP server.

        Args:
            path: Path to write the script
            server_path: Path to the MCP server script
        """
        script = f"""#!/usr/bin/env bash
# PopKit MCP Server Startup Script
# Generated by popkit provider wire

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
SERVER_PATH="{server_path}"

if [ ! -f "$SERVER_PATH" ]; then
    echo "Error: MCP server not found at $SERVER_PATH"
    echo "Run 'popkit install' first."
    exit 1
fi

echo "Starting PopKit MCP Server..."
exec python3 "$SERVER_PATH"
"""
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(script)

        # Make executable on Unix
        try:
            os.chmod(path, 0o755)
        except OSError:
            pass
