#!/usr/bin/env python3
"""Tests for popkit_shared.utils.interaction_surface."""

from popkit_shared.utils.interaction_surface import (
    DecisionSpec,
    InteractionSurface,
    QuestionOption,
    SelectionMode,
    resolve_runtime_capabilities,
)


def test_decision_spec_serializes_options():
    spec = DecisionSpec(
        header="Next Action",
        question="What should PopKit do next?",
        options=[
            QuestionOption(
                id="commit",
                label="Commit work",
                description="Checkpoint the current branch",
                recommended=True,
                follow_up="git commit",
            )
        ],
        selection_mode=SelectionMode.SINGLE,
        source_command="/popkit-dev:next",
    )

    payload = spec.to_dict()

    assert payload["header"] == "Next Action"
    assert payload["selection_mode"] == "single"
    assert payload["source_command"] == "/popkit-dev:next"
    assert payload["options"] == [
        {
            "id": "commit",
            "label": "Commit work",
            "description": "Checkpoint the current branch",
            "recommended": True,
            "follow_up": "git commit",
        }
    ]


def test_resolve_runtime_capabilities_prefers_explicit_request_user_input():
    capabilities = resolve_runtime_capabilities(
        env={
            "POPKIT_PROVIDER": "codex",
            "POPKIT_INTERACTION_SURFACE": "request_user_input",
        }
    )

    assert capabilities.provider == "codex"
    assert capabilities.interaction_surface == InteractionSurface.REQUEST_USER_INPUT
    assert capabilities.can_request_user_input is True
    assert capabilities.can_ask_user_question is False


def test_resolve_runtime_capabilities_defaults_codex_to_plain_text():
    capabilities = resolve_runtime_capabilities(
        env={
            "POPKIT_PROVIDER": "codex",
        }
    )

    assert capabilities.provider == "codex"
    assert capabilities.interaction_surface == InteractionSurface.PLAIN_TEXT
    assert capabilities.can_request_user_input is False
    assert capabilities.can_ask_user_question is False


def test_resolve_runtime_capabilities_defaults_claude_to_ask_user_question():
    capabilities = resolve_runtime_capabilities(
        env={
            "POPKIT_PROVIDER": "claude-code",
        }
    )

    assert capabilities.provider == "claude-code"
    assert capabilities.interaction_surface == InteractionSurface.ASK_USER_QUESTION
    assert capabilities.can_request_user_input is False
    assert capabilities.can_ask_user_question is True


def test_resolve_runtime_capabilities_honors_explicit_ask_user_override():
    capabilities = resolve_runtime_capabilities(
        provider="codex",
        env={
            "POPKIT_INTERACTION_SURFACE": "ask_user_question",
            "POPKIT_CAN_ASK_USER_QUESTION": "true",
        },
    )

    assert capabilities.provider == "codex"
    assert capabilities.interaction_surface == InteractionSurface.ASK_USER_QUESTION
    assert capabilities.can_request_user_input is False
    assert capabilities.can_ask_user_question is True
