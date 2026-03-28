#!/usr/bin/env python3
"""
Interaction surface contract for provider-aware user decisions.

Defines provider-agnostic question/decision models plus runtime capability
resolution for choosing between AskUserQuestion, request_user_input, and
plain-text fallback surfaces.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping


class InteractionSurface(str, Enum):
    """Supported user-interaction surfaces."""

    ASK_USER_QUESTION = "ask_user_question"
    REQUEST_USER_INPUT = "request_user_input"
    PLAIN_TEXT = "plain_text"


class SelectionMode(str, Enum):
    """Selection semantics for a decision prompt."""

    SINGLE = "single"
    MULTI = "multi"


@dataclass(frozen=True)
class QuestionOption:
    """A stable option in a provider-agnostic decision prompt."""

    id: str
    label: str
    description: str
    recommended: bool = False
    follow_up: str | None = None

    def to_dict(self) -> dict[str, str | bool]:
        """Convert to a serializable representation."""
        payload: dict[str, str | bool] = {
            "id": self.id,
            "label": self.label,
            "description": self.description,
            "recommended": self.recommended,
        }
        if self.follow_up:
            payload["follow_up"] = self.follow_up
        return payload


@dataclass(frozen=True)
class DecisionSpec:
    """Provider-neutral decision prompt that hosts can render."""

    header: str
    question: str
    options: list[QuestionOption]
    selection_mode: SelectionMode = SelectionMode.SINGLE
    source_command: str | None = None
    follow_up: str | None = None

    def to_dict(self) -> dict[str, object]:
        """Convert to a serializable representation."""
        payload: dict[str, object] = {
            "header": self.header,
            "question": self.question,
            "options": [option.to_dict() for option in self.options],
            "selection_mode": self.selection_mode.value,
        }
        if self.source_command:
            payload["source_command"] = self.source_command
        if self.follow_up:
            payload["follow_up"] = self.follow_up
        return payload


@dataclass(frozen=True)
class RuntimeCapabilities:
    """Runtime interaction capabilities selected by the host."""

    provider: str
    interaction_surface: InteractionSurface
    can_request_user_input: bool = False
    can_ask_user_question: bool = False
    metadata: dict[str, str] = field(default_factory=dict)

    def supports(self, surface: InteractionSurface) -> bool:
        """Return True when the runtime can use the given surface."""
        if surface == InteractionSurface.REQUEST_USER_INPUT:
            return self.can_request_user_input
        if surface == InteractionSurface.ASK_USER_QUESTION:
            return self.can_ask_user_question
        return True

    def to_dict(self) -> dict[str, object]:
        """Convert to a serializable representation."""
        return {
            "provider": self.provider,
            "interaction_surface": self.interaction_surface.value,
            "can_request_user_input": self.can_request_user_input,
            "can_ask_user_question": self.can_ask_user_question,
            "metadata": dict(self.metadata),
        }


def _parse_bool(value: str | None) -> bool | None:
    """Parse environment-style booleans."""
    if value is None:
        return None

    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return None


def _parse_surface(value: str | None) -> InteractionSurface | None:
    """Parse a surface identifier from host-provided text."""
    if value is None:
        return None

    normalized = value.strip().lower().replace("-", "_")
    aliases = {
        "ask_user_question": InteractionSurface.ASK_USER_QUESTION,
        "askuserquestion": InteractionSurface.ASK_USER_QUESTION,
        "request_user_input": InteractionSurface.REQUEST_USER_INPUT,
        "requestuserinput": InteractionSurface.REQUEST_USER_INPUT,
        "plain_text": InteractionSurface.PLAIN_TEXT,
        "plaintext": InteractionSurface.PLAIN_TEXT,
    }
    return aliases.get(normalized)


def resolve_runtime_capabilities(
    provider: str | None = None,
    env: Mapping[str, str] | None = None,
) -> RuntimeCapabilities:
    """Resolve interaction capabilities from provider plus host-declared runtime flags."""
    values = env if env is not None else os.environ
    provider_name = (
        provider or values.get("POPKIT_PROVIDER") or values.get("provider") or "unknown"
    ).strip()
    provider_key = provider_name.lower().replace("_", "-")

    explicit_surface = _parse_surface(values.get("POPKIT_INTERACTION_SURFACE"))
    explicit_request_ui = _parse_bool(values.get("POPKIT_CAN_REQUEST_USER_INPUT"))
    explicit_ask_ui = _parse_bool(values.get("POPKIT_CAN_ASK_USER_QUESTION"))

    default_ask = provider_key in {"claude", "claude-code", "claudecode"}
    can_request_user_input = (
        explicit_request_ui
        if explicit_request_ui is not None
        else explicit_surface == InteractionSurface.REQUEST_USER_INPUT
    )
    can_ask_user_question = (
        explicit_ask_ui
        if explicit_ask_ui is not None
        else explicit_surface == InteractionSurface.ASK_USER_QUESTION or default_ask
    )

    if explicit_surface is not None:
        surface = explicit_surface
    elif can_request_user_input:
        surface = InteractionSurface.REQUEST_USER_INPUT
    elif can_ask_user_question:
        surface = InteractionSurface.ASK_USER_QUESTION
    else:
        surface = InteractionSurface.PLAIN_TEXT

    if surface == InteractionSurface.REQUEST_USER_INPUT:
        can_request_user_input = True
    elif surface == InteractionSurface.ASK_USER_QUESTION:
        can_ask_user_question = True

    metadata: dict[str, str] = {}
    if values.get("POPKIT_INTERACTION_SURFACE"):
        metadata["declared_surface"] = values["POPKIT_INTERACTION_SURFACE"]

    return RuntimeCapabilities(
        provider=provider_name,
        interaction_surface=surface,
        can_request_user_input=can_request_user_input,
        can_ask_user_question=can_ask_user_question,
        metadata=metadata,
    )
