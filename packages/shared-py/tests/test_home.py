#!/usr/bin/env python3
"""Tests for popkit_shared.utils.home — cross-platform POPKIT_HOME resolution."""

import os
from pathlib import Path
from unittest.mock import patch

from popkit_shared.utils.home import (
    _platform_default,
    get_popkit_bin_dir,
    get_popkit_data_dir,
    get_popkit_home,
    get_popkit_packages_dir,
    get_popkit_providers_dir,
)


class TestGetPopkitHome:
    """Tests for get_popkit_home()."""

    def test_uses_popkit_home_env_var(self, tmp_path):
        """POPKIT_HOME env var takes priority."""
        custom_home = tmp_path / "custom-popkit"
        with patch.dict(os.environ, {"POPKIT_HOME": str(custom_home)}):
            result = get_popkit_home()
            assert result == custom_home
            assert result.is_dir()

    def test_creates_directory_if_missing(self, tmp_path):
        """Directory is created when it doesn't exist."""
        custom_home = tmp_path / "new" / "nested" / "popkit"
        assert not custom_home.exists()
        with patch.dict(os.environ, {"POPKIT_HOME": str(custom_home)}):
            result = get_popkit_home()
            assert result.is_dir()

    def test_falls_back_to_platform_default(self, tmp_path):
        """Without env var, uses platform default."""
        with patch.dict(os.environ, {}, clear=False):
            # Remove POPKIT_HOME if set
            os.environ.pop("POPKIT_HOME", None)
            with patch(
                "popkit_shared.utils.home._platform_default", return_value=tmp_path / ".popkit"
            ):
                result = get_popkit_home()
                assert result == tmp_path / ".popkit"


class TestPlatformDefault:
    """Tests for _platform_default()."""

    def test_linux_default(self):
        """Linux uses ~/.popkit by default."""
        with patch("popkit_shared.utils.home.sys") as mock_sys:
            mock_sys.platform = "linux"
            with patch.dict(os.environ, {}, clear=False):
                os.environ.pop("XDG_DATA_HOME", None)
                result = _platform_default()
                assert result == Path.home() / ".popkit"

    def test_linux_xdg_fallback(self, tmp_path):
        """Linux respects XDG_DATA_HOME."""
        with patch("popkit_shared.utils.home.sys") as mock_sys:
            mock_sys.platform = "linux"
            xdg = tmp_path / "xdg-data"
            with patch.dict(os.environ, {"XDG_DATA_HOME": str(xdg)}):
                result = _platform_default()
                assert result == xdg / "popkit"

    def test_macos_default(self):
        """macOS uses ~/.popkit."""
        with patch("popkit_shared.utils.home.sys") as mock_sys:
            mock_sys.platform = "darwin"
            result = _platform_default()
            assert result == Path.home() / ".popkit"

    def test_windows_appdata(self, tmp_path):
        """Windows uses %APPDATA%/popkit."""
        with patch("popkit_shared.utils.home.sys") as mock_sys:
            mock_sys.platform = "win32"
            appdata = tmp_path / "AppData" / "Roaming"
            with patch.dict(os.environ, {"APPDATA": str(appdata)}, clear=False):
                os.environ.pop("MSYSTEM", None)
                os.environ.pop("MINGW_PREFIX", None)
                result = _platform_default()
                assert result == appdata / "popkit"

    def test_windows_git_bash(self):
        """Windows in Git Bash uses ~/.popkit."""
        with patch("popkit_shared.utils.home.sys") as mock_sys:
            mock_sys.platform = "win32"
            with patch.dict(os.environ, {"MSYSTEM": "MINGW64"}):
                result = _platform_default()
                assert result == Path.home() / ".popkit"


class TestSubdirectories:
    """Tests for subdirectory helpers."""

    def test_packages_dir(self, tmp_path):
        """get_popkit_packages_dir returns packages/ subdir."""
        with patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}):
            result = get_popkit_packages_dir()
            assert result == tmp_path / "packages"
            assert result.is_dir()

    def test_providers_dir(self, tmp_path):
        """get_popkit_providers_dir returns providers/ subdir."""
        with patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}):
            result = get_popkit_providers_dir()
            assert result == tmp_path / "providers"
            assert result.is_dir()

    def test_data_dir(self, tmp_path):
        """get_popkit_data_dir returns data/ subdir."""
        with patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}):
            result = get_popkit_data_dir()
            assert result == tmp_path / "data"
            assert result.is_dir()

    def test_bin_dir(self, tmp_path):
        """get_popkit_bin_dir returns bin/ subdir."""
        with patch.dict(os.environ, {"POPKIT_HOME": str(tmp_path)}):
            result = get_popkit_bin_dir()
            assert result == tmp_path / "bin"
            assert result.is_dir()
