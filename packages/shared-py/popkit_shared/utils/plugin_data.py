#!/usr/bin/env python3
"""
Plugin Data Directory Resolution

Provides a single source of truth for resolving the PopKit plugin data directory.
Uses the CLAUDE_PLUGIN_DATA environment variable (CC 2.1.78+) when available,
falling back to .claude/popkit/ for older Claude Code versions.

Usage in shared utility modules:
    from popkit_shared.utils.plugin_data import get_plugin_data_dir

Usage in standalone hook scripts (subprocess execution):
    # Copy the inline fallback pattern instead of importing:
    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA")
    data_dir = Path(plugin_data) if plugin_data else Path.cwd() / ".claude" / "popkit"
"""

import os
from pathlib import Path


def get_plugin_data_dir() -> Path:
    """Get the plugin data directory, preferring CLAUDE_PLUGIN_DATA.

    Resolution order:
    1. CLAUDE_PLUGIN_DATA env var (CC 2.1.78+) - official persistent plugin state dir
    2. Fallback to <cwd>/.claude/popkit/ for older CC versions

    The directory is created if it does not exist.

    Returns:
        Path to the plugin data directory
    """
    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA")
    if plugin_data:
        data_dir = Path(plugin_data)
    else:
        data_dir = Path.cwd() / ".claude" / "popkit"

    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_plugin_data_subdir(*parts: str) -> Path:
    """Get a subdirectory under the plugin data directory.

    Creates the full path if it doesn't exist.

    Args:
        *parts: Path components relative to data dir (e.g., "sessions", "cache")

    Returns:
        Path to the subdirectory

    Example:
        >>> get_plugin_data_subdir("sessions")
        PosixPath('/home/user/.claude/popkit/sessions')
        >>> get_plugin_data_subdir("routines", "morning")
        PosixPath('/home/user/.claude/popkit/routines/morning')
    """
    subdir = get_plugin_data_dir() / Path(*parts)
    subdir.mkdir(parents=True, exist_ok=True)
    return subdir


def get_global_plugin_data_dir() -> Path:
    """Get the global (user-level) plugin data directory.

    For state that is shared across projects (e.g., project registry,
    cloud config, recordings). Uses ~/.claude/popkit/.

    The directory is created if it does not exist.

    Returns:
        Path to the global plugin data directory
    """
    global_dir = Path.home() / ".claude" / "popkit"
    global_dir.mkdir(parents=True, exist_ok=True)
    return global_dir
