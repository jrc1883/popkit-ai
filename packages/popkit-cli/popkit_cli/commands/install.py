#!/usr/bin/env python3
"""
popkit install - Install PopKit packages to POPKIT_HOME.

Copies or symlinks PopKit packages from a source directory
into ~/.popkit/packages/ for use by all providers.
"""

import argparse
import os
from pathlib import Path
from typing import Optional


def _find_source_packages(source: Optional[str] = None) -> Path:
    """Find the source packages directory.

    Resolution:
    1. Explicit --source argument
    2. POPKIT_SOURCE env var
    3. Current directory if it contains packages/
    4. pip-installed popkit location

    Args:
        source: Explicit source path

    Returns:
        Path to source packages directory

    Raises:
        SystemExit if no source found
    """
    if source:
        p = Path(source)
        if p.is_dir():
            return p

    env_source = os.environ.get("POPKIT_SOURCE")
    if env_source:
        p = Path(env_source)
        if p.is_dir():
            return p

    # Check cwd
    cwd = Path.cwd()
    if (cwd / "packages" / "popkit-core").is_dir():
        return cwd / "packages"

    # Check parent (in case we're inside packages/)
    if (cwd.parent / "packages" / "popkit-core").is_dir():
        return cwd.parent / "packages"

    print("Error: Could not find PopKit packages source.")
    print("Run from the popkit repo root, or use --source <path>")
    raise SystemExit(1)


def _install_package(source: Path, target: Path) -> bool:
    """Install a single package by creating a symlink.

    Args:
        source: Source package directory
        target: Target location in POPKIT_HOME/packages/

    Returns:
        True if installed successfully
    """
    if target.is_symlink():
        target.unlink()
    elif target.exists():
        print(f"  Warning: {target.name} exists and is not a symlink, skipping")
        return False

    try:
        target.symlink_to(source.resolve(), target_is_directory=True)
        return True
    except OSError as e:
        print(f"  Error creating symlink: {e}")
        return False


PACKAGE_NAMES = ["popkit-core", "popkit-dev", "popkit-ops", "popkit-research", "shared-py"]


def run_install(args: argparse.Namespace) -> int:
    """Execute the install command."""
    from popkit_shared.utils.home import get_popkit_home, get_popkit_packages_dir

    source_dir = _find_source_packages(getattr(args, "source", None))
    home_dir = get_popkit_home()
    packages_dir = get_popkit_packages_dir()

    print(f"PopKit Home: {home_dir}")
    print(f"Source: {source_dir}")
    print()

    # Determine which packages to install
    if args.package:
        to_install = [args.package]
    else:
        to_install = PACKAGE_NAMES

    installed = 0
    for name in to_install:
        source = source_dir / name
        if not source.is_dir():
            print(f"  Skip: {name} (not found in source)")
            continue

        target = packages_dir / name
        if _install_package(source, target):
            print(f"  Installed: {name} → {target}")
            installed += 1

    print()
    print(f"Installed {installed} packages to {packages_dir}")

    # Create popkit.yaml if it doesn't exist
    config_path = home_dir / "popkit.yaml"
    if not config_path.exists():
        config_path.write_text(
            "# PopKit Configuration\n"
            "# See https://github.com/jrc1883/popkit-ai for documentation\n"
            "\n"
            "version: 2.0\n"
            f"packages_dir: {packages_dir}\n",
            encoding="utf-8",
        )
        print(f"Created config: {config_path}")

    print()
    print("Next steps:")
    print("  popkit provider list    # See detected AI coding tools")
    print("  popkit provider wire    # Auto-configure detected tools")
    print("  popkit mcp start        # Start the MCP server")

    return 0
