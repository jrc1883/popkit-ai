#!/usr/bin/env python3
"""
Plugin Data Directory Resolution

Provides a single source of truth for resolving the PopKit plugin data directory.
Supports both the v2 POPKIT_HOME convention and legacy Claude Code paths.

Resolution order (v2):
1. POPKIT_HOME env var (explicit override)
2. CLAUDE_PLUGIN_DATA env var (CC 2.1.78+)
3. Platform-specific default (~/.popkit/data)
4. Fallback: .claude/popkit/ (legacy)

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
    """Get the plugin data directory.

    Resolution order:
    1. POPKIT_HOME env var → $POPKIT_HOME/data/ (v2 convention)
    2. CLAUDE_PLUGIN_DATA env var (CC 2.1.78+) - official persistent plugin state dir
    3. Platform-specific default → ~/.popkit/data/ (v2 convention)
    4. Fallback to <cwd>/.claude/popkit/ for older CC versions

    Steps 3-4: only uses ~/.popkit/data/ if that directory already exists
    (i.e., popkit has been installed via the CLI). Otherwise falls back to
    the legacy .claude/popkit/ path for backward compatibility.

    The directory is created if it does not exist.

    Returns:
        Path to the plugin data directory
    """
    # 1. Explicit POPKIT_HOME override
    popkit_home = os.environ.get("POPKIT_HOME")
    if popkit_home:
        data_dir = Path(popkit_home) / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    # 2. Claude Code's official plugin data dir
    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA")
    if plugin_data:
        data_dir = Path(plugin_data)
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    # 3. Check if ~/.popkit/ exists (v2 installed)
    from .home import _platform_default

    popkit_default = _platform_default()
    if popkit_default.exists():
        data_dir = popkit_default / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir

    # 4. Legacy fallback
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
        PosixPath('/home/user/.popkit/data/sessions')
        >>> get_plugin_data_subdir("routines", "morning")
        PosixPath('/home/user/.popkit/data/routines/morning')
    """
    subdir = get_plugin_data_dir() / Path(*parts)
    subdir.mkdir(parents=True, exist_ok=True)
    return subdir


def get_global_plugin_data_dir() -> Path:
    """Get the global (user-level) plugin data directory.

    For state that is shared across projects (e.g., project registry,
    cloud config, recordings).

    Resolution:
    1. POPKIT_HOME → $POPKIT_HOME/data/ (same as get_plugin_data_dir for global)
    2. ~/.popkit/data/ if ~/.popkit exists
    3. ~/.claude/popkit/ (legacy)

    The directory is created if it does not exist.

    Returns:
        Path to the global plugin data directory
    """
    # Check POPKIT_HOME first
    popkit_home = os.environ.get("POPKIT_HOME")
    if popkit_home:
        global_dir = Path(popkit_home) / "data"
        global_dir.mkdir(parents=True, exist_ok=True)
        return global_dir

    # Check if ~/.popkit/ exists (v2 installed)
    from .home import _platform_default

    popkit_default = _platform_default()
    if popkit_default.exists():
        global_dir = popkit_default / "data"
        global_dir.mkdir(parents=True, exist_ok=True)
        return global_dir

    # Legacy fallback
    global_dir = Path.home() / ".claude" / "popkit"
    global_dir.mkdir(parents=True, exist_ok=True)
    return global_dir
