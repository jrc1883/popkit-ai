#!/usr/bin/env python3
"""
Tests for subprocess_utils module.

Issue #303: Consolidate duplicated run_command function
"""

import subprocess
import sys

import pytest

from popkit_shared.utils.subprocess_utils import (
    _resolve_command_executable,
    run_command,
    run_command_checked,
    run_command_full,
    run_command_simple,
    run_git_command,
)


class TestRunCommand:
    """Tests for run_command (full result)."""

    def test_resolves_executable_for_list_command(self, monkeypatch):
        """Test list commands resolve platform-specific executables."""
        monkeypatch.setattr(
            "popkit_shared.utils.subprocess_utils.shutil.which",
            lambda name: "/mock/npm.cmd" if name == "npm" else None,
        )

        assert _resolve_command_executable(["npm", "run", "lint:ts"]) == [
            "/mock/npm.cmd",
            "run",
            "lint:ts",
        ]

    def test_successful_command_with_list(self):
        """Test successful command with list input."""
        exit_code, stdout, stderr = run_command([sys.executable, "-c", "print('hello')"])
        assert exit_code == 0
        assert "hello" in stdout
        assert stderr == ""

    def test_successful_command_with_string(self):
        """Test successful command with string input."""
        exit_code, stdout, stderr = run_command("git --version")
        assert exit_code == 0
        assert "git version" in stdout.lower()

    def test_command_with_cwd(self, tmp_path):
        """Test command with working directory."""
        # Create a test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        exit_code, stdout, stderr = run_command(
            [
                sys.executable,
                "-c",
                "from pathlib import Path; print('\\n'.join(p.name for p in Path('.').iterdir()))",
            ],
            cwd=tmp_path,
        )
        assert exit_code == 0
        assert "test.txt" in stdout

    def test_command_with_path_cwd(self, tmp_path):
        """Test command with Path object as cwd."""
        exit_code, stdout, stderr = run_command(
            [sys.executable, "-c", "import os; print(os.getcwd())"], cwd=tmp_path
        )
        assert exit_code == 0

    def test_failed_command(self):
        """Test command that fails."""
        exit_code, stdout, stderr = run_command(["ls", "/nonexistent_directory_12345"])
        assert exit_code != 0

    def test_timeout_handling(self):
        """Test command timeout."""
        # This command would hang without timeout
        exit_code, stdout, stderr = run_command(
            [sys.executable, "-c", "import time; time.sleep(10)"], timeout=1
        )
        assert exit_code == -1
        assert "timed out" in stderr.lower()

    def test_command_not_found(self):
        """Test handling of non-existent command."""
        exit_code, stdout, stderr = run_command(["nonexistent_command_12345"])
        assert exit_code == -1
        assert "not found" in stderr.lower() or "No such file" in stderr

    def test_output_stripped(self):
        """Test that output is stripped of whitespace."""
        exit_code, stdout, stderr = run_command([sys.executable, "-c", "print('  hello  ')"])
        # echo adds its own newline, but we strip
        assert stdout.strip() == "hello"


class TestRunCommandSimple:
    """Tests for run_command_simple (simplified result)."""

    def test_successful_command(self):
        """Test successful command returns output and True."""
        output, success = run_command_simple([sys.executable, "-c", "print('hello')"])
        assert success is True
        assert "hello" in output

    def test_failed_command(self):
        """Test failed command returns error and False."""
        output, success = run_command_simple(
            [
                sys.executable,
                "-c",
                "import sys; sys.stderr.write('missing\\n'); sys.exit(2)",
            ]
        )
        assert success is False
        assert "missing" in output

    def test_with_cwd(self, tmp_path):
        """Test command with working directory."""
        output, success = run_command_simple(
            [sys.executable, "-c", "import os; print(os.getcwd())"], cwd=tmp_path
        )
        assert success is True

    def test_timeout(self):
        """Test timeout returns error message and False."""
        output, success = run_command_simple(
            [sys.executable, "-c", "import time; time.sleep(10)"], timeout=1
        )
        assert success is False
        assert "timed out" in output.lower()


class TestRunCommandChecked:
    """Tests for run_command_checked (raises on failure)."""

    def test_successful_command(self):
        """Test successful command returns output."""
        output = run_command_checked([sys.executable, "-c", "print('hello')"])
        assert "hello" in output

    def test_failed_command_raises(self):
        """Test failed command raises RuntimeError."""
        with pytest.raises(RuntimeError) as exc_info:
            run_command_checked("ls /nonexistent_directory_12345")
        assert "Command failed" in str(exc_info.value)

    def test_timeout_raises(self):
        """Test timeout raises RuntimeError."""
        with pytest.raises(RuntimeError) as exc_info:
            run_command_checked([sys.executable, "-c", "import time; time.sleep(10)"], timeout=1)
        assert "timed out" in str(exc_info.value).lower()


class TestRunGitCommand:
    """Tests for run_git_command helper."""

    def test_git_command_string(self, tmp_path):
        """Test git command with string args."""
        # Initialize a git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)

        output, success = run_git_command("status", cwd=tmp_path)
        assert success is True

    def test_git_command_list(self, tmp_path):
        """Test git command with list args."""
        # Initialize a git repo
        subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)

        output, success = run_git_command(["status", "--short"], cwd=tmp_path)
        assert success is True

    def test_git_command_not_a_repo(self, tmp_path):
        """Test git command in non-repo directory."""
        output, success = run_git_command("status", cwd=tmp_path)
        assert success is False


class TestRunCommandFull:
    """Tests for legacy run_command_full compatibility."""

    def test_legacy_signature(self, tmp_path):
        """Test legacy signature works."""
        exit_code, stdout, stderr = run_command_full(
            [sys.executable, "-c", "print('hello')"], str(tmp_path), timeout=30
        )
        assert exit_code == 0
        assert "hello" in stdout


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_command(self):
        """Test handling of empty command."""
        exit_code, stdout, stderr = run_command([])
        assert exit_code == -1

    def test_command_with_special_chars(self):
        """Test command with special characters in output."""
        exit_code, stdout, stderr = run_command([sys.executable, "-c", "print('hello\\tworld')"])
        assert exit_code == 0

    def test_large_output(self):
        """Test handling of large output."""
        # Generate large output
        exit_code, stdout, stderr = run_command([sys.executable, "-c", "print('x' * 10000)"])
        assert exit_code == 0
        assert len(stdout) >= 10000

    def test_stderr_capture(self):
        """Test that stderr is captured separately."""
        exit_code, stdout, stderr = run_command(
            [sys.executable, "-c", "import sys; sys.stderr.write('error\\n')"]
        )
        assert exit_code == 0
        assert "error" in stderr
