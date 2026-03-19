#!/usr/bin/env python3
"""
Session State Restore Script.

Restore session state from STATUS.json.

Usage:
    python restore_state.py [--mode MODE] [--status-path PATH]

Modes:
    find       - Find STATUS.json in expected locations
    parse      - Parse STATUS.json and validate structure
    verify-git - Verify git state matches saved state
    summary    - Generate session summary
    all        - Full restore process

Output:
    JSON object with restored state and session type
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from popkit_shared.utils.subprocess_utils import run_command_simple

try:
    from popkit_shared.utils.session_branch_manager import (
        get_current_branch as get_session_branch,
        list_branches as list_session_branches,
    )

    HAS_SESSION_BRANCHES = True
except ImportError:
    HAS_SESSION_BRANCHES = False


def find_status_file() -> Optional[Path]:
    """Find STATUS.json in expected locations."""
    locations = [
        Path(".claude/STATUS.json"),
        Path("STATUS.json"),
        Path.home() / ".claude" / "STATUS.json",
    ]

    for path in locations:
        if path.exists():
            return path

    return None


def parse_status_file(path: Path) -> Dict[str, Any]:
    """Parse STATUS.json and return contents."""
    content = path.read_text()
    return json.loads(content)


def calculate_session_type(last_update: str) -> Dict[str, Any]:
    """Calculate session type based on time since last update."""
    try:
        # Parse the timestamp
        if last_update.endswith("Z"):
            last_update = last_update[:-1] + "+00:00"
        last_dt = datetime.fromisoformat(last_update.replace("Z", "+00:00"))
        now = datetime.now(last_dt.tzinfo) if last_dt.tzinfo else datetime.now()

        # Calculate hours since
        delta = (
            now - last_dt.replace(tzinfo=None) if not last_dt.tzinfo else now - last_dt
        )
        hours_since = delta.total_seconds() / 3600

        if hours_since < 0.5:
            session_type = "Continuation"
            behavior = "Quick restore, assume full context"
        elif hours_since < 4:
            session_type = "Resume"
            behavior = "Restore context, brief refresh"
        else:
            session_type = "Fresh Start"
            behavior = "Full context load, verify state"

        # Format time since
        if hours_since < 1:
            time_since = f"{int(hours_since * 60)} minutes ago"
        elif hours_since < 24:
            time_since = f"{int(hours_since)} hours ago"
        else:
            days = int(hours_since / 24)
            time_since = f"{days} day{'s' if days > 1 else ''} ago"

        return {
            "session_type": session_type,
            "hours_since": round(hours_since, 2),
            "time_since": time_since,
            "behavior": behavior,
        }
    except Exception as e:
        return {
            "session_type": "Fresh Start",
            "hours_since": -1,
            "time_since": "unknown",
            "behavior": "Full context load, verify state",
            "error": str(e),
        }


def verify_git_state(saved_git: Dict[str, Any]) -> Dict[str, Any]:
    """Verify current git state matches saved state."""
    verification = {"matches": True, "discrepancies": []}

    # Check branch
    current_branch, ok = run_command_simple("git branch --show-current")
    if ok:
        if current_branch != saved_git.get("branch", ""):
            verification["matches"] = False
            verification["discrepancies"].append(
                {
                    "field": "branch",
                    "saved": saved_git.get("branch"),
                    "current": current_branch,
                }
            )

    # Check uncommitted files count
    status, ok = run_command_simple("git status --porcelain")
    if ok:
        current_uncommitted = len([l for l in status.split("\n") if l.strip()])
        saved_uncommitted = saved_git.get("uncommittedFiles", 0)

        if current_uncommitted != saved_uncommitted:
            verification["matches"] = False
            verification["discrepancies"].append(
                {
                    "field": "uncommittedFiles",
                    "saved": saved_uncommitted,
                    "current": current_uncommitted,
                }
            )

    # Check last commit
    commit, ok = run_command_simple("git log -1 --format='%h - %s'")
    if ok:
        if commit != saved_git.get("lastCommit", ""):
            verification["discrepancies"].append(
                {
                    "field": "lastCommit",
                    "saved": saved_git.get("lastCommit"),
                    "current": commit,
                    "note": "New commits since last session",
                }
            )

    verification["current_git"] = {
        "branch": current_branch if ok else "unknown",
        "uncommittedFiles": current_uncommitted if ok else -1,
        "lastCommit": commit if ok else "unknown",
    }

    return verification


def collect_session_branch_context(status: Dict[str, Any]) -> Dict[str, Any]:
    """
    Collect session branch context from STATUS.json and the branch manager.

    Args:
        status: Parsed STATUS.json contents

    Returns:
        Dict with session branch information:
        - current_branch: Current session branch ID
        - current_branch_reason: Reason for the current branch
        - unmerged: List of unmerged branch summaries
        - stale: List of stale branch IDs (>3 days)
    """
    result = {
        "current_branch": "main",
        "current_branch_reason": "",
        "unmerged": [],
        "stale": [],
    }

    # Try the branch manager first (live data)
    if HAS_SESSION_BRANCHES:
        try:
            branch_id, branch_data = get_session_branch()
            branches = list_session_branches()

            result["current_branch"] = branch_id
            result["current_branch_reason"] = branch_data.get("reason", "")

            now = datetime.now(timezone.utc)
            for b in branches:
                if b.get("id") == "main" or b.get("merged", False):
                    continue
                branch_info = {
                    "id": b.get("id"),
                    "reason": b.get("reason", ""),
                    "parent": b.get("parent", "main"),
                    "age_days": 0,
                }
                created = b.get("created")
                if created:
                    try:
                        created_dt = datetime.fromisoformat(
                            created.replace("Z", "+00:00")
                        )
                        age_days = (now - created_dt).total_seconds() / 86400
                        branch_info["age_days"] = round(age_days, 1)
                        if age_days > 3:
                            result["stale"].append(b.get("id"))
                    except (ValueError, TypeError):
                        pass
                result["unmerged"].append(branch_info)
            return result
        except Exception:
            pass

    # Fallback: read from STATUS.json directly
    branches = status.get("branches", {})
    current_branch = status.get("currentBranch", "main")
    result["current_branch"] = current_branch

    if current_branch in branches:
        result["current_branch_reason"] = branches[current_branch].get("reason", "")

    now = datetime.now(timezone.utc)
    for bid, bdata in branches.items():
        if bid == "main" or bdata.get("merged", False):
            continue
        branch_info = {
            "id": bid,
            "reason": bdata.get("reason", ""),
            "parent": bdata.get("parent", "main"),
            "age_days": 0,
        }
        created = bdata.get("created")
        if created:
            try:
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                age_days = (now - created_dt).total_seconds() / 86400
                branch_info["age_days"] = round(age_days, 1)
                if age_days > 3:
                    result["stale"].append(bid)
            except (ValueError, TypeError):
                pass
        result["unmerged"].append(branch_info)

    return result


def generate_summary(
    status: Dict[str, Any],
    session_info: Dict[str, Any],
    verification: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Generate session summary for display."""
    # Collect session branch context
    branch_context = collect_session_branch_context(status)

    summary = {
        "session_type": session_info["session_type"],
        "time_since": session_info["time_since"],
        "project": status.get("project", "unknown"),
        "git": {
            "branch": status.get("git", {}).get("branch", "unknown"),
            "uncommitted": status.get("git", {}).get("uncommittedFiles", 0),
            "lastCommit": status.get("git", {}).get("lastCommit", "unknown"),
        },
        "session_branch": branch_context,
        "tasks": {
            "inProgress": status.get("tasks", {}).get("inProgress", []),
            "completed": status.get("tasks", {}).get("completed", [])[:3],  # Last 3
            "blocked": status.get("tasks", {}).get("blocked", []),
        },
        "context": {
            "focusArea": status.get("context", {}).get("focusArea", ""),
            "nextAction": status.get("context", {}).get("nextAction", ""),
            "blocker": status.get("context", {}).get("blocker"),
            "keyDecisions": status.get("context", {}).get("keyDecisions", []),
        },
        "projectData": status.get("projectData", {}),
    }

    # Build options list - include session branch switch if applicable
    options = []
    options.append({"label": "Continue with next action", "value": "continue"})

    # Offer to switch back to session branch if it was active last session
    if (
        branch_context["current_branch"] != "main"
        and branch_context["current_branch_reason"]
    ):
        options.append(
            {
                "label": f"Switch to session branch: {branch_context['current_branch']}",
                "value": "switch_branch",
                "description": branch_context["current_branch_reason"],
            }
        )

    options.append({"label": "Review full context first", "value": "review"})
    options.append({"label": "Start fresh", "value": "fresh"})
    summary["options"] = options

    if verification:
        summary["verification"] = verification

    return summary


