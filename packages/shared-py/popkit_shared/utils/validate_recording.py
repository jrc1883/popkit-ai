#!/usr/bin/env python3
"""
Recording Validation Script

Validates that session recordings follow the expected workflow defined in /popkit:record.
Checks event integrity, chronological ordering, and completeness.

Usage: python validate_recording.py <recording.json>
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Set


class RecordingValidator:
    """Validates session recording integrity and workflow compliance."""

    def __init__(self, recording_file: Path):
        self.recording_file = recording_file
        with open(recording_file) as f:
            self.data = json.load(f)

        self.session_id = self.data.get('session_id', 'unknown')
        self.events = self.data.get('events', [])
        self.errors = []
        self.warnings = []
        self.info = []

    def validate(self) -> bool:
        """Run all validation checks. Returns True if all pass."""
        print(f"Validating recording: {self.session_id}")
        print(f"Total events: {len(self.events)}\n")

        # Run all validation checks
        self.check_session_lifecycle()
        self.check_event_pairing()
        self.check_chronological_order()
        self.check_subagent_correlation()
        self.check_event_integrity()
        self.check_expected_workflow()

        # Print results
        self.print_results()

        # Return overall status
        return len(self.errors) == 0

    def check_session_lifecycle(self):
        """Check that session has proper start and end events."""
        print("1. Checking session lifecycle...")

        # Check for session_start
        session_starts = [e for e in self.events if e.get('type') == 'session_start']
        if not session_starts:
            self.errors.append("Missing 'session_start' event")
        elif len(session_starts) > 1:
            self.warnings.append(f"Multiple session_start events ({len(session_starts)})")
        else:
            self.info.append("[OK] Session start event present")

        # Check for session_end
        session_ends = [e for e in self.events if e.get('type') == 'session_end']
        if not session_ends:
            self.errors.append("Missing 'session_end' event - recording stop did not complete properly")
        else:
            self.info.append("[OK]Session end event present")

    def check_event_pairing(self):
        """Check that all tool_call_start events have matching tool_call_complete."""
        print("2. Checking event pairing...")

        starts = {}  # sequence -> event
        completes = {}  # sequence -> event

        for event in self.events:
            event_type = event.get('type')
            seq = event.get('sequence')

            if event_type == 'tool_call_start':
                starts[seq] = event
            elif event_type == 'tool_call_complete':
                completes[seq] = event

        # Check for unpaired starts
        unpaired_starts = []
        for seq, start_event in starts.items():
            # Find matching complete (should be sequence + 1 or later)
            tool_name = start_event.get('tool_name')

            # Look for a complete event for this tool
            found_complete = False
            for complete_seq, complete_event in completes.items():
                if complete_event.get('tool_name') == tool_name and complete_seq > seq:
                    found_complete = True
                    break

            if not found_complete:
                unpaired_starts.append((seq, tool_name))

        if unpaired_starts:
            for seq, tool_name in unpaired_starts:
                self.errors.append(f"Unpaired tool_call_start: sequence {seq}, tool {tool_name} - no matching completion")
        else:
            self.info.append(f"✓ All {len(starts)} tool starts have completions")

        # Check for orphaned completes
        orphaned_completes = []
        for seq, complete_event in completes.items():
            tool_name = complete_event.get('tool_name')

            # Look for a start event for this tool
            found_start = False
            for start_seq, start_event in starts.items():
                if start_event.get('tool_name') == tool_name and start_seq < seq:
                    found_start = True
                    break

            if not found_start:
                orphaned_completes.append((seq, tool_name))

        if orphaned_completes:
            for seq, tool_name in orphaned_completes:
                self.warnings.append(f"Orphaned tool_call_complete: sequence {seq}, tool {tool_name} - no matching start")

    def check_chronological_order(self):
        """Check that events are in chronological order."""
        print("3. Checking chronological order...")

        prev_timestamp = None
        out_of_order = []

        for i, event in enumerate(self.events):
            timestamp_str = event.get('timestamp')
            if not timestamp_str:
                continue

            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))

                if prev_timestamp and timestamp < prev_timestamp:
                    out_of_order.append((i, event.get('type'), timestamp_str))

                prev_timestamp = timestamp
            except:
                self.warnings.append(f"Invalid timestamp format at event {i}: {timestamp_str}")

        if out_of_order:
            for i, event_type, ts in out_of_order:
                self.errors.append(f"Event {i} ({event_type}) is out of chronological order: {ts}")
        else:
            self.info.append(f"✓ All {len(self.events)} events in chronological order")

    def check_subagent_correlation(self):
        """Check that subagent_stop events correlate with task launches."""
        print("4. Checking sub-agent correlation...")

        # Find all task launches
        task_launches = []
        for event in self.events:
            if event.get('type') == 'tool_call_start':
                params = event.get('parameters', {})
                if 'subagent_type' in params:
                    task_launches.append(event)

        # Find all subagent_stop events
        subagent_stops = [e for e in self.events if e.get('type') == 'subagent_stop']

        if len(task_launches) != len(subagent_stops):
            self.warnings.append(
                f"Mismatch: {len(task_launches)} task launches vs {len(subagent_stops)} subagent_stop events"
            )
        else:
            self.info.append(f"✓ {len(task_launches)} task launches matched with {len(subagent_stops)} completions")

        # Check that each subagent_stop has a corresponding task launch
        for stop_event in subagent_stops:
            agent_id = stop_event.get('agent_id')
            stop_session = stop_event.get('session_id')

            # Session ID should match if we're tracking correctly
            # (This was the Issue #603 fix)
            if not stop_session:
                self.warnings.append(f"SubagentStop for {agent_id} missing session_id")

    def check_event_integrity(self):
        """Check that all events have required fields."""
        print("5. Checking event integrity...")

        required_fields = ['type', 'timestamp', 'sequence']

        for i, event in enumerate(self.events):
            for field in required_fields:
                if field not in event:
                    self.errors.append(f"Event {i} missing required field '{field}'")

        # Check for duplicate sequence numbers
        sequences = [e.get('sequence') for e in self.events if e.get('sequence') is not None]
        if len(sequences) != len(set(sequences)):
            duplicates = [s for s in sequences if sequences.count(s) > 1]
            self.errors.append(f"Duplicate sequence numbers: {set(duplicates)}")
        else:
            self.info.append(f"✓ All {len(sequences)} sequence numbers are unique")

    def check_expected_workflow(self):
        """Check against the expected /popkit:record workflow."""
        print("6. Checking expected workflow...")

        # Expected workflow from /popkit:record command:
        # 1. session_start
        # 2. Bash command to enable recording (writes state file)
        # 3. [user work happens - tool calls, sub-agents]
        # 4. Bash command to disable recording
        # 5. session_end (currently missing!)

        event_types = [e.get('type') for e in self.events]

        # Check workflow steps
        if 'session_start' not in event_types:
            self.errors.append("Workflow violation: Missing session_start")

        # Check for recording enable (Bash command with "Recording ENABLED")
        enable_found = False
        for event in self.events:
            if event.get('type') == 'tool_call_complete':
                result = str(event.get('result', ''))
                if 'Recording ENABLED' in result or 'POPKIT_RECORD' in result:
                    enable_found = True
                    break

        if not enable_found:
            self.warnings.append("Could not find recording enable confirmation")
        else:
            self.info.append("[OK]Recording enable command detected")

        # Check for recording disable (Bash command with "Recording STOPPED")
        disable_found = False
        disable_complete = False
        for event in self.events:
            if event.get('type') == 'tool_call_start':
                params = event.get('parameters', {})
                if 'Recording STOPPED' in str(params.get('command', '')):
                    disable_found = True
            elif event.get('type') == 'tool_call_complete':
                result = str(event.get('result', ''))
                if 'Recording STOPPED' in result:
                    disable_complete = True

        if not disable_found:
            self.warnings.append("Could not find recording stop command")
        else:
            self.info.append("[OK]Recording stop command detected")

        # Check if stop command was completed (Solution A should have added completion)
        if disable_found and not disable_complete:
            # Check if we have a manually-added completion for the stop command
            # (Solution A records the completion before disabling)
            has_manual_completion = False
            for event in self.events:
                if event.get('type') == 'tool_call_complete':
                    result = str(event.get('result', ''))
                    if 'stopped successfully' in result.lower():
                        has_manual_completion = True
                        break

            if not has_manual_completion:
                self.errors.append(
                    "Recording stop command started but did not complete - "
                    "need to implement Solution A to record final events before stopping"
                )
            else:
                self.info.append("[OK]Recording stop command properly completed (Solution A working)")

        # Check for session_end (Solution A should add this)
        if 'session_end' not in event_types:
            self.errors.append(
                "Workflow violation: Missing session_end event - "
                "Solution A not implemented correctly"
            )

    def print_results(self):
        """Print validation results."""
        print("\n" + "="*80)
        print("VALIDATION RESULTS")
        print("="*80 + "\n")

        if self.info:
            print("[OK] PASSED CHECKS:")
            for msg in self.info:
                # Remove checkmarks from info messages
                msg = msg.replace('✓', '[OK]')
                print(f"  {msg}")
            print()

        if self.warnings:
            print("[WARN] WARNINGS:")
            for msg in self.warnings:
                print(f"  {msg}")
            print()

        if self.errors:
            print("[ERROR] ERRORS:")
            for msg in self.errors:
                print(f"  {msg}")
            print()

        # Overall status
        if not self.errors and not self.warnings:
            print("[OK] VALIDATION PASSED - Recording is complete and correct")
        elif not self.errors:
            print("[OK] VALIDATION PASSED - Recording is complete (with warnings)")
        else:
            print("[ERROR] VALIDATION FAILED - Recording has errors")

        print("\n" + "="*80)


def main():
    if len(sys.argv) != 2:
        print("Usage: python validate_recording.py <recording.json>")
        sys.exit(1)

    recording_file = Path(sys.argv[1])

    if not recording_file.exists():
        print(f"Error: Recording file not found: {recording_file}")
        sys.exit(1)

    validator = RecordingValidator(recording_file)
    success = validator.validate()

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
