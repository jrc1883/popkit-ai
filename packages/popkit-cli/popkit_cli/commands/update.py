#!/usr/bin/env python3
"""
popkit update - Update PopKit packages to latest version.

Checks for newer versions and updates installed packages.
"""

import argparse
import subprocess


def run_update(args: argparse.Namespace) -> int:
    """Execute the update command."""
    from popkit_shared.utils.home import get_popkit_packages_dir

    packages_dir = get_popkit_packages_dir()

    print("PopKit Update")
    print("=" * 40)
    print()

    if not packages_dir.is_dir():
        print("Error: PopKit is not installed. Run 'popkit install' first.")
        return 1

    # Check installed packages
    installed = []
    for pkg in sorted(packages_dir.iterdir()):
        if pkg.is_dir() and pkg.name not in ("__pycache__",):
            installed.append(pkg)

    if not installed:
        print("No packages installed.")
        return 0

    print(f"Installed packages: {len(installed)}")
    for pkg in installed:
        link_info = f" -> {pkg.resolve()}" if pkg.is_symlink() else ""
        print(f"  - {pkg.name}{link_info}")

    print()

    # Check if packages are symlinked (development mode)
    symlinked = [p for p in installed if p.is_symlink()]
    if symlinked:
        print("Development mode detected (symlinked packages).")
        print("To update, pull the latest changes in your source repo:")
        print()

        # Find source repo
        source = symlinked[0].resolve().parent
        print(f"  cd {source}")
        print("  git pull")
        print()
        print("Packages will automatically reflect the latest changes.")
        return 0

    # For non-symlinked installs, check GitHub for latest release
    print("Checking for updates...")

    try:
        result = subprocess.run(
            ["gh", "api", "repos/jrc1883/popkit-ai/releases/latest", "--jq", ".tag_name"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            latest = result.stdout.strip()
            print(f"Latest release: {latest}")
            print()
            print("To update, run:")
            print("  popkit install --source <path-to-extracted-release>")
        else:
            print("Could not check for updates. Ensure 'gh' CLI is installed.")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("GitHub CLI not available. Check releases at:")
        print("  https://github.com/jrc1883/popkit-ai/releases")

    return 0
