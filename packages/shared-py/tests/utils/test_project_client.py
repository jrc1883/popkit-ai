#!/usr/bin/env python3
"""Tests for project_client telemetry gating and payload shaping."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from popkit_shared.utils.onboarding import OnboardingManager, TelemetryMode
from popkit_shared.utils.project_client import ProjectActivity, ProjectClient


def test_client_unavailable_when_telemetry_is_off():
    """Project client should disable remote calls when telemetry is off."""
    with tempfile.TemporaryDirectory() as tmpdir:
        onboarding = OnboardingManager(Path(tmpdir))
        onboarding.set_telemetry_mode(TelemetryMode.OFF)
        client = ProjectClient(api_key="pk_test_123", onboarding_manager=onboarding)

        assert client.is_available is False


def test_register_project_omits_identity_in_anonymous_mode():
    """Anonymous telemetry should omit project name and path hint."""
    with tempfile.TemporaryDirectory() as tmpdir:
        onboarding = OnboardingManager(Path(tmpdir))
        onboarding.set_telemetry_mode(TelemetryMode.ANONYMOUS)
        client = ProjectClient(api_key="pk_test_123", onboarding_manager=onboarding)

        with patch.object(
            client, "_post", return_value={"status": "ok", "session_count": 1}
        ) as mock_post:
            client.register_project(project_path=tmpdir, name="PopKit Test")

        request_body = mock_post.call_args[0][1]
        assert request_body["project_id"]
        assert "name" not in request_body
        assert "path_hint" not in request_body


def test_register_project_keeps_identity_in_community_mode():
    """Community telemetry should preserve project identity fields."""
    with tempfile.TemporaryDirectory() as tmpdir:
        onboarding = OnboardingManager(Path(tmpdir))
        onboarding.set_telemetry_mode(TelemetryMode.COMMUNITY)
        client = ProjectClient(api_key="pk_test_123", onboarding_manager=onboarding)

        with patch.object(
            client, "_post", return_value={"status": "ok", "session_count": 1}
        ) as mock_post:
            client.register_project(project_path=tmpdir, name="PopKit Test")

        request_body = mock_post.call_args[0][1]
        assert request_body["name"] == "PopKit Test"
        assert "path_hint" in request_body


def test_record_activity_skips_when_telemetry_is_off():
    """Activity recording should short-circuit when telemetry is disabled."""
    with tempfile.TemporaryDirectory() as tmpdir:
        onboarding = OnboardingManager(Path(tmpdir))
        onboarding.set_telemetry_mode(TelemetryMode.OFF)
        client = ProjectClient(api_key="pk_test_123", onboarding_manager=onboarding)

        with patch.object(client, "_post") as mock_post:
            result = client.record_activity(ProjectActivity(tool_name="Read"), project_id="proj123")

        assert result is False
        mock_post.assert_not_called()
