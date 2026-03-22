#!/usr/bin/env python3
"""
popkit status - Show PopKit system status.
"""

import argparse
import os


def run_status(args: argparse.Namespace) -> int:
    """Show PopKit system status."""
    from popkit_shared.utils.home import (
        get_popkit_data_dir,
        get_popkit_home,
        get_popkit_packages_dir,
        get_popkit_providers_dir,
    )

    home = get_popkit_home()
    packages = get_popkit_packages_dir()
    providers = get_popkit_providers_dir()
    data = get_popkit_data_dir()

    print("PopKit System Status")
    print("=" * 40)
    print()
    print(f"POPKIT_HOME: {home}")
    print(f"  Exists: {home.is_dir()}")
    print()

    # Count installed packages
    pkg_count = 0
    if packages.is_dir():
        for p in packages.iterdir():
            if p.is_dir() and p.name not in ("__pycache__",):
                pkg_count += 1

    print(f"Packages: {packages}")
    print(f"  Installed: {pkg_count}")
    if packages.is_dir():
        for p in sorted(packages.iterdir()):
            if p.is_dir() and p.name not in ("__pycache__",):
                link = f" → {p.resolve()}" if p.is_symlink() else ""
                print(f"    - {p.name}{link}")
    print()

    # Providers
    print(f"Providers: {providers}")
    if providers.is_dir():
        for p in sorted(providers.iterdir()):
            if p.is_dir():
                print(f"    - {p.name}")
    print()

    # Data
    print(f"Data: {data}")
    print()

    # Environment
    print("Environment:")
    for var in ("POPKIT_HOME", "CLAUDE_PLUGIN_DATA", "CLAUDE_PLUGIN_ROOT"):
        val = os.environ.get(var)
        if val:
            print(f"  {var} = {val}")
        else:
            print(f"  {var} = (not set)")

    return 0
