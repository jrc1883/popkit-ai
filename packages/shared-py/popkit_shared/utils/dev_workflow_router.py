#!/usr/bin/env python3
"""
Issue #218: Hybrid PopKit/feature-dev execution planning.

Builds an executable plan from provider resolution:
- native PopKit execution path
- delegated feature-dev path with PopKit fallback
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional

from .dev_provider_resolver import (
    DevProvider,
    DevProviderResolver,
    ProviderAvailability,
    ProviderContext,
    ProviderDecision,
    detect_feature_dev_plugin,
)

VALID_MODES = {"quick", "full"}


def _normalize_mode(mode: str) -> str:
    normalized = (mode or "").strip().lower()
    if normalized in VALID_MODES:
        return normalized
    return "full"


def _escape_for_double_quotes(value: str) -> str:
    return value.replace('"', '\\"')


@dataclass(frozen=True)
class DevWorkflowRequest:
    """Inputs for building a dev workflow execution plan."""

    task: str
    mode: str = "full"
    issue_number: Optional[int] = None
    requested_provider: DevProvider = DevProvider.AUTO
    allow_upstream: bool = True
    requires_popkit_orchestration: bool = False
    requires_github_cache: bool = False


@dataclass
class DevWorkflowPlan:
    """Executable plan for the selected development provider."""

    decision: ProviderDecision
    execution_mode: str  # "native" | "delegated"
    primary_command: str
    fallback_command: Optional[str] = None
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "decision": self.decision.to_dict(),
            "execution_mode": self.execution_mode,
            "primary_command": self.primary_command,
            "fallback_command": self.fallback_command,
            "notes": self.notes,
        }


class DevWorkflowRouter:
    """Resolve provider and build a runnable workflow plan."""

    def __init__(self, resolver: Optional[DevProviderResolver] = None):
        self.resolver = resolver or DevProviderResolver()

    def build_plan(
        self,
        request: DevWorkflowRequest,
        plugin_scan_data: Optional[Any] = None,
    ) -> DevWorkflowPlan:
        required_capabilities = set()
        if request.requires_popkit_orchestration:
            required_capabilities.add("worktree_orchestration")
        if request.requires_github_cache:
            required_capabilities.add("issue_guidance")

        availability = ProviderAvailability(
            feature_dev_available=detect_feature_dev_plugin(plugin_scan_data),
            popkit_available=True,
        )
        context = ProviderContext(
            requested_provider=request.requested_provider,
            required_capabilities=required_capabilities,
            allow_upstream=request.allow_upstream,
            workflow_mode=_normalize_mode(request.mode),
        )
        decision = self.resolver.resolve(context, availability)
        normalized_mode = _normalize_mode(request.mode)

        popkit_command = self._build_popkit_command(
            task=request.task,
            mode=normalized_mode,
            issue_number=request.issue_number,
        )
        notes: List[str] = []
        if request.task.strip():
            notes.append(f"Task context: {request.task.strip()}")
        if request.issue_number is not None:
            notes.append(f"Issue context: #{request.issue_number}")

        if decision.selected_provider == DevProvider.FEATURE_DEV:
            notes.append("Run PopKit enhancement hooks after delegated feature-dev execution.")
            return DevWorkflowPlan(
                decision=decision,
                execution_mode="delegated",
                primary_command="/popkit:feature-dev",
                fallback_command=popkit_command,
                notes=notes,
            )

        return DevWorkflowPlan(
            decision=decision,
            execution_mode="native",
            primary_command=popkit_command,
            fallback_command=None,
            notes=notes,
        )

    @staticmethod
    def _build_popkit_command(task: str, mode: str, issue_number: Optional[int]) -> str:
        if issue_number is not None:
            target = f"work #{issue_number}"
        else:
            task_text = _escape_for_double_quotes(task.strip())
            target = f'"{task_text}"'

        return f"/popkit-dev:dev {target} --mode {mode} --provider popkit"
