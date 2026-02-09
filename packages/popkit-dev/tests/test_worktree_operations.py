#!/usr/bin/env python3
"""
Unit Tests for Git Worktree Operations.

Test suite for the pop-worktree-manager skill.
Covers all 8 operations with various edge cases.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(
    0, str(Path(__file__).parents[1] / "skills" / "pop-worktree-manager" / "scripts")
)

from worktree_operations import (
    DEFAULT_CONFIG,
    enable_windows_longpaths,
    load_config,
    operation_analyze,
    operation_create,
    operation_init,
    operation_list,
    operation_prune,
    operation_remove,
    operation_switch,
    operation_update_all,
    resolve_worktree_path,
    run_git_command,
)


class TestGitCommandExecution(unittest.TestCase):
    """Test safe git command execution."""

    @patch("subprocess.run")
    def test_run_git_command_success(self, mock_run):
        """Test successful command execution."""
        mock_run.return_value = MagicMock(stdout="output\n", returncode=0)

        output, ok = run_git_command("status")

        self.assertTrue(ok)
        self.assertEqual(output, "output")
        mock_run.assert_called_once()

    @patch("subprocess.run")
    def test_run_git_command_failure(self, mock_run):
        """Test failed command execution returns stderr on failure."""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_result.stderr = "error\n"
        mock_run.return_value = mock_result

        output, ok = run_git_command("invalid")

        self.assertFalse(ok)
        self.assertEqual(output, "error")

    @patch("subprocess.run")
    def test_run_git_command_timeout(self, mock_run):
        """Test command timeout handling."""
        mock_run.side_effect = subprocess.TimeoutExpired("git", 30)

        output, ok = run_git_command("status")

        self.assertFalse(ok)
        self.assertEqual(output, "Command timed out")


class TestConfiguration(unittest.TestCase):
    """Test configuration loading and defaults."""

    def test_default_config(self):
        """Test default configuration values."""
        config = DEFAULT_CONFIG

        self.assertIn("worktree", config)
        self.assertTrue(config["worktree"]["enabled"])
        self.assertEqual(config["worktree"]["worktreeDir"], "../[project]-worktrees")
        self.assertEqual(config["worktree"]["namingPattern"], "dev-[branch]")

    def test_load_config_with_no_file(self):
        """Test loading config when file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("pathlib.Path.cwd", return_value=Path(tmpdir)):
                config = load_config()

                self.assertEqual(config, DEFAULT_CONFIG)

    def test_load_config_with_file(self):
        """Test loading config from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = Path(tmpdir) / ".popkit"
            config_dir.mkdir()
            config_file = config_dir / "config.json"

            custom_config = {
                "worktree": {
                    "enabled": True,
                    "worktreeDir": "./worktrees",
                    "namingPattern": "[branch]",
                }
            }

            config_file.write_text(json.dumps(custom_config))

            with patch("pathlib.Path.cwd", return_value=Path(tmpdir)):
                config = load_config()

                self.assertEqual(config["worktree"]["worktreeDir"], "./worktrees")
                self.assertEqual(config["worktree"]["namingPattern"], "[branch]")

    def test_protected_branches_in_config(self):
        """Test protected branches are in default config."""
        config = DEFAULT_CONFIG

        protected = config["worktree"]["protectedBranches"]
        self.assertIn("main", protected)
        self.assertIn("master", protected)
        self.assertIn("develop", protected)
        self.assertIn("production", protected)


class TestPathResolution(unittest.TestCase):
    """Test worktree path resolution."""

    @patch("worktree_operations.get_project_name", return_value="test-project")
    @patch("worktree_operations.run_git_command")
    def test_resolve_worktree_path_basic(self, mock_git, mock_project):
        """Test basic path resolution."""
        mock_git.return_value = ("/home/user/project", True)

        config = DEFAULT_CONFIG
        path = resolve_worktree_path("feat/new-feature", config)

        self.assertIn("test-project-worktrees", str(path))
        self.assertIn("dev-feat-new-feature", str(path))

    @patch("worktree_operations.get_project_name", return_value="test-project")
    @patch("worktree_operations.run_git_command")
    def test_resolve_worktree_path_custom_name(self, mock_git, mock_project):
        """Test path resolution with custom name."""
        mock_git.return_value = ("/home/user/project", True)

        config = DEFAULT_CONFIG
        path = resolve_worktree_path("feat/new-feature", config, name="custom-name")

        self.assertIn("custom-name", str(path))

    @patch("worktree_operations.get_project_name", return_value="test-project")
    @patch("worktree_operations.run_git_command")
    def test_resolve_worktree_path_slash_replacement(self, mock_git, mock_project):
        """Test that slashes in branch names are replaced."""
        mock_git.return_value = ("/home/user/project", True)

        config = DEFAULT_CONFIG
        path = resolve_worktree_path("feat/new/feature", config)

        # Should replace / with -
        self.assertIn("dev-feat-new-feature", str(path))


class TestOperationList(unittest.TestCase):
    """Test list operation."""

    @patch("worktree_operations.run_git_command")
    def test_list_empty(self, mock_git):
        """Test listing with no worktrees."""
        mock_git.return_value = ("", True)

        result = operation_list(json_output=True)

        self.assertTrue(result["success"])
        self.assertEqual(len(result["worktrees"]), 0)

    @patch("worktree_operations.run_git_command")
    def test_list_single_worktree(self, mock_git):
        """Test listing with one worktree."""
        mock_git.return_value = (
            "worktree /home/user/project\nHEAD abc123\nbranch refs/heads/main\n",
            True,
        )

        result = operation_list(json_output=True)

        self.assertTrue(result["success"])
        self.assertEqual(len(result["worktrees"]), 1)
        self.assertEqual(result["worktrees"][0]["branch"], "main")

    @patch("worktree_operations.run_git_command")
    def test_list_command_failure(self, mock_git):
        """Test list operation when git command fails."""
        mock_git.return_value = ("error", False)

        result = operation_list(json_output=True)

        self.assertFalse(result["success"])
        self.assertIn("error", result)


class TestOperationCreate(unittest.TestCase):
    """Test create operation."""

    def test_create_protected_branch(self):
        """Test creating worktree on protected branch."""
        result = operation_create("main")

        self.assertFalse(result["success"])
        self.assertIn("protected", result["error"].lower())

    @patch("worktree_operations.resolve_worktree_path")
    def test_create_existing_path(self, mock_resolve):
        """Test creating worktree when path already exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_resolve.return_value = Path(tmpdir)

            result = operation_create("test-branch")

            self.assertFalse(result["success"])
            self.assertIn("already exists", result["error"].lower())

    @patch("worktree_operations.save_status_json")
    @patch("worktree_operations.load_status_json")
    @patch("worktree_operations.enable_windows_longpaths")
    @patch("worktree_operations.run_git_command")
    @patch("worktree_operations.resolve_worktree_path")
    def test_create_success(
        self, mock_resolve, mock_git, mock_enable, mock_load, mock_save
    ):
        """Test successful worktree creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            worktree_path = Path(tmpdir) / "nonexistent"
            mock_resolve.return_value = worktree_path
            mock_git.return_value = ("Preparing worktree", True)
            mock_load.return_value = {}
            mock_save.return_value = True

            result = operation_create("test-branch", base="main")

            self.assertTrue(result["success"])
            self.assertIn("path", result)
            self.assertEqual(result["branch"], "test-branch")


class TestOperationRemove(unittest.TestCase):
    """Test remove operation."""

    @patch("worktree_operations.operation_list")
    def test_remove_nonexistent(self, mock_list):
        """Test removing nonexistent worktree."""
        mock_list.return_value = {"success": True, "worktrees": []}

        result = operation_remove("nonexistent")

        self.assertFalse(result["success"])
        self.assertIn("not found", result["error"].lower())

    @patch("worktree_operations.operation_list")
    def test_remove_with_uncommitted_changes(self, mock_list):
        """Test removing worktree with uncommitted changes."""
        mock_list.return_value = {
            "success": True,
            "worktrees": [
                {"path": "/test/path", "branch": "test", "uncommittedChanges": True}
            ],
        }

        result = operation_remove("test", force=False)

        self.assertFalse(result["success"])
        self.assertIn("uncommitted", result["error"].lower())

    @patch("worktree_operations.run_git_command")
    @patch("worktree_operations.operation_list")
    def test_remove_success(self, mock_list, mock_git):
        """Test successful worktree removal."""
        mock_list.return_value = {
            "success": True,
            "worktrees": [
                {"path": "/test/path", "branch": "test", "uncommittedChanges": False}
            ],
        }
        mock_git.return_value = ("", True)

        result = operation_remove("test")

        self.assertTrue(result["success"])
        self.assertIn("message", result)


class TestOperationSwitch(unittest.TestCase):
    """Test switch operation."""

    @patch("worktree_operations.operation_list")
    def test_switch_nonexistent(self, mock_list):
        """Test switching to nonexistent worktree."""
        mock_list.return_value = {"success": True, "worktrees": []}

        result = operation_switch("nonexistent")

        self.assertFalse(result["success"])

    @patch("worktree_operations.operation_list")
    def test_switch_success(self, mock_list):
        """Test successful switch."""
        mock_list.return_value = {
            "success": True,
            "worktrees": [{"path": "/test/path", "branch": "test"}],
        }

        result = operation_switch("test")

        self.assertTrue(result["success"])
        self.assertEqual(result["path"], "/test/path")


class TestOperationUpdateAll(unittest.TestCase):
    """Test update-all operation."""

    @patch("worktree_operations.operation_list")
    def test_update_all_empty(self, mock_list):
        """Test updating with no worktrees."""
        mock_list.return_value = {"success": True, "worktrees": []}

        result = operation_update_all()

        self.assertTrue(result["success"])
        self.assertEqual(result["totalWorktrees"], 0)
        self.assertEqual(result["successCount"], 0)

    @patch("worktree_operations.run_git_command")
    @patch("worktree_operations.operation_list")
    def test_update_all_success(self, mock_list, mock_git):
        """Test successful update of all worktrees."""
        mock_list.return_value = {
            "success": True,
            "worktrees": [{"path": "/test/path", "branch": "test"}],
        }
        mock_git.return_value = ("Already up to date", True)

        result = operation_update_all()

        self.assertTrue(result["success"])
        self.assertEqual(result["totalWorktrees"], 1)
        self.assertEqual(result["successCount"], 1)


class TestOperationPrune(unittest.TestCase):
    """Test prune operation."""

    @patch("worktree_operations.run_git_command")
    def test_prune_dry_run(self, mock_git):
        """Test prune with dry-run."""
        mock_git.return_value = ("worktree /test/path\nbranch refs/heads/test\n", True)

        result = operation_prune(dry_run=True)

        self.assertTrue(result["success"])
        self.assertTrue(result["dryRun"])
        self.assertIn("staleWorktrees", result)

    @patch("worktree_operations.run_git_command")
    def test_prune_actual(self, mock_git):
        """Test actual prune execution."""
        mock_git.return_value = ("", True)

        result = operation_prune(dry_run=False)

        self.assertTrue(result["success"])


class TestOperationInit(unittest.TestCase):
    """Test init operation."""

    @patch("worktree_operations.run_git_command")
    def test_init_no_matching_branches(self, mock_git):
        """Test init with no matching branches."""
        mock_git.return_value = ("", True)

        result = operation_init(pattern="nonexistent-*")

        self.assertTrue(result["success"])
        self.assertIn("message", result)

    @patch("worktree_operations.operation_create")
    @patch("worktree_operations.operation_list")
    @patch("worktree_operations.run_git_command")
    def test_init_with_branches(self, mock_git, mock_list, mock_create):
        """Test init with matching branches."""
        mock_git.return_value = ("  test-branch-1\n  test-branch-2", True)
        mock_list.return_value = {"success": True, "worktrees": []}
        mock_create.return_value = {"success": True}

        result = operation_init(pattern="test-*")

        self.assertTrue(result["success"])
        self.assertEqual(len(result["created"]), 2)

    @patch("worktree_operations.operation_list")
    @patch("worktree_operations.run_git_command")
    def test_init_skips_existing(self, mock_git, mock_list):
        """Test init skips branches with existing worktrees."""
        mock_git.return_value = ("  test-branch", True)
        mock_list.return_value = {
            "success": True,
            "worktrees": [{"branch": "test-branch"}],
        }

        result = operation_init(pattern="test-*")

        self.assertTrue(result["success"])
        self.assertEqual(len(result["skipped"]), 1)
        self.assertEqual(len(result["created"]), 0)


class TestOperationAnalyze(unittest.TestCase):
    """Test analyze operation."""

    @patch("worktree_operations.operation_list")
    def test_analyze_empty(self, mock_list):
        """Test analyze with no worktrees."""
        mock_list.return_value = {"success": True, "worktrees": []}

        result = operation_analyze()

        self.assertTrue(result["success"])
        self.assertEqual(len(result["recommendations"]), 0)

    @patch("worktree_operations.run_git_command")
    @patch("worktree_operations.operation_list")
    def test_analyze_behind_base(self, mock_list, mock_git):
        """Test analyze detects worktree behind base."""
        mock_list.return_value = {
            "success": True,
            "worktrees": [{"path": "/test/path", "branch": "test"}],
        }
        mock_git.return_value = ("5", True)

        result = operation_analyze()

        self.assertTrue(result["success"])
        self.assertGreater(len(result["recommendations"]), 0)
        self.assertEqual(result["recommendations"][0]["id"], "sync_worktree")


class TestCrossPlatformCompatibility(unittest.TestCase):
    """Test cross-platform compatibility features."""

    @patch("sys.platform", "win32")
    @patch("worktree_operations.run_git_command")
    def test_enable_windows_longpaths(self, mock_git):
        """Test Windows long path enabling."""
        mock_git.return_value = ("", True)

        result = enable_windows_longpaths()

        self.assertTrue(result)
        mock_git.assert_called_with("config core.longpaths true")

    @patch("sys.platform", "linux")
    def test_enable_windows_longpaths_on_linux(self):
        """Test Windows long path enabling on non-Windows."""
        result = enable_windows_longpaths()

        self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()
