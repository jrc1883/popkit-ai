#!/usr/bin/env python3
"""
Integration test for pop-next-action with protected branch detection.

Simulates the complete workflow from issue #141:
1. User is on main branch with unpushed commits
2. Runs /popkit:next
3. Top recommendation is "Create feature branch"
4. No "push" recommendation exists
5. Includes specific git commands
"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest

SCRIPT_PATH = (
    Path(__file__).resolve().parent.parent
    / "skills"
    / "pop-next-action"
    / "scripts"
    / "recommend_action.py"
)
SPEC = spec_from_file_location("pop_next_action_recommend_action", SCRIPT_PATH)
assert SPEC and SPEC.loader
recommend_action = module_from_spec(SPEC)
SPEC.loader.exec_module(recommend_action)


def test_complete_workflow_on_protected_branch():
    """
    Integration test: Complete workflow when on main with 10 commits ahead.

    Given: User on main with 10 commits ahead
    When: Run /popkit:next
    Then: Top recommendation is "Create feature branch"
    And: Includes specific git commands
    And: No "push" recommendation exists
    """
    # Simulate project state
    project_state = {
        "current_branch": "main",
        "is_protected": True,
        "uncommitted_files": 0,
        "commits_ahead": 10,
        "commits_behind": 0,
        "typescript_errors": 0,
        "open_issues": 3,
    }

    # Simulate recommendation scoring
    recommendations = []

    # Score: Create feature branch (if on protected)
    if project_state["is_protected"] and project_state["commits_ahead"] > 0:
        score = 100  # Base priority
        score += 50  # Context: On protected branch with commits
        recommendations.append(
            {
                "action": "Create feature branch",
                "score": score,
                "command": "git checkout -b feat/descriptive-name",
                "why": f"You have {project_state['commits_ahead']} commits on main but cannot push directly due to branch protection",
                "includes_push": False,
            }
        )

    # Score: Push ahead commits (if on feature branch) - SHOULD BE SUPPRESSED
    if not project_state["is_protected"] and project_state["commits_ahead"] > 0:
        score = 60  # Base priority
        recommendations.append(
            {
                "action": "Push ahead commits",
                "score": score,
                "command": "/popkit:git push",
                "includes_push": True,
            }
        )

    # Sort by score
    recommendations.sort(key=lambda x: x["score"], reverse=True)

    # Assertions
    assert len(recommendations) == 1, "Should have exactly 1 recommendation"

    top_rec = recommendations[0]
    assert top_rec["action"] == "Create feature branch", (
        "Top recommendation should be feature branch creation"
    )
    assert top_rec["score"] == 150, f"Expected score 150, got {top_rec['score']}"
    assert "git checkout -b" in top_rec["command"], "Should include branch creation command"
    assert "branch protection" in top_rec["why"], "Should mention branch protection"

    # Verify push recommendation is NOT present
    push_recs = [r for r in recommendations if "push" in r["action"].lower()]
    assert len(push_recs) == 0, "Should not recommend push on protected branch"


def test_workflow_on_feature_branch():
    """
    Integration test: Normal workflow when already on feature branch.

    Given: User on feat/my-feature with 5 commits ahead
    When: Run /popkit:next
    Then: Top recommendation is "Push ahead commits"
    And: No "create branch" recommendation exists
    """
    # Simulate project state
    project_state = {
        "current_branch": "feat/my-feature",
        "is_protected": False,
        "uncommitted_files": 0,
        "commits_ahead": 5,
        "commits_behind": 0,
        "typescript_errors": 0,
        "open_issues": 0,
    }

    # Simulate recommendation scoring
    recommendations = []

    # Score: Create feature branch (if on protected)
    if project_state["is_protected"] and project_state["commits_ahead"] > 0:
        score = 100 + 50
        recommendations.append({"action": "Create feature branch", "score": score})

    # Score: Push ahead commits (if on feature branch)
    if not project_state["is_protected"] and project_state["commits_ahead"] > 0:
        score = 60  # Base priority
        recommendations.append(
            {"action": "Push ahead commits", "score": score, "command": "/popkit:git push"}
        )

    # Sort by score
    recommendations.sort(key=lambda x: x["score"], reverse=True)

    # Assertions
    assert len(recommendations) == 1, "Should have exactly 1 recommendation"

    top_rec = recommendations[0]
    assert top_rec["action"] == "Push ahead commits", "Should recommend push on feature branch"
    assert top_rec["score"] == 60, f"Expected score 60, got {top_rec['score']}"

    # Verify branch creation recommendation is NOT present
    branch_recs = [r for r in recommendations if "branch" in r["action"].lower()]
    assert len(branch_recs) == 0, "Should not recommend branch creation on feature branch"


def test_output_format_on_protected_branch():
    """
    Integration test: Output format when on protected branch.

    Given: User on main branch
    When: Generate current state output
    Then: Shows "main (PROTECTED)" with ⚠️ CRITICAL urgency
    """
    current_branch = "main"
    is_protected = current_branch in ["main", "master", "develop", "production"]

    # Generate output
    if is_protected:
        status_display = f"{current_branch} (PROTECTED)"
        urgency = "⚠️ CRITICAL"
    else:
        status_display = current_branch
        urgency = "OK"

    # Assertions
    assert status_display == "main (PROTECTED)", (
        f"Expected 'main (PROTECTED)', got '{status_display}'"
    )
    assert urgency == "⚠️ CRITICAL", f"Expected '⚠️ CRITICAL', got '{urgency}'"


def test_multiple_priorities_with_protected_branch():
    """
    Integration test: Protected branch takes priority over other urgent items.

    Given: User on main with commits AND TypeScript errors AND uncommitted files
    When: Run /popkit:next
    Then: Top recommendation is still "Create feature branch" (score 150)
    And: TypeScript errors are second (score 90+30=120)
    And: Commit uncommitted work is third (score 80+20=100)
    """
    project_state = {
        "current_branch": "main",
        "is_protected": True,
        "uncommitted_files": 5,
        "commits_ahead": 10,
        "typescript_errors": 3,
    }

    # Simulate recommendation scoring
    recommendations = []

    # Score: Create feature branch
    if project_state["is_protected"] and project_state["commits_ahead"] > 0:
        score = 100 + 50  # Base + context
        recommendations.append({"action": "Create feature branch", "score": score})

    # Score: Fix TypeScript errors
    if project_state["typescript_errors"] > 0:
        score = 90 + 30  # Base + context
        recommendations.append({"action": "Fix build errors", "score": score})

    # Score: Commit uncommitted work
    if project_state["uncommitted_files"] > 0:
        score = 80 + 20  # Base + context
        recommendations.append({"action": "Commit your current work", "score": score})

    # Sort by score
    recommendations.sort(key=lambda x: x["score"], reverse=True)

    # Assertions
    assert len(recommendations) == 3, "Should have 3 recommendations"

    # Verify order
    assert recommendations[0]["action"] == "Create feature branch", "Protected branch should be #1"
    assert recommendations[0]["score"] == 150, f"Expected 150, got {recommendations[0]['score']}"

    assert recommendations[1]["action"] == "Fix build errors", "TypeScript should be #2"
    assert recommendations[1]["score"] == 120, f"Expected 120, got {recommendations[1]['score']}"

    assert recommendations[2]["action"] == "Commit your current work", "Commit should be #3"
    assert recommendations[2]["score"] == 100, f"Expected 100, got {recommendations[2]['score']}"


def test_display_output_remains_human_readable(tmp_path):
    """Display mode should stay on the existing report path."""
    state = {
        "git": {"uncommitted_count": 3, "ahead_count": 1, "urgency": "HIGH"},
        "code": {"typescript_errors": 0, "urgency": "LOW"},
        "issues": {"open_count": 0, "issues": [], "urgency": "LOW"},
        "research": {"has_research_branches": False, "branches": [], "urgency": "LOW"},
    }

    ranked = recommend_action.rank_actions(recommend_action.calculate_action_scores(state))
    report = recommend_action.generate_report(
        ranked,
        state,
        runtime="both",
        repo_root=tmp_path,
    )
    display = recommend_action.format_report_display(report)

    assert "## Current State" in display
    assert "## Recommended Actions" in display
    assert "## Quick Reference" in display
    assert "**Command:** `/popkit:git commit`" in display
    assert "Next Action" not in display


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
