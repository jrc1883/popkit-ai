#!/usr/bin/env python3
"""
Claude Code Provider Adapter

Passthrough adapter that wraps the existing Claude Code plugin system.
Since PopKit was originally built for Claude Code, this adapter does
minimal translation — the existing system works as-is.

Part of the PopKit v2.0 provider-agnostic architecture.
"""

import json
import os
from pathlib import Path
from typing import List, Optional

from .base import ProviderAdapter, ProviderInfo, ToolMapping
from .tool_mapping import CLAUDE_CODE_MAPPINGS


class ClaudeCodeAdapter(ProviderAdapter):
    """Claude Code provider adapter.

    This is a passthrough wrapper — PopKit packages are already in
    Claude Code's native plugin format. The adapter handles detection
    and wiring (symlinks from ~/.popkit/packages/ to ~/.claude/plugins/).
    """

    @property
    def name(self) -> str:
        return "claude-code"

    @property
    def display_name(self) -> str:
        return "Claude Code"

    def detect(self) -> ProviderInfo:
        """Detect Claude Code installation.

        Checks for:
        1. CLAUDE_PLUGIN_DATA or CLAUDE_PLUGIN_ROOT env vars (running inside CC)
        2. ~/.claude/ directory existence
        3. 'claude' command on PATH
        """
        # Check if we're running inside Claude Code
        has_env = bool(os.environ.get("CLAUDE_PLUGIN_DATA") or os.environ.get("CLAUDE_PLUGIN_ROOT"))

        # Check for ~/.claude/ directory
        claude_dir = Path.home() / ".claude"
        has_dir = claude_dir.is_dir()

        # Check for settings.json (indicates CC is configured)
        settings_path = claude_dir / "settings.json"
        has_settings = settings_path.is_file()

        version = self._detect_version()

        return ProviderInfo(
            name=self.name,
            display_name=self.display_name,
            version=version,
            install_path=claude_dir if has_dir else None,
            is_available=has_env or has_settings,
        )

    def generate_config(self, package_dir: Path, output_dir: Path) -> List[Path]:
        """Generate Claude Code config (mostly passthrough).

        Claude Code reads .claude-plugin/plugin.json directly from
        the package directory. For wiring, we just need to ensure
        the symlink exists.

        Args:
            package_dir: Path to the PopKit package
            output_dir: Path to write generated configs

        Returns:
            List of generated file paths (empty for passthrough)
        """
        # Claude Code reads plugin.json directly — no config generation needed
        # The install() method handles symlinking
        return []

    def get_tool_mappings(self) -> List[ToolMapping]:
        """Get Claude Code tool mappings."""
        return CLAUDE_CODE_MAPPINGS

    def install(self, package_dir: Path) -> bool:
        """Wire a PopKit package into Claude Code via symlink.

        Creates: ~/.claude/plugins/{package_name} → package_dir

        Args:
            package_dir: Path to the PopKit package

        Returns:
            True if installation succeeded
        """
        package_name = package_dir.name
        plugins_dir = Path.home() / ".claude" / "plugins"
        plugins_dir.mkdir(parents=True, exist_ok=True)

        link_path = plugins_dir / package_name

        # Remove existing link if present
        if link_path.is_symlink():
            link_path.unlink()
        elif link_path.exists():
            # Not a symlink but exists — don't overwrite
            return False

        try:
            link_path.symlink_to(package_dir, target_is_directory=True)
            return True
        except OSError:
            return False

    def uninstall(self, package_name: str) -> bool:
        """Remove a PopKit package from Claude Code.

        Removes the symlink from ~/.claude/plugins/.

        Args:
            package_name: Name of the package to uninstall

        Returns:
            True if uninstallation succeeded
        """
        link_path = Path.home() / ".claude" / "plugins" / package_name

        if link_path.is_symlink():
            link_path.unlink()
            return True

        return False

    def _detect_version(self) -> Optional[str]:
        """Try to detect Claude Code version from settings or env."""
        try:
            settings_path = Path.home() / ".claude" / "settings.json"
            if settings_path.is_file():
                with open(settings_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                return settings.get("version")
        except (json.JSONDecodeError, IOError):
            pass
        return None
