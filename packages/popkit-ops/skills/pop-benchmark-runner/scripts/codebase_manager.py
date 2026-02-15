#!/usr/bin/env python3
"""
Codebase Manager - Git worktree isolation for benchmark execution.

Manages creation, configuration, and cleanup of git worktrees for benchmark trials.
"""

import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple


class WorktreeExistsError(Exception):
    """Raised when worktree already exists."""

    pass


class GitError(Exception):
    """Raised when git operation fails."""

    pass


class CodebaseManager:
    """Manages git worktrees for benchmark isolation."""

    def __init__(self, base_dir: Optional[Path] = None):
        """
        Initialize codebase manager.

        Args:
            base_dir: Base directory for worktrees (default: benchmark-worktrees/)
        """
        self.base_dir = base_dir or Path("benchmark-worktrees")
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def create_worktree(
        self,
        task_id: str,
        trial_num: int,
        baseline_ref: str = "HEAD",
        branch_name: Optional[str] = None,
    ) -> Path:
        """
        Create a fresh git worktree for benchmark trial.

        Args:
            task_id: Task identifier (e.g., "jwt-authentication")
            trial_num: Trial number (1-based)
            baseline_ref: Git ref to checkout (default: HEAD)
            branch_name: Optional branch name (default: auto-generated)

        Returns:
            Path to created worktree

        Raises:
            WorktreeExistsError: If worktree already exists
            GitError: If git operation fails
        """
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        worktree_name = f"{task_id}-trial{trial_num}-{timestamp}"
        worktree_path = self.base_dir / worktree_name

        if worktree_path.exists():
            raise WorktreeExistsError(f"Worktree already exists: {worktree_path}")

        # Generate branch name if not provided
        if not branch_name:
            branch_name = f"benchmark/{task_id}/trial{trial_num}/{timestamp}"

        # Create worktree
        cmd = [
            "git",
            "worktree",
            "add",
            "-b",
            branch_name,
            str(worktree_path),
            baseline_ref,
        ]
        returncode, stdout, stderr = self._run_git_command(cmd)

        if returncode != 0:
            raise GitError(f"Failed to create worktree: {stderr}")

        print(f"[INFO] Created worktree: {worktree_path}")
        print(f"[INFO] Branch: {branch_name}")
        print(f"[INFO] Baseline: {baseline_ref}")

        return worktree_path

    def checkout_baseline(self, worktree_path: Path, ref: str) -> None:
        """
        Checkout specific git ref in worktree.

        Args:
            worktree_path: Path to worktree
            ref: Git ref to checkout (commit hash, tag, branch)

        Raises:
            GitError: If checkout fails
        """
        cmd = ["git", "-C", str(worktree_path), "checkout", ref]
        returncode, stdout, stderr = self._run_git_command(cmd)

        if returncode != 0:
            raise GitError(f"Failed to checkout {ref}: {stderr}")

        print(f"[INFO] Checked out {ref} in {worktree_path.name}")
        return

    def cleanup_worktree(self, worktree_path: Path, force: bool = False) -> None:
        """
        Remove worktree and delete branch.

        Args:
            worktree_path: Path to worktree
            force: Force removal even with uncommitted changes

        Raises:
            GitError: If removal fails
        """
        if not worktree_path.exists():
            print(f"[WARN] Worktree does not exist: {worktree_path}")
            return

        # Get branch name before removing worktree
        branch_name = self._get_worktree_branch(worktree_path)

        # Remove worktree
        force_flag = ["--force"] if force else []
        cmd = ["git", "worktree", "remove"] + force_flag + [str(worktree_path)]
        returncode, stdout, stderr = self._run_git_command(cmd)

        if returncode != 0:
            if not force:
                # Retry with force
                print("[WARN] Failed to remove worktree, retrying with --force")
                self.cleanup_worktree(worktree_path, force=True)
                return
            raise GitError(f"Failed to remove worktree: {stderr}")

        # Delete branch if it exists
        if branch_name:
            self._delete_branch(branch_name)

        print(f"[INFO] Cleaned up worktree: {worktree_path.name}")

    def cleanup_all_worktrees(self, task_id: Optional[str] = None) -> None:
        """
        Remove all benchmark worktrees.

        Args:
            task_id: Optional task ID to filter worktrees (default: all)
        """
        if not self.base_dir.exists():
            return

        for worktree_dir in self.base_dir.iterdir():
            if not worktree_dir.is_dir():
                continue
            if task_id and not worktree_dir.name.startswith(task_id):
                continue

            try:
                self.cleanup_worktree(worktree_dir, force=True)
            except GitError as e:
                print(f"[ERROR] Failed to cleanup {worktree_dir.name}: {e}")

    def list_worktrees(self, task_id: Optional[str] = None) -> List[Path]:
        """
        List all benchmark worktrees.

        Args:
            task_id: Optional task ID to filter worktrees

        Returns:
            List of worktree paths
        """
        if not self.base_dir.exists():
            return []

        worktrees = []
        for worktree_dir in self.base_dir.iterdir():
            if not worktree_dir.is_dir():
                continue
            if task_id and not worktree_dir.name.startswith(task_id):
                continue
            worktrees.append(worktree_dir)

        return sorted(worktrees)

    def verify_clean_state(self, worktree_path: Path) -> bool:
        """
        Verify worktree has no uncommitted changes.

        Args:
            worktree_path: Path to worktree

        Returns:
            True if clean, False if dirty
        """
        cmd = ["git", "-C", str(worktree_path), "status", "--porcelain"]
        returncode, stdout, stderr = self._run_git_command(cmd)

        if returncode != 0:
            raise GitError(f"Failed to check status: {stderr}")

        is_clean = len(stdout.strip()) == 0
        if not is_clean:
            print(f"[WARN] Worktree has uncommitted changes: {worktree_path.name}")

        return is_clean

    def _get_worktree_branch(self, worktree_path: Path) -> Optional[str]:
        """Get branch name for worktree."""
        cmd = ["git", "-C", str(worktree_path), "rev-parse", "--abbrev-ref", "HEAD"]
        returncode, stdout, stderr = self._run_git_command(cmd)

        if returncode != 0:
            return None

        branch_name = stdout.strip()
        return branch_name if branch_name != "HEAD" else None

    def _delete_branch(self, branch_name: str) -> None:
        """Delete git branch (force delete)."""
        cmd = ["git", "branch", "-D", branch_name]
        returncode, stdout, stderr = self._run_git_command(cmd)

        if returncode != 0:
            print(f"[WARN] Failed to delete branch {branch_name}: {stderr}")
        else:
            print(f"[INFO] Deleted branch: {branch_name}")

    def _run_git_command(self, cmd: List[str]) -> Tuple[int, str, str]:
        """
        Run git command and return result.

        Args:
            cmd: Command as list of strings

        Returns:
            Tuple of (returncode, stdout, stderr)
        """
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timed out after 60 seconds"
        except Exception as e:
            return 1, "", str(e)


