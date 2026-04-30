#!/usr/bin/env python3
"""
Test suite for cloud_agent_search.py

Tests cloud agent search client: availability check, mocked HTTP responses,
fallback behavior, and dynamic version header.
"""

import json
import sys
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from popkit_shared.utils.cloud_agent_search import (
    AgentMatch,
    SearchResult,
    get_agent,
    is_available,
    list_agents,
    search_agents,
)

# =============================================================================
# Availability
# =============================================================================


class TestAvailability:
    """Test is_available checks."""

    def test_available_with_key(self):
        with patch.dict("os.environ", {"POPKIT_API_KEY": "test-key"}):
            assert is_available() is True

    def test_available_with_saved_login(self):
        with patch(
            "popkit_shared.utils.cloud_agent_search.resolve_cloud_config",
            return_value=("pk_saved", "https://saved.example"),
        ):
            assert is_available() is True

    def test_not_available_without_key(self):
        with patch.dict("os.environ", {}, clear=True):
            assert is_available() is False

    def test_not_available_empty_key(self):
        with patch.dict("os.environ", {"POPKIT_API_KEY": ""}):
            assert is_available() is False


# =============================================================================
# Data Classes
# =============================================================================


class TestDataClasses:
    """Test AgentMatch and SearchResult dataclasses."""

    def test_agent_match(self):
        match = AgentMatch(
            agent="code-reviewer",
            score=0.85,
            tier="tier-1",
            description="Reviews code",
            keywords=["review", "quality"],
            method="semantic",
        )
        assert match.agent == "code-reviewer"
        assert match.score == 0.85

    def test_search_result(self):
        result = SearchResult(
            query="test",
            matches=[],
            fallback_to_keywords=False,
        )
        assert result.error is None
        assert result.fallback_to_keywords is False


# =============================================================================
# search_agents
# =============================================================================


class TestSearchAgents:
    """Test search_agents function."""

    def test_no_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            result = search_agents("test query")
            assert result.fallback_to_keywords is True
            assert result.error == "POPKIT_API_KEY not set"
            assert len(result.matches) == 0

    def test_successful_search(self):
        response_data = {
            "matches": [
                {
                    "agent": "security-auditor",
                    "score": 0.92,
                    "tier": "tier-1",
                    "description": "Security scanning",
                    "keywords": ["security", "audit"],
                },
                {
                    "agent": "test-writer",
                    "score": 0.78,
                    "tier": "tier-2",
                    "description": "Writes tests",
                    "keywords": ["test"],
                },
            ],
            "fallback_to_keywords": False,
        }

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with (
            patch.dict("os.environ", {"POPKIT_API_KEY": "test-key"}),
            patch("urllib.request.urlopen", return_value=mock_response),
        ):
            result = search_agents("security scan")
            assert len(result.matches) == 2
            assert result.matches[0].agent == "security-auditor"
            assert result.matches[0].score == 0.92
            assert result.matches[0].method == "semantic"
            assert result.error is None

    def test_caps_top_k_at_10(self):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"matches": []}).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with (
            patch.dict("os.environ", {"POPKIT_API_KEY": "test-key"}),
            patch("urllib.request.urlopen", return_value=mock_response) as mock_open,
        ):
            search_agents("test", top_k=50)
            # Verify the request body has topK capped at 10
            call_args = mock_open.call_args
            request = call_args[0][0]
            body = json.loads(request.data.decode())
            assert body["topK"] == 10

    def test_tier_filter(self):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"matches": []}).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with (
            patch.dict("os.environ", {"POPKIT_API_KEY": "test-key"}),
            patch("urllib.request.urlopen", return_value=mock_response) as mock_open,
        ):
            search_agents("test", tier="tier-1")
            request = mock_open.call_args[0][0]
            body = json.loads(request.data.decode())
            assert body["tier"] == "tier-1"

    def test_http_error(self):
        error = urllib.error.HTTPError("https://api.example.com", 500, "Server Error", {}, None)
        with (
            patch.dict("os.environ", {"POPKIT_API_KEY": "test-key"}),
            patch("urllib.request.urlopen", side_effect=error),
        ):
            result = search_agents("test")
            assert result.fallback_to_keywords is True
            assert "500" in result.error

    def test_url_error(self):
        error = urllib.error.URLError("Network unreachable")
        with (
            patch.dict("os.environ", {"POPKIT_API_KEY": "test-key"}),
            patch("urllib.request.urlopen", side_effect=error),
        ):
            result = search_agents("test")
            assert result.fallback_to_keywords is True
            assert "Connection error" in result.error

    def test_timeout_error(self):
        with (
            patch.dict("os.environ", {"POPKIT_API_KEY": "test-key"}),
            patch("urllib.request.urlopen", side_effect=TimeoutError),
        ):
            result = search_agents("test")
            assert result.fallback_to_keywords is True
            assert "timeout" in result.error.lower()

    def test_generic_exception(self):
        with (
            patch.dict("os.environ", {"POPKIT_API_KEY": "test-key"}),
            patch("urllib.request.urlopen", side_effect=ValueError("bad")),
        ):
            result = search_agents("test")
            assert result.fallback_to_keywords is True


# =============================================================================
# Version Header
# =============================================================================


class TestVersionHeader:
    """Test that version header uses dynamic version."""

    def test_uses_dynamic_version(self):
        from popkit_shared import __version__

        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({"matches": []}).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with (
            patch.dict("os.environ", {"POPKIT_API_KEY": "test-key"}),
            patch("urllib.request.urlopen", return_value=mock_response) as mock_open,
        ):
            search_agents("test")
            request = mock_open.call_args[0][0]
            assert request.headers["X-popkit-version"] == __version__


# =============================================================================
# list_agents
# =============================================================================


class TestListAgents:
    """Test list_agents function."""

    def test_no_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            assert list_agents() == []

    def test_successful_list(self):
        response_data = {
            "agents": [
                {"id": "a1", "name": "Agent 1"},
                {"id": "a2", "name": "Agent 2"},
            ]
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with (
            patch.dict("os.environ", {"POPKIT_API_KEY": "test-key"}),
            patch("urllib.request.urlopen", return_value=mock_response),
        ):
            agents = list_agents()
            assert len(agents) == 2

    def test_error_returns_empty(self):
        with (
            patch.dict("os.environ", {"POPKIT_API_KEY": "test-key"}),
            patch("urllib.request.urlopen", side_effect=Exception("fail")),
        ):
            assert list_agents() == []


# =============================================================================
# get_agent
# =============================================================================


class TestGetAgent:
    """Test get_agent function."""

    def test_no_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            assert get_agent("test") is None

    def test_successful_get(self):
        response_data = {"id": "a1", "name": "Agent 1", "tier": "tier-1"}
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(response_data).encode()
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)

        with (
            patch.dict("os.environ", {"POPKIT_API_KEY": "test-key"}),
            patch("urllib.request.urlopen", return_value=mock_response),
        ):
            agent = get_agent("a1")
            assert agent["name"] == "Agent 1"

    def test_error_returns_none(self):
        with (
            patch.dict("os.environ", {"POPKIT_API_KEY": "test-key"}),
            patch("urllib.request.urlopen", side_effect=Exception("fail")),
        ):
            assert get_agent("test") is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
