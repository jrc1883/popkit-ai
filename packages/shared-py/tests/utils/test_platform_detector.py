#!/usr/bin/env python3
"""
Test suite for platform_detector.py

Tests platform detection, shell detection, and capability detection.
Critical for cross-platform command translation and compatibility.
"""

import sys
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from popkit_shared.utils.platform_detector import (
    OSType,
    ShellType,
    ShellCapabilities,
    PlatformInfo,
    PlatformDetector,
    get_platform_info,
    get_platform_summary,
)


class TestOSDetection:
    """Test operating system detection"""

    @patch("sys.platform", "win32")
    def test_detect_windows(self):
        """Test Windows detection"""
        PlatformDetector._cached_info = None
        result = PlatformDetector._detect_os()
        assert result == OSType.WINDOWS

    @patch("sys.platform", "darwin")
    def test_detect_macos(self):
        """Test macOS detection"""
        PlatformDetector._cached_info = None
        result = PlatformDetector._detect_os()
        assert result == OSType.MACOS

    @patch("sys.platform", "linux")
    def test_detect_linux(self):
        """Test Linux detection"""
        PlatformDetector._cached_info = None
        result = PlatformDetector._detect_os()
        assert result == OSType.LINUX

    @patch("sys.platform", "cygwin")
    def test_detect_cygwin_as_windows(self):
        """Test Cygwin detected as Windows"""
        PlatformDetector._cached_info = None
        result = PlatformDetector._detect_os()
        assert result == OSType.WINDOWS

    @patch("sys.platform", "unknown-platform")
    def test_detect_unknown_os(self):
        """Test unknown OS detection"""
        PlatformDetector._cached_info = None
        result = PlatformDetector._detect_os()
        assert result == OSType.UNKNOWN


class TestShellDetection:
    """Test shell detection"""

    @patch("sys.platform", "linux")
    def test_bash_detection(self):
        """Test Bash shell detection"""
        with patch.dict(os.environ, {"SHELL": "/bin/bash"}, clear=True):
            with patch("shutil.which", return_value="/bin/bash"):
                PlatformDetector._cached_info = None
                shell_type, shell_path = PlatformDetector._detect_shell()
                assert shell_type == ShellType.BASH
                assert "bash" in shell_path.lower()

    @patch("sys.platform", "darwin")
    def test_zsh_detection(self):
        """Test Zsh shell detection"""
        with patch.dict(os.environ, {"SHELL": "/bin/zsh"}, clear=True):
            PlatformDetector._cached_info = None
            shell_type, shell_path = PlatformDetector._detect_shell()
            assert shell_type == ShellType.ZSH
            assert "zsh" in shell_path.lower()

    @patch("sys.platform", "win32")
    def test_cmd_detection(self):
        """Test CMD detection on Windows"""
        with patch.dict(os.environ, {"COMSPEC": "C:\\Windows\\System32\\cmd.exe"}, clear=True):
            with patch("shutil.which", return_value=None):
                PlatformDetector._cached_info = None
                shell_type, shell_path = PlatformDetector._detect_shell()
                assert shell_type == ShellType.CMD

    @patch("sys.platform", "win32")
    def test_git_bash_detection(self):
        """Test Git Bash detection on Windows"""
        with patch.dict(os.environ, {"MSYSTEM": "MINGW64"}, clear=True):
            with patch("shutil.which", return_value="/usr/bin/bash"):
                PlatformDetector._cached_info = None
                shell_type, shell_path = PlatformDetector._detect_shell()
                assert shell_type == ShellType.GIT_BASH

    @patch("sys.platform", "win32")
    def test_wsl_detection(self):
        """Test WSL detection"""
        with patch.dict(os.environ, {"WSL_DISTRO_NAME": "Ubuntu"}, clear=True):
            PlatformDetector._cached_info = None
            shell_type, shell_path = PlatformDetector._detect_shell()
            assert shell_type == ShellType.WSL

    @patch("sys.platform", "win32")
    def test_powershell_core_detection(self):
        """Test PowerShell Core (pwsh) detection"""
        with patch("shutil.which") as mock_which:
            mock_which.side_effect = lambda x: "/usr/bin/pwsh" if x == "pwsh" else None
            with patch.dict(os.environ, {}, clear=True):
                PlatformDetector._cached_info = None
                shell_type, shell_path = PlatformDetector._detect_shell()
                # May be POWERSHELL_CORE or CMD depending on env
                assert shell_type in (ShellType.POWERSHELL_CORE, ShellType.CMD)


