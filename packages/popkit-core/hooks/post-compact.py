#!/usr/bin/env python3
"""
PostCompact Hook
Fires AFTER context compaction to restore orientation for the model.

Pairs with pre-compact.py: PreCompact saves state before compaction,
PostCompact reads it back and provides additionalContext so the model
knows what it was doing before the context window was trimmed.

With 1M context, compaction is infrequent but loses significant context.
This hook bridges the gap by surfacing preserved state.

Responsibilities:
1. Read compaction log from .claude/popkit/compaction-log.json
2. Read STATUS.json to get preserved session state
3. Return additionalContext with task summary, branch, decisions, compaction count
4. Pointer to STATUS.json for full context recovery

Design constraints:
- Must be FAST (< 3 seconds) -- model is waiting for context
- No network calls, no heavy computation
- Only reads files written by pre-compact.py
- stdlib only (json, sys, pathlib, datetime)
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path


def _get_plugin_data_dir() -> Path:
    """Get plugin data directory (CLAUDE_PLUGIN_DATA or fallback)."""
    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA")
    if plugin_data:
        return Path(plugin_data)
    return Path.cwd() / ".claude" / "popkit"


def read_compaction_log():
    """Read the compaction log written by pre-compact.py.

    Returns the full log and the latest entry, or empty defaults.
    """
    log_file = _get_plugin_data_dir() / "compaction-log.json"

    if not log_file.exists():
        return [], None

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            events = json.load(f)

        if not events:
            return [], None

        return events, events[-1]
    except (json.JSONDecodeError, OSError):
        return [], None


def read_status_json():
    """Read STATUS.json for preserved session state.

    Returns the status dict, or empty dict if unavailable.
    """
    status_file = Path.cwd() / ".claude" / "STATUS.json"

    if not status_file.exists():
        return {}

    try:
        with open(status_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def extract_task_summary(status):
    """Extract a brief summary of what was being worked on.

    Pulls from STATUS.json fields that session-capture and pre-compact
    populate: currentTask, recentDecisions, activeFiles.
    """
    parts = []

    # Current task (set by session-capture or manual STATUS update)
    current_task = status.get("currentTask") or status.get("current_task")
    if current_task:
        if isinstance(current_task, dict):
            desc = current_task.get("description") or current_task.get("name", "")
            if desc:
                parts.append(f"Task: {desc}")
        elif isinstance(current_task, str):
            parts.append(f"Task: {current_task}")

    # Recent decisions
    decisions = status.get("recentDecisions") or status.get("recent_decisions") or []
    if decisions:
        if isinstance(decisions, list):
            # Show last 3 decisions
            recent = decisions[-3:]
            for d in recent:
                if isinstance(d, dict):
                    parts.append(f"Decision: {d.get('summary', d.get('description', str(d)))}")
                elif isinstance(d, str):
                    parts.append(f"Decision: {d}")

    # Active files being worked on
    active_files = status.get("activeFiles") or status.get("active_files") or []
    if active_files and isinstance(active_files, list):
        file_list = ", ".join(str(f) for f in active_files[:5])
        parts.append(f"Active files: {file_list}")

    return parts


def build_context_message(compaction_count, latest_entry, status):
    """Build the additionalContext string for the model.

    This is the key output -- it tells the model what it was doing
    before compaction wiped the context.
    """
    lines = []

    # Header with compaction count
    lines.append(
        f"POPKIT: Context compaction #{compaction_count} has completed. "
        "Previous context was trimmed."
    )

    # Git state from the pre-compact snapshot
    if latest_entry:
        git = latest_entry.get("git", {})
        branch = git.get("branch", "")
        commit = git.get("last_commit", "")
        if branch:
            lines.append(f"Branch: {branch}")
        if commit:
            lines.append(f"Last commit: {commit}")

        # Token usage at time of compaction
        tokens = latest_entry.get("tokens", {})
        input_tokens = tokens.get("total_input_tokens", 0)
        tool_calls = tokens.get("tool_calls", 0)
        if input_tokens > 0:
            lines.append(f"Tokens at compaction: {input_tokens:,} input, {tool_calls} tool calls")

    # Task summary from STATUS.json
    task_parts = extract_task_summary(status)
    if task_parts:
        lines.append("")
        lines.append("What you were working on:")
        lines.extend(f"  - {part}" for part in task_parts)

    # Git state from STATUS.json (may be more current than compaction log)
    status_git = status.get("git", {})
    if status_git:
        branch = status_git.get("branch", "")
        if branch and (not latest_entry or branch != latest_entry.get("git", {}).get("branch", "")):
            lines.append(f"Current branch (from STATUS): {branch}")

    # Compaction history summary
    if compaction_count > 1:
        lines.append(
            f"\nThis is compaction #{compaction_count} this session. "
            "Consider keeping key context concise."
        )

    # Recovery pointer
    lines.append("")
    lines.append(
        "To recover full context, read .claude/STATUS.json. "
        "Compaction history is in .claude/popkit/compaction-log.json."
    )

    return "\n".join(lines)


def main():
    """Main entry point -- JSON stdin/stdout protocol."""
    try:
        input_text = sys.stdin.read()
        # Validate JSON input (PostCompact event payload); content not needed
        if input_text.strip():
            json.loads(input_text)

        # Read compaction log from pre-compact.py
        events, latest_entry = read_compaction_log()
        compaction_count = len(events)

        # Read STATUS.json for preserved session state
        status = read_status_json()

        # Build context message
        context_message = build_context_message(compaction_count, latest_entry, status)

        # Log to stderr
        print(
            f"  PostCompact: restoring context after compaction #{compaction_count}",
            file=sys.stderr,
        )

        # Output JSON response
        response = {
            "status": "success",
            "message": f"Post-compaction context restored (compaction #{compaction_count})",
            "timestamp": datetime.now().isoformat(),
            "additionalContext": context_message,
        }
        print(json.dumps(response))

    except json.JSONDecodeError:
        # No input or bad JSON -- still provide basic context
        response = {
            "status": "success",
            "message": "PostCompact hook completed (no input)",
            "timestamp": datetime.now().isoformat(),
            "additionalContext": (
                "POPKIT: Context compaction has completed. "
                "Check .claude/STATUS.json for preserved session state."
            ),
        }
        print(json.dumps(response))
    except Exception as e:
        response = {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
        print(json.dumps(response))
        print(f"Error in post-compact hook: {e}", file=sys.stderr)
        sys.exit(0)  # Never block post-compaction


if __name__ == "__main__":
    main()
