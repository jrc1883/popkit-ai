#!/usr/bin/env python3
"""
Graceful shutdown orchestration for Power Mode.

Issue #271: add SIGTERM -> wait(timeout) -> SIGKILL shutdown flow with
request/response correlation and cleanup hooks.
"""

import asyncio
import inspect
import json
import logging
import os
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional

from execution_spine import (
    ExecutionArtifact,
    ExecutionStatus,
    SandboxBackend,
    ValidationCheck,
    ValidationStatus,
    create_execution_lane_result,
    score_execution_lane_result,
)
from lifecycle import AgentLifecycle, AgentState
from protocol import MessageFactory, ProtocolMessage

logger = logging.getLogger(__name__)
_plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA")
DEFAULT_STATE_FILE = (
    Path(_plugin_data) / "power-mode-state.json"
    if _plugin_data
    else Path.home() / ".claude" / "popkit" / "power-mode-state.json"
)


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _is_timeout_error(exc: Exception) -> bool:
    return isinstance(exc, TimeoutError) or exc.__class__.__name__ == "TimeoutExpired"


@dataclass
class ShutdownSummary:
    """Structured shutdown result for coordinator diagnostics."""

    total_agents: int
    graceful_exits: List[str] = field(default_factory=list)
    forced_exits: List[str] = field(default_factory=list)
    request_ids: Dict[str, str] = field(default_factory=dict)
    cleanup_called: bool = False
    events: List[str] = field(default_factory=list)
    execution_result: Optional[Dict[str, Any]] = None
    execution_result_score: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "total_agents": self.total_agents,
            "graceful_exits": self.graceful_exits,
            "forced_exits": self.forced_exits,
            "request_ids": self.request_ids,
            "cleanup_called": self.cleanup_called,
            "events": self.events,
        }
        if self.execution_result is not None:
            data["execution_result"] = self.execution_result
        if self.execution_result_score is not None:
            data["execution_result_score"] = self.execution_result_score
        return data


