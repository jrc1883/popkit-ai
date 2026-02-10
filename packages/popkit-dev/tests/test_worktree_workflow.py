#!/usr/bin/env python3
"""
Integration Tests for Git Worktree Workflow.

Tests complete workflows end-to-end in a real git repository.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parents[1] / "skills" / "pop-worktree-manager" / "scripts"))

from worktree_operations import (
    operation_analyze,
    operation_create,
    operation_list,
    operation_remove,
    operation_switch,
)


class TestWorktreeWorkflow(unittest.TestCase):
    """Integration tests for complete worktree workflows."""

    def setUp(self):
        """Create a temporary git repository for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = Path.cwd()

        # Initialize git repository
        subprocess.run(["git", "init"], cwd=self.test_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.test_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=self.test_dir,
            check=True,
            capture_output=True,
        )

        # Create initial commit
        readme = Path(self.test_dir) / "README.md"
        readme.write_text("# Test Project\n")
        subprocess.run(
            ["git", "add", "README.md"],
            cwd=self.test_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=self.test_dir,
            check=True,
            capture_output=True,
        )

        # Rename branch to 'main' for consistent testing across git versions
        subprocess.run(
            ["git", "branch", "-M", "main"],
            cwd=self.test_dir,
            check=True,
            capture_output=True,
        )

        # Create .popkit directory for config
        popkit_dir = Path(self.test_dir) / ".popkit"
        popkit_dir.mkdir()

        # Change to test directory
        import os

        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        import os
        import shutil

        os.chdir(self.original_cwd)

        try:
            # Remove any worktrees first
            result = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                cwd=self.test_dir,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                worktrees = []
                current_path = None

                for line in result.stdout.split("\n"):
                    if line.startswith("worktree "):
                        current_path = line[9:]
                        worktrees.append(current_path)

                # Remove non-main worktrees
                for wt_path in worktrees:
                    if wt_path != self.test_dir:
                        subprocess.run(
                            ["git", "worktree", "remove", wt_path, "--force"],
                            cwd=self.test_dir,
                            capture_output=True,
                        )

            shutil.rmtree(self.test_dir)
        except Exception as exc:
            import sys

            print(f"tearDown cleanup failed: {exc}", file=sys.stderr)

    def test_full_workflow_create_switch_remove(self):
        """Test: create worktree → switch → remove."""
        # Create worktree
        create_result = operation_create("feature-test", base="main", name="test-worktree")
        self.assertTrue(create_result["success"], f"Create failed: {create_result}")
        self.assertIn("path", create_result)

        worktree_path = Path(create_result["path"])
        self.assertTrue(worktree_path.exists())

        # List worktrees
        list_result = operation_list(json_output=True)
        self.assertTrue(list_result["success"])
        self.assertEqual(len(list_result["worktrees"]), 2)  # main + feature-test

        # Switch to worktree
        switch_result = operation_switch("feature-test")
        self.assertTrue(switch_result["success"], f"Switch failed: {switch_result}")
        self.assertEqual(switch_result["path"], str(worktree_path.as_posix()))

        # Remove worktree
        remove_result = operation_remove("feature-test")
        self.assertTrue(remove_result["success"], f"Remove failed: {remove_result}")

        # Verify removal
        self.assertFalse(worktree_path.exists())

    def test_workflow_multiple_worktrees(self):
        """Test: work with multiple worktrees simultaneously."""
        # Create multiple worktrees
        wt1 = operation_create("feature-1", base="main", name="wt1")
        wt2 = operation_create("feature-2", base="main", name="wt2")

        self.assertTrue(wt1["success"])
        self.assertTrue(wt2["success"])

        # List should show all 3 (main + 2 features)
        list_result = operation_list(json_output=True)
        self.assertTrue(list_result["success"])
        self.assertEqual(len(list_result["worktrees"]), 3)

        # Verify branches
        branches = {wt["branch"] for wt in list_result["worktrees"]}
        self.assertIn("main", branches)
        self.assertIn("feature-1", branches)
        self.assertIn("feature-2", branches)

        # Clean up
        operation_remove("feature-1")
        operation_remove("feature-2")

    def test_workflow_protected_branch_safety(self):
        """Test: protected branch safety checks."""
        # Try to create worktree on main (protected)
        result = operation_create("main")

        self.assertFalse(result["success"])
        self.assertIn("protected", result["error"].lower())

    def test_workflow_uncommitted_changes_protection(self):
        """Test: uncommitted changes safety check."""
        # Create worktree
        create_result = operation_create("feature-test", base="main", name="test-worktree")
        self.assertTrue(create_result["success"])

        worktree_path = Path(create_result["path"])

        # Create uncommitted changes
        test_file = worktree_path / "test.txt"
        test_file.write_text("test content")

        # Try to remove without force
        remove_result = operation_remove("feature-test", force=False)

        # Should fail due to uncommitted changes
        self.assertFalse(remove_result["success"])
        self.assertIn("uncommitted", remove_result["error"].lower())

        # Force remove should work
        force_remove_result = operation_remove("feature-test", force=True)
        self.assertTrue(force_remove_result["success"])

    def test_workflow_analyze_recommendations(self):
        """Test: analyze provides relevant recommendations."""
        # Create worktree
        create_result = operation_create("feature-test", base="main", name="test-worktree")
        self.assertTrue(create_result["success"])

        worktree_path = Path(create_result["path"])

        # Create uncommitted changes
        test_file = worktree_path / "test.txt"
        test_file.write_text("test content")

        # Analyze should detect uncommitted changes
        analyze_result = operation_analyze()

        self.assertTrue(analyze_result["success"])
        self.assertGreater(len(analyze_result["recommendations"]), 0)

        # Should recommend committing changes
        recommendations = analyze_result["recommendations"]
        commit_rec = next((r for r in recommendations if r["id"] == "commit_changes"), None)
        self.assertIsNotNone(commit_rec, "Should recommend committing changes")

        # Clean up
        operation_remove("feature-test", force=True)