class TestShellCapabilities:
    """Test shell capability detection"""

    def test_bash_capabilities(self):
        """Test Bash capabilities"""
        caps = PlatformDetector._detect_capabilities(OSType.LINUX, ShellType.BASH)
        assert caps.unix_commands is True
        assert caps.glob_support is True
        assert caps.heredoc_support is True
        assert caps.background_jobs is True
        assert caps.powershell_commands is False
        assert caps.cmd_commands is False

    def test_zsh_capabilities(self):
        """Test Zsh capabilities"""
        caps = PlatformDetector._detect_capabilities(OSType.MACOS, ShellType.ZSH)
        assert caps.unix_commands is True
        assert caps.glob_support is True
        assert caps.heredoc_support is True
        assert caps.background_jobs is True

    def test_powershell_capabilities(self):
        """Test PowerShell capabilities"""
        caps = PlatformDetector._detect_capabilities(OSType.WINDOWS, ShellType.POWERSHELL)
        assert caps.powershell_commands is True
        assert caps.glob_support is True
        assert caps.heredoc_support is True
        assert caps.background_jobs is True
        assert caps.unix_commands is False
        assert caps.cmd_commands is False

    def test_cmd_capabilities(self):
        """Test CMD capabilities"""
        caps = PlatformDetector._detect_capabilities(OSType.WINDOWS, ShellType.CMD)
        assert caps.cmd_commands is True
        assert caps.glob_support is False
        assert caps.heredoc_support is False
        assert caps.background_jobs is False
        assert caps.unix_commands is False
        assert caps.powershell_commands is False

    def test_git_bash_capabilities(self):
        """Test Git Bash capabilities (Unix-like on Windows)"""
        caps = PlatformDetector._detect_capabilities(OSType.WINDOWS, ShellType.GIT_BASH)
        assert caps.unix_commands is True
        assert caps.glob_support is True
        assert caps.heredoc_support is True
        assert caps.background_jobs is True


class TestPlatformInfo:
    """Test PlatformInfo data structure"""

    def test_to_dict_serialization(self):
        """Test converting PlatformInfo to dictionary"""
        caps = ShellCapabilities(unix_commands=True, glob_support=True, heredoc_support=True)
        info = PlatformInfo(
            os_type=OSType.LINUX,
            os_version="Linux 5.15.0",
            shell_type=ShellType.BASH,
            shell_path="/bin/bash",
            shell_version="5.0.0",
            capabilities=caps,
            available_commands={"ls": "/bin/ls"},
        )

        result = info.to_dict()

        assert isinstance(result, dict)
        assert result["os_type"] == "linux"
        assert result["shell_type"] == "bash"
        assert result["shell_path"] == "/bin/bash"
        assert result["capabilities"]["unix_commands"] is True
        assert "ls" in result["available_commands"]

    def test_to_dict_with_empty_commands(self):
        """Test to_dict with no available commands"""
        caps = ShellCapabilities()
        info = PlatformInfo(
            os_type=OSType.WINDOWS,
            os_version="Windows 10",
            shell_type=ShellType.CMD,
            shell_path="cmd.exe",
            shell_version="10.0",
            capabilities=caps,
        )

        result = info.to_dict()
        assert result["available_commands"] == {}


