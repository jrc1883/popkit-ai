#!/usr/bin/env python3
"""
TaskCompleted Hook (Claude Code 2.1.33+, verified compatible through 2.1.79)
Fires when a task (subagent or todo item) completes.

Responsibilities:
1. Log task completion metrics (duration, tools, tokens)
2. Update STATUS.json with task outcome
3. Track cumulative session metrics
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


def log_task_completion(data):
    """Log task completion event."""
    logs_dir = _get_plugin_data_dir() / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_file = logs_dir / "task-completions.json"

    entry = {
        "event": "task_completed",
        "task_id": data.get("task_id", data.get("id", "unknown")),
        "task_description": data.get("description", ""),
        "status": data.get("status", "completed"),
        "duration_ms": data.get("duration_ms", 0),
        "tools_used": data.get("tools_used", 0),
        "tokens_used": data.get("tokens_used", 0),
        "agent": data.get("agent", data.get("agent_type", "")),
        "timestamp": datetime.now().isoformat(),
    }

    # Append to log file
    events = []
    if log_file.exists():
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                events = json.load(f)
        except (json.JSONDecodeError, OSError):
            events = []

    events.append(entry)

    # Keep last 200 events
    if len(events) > 200:
        events = events[-200:]

    try:
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2)
    except OSError as e:
        print(f"  Warning: failed to write task log: {e}", file=sys.stderr)

    return entry


def update_session_metrics(data):
    """Update cumulative session metrics in STATUS.json."""
    status_file = Path(".claude", "STATUS.json")

    status = {}
    if status_file.exists():
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                status = json.load(f)
        except (json.JSONDecodeError, OSError):
            status = {}

    # Update session metrics
    metrics = status.get(
        "session_metrics",
        {
            "tasks_completed": 0,
            "total_duration_ms": 0,
            "total_tokens": 0,
            "total_tools": 0,
        },
    )

    metrics["tasks_completed"] = metrics.get("tasks_completed", 0) + 1
    metrics["total_duration_ms"] = metrics.get("total_duration_ms", 0) + data.get("duration_ms", 0)
    metrics["total_tokens"] = metrics.get("total_tokens", 0) + data.get("tokens_used", 0)
    metrics["total_tools"] = metrics.get("total_tools", 0) + data.get("tools_used", 0)
    metrics["last_task_completed"] = datetime.now().isoformat()

    status["session_metrics"] = metrics

    try:
        with open(status_file, "w", encoding="utf-8") as f:
            json.dump(status, f, indent=2)
    except OSError as e:
        print(f"  Warning: failed to update STATUS.json: {e}", file=sys.stderr)


def main():
    """Main entry point - JSON stdin/stdout protocol."""
    try:
        input_data = sys.stdin.read()
        data = json.loads(input_data) if input_data.strip() else {}

        # Log the completion
        entry = log_task_completion(data)

        # Update session metrics
        update_session_metrics(data)

        task_id = entry["task_id"]
        status = entry["status"]
        duration = entry["duration_ms"]

        if duration > 0:
            print(
                f"  Task {task_id} {status} ({duration}ms)",
                file=sys.stderr,
            )
        else:
            print(f"  Task {task_id} {status}", file=sys.stderr)

        response = {
            "status": "success",
            "message": f"Task completion logged: {task_id}",
            "timestamp": datetime.now().isoformat(),
        }
        print(json.dumps(response))

    except json.JSONDecodeError:
        response = {
            "status": "success",
            "message": "TaskCompleted hook completed (no input)",
            "timestamp": datetime.now().isoformat(),
        }
        print(json.dumps(response))
    except Exception as e:
        response = {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
        print(json.dumps(response))
        print(f"Error in task-completed hook: {e}", file=sys.stderr)
        sys.exit(0)  # Never block on errors


if __name__ == "__main__":
    main()
