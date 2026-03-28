#!/usr/bin/env python3
"""
Shared onboarding state and telemetry controls for PopKit.

This module stores machine-level onboarding preferences separately from
project-level privacy settings. It is designed to be reused by first-run
flows such as /popkit:project init and by background hooks that need to
respect telemetry opt-in state.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"
ONBOARDING_FLOW_VERSION = "1.0"

INTRO_QUESTION_ID = "onboarding_intro"
INTRO_HEADER = "PopKit intro"
TELEMETRY_QUESTION_ID = "telemetry_mode"
TELEMETRY_HEADER = "PopKit telemetry"


class TelemetryMode(Enum):
    """Telemetry modes for machine-level PopKit observability."""

    OFF = "off"
    ANONYMOUS = "anonymous"
    COMMUNITY = "community"

    @classmethod
    def from_value(cls, value: str | TelemetryMode | None) -> TelemetryMode:
        """Normalize a telemetry mode value."""
        if isinstance(value, cls):
            return value

        normalized = str(value or cls.OFF.value).strip().lower()
        for mode in cls:
            if mode.value == normalized:
                return mode

        return cls.OFF


@dataclass
class OnboardingState:
    """Persistent machine-level onboarding state."""

    schema_version: str = SCHEMA_VERSION
    intro_seen: bool = False
    telemetry_prompted: bool = False
    telemetry_mode: str = TelemetryMode.OFF.value
    completed_version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert state to a JSON-serializable dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OnboardingState:
        """Create state from stored JSON data."""
        state = cls(
            schema_version=data.get("schema_version", SCHEMA_VERSION),
            intro_seen=bool(data.get("intro_seen", False)),
            telemetry_prompted=bool(data.get("telemetry_prompted", False)),
            telemetry_mode=TelemetryMode.from_value(data.get("telemetry_mode")).value,
            completed_version=data.get("completed_version"),
        )
        state.refresh_completion()
        return state

    def refresh_completion(self) -> None:
        """Update the completed_version field based on current state."""
        if self.telemetry_prompted:
            self.completed_version = ONBOARDING_FLOW_VERSION
        else:
            self.completed_version = None


def is_onboarding_header(header: str) -> bool:
    """Return True when a header belongs to the shared onboarding flow."""
    return header in {INTRO_HEADER, TELEMETRY_HEADER}


def telemetry_allows_remote(mode: str | TelemetryMode | None) -> bool:
    """Return True when remote telemetry is allowed."""
    return TelemetryMode.from_value(mode) is not TelemetryMode.OFF


def telemetry_allows_project_identity(mode: str | TelemetryMode | None) -> bool:
    """Return True when project-identifying fields may be sent remotely."""
    return TelemetryMode.from_value(mode) is TelemetryMode.COMMUNITY


def parse_telemetry_answer(answer: str | None) -> TelemetryMode:
    """Infer a telemetry mode from a user-visible option label."""
    normalized = str(answer or "").strip().lower()

    if "anonymous" in normalized:
        return TelemetryMode.ANONYMOUS
    if "community" in normalized:
        return TelemetryMode.COMMUNITY

    return TelemetryMode.OFF


def build_intro_question() -> dict[str, Any]:
    """Build the one-time intro question for guided setup."""
    return {
        "id": INTRO_QUESTION_ID,
        "question": (
            "This is the first PopKit setup on this machine. PopKit is local-first, "
            "remembers onboarding choices, and keeps telemetry separate from project "
            "sharing. How would you like to continue?"
        ),
        "header": INTRO_HEADER,
        "options": [
            {
                "label": "Use guided defaults (Recommended)",
                "description": (
                    "Continue with local-first setup. Telemetry stays off until you "
                    "choose otherwise on the next step."
                ),
            },
            {
                "label": "Skip intro details",
                "description": "Jump straight into the telemetry choice and project setup.",
            },
        ],
    }


def build_telemetry_question() -> dict[str, Any]:
    """Build the telemetry opt-in question."""
    return {
        "id": TELEMETRY_QUESTION_ID,
        "question": (
            "PopKit can send background observability signals to PopKit Cloud. "
            "Recommended: keep this off until you know you want remote insights. "
            "Which telemetry mode should this machine use?"
        ),
        "header": TELEMETRY_HEADER,
        "options": [
            {
                "label": "Off - local only (Recommended)",
                "description": "No background network observability or project registration.",
            },
            {
                "label": "Anonymous telemetry",
                "description": (
                    "Allow remote observability without project name, path hint, repo slug, "
                    "or branch."
                ),
            },
            {
                "label": "Community telemetry",
                "description": (
                    "Allow remote observability with project identity for full cross-project "
                    "insights."
                ),
            },
        ],
    }


class OnboardingManager:
    """Load, save, and update shared onboarding state."""

    def __init__(self, config_dir: str | Path | None = None):
        self.config_dir = (
            Path(config_dir)
            if config_dir is not None
            else Path.home() / ".claude" / "config" / "popkit"
        )
        self.state_file = self.config_dir / "onboarding.json"
        self._state: OnboardingState | None = None

    @property
    def state(self) -> OnboardingState:
        """Get the current onboarding state."""
        if self._state is None:
            self._state = self.load_state()
        return self._state

    def load_state(self) -> OnboardingState:
        """Load onboarding state from disk."""
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text(encoding="utf-8"))
                return OnboardingState.from_dict(data)
            except (OSError, json.JSONDecodeError, TypeError):
                pass

        return OnboardingState()

    def save_state(self, state: OnboardingState | None = None) -> None:
        """Persist onboarding state to disk."""
        if state is not None:
            self._state = state

        if self._state is None:
            return

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self._state.to_dict(), indent=2), encoding="utf-8")

    def get_telemetry_mode(self) -> TelemetryMode:
        """Get the normalized telemetry mode."""
        return TelemetryMode.from_value(self.state.telemetry_mode)

    def set_telemetry_mode(self, mode: str | TelemetryMode) -> OnboardingState:
        """Update and persist the telemetry mode."""
        self.state.telemetry_prompted = True
        self.state.telemetry_mode = TelemetryMode.from_value(mode).value
        self.state.refresh_completion()
        self.save_state()
        return self.state

    def mark_intro_seen(self) -> OnboardingState:
        """Mark the onboarding intro as shown."""
        self.state.intro_seen = True
        self.state.refresh_completion()
        self.save_state()
        return self.state

    def pending_questions(self) -> list[dict[str, Any]]:
        """Return onboarding questions that still need to be asked."""
        questions: list[dict[str, Any]] = []

        if not self.state.intro_seen:
            questions.append(build_intro_question())

        if not self.state.telemetry_prompted:
            questions.append(build_telemetry_question())

        return questions

    def apply_answers(self, answers: dict[str, Any]) -> OnboardingState:
        """Apply AskUserQuestion answers to onboarding state."""
        changed = False

        for header, answer in answers.items():
            if header == INTRO_HEADER:
                self.state.intro_seen = True
                changed = True
            elif header == TELEMETRY_HEADER:
                self.state.telemetry_prompted = True
                self.state.telemetry_mode = parse_telemetry_answer(str(answer)).value
                changed = True

        if changed:
            self.state.refresh_completion()
            self.save_state()

        return self.state

    def get_status_snapshot(self) -> dict[str, Any]:
        """Return the current state in a command-friendly format."""
        return self.state.to_dict()
