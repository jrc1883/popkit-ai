#!/usr/bin/env python3
"""
popkit provider launch - Start provider-owned sessions with PopKit runtime markers.
"""

import argparse
import os
import subprocess
from pathlib import Path

from popkit_shared.providers.codex import CodexAdapter
from popkit_shared.providers.registry import get_adapter


def _parse_bool(value: str | None) -> bool:
    """Parse a truthy/falsey environment value."""
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _host_supports_plan_mode(env: dict[str, str] | None = None) -> bool:
    """Return True when the launcher host declares plan-capable Codex support."""
    values = env if env is not None else os.environ
    return _parse_bool(values.get("POPKIT_HOST_CAN_REQUEST_USER_INPUT")) or _parse_bool(
        values.get("POPKIT_HOST_SUPPORTS_CODEX_PLAN_MODE")
    )


def _format_command(command: list[str]) -> str:
    """Format a command for display."""
    return subprocess.list2cmdline(command)


def run_launch(args: argparse.Namespace) -> int:
    """Launch a provider session using host-owned interaction-surface rules."""
    provider_name = getattr(args, "provider", None)
    mode = getattr(args, "mode", "default")
    prompt = getattr(args, "launch_command", None)
    print_only = getattr(args, "print_only", False)

    adapter = get_adapter(provider_name or "")
    if adapter is None:
        print(f"Error: Unknown provider '{provider_name}'")
        return 1

    if provider_name != "codex" or not isinstance(adapter, CodexAdapter):
        print(f"Error: provider launch is not implemented for '{provider_name}' yet.")
        return 1

    launch_dir = Path(getattr(args, "cd", None) or Path.cwd()).expanduser().resolve()
    plan_supported = _host_supports_plan_mode()
    launch_spec = adapter.build_launch_spec(
        mode=mode,
        prompt=prompt,
        cwd=launch_dir,
        env=dict(os.environ),
        host_plan_supported=plan_supported,
    )

    print("PopKit Provider Launch")
    print("=" * 40)
    print(f"Provider: {provider_name}")
    print(f"Requested mode: {launch_spec.requested_mode}")
    print(f"Actual mode: {launch_spec.actual_mode}")
    print(f"Interaction surface: {launch_spec.interaction_surface.value}")
    if launch_spec.warning:
        print(f"Warning: {launch_spec.warning}")
    print(f"Workspace: {launch_dir}")
    print(f"Command: {_format_command(launch_spec.command)}")

    if print_only:
        return 0

    try:
        result = subprocess.run(
            launch_spec.command,
            cwd=str(launch_dir),
            env=launch_spec.env,
            check=False,
        )
        return result.returncode
    except KeyboardInterrupt:
        print("\nLaunch cancelled.")
        return 130
