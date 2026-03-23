#!/usr/bin/env python3
"""
popkit provider - Manage AI coding tool provider integrations.

Commands:
    popkit provider list    Show detected providers
    popkit provider wire    Generate provider configs
"""

import argparse
from typing import Optional


def run_provider(args: argparse.Namespace) -> int:
    """Execute provider subcommands."""
    command = getattr(args, "provider_command", None)

    if command == "list":
        return _provider_list()
    elif command == "wire":
        provider_name = getattr(args, "provider", None)
        return _provider_wire(provider_name)
    else:
        print("Usage: popkit provider [list|wire]")
        return 1


def _provider_list() -> int:
    """List detected providers."""
    from popkit_shared.providers import detect_providers, list_adapters

    print("PopKit Provider Detection")
    print("=" * 40)
    print()

    all_adapters = list_adapters()
    detected = detect_providers()

    for adapter in all_adapters:
        info = adapter.detect()
        status = "AVAILABLE" if info.is_available else "not found"
        marker = "+" if info.is_available else "-"

        print(f"  [{marker}] {info.display_name}")
        print(f"      Name: {info.name}")
        print(f"      Status: {status}")
        if info.version:
            print(f"      Version: {info.version}")
        if info.install_path:
            print(f"      Path: {info.install_path}")
        print()

    print(f"Detected: {len(detected)} of {len(all_adapters)} providers")
    return 0


def _provider_wire(provider_name: Optional[str] = None) -> int:
    """Generate configs for detected providers."""
    from popkit_shared.providers import detect_providers, get_adapter
    from popkit_shared.utils.home import get_popkit_packages_dir, get_popkit_providers_dir

    packages_dir = get_popkit_packages_dir()
    providers_dir = get_popkit_providers_dir()

    print("PopKit Provider Wiring")
    print("=" * 40)
    print()

    if provider_name:
        adapter = get_adapter(provider_name)
        if not adapter:
            print(f"Error: Unknown provider '{provider_name}'")
            return 1
        adapters_to_wire = [adapter]
    else:
        detected = detect_providers()
        from popkit_shared.providers.registry import _ADAPTER_INSTANCES

        adapters_to_wire = [
            _ADAPTER_INSTANCES[p.name] for p in detected if p.name in _ADAPTER_INSTANCES
        ]

    if not adapters_to_wire:
        print("No providers detected. Install an AI coding tool first.")
        return 1

    for adapter in adapters_to_wire:
        print(f"Wiring {adapter.display_name}...")
        output_dir = providers_dir / adapter.name
        output_dir.mkdir(parents=True, exist_ok=True)

        # Install packages
        installed = 0
        for pkg_dir in sorted(packages_dir.iterdir()):
            if not pkg_dir.is_dir():
                continue
            if pkg_dir.name in ("shared-py", "popkit-mcp", "popkit-cli", "__pycache__"):
                continue

            if adapter.install(pkg_dir):
                installed += 1

        # Generate configs
        generated = adapter.generate_config(packages_dir, output_dir)

        print(f"  Packages wired: {installed}")
        if generated:
            print(f"  Configs generated: {len(generated)}")
            for path in generated:
                print(f"    - {path}")
        print()

    print("Wiring complete.")
    return 0
