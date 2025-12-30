#!/usr/bin/env python3
r"""
Test script for Issue #213 - Platform-aware security path validation

Tests that the pre-tool-use hook correctly validates paths across:
- Windows (C:\Windows, Program Files, APPDATA, Registry)
- macOS (/System/, /Library/System/, ~/Library/Preferences/)
- Linux/Unix (/etc/, /root/, /boot/)
"""

import sys
import os
import json
import importlib.util

# Add the hooks directory to path and import hook module dynamically
hooks_path = os.path.join(os.path.dirname(__file__), "packages", "popkit-core", "hooks", "pre-tool-use.py")

# Load module dynamically
spec = importlib.util.spec_from_file_location("pre_tool_use", hooks_path)
pre_tool_use_module = importlib.util.module_from_spec(spec)
sys.modules["pre_tool_use"] = pre_tool_use_module
spec.loader.exec_module(pre_tool_use_module)

PreToolUseHook = pre_tool_use_module.PreToolUseHook


def test_windows_paths():
    """Test Windows-specific dangerous paths"""
    print("\n=== Testing Windows Paths ===")

    hook = PreToolUseHook()

    # Override platform detection for testing
    original_platform = sys.platform
    sys.platform = "win32"

    test_cases = [
        ("C:\\Windows\\System32\\calc.exe", True),
        ("C:\\Program Files\\MyApp\\config.txt", True),
        ("C:\\Users\\TestUser\\Documents\\file.txt", False),
        ("%APPDATA%\\sensitive\\data.json", True),
        ("C:\\ProgramData\\config.ini", True),
    ]

    for path, should_block in test_cases:
        violations = hook.check_safety_violations("Write", {"file_path": path})
        blocked = len(violations) > 0
        status = "[PASS]" if blocked == should_block else "[FAIL]"
        print(f"{status} {path}: {'BLOCKED' if blocked else 'ALLOWED'} (expected: {'BLOCK' if should_block else 'ALLOW'})")

    # Restore platform
    sys.platform = original_platform


def test_macos_paths():
    """Test macOS-specific dangerous paths"""
    print("\n=== Testing macOS Paths ===")

    hook = PreToolUseHook()

    # Override platform detection for testing
    original_platform = sys.platform
    sys.platform = "darwin"

    test_cases = [
        ("/System/Library/CoreServices/Finder.app", True),
        ("/Library/System/important.conf", True),
        ("~/Library/Preferences/com.apple.Safari.plist", True),
        ("/Users/TestUser/Documents/file.txt", False),
        ("/Applications/Safari.app/Contents/Info.plist", True),
    ]

    for path, should_block in test_cases:
        violations = hook.check_safety_violations("Write", {"file_path": path})
        blocked = len(violations) > 0
        status = "[PASS]" if blocked == should_block else "[FAIL]"
        print(f"{status} {path}: {'BLOCKED' if blocked else 'ALLOWED'} (expected: {'BLOCK' if should_block else 'ALLOW'})")

    # Restore platform
    sys.platform = original_platform


def test_linux_paths():
    """Test Linux/Unix dangerous paths"""
    print("\n=== Testing Linux/Unix Paths ===")

    hook = PreToolUseHook()

    # Override platform detection for testing
    original_platform = sys.platform
    sys.platform = "linux"

    test_cases = [
        ("/etc/passwd", True),
        ("/etc/shadow", True),
        ("/root/.bashrc", True),
        ("/boot/grub/grub.cfg", True),
        ("/home/user/documents/file.txt", False),
        ("~/.ssh/id_rsa", True),
        ("~/.aws/credentials", True),
    ]

    for path, should_block in test_cases:
        violations = hook.check_safety_violations("Write", {"file_path": path})
        blocked = len(violations) > 0
        status = "[PASS]" if blocked == should_block else "[FAIL]"
        print(f"{status} {path}: {'BLOCKED' if blocked else 'ALLOWED'} (expected: {'BLOCK' if should_block else 'ALLOW'})")

    # Restore platform
    sys.platform = original_platform


def test_cross_platform_paths():
    """Test cross-platform paths (temp directories)"""
    print("\n=== Testing Cross-Platform Paths ===")

    hook = PreToolUseHook()

    test_cases = [
        ("/tmp/sensitive_cache", True),
        ("C:\\Windows\\Temp\\temp.dat", True),
        ("~/.cache/app_cache", True),
    ]

    for path, should_block in test_cases:
        violations = hook.check_safety_violations("Write", {"file_path": path})
        blocked = len(violations) > 0
        status = "[PASS]" if blocked == should_block else "[FAIL]"
        print(f"{status} {path}: {'BLOCKED' if blocked else 'ALLOWED'} (expected: {'BLOCK' if should_block else 'ALLOW'})")


def main():
    print("Testing Platform-Aware Security Path Validation (Issue #213)")
    print("=" * 60)

    # Show current platform
    print(f"\nCurrent platform: {sys.platform}")

    # Run all tests
    test_windows_paths()
    test_macos_paths()
    test_linux_paths()
    test_cross_platform_paths()

    print("\n" + "=" * 60)
    print("Testing complete!")


if __name__ == "__main__":
    main()
