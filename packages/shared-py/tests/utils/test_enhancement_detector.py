#!/usr/bin/env python3
"""Tests for saved-login handling in enhancement_detector."""

from unittest.mock import MagicMock, patch

from popkit_shared.utils import enhancement_detector


def test_has_api_key_uses_saved_cloud_config():
    """Saved login config should be treated like an exported API key."""
    response = MagicMock()
    response.status = 200
    response.__enter__.return_value = response

    with (
        patch(
            "popkit_shared.utils.enhancement_detector.get_cloud_api_key", return_value="pk_saved"
        ),
        patch(
            "popkit_shared.utils.enhancement_detector.get_cloud_api_url",
            return_value="https://saved.example",
        ),
        patch("urllib.request.urlopen", return_value=response) as mock_urlopen,
    ):
        assert enhancement_detector.has_api_key() is True

    request = mock_urlopen.call_args.args[0]
    assert request.full_url == "https://saved.example/v1/health"


def test_track_enhancement_usage_uses_saved_login():
    """Usage tracking should use saved login credentials when env vars are absent."""
    response = MagicMock()
    response.status = 200
    response.__enter__.return_value = response

    with (
        patch(
            "popkit_shared.utils.enhancement_detector.get_cloud_api_key", return_value="pk_saved"
        ),
        patch(
            "popkit_shared.utils.enhancement_detector.get_cloud_api_url",
            return_value="https://saved.example",
        ),
        patch("urllib.request.urlopen", return_value=response) as mock_urlopen,
    ):
        assert enhancement_detector.track_enhancement_usage("agent-routing") is True

    request = mock_urlopen.call_args.args[0]
    assert request.full_url == "https://saved.example/v1/usage/track"
