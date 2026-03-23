#!/usr/bin/env python3
"""
popkit mcp - MCP server management.

Commands:
    popkit mcp start    Start the PopKit MCP server
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_mcp(args: argparse.Namespace) -> int:
    """Execute MCP subcommands."""
    command = getattr(args, "mcp_command", None)

    if command == "start":
        return _mcp_start(args)
    else:
        print("Usage: popkit mcp [start]")
        return 1


def _mcp_start(args: argparse.Namespace) -> int:
    """Start the PopKit MCP server."""
    transport = getattr(args, "transport", "stdio")
    port = getattr(args, "port", 8080)

    # Find the MCP server module
    server_path = _find_mcp_server()
    if not server_path:
        print("Error: popkit-mcp package not found.")
        print("Install it with: pip install popkit-mcp")
        return 1

    print(f"Starting PopKit MCP Server ({transport})...")

    cmd = [sys.executable, "-m", "popkit_mcp.server", "--transport", transport]
    if transport in ("sse", "streamable-http"):
        cmd.extend(["--port", str(port)])
        print(f"Listening on port {port}")

    try:
        result = subprocess.run(cmd)
        return result.returncode
    except KeyboardInterrupt:
        print("\nServer stopped.")
        return 0


def _find_mcp_server() -> bool:
    """Check if the MCP server is importable."""
    try:
        import popkit_mcp.server  # noqa: F401

        return True
    except ImportError:
        pass

    # Check for development installation (sibling package)
    dev_server = Path(__file__).parent.parent.parent.parent / "popkit-mcp" / "server.py"
    if dev_server.is_file():
        return True

    return False
