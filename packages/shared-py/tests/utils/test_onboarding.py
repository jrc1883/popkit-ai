#!/usr/bin/env python3
"""Tests for shared onboarding state and telemetry controls."""

import tempfile
from pathlib import Path

from popkit_shared.utils.onboarding import (
    INTRO_HEADER,
    TELEMETRY_HEADER,
    OnboardingManager,
    TelemetryMode,
    is_onboarding_header,
    telemetry_allows_project_identity,
    telemetry_allows_remote,
)


def test_pending_questions_exist_on_first_run():
    """First run should ask both intro and telemetry questions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = OnboardingManager(Path(tmpdir))
        questions = manager.pending_questions()

        headers = [question["header"] for question in questions]
        assert headers == [INTRO_HEADER, TELEMETRY_HEADER]


def test_apply_answers_persists_and_skips_repeat_prompts():
    """Answered onboarding questions should not reappear on later runs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = OnboardingManager(Path(tmpdir))
        manager.apply_answers(
            {
                INTRO_HEADER: "Use guided defaults (Recommended)",
                TELEMETRY_HEADER: "Anonymous telemetry",
            }
        )

        reloaded = OnboardingManager(Path(tmpdir))
        state = reloaded.load_state()

        assert state.intro_seen is True
        assert state.telemetry_prompted is True
        assert state.telemetry_mode == "anonymous"
        assert reloaded.pending_questions() == []


def test_set_telemetry_mode_marks_prompted():
    """Direct telemetry updates should mark onboarding as completed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = OnboardingManager(Path(tmpdir))
        manager.set_telemetry_mode(TelemetryMode.COMMUNITY)

        state = manager.load_state()
        assert state.telemetry_prompted is True
        assert state.telemetry_mode == "community"
        assert state.completed_version is not None


def test_telemetry_helpers_reflect_mode_capabilities():
    """Telemetry helpers should distinguish remote and identified modes."""
    assert telemetry_allows_remote(TelemetryMode.OFF) is False
    assert telemetry_allows_remote(TelemetryMode.ANONYMOUS) is True
    assert telemetry_allows_project_identity(TelemetryMode.ANONYMOUS) is False
    assert telemetry_allows_project_identity(TelemetryMode.COMMUNITY) is True


def test_is_onboarding_header_matches_known_headers():
    """Known onboarding headers should be detectable."""
    assert is_onboarding_header(INTRO_HEADER) is True
    assert is_onboarding_header(TELEMETRY_HEADER) is True
    assert is_onboarding_header("Quality") is False