class TestStatusJsonIntegration(unittest.TestCase):
    """Test STATUS.json integration."""

    def setUp(self):
        """Create a temporary git repository for testing."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = Path.cwd()

        # Initialize git repository
        subprocess.run(["git", "init"], cwd=self.test_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.test_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=self.test_dir,
            check=True,
            capture_output=True,
        )

        # Create initial commit
        readme = Path(self.test_dir) / "README.md"
        readme.write_text("# Test Project\n")
        subprocess.run(
            ["git", "add", "README.md"],
            cwd=self.test_dir,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=self.test_dir,
            check=True,
            capture_output=True,
        )

        # Rename branch to 'main' for consistent testing across git versions
        subprocess.run(
            ["git", "branch", "-M", "main"],
            cwd=self.test_dir,
            check=True,
            capture_output=True,
        )

        # Create .popkit directory
        popkit_dir = Path(self.test_dir) / ".popkit"
        popkit_dir.mkdir()

        # Change to test directory
        import os

        os.chdir(self.test_dir)

    def tearDown(self):
        """Clean up temporary directory."""
        import os
        import shutil

        os.chdir(self.original_cwd)

        try:
            # Remove any worktrees first
            result = subprocess.run(
                ["git", "worktree", "list", "--porcelain"],
                cwd=self.test_dir,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                worktrees = []
                current_path = None

                for line in result.stdout.split("\n"):
                    if line.startswith("worktree "):
                        current_path = line[9:]
                        worktrees.append(current_path)

                # Remove non-main worktrees
                for wt_path in worktrees:
                    if wt_path != self.test_dir:
                        subprocess.run(
                            ["git", "worktree", "remove", wt_path, "--force"],
                            cwd=self.test_dir,
                            capture_output=True,
                        )

            shutil.rmtree(self.test_dir)
        except Exception as exc:
            import sys

            print(f"tearDown cleanup failed: {exc}", file=sys.stderr)

    def test_status_json_created_on_worktree_creation(self):
        """Test: STATUS.json is created/updated when worktree is created."""
        # Create worktree
        create_result = operation_create("feature-test", base="main", name="test-worktree")
        self.assertTrue(create_result["success"])

        # Check STATUS.json exists
        status_file = Path.cwd() / ".popkit" / "STATUS.json"
        self.assertTrue(status_file.exists(), "STATUS.json should be created")

        # Check STATUS.json content
        status_data = json.loads(status_file.read_text())

        self.assertIn("git", status_data)
        self.assertIn("worktree", status_data["git"])

        worktree_info = status_data["git"]["worktree"]
        self.assertTrue(worktree_info["isWorktree"])
        self.assertEqual(worktree_info["name"], "test-worktree")
        self.assertEqual(worktree_info["baseRef"], "main")

        # Clean up
        operation_remove("feature-test")


if __name__ == "__main__":
    unittest.main()
