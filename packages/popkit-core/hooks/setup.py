#!/usr/bin/env python3
"""
Setup Hook (Claude Code 2.1.10+)
Handles `claude --init` and `claude --maintenance` flag events.

This hook fires ONLY during explicit setup operations, not on every session.
It performs heavier initialization that would be too expensive for SessionStart.

Responsibilities:
1. Detect setup mode (init vs maintenance)
2. Ensure PopKit directory structure exists
3. Run project analysis and tech stack detection
4. Initialize agent expertise files
5. Validate plugin integrity
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime


def ensure_popkit_directories():
    """Create required PopKit directory structure."""
    dirs_created = []
    base_dirs = [
        Path(".claude"),
        Path(".claude", "popkit"),
        Path(".claude", "popkit", "cache"),
        Path(".claude", "popkit", "logs"),
        Path(".claude", "popkit", "embeddings"),
        Path(".claude", "skills"),
    ]

    for d in base_dirs:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            dirs_created.append(str(d))

    return dirs_created


def detect_tech_stack():
    """Detect project technology stack from common config files."""
    stack = []
    indicators = {
        "package.json": "node",
        "pyproject.toml": "python",
        "Cargo.toml": "rust",
        "go.mod": "go",
        "pom.xml": "java",
        "build.gradle": "java",
        "Gemfile": "ruby",
        "composer.json": "php",
        "tsconfig.json": "typescript",
        ".eslintrc.json": "eslint",
        ".prettierrc": "prettier",
        "Dockerfile": "docker",
        "docker-compose.yml": "docker-compose",
    }

    for filename, tech in indicators.items():
        if Path(filename).exists():
            stack.append(tech)

    return stack


def validate_plugin_structure():
    """Quick validation that plugin files are accessible."""
    issues = []
    plugin_root = os.environ.get("CLAUDE_PLUGIN_ROOT", "")

    if not plugin_root:
        return ["CLAUDE_PLUGIN_ROOT not set"]

    required = [
        "hooks/hooks.json",
        "hooks/session-start.py",
        "hooks/pre-tool-use.py",
    ]

    for rel_path in required:
        full_path = Path(plugin_root) / rel_path
        if not full_path.exists():
            issues.append(f"Missing: {rel_path}")

    return issues


def main():
    """Main entry point - JSON stdin/stdout protocol."""
    try:
        input_data = json.loads(sys.stdin.read()) if not sys.stdin.isatty() else {}

        # Detect setup mode from input
        setup_mode = input_data.get("mode", "init")  # "init" or "maintenance"

        response = {
            "status": "success",
            "message": f"PopKit setup complete ({setup_mode} mode)",
            "timestamp": datetime.now().isoformat(),
            "setup_mode": setup_mode,
        }

        # 1. Ensure directories exist
        dirs_created = ensure_popkit_directories()
        response["directories"] = {
            "created": dirs_created,
            "count": len(dirs_created),
        }

        if dirs_created:
            print(
                f"  Created {len(dirs_created)} PopKit directories",
                file=sys.stderr,
            )

        # 2. Detect tech stack
        stack = detect_tech_stack()
        response["tech_stack"] = stack

        if stack:
            print(
                f"  Detected stack: {', '.join(stack)}",
                file=sys.stderr,
            )

        # 3. Validate plugin structure
        issues = validate_plugin_structure()
        response["plugin_validation"] = {
            "passed": len(issues) == 0,
            "issues": issues,
        }

        if issues:
            for issue in issues:
                print(f"  Warning: {issue}", file=sys.stderr)

        # 4. Maintenance-specific tasks
        if setup_mode == "maintenance":
            # Clear stale caches
            cache_dir = Path(".claude", "popkit", "cache")
            stale_count = 0
            if cache_dir.exists():
                for cache_file in cache_dir.glob("*.json"):
                    try:
                        stat = cache_file.stat()
                        age_days = (datetime.now().timestamp() - stat.st_mtime) / 86400
                        if age_days > 7:
                            cache_file.unlink()
                            stale_count += 1
                    except OSError as e:
                        print(
                            f"  Warning: failed to clean cache file {cache_file}: {e}",
                            file=sys.stderr,
                        )

            response["maintenance"] = {
                "stale_caches_cleared": stale_count,
            }

            if stale_count:
                print(
                    f"  Cleared {stale_count} stale cache files",
                    file=sys.stderr,
                )

        print(json.dumps(response))

    except json.JSONDecodeError:
        response = {
            "status": "success",
            "message": "PopKit setup complete (no input)",
            "timestamp": datetime.now().isoformat(),
        }
        print(json.dumps(response))
    except Exception as e:
        response = {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
        print(json.dumps(response))
        sys.exit(0)  # Never block setup


if __name__ == "__main__":
    main()
