#!/usr/bin/env python3
"""
Tests for project_registry.py GitHub issue integration.
"""

import pytest
from datetime import datetime, timedelta
from popkit_shared.utils.project_registry import get_cached_issue_count


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
