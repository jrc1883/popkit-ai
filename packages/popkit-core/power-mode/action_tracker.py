#!/usr/bin/env python3
"""
Action tracker for Power Mode dashboard state.

Issue #270: maintain fast, in-memory action state driven by lifecycle events
so dashboard/API queries avoid repeated file I/O.
"""

from datetime import datetime, timezone
from threading import RLock
from typing import Any, Dict, List, Optional

from lifecycle import AgentLifecycle, LifecycleEvent


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


class ActionTracker:
    """Track approvals, idle agents, and unassigned tasks in memory."""

    def __init__(self, api_base: str = "/api"):
        self.api_base = api_base.rstrip("/")
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}
        self.idle_agents: Dict[str, Dict[str, Any]] = {}
        self.unassigned_tasks: Dict[str, Dict[str, Any]] = {}
        self._lifecycle: Optional[AgentLifecycle] = None
        self._attached = False
        self._updated_at = _utc_timestamp()
        self._lock = RLock()

    def attach(self, lifecycle: AgentLifecycle) -> None:
        """Subscribe to lifecycle events that update dashboard state."""
        if self._attached and self._lifecycle is lifecycle:
            return
        if self._attached and self._lifecycle is not None:
            self.detach()

        self._lifecycle = lifecycle
        lifecycle.on(LifecycleEvent.PERMISSION_REQUEST, self.on_permission_request)
        lifecycle.on(LifecycleEvent.PLAN_APPROVAL_REQUEST, self.on_plan_request)
        lifecycle.on(LifecycleEvent.AGENT_IDLE, self.on_agent_idle)
        lifecycle.on(LifecycleEvent.AGENT_STATE_CHANGED, self.on_agent_state_changed)
        lifecycle.on(LifecycleEvent.TASK_COMPLETED, self.on_task_completed)
        lifecycle.on("task:unassigned", self.on_task_unassigned)
        lifecycle.on("task:assigned", self.on_task_assigned)
        self._attached = True

    def detach(self) -> None:
        """Unsubscribe from lifecycle events."""
        if not self._attached or self._lifecycle is None:
            return

        lifecycle = self._lifecycle
        lifecycle.off(LifecycleEvent.PERMISSION_REQUEST, self.on_permission_request)
        lifecycle.off(LifecycleEvent.PLAN_APPROVAL_REQUEST, self.on_plan_request)
        lifecycle.off(LifecycleEvent.AGENT_IDLE, self.on_agent_idle)
        lifecycle.off(LifecycleEvent.AGENT_STATE_CHANGED, self.on_agent_state_changed)
        lifecycle.off(LifecycleEvent.TASK_COMPLETED, self.on_task_completed)
        lifecycle.off("task:unassigned", self.on_task_unassigned)
        lifecycle.off("task:assigned", self.on_task_assigned)

        self._lifecycle = None
        self._attached = False

    def on_permission_request(self, agent: str, **msg: Any) -> None:
        request_id = str(msg.get("request_id") or "")
        if not request_id:
            return

        tool_name = msg.get("tool_name", "unknown")
        with self._lock:
            self.pending_approvals[request_id] = {
                "request_id": request_id,
                "type": "permission",
                "agent": agent,
                "tool": tool_name,
                "action_url": f"{self.api_base}/agents/{agent}/approve/{request_id}",
                "created_at": _utc_timestamp(),
            }
            self._touch()

    def on_plan_request(self, agent: str, **msg: Any) -> None:
        request_id = str(msg.get("request_id") or "")
        if not request_id:
            return

        summary = msg.get("summary") or msg.get("plan_summary") or ""
        with self._lock:
            self.pending_approvals[request_id] = {
                "request_id": request_id,
                "type": "plan",
                "agent": agent,
                "summary": summary,
                "action_url": f"{self.api_base}/plans/{agent}/approve/{request_id}",
                "created_at": _utc_timestamp(),
            }
            self._touch()

    def on_agent_idle(self, agent: str, **msg: Any) -> None:
        with self._lock:
            self.idle_agents[agent] = {
                "agent": agent,
                "reason": msg.get("reason", ""),
                "action_url": f"{self.api_base}/agents/{agent}/assign",
                "since": _utc_timestamp(),
            }
            self._touch()

    def on_agent_state_changed(self, agent: str, **msg: Any) -> None:
        """Remove agent from idle list when they are no longer idle."""
        new_state = str(msg.get("new_state") or "")
        if new_state == "idle":
            return

        with self._lock:
            if agent in self.idle_agents:
                self.idle_agents.pop(agent, None)
                self._touch()

    def on_task_unassigned(self, _: str, **msg: Any) -> None:
        task_id = str(msg.get("task_id") or "")
        if not task_id:
            return

        with self._lock:
            self.unassigned_tasks[task_id] = {
                "task_id": task_id,
                "description": msg.get("description", ""),
                "priority": msg.get("priority", "normal"),
                "labels": msg.get("labels", []),
                "action_url": f"{self.api_base}/tasks/{task_id}/assign",
                "created_at": _utc_timestamp(),
            }
            self._touch()

    def on_task_assigned(self, _: str, **msg: Any) -> None:
        task_id = str(msg.get("task_id") or "")
        assignee = str(msg.get("assignee") or msg.get("agent") or "")

        with self._lock:
            if task_id:
                self.unassigned_tasks.pop(task_id, None)
            if assignee:
                self.idle_agents.pop(assignee, None)
            self._touch()

    def on_task_completed(self, agent: str, **msg: Any) -> None:
        task_id = str(msg.get("task_id") or "")
        with self._lock:
            if task_id:
                self.unassigned_tasks.pop(task_id, None)
            self.idle_agents.pop(agent, None)
            self._touch()

    def add_unassigned_task(
        self,
        task_id: str,
        description: str,
        priority: str = "normal",
        labels: Optional[List[str]] = None,
    ) -> None:
        """Convenience helper for coordinators that create orphaned tasks."""
        self.on_task_unassigned(
            "coordinator",
            task_id=task_id,
            description=description,
            priority=priority,
            labels=labels or [],
        )

    def resolve_approval(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Remove approval from pending set and return the removed record."""
        with self._lock:
            removed = self.pending_approvals.pop(request_id, None)
            if removed is not None:
                self._touch()
            return removed

    def get_dashboard_state(self) -> Dict[str, Any]:
        """Return current in-memory state for dashboard/API queries."""
        with self._lock:
            approvals = list(self.pending_approvals.values())
            idle = list(self.idle_agents.values())
            tasks = list(self.unassigned_tasks.values())
            total_pending = len(approvals) + len(idle)
            total_actions = total_pending + len(tasks)
            return {
                "pending_approvals": approvals,
                "idle_agents": idle,
                "unassigned_tasks": tasks,
                "totals": {
                    "pending_approvals": len(approvals),
                    "idle_agents": len(idle),
                    "unassigned_tasks": len(tasks),
                    "total_pending": total_pending,
                    "total_actions": total_actions,
                },
                "updated_at": self._updated_at,
            }

    def _touch(self) -> None:
        self._updated_at = _utc_timestamp()


def register_actions_endpoint(
    app: Any, tracker: ActionTracker, path: str = "/api/actions"
) -> Any:
    """
    Register a dashboard state endpoint on a FastAPI-compatible app.

    The app only needs a `.get(path)` decorator method. This avoids requiring
    FastAPI as a hard dependency in the core module.
    """
    get_decorator = getattr(app, "get", None)
    if not callable(get_decorator):
        raise TypeError("app must provide a callable .get(path) decorator")

    @app.get(path)
    def get_actions() -> Dict[str, Any]:
        return tracker.get_dashboard_state()

    return get_actions