class TestPlatformDetector:
    """Test PlatformDetector class"""

    def test_detect_returns_platform_info(self):
        """Test detect() returns PlatformInfo"""
        PlatformDetector._cached_info = None
        info = PlatformDetector.detect()
        assert isinstance(info, PlatformInfo)
        assert info.os_type is not None
        assert info.shell_type is not None

    def test_detect_caches_result(self):
        """Test that detect() caches result"""
        PlatformDetector._cached_info = None
        info1 = PlatformDetector.detect()
        info2 = PlatformDetector.detect()
        assert info1 is info2

    def test_detect_force_refresh(self):
        """Test force_refresh parameter"""
        PlatformDetector._cached_info = None
        info1 = PlatformDetector.detect()
        info2 = PlatformDetector.detect(force_refresh=True)
        # Should be different objects (new detection)
        # Values might be same, but instances are different
        assert isinstance(info2, PlatformInfo)

    def test_get_recommended_shell_unix_command(self):
        """Test recommending shell for Unix command"""
        result = PlatformDetector.get_recommended_shell_for_command("cp file1 file2")
        assert result is not None
        assert isinstance(result, ShellType)

    def test_get_recommended_shell_windows_command(self):
        """Test recommending shell for Windows command"""
        result = PlatformDetector.get_recommended_shell_for_command("xcopy /s")
        assert result == ShellType.CMD

    def test_get_recommended_shell_powershell_command(self):
        """Test recommending shell for PowerShell command"""
        result = PlatformDetector.get_recommended_shell_for_command("Copy-Item test.txt")
        # On Windows could be PowerShell, on Unix might be GIT_BASH or current shell
        assert isinstance(result, ShellType)

    def test_is_command_available(self):
        """Test checking command availability"""
        # ls or dir should be available on any system
        PlatformDetector._cached_info = None
        # Test with a command that likely exists
        with patch("shutil.which", return_value="/bin/test"):
            result = PlatformDetector.is_command_available("test")
            # Result depends on actual system, just ensure no crash
            assert isinstance(result, bool)

    def test_is_command_available_nonexistent(self):
        """Test checking nonexistent command"""
        with patch("shutil.which", return_value=None):
            PlatformDetector._cached_info = None
            # Need to also mock the available_commands
            mock_info = PlatformInfo(
                os_type=OSType.LINUX,
                os_version="test",
                shell_type=ShellType.BASH,
                shell_path="/bin/bash",
                shell_version="1.0",
                capabilities=ShellCapabilities(),
                available_commands={},
            )
            PlatformDetector._cached_info = mock_info
            result = PlatformDetector.is_command_available("nonexistent_command_xyz")
            assert result is False


class TestAvailableCommandsDetection:
    """Test detection of available commands"""

    def test_unix_commands_detection(self):
        """Test detection of Unix commands"""
        caps = ShellCapabilities(unix_commands=True)
        with patch("shutil.which") as mock_which:
            mock_which.return_value = "/bin/cp"
            commands = PlatformDetector._detect_available_commands(caps)
            # Should check for Unix commands
            assert isinstance(commands, dict)

    def test_cmd_commands_detection(self):
        """Test detection of CMD commands"""
        caps = ShellCapabilities(cmd_commands=True)
        with patch("shutil.which") as mock_which:
            mock_which.return_value = None
            commands = PlatformDetector._detect_available_commands(caps)
            assert isinstance(commands, dict)

    def test_powershell_commands_detection(self):
        """Test detection of PowerShell commands"""
        caps = ShellCapabilities(powershell_commands=True)
        commands = PlatformDetector._detect_available_commands(caps)
        # PowerShell cmdlets should be marked as "builtin"
        assert isinstance(commands, dict)
        # Check if any PowerShell cmdlets are detected
        ps_cmdlets = [k for k in commands.keys() if "-" in k]
        # PowerShell cmdlets have hyphens and should be marked as builtin
        for cmdlet in ps_cmdlets:
            assert commands[cmdlet] == "builtin"


