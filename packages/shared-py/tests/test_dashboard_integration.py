#!/usr/bin/env python3
"""
Integration tests for GitHub issue dashboard integration.

Tests the complete workflow:
1. Dashboard displays '--' for uncached projects
2. Refresh fetches and caches issue counts
3. Dashboard displays cached counts
4. Stale cache returns '--'
"""

import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from popkit_shared.utils.project_registry import (
    get_cached_issue_count,
    fetch_project_issues,
    refresh_project_issue_counts,
    format_dashboard
)


@patch("popkit_shared.utils.project_registry.fetch_project_issues")
def test_full_dashboard_workflow(mock_fetch):
    """Test complete workflow: display → refresh → display with cache."""
    # Step 1: Create registry with projects (no cached data)
    registry = {
        "projects": [
            {"name": "project1", "path": "/path/1", "healthScore": 92},
            {"name": "project2", "path": "/path/2", "healthScore": 85},
            {"name": "project3", "path": "/path/3", "healthScore": 78}
        ]
    }

    # Step 2: Verify dashboard shows '--' for all projects (no cache)
    for project in registry["projects"]:
        issues = get_cached_issue_count(project)
        assert issues == "--", f"Expected '--', got '{issues}'"

    # Step 3: Mock fetch_project_issues to return counts
    mock_fetch.side_effect = [5, 3, 0]  # Different counts for each project

    # Step 4: Refresh issue counts
    updated_count = refresh_project_issue_counts(registry)

    # Verify all 3 projects were updated
    assert updated_count == 3, f"Expected 3, got {updated_count}"

    # Step 5: Verify cache was populated with correct counts
    assert registry["projects"][0]["github_issues"]["open_count"] == 5
    assert registry["projects"][1]["github_issues"]["open_count"] == 3
    assert registry["projects"][2]["github_issues"]["open_count"] == 0

    # Step 6: Verify cached_at timestamps exist and are recent
    for project in registry["projects"]:
        cached_at_str = project["github_issues"]["cached_at"]
        cached_at = datetime.fromisoformat(cached_at_str)
        age = datetime.now() - cached_at
        assert age.total_seconds() < 5, f"Timestamp too old: {age.total_seconds()}s"

    # Step 7: Verify dashboard displays cached counts
    issues1 = get_cached_issue_count(registry["projects"][0])
    issues2 = get_cached_issue_count(registry["projects"][1])
    issues3 = get_cached_issue_count(registry["projects"][2])

    assert issues1 == "5", f"Expected '5', got '{issues1}'"
    assert issues2 == "3", f"Expected '3', got '{issues2}'"
    assert issues3 == "0", f"Expected '0', got '{issues3}'"


def test_stale_cache_behavior():
    """Test that stale cache (> 15 min) returns '--'."""
    # Create project with stale cache (20 minutes old)
    stale_timestamp = (datetime.now() - timedelta(minutes=20)).isoformat()

    project = {
        "name": "stale-project",
        "path": "/path/to/project",
        "github_issues": {
            "open_count": 10,
            "cached_at": stale_timestamp
        }
    }

    # Verify stale cache returns '--'
    result = get_cached_issue_count(project)
    assert result == "--", f"Expected '--' for stale cache, got '{result}'"


def test_non_github_project():
    """Test that non-GitHub projects show '--'."""
    project = {
        "name": "local-project",
        "path": "/path/to/local"
        # No github_issues field
    }

    result = get_cached_issue_count(project)
    assert result == "--", f"Expected '--' for non-GitHub project, got '{result}'"


@patch("popkit_shared.utils.project_registry.fetch_project_issues")
def test_partial_refresh_failure(mock_fetch):
    """Test that partial failures during refresh are handled gracefully."""
    # Mock: first succeeds, second fails (gh CLI error), third succeeds
    mock_fetch.side_effect = [5, None, 3]

    registry = {
        "projects": [
            {"name": "project1", "path": "/path/1"},
            {"name": "project2", "path": "/path/2"},
            {"name": "project3", "path": "/path/3"}
        ]
    }

    # Refresh
    updated_count = refresh_project_issue_counts(registry)

    # Only 2 projects updated (project2 failed)
    assert updated_count == 2, f"Expected 2, got {updated_count}"

    # Verify successful projects have cache
    assert "github_issues" in registry["projects"][0]
    assert registry["projects"][0]["github_issues"]["open_count"] == 5
    assert "github_issues" in registry["projects"][2]
    assert registry["projects"][2]["github_issues"]["open_count"] == 3

    # Verify failed project has no cache
    assert "github_issues" not in registry["projects"][1]

    # Verify dashboard shows '--' for failed project
    result = get_cached_issue_count(registry["projects"][1])
    assert result == "--", f"Expected '--' for failed project, got '{result}'"


def test_zero_issues_displays_correctly():
    """Test that projects with 0 open issues display '0', not '--'."""
    # Fresh cache with 0 issues
    fresh_timestamp = datetime.now().isoformat()

    project = {
        "name": "zero-issues",
        "path": "/path/to/project",
        "github_issues": {
            "open_count": 0,
            "cached_at": fresh_timestamp
        }
    }

    result = get_cached_issue_count(project)
    assert result == "0", f"Expected '0' for zero issues, got '{result}'"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
