#!/usr/bin/env python3
"""
Morning Report Generator

Generates formatted morning routine reports with Ready to Code Score,
setup recommendations, and today's action items.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List

# Try relative import (when used as package), fall back to direct import
try:
    from .ready_to_code_score import format_breakdown_table, get_score_interpretation
except ImportError:
    from ready_to_code_score import format_breakdown_table, get_score_interpretation


def generate_morning_report(
    score: int, breakdown: Dict[str, Dict[str, Any]], state: Dict[str, Any]
) -> str:
    """
    Generate complete morning routine report.

    Args:
        score: Ready to Code Score (0-100)
        breakdown: Score breakdown from calculate_ready_to_code_score()
        state: Full project state

    Returns:
        Formatted markdown report string
    """
    interpretation = get_score_interpretation(score)

    report_lines = [
        "# ☀️ Morning Routine Report",
        "",
        f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**Ready to Code Score**: {score}/100 {interpretation['emoji']}",
        f"**Grade**: {interpretation['grade']} - {interpretation['interpretation']}",
        "",
        "## Score Breakdown",
        "",
        format_breakdown_table(breakdown),
        "",
    ]

    # Add session branches section if there are unmerged branches
    session_branches_breakdown = breakdown.get("session_branches_clean", {})
    if session_branches_breakdown.get("points", 0) < session_branches_breakdown.get(
        "max", 10
    ):
        report_lines.extend(_generate_session_branches_section(state))

    # Add service status if services are not healthy
    services_breakdown = breakdown.get("services_healthy", {})
    if services_breakdown.get("points", 0) < services_breakdown.get("max", 20):
        report_lines.extend(_generate_service_status_section(state))

    # Add dependency updates if there are outdated packages
    deps_breakdown = breakdown.get("dependencies_updated", {})
    if deps_breakdown.get("points", 0) < deps_breakdown.get("max", 15):
        report_lines.extend(_generate_dependencies_section(state))

    # Add branch sync status if behind remote
    branches_breakdown = breakdown.get("branches_synced", {})
    if branches_breakdown.get("points", 0) < branches_breakdown.get("max", 15):
        report_lines.extend(_generate_sync_section(state))

    # Add PR review queue if there are PRs
    prs_breakdown = breakdown.get("prs_reviewed", {})
    if prs_breakdown.get("points", 0) < prs_breakdown.get("max", 15):
        report_lines.extend(_generate_pr_section(state))

    # Add issue triage if there are issues
    issues_breakdown = breakdown.get("issues_triaged", {})
    if issues_breakdown.get("points", 0) < issues_breakdown.get("max", 15):
        report_lines.extend(_generate_issues_section(state))

    # Add recommendations
    report_lines.extend(["## 📋 Recommendations", "", "**Before Starting Work:**"])
    report_lines.extend(
        [f"- {rec}" for rec in _generate_setup_recommendations(score, state)]
    )

    report_lines.extend(["", "**Today's Focus:**"])
    report_lines.extend([f"- {rec}" for rec in _generate_today_recommendations(state)])

    # Add STATUS.json confirmation
    report_lines.extend(
        [
            "",
            "---",
            "",
            "STATUS.json updated ✅",
            "Morning session initialized. Ready to code!",
            "",
            "## 🎯 Next Steps",
            "",
        ]
    )

    # Add PopKit Way ending: AskUserQuestion instructions
    report_lines.extend(_generate_ask_user_question_section(score, breakdown, state))

    return "\n".join(report_lines)


def generate_quick_summary(
    score: int, breakdown: Dict[str, Dict[str, Any]], state: Dict[str, Any]
) -> str:
    """
    Generate one-line summary for quick mode.

    Args:
        score: Ready to Code Score (0-100)
        breakdown: Score breakdown
        state: Full project state

    Returns:
        One-line summary string
    """
    interpretation = get_score_interpretation(score)

    # Collect key issues
    issues = []

    if breakdown.get("services_healthy", {}).get("points", 0) < 20:
        services_data = state.get("services", {})
        required = services_data.get("required_services", [])
        running = services_data.get("running_services", [])
        missing = [s for s in required if s not in running]
        if missing:
            issues.append(f"{len(missing)} services down")

    if breakdown.get("dependencies_updated", {}).get("points", 0) < 15:
        deps_data = state.get("dependencies", {})
        outdated = deps_data.get("outdated_count", 0)
        if outdated > 0:
            issues.append(f"{outdated} outdated deps")

    if breakdown.get("branches_synced", {}).get("points", 0) < 15:
        git_data = state.get("git", {})
        behind = git_data.get("behind_remote", 0)
        if behind > 0:
            issues.append(f"{behind} commits behind")

    if breakdown.get("prs_reviewed", {}).get("points", 0) < 15:
        github_data = state.get("github", {})
        prs = len(github_data.get("prs_needing_review", []))
        if prs > 0:
            issues.append(f"{prs} PRs to review")

    issue_str = ", ".join(issues) if issues else "all clear"
    return f"Ready to Code Score: {score}/100 {interpretation['emoji']} - {issue_str}"


def _generate_service_status_section(state: Dict[str, Any]) -> List[str]:
    """Generate service status section."""
    services_data = state.get("services", {})
    required = services_data.get("required_services", [])
    running = services_data.get("running_services", [])
    missing = [s for s in required if s not in running]

    lines = [
        "## 🔧 Dev Services Status",
        "",
        f"**Required**: {len(required)} services",
        f"**Running**: {len([s for s in required if s in running])} services",
        "",
    ]

    if missing:
        lines.extend(["**Not Running:**", ""])
        for service in missing:
            lines.append(f"- {service}")
        lines.append("")

    return lines


def _generate_dependencies_section(state: Dict[str, Any]) -> List[str]:
    """Generate dependencies section."""
    deps_data = state.get("dependencies", {})
    outdated_count = deps_data.get("outdated_count", 0)
    outdated_list = deps_data.get("outdated_packages", [])

    lines = [
        "## 📦 Dependency Updates",
        "",
        f"**Outdated Packages**: {outdated_count}",
        "",
    ]

    if outdated_list:
        lines.append("**Top Updates:**")
        lines.append("")
        for pkg in outdated_list[:5]:  # Show top 5
            lines.append(f"- {pkg}")
        if len(outdated_list) > 5:
            lines.append(f"- ... and {len(outdated_list) - 5} more")
        lines.append("")

    return lines


def _generate_sync_section(state: Dict[str, Any]) -> List[str]:
    """Generate branch sync section."""
    git_data = state.get("git", {})
    behind = git_data.get("behind_remote", 0)
    branch = git_data.get("branch", "unknown")

    return [
        "## 🔄 Branch Sync Status",
        "",
        f"**Current Branch**: {branch}",
        f"**Commits Behind Remote**: {behind}",
        "",
        "Run `git pull` to sync with remote.",
        "",
    ]


def _generate_pr_section(state: Dict[str, Any]) -> List[str]:
    """Generate PR review section."""
    github_data = state.get("github", {})
    prs = github_data.get("prs_needing_review", [])

    lines = ["## 🔍 Pull Requests Needing Review", "", f"**Count**: {len(prs)} PRs", ""]

    if prs:
        for pr in prs[:5]:  # Show top 5
            lines.append(f"- #{pr.get('number')}: {pr.get('title')}")
        if len(prs) > 5:
            lines.append(f"- ... and {len(prs) - 5} more")
        lines.append("")

    return lines


def _generate_issues_section(state: Dict[str, Any]) -> List[str]:
    """Generate issues section."""
    github_data = state.get("github", {})
    issues = github_data.get("issues_needing_triage", [])

    lines = ["## 📝 Issues Needing Triage", "", f"**Count**: {len(issues)} issues", ""]

    if issues:
        for issue in issues[:5]:  # Show top 5
            lines.append(f"- #{issue.get('number')}: {issue.get('title')}")
        if len(issues) > 5:
            lines.append(f"- ... and {len(issues) - 5} more")
        lines.append("")

    return lines


def _generate_session_branches_section(state: Dict[str, Any]) -> List[str]:
    """Generate session branches section for morning report."""
    session_branches_data = state.get("session_branches", {})
    branches_list = session_branches_data.get("branches", [])
    current_branch = session_branches_data.get("current_branch", "main")

    unmerged = [
        b for b in branches_list if b.get("id") != "main" and not b.get("merged", False)
    ]

    if not unmerged:
        return []

    now = datetime.now(timezone.utc)
    lines = [
        "## Session Branches",
        "",
        f"**Current session branch**: {current_branch}",
        f"**Unmerged branches**: {len(unmerged)}",
        "",
        "| Branch | Reason | Age | Status |",
        "|--------|--------|-----|--------|",
    ]

    for branch in unmerged:
        branch_id = branch.get("id", "unknown")
        reason = branch.get("reason", "")[:40]
        created = branch.get("created")
        age_str = "unknown"
        status = "Active"

        if created:
            try:
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                age_days = (now - created_dt).total_seconds() / 86400
                if age_days < 1:
                    age_str = f"{int(age_days * 24)}h"
                else:
                    age_str = f"{int(age_days)}d"
                if age_days > 3:
                    status = "STALE"
            except (ValueError, TypeError):
                pass  # Malformed timestamp; leave age as default

        active_marker = " (current)" if branch_id == current_branch else ""
        lines.append(
            f"| {branch_id}{active_marker} | {reason} | {age_str} | {status} |"
        )

    # Add recommendations for stale branches
    stale = [b for b in unmerged if _branch_age_days(b) > 3]
    if stale:
        lines.append("")
        lines.append("**Stale branch cleanup recommended:**")
        for b in stale:
            age = int(_branch_age_days(b))
            lines.append(f"- Merge or delete `{b.get('id')}` ({age} days old)")

    lines.append("")
    return lines


def _branch_age_days(branch: Dict[str, Any]) -> float:
    """Calculate age of a branch in days."""
    created = branch.get("created")
    if not created:
        return 0
    try:
        created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        return (now - created_dt).total_seconds() / 86400
    except (ValueError, TypeError):
        return 0


def _generate_setup_recommendations(score: int, state: Dict[str, Any]) -> List[str]:
    """Generate setup recommendations before starting work."""
    recommendations = []

    # Service recommendations
    services_data = state.get("services", {})
    required = services_data.get("required_services", [])
    running = services_data.get("running_services", [])
    missing = [s for s in required if s not in running]

    if missing:
        recommendations.append(
            f"Start {len(missing)} dev services: {', '.join(missing)}"
        )

    # Sync recommendations
    git_data = state.get("git", {})
    behind = git_data.get("behind_remote", 0)

    if behind > 0:
        recommendations.append(
            f"Sync with remote: git pull (behind by {behind} commits)"
        )

    # Dependency recommendations
    deps_data = state.get("dependencies", {})
    outdated_count = deps_data.get("outdated_count", 0)

    if outdated_count > 10:
        recommendations.append(
            f"Update {outdated_count} outdated dependencies: pnpm update"
        )
    elif outdated_count > 0:
        recommendations.append(f"Review {outdated_count} dependency updates (optional)")

    # Session branch cleanup
    session_branches_data = state.get("session_branches", {})
    branches_list = session_branches_data.get("branches", [])
    stale_branches = [
        b
        for b in branches_list
        if b.get("id") != "main"
        and not b.get("merged", False)
        and _branch_age_days(b) > 3
    ]
    if stale_branches:
        names = ", ".join(b.get("id", "?") for b in stale_branches[:3])
        recommendations.append(
            f"Clean up {len(stale_branches)} stale session branch{'es' if len(stale_branches) != 1 else ''}: {names}"
        )

    # Low score warning
    if score < 60:
        recommendations.append(
            "⚠️ Low Ready to Code Score - address critical issues first"
        )

    if not recommendations:
        recommendations.append("All set! Start coding immediately.")

    return recommendations


def _generate_today_recommendations(state: Dict[str, Any]) -> List[str]:
    """Generate today's focus recommendations."""
    recommendations = []

    # PR reviews
    github_data = state.get("github", {})
    prs = github_data.get("prs_needing_review", [])

    if prs:
        recommendations.append(f"Review {len(prs)} pending PRs")

    # Issue triage
    issues = github_data.get("issues_needing_triage", [])

    if issues:
        recommendations.append(f"Triage {len(issues)} open issues")

    # Check overnight changes
    recommendations.append("Review overnight commits and CI results")

    # Session restoration
    session_data = state.get("session", {})
    if session_data.get("restored", False):
        last_work = session_data.get("last_work_summary", "previous work")
        recommendations.append(f"Continue: {last_work}")
    else:
        recommendations.append("Check STATUS.json for yesterday's context")

    return recommendations


