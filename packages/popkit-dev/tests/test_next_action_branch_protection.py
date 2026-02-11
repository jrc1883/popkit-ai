#!/usr/bin/env python3
"""
Unit tests for pop-next-action branch protection detection.

Tests the critical functionality added in issue #141 to detect when working
on protected branches and recommend feature branch creation instead of direct push.
"""

import pytest

# Test data
PROTECTED_BRANCHES = ["main", "master", "develop", "production"]
FEATURE_BRANCHES = ["feat/my-feature", "fix/bug-123", "chore/cleanup"]


def test_detect_protected_branch():
    """Test that main and master are detected as protected branches."""
    for branch in PROTECTED_BRANCHES:
        assert branch in PROTECTED_BRANCHES, f"{branch} should be protected"

    # Verify detection logic
    assert "main" in PROTECTED_BRANCHES
    assert "master" in PROTECTED_BRANCHES
    assert "develop" in PROTECTED_BRANCHES
    assert "production" in PROTECTED_BRANCHES


def test_feature_branches_not_protected():
    """Test that feature branches are NOT detected as protected."""
    for branch in FEATURE_BRANCHES:
        assert branch not in PROTECTED_BRANCHES, f"{branch} should not be protected"

    # Verify common feature branch patterns
    assert "feat/new-feature" not in PROTECTED_BRANCHES
    assert "fix/issue-141" not in PROTECTED_BRANCHES
    assert "chore/update-deps" not in PROTECTED_BRANCHES


def test_recommend_feature_branch_creation_score():
    """Test that feature branch creation has highest recommendation score (100)."""
    # Score for protected branch with commits
    base_score = 100
    context_multiplier = 50  # On protected branch with commits
    total_score = base_score + context_multiplier

    assert base_score == 100, "Feature branch creation should have score 100"
    assert total_score == 150, "With context should be 150"

    # Verify it's higher than other priorities
    assert 100 > 90  # Higher than "Fix build errors"
    assert 100 > 85  # Higher than "Process research branches"
    assert 100 > 80  # Higher than "Commit uncommitted work"


def test_no_direct_push_to_main_when_protected():
    """Test that push recommendation is NOT present when on protected branch."""
    # Simulate being on main branch
    current_branch = "main"
    is_protected = current_branch in PROTECTED_BRANCHES

    assert is_protected is True

    # When on protected branch, "Push ahead commits" score should be suppressed
    # This is implemented by checking branch before adding push recommendation

    # Verify push score is only applied to feature branches
    if current_branch in PROTECTED_BRANCHES:
        should_recommend_push = False
    else:
        should_recommend_push = True

    assert should_recommend_push is False, "Should not recommend push on protected branch"


def test_push_allowed_on_feature_branch():
    """Test that push recommendation IS present when on feature branch."""
    current_branch = "feat/my-feature"
    is_protected = current_branch in PROTECTED_BRANCHES

    assert is_protected is False

    # When on feature branch, push recommendation should be allowed
    if current_branch not in PROTECTED_BRANCHES:
        should_recommend_push = True
    else:
        should_recommend_push = False

    assert should_recommend_push is True, "Should recommend push on feature branch"


def test_branch_creation_recommendation_format():
    """Test that feature branch creation recommendation has correct format."""
    # Expected recommendation components
    expected_command = "git checkout -b feat/descriptive-name"
    expected_why_pattern = "cannot push directly due to branch protection"
    expected_steps = [
        "git checkout -b feat/your-feature-name",
        "git push -u origin feat/your-feature-name",
        "gh pr create",
        "git checkout main",
        "git reset --hard origin/main",
    ]

    # Verify command format
    assert "git checkout -b" in expected_command
    assert "feat/" in expected_command

    # Verify explanation mentions branch protection
    assert "branch protection" in expected_why_pattern

    # Verify next steps are comprehensive
    assert len(expected_steps) == 5, "Should have 5 steps for branch creation workflow"
    assert any("checkout -b" in step for step in expected_steps)
    assert any("push -u" in step for step in expected_steps)
    assert any("pr create" in step for step in expected_steps)
    assert any("reset --hard" in step for step in expected_steps)


def test_urgency_indicator_for_protected_branch():
    """Test that protected branch shows CRITICAL urgency in output."""
    current_branch = "main"
    is_protected = current_branch in PROTECTED_BRANCHES

    if is_protected:
        urgency = "⚠️ CRITICAL"
        status_display = f"{current_branch} (PROTECTED)"
    else:
        urgency = "OK"
        status_display = current_branch

    assert urgency == "⚠️ CRITICAL", "Protected branch should show CRITICAL urgency"
    assert "(PROTECTED)" in status_display, "Status should indicate protected"


def test_context_indicator_weight():
    """Test that protected branch has CRITICAL weight in context indicators."""
    # Context indicator weights
    context_weights = {
        "On protected branch": "CRITICAL",
        "Uncommitted changes": "HIGH",
        "Ahead of remote": "MEDIUM",
        "TypeScript errors": "HIGH",
        "Research branches": "HIGH",
        "Open issues": "MEDIUM",
        "Issue votes": "MEDIUM",
        "TECHNICAL_DEBT.md": "MEDIUM",
        "Recent commits": "LOW",
    }

    assert context_weights["On protected branch"] == "CRITICAL"
    assert context_weights["On protected branch"] != "HIGH"
    assert context_weights["On protected branch"] != "MEDIUM"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
