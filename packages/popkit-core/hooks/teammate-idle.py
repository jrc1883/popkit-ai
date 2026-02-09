#!/usr/bin/env python3
"""
TeammateIdle Hook (Claude Code 2.1.33+)
Fires when an Agent Teams teammate becomes idle (waiting for work).

Responsibilities:
1. Log idle events for observability and utilization tracking
2. Record teammate metrics (duration active, tools used)
3. Update STATUS.json with teammate state
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def log_teammate_idle(data):
    """Log teammate idle event to observability file."""
    logs_dir = Path(".claude", "popkit", "logs")
    logs_dir.mkdir(parents=True, exist_ok=True)

    log_file = logs_dir / "teammate-events.json"

    entry = {
        "event": "teammate_idle",
        "teammate": data.get("teammate", data.get("agent", "unknown")),
        "reason": data.get("reason", "completed_work"),
        "duration_ms": data.get("duration_ms", 0),
        "tools_used": data.get("tools_used", 0),
        "tokens_used": data.get("tokens_used", 0),
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

    # Keep last 100 events to prevent unbounded growth
    if len(events) > 100:
        events = events[-100:]

    try:
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(events, f, indent=2)
    except OSError as e:
        print(f"  Warning: failed to write teammate log: {e}", file=sys.stderr)


def update_status(data):
    """Update STATUS.json with teammate idle state."""
    status_file = Path(".claude", "STATUS.json")

    status = {}
    if status_file.exists():
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                status = json.load(f)
        except (json.JSONDecodeError, OSError):
            status = {}

    # Update teammates section
    teammates = status.get("teammates", {})
    teammate_name = data.get("teammate", data.get("agent", "unknown"))
    teammates[teammate_name] = {
        "state": "idle",
        "last_active": datetime.now().isoformat(),
        "tools_used": data.get("tools_used", 0),
        "tokens_used": data.get("tokens_used", 0),
    }
    status["teammates"] = teammates

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

        # Log the idle event
        log_teammate_idle(data)

        # Update STATUS.json
        update_status(data)

        teammate = data.get("teammate", data.get("agent", "unknown"))
        print(f"  Teammate {teammate} is now idle", file=sys.stderr)

        response = {
            "status": "success",
            "message": f"Teammate idle event logged for {teammate}",
            "timestamp": datetime.now().isoformat(),
        }
        print(json.dumps(response))

    except json.JSONDecodeError:
        response = {
            "status": "success",
            "message": "TeammateIdle hook completed (no input)",
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
        print(f"Error in teammate-idle hook: {e}", file=sys.stderr)
        sys.exit(0)  # Never block on errors


if __name__ == "__main__":
    main()
