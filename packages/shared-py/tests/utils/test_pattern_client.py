#!/usr/bin/env python3
"""Tests for saved-login handling in pattern_client."""

from unittest.mock import patch

from popkit_shared.utils.pattern_client import PatternClient


def test_pattern_client_uses_saved_cloud_config():
    """Pattern client should pick up saved login credentials automatically."""
    with patch(
        "popkit_shared.utils.pattern_client.resolve_cloud_config",
        return_value=("pk_saved", "https://saved.example"),
    ):
        client = PatternClient()

    assert client.api_key == "pk_saved"
    assert client.api_url == "https://saved.example"


def test_pattern_client_explicit_args_override_saved_cloud_config():
    """Explicit constructor args should still win over saved login defaults."""
    with patch(
        "popkit_shared.utils.pattern_client.resolve_cloud_config",
        return_value=("pk_saved", "https://saved.example"),
    ):
        client = PatternClient(api_key="pk_explicit", api_url="https://explicit.example")

    assert client.api_key == "pk_explicit"
    assert client.api_url == "https://explicit.example"
