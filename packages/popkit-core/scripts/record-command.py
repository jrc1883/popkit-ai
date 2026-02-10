#!/usr/bin/env python3
"""
Wrapper to enable recording for any PopKit command execution.

Usage:
    python record-command.py "command description"

This sets POPKIT_RECORD=true and prints the recording file path.
"""

import os
import sys
from datetime import datetime
from pathlib import Path

# Enable recording
os.environ["POPKIT_RECORD"] = "true"

# Set command name from argument or default
command_name = sys.argv[1] if len(sys.argv) > 1 else "manual-test"
os.environ["POPKIT_COMMAND"] = command_name

# Generate session ID
session_id = datetime.now().strftime("%Y%m%d-%H%M%S")
os.environ["POPKIT_RECORD_ID"] = session_id

# Print recording info
recordings_dir = Path.home() / ".claude" / "popkit" / "recordings"
timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
recording_file = recordings_dir / f"{timestamp}-{command_name}-{session_id}.json"

print(f"Recording enabled for: {command_name}")
print(f"Session ID: {session_id}")
print("Recording will be saved to:")
print(f"  {recording_file}")
print()
print("Now run your PopKit command in Claude Code...")
print("All tool calls will be captured automatically.")
print()
print("After command completes, analyze with:")
print(f"  python packages/shared-py/popkit_shared/utils/recording_analyzer.py {recording_file}")
