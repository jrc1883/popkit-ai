#!/usr/bin/env python3
"""
Project Configuration Utility

CLI tool to configure .popkit/project.json for customizing project detection.

Usage:
    python configure_project.py show
    python configure_project.py set-services 3000 8080
    python configure_project.py set-package-manager pnpm
    python configure_project.py clear-cache
    python configure_project.py detect

Issue #69: Generic Workspace Routine Templates - Configuration CLI
"""

import json
import sys
from pathlib import Path

from .project_config import ProjectConfig, get_project_type_with_cache


def show_config(config_manager: ProjectConfig):
    """Show current project configuration."""
    config = config_manager.load()

    if not config:
        print("No project configuration found.")
        print("Run a morning/nightly routine to initialize: .popkit/project.json")
        return 1

    print("Current Project Configuration:")
    print("=" * 60)
    print(json.dumps(config, indent=2))
    print("=" * 60)

    # Show cache validity
    if config_manager.is_cache_valid(config):
        print("\n[OK] Cache is valid and will be used")
    else:
        print("\n[WARN] Cache is expired, will re-detect on next routine")

    return 0


def set_services(config_manager: ProjectConfig, ports: list):
    """Set expected services by port numbers."""
    if not ports:
        print("Error: Provide at least one port number")
        print("Usage: configure_project.py set-services 3000 8080 5432")
        return 1

    services = []
    for port_str in ports:
        try:
            port = int(port_str)
            services.append(
                {
                    "name": f"service-{port}",
                    "port": port,
                    "description": f"Service on port {port}",
                }
            )
        except ValueError:
            print(f"Error: Invalid port number: {port_str}")
            return 1

    # Update overrides
    if config_manager.update_overrides({"expected_services": services}):
        print(f"[OK] Set {len(services)} expected services:")
        for service in services:
            print(f"  - {service['name']} on port {service['port']}")
        return 0
    else:
        print("[ERROR] Failed to update configuration")
        return 1


def set_package_manager(config_manager: ProjectConfig, package_manager: str):
    """Set package manager override."""
    valid_managers = [
        "npm",
        "pnpm",
        "yarn",
        "pip",
        "poetry",
        "cargo",
        "go",
        "bundler",
        "maven",
        "gradle",
        "dotnet",
    ]

    if package_manager not in valid_managers:
        print(f"Warning: {package_manager} is not a recognized package manager")
        print(f"Valid options: {', '.join(valid_managers)}")
        print("Proceeding anyway...")

    if config_manager.update_overrides({"package_manager": package_manager}):
        print(f"[OK] Set package manager to: {package_manager}")
        return 0
    else:
        print("[ERROR] Failed to update configuration")
        return 1


def clear_cache(config_manager: ProjectConfig):
    """Clear cached project detection."""
    if config_manager.clear_cache():
        print("[OK] Cache cleared. Next routine will re-detect project type.")
        return 0
    else:
        print("[ERROR] Failed to clear cache")
        return 1


def force_detect(project_path: str):
    """Force fresh project detection."""
    print("Detecting project type...")

    project_type = get_project_type_with_cache(project_path, force_refresh=True)

    if project_type:
        print("\n[OK] Project detected successfully:")
        print(f"  Language: {project_type.primary_language}")
        print(f"  Package Manager: {project_type.package_manager}")
        print(f"  Test Framework: {project_type.test_framework}")
        print(f"  Build Tool: {project_type.build_tool}")

        if project_type.expected_services:
            print("\n  Expected Services:")
            for service in project_type.expected_services:
                print(f"    - {service['name']} on port {service['port']}")

        print("\n[OK] Configuration saved to .popkit/project.json")
        return 0
    else:
        print("\n[ERROR] Project detection failed")
        return 1


def main():
    """Main CLI entry point."""
    if len(sys.argv) < 2:
        print("Project Configuration Utility")
        print("\nUsage:")
        print("  python configure_project.py show")
        print("  python configure_project.py set-services <port1> <port2> ...")
        print("  python configure_project.py set-package-manager <npm|pnpm|yarn|...>")
        print("  python configure_project.py clear-cache")
        print("  python configure_project.py detect")
        return 1

    command = sys.argv[1]
    project_path = Path.cwd()
    config_manager = ProjectConfig(str(project_path))

    if command == "show":
        return show_config(config_manager)

    elif command == "set-services":
        return set_services(config_manager, sys.argv[2:])

    elif command == "set-package-manager":
        if len(sys.argv) < 3:
            print("Error: Provide package manager name")
            return 1
        return set_package_manager(config_manager, sys.argv[2])

    elif command == "clear-cache":
        return clear_cache(config_manager)

    elif command == "detect":
        return force_detect(str(project_path))

    else:
        print(f"Unknown command: {command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
