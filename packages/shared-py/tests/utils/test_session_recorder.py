#!/usr/bin/env python3
"""Tests for session_recorder.py"""

import os

from popkit_shared.utils.session_recorder import SessionRecorder


def test_record_subagent_completion(tmp_path):
    """Test recording subagent completion with transcript data."""
    # Arrange
    os.environ["POPKIT_RECORD"] = "true"
    recorder = SessionRecorder()
    recorder.recordings_dir = tmp_path  # Override for testing
    recorder._init_recording()

    # Clear any pre-existing events from loaded recording
    recorder.events.clear()
    recorder.sequence_counter = 0

    # Act
    recorder.record_subagent_completion(
        subagent_id="agent_123",
        tool_count=5,
        input_tokens=1200,
        output_tokens=800,
        total_tokens=2000,
        tool_details=[
            {"tool_use_id": "tool_1", "tool_name": "Read"},
            {"tool_use_id": "tool_2", "tool_name": "Write"},
        ],
    )

    # Assert
    assert len(recorder.events) == 1  # Only the subagent_completion event
    event = recorder.events[0]
    assert event["type"] == "subagent_completion"
    assert event["subagent_id"] == "agent_123"
    assert event["tool_count"] == 5
    assert event["token_usage"]["total_tokens"] == 2000
    assert len(event["tool_details"]) == 2


def test_record_cross_model_review(tmp_path):
    """Test recording outside-voice review lifecycle events."""
    os.environ["POPKIT_RECORD"] = "true"
    recorder = SessionRecorder()
    recorder.recordings_dir = tmp_path
    recorder._init_recording()

    recorder.events.clear()

    recorder.record_cross_model_review(
        "completed",
        {
            "requested_by_provider": "claude-code",
            "reviewer_provider": "codex",
            "verdict": "approve",
        },
    )

    assert len(recorder.events) == 1
    event = recorder.events[0]
    assert event["type"] == "cross_model_review_completed"
    assert event["requested_by_provider"] == "claude-code"
    assert event["reviewer_provider"] == "codex"
    assert event["verdict"] == "approve"
