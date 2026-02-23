#!/usr/bin/env python3
"""
Deploy Configuration Creator.

Creates .claude/popkit/deploy.json from user selections.

Usage:
    python create_deploy_config.py --dir DIR --targets TARGET1,TARGET2 --primary TARGET --ci MODE

Output:
    Creates deploy.json and outputs confirmation
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def get_default_target_config(target: str, project_name: str) -> dict[str, Any]:
    """Get default configuration for a deployment target."""
    configs = {
        "docker": {
            "enabled": True,
            "config": {
                "image_name": project_name.lower().replace(" ", "-"),
                "registry": "ghcr.io",
                "build_context": ".",
                "dockerfile": "Dockerfile",
                "platforms": ["linux/amd64"],
                "tags": ["latest", "{{version}}"],
            },
        },
        "npm": {
            "enabled": True,
            "config": {
                "registry": "https://registry.npmjs.org",
                "access": "public",
                "tag": "latest",
                "dry_run": False,
            },
        },
        "pypi": {
            "enabled": True,
            "config": {
                "registry": "https://upload.pypi.org/legacy/",
                "test_registry": "https://test.pypi.org/legacy/",
                "distributions": ["wheel", "sdist"],
            },
        },
        "vercel": {
            "enabled": True,
            "config": {
                "production_branch": "main",
                "preview_branches": ["develop", "staging"],
                "environment_variables": {},
            },
        },
        "netlify": {
            "enabled": True,
            "config": {
                "production_branch": "main",
                "build_command": "npm run build",
                "publish_directory": "dist",
            },
        },
        "github_releases": {
            "enabled": True,
            "config": {
                "release_notes_source": "changelog",
                "draft": False,
                "prerelease": False,
                "assets": [],
            },
        },
    }

    return configs.get(target, {"enabled": True, "config": {}})


def get_ci_config(mode: str, targets: list[str]) -> dict[str, Any]:
    """Get CI/CD configuration based on mode."""
    if mode == "manual_only":
        return {
            "provider": None,
            "triggers": {},
            "manual_only": True,
        }

    config = {
        "provider": "github_actions",
        "triggers": {
            "push": ["main"],
            "pull_request": ["main"],
        },
        "manual_only": False,
    }

    # Add tag triggers for release-related targets
    if any(t in targets for t in ["npm", "pypi", "github_releases", "docker"]):
        config["triggers"]["tag"] = ["v*"]

    if mode == "both":
        config["workflow_dispatch"] = True

    return config


def create_deploy_config(
    project_dir: Path,
    project_name: str,
    targets: list[str],
    primary_target: str,
    ci_mode: str,
) -> dict[str, Any]:
    """Create the deploy.json configuration."""
    config = {
        "version": "1.0",
        "project_name": project_name,
        "created_at": datetime.now().isoformat(),
        "targets": {},
        "ci": get_ci_config(ci_mode, targets),
        "history": [],
    }

    # Add target configurations
    for target in targets:
        target_config = get_default_target_config(target, project_name)
        target_config["primary"] = target == primary_target
        config["targets"][target] = target_config

    return config


def write_config(project_dir: Path, config: dict[str, Any]) -> Path:
    """Write configuration to .claude/popkit/deploy.json."""
    config_dir = project_dir / ".claude" / "popkit"
    config_dir.mkdir(parents=True, exist_ok=True)

    config_file = config_dir / "deploy.json"

    # Backup existing config if present
    if config_file.exists():
        backup_file = (
            config_dir
            / f"deploy.backup.{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        )
        backup_file.write_text(config_file.read_text())

    config_file.write_text(json.dumps(config, indent=2))
    return config_file


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Create deploy configuration")
    parser.add_argument("--dir", default=".", help="Project directory")
    parser.add_argument(
        "--targets", required=True, help="Comma-separated list of targets"
    )
    parser.add_argument("--primary", help="Primary deployment target")
    parser.add_argument(
        "--ci",
        default="github_actions",
        choices=["github_actions", "manual_only", "both"],
        help="CI/CD mode",
    )
    parser.add_argument(
        "--project-name", help="Project name (auto-detected if not provided)"
    )
    args = parser.parse_args()

    project_dir = Path(args.dir).resolve()
    targets = [t.strip() for t in args.targets.split(",") if t.strip()]

    if not targets:
        print(
            json.dumps({"error": "No targets specified"}, indent=2),
            file=sys.stderr,
        )
        return 1

    # Get project name
    project_name = args.project_name
    if not project_name:
        pkg_json = project_dir / "package.json"
        if pkg_json.exists():
            try:
                pkg = json.loads(pkg_json.read_text())
                project_name = pkg.get("name", "").split("/")[-1]
            except (json.JSONDecodeError, OSError):
                # Best-effort: skip if package.json is malformed or unreadable
                pass

        if not project_name:
            project_name = project_dir.name

    # Determine primary target
    primary_target = args.primary if args.primary else targets[0]
    if primary_target not in targets:
        primary_target = targets[0]

    # Create configuration
    config = create_deploy_config(
        project_dir=project_dir,
        project_name=project_name,
        targets=targets,
        primary_target=primary_target,
        ci_mode=args.ci,
    )

    # Write configuration
    config_file = write_config(project_dir, config)

    report = {
        "operation": "create_deploy_config",
        "success": True,
        "config_file": str(config_file),
        "project_name": project_name,
        "targets": targets,
        "primary_target": primary_target,
        "ci_mode": args.ci,
        "config": config,
    }

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
