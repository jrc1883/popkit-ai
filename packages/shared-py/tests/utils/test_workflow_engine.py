#!/usr/bin/env python3
"""Tests for saved-login handling in workflow_engine."""

from unittest.mock import patch

from popkit_shared.utils.workflow_engine import UpstashWorkflowEngine, has_api_key


def test_has_api_key_uses_saved_cloud_login():
    """Workflow engine availability should respect saved login config."""
    with patch("popkit_shared.utils.workflow_engine.has_cloud_api_key", return_value=True):
        assert has_api_key() is True


def test_upstash_workflow_engine_uses_saved_cloud_config():
    """Cloud workflow engine should use saved login credentials by default."""
    with (
        patch("popkit_shared.utils.workflow_engine.get_cloud_api_key", return_value="pk_saved"),
        patch(
            "popkit_shared.utils.workflow_engine.get_cloud_api_url",
            return_value="https://saved.example",
        ),
    ):
        engine = UpstashWorkflowEngine("workflow-123")

    assert engine.api_key == "pk_saved"
    assert engine.api_url == "https://saved.example"
