#!/usr/bin/env python3
"""
Issue #218: Hybrid PopKit/feature-dev execution planning.

Builds an executable plan from provider resolution:
- native PopKit execution path
- delegated feature-dev path with PopKit fallback
"""

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    from .dev_provider_resolver import (
        DevProvider,
        DevProviderResolver,
        ProviderAvailability,
        ProviderContext,
        ProviderDecision,
        detect_feature_dev_plugin,
    )
except ImportError:
    # Support direct script execution via `python path/to/dev_workflow_router.py`.
    shared_py_root = Path(__file__).resolve().parents[2]
    if str(shared_py_root) not in sys.path:
        sys.path.insert(0, str(shared_py_root))
    from popkit_shared.utils.dev_provider_resolver import (  # type: ignore[no-redef]
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


def _normalize_requested_provider(value: str) -> DevProvider:
    normalized = (value or "").strip().lower().replace("_", "-")
    if normalized in {"featuredev", "feature-dev"}:
        return DevProvider.FEATURE_DEV
    if normalized == DevProvider.POPKIT.value:
        return DevProvider.POPKIT
    return DevProvider.AUTO


@dataclass(frozen=True)
class DevWorkflowRequest:
    """Inputs for building a dev workflow execution plan."""

    task: str
    mode: str = "full"
    issue_number: int | None = None
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
    fallback_command: str | None = None
    notes: list[str] = field(default_factory=list)

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

    def __init__(self, resolver: DevProviderResolver | None = None):
        self.resolver = resolver or DevProviderResolver()

    def build_plan(
        self,
        request: DevWorkflowRequest,
        plugin_scan_data: Any | None = None,
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
        notes: list[str] = []
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
    def _build_popkit_command(task: str, mode: str, issue_number: int | None) -> str:
        if issue_number is not None:
            target = f"work #{issue_number}"
        else:
            task_text = _escape_for_double_quotes(task.strip())
            target = f'"{task_text}"'

        return f"/popkit-dev:dev {target} --mode {mode} --provider popkit"


def format_plan_display(plan: DevWorkflowPlan) -> str:
    """Format a plan for human-readable command preflight output."""
    lines = [
        "## Provider Preflight",
        f"Selected provider: {plan.decision.selected_provider.value}",
        f"Execution mode: {plan.execution_mode}",
        f"Primary command: {plan.primary_command}",
    ]
    if plan.fallback_command:
        lines.append(f"Fallback command: {plan.fallback_command}")
    if plan.notes:
        lines.append("")
        lines.append("Notes:")
        lines.extend(f"- {note}" for note in plan.notes)
    if plan.decision.rationale:
        lines.append("")
        lines.append("Rationale:")
        lines.extend(f"- {reason}" for reason in plan.decision.rationale)
    return "\n".join(lines)


def _load_plugins_json(path: str | None) -> Any | None:
    if not path:
        return None

    raw = Path(path).read_text(encoding="utf-8")
    payload = json.loads(raw)
    if isinstance(payload, dict) and isinstance(payload.get("plugins"), list):
        return payload["plugins"]
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Resolve and plan hybrid PopKit/feature-dev workflow execution."
    )
    parser.add_argument("--task", default="", help="Task description for dev workflow.")
    parser.add_argument(
        "--issue",
        dest="issue_number",
        type=int,
        help="Issue number for `work #N` routing.",
    )
    parser.add_argument(
        "--mode",
        default="full",
        help="Workflow mode: quick|full (invalid values normalize to full).",
    )
    parser.add_argument(
        "--provider",
        default=DevProvider.AUTO.value,
        help="Requested provider: auto|popkit|feature-dev.",
    )
    parser.add_argument(
        "--allow-upstream",
        dest="allow_upstream",
        action="store_true",
        default=True,
        help="Allow delegated upstream provider usage.",
    )
    parser.add_argument(
        "--no-allow-upstream",
        dest="allow_upstream",
        action="store_false",
        help="Force PopKit-only execution for this invocation.",
    )
    parser.add_argument(
        "--requires-popkit-orchestration",
        action="store_true",
        help="Mark task as requiring PopKit-specific orchestration capabilities.",
    )
    parser.add_argument(
        "--requires-github-cache",
        action="store_true",
        help="Mark task as requiring PopKit GitHub cache guidance capabilities.",
    )
    parser.add_argument(
        "--plugins-json",
        help="Optional plugin scan JSON path for deterministic availability checks.",
    )
    parser.add_argument(
        "--format",
        choices=["display", "json"],
        default="display",
        help="Output format.",
    )

    args = parser.parse_args(argv)

    try:
        plugin_scan_data = _load_plugins_json(args.plugins_json)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Failed to load plugins JSON: {exc}", file=sys.stderr)
        return 2

    router = DevWorkflowRouter()
    request = DevWorkflowRequest(
        task=args.task or "",
        mode=args.mode,
        issue_number=args.issue_number,
        requested_provider=_normalize_requested_provider(args.provider),
        allow_upstream=args.allow_upstream,
        requires_popkit_orchestration=args.requires_popkit_orchestration,
        requires_github_cache=args.requires_github_cache,
    )

    plan = router.build_plan(request, plugin_scan_data=plugin_scan_data)

    if args.format == "json":
        print(json.dumps(plan.to_dict(), indent=2))
    else:
        print(format_plan_display(plan))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