def _generate_ask_user_question_section(
    score: int, breakdown: Dict[str, Dict[str, Any]], state: Dict[str, Any]
) -> List[str]:
    """
    Generate AskUserQuestion instructions for Claude (The PopKit Way).

    This section tells Claude to invoke the AskUserQuestion tool with
    context-aware options based on the morning report results.

    Args:
        score: Ready to Code Score (0-100)
        breakdown: Score breakdown from calculate_ready_to_code_score()
        state: Full project state

    Returns:
        List of lines containing AskUserQuestion instructions for Claude
    """
    # Analyze state to determine appropriate options
    services_data = state.get("services", {})
    git_data = state.get("git", {})
    github_data = state.get("github", {})

    required_services = services_data.get("required_services", [])
    running_services = services_data.get("running_services", [])
    missing_services = [s for s in required_services if s not in running_services]

    behind_commits = git_data.get("behind_remote", 0)
    prs_needing_review = github_data.get("prs_needing_review", [])
    issues_needing_triage = github_data.get("issues_needing_triage", [])

    # Build context-aware AskUserQuestion options
    options = []

    # Option 1: Fix environment issues (if score < 80)
    if score < 80:
        issues_list = []
        if missing_services:
            issues_list.append(f"start {len(missing_services)} services")
        if behind_commits > 0:
            issues_list.append(f"pull {behind_commits} commits")

        if issues_list:
            options.append(
                {
                    "label": "Fix environment issues (Recommended)",
                    "description": ", ".join(issues_list).capitalize(),
                }
            )

    # Option 2: Work on highest priority issue
    if issues_needing_triage:
        first_issue = issues_needing_triage[0]
        issue_num = first_issue.get("number", "?")
        issue_title = first_issue.get("title", "Unknown")
        options.append(
            {
                "label": f"Work on #{issue_num}: {issue_title[:50]}",
                "description": "Highest priority issue needing attention",
            }
        )
    else:
        # Generic "start working" option
        session_data = state.get("session", {})
        last_work = session_data.get("last_work_summary", "previous task")
        options.append(
            {
                "label": f"Continue: {last_work}",
                "description": "Pick up where you left off yesterday",
            }
        )

    # Option 3: Review PRs (if any)
    if prs_needing_review:
        pr_count = len(prs_needing_review)
        options.append(
            {
                "label": f"Review {pr_count} open PR{'s' if pr_count > 1 else ''}",
                "description": "PRs waiting for your review",
            }
        )

    # Option 4: Triage issues (if any and score >= 80)
    if issues_needing_triage and score >= 80:
        issue_count = len(issues_needing_triage)
        options.append(
            {
                "label": f"Triage {issue_count} issue{'s' if issue_count > 1 else ''}",
                "description": "Issues needing assignment or labels",
            }
        )

    # Always include "Other" option
    options.append({"label": "Other", "description": "I have something else in mind"})

    # Generate the AskUserQuestion instruction section
    lines = [
        "**IMPORTANT - The PopKit Way**: You MUST now use the AskUserQuestion tool to keep PopKit in control of the workflow.",
        "",
        "Use AskUserQuestion with the following configuration:",
        "",
        "```json",
        "{",
        '  "questions": [',
        "    {",
        '      "question": "What would you like to do next?",',
        '      "header": "Next Action",',
        '      "multiSelect": false,',
        '      "options": [',
    ]

    # Add each option
    for i, option in enumerate(options):
        is_last = i == len(options) - 1
        lines.append("        {")
        lines.append(f'          "label": "{option["label"]}",')
        lines.append(f'          "description": "{option["description"]}"')
        lines.append("        }" + ("" if is_last else ","))

    lines.extend(
        [
            "      ]",
            "    }",
            "  ]",
            "}",
            "```",
            "",
            "**DO NOT** just end the session after showing this report. You MUST invoke AskUserQuestion to maintain The PopKit Way pattern.",
        ]
    )

    return lines
