#!/usr/bin/env python3
"""Test telemetry module for PopKit behavioral validation (Issue #258)."""

import json
import os
import sys
from datetime import UTC, datetime
from typing import Any


def is_test_mode() -> bool:
    """Check if running in test mode."""
    return os.getenv("TEST_MODE", "").lower() == "true"


def get_test_session_id() -> str | None:
    """Get the current test session ID."""
    return os.getenv("TEST_SESSION_ID")


def create_event(
    event_type: str, data: dict[str, Any], session_id: str | None = None
) -> dict[str, Any]:
    """Create a standardized telemetry event."""
    return {
        "type": event_type,
        "timestamp": datetime.now(UTC).isoformat(),
        "session_id": session_id or get_test_session_id(),
        "data": data,
    }


def emit_event(event: dict[str, Any]) -> None:
    """Emit a telemetry event to stdout."""
    if not is_test_mode():
        return
    try:
        print(f"TELEMETRY:{json.dumps(event)}", file=sys.stdout, flush=True)
    except Exception:
        # Best-effort fallback: ignore optional failure.
        pass


def emit_routing_decision(
    trigger: dict[str, Any],
    candidates: list[dict[str, Any]],
    selected: list[str],
    confidence: int | None = None,
    reasoning: str | None = None,
) -> None:
    """Emit a routing decision event.

    Called by agent-orchestrator.py when routing user prompts to agents.
    """
    event = create_event(
        "routing_decision",
        {
            "trigger": trigger,
            "candidates": candidates,
            "selected": selected,
            "confidence": confidence,
            "reasoning": reasoning,
        },
    )
    emit_event(event)


def emit_agent_invocation(
    agent_name: str,
    agent_id: str,
    prompt: str,
    invoked_by: str = "hook",
    background: bool = False,
    effort: str | None = None,
) -> None:
    """Emit an agent invocation start event.

    Called by agent-orchestrator.py when Task tool is invoked.
    """
    event = create_event(
        "agent_invocation_start",
        {
            "agent_name": agent_name,
            "agent_id": agent_id,
            "prompt": prompt,
            "invoked_by": invoked_by,
            "background": background,
            "effort": effort,
        },
    )
    emit_event(event)


def emit_agent_completion(
    agent_name: str,
    agent_id: str,
    status: str,
    duration_ms: int | None = None,
    exit_code: int | None = None,
    error: str | None = None,
) -> None:
    """Emit an agent invocation completion event.

    Called when an agent completes (success or failure).
    """
    event = create_event(
        "agent_invocation_complete",
        {
            "agent_name": agent_name,
            "agent_id": agent_id,
            "status": status,
            "duration_ms": duration_ms,
            "exit_code": exit_code,
            "error": error,
        },
    )
    emit_event(event)


def emit_skill_start(
    skill_name: str,
    workflow_id: str | None = None,
    invoked_by: str = "agent",
    activity_id: str | None = None,
) -> None:
    """Emit a skill start event.

    Called by skill_state.py when a skill is invoked via Skill tool.
    """
    event = create_event(
        "skill_start",
        {
            "skill_name": skill_name,
            "workflow_id": workflow_id,
            "invoked_by": invoked_by,
            "activity_id": activity_id,
        },
    )
    emit_event(event)


def emit_skill_complete(
    skill_name: str,
    workflow_id: str | None = None,
    status: str = "complete",
    tool_calls: int = 0,
    decisions_made: list[str] | None = None,
    error: str | None = None,
    duration_ms: int | None = None,
) -> None:
    """Emit a skill completion event.

    Called by skill_state.py when a skill completes.
    """
    event = create_event(
        "skill_complete",
        {
            "skill_name": skill_name,
            "workflow_id": workflow_id,
            "status": status,
            "tool_calls": tool_calls,
            "decisions_made": decisions_made or [],
            "error": error,
            "duration_ms": duration_ms,
        },
    )
    emit_event(event)


def emit_phase_transition(
    workflow_id: str,
    from_phase: str | None,
    to_phase: str,
    skill_name: str | None = None,
    tool_calls_so_far: int = 0,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Emit a workflow phase transition event.

    Called by skill_state.py when a multi-phase workflow transitions between phases.
    """
    event = create_event(
        "phase_transition",
        {
            "workflow_id": workflow_id,
            "from_phase": from_phase,
            "to_phase": to_phase,
            "skill_name": skill_name,
            "tool_calls_so_far": tool_calls_so_far,
            "metadata": metadata or {},
        },
    )
    emit_event(event)


def emit_user_decision(
    decision_id: str,
    question: str,
    selected_options: list[str],
    skill_name: str | None = None,
    workflow_id: str | None = None,
) -> None:
    """Emit a user decision event.

    Called when AskUserQuestion tool is used during skill execution.
    """
    event = create_event(
        "user_decision",
        {
            "decision_id": decision_id,
            "question": question,
            "selected_options": selected_options,
            "skill_name": skill_name,
            "workflow_id": workflow_id,
        },
    )
    emit_event(event)


def emit_tool_call(
    tool_name: str,
    tool_input: dict[str, Any],
    tool_output: str | None = None,
    agent_id: str | None = None,
    agent_name: str | None = None,
    session_id: str | None = None,
    error: str | None = None,
) -> None:
    """Emit a tool call event.

    Can be called to track individual tool usage patterns.
    """
    event = create_event(
        "tool_call",
        {
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_output": tool_output[:200] if tool_output else None,
            "agent_id": agent_id,
            "agent_name": agent_name,
            "error": error,
        },
        session_id=session_id,
    )
    emit_event(event)
