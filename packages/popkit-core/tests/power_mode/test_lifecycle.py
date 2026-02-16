#!/usr/bin/env python3
"""Tests for Issue #269 lifecycle event system."""

import sys
from pathlib import Path

import pytest

POWER_MODE_DIR = Path(__file__).resolve().parents[2] / "power-mode"
sys.path.insert(0, str(POWER_MODE_DIR))

from lifecycle import AgentLifecycle, AgentState, LifecycleEvent  # noqa: E402


def test_emit_invokes_registered_handlers():
    lifecycle = AgentLifecycle()
    seen = []

    def handler(agent: str, **_: object) -> None:
        seen.append(agent)

    lifecycle.on(LifecycleEvent.AGENT_IDLE, handler)
    lifecycle.emit(LifecycleEvent.AGENT_IDLE, "agent-1")

    assert seen == ["agent-1"]


def test_set_state_emits_state_changed_event():
    lifecycle = AgentLifecycle()
    transitions = []

    def on_state_changed(agent: str, **data: object) -> None:
        transitions.append((agent, data.get("old_state"), data.get("new_state")))

    lifecycle.on(LifecycleEvent.AGENT_STATE_CHANGED, on_state_changed)

    lifecycle.set_state("agent-1", AgentState.SPAWNED)
    lifecycle.set_state("agent-1", AgentState.RUNNING)

    assert transitions[0] == ("agent-1", None, "spawned")
    assert transitions[1] == ("agent-1", "spawned", "running")


def test_invalid_transition_raises_error():
    lifecycle = AgentLifecycle()
    lifecycle.set_state("agent-1", AgentState.SPAWNED)
    lifecycle.set_state("agent-1", AgentState.RUNNING)
    lifecycle.set_state("agent-1", AgentState.EXITED)

    with pytest.raises(ValueError):
        lifecycle.set_state("agent-1", AgentState.RUNNING)


def test_spawn_idle_exit_emit_specific_events():
    lifecycle = AgentLifecycle()
    events = []

    def on_any(agent: str, **_: object) -> None:
        events.append(agent)

    lifecycle.on(LifecycleEvent.AGENT_SPAWNED, on_any)
    lifecycle.on(LifecycleEvent.AGENT_IDLE, on_any)
    lifecycle.on(LifecycleEvent.AGENT_EXITED, on_any)

    lifecycle.set_state("agent-1", AgentState.SPAWNED)
    lifecycle.set_state("agent-1", AgentState.RUNNING)
    lifecycle.set_state("agent-1", AgentState.IDLE)
    lifecycle.set_state("agent-1", AgentState.EXITED)

    assert events == ["agent-1", "agent-1", "agent-1"]


def test_permission_and_plan_request_events_include_request_id():
    lifecycle = AgentLifecycle()
    emitted = []

    def recorder(agent: str, **data: object) -> None:
        emitted.append((agent, data.get("request_id")))

    lifecycle.on(LifecycleEvent.PERMISSION_REQUEST, recorder)
    lifecycle.on(LifecycleEvent.PLAN_APPROVAL_REQUEST, recorder)

    lifecycle.mark_permission_requested("agent-1", "req-1", tool_name="Bash")
    lifecycle.mark_plan_approval_requested("agent-1", "req-2", summary="plan")

    assert emitted == [("agent-1", "req-1"), ("agent-1", "req-2")]


def test_snapshot_is_json_serializable_shape():
    lifecycle = AgentLifecycle()
    lifecycle.set_state("agent-1", AgentState.SPAWNED)
    lifecycle.set_state("agent-1", AgentState.RUNNING)

    snapshot = lifecycle.snapshot()

    assert snapshot["states"]["agent-1"] == "running"
    assert snapshot["event_count"] >= 2
    assert isinstance(snapshot["recent_events"], list)
