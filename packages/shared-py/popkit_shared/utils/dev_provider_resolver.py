#!/usr/bin/env python3
"""
Provider resolver for PopKit development workflows (Issue #218).

First principle:
Pick the simplest provider that can satisfy required capabilities with the
lowest operational risk, then reassess when assumptions change.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from .plugin_detector import scan_installed_plugins


class DevProvider(str, Enum):
    """Supported workflow providers."""

    AUTO = "auto"
    POPKIT = "popkit"
    FEATURE_DEV = "feature-dev"


POPKIT_ONLY_CAPABILITIES: set[str] = {
    "power_mode",
    "issue_guidance",
    "quality_gate_overrides",
    "label_validation",
    "worktree_orchestration",
    "session_capture_hooks",
}

UPSTREAM_BASE_CAPABILITIES: set[str] = {
    "feature_scaffold",
    "basic_plan_execute",
    "standard_review",
}


def _normalize_provider(value: str) -> str:
    normalized = value.strip().lower().replace("_", "-")
    if normalized in {"featuredev", "feature-dev"}:
        return DevProvider.FEATURE_DEV.value
    if normalized in {"popkit", "auto"}:
        return normalized
    return normalized


def detect_feature_dev_plugin(plugins: list[dict[str, Any]] | None = None) -> bool:
    """Detect whether the official feature-dev plugin is installed."""
    if plugins is None:
        try:
            plugins = scan_installed_plugins()
        except Exception:
            return False

    for plugin in plugins:
        manifest = plugin.get("manifest", {})
        candidates = {
            str(plugin.get("name", "")),
            str(manifest.get("name", "")),
        }
        for candidate in candidates:
            if _normalize_provider(candidate) == DevProvider.FEATURE_DEV.value:
                return True
    return False


@dataclass
class ProviderAvailability:
    """Availability snapshot for provider resolution."""

    popkit_available: bool = True
    feature_dev_available: bool = False
    detection_source: str = "default"

    @classmethod
    def from_installed_plugins(
        cls, plugins: list[dict[str, Any]] | None = None
    ) -> "ProviderAvailability":
        return cls(
            popkit_available=True,
            feature_dev_available=detect_feature_dev_plugin(plugins=plugins),
            detection_source="installed_plugins",
        )


@dataclass
class ProviderContext:
    """Inputs that drive provider selection."""

    requested_provider: DevProvider = DevProvider.AUTO
    required_capabilities: set[str] = field(default_factory=set)
    complexity: int = 5  # 1-10 scale
    workflow_mode: str = "full"
    allow_upstream: bool = True
    prefer_upstream_for_commodity: bool = True


@dataclass
class ProviderDecision:
    """Resolution output with explicit assumptions and reassessment points."""

    selected_provider: DevProvider
    fallback_from: DevProvider | None = None
    rationale: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    reassessment_triggers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "selected_provider": self.selected_provider.value,
            "fallback_from": self.fallback_from.value if self.fallback_from else None,
            "rationale": self.rationale,
            "assumptions": self.assumptions,
            "reassessment_triggers": self.reassessment_triggers,
        }


class DevProviderResolver:
    """Resolve popkit vs feature-dev provider using explicit capability checks."""

    def __init__(
        self,
        popkit_only_capabilities: Iterable[str] | None = None,
        complexity_popkit_threshold: int = 8,
    ):
        self.popkit_only_capabilities = set(popkit_only_capabilities or POPKIT_ONLY_CAPABILITIES)
        self.complexity_popkit_threshold = complexity_popkit_threshold

    def detect_availability(self) -> ProviderAvailability:
        return ProviderAvailability.from_installed_plugins()

    def resolve(
        self,
        context: ProviderContext,
        availability: ProviderAvailability | None = None,
    ) -> ProviderDecision:
        availability = availability or self.detect_availability()

        if context.requested_provider == DevProvider.POPKIT:
            return self._decision_popkit("Explicit provider override: popkit.")

        if context.requested_provider == DevProvider.FEATURE_DEV:
            if availability.feature_dev_available and context.allow_upstream:
                return self._decision_upstream("Explicit provider override: feature-dev.")
            return self._decision_popkit(
                "feature-dev was requested but unavailable; fallback to popkit.",
                fallback_from=DevProvider.FEATURE_DEV,
            )

        popkit_required = context.required_capabilities & self.popkit_only_capabilities
        if popkit_required:
            return self._decision_popkit(
                "Required capabilities are PopKit-specific: "
                + ", ".join(sorted(popkit_required))
                + "."
            )

        if not context.allow_upstream:
            return self._decision_popkit("Upstream provider explicitly disabled for this run.")

        if not availability.feature_dev_available:
            return self._decision_popkit("feature-dev plugin is not installed.")

        if (
            context.workflow_mode == "full"
            and context.complexity >= self.complexity_popkit_threshold
            and not context.prefer_upstream_for_commodity
        ):
            return self._decision_popkit(
                "High-complexity full workflow favors PopKit orchestration."
            )

        return self._decision_upstream(
            "Commodity workflow with no PopKit-only requirements; prefer upstream."
        )

    def _decision_popkit(
        self,
        reason: str,
        fallback_from: DevProvider | None = None,
    ) -> ProviderDecision:
        return ProviderDecision(
            selected_provider=DevProvider.POPKIT,
            fallback_from=fallback_from,
            rationale=[reason, "PopKit remains default for differentiated orchestration."],
            assumptions=[
                "PopKit workflow quality is at least parity for this task.",
                "Required orchestration features are stable locally.",
            ],
            reassessment_triggers=[
                "feature-dev gains equivalent orchestration hooks.",
                "PopKit error rate exceeds upstream for two consecutive sprints.",
                "Cycle time worsens by >20% on comparable tasks.",
            ],
        )

    def _decision_upstream(self, reason: str) -> ProviderDecision:
        return ProviderDecision(
            selected_provider=DevProvider.FEATURE_DEV,
            rationale=[
                reason,
                "Use upstream for baseline feature flow and keep PopKit as augmentation layer.",
            ],
            assumptions=[
                "feature-dev remains installed and operational.",
                "Task does not require PopKit-only capabilities.",
            ],
            reassessment_triggers=[
                "feature-dev invocation fails or regresses on key workflow steps.",
                "New requirement introduces PopKit-only capability dependency.",
                "Upstream release notes include breaking workflow changes.",
            ],
        )
