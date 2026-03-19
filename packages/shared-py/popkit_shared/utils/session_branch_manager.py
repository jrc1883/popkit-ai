#!/usr/bin/env python3
"""
Session Branch Manager - DAG-based session branching for side investigations.

Allows users to branch off from the main session to investigate something
without polluting the main context. Inspired by Pi's session architecture.

Issue #313: Session branching for side-quest investigations

Usage:
    from popkit_shared.utils.session_branch_manager import (
        create_branch,
        switch_branch,
        merge_branch,
        get_current_branch,
        list_branches,
    )

    # Create a new branch for investigation
    create_branch("auth-bug", reason="Investigating token expiry issue")

    # Switch between branches
    switch_branch("main")

    # Merge findings back
    merge_branch("auth-bug", outcome="Fixed: tokens now refresh correctly")
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _get_status_path() -> Path:
    """Get the path to STATUS.json."""
    # Check .claude directory first
    claude_dir = Path.cwd() / ".claude"
    if claude_dir.exists():
        return claude_dir / "STATUS.json"

    # Fall back to project root
    return Path.cwd() / "STATUS.json"


def _load_status() -> Dict[str, Any]:
    """Load STATUS.json, initializing branch structure if needed."""
    status_path = _get_status_path()

    if status_path.exists():
        try:
            status = json.loads(status_path.read_text())
        except json.JSONDecodeError:
            status = {}
    else:
        status = {}

    # Initialize branch structure if not present
    if "branches" not in status:
        status["branches"] = {
            "main": {
                "id": "main",
                "parent": None,
                "created": datetime.now(timezone.utc).isoformat(),
                "reason": "Main development branch",
                "context": status.get("context", {}),
                "tasks": status.get("tasks", {}),
                "git": status.get("git", {}),
            }
        }
        status["currentBranch"] = "main"
        status["branchHistory"] = []

    return status


def _save_status(status: Dict[str, Any]) -> None:
    """Save STATUS.json."""
    status_path = _get_status_path()
    status_path.parent.mkdir(parents=True, exist_ok=True)
    status_path.write_text(json.dumps(status, indent=2))


def get_current_branch() -> Tuple[str, Dict[str, Any]]:
    """Get the current branch ID and its data.

    Returns:
        Tuple of (branch_id, branch_data)
    """
    status = _load_status()
    branch_id = status.get("currentBranch", "main")
    branch_data = status.get("branches", {}).get(branch_id, {})
    return branch_id, branch_data


def list_branches() -> List[Dict[str, Any]]:
    """List all branches with their metadata.

    Returns:
        List of branch dictionaries with id, parent, created, reason, and active status
    """
    status = _load_status()
    current = status.get("currentBranch", "main")
    branches = status.get("branches", {})

    result = []
    for branch_id, branch_data in branches.items():
        result.append(
            {
                "id": branch_id,
                "parent": branch_data.get("parent"),
                "created": branch_data.get("created"),
                "reason": branch_data.get("reason", ""),
                "active": branch_id == current,
                "merged": branch_data.get("merged", False),
                "merged_at": branch_data.get("merged_at"),
            }
        )

    # Sort by created date, main first
    result.sort(key=lambda b: (b["id"] != "main", b.get("created", "")))
    return result


def create_branch(
    branch_id: str,
    reason: str,
    copy_context: bool = True,
) -> Dict[str, Any]:
    """Create a new branch for side investigation.

    Args:
        branch_id: Unique identifier for the branch (e.g., "auth-bug", "api-research")
        reason: Why this branch was created
        copy_context: Whether to copy current branch context to new branch

    Returns:
        The created branch data

    Raises:
        ValueError: If branch_id already exists
    """
    status = _load_status()
    branches = status.get("branches", {})
    current_id = status.get("currentBranch", "main")

    # Validate branch_id
    if branch_id in branches:
        raise ValueError(f"Branch '{branch_id}' already exists")

    if not branch_id or "/" in branch_id or " " in branch_id:
        raise ValueError("Branch ID must be non-empty and contain no spaces or slashes")

    # Get current branch data for copying
    current_branch = branches.get(current_id, {})

    # Create new branch
    new_branch = {
        "id": branch_id,
        "parent": current_id,
        "created": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
        "merged": False,
    }

    if copy_context:
        new_branch["context"] = current_branch.get("context", {}).copy()
        new_branch["tasks"] = {"inProgress": [], "completed": [], "blocked": []}
        new_branch["git"] = current_branch.get("git", {}).copy()
    else:
        new_branch["context"] = {}
        new_branch["tasks"] = {"inProgress": [], "completed": [], "blocked": []}
        new_branch["git"] = {}

    # Add to branches
    branches[branch_id] = new_branch
    status["branches"] = branches

    # Switch to new branch
    status["currentBranch"] = branch_id

    # Record in history
    history = status.get("branchHistory", [])
    history.append(
        {
            "action": "branch",
            "from": current_id,
            "to": branch_id,
            "reason": reason,
            "at": datetime.now(timezone.utc).isoformat(),
        }
    )
    status["branchHistory"] = history

    _save_status(status)

    return new_branch


def switch_branch(branch_id: str) -> Dict[str, Any]:
    """Switch to a different branch.

    Args:
        branch_id: The branch to switch to

    Returns:
        The branch data after switching

    Raises:
        ValueError: If branch doesn't exist
    """
    status = _load_status()
    branches = status.get("branches", {})
    current_id = status.get("currentBranch", "main")

    if branch_id not in branches:
        raise ValueError(f"Branch '{branch_id}' does not exist")

    if branch_id == current_id:
        return branches[branch_id]

    # Record in history
    history = status.get("branchHistory", [])
    history.append(
        {
            "action": "switch",
            "from": current_id,
            "to": branch_id,
            "at": datetime.now(timezone.utc).isoformat(),
        }
    )
    status["branchHistory"] = history

    # Switch
    status["currentBranch"] = branch_id

    _save_status(status)

    return branches[branch_id]


def merge_branch(
    branch_id: str,
    outcome: str,
    delete_after_merge: bool = False,
) -> Dict[str, Any]:
    """Merge a branch back to its parent.

    Args:
        branch_id: The branch to merge
        outcome: Description of what was learned/fixed
        delete_after_merge: Whether to delete the branch after merging

    Returns:
        The merge result with parent branch data

    Raises:
        ValueError: If branch doesn't exist or is main
    """
    status = _load_status()
    branches = status.get("branches", {})

    if branch_id not in branches:
        raise ValueError(f"Branch '{branch_id}' does not exist")

    if branch_id == "main":
        raise ValueError("Cannot merge main branch")

    branch = branches[branch_id]
    parent_id = branch.get("parent", "main")

    if parent_id not in branches:
        parent_id = "main"

    parent = branches[parent_id]

    # Mark branch as merged
    branch["merged"] = True
    branch["merged_at"] = datetime.now(timezone.utc).isoformat()
    branch["outcome"] = outcome

    # Copy key findings to parent context
    parent_context = parent.get("context", {})
    branch_context = branch.get("context", {})

    # Merge key decisions
    parent_decisions = parent_context.get("keyDecisions", [])
    branch_decisions = branch_context.get("keyDecisions", [])
    merged_decisions = parent_decisions + [
        f"[{branch_id}] {d}" for d in branch_decisions if d not in parent_decisions
    ]
    parent_context["keyDecisions"] = merged_decisions

    # Add outcome to parent context
    if outcome:
        parent_context["recentMerges"] = parent_context.get("recentMerges", [])
        parent_context["recentMerges"].append(
            {
                "branch": branch_id,
                "outcome": outcome,
                "at": datetime.now(timezone.utc).isoformat(),
            }
        )
        # Keep only last 5 merges
        parent_context["recentMerges"] = parent_context["recentMerges"][-5:]

    parent["context"] = parent_context
    branches[parent_id] = parent
    branches[branch_id] = branch

    # Record in history
    history = status.get("branchHistory", [])
    history.append(
        {
            "action": "merge",
            "from": branch_id,
            "to": parent_id,
            "outcome": outcome,
            "at": datetime.now(timezone.utc).isoformat(),
        }
    )
    status["branchHistory"] = history

    # Switch to parent
    status["currentBranch"] = parent_id

    # Optionally delete branch
    if delete_after_merge:
        del branches[branch_id]

    status["branches"] = branches
    _save_status(status)

    return {
        "merged": True,
        "from": branch_id,
        "to": parent_id,
        "outcome": outcome,
        "parent": parent,
    }


def delete_branch(branch_id: str, force: bool = False) -> bool:
    """Delete a branch.

    Args:
        branch_id: The branch to delete
        force: Delete even if not merged

    Returns:
        True if deleted

    Raises:
        ValueError: If branch is main, current, or not merged (without force)
    """
    status = _load_status()
    branches = status.get("branches", {})
    current_id = status.get("currentBranch", "main")

    if branch_id not in branches:
        raise ValueError(f"Branch '{branch_id}' does not exist")

    if branch_id == "main":
        raise ValueError("Cannot delete main branch")

    if branch_id == current_id:
        raise ValueError("Cannot delete current branch. Switch to another branch first.")

    branch = branches[branch_id]
    if not branch.get("merged", False) and not force:
        raise ValueError(f"Branch '{branch_id}' is not merged. Use force=True to delete anyway.")

    # Record in history
    history = status.get("branchHistory", [])
    history.append(
        {
            "action": "delete",
            "branch": branch_id,
            "forced": force and not branch.get("merged", False),
            "at": datetime.now(timezone.utc).isoformat(),
        }
    )
    status["branchHistory"] = history

    del branches[branch_id]
    status["branches"] = branches
    _save_status(status)

    return True


def get_branch_history(limit: int = 20) -> List[Dict[str, Any]]:
    """Get recent branch history.

    Args:
        limit: Maximum number of history entries to return

    Returns:
        List of history entries (most recent first)
    """
    status = _load_status()
    history = status.get("branchHistory", [])
    return list(reversed(history[-limit:]))


def update_branch_context(
    context_updates: Dict[str, Any],
    branch_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Update context for a branch.

    Args:
        context_updates: Context fields to update
        branch_id: Branch to update (defaults to current)

    Returns:
        Updated branch data
    """
    status = _load_status()
    branches = status.get("branches", {})

    if branch_id is None:
        branch_id = status.get("currentBranch", "main")

    if branch_id not in branches:
        raise ValueError(f"Branch '{branch_id}' does not exist")

    branch = branches[branch_id]
    context = branch.get("context", {})
    context.update(context_updates)
    branch["context"] = context
    branch["lastUpdated"] = datetime.now(timezone.utc).isoformat()

    branches[branch_id] = branch
    status["branches"] = branches
    _save_status(status)

    return branch


def update_branch_tasks(
    tasks_updates: Dict[str, List[str]],
    branch_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Update tasks for a branch.

    Args:
        tasks_updates: Tasks to update (inProgress, completed, blocked)
        branch_id: Branch to update (defaults to current)

    Returns:
        Updated branch data
    """
    status = _load_status()
    branches = status.get("branches", {})

    if branch_id is None:
        branch_id = status.get("currentBranch", "main")

    if branch_id not in branches:
        raise ValueError(f"Branch '{branch_id}' does not exist")

    branch = branches[branch_id]
    tasks = branch.get("tasks", {"inProgress": [], "completed": [], "blocked": []})
    tasks.update(tasks_updates)
    branch["tasks"] = tasks
    branch["lastUpdated"] = datetime.now(timezone.utc).isoformat()

    branches[branch_id] = branch
    status["branches"] = branches
    _save_status(status)

    return branch
