#!/usr/bin/env python3
"""
Tests for benchmark_responses.py

Tests the benchmark automation utility that provides pre-defined responses
during benchmarking mode to avoid requiring human interaction.
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import popkit_shared.utils.benchmark_responses as br

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(autouse=True)
def reset_cache():
    """Reset the module-level responses cache between tests."""
    br._responses_cache = None
    yield
    br._responses_cache = None


@pytest.fixture
def response_file(tmp_path):
    """Create a temporary response file with test data."""
    data = {
        "responses": {
            "Auth method": "JWT (jsonwebtoken library)",
            "Token storage": "HTTP-only cookies",
            "Token expiry": "1 hour",
        },
        "standardAutoApprove": [
            "install.*dependencies",
            "run.*tests",
            "commit.*changes",
        ],
        "explicitDeclines": [
            "delete.*database",
            "drop.*table",
        ],
    }
    file_path = tmp_path / "test-responses.json"
    file_path.write_text(json.dumps(data))
    return str(file_path)


# =============================================================================
# is_benchmark_mode Tests
# =============================================================================


class TestIsBenchmarkMode:
    """Test benchmark mode detection."""

    def test_not_benchmark_mode_by_default(self):
        """Default should not be benchmark mode."""
        with patch.object(br, "BENCHMARK_MODE", False):
            assert br.is_benchmark_mode() is False

    def test_benchmark_mode_when_enabled(self):
        """Should detect benchmark mode when BENCHMARK_MODE is True."""
        with patch.object(br, "BENCHMARK_MODE", True):
            assert br.is_benchmark_mode() is True


# =============================================================================
# load_responses Tests
# =============================================================================


class TestLoadResponses:
    """Test response file loading."""

    def test_load_valid_response_file(self, response_file):
        """Should load and parse a valid response file."""
        with patch.object(br, "RESPONSE_FILE", response_file):
            data = br.load_responses()

        assert "responses" in data
        assert data["responses"]["Auth method"] == "JWT (jsonwebtoken library)"
        assert len(data["standardAutoApprove"]) == 3
        assert len(data["explicitDeclines"]) == 2

    def test_load_empty_response_file_path(self):
        """Should return defaults when no response file path is set."""
        with patch.object(br, "RESPONSE_FILE", ""):
            data = br.load_responses()

        assert data["responses"] == {}
        assert data["standardAutoApprove"] == []
        assert data["explicitDeclines"] == []

    def test_load_nonexistent_file(self):
        """Should return defaults when response file doesn't exist."""
        with patch.object(br, "RESPONSE_FILE", "/nonexistent/responses.json"):
            data = br.load_responses()

        assert data["responses"] == {}

    def test_load_invalid_json_file(self, tmp_path):
        """Should return defaults for invalid JSON."""
        bad_file = tmp_path / "bad.json"
        bad_file.write_text("not valid json {{{")

        with patch.object(br, "RESPONSE_FILE", str(bad_file)):
            data = br.load_responses()

        assert data["responses"] == {}

    def test_caches_responses(self, response_file):
        """Should cache responses after first load."""
        with patch.object(br, "RESPONSE_FILE", response_file):
            data1 = br.load_responses()
            data2 = br.load_responses()

        assert data1 is data2  # Same object (cached)


# =============================================================================
# get_response Tests
# =============================================================================


class TestGetResponse:
    """Test response retrieval logic."""

    def test_returns_none_when_not_benchmark_mode(self):
        """Should return None when not in benchmark mode."""
        with patch.object(br, "BENCHMARK_MODE", False):
            result = br.get_response("Auth method", "What auth method?")
        assert result is None

    def test_returns_explicit_response_by_header(self, response_file):
        """Should return explicit response matching question header."""
        with (
            patch.object(br, "BENCHMARK_MODE", True),
            patch.object(br, "RESPONSE_FILE", response_file),
        ):
            result = br.get_response("Auth method")
        assert result == "JWT (jsonwebtoken library)"

    def test_returns_explicit_response_for_token_storage(self, response_file):
        """Should return explicit response for Token storage."""
        with (
            patch.object(br, "BENCHMARK_MODE", True),
            patch.object(br, "RESPONSE_FILE", response_file),
        ):
            result = br.get_response("Token storage")
        assert result == "HTTP-only cookies"

    def test_returns_false_for_explicit_decline(self, response_file):
        """Should return False for questions matching explicitDeclines."""
        with (
            patch.object(br, "BENCHMARK_MODE", True),
            patch.object(br, "RESPONSE_FILE", response_file),
        ):
            result = br.get_response("Confirm", "Should we delete database?")
        assert result is False

    def test_returns_true_for_auto_approve_pattern(self, response_file):
        """Should return True for questions matching standardAutoApprove."""
        with (
            patch.object(br, "BENCHMARK_MODE", True),
            patch.object(br, "RESPONSE_FILE", response_file),
        ):
            result = br.get_response("Confirm", "Do you want to install dependencies?")
        assert result is True

    def test_returns_true_for_unknown_question(self, response_file):
        """Should return True (auto-select first option) for unknown questions."""
        with (
            patch.object(br, "BENCHMARK_MODE", True),
            patch.object(br, "RESPONSE_FILE", response_file),
        ):
            result = br.get_response("Unknown header", "Some random question?")
        assert result is True

    def test_explicit_decline_takes_priority_over_auto_approve(self, response_file):
        """Explicit declines should take priority over auto-approve patterns."""
        with (
            patch.object(br, "BENCHMARK_MODE", True),
            patch.object(br, "RESPONSE_FILE", response_file),
        ):
            # This matches both explicitDeclines and could match auto-approve
            result = br.get_response("Action", "Please delete database and run tests")
        assert result is False


