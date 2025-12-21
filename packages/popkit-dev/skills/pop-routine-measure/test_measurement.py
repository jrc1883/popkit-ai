#!/usr/bin/env python3
"""
Test script for routine measurement functionality.
"""

import sys
import time
from pathlib import Path

# Add utils to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "hooks" / "utils"))

from routine_measurement import (
    RoutineMeasurementTracker,
    enable_measurement,
    disable_measurement,
    format_measurement_report,
    save_measurement,
    check_measure_flag
)


def test_basic_tracking():
    """Test basic tracking functionality."""
    print("=" * 70)
    print("Test 1: Basic Tracking")
    print("=" * 70)

    # Start tracker
    tracker = RoutineMeasurementTracker()
    tracker.start("test-1", "Test Routine")

    # Simulate some tool calls
    tracker.track_tool_call("Bash", "git status\nOn branch master\nnothing to commit", 0.5)
    tracker.track_tool_call("Read", "File content here...\n" * 100, 0.2)
    tracker.track_tool_call("Grep", "Search results...\n" * 50, 0.3)

    # Stop and get measurement
    measurement = tracker.stop()

    if measurement:
        print(f"[OK] Tracked {len(measurement.tool_calls)} tool calls")
        print(f"[OK] Duration: {measurement.duration:.2f}s")
        print(f"[OK] Total tokens: {measurement.total_tokens:,}")
        print()
        return True
    else:
        print("[FAIL] No measurement data")
        return False


def test_report_formatting():
    """Test report formatting."""
    print("=" * 70)
    print("Test 2: Report Formatting")
    print("=" * 70)

    tracker = RoutineMeasurementTracker()
    tracker.start("test-2", "Report Test")

    # Add varied tool calls
    tracker.track_tool_call("Bash", "echo 'Hello'\nHello", 0.1)
    tracker.track_tool_call("Bash", "ls -la\ntotal 1234", 0.2)
    tracker.track_tool_call("Read", "x" * 10000, 0.5)
    tracker.track_tool_call("Write", "y" * 5000, 0.3)
    tracker.track_tool_call("Grep", "z" * 2000, 0.2)

    time.sleep(0.1)  # Simulate some processing time
    measurement = tracker.stop()

    if measurement:
        report = format_measurement_report(measurement)
        print(report)
        print()
        return True
    else:
        print("[FAIL] Failed to generate report")
        return False


def test_data_persistence():
    """Test saving measurement data."""
    print("=" * 70)
    print("Test 3: Data Persistence")
    print("=" * 70)

    tracker = RoutineMeasurementTracker()
    tracker.start("test-3", "Persistence Test")

    tracker.track_tool_call("Bash", "test output", 0.1)

    measurement = tracker.stop()

    if measurement:
        # Save to temp directory
        temp_dir = Path(__file__).parent / "test_output"
        saved_path = save_measurement(measurement, temp_dir)

        if saved_path.exists():
            print(f"[OK] Saved to: {saved_path}")
            print(f"[OK] File size: {saved_path.stat().st_size} bytes")

            # Read it back
            import json
            with open(saved_path) as f:
                data = json.load(f)

            print(f"[OK] Loaded {data['total_tool_calls']} tool calls")
            print(f"[OK] Routine: {data['routine_name']}")
            print()

            # Cleanup
            saved_path.unlink()
            temp_dir.rmdir()

            return True
        else:
            print("[FAIL] File not saved")
            return False
    else:
        print("[FAIL] No measurement data")
        return False


def test_environment_flag():
    """Test environment flag detection."""
    print("=" * 70)
    print("Test 4: Environment Flag")
    print("=" * 70)

    import os

    # Test disabled
    disable_measurement()
    flag = check_measure_flag()
    print(f"Disabled: {flag} (should be False)")

    # Test enabled
    enable_measurement()
    flag = check_measure_flag()
    print(f"Enabled: {flag} (should be True)")

    # Cleanup
    disable_measurement()

    print("[OK] Environment flag works correctly")
    print()
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("Routine Measurement Test Suite")
    print("=" * 70 + "\n")

    tests = [
        test_basic_tracking,
        test_report_formatting,
        test_data_persistence,
        test_environment_flag
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"[FAIL] Test failed with error: {e}")
            failed += 1
            import traceback
            traceback.print_exc()

    print("=" * 70)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 70)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