def main():
    """Test codebase manager functionality."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python codebase_manager.py <command> [args]")
        print("Commands:")
        print("  create <task-id> <trial-num> [baseline-ref]")
        print("  cleanup <task-id> <trial-num>")
        print("  cleanup-all [task-id]")
        print("  list [task-id]")
        sys.exit(1)

    manager = CodebaseManager()
    command = sys.argv[1]

    try:
        if command == "create":
            task_id = sys.argv[2]
            trial_num = int(sys.argv[3])
            baseline_ref = sys.argv[4] if len(sys.argv) > 4 else "HEAD"
            worktree_path = manager.create_worktree(task_id, trial_num, baseline_ref)
            print(f"Created: {worktree_path}")

        elif command == "cleanup":
            task_id = sys.argv[2]
            trial_num = int(sys.argv[3])
            timestamp = "*"  # Match any timestamp
            pattern = f"{task_id}-trial{trial_num}-{timestamp}"
            worktrees = manager.list_worktrees(task_id)
            matching = [w for w in worktrees if f"trial{trial_num}" in w.name]
            if matching:
                manager.cleanup_worktree(matching[0])
            else:
                print(f"No worktree found matching: {pattern}")

        elif command == "cleanup-all":
            task_id = sys.argv[2] if len(sys.argv) > 2 else None
            manager.cleanup_all_worktrees(task_id)
            print("Cleanup complete")

        elif command == "list":
            task_id = sys.argv[2] if len(sys.argv) > 2 else None
            worktrees = manager.list_worktrees(task_id)
            if worktrees:
                print(f"Found {len(worktrees)} worktree(s):")
                for w in worktrees:
                    print(f"  {w.name}")
            else:
                print("No worktrees found")

        else:
            print(f"Unknown command: {command}")
            sys.exit(1)

    except (WorktreeExistsError, GitError) as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
