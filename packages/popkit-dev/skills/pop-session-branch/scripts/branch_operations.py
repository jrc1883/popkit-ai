#!/usr/bin/env python3
"""
Branch Operations Script.

CLI interface for session branch management.

Usage:
    python branch_operations.py create <branch-id> <reason>
    python branch_operations.py switch <branch-id>
    python branch_operations.py merge <branch-id> <outcome>
    python branch_operations.py list
    python branch_operations.py delete <branch-id> [--force]
    python branch_operations.py current
    python branch_operations.py history [--limit N]

Issue #313: Session branching for side-quest investigations
"""

import argparse
import json
import sys
from typing import Any, Dict

from popkit_shared.utils.session_branch_manager import (
    create_branch,
    delete_branch,
    get_branch_history,
    get_current_branch,
    list_branches,
    merge_branch,
    switch_branch,
)


def cmd_create(args: argparse.Namespace) -> Dict[str, Any]:
    """Create a new branch."""
    try:
        branch = create_branch(
            branch_id=args.branch_id,
            reason=args.reason,
            copy_context=not args.no_copy,
        )
        return {
            "success": True,
            "action": "create",
            "branch": branch,
            "message": f"Created and switched to branch '{args.branch_id}'",
        }
    except ValueError as e:
        return {"success": False, "error": str(e)}


def cmd_switch(args: argparse.Namespace) -> Dict[str, Any]:
    """Switch to a branch."""
    try:
        branch = switch_branch(args.branch_id)
        return {
            "success": True,
            "action": "switch",
            "branch": branch,
            "message": f"Switched to branch '{args.branch_id}'",
        }
    except ValueError as e:
        return {"success": False, "error": str(e)}


def cmd_merge(args: argparse.Namespace) -> Dict[str, Any]:
    """Merge a branch."""
    try:
        result = merge_branch(
            branch_id=args.branch_id,
            outcome=args.outcome,
            delete_after_merge=args.delete,
        )
        return {
            "success": True,
            "action": "merge",
            "result": result,
            "message": f"Merged '{args.branch_id}' into '{result['to']}' with outcome: {args.outcome}",
        }
    except ValueError as e:
        return {"success": False, "error": str(e)}


def cmd_list(args: argparse.Namespace) -> Dict[str, Any]:
    """List all branches."""
    branches = list_branches()
    return {
        "success": True,
        "action": "list",
        "branches": branches,
        "count": len(branches),
    }


def cmd_delete(args: argparse.Namespace) -> Dict[str, Any]:
    """Delete a branch."""
    try:
        delete_branch(args.branch_id, force=args.force)
        return {
            "success": True,
            "action": "delete",
            "branch_id": args.branch_id,
            "message": f"Deleted branch '{args.branch_id}'",
        }
    except ValueError as e:
        return {"success": False, "error": str(e)}


def cmd_current(args: argparse.Namespace) -> Dict[str, Any]:
    """Show current branch."""
    branch_id, branch_data = get_current_branch()
    return {
        "success": True,
        "action": "current",
        "branch_id": branch_id,
        "branch": branch_data,
    }


def cmd_history(args: argparse.Namespace) -> Dict[str, Any]:
    """Show branch history."""
    history = get_branch_history(limit=args.limit)
    return {
        "success": True,
        "action": "history",
        "history": history,
        "count": len(history),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Session branch operations")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create
    create_parser = subparsers.add_parser("create", help="Create a new branch")
    create_parser.add_argument("branch_id", help="Branch identifier (no spaces)")
    create_parser.add_argument("reason", help="Why this branch was created")
    create_parser.add_argument(
        "--no-copy", action="store_true", help="Don't copy context from current branch"
    )

    # switch
    switch_parser = subparsers.add_parser("switch", help="Switch to a branch")
    switch_parser.add_argument("branch_id", help="Branch to switch to")

    # merge
    merge_parser = subparsers.add_parser("merge", help="Merge a branch")
    merge_parser.add_argument("branch_id", help="Branch to merge")
    merge_parser.add_argument("outcome", help="What was learned/fixed")
    merge_parser.add_argument(
        "--delete", action="store_true", help="Delete branch after merge"
    )

    # list
    subparsers.add_parser("list", help="List all branches")

    # delete
    delete_parser = subparsers.add_parser("delete", help="Delete a branch")
    delete_parser.add_argument("branch_id", help="Branch to delete")
    delete_parser.add_argument(
        "--force", action="store_true", help="Delete even if not merged"
    )

    # current
    subparsers.add_parser("current", help="Show current branch")

    # history
    history_parser = subparsers.add_parser("history", help="Show branch history")
    history_parser.add_argument(
        "--limit", type=int, default=20, help="Maximum entries to show"
    )

    args = parser.parse_args()

    # Dispatch to command handler
    handlers = {
        "create": cmd_create,
        "switch": cmd_switch,
        "merge": cmd_merge,
        "list": cmd_list,
        "delete": cmd_delete,
        "current": cmd_current,
        "history": cmd_history,
    }

    handler = handlers.get(args.command)
    if handler:
        result = handler(args)
        print(json.dumps(result, indent=2, default=str))
        return 0 if result.get("success", False) else 1
    else:
        print(
            json.dumps({"success": False, "error": f"Unknown command: {args.command}"})
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
