#!/usr/bin/env python3
"""
Tests for project_registry.py GitHub issue integration.
"""

import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from popkit_shared.utils.project_registry import get_cached_issue_count, fetch_project_issues


def test_get_cached_issue_count_fresh():
    """Test that fresh cache returns the issue count."""
    # Cache is 5 minutes old (TTL is 15 minutes)
    cached_at = (datetime.now() - timedelta(minutes=5)).isoformat()

    project = {
        "name": "test-project",
        "path": "/path/to/project",
        "github_issues": {
            "open_count": 5,
            "cached_at": cached_at
        }
    }

    result = get_cached_issue_count(project)
    assert result == "5", f"Expected '5', got '{result}'"


def test_get_cached_issue_count_stale():
    """Test that stale cache returns '--'."""
    # Cache is 20 minutes old (TTL is 15 minutes)
    cached_at = (datetime.now() - timedelta(minutes=20)).isoformat()

    project = {
        "name": "test-project",
        "path": "/path/to/project",
        "github_issues": {
            "open_count": 5,
            "cached_at": cached_at
        }
    }

    result = get_cached_issue_count(project)
    assert result == "--", f"Expected '--', got '{result}'"


def test_get_cached_issue_count_missing():
    """Test that missing cache data returns '--'."""
    # Project with no github_issues field
    project = {
        "name": "test-project",
        "path": "/path/to/project"
    }

    result = get_cached_issue_count(project)
    assert result == "--", f"Expected '--', got '{result}'"


def test_get_cached_issue_count_invalid_format():
    """Test that invalid timestamp format returns '--'."""
    project = {
        "name": "test-project",
        "path": "/path/to/project",
        "github_issues": {
            "open_count": 5,
            "cached_at": "invalid-timestamp"
        }
    }

    result = get_cached_issue_count(project)
    assert result == "--", f"Expected '--', got '{result}'"


@patch("subprocess.run")
def test_fetch_project_issues_success(mock_run):
    """Test successful issue fetching via gh CLI."""
    # Mock successful gh CLI response
    mock_result = MagicMock()
    mock_result.returncode = 0
    mock_result.stdout = json.dumps([
        {"number": 1},
        {"number": 2},
        {"number": 3}
    ])
    mock_run.return_value = mock_result

    result = fetch_project_issues("/path/to/project", timeout=5)
    assert result == 3, f"Expected 3, got {result}"

    # Verify gh CLI was called correctly
    mock_run.assert_called_once()
    call_args = mock_run.call_args
    assert call_args[0][0][0] == "gh"
    assert call_args[0][0][1] == "issue"
    assert call_args[0][0][2] == "list"


@patch("subprocess.run")
def test_fetch_project_issues_failure(mock_run):
    """Test failed issue fetching returns None."""
    # Mock gh CLI failure
    mock_result = MagicMock()
    mock_result.returncode = 1
    mock_result.stderr = "fatal: not a git repository"
    mock_run.return_value = mock_result

    result = fetch_project_issues("/path/to/nonexistent", timeout=5)
    assert result is None, f"Expected None, got {result}"
