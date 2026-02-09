#!/usr/bin/env python3
"""
Test suite for codebase_manager.py

Tests git worktree operations for benchmark isolation.
"""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared-py"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from codebase_manager import CodebaseManager, GitError, WorktreeExistsError


class TestCodebaseManager(unittest.TestCase):
    """Test CodebaseManager functionality"""

    def setUp(self):
        """Set up test fixtures"""
        # Create temporary directory for tests
        self.temp_dir = Path(tempfile.mkdtemp())
        self.manager = CodebaseManager(base_dir=self.temp_dir / "test-worktrees")

    def tearDown(self):
        """Clean up test fixtures"""
        # Remove temporary directory
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    # =========================================================================
    # INITIALIZATION TESTS
    # =========================================================================

    def test_init_creates_base_directory(self):
        """Test that __init__ creates base directory"""
        self.assertTrue(self.manager.base_dir.exists())
        self.assertTrue(self.manager.base_dir.is_dir())

    def test_init_uses_default_directory(self):
        """Test default base directory name"""
        manager = CodebaseManager()
        self.assertEqual(manager.base_dir, Path("benchmark-worktrees"))

    def test_init_uses_custom_directory(self):
        """Test custom base directory"""
        custom_path = self.temp_dir / "custom-worktrees"
        manager = CodebaseManager(base_dir=custom_path)
        self.assertEqual(manager.base_dir, custom_path)
        self.assertTrue(custom_path.exists())

    # =========================================================================
    # CREATE WORKTREE TESTS
    # =========================================================================

    @patch.object(CodebaseManager, "_run_git_command")
    def test_create_worktree_success(self, mock_git):
        """Test successful worktree creation"""
        mock_git.return_value = (0, "Preparing worktree...", "")

        worktree_path = self.manager.create_worktree(
            task_id="test-task", trial_num=1, baseline_ref="main"
        )

        # Verify worktree path format
        self.assertIn("test-task-trial1", str(worktree_path))
        self.assertEqual(worktree_path.parent, self.manager.base_dir)

        # Verify git command called
        mock_git.assert_called_once()
        cmd = mock_git.call_args[0][0]
        self.assertEqual(cmd[0:3], ["git", "worktree", "add"])
        self.assertIn("-b", cmd)
        self.assertIn("main", cmd)

    @patch.object(CodebaseManager, "_run_git_command")
    def test_create_worktree_with_custom_branch(self, mock_git):
        """Test worktree creation with custom branch name"""
        mock_git.return_value = (0, "", "")

        self.manager.create_worktree(task_id="test-task", trial_num=1, branch_name="custom-branch")

        cmd = mock_git.call_args[0][0]
        self.assertIn("custom-branch", cmd)

    @patch.object(CodebaseManager, "_run_git_command")
    def test_create_worktree_failure(self, mock_git):
        """Test worktree creation failure"""
        mock_git.return_value = (1, "", "fatal: invalid reference")

        with self.assertRaises(GitError) as ctx:
            self.manager.create_worktree(task_id="test-task", trial_num=1)

        self.assertIn("Failed to create worktree", str(ctx.exception))

    def test_create_worktree_already_exists(self):
        """Test WorktreeExistsError when path already exists"""
        # Create directory to simulate existing worktree
        existing_path = self.manager.base_dir / "test-task-trial1-20260116-120000"
        existing_path.mkdir(parents=True)

        # Mock datetime to return fixed timestamp
        with patch("codebase_manager.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20260116-120000"

            with self.assertRaises(WorktreeExistsError):
                self.manager.create_worktree(task_id="test-task", trial_num=1)

    # =========================================================================
    # CHECKOUT BASELINE TESTS
    # =========================================================================

    @patch.object(CodebaseManager, "_run_git_command")
    def test_checkout_baseline_success(self, mock_git):
        """Test successful baseline checkout"""
        mock_git.return_value = (0, "HEAD is now at abc123", "")

        worktree_path = self.temp_dir / "test-worktree"
        worktree_path.mkdir()

        self.manager.checkout_baseline(worktree_path, "v1.0.0")

        # Verify git checkout command
        mock_git.assert_called_once()
        cmd = mock_git.call_args[0][0]
        self.assertEqual(cmd[0:2], ["git", "-C"])
        self.assertIn("checkout", cmd)
        self.assertIn("v1.0.0", cmd)

    @patch.object(CodebaseManager, "_run_git_command")
    def test_checkout_baseline_failure(self, mock_git):
        """Test checkout failure"""
        mock_git.return_value = (1, "", "error: pathspec 'invalid' did not match")

        worktree_path = self.temp_dir / "test-worktree"

        with self.assertRaises(GitError) as ctx:
            self.manager.checkout_baseline(worktree_path, "invalid")

        self.assertIn("Failed to checkout", str(ctx.exception))

    # =========================================================================
    # CLEANUP WORKTREE TESTS
    # =========================================================================

    @patch.object(CodebaseManager, "_run_git_command")
    @patch.object(CodebaseManager, "_get_worktree_branch")
    @patch.object(CodebaseManager, "_delete_branch")
    def test_cleanup_worktree_success(self, mock_delete, mock_get_branch, mock_git):
        """Test successful worktree cleanup"""
        worktree_path = self.temp_dir / "test-worktree"
        worktree_path.mkdir()

        mock_git.return_value = (0, "", "")
        mock_get_branch.return_value = "benchmark/test/trial1"

        self.manager.cleanup_worktree(worktree_path)

        # Verify git worktree remove called
        mock_git.assert_called_once()
        cmd = mock_git.call_args[0][0]
        self.assertEqual(cmd[0:3], ["git", "worktree", "remove"])

        # Verify branch deletion called
        mock_delete.assert_called_once_with("benchmark/test/trial1")

    @patch.object(CodebaseManager, "_run_git_command")
    @patch.object(CodebaseManager, "_get_worktree_branch")
    def test_cleanup_worktree_with_force(self, mock_get_branch, mock_git):
        """Test force cleanup when normal cleanup fails"""
        worktree_path = self.temp_dir / "test-worktree"
        worktree_path.mkdir()

        # First call fails, second succeeds (with force)
        mock_git.side_effect = [(1, "", "has modifications"), (0, "", "")]
        mock_get_branch.return_value = "test-branch"

        # Should auto-retry with force
        self.manager.cleanup_worktree(worktree_path, force=False)

        # Verify called twice (once without force, once with)
        self.assertEqual(mock_git.call_count, 2)
        second_call = mock_git.call_args_list[1][0][0]
        self.assertIn("--force", second_call)

    @patch.object(CodebaseManager, "_run_git_command")
    def test_cleanup_worktree_nonexistent(self, mock_git):
        """Test cleanup of non-existent worktree"""
        worktree_path = self.temp_dir / "nonexistent"

        # Should not raise error, just warn
        self.manager.cleanup_worktree(worktree_path)

        # Git command should not be called
        mock_git.assert_not_called()

    # =========================================================================
    # CLEANUP ALL WORKTREES TESTS
    # =========================================================================

    @patch.object(CodebaseManager, "cleanup_worktree")
    def test_cleanup_all_worktrees(self, mock_cleanup):
        """Test cleanup of all worktrees"""
        # Create test worktree directories
        (self.manager.base_dir / "task1-trial1-20260116").mkdir()
        (self.manager.base_dir / "task1-trial2-20260116").mkdir()
        (self.manager.base_dir / "task2-trial1-20260116").mkdir()

        self.manager.cleanup_all_worktrees()

        # Verify cleanup called for each worktree
        self.assertEqual(mock_cleanup.call_count, 3)

    @patch.object(CodebaseManager, "cleanup_worktree")
    def test_cleanup_all_worktrees_filtered(self, mock_cleanup):
        """Test cleanup filtered by task ID"""
        # Create test worktree directories
        (self.manager.base_dir / "task1-trial1-20260116").mkdir()
        (self.manager.base_dir / "task1-trial2-20260116").mkdir()
        (self.manager.base_dir / "task2-trial1-20260116").mkdir()

        self.manager.cleanup_all_worktrees(task_id="task1")

        # Verify cleanup called only for task1 worktrees
        self.assertEqual(mock_cleanup.call_count, 2)

    @patch.object(CodebaseManager, "cleanup_worktree")
    def test_cleanup_all_worktrees_handles_errors(self, mock_cleanup):
        """Test cleanup continues on error"""
        # Create test worktree directories
        (self.manager.base_dir / "task1-trial1-20260116").mkdir()
        (self.manager.base_dir / "task2-trial1-20260116").mkdir()

        # First cleanup fails, second succeeds
        mock_cleanup.side_effect = [GitError("Failed"), None]

        # Should not raise error, just continue
        self.manager.cleanup_all_worktrees()

        # Verify cleanup called for both
        self.assertEqual(mock_cleanup.call_count, 2)

    # =========================================================================
    # LIST WORKTREES TESTS
    # =========================================================================

    def test_list_worktrees_empty(self):
        """Test listing when no worktrees exist"""
        worktrees = self.manager.list_worktrees()
        self.assertEqual(worktrees, [])

    def test_list_worktrees_all(self):
        """Test listing all worktrees"""
        # Create test worktree directories
        (self.manager.base_dir / "task1-trial1-20260116").mkdir()
        (self.manager.base_dir / "task2-trial1-20260116").mkdir()

        worktrees = self.manager.list_worktrees()

        self.assertEqual(len(worktrees), 2)
        self.assertTrue(all(isinstance(w, Path) for w in worktrees))

    def test_list_worktrees_filtered(self):
        """Test listing filtered by task ID"""
        # Create test worktree directories
        (self.manager.base_dir / "task1-trial1-20260116").mkdir()
        (self.manager.base_dir / "task1-trial2-20260116").mkdir()
        (self.manager.base_dir / "task2-trial1-20260116").mkdir()

        worktrees = self.manager.list_worktrees(task_id="task1")

        self.assertEqual(len(worktrees), 2)
        self.assertTrue(all("task1" in w.name for w in worktrees))

    def test_list_worktrees_ignores_files(self):
        """Test that list_worktrees ignores files"""
        # Create worktree directory and file
        (self.manager.base_dir / "task1-trial1-20260116").mkdir()
        (self.manager.base_dir / "readme.txt").touch()

        worktrees = self.manager.list_worktrees()

        # Should only list directory, not file
        self.assertEqual(len(worktrees), 1)

    def test_list_worktrees_sorted(self):
        """Test that worktrees are sorted"""
        # Create worktrees in non-alphabetical order
        (self.manager.base_dir / "zzz-task").mkdir()
        (self.manager.base_dir / "aaa-task").mkdir()
        (self.manager.base_dir / "mmm-task").mkdir()

        worktrees = self.manager.list_worktrees()

        # Verify sorted order
        names = [w.name for w in worktrees]
        self.assertEqual(names, sorted(names))

    # =========================================================================
    # VERIFY CLEAN STATE TESTS
    # =========================================================================

    @patch.object(CodebaseManager, "_run_git_command")
    def test_verify_clean_state_clean(self, mock_git):
        """Test verify_clean_state with clean worktree"""
        mock_git.return_value = (0, "", "")  # Empty output = clean

        worktree_path = self.temp_dir / "test-worktree"
        is_clean = self.manager.verify_clean_state(worktree_path)

        self.assertTrue(is_clean)

        # Verify git status --porcelain called
        cmd = mock_git.call_args[0][0]
        self.assertIn("status", cmd)
        self.assertIn("--porcelain", cmd)

    @patch.object(CodebaseManager, "_run_git_command")
    def test_verify_clean_state_dirty(self, mock_git):
        """Test verify_clean_state with uncommitted changes"""
        mock_git.return_value = (0, " M file.txt\n", "")  # Modified file

        worktree_path = self.temp_dir / "test-worktree"
        is_clean = self.manager.verify_clean_state(worktree_path)

        self.assertFalse(is_clean)

    @patch.object(CodebaseManager, "_run_git_command")
    def test_verify_clean_state_failure(self, mock_git):
        """Test verify_clean_state when git command fails"""
        mock_git.return_value = (1, "", "fatal: not a git repository")

        worktree_path = self.temp_dir / "test-worktree"

        with self.assertRaises(GitError):
            self.manager.verify_clean_state(worktree_path)

    # =========================================================================
    # PRIVATE METHOD TESTS
    # =========================================================================

    @patch.object(CodebaseManager, "_run_git_command")
    def test_get_worktree_branch_success(self, mock_git):
        """Test _get_worktree_branch with valid branch"""
        mock_git.return_value = (0, "benchmark/test/trial1\n", "")

        worktree_path = self.temp_dir / "test-worktree"
        branch = self.manager._get_worktree_branch(worktree_path)

        self.assertEqual(branch, "benchmark/test/trial1")

    @patch.object(CodebaseManager, "_run_git_command")
    def test_get_worktree_branch_detached_head(self, mock_git):
        """Test _get_worktree_branch with detached HEAD"""
        mock_git.return_value = (0, "HEAD\n", "")

        worktree_path = self.temp_dir / "test-worktree"
        branch = self.manager._get_worktree_branch(worktree_path)

        self.assertIsNone(branch)

    @patch.object(CodebaseManager, "_run_git_command")
    def test_get_worktree_branch_failure(self, mock_git):
        """Test _get_worktree_branch when command fails"""
        mock_git.return_value = (1, "", "error")

        worktree_path = self.temp_dir / "test-worktree"
        branch = self.manager._get_worktree_branch(worktree_path)

        self.assertIsNone(branch)

    @patch.object(CodebaseManager, "_run_git_command")
    def test_delete_branch_success(self, mock_git):
        """Test _delete_branch success"""
        mock_git.return_value = (0, "Deleted branch test-branch", "")

        self.manager._delete_branch("test-branch")

        # Verify git branch -D called
        cmd = mock_git.call_args[0][0]
        self.assertEqual(cmd, ["git", "branch", "-D", "test-branch"])

    @patch.object(CodebaseManager, "_run_git_command")
    def test_delete_branch_failure(self, mock_git):
        """Test _delete_branch handles failure gracefully"""
        mock_git.return_value = (1, "", "error: branch not found")

        # Should not raise error, just warn
        self.manager._delete_branch("nonexistent-branch")

    @patch("codebase_manager.subprocess.run")
    def test_run_git_command_success(self, mock_run):
        """Test _run_git_command success"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "output"
        mock_result.stderr = ""
        mock_run.return_value = mock_result

        returncode, stdout, stderr = self.manager._run_git_command(["git", "status"])

        self.assertEqual(returncode, 0)
        self.assertEqual(stdout, "output")
        self.assertEqual(stderr, "")

        # Verify subprocess.run called with correct args
        mock_run.assert_called_once()
        call_kwargs = mock_run.call_args[1]
        self.assertTrue(call_kwargs["capture_output"])
        self.assertTrue(call_kwargs["text"])
        self.assertEqual(call_kwargs["timeout"], 60)

    @patch("codebase_manager.subprocess.run")
    def test_run_git_command_timeout(self, mock_run):
        """Test _run_git_command timeout"""
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["git"], timeout=60)

        returncode, stdout, stderr = self.manager._run_git_command(["git", "status"])

        self.assertEqual(returncode, 1)
        self.assertEqual(stdout, "")
        self.assertIn("timed out", stderr)

    @patch("codebase_manager.subprocess.run")
    def test_run_git_command_exception(self, mock_run):
        """Test _run_git_command handles exceptions"""
        mock_run.side_effect = Exception("Something went wrong")

        returncode, stdout, stderr = self.manager._run_git_command(["git", "status"])

        self.assertEqual(returncode, 1)
        self.assertEqual(stdout, "")
        self.assertIn("Something went wrong", stderr)


if __name__ == "__main__":
    unittest.main()
