#!/usr/bin/env python3
"""Tests for Issue #271 graceful shutdown manager."""

import asyncio
import json
import logging
import sys
from pathlib import Path

POWER_MODE_DIR = Path(__file__).resolve().parents[2] / "power-mode"
sys.path.insert(0, str(POWER_MODE_DIR))

from lifecycle import AgentLifecycle, AgentState  # noqa: E402
from shutdown_manager import GracefulShutdownManager  # noqa: E402


class AsyncProcess:
    def __init__(self, delay: float = 0.0):
        self.delay = delay
        self.terminate_calls = 0
        self.kill_calls = 0

    async def wait(self) -> int:
        await asyncio.sleep(self.delay)
        return 0

    def terminate(self) -> None:
        self.terminate_calls += 1

    def kill(self) -> None:
        self.kill_calls += 1


def test_shutdown_graceful_exit_updates_state_file(tmp_path):
    state_file = tmp_path / "power-mode-state.json"
    state_file.write_text(
        json.dumps({"active": True, "session_id": "abc"}), encoding="utf-8"
    )

    lifecycle = AgentLifecycle()
    lifecycle.set_state("agent-1", AgentState.SPAWNED)
    lifecycle.set_state("agent-1", AgentState.RUNNING)

    observed_requests = []
    lifecycle.on(
        "shutdown:request",
        lambda agent, **data: observed_requests.append((agent, data.get("request_id"))),
    )

    process = AsyncProcess(delay=0.0)
    manager = GracefulShutdownManager(
        {"agent-1": process},
        lifecycle=lifecycle,
        state_file=state_file,
    )

    summary = asyncio.run(manager.shutdown(timeout_seconds=0.1))

    assert summary["graceful_exits"] == ["agent-1"]
    assert summary["forced_exits"] == []
    assert observed_requests and observed_requests[0][0] == "agent-1"
    assert observed_requests[0][1]
    assert process.terminate_calls == 1
    assert process.kill_calls == 0
    assert lifecycle.get_state("agent-1") == AgentState.EXITED

    saved_state = json.loads(state_file.read_text(encoding="utf-8"))
    assert saved_state["active"] is False
    assert "deactivated_at" in saved_state
    assert saved_state["shutdown"]["graceful_exits"] == ["agent-1"]


def test_shutdown_timeout_force_kills_stragglers(tmp_path):
    process = AsyncProcess(delay=1.0)
    manager = GracefulShutdownManager(
        {"agent-2": process},
        state_file=tmp_path / "power-mode-state.json",
    )

    summary = asyncio.run(manager.shutdown(timeout_seconds=0.01))

    assert summary["graceful_exits"] == []
    assert summary["forced_exits"] == ["agent-2"]
    assert process.terminate_calls == 1
    assert process.kill_calls == 1


def test_send_shutdown_request_awaits_async_dispatcher(tmp_path):
    dispatched = []

    async def dispatcher(agent: str, message) -> None:
        await asyncio.sleep(0)
        dispatched.append((agent, message.type.value, message.request_id))

    manager = GracefulShutdownManager(
        {},
        message_dispatcher=dispatcher,
        state_file=tmp_path / "power-mode-state.json",
    )

    message = asyncio.run(manager.send_shutdown_request("agent-3"))

    assert message.request_id
    assert dispatched == [("agent-3", "shutdown_request", message.request_id)]


def test_shutdown_runs_cleanup_callback(tmp_path):
    callback_state = {"called": False}

    async def cleanup() -> None:
        callback_state["called"] = True

    manager = GracefulShutdownManager(
        {},
        cleanup_callback=cleanup,
        state_file=tmp_path / "power-mode-state.json",
    )
    summary = asyncio.run(manager.shutdown(timeout_seconds=0.01))

    assert callback_state["called"] is True
    assert summary["cleanup_called"] is True
    assert "cleanup:callback" in summary["events"]


def test_shutdown_logs_sequence(caplog, tmp_path):
    process = AsyncProcess(delay=0.0)
    manager = GracefulShutdownManager(
        {"agent-4": process},
        state_file=tmp_path / "power-mode-state.json",
    )

    with caplog.at_level(logging.INFO):
        asyncio.run(manager.shutdown(timeout_seconds=0.05))

    messages = " ".join(record.getMessage() for record in caplog.records)
    assert "Initiating graceful shutdown" in messages
    assert "Shutdown complete" in messages