# =============================================================================
# should_skip_question Tests
# =============================================================================


class TestShouldSkipQuestion:
    """Test question skip logic."""

    def test_should_not_skip_when_not_benchmark_mode(self):
        """Should not skip when not in benchmark mode."""
        with patch.object(br, "BENCHMARK_MODE", False):
            assert br.should_skip_question("Auth method") is False

    def test_should_skip_with_explicit_response(self, response_file):
        """Should skip when explicit response exists."""
        with (
            patch.object(br, "BENCHMARK_MODE", True),
            patch.object(br, "RESPONSE_FILE", response_file),
        ):
            assert br.should_skip_question("Auth method") is True

    def test_should_skip_for_auto_approve(self, response_file):
        """Should skip for auto-approve patterns."""
        with (
            patch.object(br, "BENCHMARK_MODE", True),
            patch.object(br, "RESPONSE_FILE", response_file),
        ):
            assert br.should_skip_question("Confirm", "run tests") is True

    def test_should_skip_for_unknown_question(self, response_file):
        """Should skip for unknown questions (defaults to True)."""
        with (
            patch.object(br, "BENCHMARK_MODE", True),
            patch.object(br, "RESPONSE_FILE", response_file),
        ):
            assert br.should_skip_question("Unknown", "Whatever") is True


# =============================================================================
# format_response_for_tool Tests
# =============================================================================


class TestFormatResponseForTool:
    """Test response formatting for AskUserQuestion tool results."""

    def test_format_true_with_options(self):
        """True response should select first option."""
        options = [
            {"label": "Option A", "description": "First"},
            {"label": "Option B", "description": "Second"},
        ]
        result = br.format_response_for_tool(True, "Test", options)
        assert result == {"Test": "Option A"}

    def test_format_true_without_options(self):
        """True response without options should return 'yes'."""
        result = br.format_response_for_tool(True, "Test", None)
        assert result == {"Test": "yes"}

    def test_format_false_with_no_option(self):
        """False response should select 'no' option if present."""
        options = [
            {"label": "Yes", "description": "Proceed"},
            {"label": "No", "description": "Cancel"},
        ]
        result = br.format_response_for_tool(False, "Test", options)
        assert result == {"Test": "No"}

    def test_format_false_with_skip_option(self):
        """False response should select 'skip' option if present."""
        options = [
            {"label": "Proceed", "description": "Go ahead"},
            {"label": "Skip", "description": "Skip this step"},
        ]
        result = br.format_response_for_tool(False, "Test", options)
        assert result == {"Test": "Skip"}

    def test_format_false_falls_back_to_last_option(self):
        """False response should fall back to last option if no 'no' option."""
        options = [
            {"label": "Option A", "description": "First"},
            {"label": "Option B", "description": "Second"},
        ]
        result = br.format_response_for_tool(False, "Test", options)
        assert result == {"Test": "Option B"}

    def test_format_false_without_options(self):
        """False response without options should return 'no'."""
        result = br.format_response_for_tool(False, "Test", None)
        assert result == {"Test": "no"}

    def test_format_string_response(self):
        """String response should be returned directly."""
        result = br.format_response_for_tool("JWT tokens", "Auth method", None)
        assert result == {"Auth method": "JWT tokens"}

    def test_format_list_response(self):
        """List response should be joined with comma."""
        result = br.format_response_for_tool(["Option A", "Option B"], "Features", None)
        assert result == {"Features": "Option A, Option B"}

    def test_format_dict_with_other_key(self):
        """Dict with 'other' key should extract free-text response."""
        result = br.format_response_for_tool({"other": "Custom response"}, "Custom", None)
        assert result == {"Custom": "Custom response"}

    def test_format_unknown_type_with_options(self):
        """Unknown type with options should fall back to first option."""
        options = [{"label": "Default", "description": "Fallback"}]
        result = br.format_response_for_tool(42, "Test", options)
        assert result == {"Test": "Default"}

    def test_format_unknown_type_without_options(self):
        """Unknown type without options should convert to string."""
        result = br.format_response_for_tool(42, "Test", None)
        assert result == {"Test": "42"}


# =============================================================================
# log_benchmark_response Tests
# =============================================================================


class TestLogBenchmarkResponse:
    """Test benchmark response logging."""

    def test_logging_does_not_raise(self):
        """Logging should not raise exceptions."""
        # Should work silently when not in verbose mode
        br.log_benchmark_response("Auth", "What auth?", "JWT")

    def test_verbose_logging(self, capsys):
        """Should output to stderr in verbose mode."""
        with patch.dict(os.environ, {"POPKIT_BENCHMARK_VERBOSE": "true"}):
            br.log_benchmark_response("Auth", "What auth?", "JWT")

        captured = capsys.readouterr()
        assert "Auto-response" in captured.err
        assert "Auth" in captured.err


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
