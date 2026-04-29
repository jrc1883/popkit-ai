#!/usr/bin/env python3
"""Tests for the PopKit execution lane result contract."""

import sys
from pathlib import Path

POWER_MODE_DIR = Path(__file__).resolve().parents[2] / "power-mode"
sys.path.insert(0, str(POWER_MODE_DIR))

from execution_spine import (  # noqa: E402
    ExecutionArtifact,
    ExecutionStatus,
    SandboxBackend,
    ValidationCheck,
    ValidationStatus,
    create_execution_lane_result,
    score_execution_lane_result,
)


def test_execution_lane_result_serializes_canonical_shape():
    result = create_execution_lane_result(
        objective="Prototype safe execution result handoffs",
        sandbox_backend=SandboxBackend.LOCAL_WORKTREE,
        status=ExecutionStatus.SUCCEEDED,
        branch="codex/example",
        worktree_path="C:/worktrees/example",
        log_path=".popkit/runs/example.log",
        commits=["abc1234"],
        artifacts=[
            ExecutionArtifact(
                kind="doc",
                path="packages/docs/src/content/docs/concepts/execution-spine.md",
                description="Execution spine design note",
            )
        ],
        validation=[
            ValidationCheck(
                name="pytest",
                status=ValidationStatus.PASSED,
                command="python -m pytest packages/popkit-core/tests/power_mode",
                summary="Power Mode tests passed",
            )
        ],
        summary="Execution result was captured with traceability.",
        next_action="Wire this result into the lane coordinator.",
    )

    data = result.to_dict()

    assert data["status"] == "succeeded"
    assert data["sandboxBackend"] == "local-worktree"
    assert data["nextAction"] == "Wire this result into the lane coordinator."
    assert data["artifacts"][0]["kind"] == "doc"
    assert data["validation"][0]["status"] == "passed"
    assert data["branch"] == "codex/example"

    score = score_execution_lane_result(result)
    assert score["passedAll"] is True
    assert score["score"] == 100


def test_execution_lane_result_accepts_provider_backends_as_strings():
    result = create_execution_lane_result(
        objective="Run in a future provider",
        sandbox_backend="cloudflare-sandbox",
        status="blocked",
        summary="Provider adapter is not implemented yet.",
        next_action="Keep the enum but do not add a dependency.",
        artifacts=[
            {
                "kind": "decision",
                "path": "packages/docs/src/content/docs/concepts/execution-spine.md",
            }
        ],
        validation=[{"name": "adversarial-review", "status": "passed"}],
    )

    assert result.sandbox_backend == SandboxBackend.CLOUDFLARE_SANDBOX
    assert result.status == ExecutionStatus.BLOCKED
    assert result.to_dict()["sandboxBackend"] == "cloudflare-sandbox"


def test_score_execution_lane_result_flags_missing_traceability():
    result = create_execution_lane_result(
        objective="",
        sandbox_backend=SandboxBackend.NONE,
        status=ExecutionStatus.SUCCEEDED,
        summary="",
        next_action="",
    )

    score = score_execution_lane_result(result)

    assert score["passedAll"] is False
    assert score["score"] < 60
    assert "objective" in score["missing"]
    assert "summary" in score["missing"]
    assert "trace" in score["missing"]
    assert "validation" in score["missing"]


def test_score_execution_lane_result_rejects_success_with_failed_validation():
    result = create_execution_lane_result(
        objective="Ship a change",
        sandbox_backend=SandboxBackend.E2B,
        status=ExecutionStatus.SUCCEEDED,
        summary="The lane says it succeeded.",
        next_action="Fix the failing validation before handoff.",
        log_path=".popkit/runs/lane.log",
        validation=[ValidationCheck(name="unit-tests", status=ValidationStatus.FAILED)],
    )

    score = score_execution_lane_result(result)

    assert score["passedAll"] is False
    assert "statusMatchesValidation" in score["missing"]


def test_provider_backend_enum_tracks_current_and_candidate_sandboxes():
    assert SandboxBackend.E2B.value == "e2b"
    assert SandboxBackend.LOCAL_WORKTREE.value == "local-worktree"
    assert SandboxBackend.VERCEL_SANDBOX.value == "vercel-sandbox"
    assert SandboxBackend.CLOUDFLARE_SANDBOX.value == "cloudflare-sandbox"
