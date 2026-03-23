#!/usr/bin/env python3
"""Tests for popkit_shared.utils.plugin_data — v2 POPKIT_HOME integration."""

import os
from pathlib import Path
from unittest.mock import patch

from popkit_shared.utils.plugin_data import (
    get_global_plugin_data_dir,
    get_plugin_data_dir,
    get_plugin_data_subdir,
)


class TestPluginDataDirV2:
    """Tests for the v2 resolution chain in get_plugin_data_dir()."""

    def test_popkit_home_takes_priority(self, tmp_path):
        """POPKIT_HOME env var takes highest priority."""
        popkit_home = tmp_path / "popkit-home"
        with patch.dict(os.environ, {"POPKIT_HOME": str(popkit_home)}, clear=False):
            os.environ.pop("CLAUDE_PLUGIN_DATA", None)
            result = get_plugin_data_dir()
            assert result == popkit_home / "data"
            assert result.is_dir()

    def test_claude_plugin_data_second_priority(self, tmp_path):
        """CLAUDE_PLUGIN_DATA used when POPKIT_HOME not set."""
        plugin_data = tmp_path / "claude-plugin-data"
        with patch.dict(os.environ, {"CLAUDE_PLUGIN_DATA": str(plugin_data)}, clear=False):
            os.environ.pop("POPKIT_HOME", None)
            result = get_plugin_data_dir()
            assert result == plugin_data
            assert result.is_dir()

    def test_popkit_home_over_claude_plugin_data(self, tmp_path):
        """POPKIT_HOME wins over CLAUDE_PLUGIN_DATA."""
        popkit_home = tmp_path / "popkit-home"
        plugin_data = tmp_path / "claude-data"
        with patch.dict(
            os.environ,
            {"POPKIT_HOME": str(popkit_home), "CLAUDE_PLUGIN_DATA": str(plugin_data)},
        ):
            result = get_plugin_data_dir()
            assert result == popkit_home / "data"

    def test_platform_default_when_exists(self, tmp_path):
        """Uses ~/.popkit/data when ~/.popkit exists and no env vars."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("POPKIT_HOME", None)
            os.environ.pop("CLAUDE_PLUGIN_DATA", None)
            with patch(
                "popkit_shared.utils.home._platform_default",
                return_value=tmp_path / ".popkit",
            ):
                # Create the directory to simulate v2 install
                (tmp_path / ".popkit").mkdir()
                result = get_plugin_data_dir()
                assert result == tmp_path / ".popkit" / "data"

    def test_legacy_fallback_when_no_popkit_home(self, tmp_path, monkeypatch):
        """Falls back to .claude/popkit/ when nothing else exists."""
        monkeypatch.delenv("POPKIT_HOME", raising=False)
        monkeypatch.delenv("CLAUDE_PLUGIN_DATA", raising=False)

        nonexistent = tmp_path / "nonexistent"
        with patch(
            "popkit_shared.utils.home._platform_default",
            return_value=nonexistent,
        ):
            monkeypatch.chdir(tmp_path)
            result = get_plugin_data_dir()
            assert result == tmp_path / ".claude" / "popkit"

    def test_subdir_under_popkit_home(self, tmp_path):
        """get_plugin_data_subdir works with POPKIT_HOME."""
        popkit_home = tmp_path / "popkit"
        with patch.dict(os.environ, {"POPKIT_HOME": str(popkit_home)}, clear=False):
            result = get_plugin_data_subdir("sessions", "active")
            assert result == popkit_home / "data" / "sessions" / "active"
            assert result.is_dir()


class TestGlobalPluginDataDirV2:
    """Tests for v2 get_global_plugin_data_dir()."""

    def test_uses_popkit_home(self, tmp_path):
        """Global dir uses POPKIT_HOME/data."""
        popkit_home = tmp_path / "popkit"
        with patch.dict(os.environ, {"POPKIT_HOME": str(popkit_home)}):
            result = get_global_plugin_data_dir()
            assert result == popkit_home / "data"
            assert result.is_dir()

    def test_legacy_fallback(self, tmp_path):
        """Falls back to ~/.claude/popkit/ without POPKIT_HOME."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("POPKIT_HOME", None)
            nonexistent = tmp_path / "nonexistent"
            with patch(
                "popkit_shared.utils.home._platform_default",
                return_value=nonexistent,
            ):
                result = get_global_plugin_data_dir()
                assert result == Path.home() / ".claude" / "popkit"
