#!/usr/bin/env python3
"""
PopKit CLI Entry Point

Main CLI for managing PopKit packages and provider integrations.

Commands:
    popkit install [package]    Install packages to ~/.popkit/
    popkit provider list        Show detected AI coding tool providers
    popkit provider wire        Auto-detect tools, generate configs
    popkit provider launch      Start a provider session with PopKit launch metadata
    popkit mcp start            Launch the MCP server
    popkit status               Show system status
    popkit version              Show version info
"""

import argparse
import sys

from . import __version__


def cmd_install(args: argparse.Namespace) -> int:
    """Install PopKit packages to POPKIT_HOME."""
    from .commands.install import run_install

    return run_install(args)


def cmd_provider(args: argparse.Namespace) -> int:
    """Manage provider integrations."""
    from .commands.provider import run_provider

    return run_provider(args)


def cmd_mcp(args: argparse.Namespace) -> int:
    """MCP server management."""
    from .commands.mcp import run_mcp

    return run_mcp(args)


def cmd_status(args: argparse.Namespace) -> int:
    """Show system status."""
    from .commands.status import run_status

    return run_status(args)


def cmd_update(args: argparse.Namespace) -> int:
    """Update PopKit packages."""
    from .commands.update import run_update

    return run_update(args)


def cmd_login(args: argparse.Namespace) -> int:
    """Log in to PopKit Cloud."""
    from .commands.login import run_login

    return run_login(args)


def cmd_version(args: argparse.Namespace) -> int:
    """Show version information."""
    print(f"popkit {__version__}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="popkit",
        description="PopKit - LLM-agnostic developer orchestration engine",
    )
    parser.add_argument("--version", action="version", version=f"popkit {__version__}")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # install
    install_parser = subparsers.add_parser("install", help="Install PopKit packages to ~/.popkit/")
    install_parser.add_argument(
        "package",
        nargs="?",
        default=None,
        help="Package name or path to install (default: all packages)",
    )
    install_parser.add_argument(
        "--source",
        type=str,
        default=None,
        help="Source directory containing packages (default: auto-detect)",
    )
    install_parser.set_defaults(func=cmd_install)

    # provider
    provider_parser = subparsers.add_parser(
        "provider", help="Manage AI coding tool provider integrations"
    )
    provider_sub = provider_parser.add_subparsers(dest="provider_command", help="Provider commands")

    # provider list
    provider_list = provider_sub.add_parser("list", help="Show detected providers")
    provider_list.set_defaults(func=cmd_provider)

    # provider wire
    provider_wire = provider_sub.add_parser(
        "wire", help="Auto-detect tools, generate provider configs"
    )
    provider_wire.add_argument(
        "--provider",
        type=str,
        default=None,
        help="Wire a specific provider only",
    )
    provider_wire.set_defaults(func=cmd_provider)

    # provider launch
    provider_launch = provider_sub.add_parser(
        "launch", help="Launch a provider session with PopKit runtime markers"
    )
    provider_launch.add_argument(
        "provider",
        type=str,
        help="Provider to launch (currently: codex)",
    )
    provider_launch.add_argument(
        "--mode",
        choices=["default", "plan"],
        default="default",
        help="Launch mode. 'plan' requests host-managed request_user_input support.",
    )
    provider_launch.add_argument(
        "--command",
        dest="launch_command",
        type=str,
        default=None,
        help="Initial prompt or command to pass to the provider",
    )
    provider_launch.add_argument(
        "--cd",
        type=str,
        default=None,
        help="Workspace directory to open in the launched provider session",
    )
    provider_launch.add_argument(
        "--print-only",
        action="store_true",
        help="Print the resolved launch command without executing it",
    )
    provider_launch.set_defaults(func=cmd_provider)

    # mcp
    mcp_parser = subparsers.add_parser("mcp", help="MCP server management")
    mcp_sub = mcp_parser.add_subparsers(dest="mcp_command", help="MCP commands")

    # mcp start
    mcp_start = mcp_sub.add_parser("start", help="Start the MCP server")
    mcp_start.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="MCP transport protocol (default: stdio)",
    )
    mcp_start.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for HTTP transports (default: 8080)",
    )
    mcp_start.set_defaults(func=cmd_mcp)

    # update
    update_parser = subparsers.add_parser("update", help="Update PopKit packages")
    update_parser.set_defaults(func=cmd_update)

    # status
    status_parser = subparsers.add_parser("status", help="Show system status")
    status_parser.set_defaults(func=cmd_status)

    # login
    login_parser = subparsers.add_parser("login", help="Log in to PopKit Cloud")
    login_parser.add_argument(
        "--key",
        type=str,
        default=None,
        help="API key to store (skip interactive login)",
    )
    login_parser.set_defaults(func=cmd_login)

    # version
    version_parser = subparsers.add_parser("version", help="Show version info")
    version_parser.set_defaults(func=cmd_version)

    return parser


def main() -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if hasattr(args, "func"):
        return args.func(args)

    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