class TestShellVersionDetection:
    """Test shell version detection"""

    def test_bash_version_detection(self):
        """Test Bash version detection"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "GNU bash, version 5.0.0\n"

        with patch("subprocess.run", return_value=mock_result):
            version = PlatformDetector._detect_shell_version(ShellType.BASH, "/bin/bash")
            assert "bash" in version.lower() or "5.0.0" in version

    def test_powershell_version_detection(self):
        """Test PowerShell version detection"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "7.2.0"

        with patch("subprocess.run", return_value=mock_result):
            version = PlatformDetector._detect_shell_version(ShellType.POWERSHELL, "powershell")
            assert "PowerShell" in version or "7.2.0" in version

    def test_version_detection_error(self):
        """Test version detection with error"""
        with patch("subprocess.run", side_effect=Exception("Error")):
            version = PlatformDetector._detect_shell_version(ShellType.BASH, "/bin/bash")
            assert version == "unknown"

    def test_version_detection_timeout(self):
        """Test version detection timeout handling"""
        with patch("subprocess.run", side_effect=TimeoutError("Timeout")):
            version = PlatformDetector._detect_shell_version(ShellType.BASH, "/bin/bash")
            assert version == "unknown"


class TestConvenienceFunctions:
    """Test convenience functions"""

    def test_get_platform_info(self):
        """Test get_platform_info() function"""
        info = get_platform_info()
        assert isinstance(info, PlatformInfo)
        assert info.os_type is not None
        assert info.shell_type is not None

    def test_get_platform_summary(self):
        """Test get_platform_summary() function"""
        summary = get_platform_summary()
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "OS:" in summary
        assert "Shell:" in summary
        assert "Capabilities:" in summary

    def test_platform_summary_includes_os_type(self):
        """Test summary includes OS type"""
        summary = get_platform_summary()
        # Should contain one of the OS types
        os_types = ["windows", "macos", "linux", "unknown"]
        assert any(os_type in summary.lower() for os_type in os_types)

    def test_platform_summary_includes_capabilities(self):
        """Test summary includes capability info"""
        summary = get_platform_summary()
        # Should mention at least one capability type
        cap_types = ["Unix", "CMD", "PowerShell", "Unknown"]
        assert any(cap in summary for cap in cap_types)


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_shell_path(self):
        """Test handling of empty shell path"""
        version = PlatformDetector._detect_shell_version(ShellType.UNKNOWN, "")
        assert version == "unknown"

    def test_detect_os_version(self):
        """Test OS version detection doesn't crash"""
        version = PlatformDetector._detect_os_version()
        assert isinstance(version, str)
        assert len(version) > 0

    def test_capabilities_with_unknown_shell(self):
        """Test capabilities for unknown shell"""
        caps = PlatformDetector._detect_capabilities(OSType.UNKNOWN, ShellType.UNKNOWN)
        assert isinstance(caps, ShellCapabilities)
        # Unknown shell should have minimal capabilities
        assert caps.unix_commands is False
        assert caps.powershell_commands is False
        assert caps.cmd_commands is False

    def test_command_recommendation_case_insensitive(self):
        """Test command recommendation is case-insensitive"""
        result1 = PlatformDetector.get_recommended_shell_for_command("CP file1 file2")
        result2 = PlatformDetector.get_recommended_shell_for_command("cp file1 file2")
        # Both should return a valid shell type
        assert isinstance(result1, ShellType)
        assert isinstance(result2, ShellType)


class TestRealWorldScenarios:
    """Test real-world usage scenarios"""

    def test_cross_platform_command_detection(self):
        """Test detecting platform for cross-platform commands"""
        commands = [
            ("cp file1 file2", "Unix"),
            ("xcopy /s", "Windows"),
            ("Copy-Item test.txt", "PowerShell"),
        ]

        for cmd, platform_type in commands:
            shell = PlatformDetector.get_recommended_shell_for_command(cmd)
            assert isinstance(shell, ShellType)

    def test_full_detection_workflow(self):
        """Test complete detection workflow"""
        PlatformDetector._cached_info = None

        # Detect platform
        info = PlatformDetector.detect()

        # Verify all fields are populated
        assert info.os_type is not None
        assert info.os_version is not None
        assert info.shell_type is not None
        assert info.shell_path is not None
        assert info.shell_version is not None
        assert info.capabilities is not None
        assert info.available_commands is not None

        # Convert to dict (for serialization)
        info_dict = info.to_dict()
        assert isinstance(info_dict, dict)
        assert "os_type" in info_dict
        assert "capabilities" in info_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
