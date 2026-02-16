#!/usr/bin/env python3
"""
Power Mode agent lifecycle event system.

Issue #269 introduces event-driven state transitions so coordinator logic can
stay decoupled from side effects (logging, dashboards, automation hooks).
"""

from collections import defaultdict
from datetime import datetime, timezone
from enum import Enum
from threading import RLock
from typing import Any, Callable, DefaultDict, Dict, List, Optional, Union


class LifecycleEvent(str, Enum):
    """Supported lifecycle event names."""

    AGENT_SPAWNED = "agent:spawned"
    AGENT_IDLE = "agent:idle"
    AGENT_STATE_CHANGED = "agent:state_changed"
    PLAN_APPROVAL_REQUEST = "plan:approval_request"
    PERMISSION_REQUEST = "permission:request"
    TASK_COMPLETED = "task:completed"
    AGENT_EXITED = "agent:exited"


class AgentState(str, Enum):
    """Canonical agent execution states."""

    SPAWNED = "spawned"
    RUNNING = "running"
    IDLE = "idle"
    PLANNING = "planning"
    AWAITING_APPROVAL = "awaiting_approval"
    EXITED = "exited"


VALID_STATE_TRANSITIONS: Dict[AgentState, set[AgentState]] = {
    AgentState.SPAWNED: {AgentState.RUNNING, AgentState.EXITED},
    AgentState.RUNNING: {
        AgentState.IDLE,
        AgentState.PLANNING,
        AgentState.AWAITING_APPROVAL,
        AgentState.EXITED,
    },
    AgentState.IDLE: {AgentState.RUNNING, AgentState.PLANNING, AgentState.EXITED},
    AgentState.PLANNING: {
        AgentState.RUNNING,
        AgentState.AWAITING_APPROVAL,
        AgentState.EXITED,
    },
    AgentState.AWAITING_APPROVAL: {AgentState.RUNNING, AgentState.EXITED},
    AgentState.EXITED: set(),
}


LifecycleHandler = Callable[[str], None]


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalize_event(event: Union[LifecycleEvent, str]) -> str:
    return event.value if isinstance(event, LifecycleEvent) else str(event)


def _normalize_state(state: Union[AgentState, str]) -> AgentState:
    if isinstance(state, AgentState):
        return state
    return AgentState(state)


class AgentLifecycle:
    """Event emitter + state machine for power-mode agent lifecycle."""

    def __init__(self, max_history: int = 500):
        self.max_history = max_history
        self._handlers: DefaultDict[str, List[Callable[..., None]]] = defaultdict(list)
        self._states: Dict[str, AgentState] = {}
        self._history: List[Dict[str, Any]] = []
        self._lock = RLock()

    def on(
        self, event: Union[LifecycleEvent, str], handler: Callable[..., None]
    ) -> None:
        """Register an event handler."""
        event_name = _normalize_event(event)
        with self._lock:
            self._handlers[event_name].append(handler)

    def off(
        self, event: Union[LifecycleEvent, str], handler: Callable[..., None]
    ) -> None:
        """Unregister an event handler."""
        event_name = _normalize_event(event)
        with self._lock:
            handlers = self._handlers.get(event_name, [])
            if handler in handlers:
                handlers.remove(handler)

    def emit(self, event: Union[LifecycleEvent, str], agent: str, **data: Any) -> int:
        """Emit an event and invoke subscribed handlers."""
        event_name = _normalize_event(event)

        with self._lock:
            handlers = list(self._handlers.get(event_name, []))
            self._history.append(
                {
                    "timestamp": _utc_timestamp(),
                    "event": event_name,
                    "agent": agent,
                    "data": data,
                }
            )
            if len(self._history) > self.max_history:
                self._history = self._history[-self.max_history :]

        for handler in handlers:
            handler(agent, **data)

        return len(handlers)

    def can_transition(
        self,
        agent: str,
        new_state: Union[AgentState, str],
    ) -> bool:
        """Check whether an agent can move to a new state."""
        target = _normalize_state(new_state)
        current = self._states.get(agent)

        if current is None:
            return target == AgentState.SPAWNED
        if current == target:
            return True

        return target in VALID_STATE_TRANSITIONS[current]

    def set_state(
        self,
        agent: str,
        new_state: Union[AgentState, str],
        **metadata: Any,
    ) -> AgentState:
        """Transition an agent to a new state and emit lifecycle events."""
        target = _normalize_state(new_state)

        if not self.can_transition(agent, target):
            current = self._states.get(agent)
            current_value = current.value if current else "none"
            raise ValueError(
                f"Invalid state transition for {agent}: {current_value} -> {target.value}"
            )

        old_state = self._states.get(agent)
        self._states[agent] = target

        self.emit(
            LifecycleEvent.AGENT_STATE_CHANGED,
            agent,
            old_state=old_state.value if old_state else None,
            new_state=target.value,
            **metadata,
        )

        if target == AgentState.SPAWNED:
            self.emit(LifecycleEvent.AGENT_SPAWNED, agent, **metadata)
        elif target == AgentState.IDLE:
            self.emit(LifecycleEvent.AGENT_IDLE, agent, **metadata)
        elif target == AgentState.EXITED:
            self.emit(LifecycleEvent.AGENT_EXITED, agent, **metadata)

        return target

    def mark_permission_requested(
        self, agent: str, request_id: str, **data: Any
    ) -> None:
        """Emit permission request event."""
        self.emit(
            LifecycleEvent.PERMISSION_REQUEST,
            agent,
            request_id=request_id,
            **data,
        )

    def mark_plan_approval_requested(
        self, agent: str, request_id: str, **data: Any
    ) -> None:
        """Emit plan approval request event."""
        self.emit(
            LifecycleEvent.PLAN_APPROVAL_REQUEST,
            agent,
            request_id=request_id,
            **data,
        )

    def mark_task_completed(self, agent: str, task_id: str, **data: Any) -> None:
        """Emit task completed event."""
        self.emit(
            LifecycleEvent.TASK_COMPLETED,
            agent,
            task_id=task_id,
            **data,
        )

    def get_state(self, agent: str) -> Optional[AgentState]:
        """Get current state for an agent."""
        return self._states.get(agent)

    def running_agents(self) -> List[str]:
        """Get all currently non-exited agents."""
        return [
            agent for agent, state in self._states.items() if state != AgentState.EXITED
        ]

    def recent_events(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Return recent event history entries."""
        if limit <= 0:
            return []
        return self._history[-limit:]

    def snapshot(self) -> Dict[str, Any]:
        """Return JSON-serializable lifecycle snapshot."""
        return {
            "states": {agent: state.value for agent, state in self._states.items()},
            "event_count": len(self._history),
            "recent_events": self.recent_events(limit=10),
        }
