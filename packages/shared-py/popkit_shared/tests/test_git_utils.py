#!/usr/bin/env python3
"""Test suite for git_utils.py from popkit-dev hooks."""

import sys
import io
import unittest
from pathlib import Path

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add popkit-dev hooks to path
hooks_path = Path(__file__).parents[3] / 'popkit-dev' / 'hooks'
sys.path.insert(0, str(hooks_path))

from git_utils import (
    is_git_repo,
    git_fetch_prune,
    find_stale_local_branches,
    format_stale_branches_report,
    count_stale_branches
)


class TestGitUtils(unittest.TestCase):
    """Test suite for git utility functions."""

    def test_is_git_repo(self):
        """Test git repository detection."""
        # We should be running from within a git repo
        self.assertTrue(is_git_repo(), "Should detect that we're in a git repository")

    def test_git_fetch_prune(self):
        """Test git fetch --prune functionality."""
        success, message = git_fetch_prune()

        # Should succeed (either pruned or already up to date)
        self.assertTrue(success, f"git fetch --prune should succeed: {message}")

        # Message should indicate success
        self.assertIn('✓', message, "Success message should contain checkmark")

        # Should mention 'origin' remote
        self.assertIn('origin', message.lower(), "Message should reference origin remote")

    def test_find_stale_local_branches(self):
        """Test finding stale local branches."""
        stale_branches = find_stale_local_branches()

        # Should return a list (may be empty)
        self.assertIsInstance(stale_branches, list)

        # Each item should be a tuple with (branch_name, tracking_info)
        for item in stale_branches:
            self.assertIsInstance(item, tuple)
            self.assertEqual(len(item), 2)
            branch_name, tracking_info = item
            self.assertIsInstance(branch_name, str)
            self.assertIsInstance(tracking_info, str)
            # Tracking info should indicate "gone"
            self.assertIn('gone', tracking_info.lower())

    def test_format_stale_branches_report(self):
        """Test report formatting for stale branches."""
        # Test with no stale branches
        report = format_stale_branches_report([])
        self.assertIn('No stale local branches', report)
        self.assertIn('✓', report)

        # Test with sample stale branches
        sample_branches = [
            ('feat/old-feature', '  feat/old-feature abc1234 [origin/feat/old-feature: gone] commit message'),
            ('fix/bug-123', '  fix/bug-123 def5678 [origin/fix/bug-123: gone] fix bug'),
        ]
        report = format_stale_branches_report(sample_branches)

        # Should show count
        self.assertIn('2', report)
        self.assertIn('stale', report.lower())

        # Should list branch names
        self.assertIn('feat/old-feature', report)
        self.assertIn('fix/bug-123', report)

        # Should include suggestion
        self.assertIn('git branch -d', report)

        # Test with many branches (should truncate display)
        many_branches = [(f'branch-{i}', f'  branch-{i} hash [origin/branch-{i}: gone] msg') for i in range(10)]
        report = format_stale_branches_report(many_branches, max_display=5)

        # Should show count
        self.assertIn('10', report)

        # Should indicate more branches
        self.assertIn('more', report.lower())

    def test_count_stale_branches(self):
        """Test counting stale branches."""
        count = count_stale_branches()

        # Should return a non-negative integer
        self.assertIsInstance(count, int)
        self.assertGreaterEqual(count, 0)


class TestGitUtilsIntegration(unittest.TestCase):
    """Integration tests for git utils workflow."""

    def test_full_workflow(self):
        """Test complete workflow: fetch prune -> find stale -> format report."""
        # Step 1: Run git fetch --prune
        success, message = git_fetch_prune()
        self.assertTrue(success, f"Fetch prune should succeed: {message}")

        # Step 2: Find stale branches
        stale_branches = find_stale_local_branches()
        self.assertIsInstance(stale_branches, list)

        # Step 3: Format report
        report = format_stale_branches_report(stale_branches)
        self.assertIsInstance(report, str)
        self.assertGreater(len(report), 0)

        # Step 4: Count stale branches
        count = count_stale_branches()
        self.assertEqual(count, len(stale_branches), "Count should match list length")


def print_test_report():
    """Print detailed test report."""
    print("=" * 70)
    print("Git Utilities Test Suite")
    print("=" * 70)
    print()

    # Run git fetch prune
    print("1. Testing git_fetch_prune()...")
    success, message = git_fetch_prune()
    print(f"   {message}")
    print()

    # Find stale branches
    print("2. Testing find_stale_local_branches()...")
    stale_branches = find_stale_local_branches()
    print(f"   Found {len(stale_branches)} stale branches")
    print()

    # Format report
    print("3. Testing format_stale_branches_report()...")
    report = format_stale_branches_report(stale_branches)
    print(report)
    print()

    # Count stale branches
    print("4. Testing count_stale_branches()...")
    count = count_stale_branches()
    print(f"   Stale branch count: {count}")
    print()

    print("=" * 70)
    print("Running unit tests...")
    print("=" * 70)
    print()


if __name__ == "__main__":
    # Check if running as a manual test or unittest
    if len(sys.argv) > 1 and sys.argv[1] == '--report':
        print_test_report()
    else:
        # Run as unittest
        unittest.main()