def format_display_box(summary: Dict[str, Any]) -> str:
    """Format summary as display box."""
    session_emoji = {"Continuation": "⚡", "Resume": "🔄", "Fresh Start": "🌅"}

    emoji = session_emoji.get(summary["session_type"], "📋")

    lines = [
        "┌─────────────────────────────────────────────┐",
        f"│ {emoji} {summary['session_type']} Session{' ' * (30 - len(summary['session_type']))}│",
        f"│ Last: {summary['time_since']}{' ' * (36 - len(summary['time_since']))}│",
        "├─────────────────────────────────────────────┤",
        f"│ Branch: {summary['git']['branch'][:30]}{' ' * (34 - min(30, len(summary['git']['branch'])))}│",
    ]

    # Show session branch if not on main
    branch_ctx = summary.get("session_branch", {})
    session_branch_id = branch_ctx.get("current_branch", "main")
    if session_branch_id != "main":
        sb_display = session_branch_id[:28]
        lines.append(f"│ Session branch: {sb_display}{' ' * (27 - len(sb_display))}│")

    lines.append(f"│ Uncommitted: {summary['git']['uncommitted']} files{' ' * 24}│")

    # Show unmerged session branches
    unmerged = branch_ctx.get("unmerged", [])
    if unmerged:
        lines.append("├─────────────────────────────────────────────┤")
        count_label = f"Session Branches ({len(unmerged)} unmerged):"
        lines.append(f"│ {count_label}{' ' * (42 - len(count_label))}│")
        for b in unmerged[:3]:
            bid = b.get("id", "?")[:16]
            reason = b.get("reason", "")[:16]
            age = b.get("age_days", 0)
            stale_marker = ", stale" if age > 3 else ""
            if age < 1:
                age_str = f"{int(age * 24)}h"
            else:
                age_str = f"{int(age)}d"
            entry = f"{bid}: {reason} ({age_str}{stale_marker})"
            entry_short = entry[:40]
            lines.append(f"│ * {entry_short}{' ' * (40 - len(entry_short))}│")

    if summary["tasks"]["inProgress"]:
        lines.append("├─────────────────────────────────────────────┤")
        lines.append("│ In Progress:                                │")
        for task in summary["tasks"]["inProgress"][:3]:
            task_short = task[:38]
            lines.append(f"│ * {task_short}{' ' * (40 - len(task_short))}│")

    if summary["context"]["nextAction"]:
        lines.append("├─────────────────────────────────────────────┤")
        lines.append("│ Next Action:                                │")
        next_action = summary["context"]["nextAction"][:38]
        lines.append(f"│ {next_action}{' ' * (42 - len(next_action))}│")

    lines.append("└─────────────────────────────────────────────┘")

    return "\n".join(lines)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Restore session state")
    parser.add_argument(
        "--mode",
        choices=["find", "parse", "verify-git", "summary", "all"],
        default="all",
        help="Operation mode",
    )
    parser.add_argument("--status-path", help="Path to STATUS.json")
    parser.add_argument(
        "--format", choices=["json", "display"], default="json", help="Output format"
    )
    args = parser.parse_args()

    result = {
        "operation": "restore_state",
        "mode": args.mode,
        "timestamp": datetime.now().isoformat(),
    }

    # Find STATUS.json
    if args.status_path:
        status_path = Path(args.status_path)
    else:
        status_path = find_status_file()

    if args.mode == "find":
        if status_path and status_path.exists():
            result["found"] = True
            result["path"] = str(status_path)
        else:
            result["found"] = False
            result["searched"] = [
                ".claude/STATUS.json",
                "STATUS.json",
                "~/.claude/STATUS.json",
            ]
        print(json.dumps(result, indent=2))
        return 0 if result.get("found") else 1

    if not status_path or not status_path.exists():
        result["success"] = False
        result["error"] = "STATUS.json not found"
        print(json.dumps(result, indent=2))
        return 1

    result["status_path"] = str(status_path)

    # Parse STATUS.json
    try:
        status = parse_status_file(status_path)
        result["status"] = status
    except json.JSONDecodeError as e:
        result["success"] = False
        result["error"] = f"Invalid JSON: {e}"
        print(json.dumps(result, indent=2))
        return 1

    if args.mode == "parse":
        result["success"] = True
        print(json.dumps(result, indent=2))
        return 0

    # Calculate session type
    session_info = calculate_session_type(status.get("lastUpdate", ""))
    result["session_info"] = session_info

    # Verify git state
    verification = None
    if (
        args.mode in ["verify-git", "all"]
        and session_info["session_type"] == "Fresh Start"
    ):
        verification = verify_git_state(status.get("git", {}))
        result["verification"] = verification

    # Generate summary
    if args.mode in ["summary", "all"]:
        summary = generate_summary(status, session_info, verification)
        result["summary"] = summary

        if args.format == "display":
            print(format_display_box(summary))
            return 0

    result["success"] = True
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
