#!/usr/bin/env python3
"""Test script for git_utils.py"""

import sys
import os
import io

# Fix Windows console encoding for Unicode characters
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add packages to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'packages', 'popkit-dev', 'hooks'))

from git_utils import (
    is_git_repo,
    git_fetch_prune,
    find_stale_local_branches,
    format_stale_branches_report,
    count_stale_branches
)


def main():
    print("=" * 70)
    print("Git Fetch --Prune Test Suite")
    print("=" * 70)
    print()

    # Test 1: Check if in git repo
    print("1. Testing is_git_repo()...")
    if is_git_repo():
        print("   ✓ Current directory is a git repository")
    else:
        print("   ✗ Not a git repository")
        return 1
    print()

    # Test 2: Git fetch prune
    print("2. Testing git_fetch_prune()...")
    success, message = git_fetch_prune()
    print(f"   {message}")
    print()

    # Test 3: Find stale branches
    print("3. Testing find_stale_local_branches()...")
    stale_branches = find_stale_local_branches()
    print(f"   Found {len(stale_branches)} stale branches")
    print()

    # Test 4: Format report
    print("4. Testing format_stale_branches_report()...")
    report = format_stale_branches_report(stale_branches)
    print(report)
    print()

    # Test 5: Count stale branches
    print("5. Testing count_stale_branches()...")
    count = count_stale_branches()
    print(f"   Stale branch count: {count}")
    print()

    print("=" * 70)
    print("Test completed successfully!")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    sys.exit(main())
