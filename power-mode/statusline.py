#!/usr/bin/env python3
"""
Power Mode Status Line Script
Displays Power Mode status in Claude Code status line.

Format: [POP] #N Phase: X (N/M) [####------] 40% (/power status | stop)

Components:
- [POP] - Yellow bold indicator when Power Mode is active
- #N - Issue number (if working on a GitHub issue)
- Phase: X (N/M) - Current phase and progress
- Progress bar - Visual completion indicator
- Commands hint - Quick reference

Usage:
  Configured in .claude/settings.json as statusLine command
  Reads state from ~/.claude/power-mode-state.json

Part of the popkit plugin system.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional


# ANSI color codes
class Colors:
    YELLOW = "\033[33m"
    GREEN = "\033[32m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    RED = "\033[31m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"


def get_state_file_path() -> Path:
    """Get path to power mode state file."""
    # Try project-local first
    local_state = Path.cwd() / ".claude" / "power-mode-state.json"
    if local_state.exists():
        return local_state

    # Fall back to user home
    home_state = Path.home() / ".claude" / "power-mode-state.json"
    return home_state


def load_power_mode_state() -> Dict[str, Any]:
    """Load Power Mode state from file.

    Returns:
        State dict or {"active": False} if not found
    """
    state_file = get_state_file_path()

    if not state_file.exists():
        return {"active": False}

    try:
        return json.loads(state_file.read_text())
    except (json.JSONDecodeError, IOError):
        return {"active": False}


def format_progress_bar(progress: float, width: int = 10) -> str:
    """Format a progress bar.

    Args:
        progress: Progress value (0.0 to 1.0)
        width: Bar width in characters

    Returns:
        Formatted progress bar string
    """
    progress = max(0.0, min(1.0, progress))  # Clamp to [0, 1]
    filled = int(progress * width)
    empty = width - filled

    return f"[{'#' * filled}{'-' * empty}]"


def format_runtime(activated_at: str) -> str:
    """Format runtime duration.

    Args:
        activated_at: ISO format timestamp

    Returns:
        Human-readable duration (e.g., "5m", "1h 23m")
    """
    try:
        start = datetime.fromisoformat(activated_at.replace('Z', '+00:00'))
        now = datetime.now(start.tzinfo) if start.tzinfo else datetime.now()
        delta = now - start

        total_seconds = int(delta.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    except Exception:
        return "?"


def format_status_line(state: Dict[str, Any]) -> str:
    """Format the status line output.

    Args:
        state: Power Mode state dict

    Returns:
        Formatted status line string (empty if Power Mode inactive)
    """
    if not state.get("active"):
        return ""  # No status line when inactive

    # Build components
    components = []

    # [POP] indicator
    pop_indicator = f"{Colors.YELLOW}{Colors.BOLD}[POP]{Colors.RESET}"
    components.append(pop_indicator)

    # Issue number (if present)
    issue_num = state.get("active_issue")
    if issue_num:
        issue_display = f"{Colors.MAGENTA}#{issue_num}{Colors.RESET}"
        components.append(issue_display)

    # Phase info
    current_phase = state.get("current_phase", "unknown")
    phase_index = state.get("phase_index", 0)
    total_phases = state.get("total_phases", 0)

    if total_phases > 0:
        phase_display = f"{Colors.BLUE}Phase: {current_phase} ({phase_index}/{total_phases}){Colors.RESET}"
    else:
        phase_display = f"{Colors.BLUE}Phase: {current_phase}{Colors.RESET}"
    components.append(phase_display)

    # Progress bar
    progress = state.get("progress", 0.0)
    bar = format_progress_bar(progress)
    percent = int(progress * 100)
    progress_display = f"{Colors.GREEN}{bar} {percent}%{Colors.RESET}"
    components.append(progress_display)

    # Commands hint (dimmed)
    hint = f"{Colors.DIM}(/power status | stop){Colors.RESET}"
    components.append(hint)

    return " ".join(components)


def format_detailed_status(state: Dict[str, Any]) -> str:
    """Format detailed status for /popkit:power status command.

    Args:
        state: Power Mode state dict

    Returns:
        Multi-line detailed status
    """
    if not state.get("active"):
        lines = [
            "",
            f"{Colors.BLUE}[i] POWER MODE INACTIVE{Colors.RESET}",
            "",
            "No active Power Mode session.",
            "",
            "To start Power Mode:",
            "  /popkit:work #N -p     Work on issue with Power Mode",
            "  /popkit:power \"task\"   Start with custom objective",
            "  /popkit:issues --power List issues recommending Power Mode",
            ""
        ]
        return '\n'.join(lines)

    # Active session details
    issue_num = state.get("active_issue")
    session_id = state.get("session_id", "unknown")
    activated_at = state.get("activated_at", "")
    runtime = format_runtime(activated_at) if activated_at else "?"

    current_phase = state.get("current_phase", "unknown")
    phase_index = state.get("phase_index", 0)
    total_phases = state.get("total_phases", 0)
    progress = state.get("progress", 0.0)
    percent = int(progress * 100)

    phases_completed = state.get("phases_completed", [])
    source = state.get("source", "unknown")

    lines = [
        "",
        f"{Colors.GREEN}[+] POWER MODE ACTIVE{Colors.RESET}",
        "",
        f"Session: {session_id}",
    ]

    if issue_num:
        lines.append(f"Issue: #{issue_num}")

    lines.extend([
        f"Source: {source}",
        f"Started: {runtime} ago" if runtime else "",
        "",
        "Current State:",
        f"  Phase: {current_phase} ({phase_index}/{total_phases})",
        f"  Progress: {format_progress_bar(progress)} {percent}%",
        "",
        "Phases Completed:" if phases_completed else "",
    ])

    for phase in phases_completed:
        lines.append(f"  - {phase}")

    lines.extend([
        "",
        "Commands:",
        f"  {Colors.CYAN}/popkit:power stop{Colors.RESET}    Stop Power Mode",
    ])

    if issue_num:
        lines.append(f"  {Colors.CYAN}/popkit:work #{issue_num}{Colors.RESET}     Continue current issue")

    lines.append("")

    return '\n'.join(lines)


def main():
    """Main entry point.

    Reads session info from stdin (JSON from Claude Code) if available,
    then outputs formatted status line.
    """
    # Try to read session info from stdin
    try:
        if not sys.stdin.isatty():
            session_info = json.loads(sys.stdin.read())
        else:
            session_info = {}
    except Exception:
        session_info = {}

    # Load state
    state = load_power_mode_state()

    # Check for command-line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "status" or sys.argv[1] == "--detailed":
            # Output detailed status
            print(format_detailed_status(state))
        elif sys.argv[1] == "raw":
            # Output raw JSON state
            print(json.dumps(state, indent=2))
        else:
            # Output status line
            status_line = format_status_line(state)
            if status_line:
                print(status_line)
    else:
        # Default: output status line
        status_line = format_status_line(state)
        if status_line:
            print(status_line)


if __name__ == "__main__":
    main()
