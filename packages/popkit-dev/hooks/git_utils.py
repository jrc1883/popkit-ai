#!/usr/bin/env python3
"""
Git utilities for PopKit routines.
Provides git fetch --prune functionality and stale branch detection.
"""

import subprocess
from typing import List, Optional, Tuple


def run_git_command(cmd: List[str], cwd: Optional[str] = None) -> Tuple[int, str, str]:
    """Run a git command and return exit code, stdout, stderr."""
    try:
        result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=30)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Git command timed out after 30 seconds"
    except Exception as e:
        return 1, "", str(e)


def git_fetch_prune(remote: str = "origin") -> Tuple[bool, str]:
    """
    Run git fetch --prune to remove stale remote tracking branches.

    Args:
        remote: Remote name to fetch from (default: "origin")

    Returns:
        Tuple of (success: bool, message: str)
    """
    exit_code, stdout, stderr = run_git_command(["git", "fetch", "--prune", remote])

    if exit_code == 0:
        output = stdout + stderr
        if "pruned" in output.lower() or "[deleted]" in output:
            return True, f"✓ Pruned stale remote tracking branches from {remote}"
        else:
            return True, f"✓ Remote {remote} up to date (no stale branches)"
    else:
        return False, f"✗ Failed to prune {remote}: {stderr.strip()}"


def find_stale_local_branches() -> List[Tuple[str, str]]:
    """
    Find local branches whose remote tracking branches have been deleted.

    Returns:
        List of tuples: (branch_name, tracking_info)
    """
    exit_code, stdout, stderr = run_git_command(["git", "branch", "-vv"])

    if exit_code != 0:
        return []

    stale_branches = []
    for line in stdout.splitlines():
        if ": gone]" in line:
            parts = line.strip().split()
            if not parts:
                continue

            branch_name = parts[1] if parts[0] == "*" else parts[0]
            stale_branches.append((branch_name, line.strip()))

    return stale_branches


def format_stale_branches_report(
    stale_branches: List[Tuple[str, str]], max_display: int = 5
) -> str:
    """Format stale branches into a human-readable report."""
    if not stale_branches:
        return "✓ No stale local branches found"

    count = len(stale_branches)
    lines = [f"⚠️  Found {count} stale local branch{'es' if count != 1 else ''} (remote deleted):"]

    for branch_name, _ in stale_branches[:max_display]:
        lines.append(f"   - {branch_name}")

    if count > max_display:
        lines.append(f"   ... and {count - max_display} more")

    lines.append("")
    lines.append("💡 Suggestion: Review and delete with 'git branch -d <branch>'")

    return "\n".join(lines)


def count_stale_branches() -> int:
    """Quick count of stale branches for scoring."""
    return len(find_stale_local_branches())


def is_git_repo() -> bool:
    """Check if current directory is a git repository."""
    exit_code, _, _ = run_git_command(["git", "rev-parse", "--git-dir"])
    return exit_code == 0
