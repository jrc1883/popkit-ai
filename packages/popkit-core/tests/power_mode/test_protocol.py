#!/usr/bin/env python3
"""Tests for Issue #268 structured message protocol."""

import sys
from pathlib import Path

import pytest

POWER_MODE_DIR = Path(__file__).resolve().parents[2] / "power-mode"
sys.path.insert(0, str(POWER_MODE_DIR))

from protocol import (  # noqa: E402
    MessageFactory,
    MessageType,
    ProtocolMessage,
    ProtocolValidationError,
    create_objective,
    is_response_for,
)


def test_permission_request_response_have_matching_request_ids():
    request = MessageFactory.create_permission_request(
        agent_name="agent-1",
        content="Need Write permission for docs",
    )

    response = MessageFactory.create_permission_response(
        agent_name="coordinator",
        request_id=request.request_id or "",
        approved=True,
        reason="Approved",
    )

    assert request.request_id
    assert response.request_id == request.request_id
    assert is_response_for(response, request)


def test_request_response_validation_requires_request_id():
    with pytest.raises(ProtocolValidationError):
        ProtocolMessage(
            type=MessageType.PERMISSION_RESPONSE,
            from_agent="coordinator",
            payload={"approved": True, "reason": "ok"},
        )


def test_unknown_message_type_is_rejected():
    with pytest.raises(ProtocolValidationError):
        ProtocolMessage.from_dict(
            {
                "type": "totally:unknown",
                "from_agent": "agent-1",
                "message_id": "msg-1",
                "timestamp": "2026-02-16T00:00:00+00:00",
                "payload": {},
            }
        )


def test_broadcast_round_trip_serialization():
    message = MessageFactory.create_broadcast(
        sender_id="coordinator",
        content="Session initialized",
        metadata={"session_id": "abc123"},
    )

    parsed = ProtocolMessage.from_json(message.to_json())

    assert parsed.type == MessageType.BROADCAST
    assert parsed.payload["content"] == "Session initialized"
    assert parsed.payload["metadata"]["session_id"] == "abc123"


def test_task_assignment_requires_description():
    with pytest.raises(ProtocolValidationError):
        ProtocolMessage(
            type=MessageType.TASK_ASSIGNED,
            from_agent="coordinator",
            to_agent="agent-2",
            payload={"task_id": "task-42"},
        )


def test_create_objective_preserves_constraints():
    objective = create_objective(
        description="Build auth",
        success_criteria=["Login endpoint works"],
        phases=["explore", "implement"],
        file_patterns=["src/auth/**"],
        restricted_tools=["Write:.env"],
    )

    data = objective.to_dict()
    assert data["description"] == "Build auth"
    assert data["success_criteria"] == ["Login endpoint works"]
    assert data["phases"] == ["explore", "implement"]
    assert data["file_patterns"] == ["src/auth/**"]
    assert data["restricted_tools"] == ["Write:.env"]