class GracefulShutdownManager:
    """Coordinate orderly power-mode shutdown with timeout escalation."""

    def __init__(
        self,
        processes: Dict[str, Any],
        lifecycle: Optional[AgentLifecycle] = None,
        message_dispatcher: Optional[
            Callable[[str, ProtocolMessage], Optional[Awaitable[None]]]
        ] = None,
        cleanup_callback: Optional[Callable[[], Optional[Awaitable[None]]]] = None,
        state_file: Optional[Path] = None,
    ):
        self.processes = processes
        self.lifecycle = lifecycle
        self.message_dispatcher = message_dispatcher
        self.cleanup_callback = cleanup_callback
        self.state_file = state_file or DEFAULT_STATE_FILE
        self.sent_requests: Dict[str, ProtocolMessage] = {}

    def running_agents(self) -> List[str]:
        """Return all tracked agents that have not been marked EXITED."""
        if not self.lifecycle:
            return list(self.processes.keys())

        running: List[str] = []
        for agent in self.processes.keys():
            state = self.lifecycle.get_state(agent)
            if state is None or state != AgentState.EXITED:
                running.append(agent)
        return running

    async def send_shutdown_request(
        self,
        agent: str,
        reason: str = "User requested shutdown",
    ) -> ProtocolMessage:
        """Create and optionally dispatch shutdown request message."""
        message = MessageFactory.create_shutdown_request(
            sender_id="coordinator",
            reason=reason,
            to_agent=agent,
        )
        self.sent_requests[agent] = message

        logger.debug("Sending shutdown request to %s (request_id=%s)", agent, message.request_id)

        if self.lifecycle:
            state = self.lifecycle.get_state(agent)
            if state is None:
                self.lifecycle.set_state(agent, AgentState.SPAWNED)
                self.lifecycle.set_state(agent, AgentState.RUNNING)
            if self.lifecycle.can_transition(agent, AgentState.AWAITING_APPROVAL):
                self.lifecycle.set_state(agent, AgentState.AWAITING_APPROVAL)
            self.lifecycle.emit(
                "shutdown:request",
                agent,
                request_id=message.request_id,
                reason=reason,
            )

        if self.message_dispatcher:
            dispatch_result = self.message_dispatcher(agent, message)
            if inspect.isawaitable(dispatch_result):
                _ = await dispatch_result

        return message

    async def shutdown(
        self,
        timeout_seconds: float = 10.0,
        reason: str = "User requested shutdown",
    ) -> Dict[str, Any]:
        """
        Graceful shutdown sequence:
        1) send shutdown request to each running agent
        2) send SIGTERM (terminate) and wait up to timeout for exit
        3) force-kill stragglers with SIGKILL (kill)
        4) clean up filesystem state and execute optional callback
        """
        agents = self.running_agents()
        summary = ShutdownSummary(total_agents=len(agents))
        logger.info(
            "Initiating graceful shutdown for %d agent(s), timeout=%ss",
            len(agents),
            timeout_seconds,
        )

        for agent in agents:
            msg = await self.send_shutdown_request(agent, reason=reason)
            summary.request_ids[agent] = msg.request_id or ""
            summary.events.append(f"request:{agent}")

        for agent in agents:
            proc = self.processes.get(agent)
            if proc is None:
                logger.warning("No process handle found for agent %s; marking as exited", agent)
                summary.events.append(f"missing-process:{agent}")
                self._mark_exited(agent)
                continue

            self._send_terminate(proc, agent)
            exited = await self._wait_for_exit(proc, timeout_seconds)

            if exited:
                summary.graceful_exits.append(agent)
                summary.events.append(f"graceful:{agent}")
                logger.info("Agent %s exited gracefully", agent)
            else:
                self._force_kill(proc, agent)
                summary.forced_exits.append(agent)
                summary.events.append(f"forced:{agent}")
                logger.warning("Agent %s exceeded timeout and was force-killed", agent)

            self._mark_exited(agent)

        await self._cleanup_filesystem_state(summary)
        await self._run_cleanup_callback(summary)
        logger.info(
            "Shutdown complete: graceful=%d forced=%d",
            len(summary.graceful_exits),
            len(summary.forced_exits),
        )
        return summary.to_dict()

    async def _wait_for_exit(self, process: Any, timeout_seconds: float) -> bool:
        """Wait for process exit up to timeout."""
        wait_fn = getattr(process, "wait", None)
        if not callable(wait_fn):
            return True

        if inspect.iscoroutinefunction(wait_fn):
            try:
                await asyncio.wait_for(wait_fn(), timeout=timeout_seconds)
                return True
            except TimeoutError:
                return False

        try:
            signature = inspect.signature(wait_fn)
        except (TypeError, ValueError):
            signature = None

        if signature and "timeout" in signature.parameters:
            try:
                wait_fn(timeout=timeout_seconds)
                return True
            except Exception as exc:
                if _is_timeout_error(exc):
                    return False
                raise

        poll_fn = getattr(process, "poll", None)
        if callable(poll_fn):
            deadline = time.monotonic() + timeout_seconds
            while time.monotonic() < deadline:
                if poll_fn() is not None:
                    return True
                await asyncio.sleep(0.05)
            return False

        try:
            await asyncio.wait_for(asyncio.to_thread(wait_fn), timeout=timeout_seconds)
            return True
        except TimeoutError:
            return False

    def _send_terminate(self, process: Any, agent: str) -> None:
        terminate_fn = getattr(process, "terminate", None)
        if callable(terminate_fn):
            terminate_fn()
            logger.debug("SIGTERM sent to %s", agent)

    def _force_kill(self, process: Any, agent: str) -> None:
        """Force terminate a process after graceful wait timeout."""
        kill_fn = getattr(process, "kill", None)
        if callable(kill_fn):
            kill_fn()
            logger.debug("SIGKILL sent to %s", agent)
            return

        terminate_fn = getattr(process, "terminate", None)
        if callable(terminate_fn):
            terminate_fn()
            logger.debug("Fallback terminate used for %s (no kill method)", agent)

    def _mark_exited(self, agent: str) -> None:
        if not self.lifecycle:
            return

        state = self.lifecycle.get_state(agent)
        if state is None:
            self.lifecycle.set_state(agent, AgentState.SPAWNED)
            self.lifecycle.set_state(agent, AgentState.RUNNING)

        if self.lifecycle.can_transition(agent, AgentState.EXITED):
            self.lifecycle.set_state(agent, AgentState.EXITED)

    async def _cleanup_filesystem_state(self, summary: ShutdownSummary) -> None:
        state: Dict[str, Any] = {}
        if self.state_file.exists():
            try:
                state = json.loads(self.state_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                logger.warning("State file is not valid JSON; rebuilding %s", self.state_file)
                state = {}

        state["active"] = False
        state["deactivated_at"] = _utc_timestamp()
        state["shutdown"] = {
            "graceful_exits": list(summary.graceful_exits),
            "forced_exits": list(summary.forced_exits),
            "request_ids": dict(summary.request_ids),
        }
        self._attach_execution_result(state, summary)

        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(state, indent=2), encoding="utf-8")
        summary.cleanup_called = True
        summary.events.append("cleanup:filesystem")
        logger.debug("Filesystem shutdown state written to %s", self.state_file)

    async def _run_cleanup_callback(self, summary: ShutdownSummary) -> None:
        if not self.cleanup_callback:
            return

        cleanup_result = self.cleanup_callback()
        if inspect.isawaitable(cleanup_result):
            _ = await cleanup_result

        summary.cleanup_called = True
        summary.events.append("cleanup:callback")
        logger.debug("Cleanup callback executed")

    def _attach_execution_result(
        self,
        state: Dict[str, Any],
        summary: ShutdownSummary,
    ) -> None:
        """Attach the canonical execution result to the final state snapshot."""
        result = create_execution_lane_result(
            objective=str(state.get("objective") or "Power Mode session"),
            sandbox_backend=_sandbox_backend_from_state(state),
            status=(ExecutionStatus.FAILED if summary.forced_exits else ExecutionStatus.SUCCEEDED),
            branch=_optional_string(state.get("branch")),
            worktree_path=_optional_string(state.get("worktree_path")),
            log_path=_optional_string(state.get("log_path")),
            provider_run_id=_optional_string(state.get("provider_run_id")),
            commits=[str(commit) for commit in (state.get("commits") or [])],
            artifacts=[
                ExecutionArtifact(
                    kind="state",
                    path=str(self.state_file),
                    description="Power Mode state file updated at shutdown",
                )
            ],
            validation=[
                ValidationCheck(
                    name="graceful-shutdown",
                    status=(
                        ValidationStatus.FAILED if summary.forced_exits else ValidationStatus.PASSED
                    ),
                    summary=(
                        f"{len(summary.graceful_exits)} graceful exit(s), "
                        f"{len(summary.forced_exits)} forced exit(s)"
                    ),
                )
            ],
            summary=(
                f"Power Mode shutdown completed for {summary.total_agents} agent(s): "
                f"{len(summary.graceful_exits)} graceful, "
                f"{len(summary.forced_exits)} forced."
            ),
            next_action=(
                "Review forced exits before continuing."
                if summary.forced_exits
                else "Review execution artifacts and continue with the next lane."
            ),
            started_at=str(state.get("started_at") or _utc_timestamp()),
            completed_at=str(state["deactivated_at"]),
            metadata={
                "session_id": state.get("session_id"),
                "mode": state.get("mode"),
                "issues": state.get("issues") or [],
                "shutdown": state["shutdown"],
            },
        )
        result_data = result.to_dict()
        score = score_execution_lane_result(result)
        state["execution_result"] = result_data
        state["execution_result_score"] = score
        summary.execution_result = result_data
        summary.execution_result_score = score


def _sandbox_backend_from_state(state: Dict[str, Any]) -> SandboxBackend:
    mode = str(state.get("sandbox_backend") or state.get("mode") or "").lower()
    if "e2b" in mode:
        return SandboxBackend.E2B
    if "worktree" in mode or "local" in mode:
        return SandboxBackend.LOCAL_WORKTREE
    if "vercel" in mode:
        return SandboxBackend.VERCEL_SANDBOX
    if "cloudflare" in mode:
        return SandboxBackend.CLOUDFLARE_SANDBOX
    return SandboxBackend.NONE


def _optional_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value)
    return text or None
