#!/usr/bin/env python3
"""
PreCompact Hook
Fires before context compaction to preserve critical session state.

With 1M context, compaction happens less often but loses MORE context at once.
This hook ensures key state is captured before the compaction pass runs.

Responsibilities:
1. Snapshot current session state to .claude/popkit/compaction-log.json
2. Update STATUS.json with a lightweight git + context snapshot
3. Return additionalContext so the model knows compaction happened

Design constraints:
- Must be FAST (< 3 seconds) -- compaction cannot wait
- No network calls, no heavy project checks
- Only git state + in-memory context summary
"""

import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_git_snapshot():
    """Get minimal git state -- branch + last commit only.

    This is intentionally lightweight: no porcelain status,
    no diff stats, just enough to orient after compaction.
    """
    snapshot = {"branch": "", "last_commit": ""}

    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            snapshot["branch"] = result.stdout.strip()
    except Exception:
        pass

    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%h - %s"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            snapshot["last_commit"] = result.stdout.strip()
    except Exception:
        pass

    return snapshot


def get_session_token_summary():
    """Read token tracking data from context-monitor's session file.

    Returns whatever the context-monitor has accumulated, or empty defaults.
    """
    summary = {
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "tool_calls": 0,
    }

    # Check project-local first, then global
    for session_file in [
        Path.cwd() / ".claude" / "session-tokens.json",
        Path.home() / ".claude" / "session-tokens.json",
    ]:
        if session_file.exists():
            try:
                with open(session_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                summary["total_input_tokens"] = data.get("total_input_tokens", 0)
                summary["total_output_tokens"] = data.get("total_output_tokens", 0)
                summary["tool_calls"] = data.get("tool_calls", 0)
                break
            except (json.JSONDecodeError, OSError):
                pass

    return summary


def write_compaction_log(entry):
    """Append compaction event to .claude/popkit/compaction-log.json.

    Keeps the last 50 entries to avoid unbounded growth.
    """
    log_dir = Path.cwd() / ".claude" / "popkit"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "compaction-log.json"

    events = []
    if log_file.exists():
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                events = json.load(f)
        except (json.JSONDecodeError, OSError):
            events = []

    events.append(entry)

    # Keep last 50 compaction events
    if len(events) > 50:
        events = events[-50:]

    try:
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2)
    except OSError as e:
        print(f"  Warning: failed to write compaction log: {e}", file=sys.stderr)


def update_status_json(git_snapshot, token_summary, compaction_count):
    """Update STATUS.json with compaction marker and git snapshot.

    This is a lightweight merge -- only updates compaction-related fields
    and the git snapshot. Does NOT run expensive checks (tests, build, lint).
    """
    status_file = Path.cwd() / ".claude" / "STATUS.json"

    status = {}
    if status_file.exists():
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                status = json.load(f)
        except (json.JSONDecodeError, OSError):
            status = {}

    # Update git snapshot (lightweight -- no service/check gathering)
    status["git"] = {
        "branch": git_snapshot["branch"],
        "lastCommit": git_snapshot["last_commit"],
    }

    # Add compaction marker
    status["lastCompaction"] = {
        "timestamp": datetime.now().isoformat() + "Z",
        "tokensBefore": token_summary["total_input_tokens"],
        "toolCallsBefore": token_summary["tool_calls"],
        "compactionNumber": compaction_count,
    }

    status["lastUpdate"] = datetime.now().isoformat() + "Z"

    try:
        status_file.parent.mkdir(parents=True, exist_ok=True)
        with open(status_file, "w", encoding="utf-8") as f:
            json.dump(status, f, indent=2)
    except OSError as e:
        print(f"  Warning: failed to update STATUS.json: {e}", file=sys.stderr)


def count_previous_compactions():
    """Count how many compactions have occurred this session."""
    log_file = Path.cwd() / ".claude" / "popkit" / "compaction-log.json"
    if not log_file.exists():
        return 0

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            events = json.load(f)
        return len(events)
    except (json.JSONDecodeError, OSError):
        return 0


def main():
    """Main entry point -- JSON stdin/stdout protocol."""
    try:
        input_text = sys.stdin.read()
        input_data = json.loads(input_text) if input_text.strip() else {}

        # Gather lightweight state
        git_snapshot = get_git_snapshot()
        token_summary = get_session_token_summary()
        compaction_count = count_previous_compactions() + 1

        # Build compaction log entry
        log_entry = {
            "event": "pre_compact",
            "compaction_number": compaction_count,
            "timestamp": datetime.now().isoformat() + "Z",
            "git": git_snapshot,
            "tokens": token_summary,
            "input_summary": {
                "keys": list(input_data.keys()) if input_data else [],
            },
        }

        # Write compaction log
        write_compaction_log(log_entry)

        # Update STATUS.json with lightweight snapshot
        update_status_json(git_snapshot, token_summary, compaction_count)

        # Build additionalContext for the model post-compaction
        branch_info = (
            f" on branch '{git_snapshot['branch']}'" if git_snapshot["branch"] else ""
        )
        token_info = (
            f" ({token_summary['total_input_tokens']:,} input tokens consumed)"
            if token_summary["total_input_tokens"] > 0
            else ""
        )

        context_lines = [
            f"POPKIT: Context compaction #{compaction_count} is occurring{branch_info}{token_info}.",
            "Session state has been saved to .claude/STATUS.json and .claude/popkit/compaction-log.json.",
            "After compaction, check .claude/STATUS.json if you need to recall the current task, branch, or recent decisions.",
        ]

        # Log to stderr
        print(
            f"  PreCompact: compaction #{compaction_count}{branch_info}{token_info}",
            file=sys.stderr,
        )

        # Output JSON response
        response = {
            "status": "success",
            "message": f"Pre-compaction snapshot saved (compaction #{compaction_count})",
            "timestamp": datetime.now().isoformat(),
            "additionalContext": "\n".join(context_lines),
        }
        print(json.dumps(response))

    except json.JSONDecodeError:
        # No input or bad JSON -- still save what we can
        response = {
            "status": "success",
            "message": "PreCompact hook completed (no input)",
            "timestamp": datetime.now().isoformat(),
            "additionalContext": "POPKIT: Context compaction is occurring. Check .claude/STATUS.json for preserved session state.",
        }
        print(json.dumps(response))
    except Exception as e:
        response = {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
        print(json.dumps(response))
        print(f"Error in pre-compact hook: {e}", file=sys.stderr)
        sys.exit(0)  # Never block compaction


if __name__ == "__main__":
    main()
