#!/usr/bin/env python3
"""
Generic MCP Provider Adapter

Universal fallback adapter that exposes PopKit through an MCP server.
Any tool that speaks MCP (Cursor, Codex, Copilot, etc.) can use PopKit
through this adapter without a dedicated integration.

Generates:
- mcp-config.json (connection config for any MCP client)
- start-mcp-server.sh (Unix startup script)
- start-mcp-server.bat (Windows startup script)
- popkit-mcp.service (systemd unit file for Linux daemons)
- com.popkit.mcp.plist (launchd plist for macOS daemons)
- Dockerfile (containerized MCP server)

Part of the PopKit v2.0 provider-agnostic architecture.
"""

import json
import os
import sys
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
        """Generate MCP server configuration files.

        Creates configs for connecting to the PopKit MCP server across
        different platforms and deployment scenarios.

        Args:
            package_dir: Path to the PopKit package
            output_dir: Path to write generated configs

        Returns:
            List of generated file paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        generated = []

        from ..utils.home import get_popkit_home

        popkit_home = get_popkit_home()

        # 1. MCP config JSON (universal)
        mcp_config = self._build_mcp_config(popkit_home)
        config_path = output_dir / "mcp-config.json"
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(mcp_config, f, indent=2)
        generated.append(config_path)

        # 2. Startup scripts
        sh_path = output_dir / "start-mcp-server.sh"
        self._write_unix_startup(sh_path)
        generated.append(sh_path)

        bat_path = output_dir / "start-mcp-server.bat"
        self._write_windows_startup(bat_path)
        generated.append(bat_path)

        # 3. systemd service (Linux)
        service_path = output_dir / "popkit-mcp.service"
        self._write_systemd_service(service_path)
        generated.append(service_path)

        # 4. launchd plist (macOS)
        plist_path = output_dir / "com.popkit.mcp.plist"
        self._write_launchd_plist(plist_path)
        generated.append(plist_path)

        # 5. Dockerfile
        dockerfile_path = output_dir / "Dockerfile"
        self._write_dockerfile(dockerfile_path)
        generated.append(dockerfile_path)

        return generated

    def get_tool_mappings(self) -> List[ToolMapping]:
        """Get generic MCP tool mappings."""
        return GENERIC_MCP_MAPPINGS

    def install(self, package_dir: Path) -> bool:
        """Install package by symlinking into POPKIT_HOME/packages/."""
        from ..utils.home import get_popkit_packages_dir

        packages_dir = get_popkit_packages_dir()
        package_name = package_dir.name
        target = packages_dir / package_name

        if target.exists() and target.resolve() == package_dir.resolve():
            return True

        if target.is_symlink():
            target.unlink()

        try:
            target.symlink_to(package_dir, target_is_directory=True)
            return True
        except OSError:
            return False

    def uninstall(self, package_name: str) -> bool:
        """Remove package symlink from POPKIT_HOME/packages/."""
        from ..utils.home import get_popkit_packages_dir

        packages_dir = get_popkit_packages_dir()
        target = packages_dir / package_name

        if target.is_symlink():
            target.unlink()
            return True

        return False

    # =========================================================================
    # Config Generators
    # =========================================================================

    def _build_mcp_config(self, popkit_home: Path) -> Dict[str, Any]:
        """Build universal MCP configuration."""
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

    def _write_unix_startup(self, path: Path) -> None:
        """Write Unix startup script."""
        script = """#!/usr/bin/env bash
# PopKit MCP Server Startup Script
# Generated by: popkit provider wire

set -euo pipefail

# Check if popkit-mcp is installed via pip
if python3 -m popkit_mcp.server --help > /dev/null 2>&1; then
    echo "Starting PopKit MCP Server (pip install)..."
    exec python3 -m popkit_mcp.server "$@"
fi

# Check if uvx is available
if command -v uvx > /dev/null 2>&1; then
    echo "Starting PopKit MCP Server (uvx)..."
    exec uvx popkit-mcp "$@"
fi

echo "Error: popkit-mcp not found."
echo "Install with: pip install popkit-mcp"
echo "Or use: uvx popkit-mcp"
exit 1
"""
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(script)
        try:
            os.chmod(path, 0o755)
        except OSError:
            pass

    def _write_windows_startup(self, path: Path) -> None:
        """Write Windows startup script."""
        script = """@echo off
REM PopKit MCP Server Startup Script
REM Generated by: popkit provider wire

python -m popkit_mcp.server %*
if %ERRORLEVEL% NEQ 0 (
    echo Error: popkit-mcp not found.
    echo Install with: pip install popkit-mcp
    exit /b 1
)
"""
        with open(path, "w", encoding="utf-8", newline="\r\n") as f:
            f.write(script)

    def _write_systemd_service(self, path: Path) -> None:
        """Write systemd service unit file for Linux."""
        python_path = sys.executable
        service = f"""[Unit]
Description=PopKit MCP Server
After=network.target

[Service]
Type=simple
ExecStart={python_path} -m popkit_mcp.server --transport streamable-http --port 8080
Restart=on-failure
RestartSec=5
Environment=POPKIT_HOME=%h/.popkit

[Install]
WantedBy=default.target
"""
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(service)

    def _write_launchd_plist(self, path: Path) -> None:
        """Write launchd plist for macOS."""
        python_path = sys.executable
        plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.popkit.mcp</string>
    <key>ProgramArguments</key>
    <array>
        <string>{python_path}</string>
        <string>-m</string>
        <string>popkit_mcp.server</string>
        <string>--transport</string>
        <string>streamable-http</string>
        <string>--port</string>
        <string>8080</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/popkit-mcp.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/popkit-mcp.err</string>
</dict>
</plist>
"""
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(plist)

    def _write_dockerfile(self, path: Path) -> None:
        """Write Dockerfile for containerized MCP server."""
        dockerfile = """FROM python:3.12-slim

WORKDIR /app

# Install popkit-mcp from PyPI
RUN pip install --no-cache-dir popkit-mcp

# Create popkit home
ENV POPKIT_HOME=/app/popkit
RUN mkdir -p $POPKIT_HOME/packages

# Expose MCP server port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \\
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/')" || exit 1

# Run MCP server with streamable HTTP transport
CMD ["python3", "-m", "popkit_mcp.server", "--transport", "streamable-http", "--host", "0.0.0.0", "--port", "8080"]
"""
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(dockerfile)
