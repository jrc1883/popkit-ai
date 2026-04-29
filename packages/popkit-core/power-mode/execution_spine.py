#!/usr/bin/env python3
"""
Execution lane result contract for PopKit's context -> sandbox -> eval spine.

This intentionally avoids binding PopKit to a specific sandbox or eval provider.
The contract gives Power Mode, worktree flows, and future sandbox adapters one
small artifact shape to emit after a lane runs.
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class ExecutionStatus(str, Enum):
    """Lifecycle status for an execution lane."""

    PLANNED = "planned"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELED = "canceled"


class SandboxBackend(str, Enum):
    """Sandbox/provider target used by an execution lane."""

    NONE = "none"
    LOCAL_WORKTREE = "local-worktree"
    E2B = "e2b"
    VERCEL_SANDBOX = "vercel-sandbox"
    CLOUDFLARE_SANDBOX = "cloudflare-sandbox"


class ValidationStatus(str, Enum):
    """Validation result for a command, eval, or reviewer check."""

    NOT_RUN = "not-run"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ExecutionArtifact:
    """File, URL, log, diff, or other artifact created by a lane."""

    kind: str
    path: str
    description: str = ""

    def to_dict(self) -> Dict[str, str]:
        return {
            "kind": self.kind,
            "path": self.path,
            "description": self.description,
        }


@dataclass
class ValidationCheck:
    """A test, eval, review, or smoke check attached to an execution lane."""

    name: str
    status: Union[ValidationStatus, str]
    command: str = ""
    summary: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.status, ValidationStatus):
            self.status = ValidationStatus(self.status)

    def to_dict(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "status": self.status.value,
            "command": self.command,
            "summary": self.summary,
        }


@dataclass
class ExecutionLaneResult:
    """Canonical result emitted by one PopKit execution lane."""

    objective: str
    status: Union[ExecutionStatus, str]
    sandbox_backend: Union[SandboxBackend, str]
    summary: str
    next_action: str
    branch: Optional[str] = None
    worktree_path: Optional[str] = None
    log_path: Optional[str] = None
    provider_run_id: Optional[str] = None
    commits: List[str] = field(default_factory=list)
    artifacts: List[Union[ExecutionArtifact, Dict[str, str]]] = field(default_factory=list)
    validation: List[Union[ValidationCheck, Dict[str, str]]] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: _utc_timestamp())
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.status, ExecutionStatus):
            self.status = ExecutionStatus(self.status)
        if not isinstance(self.sandbox_backend, SandboxBackend):
            self.sandbox_backend = SandboxBackend(self.sandbox_backend)
        self.artifacts = [
            artifact if isinstance(artifact, ExecutionArtifact) else ExecutionArtifact(**artifact)
            for artifact in self.artifacts
        ]
        self.validation = [
            check if isinstance(check, ValidationCheck) else ValidationCheck(**check)
            for check in self.validation
        ]

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "objective": self.objective,
            "status": self.status.value,
            "sandboxBackend": self.sandbox_backend.value,
            "summary": self.summary,
            "nextAction": self.next_action,
            "commits": list(self.commits),
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "validation": [check.to_dict() for check in self.validation],
            "startedAt": self.started_at,
            "metadata": dict(self.metadata),
        }

        optional_fields = {
            "branch": self.branch,
            "worktreePath": self.worktree_path,
            "logPath": self.log_path,
            "providerRunId": self.provider_run_id,
            "completedAt": self.completed_at,
        }
        data.update({key: value for key, value in optional_fields.items() if value})
        return data


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def create_execution_lane_result(
    objective: str,
    sandbox_backend: Union[SandboxBackend, str],
    status: Union[ExecutionStatus, str] = ExecutionStatus.PLANNED,
    summary: str = "",
    next_action: str = "",
    **kwargs: Any,
) -> ExecutionLaneResult:
    """Create an execution result while keeping call sites terse."""

    return ExecutionLaneResult(
        objective=objective,
        status=status,
        sandbox_backend=sandbox_backend,
        summary=summary,
        next_action=next_action,
        **kwargs,
    )


def score_execution_lane_result(result: ExecutionLaneResult) -> Dict[str, Any]:
    """
    Score whether an execution lane result is useful enough to hand off.

    This is a lightweight local gate, not a replacement for a full Evalite suite.
    It makes missing traceability visible before PopKit adopts any provider.
    """

    checks = {
        "objective": bool(result.objective.strip()),
        "sandboxBackend": isinstance(result.sandbox_backend, SandboxBackend),
        "status": isinstance(result.status, ExecutionStatus),
        "summary": bool(result.summary.strip()),
        "nextAction": bool(result.next_action.strip()),
        "trace": bool(result.commits or result.artifacts or result.log_path),
        "validation": bool(result.validation),
    }

    warnings: List[str] = []
    if result.status == ExecutionStatus.SUCCEEDED and any(
        check.status == ValidationStatus.FAILED for check in result.validation
    ):
        checks["statusMatchesValidation"] = False
    else:
        checks["statusMatchesValidation"] = True

    if result.validation and all(
        check.status == ValidationStatus.NOT_RUN for check in result.validation
    ):
        warnings.append("validation checks were recorded but not run")

    if result.status in {ExecutionStatus.PLANNED, ExecutionStatus.RUNNING}:
        warnings.append("result is not terminal yet")

    passed = [name for name, ok in checks.items() if ok]
    missing = [name for name, ok in checks.items() if not ok]
    score = round((len(passed) / len(checks)) * 100)

    return {
        "score": score,
        "passed": passed,
        "missing": missing,
        "warnings": warnings,
        "passedAll": not missing,
    }


__all__ = [
    "ExecutionArtifact",
    "ExecutionLaneResult",
    "ExecutionStatus",
    "SandboxBackend",
    "ValidationCheck",
    "ValidationStatus",
    "create_execution_lane_result",
    "score_execution_lane_result",
]
