#!/usr/bin/env python3
"""
Sleep Score Calculator for Nightly Routine

Calculates a 0-100 score based on 6 project health dimensions:
1. Uncommitted work saved (25 points)
2. Branches cleaned (20 points)
3. Issues updated (20 points)
4. CI passing (15 points)
5. Services stopped (10 points)
6. Logs archived (10 points)
"""

from datetime import datetime
from typing import Any, Dict, Tuple


def calculate_sleep_score(
    state: Dict[str, Any],
) -> Tuple[int, Dict[str, Dict[str, Any]]]:
    """
    Calculate Sleep Score (0-100) based on project state.

    Args:
        state: Project state from capture_state.py with keys:
            - git: Git context
            - github: GitHub context
            - services: Service status
            - timestamp: ISO timestamp

    Returns:
        Tuple of (score, breakdown) where:
        - score: int 0-100
        - breakdown: dict with scoring details for each check
    """
    score = 0
    breakdown = {}

    # 1. Uncommitted work saved (25 points)
    git_state = state.get("git", {})
    uncommitted_count = git_state.get("uncommitted_files", 0)

    if uncommitted_count == 0:
        score += 25
        breakdown["uncommitted_work_saved"] = {
            "points": 25,
            "max": 25,
            "status": "✅",
            "reason": "No uncommitted changes",
        }
    else:
        breakdown["uncommitted_work_saved"] = {
            "points": 0,
            "max": 25,
            "status": "❌",
            "reason": f"{uncommitted_count} uncommitted files",
        }

    # 2. Branches cleaned (20 points)
    merged_branches = git_state.get("merged_branches", 0)
    stale_branches = git_state.get("stale_branches", 0)

    # Calculate branch cleanup score
    branch_score = 0
    cleanup_reasons = []
    cleanup_status = "✅"

    if merged_branches > 0:
        cleanup_reasons.append(f"{merged_branches} merged branches not deleted")
        cleanup_status = "❌"

    if stale_branches > 0:
        cleanup_reasons.append(
            f"{stale_branches} stale branch{'es' if stale_branches != 1 else ''} (remote deleted)"
        )
        if cleanup_status == "✅":
            cleanup_status = "⚠️"

    if not cleanup_reasons:
        branch_score = 20
        cleanup_status = "✅"
        cleanup_reason = "No stale branches"
    else:
        # Deduct points for cleanup issues
        # 10 points for merged branches, 10 points for stale branches
        if merged_branches == 0:
            branch_score = max(0, 20 - min(stale_branches * 2, 10))
        cleanup_reason = "; ".join(cleanup_reasons)

    score += branch_score
    breakdown["branches_cleaned"] = {
        "points": branch_score,
        "max": 20,
        "status": cleanup_status,
        "reason": cleanup_reason,
    }

    # 3. Issues updated (20 points)
    github_state = state.get("github", {})
    issues = github_state.get("issues", [])
    today = datetime.now().strftime("%Y-%m-%d")

    if issues:
        # Check if all issues were updated today
        updated_today = all(today in issue.get("updatedAt", "") for issue in issues)

        if updated_today:
            score += 20
            breakdown["issues_updated"] = {
                "points": 20,
                "max": 20,
                "status": "✅",
                "reason": f"All {len(issues)} issues updated today",
            }
        else:
            breakdown["issues_updated"] = {
                "points": 10,  # Partial credit
                "max": 20,
                "status": "⚠️",
                "reason": "Some issues not updated today",
            }
            score += 10
    else:
        # No open issues = good
        score += 20
        breakdown["issues_updated"] = {
            "points": 20,
            "max": 20,
            "status": "✅",
            "reason": "No open issues",
        }

    # 4. CI passing (15 points)
    ci_status = github_state.get("ci_status", {})
    ci_conclusion = ci_status.get("conclusion", "unknown")

    if ci_conclusion == "success":
        score += 15
        breakdown["ci_passing"] = {
            "points": 15,
            "max": 15,
            "status": "✅",
            "reason": "Latest CI run successful",
        }
    elif ci_conclusion == "skipped":
        breakdown["ci_passing"] = {
            "points": 0,
            "max": 15,
            "status": "❌",
            "reason": "Latest CI run skipped",
        }
    elif ci_conclusion == "failure":
        breakdown["ci_passing"] = {
            "points": 0,
            "max": 15,
            "status": "❌",
            "reason": "Latest CI run failed",
        }
    else:
        # Unknown/pending
        breakdown["ci_passing"] = {
            "points": 0,
            "max": 15,
            "status": "⚠️",
            "reason": f"CI status: {ci_conclusion}",
        }

    # 5. Services stopped (10 points)
    services_state = state.get("services", {})
    running_services = services_state.get("running_services", [])

    if not running_services:
        score += 10
        breakdown["services_stopped"] = {
            "points": 10,
            "max": 10,
            "status": "✅",
            "reason": "No dev services running",
        }
    else:
        breakdown["services_stopped"] = {
            "points": 0,
            "max": 10,
            "status": "❌",
            "reason": f"{len(running_services)} services still running",
        }

    # 6. Logs archived (10 points)
    log_count = services_state.get("log_files", 0)

    if log_count == 0:
        score += 10
        breakdown["logs_archived"] = {
            "points": 10,
            "max": 10,
            "status": "✅",
            "reason": "No logs to archive",
        }
    else:
        # Partial credit if logs exist but aren't excessive
        if log_count <= 5:
            score += 5
            breakdown["logs_archived"] = {
                "points": 5,
                "max": 10,
                "status": "⚠️",
                "reason": f"{log_count} log files to archive",
            }
        else:
            breakdown["logs_archived"] = {
                "points": 0,
                "max": 10,
                "status": "❌",
                "reason": f"{log_count} log files to archive",
            }

    return score, breakdown


