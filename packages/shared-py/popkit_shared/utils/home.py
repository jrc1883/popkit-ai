#!/usr/bin/env python3
"""
Cross-Platform POPKIT_HOME Resolution

Provides platform-aware resolution of the PopKit home directory (~/.popkit).
This is the central location for all PopKit packages, provider configs, and runtime data.

Resolution order:
1. POPKIT_HOME env var (explicit override)
2. Platform-specific default:
   - Linux: ~/.popkit (XDG fallback: $XDG_DATA_HOME/popkit)
   - macOS: ~/.popkit
   - Windows: %APPDATA%/popkit (Git Bash fallback: ~/.popkit)

Part of the PopKit v2.0 provider-agnostic architecture.
"""

import os
import sys
from pathlib import Path


def get_popkit_home() -> Path:
    """Get the PopKit home directory.

    Resolution order:
    1. POPKIT_HOME env var (explicit override)
    2. Platform-specific default

    The directory is created if it does not exist.

    Returns:
        Path to the PopKit home directory
    """
    # 1. Explicit override
    popkit_home = os.environ.get("POPKIT_HOME")
    if popkit_home:
        home_dir = Path(popkit_home)
        home_dir.mkdir(parents=True, exist_ok=True)
        return home_dir

    # 2. Platform-specific default
    home_dir = _platform_default()
    home_dir.mkdir(parents=True, exist_ok=True)
    return home_dir


def _platform_default() -> Path:
    """Get platform-specific default for POPKIT_HOME.

    - Linux: ~/.popkit (XDG fallback: $XDG_DATA_HOME/popkit)
    - macOS: ~/.popkit
    - Windows: %APPDATA%/popkit (Git Bash fallback: ~/.popkit)

    Returns:
        Path to the default PopKit home directory
    """
    if sys.platform == "win32":
        # Check if running in Git Bash / MSYS2
        if os.environ.get("MSYSTEM") or os.environ.get("MINGW_PREFIX"):
            return Path.home() / ".popkit"
        # Native Windows: use APPDATA
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / "popkit"
        return Path.home() / ".popkit"

    elif sys.platform == "linux":
        # XDG fallback for Linux
        xdg_data = os.environ.get("XDG_DATA_HOME")
        if xdg_data:
            return Path(xdg_data) / "popkit"
        return Path.home() / ".popkit"

    else:
        # macOS and others
        return Path.home() / ".popkit"


def get_popkit_packages_dir() -> Path:
    """Get the packages directory under POPKIT_HOME.

    Returns:
        Path to ~/.popkit/packages/
    """
    pkg_dir = get_popkit_home() / "packages"
    pkg_dir.mkdir(parents=True, exist_ok=True)
    return pkg_dir


def get_popkit_providers_dir() -> Path:
    """Get the providers directory under POPKIT_HOME.

    Returns:
        Path to ~/.popkit/providers/
    """
    prov_dir = get_popkit_home() / "providers"
    prov_dir.mkdir(parents=True, exist_ok=True)
    return prov_dir


def get_popkit_data_dir() -> Path:
    """Get the runtime data directory under POPKIT_HOME.

    For sessions, cache, logs, and other runtime state.

    Returns:
        Path to ~/.popkit/data/
    """
    data_dir = get_popkit_home() / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_popkit_bin_dir() -> Path:
    """Get the bin directory under POPKIT_HOME.

    For CLI entry points and executables.

    Returns:
        Path to ~/.popkit/bin/
    """
    bin_dir = get_popkit_home() / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    return bin_dir
