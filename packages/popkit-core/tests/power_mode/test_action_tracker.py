#!/usr/bin/env python3
"""Tests for Issue #270 action tracker."""

import sys
from pathlib import Path

POWER_MODE_DIR = Path(__file__).resolve().parents[2] / "power-mode"
sys.path.insert(0, str(POWER_MODE_DIR))

from action_tracker import ActionTracker, register_actions_endpoint  # noqa: E402
from lifecycle import AgentLifecycle, AgentState  # noqa: E402


def test_permission_and_plan_requests_populate_pending_approvals():
    lifecycle = AgentLifecycle()
    tracker = ActionTracker()
    tracker.attach(lifecycle)

    lifecycle.mark_permission_requested("agent-1", "req-perm", tool_name="Write")
    lifecycle.mark_plan_approval_requested(
        "agent-2", "req-plan", summary="Refactor queue"
    )

    state = tracker.get_dashboard_state()
    assert state["totals"]["pending_approvals"] == 2
    by_type = {item["type"]: item for item in state["pending_approvals"]}
    assert by_type["permission"]["action_url"] == "/api/agents/agent-1/approve/req-perm"
    assert by_type["plan"]["action_url"] == "/api/plans/agent-2/approve/req-plan"


def test_idle_agents_are_removed_when_state_changes():
    lifecycle = AgentLifecycle()
    tracker = ActionTracker()
    tracker.attach(lifecycle)

    lifecycle.set_state("agent-1", AgentState.SPAWNED)
    lifecycle.set_state("agent-1", AgentState.RUNNING)
    lifecycle.set_state("agent-1", AgentState.IDLE, reason="Awaiting work")

    state = tracker.get_dashboard_state()
    assert state["totals"]["idle_agents"] == 1
    assert state["idle_agents"][0]["action_url"] == "/api/agents/agent-1/assign"

    lifecycle.set_state("agent-1", AgentState.RUNNING)
    state = tracker.get_dashboard_state()
    assert state["totals"]["idle_agents"] == 0


def test_unassigned_task_tracking_and_assignment():
    lifecycle = AgentLifecycle()
    tracker = ActionTracker()
    tracker.attach(lifecycle)

    tracker.add_unassigned_task("task-1", "Fix failing lint check", priority="high")
    state = tracker.get_dashboard_state()
    assert state["totals"]["unassigned_tasks"] == 1
    assert state["unassigned_tasks"][0]["action_url"] == "/api/tasks/task-1/assign"

    lifecycle.emit("task:assigned", "coordinator", task_id="task-1", assignee="agent-7")
    state = tracker.get_dashboard_state()
    assert state["totals"]["unassigned_tasks"] == 0


def test_resolve_approval_removes_pending_entry():
    lifecycle = AgentLifecycle()
    tracker = ActionTracker()
    tracker.attach(lifecycle)

    lifecycle.mark_permission_requested("agent-3", "req-3", tool_name="Bash")
    removed = tracker.resolve_approval("req-3")

    assert removed is not None
    assert removed["request_id"] == "req-3"
    assert tracker.get_dashboard_state()["totals"]["pending_approvals"] == 0


def test_register_actions_endpoint_returns_live_dashboard_state():
    class FakeApp:
        def __init__(self):
            self.routes = {}

        def get(self, path):
            def decorator(fn):
                self.routes[path] = fn
                return fn

            return decorator

    tracker = ActionTracker()
    tracker.add_unassigned_task("task-2", "Write docs")

    app = FakeApp()
    register_actions_endpoint(app, tracker)
    response = app.routes["/api/actions"]()

    assert response["totals"]["unassigned_tasks"] == 1
    assert response["unassigned_tasks"][0]["task_id"] == "task-2"