def get_score_interpretation(score: int) -> Dict[str, str]:
    """
    Get human-readable interpretation of Sleep Score.

    Args:
        score: Sleep Score (0-100)

    Returns:
        dict with keys:
        - grade: Letter grade (A+, A, B, etc.)
        - emoji: Visual indicator
        - interpretation: Text description
        - recommendation: What to do
    """
    if score >= 90:
        return {
            "grade": "A+",
            "emoji": "🌟",
            "interpretation": "Perfect shutdown - ready for tomorrow",
            "recommendation": "Great job! Your project is in excellent shape.",
        }
    elif score >= 80:
        return {
            "grade": "A",
            "emoji": "✅",
            "interpretation": "Excellent - very clean state",
            "recommendation": "Almost perfect. Minor cleanup if time permits.",
        }
    elif score >= 70:
        return {
            "grade": "B",
            "emoji": "👍",
            "interpretation": "Good - minor cleanup needed",
            "recommendation": "A few items to address before leaving.",
        }
    elif score >= 60:
        return {
            "grade": "C",
            "emoji": "⚠️",
            "interpretation": "Fair - some uncommitted work or issues",
            "recommendation": "Consider committing or stashing changes.",
        }
    elif score >= 50:
        return {
            "grade": "D",
            "emoji": "⚠️",
            "interpretation": "Below average - attention needed",
            "recommendation": "Spend a few minutes cleaning up before leaving.",
        }
    else:
        return {
            "grade": "F",
            "emoji": "❌",
            "interpretation": "Poor - significant cleanup required",
            "recommendation": "Take time to address issues before leaving.",
        }


def format_breakdown_table(breakdown: Dict[str, Dict[str, Any]]) -> str:
    """
    Format score breakdown as markdown table.

    Args:
        breakdown: Score breakdown from calculate_sleep_score

    Returns:
        Markdown table string
    """
    table = "| Check | Points | Status |\n"
    table += "|-------|--------|--------|\n"

    check_names = {
        "uncommitted_work_saved": "Uncommitted work saved",
        "branches_cleaned": "Branches cleaned",
        "issues_updated": "Issues updated",
        "ci_passing": "CI passing",
        "services_stopped": "Services stopped",
        "logs_archived": "Logs archived",
    }

    for key, name in check_names.items():
        if key in breakdown:
            item = breakdown[key]
            points = item["points"]
            max_points = item["max"]
            status = item["status"]
            reason = item["reason"]

            table += f"| {name} | {points}/{max_points} | {status} {reason} |\n"

    return table


if __name__ == "__main__":
    # Test with sample data
    sample_state = {
        "git": {"uncommitted_files": 3, "merged_branches": 0, "stashes": 8},
        "github": {
            "issues": [
                {
                    "number": 629,
                    "title": "Feature A",
                    "updatedAt": "2025-12-28T10:00:00Z",
                },
                {
                    "number": 628,
                    "title": "Feature B",
                    "updatedAt": "2025-12-28T11:00:00Z",
                },
            ],
            "ci_status": {"conclusion": "skipped", "status": "completed"},
        },
        "services": {"running_services": [], "log_files": 0},
        "timestamp": "2025-12-28T15:30:00Z",
    }

    score, breakdown = calculate_sleep_score(sample_state)
    interpretation = get_score_interpretation(score)

    print(f"Sleep Score: {score}/100 {interpretation['emoji']}")
    print(f"Grade: {interpretation['grade']}")
    print(f"Interpretation: {interpretation['interpretation']}")
    print()
    print(format_breakdown_table(breakdown))
