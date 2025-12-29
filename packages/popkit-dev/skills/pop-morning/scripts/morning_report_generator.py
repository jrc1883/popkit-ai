#!/usr/bin/env python3
"""
Morning Report Generator

Generates formatted morning routine reports with Ready to Code Score,
setup recommendations, and today's action items.
"""

from typing import Dict, Any, List
from datetime import datetime

# Try relative import (when used as package), fall back to direct import
try:
    from .ready_to_code_score import format_breakdown_table, get_score_interpretation
except ImportError:
    from ready_to_code_score import format_breakdown_table, get_score_interpretation


def generate_morning_report(
    score: int,
    breakdown: Dict[str, Dict[str, Any]],
    state: Dict[str, Any]
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
        ""
    ]

    # Add service status if services are not healthy
    services_breakdown = breakdown.get('services_healthy', {})
    if services_breakdown.get('points', 0) < services_breakdown.get('max', 20):
        report_lines.extend(_generate_service_status_section(state))

    # Add dependency updates if there are outdated packages
    deps_breakdown = breakdown.get('dependencies_updated', {})
    if deps_breakdown.get('points', 0) < deps_breakdown.get('max', 15):
        report_lines.extend(_generate_dependencies_section(state))

    # Add branch sync status if behind remote
    branches_breakdown = breakdown.get('branches_synced', {})
    if branches_breakdown.get('points', 0) < branches_breakdown.get('max', 15):
        report_lines.extend(_generate_sync_section(state))

    # Add PR review queue if there are PRs
    prs_breakdown = breakdown.get('prs_reviewed', {})
    if prs_breakdown.get('points', 0) < prs_breakdown.get('max', 15):
        report_lines.extend(_generate_pr_section(state))

    # Add issue triage if there are issues
    issues_breakdown = breakdown.get('issues_triaged', {})
    if issues_breakdown.get('points', 0) < issues_breakdown.get('max', 15):
        report_lines.extend(_generate_issues_section(state))

    # Add recommendations
    report_lines.extend([
        "## 📋 Recommendations",
        "",
        "**Before Starting Work:**"
    ])
    report_lines.extend([f"- {rec}" for rec in _generate_setup_recommendations(score, state)])

    report_lines.extend([
        "",
        "**Today's Focus:**"
    ])
    report_lines.extend([f"- {rec}" for rec in _generate_today_recommendations(state)])

    # Add STATUS.json confirmation
    report_lines.extend([
        "",
        "---",
        "",
        "STATUS.json updated ✅",
        "Morning session initialized. Ready to code!"
    ])

    return "\n".join(report_lines)


def generate_quick_summary(
    score: int,
    breakdown: Dict[str, Dict[str, Any]],
    state: Dict[str, Any]
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

    if breakdown.get('services_healthy', {}).get('points', 0) < 20:
        services_data = state.get('services', {})
        required = services_data.get('required_services', [])
        running = services_data.get('running_services', [])
        missing = [s for s in required if s not in running]
        if missing:
            issues.append(f"{len(missing)} services down")

    if breakdown.get('dependencies_updated', {}).get('points', 0) < 15:
        deps_data = state.get('dependencies', {})
        outdated = deps_data.get('outdated_count', 0)
        if outdated > 0:
            issues.append(f"{outdated} outdated deps")

    if breakdown.get('branches_synced', {}).get('points', 0) < 15:
        git_data = state.get('git', {})
        behind = git_data.get('behind_remote', 0)
        if behind > 0:
            issues.append(f"{behind} commits behind")

    if breakdown.get('prs_reviewed', {}).get('points', 0) < 15:
        github_data = state.get('github', {})
        prs = len(github_data.get('prs_needing_review', []))
        if prs > 0:
            issues.append(f"{prs} PRs to review")

    issue_str = ", ".join(issues) if issues else "all clear"
    return f"Ready to Code Score: {score}/100 {interpretation['emoji']} - {issue_str}"


def _generate_service_status_section(state: Dict[str, Any]) -> List[str]:
    """Generate service status section."""
    services_data = state.get('services', {})
    required = services_data.get('required_services', [])
    running = services_data.get('running_services', [])
    missing = [s for s in required if s not in running]

    lines = [
        "## 🔧 Dev Services Status",
        "",
        f"**Required**: {len(required)} services",
        f"**Running**: {len([s for s in required if s in running])} services",
        ""
    ]

    if missing:
        lines.extend([
            "**Not Running:**",
            ""
        ])
        for service in missing:
            lines.append(f"- {service}")
        lines.append("")

    return lines


def _generate_dependencies_section(state: Dict[str, Any]) -> List[str]:
    """Generate dependencies section."""
    deps_data = state.get('dependencies', {})
    outdated_count = deps_data.get('outdated_count', 0)
    outdated_list = deps_data.get('outdated_packages', [])

    lines = [
        "## 📦 Dependency Updates",
        "",
        f"**Outdated Packages**: {outdated_count}",
        ""
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
    git_data = state.get('git', {})
    behind = git_data.get('behind_remote', 0)
    branch = git_data.get('branch', 'unknown')

    return [
        "## 🔄 Branch Sync Status",
        "",
        f"**Current Branch**: {branch}",
        f"**Commits Behind Remote**: {behind}",
        "",
        "Run `git pull` to sync with remote.",
        ""
    ]


def _generate_pr_section(state: Dict[str, Any]) -> List[str]:
    """Generate PR review section."""
    github_data = state.get('github', {})
    prs = github_data.get('prs_needing_review', [])

    lines = [
        "## 🔍 Pull Requests Needing Review",
        "",
        f"**Count**: {len(prs)} PRs",
        ""
    ]

    if prs:
        for pr in prs[:5]:  # Show top 5
            lines.append(f"- #{pr.get('number')}: {pr.get('title')}")
        if len(prs) > 5:
            lines.append(f"- ... and {len(prs) - 5} more")
        lines.append("")

    return lines


def _generate_issues_section(state: Dict[str, Any]) -> List[str]:
    """Generate issues section."""
    github_data = state.get('github', {})
    issues = github_data.get('issues_needing_triage', [])

    lines = [
        "## 📝 Issues Needing Triage",
        "",
        f"**Count**: {len(issues)} issues",
        ""
    ]

    if issues:
        for issue in issues[:5]:  # Show top 5
            lines.append(f"- #{issue.get('number')}: {issue.get('title')}")
        if len(issues) > 5:
            lines.append(f"- ... and {len(issues) - 5} more")
        lines.append("")

    return lines


def _generate_setup_recommendations(score: int, state: Dict[str, Any]) -> List[str]:
    """Generate setup recommendations before starting work."""
    recommendations = []

    # Service recommendations
    services_data = state.get('services', {})
    required = services_data.get('required_services', [])
    running = services_data.get('running_services', [])
    missing = [s for s in required if s not in running]

    if missing:
        recommendations.append(f"Start {len(missing)} dev services: {', '.join(missing)}")

    # Sync recommendations
    git_data = state.get('git', {})
    behind = git_data.get('behind_remote', 0)

    if behind > 0:
        recommendations.append(f"Sync with remote: git pull (behind by {behind} commits)")

    # Dependency recommendations
    deps_data = state.get('dependencies', {})
    outdated_count = deps_data.get('outdated_count', 0)

    if outdated_count > 10:
        recommendations.append(f"Update {outdated_count} outdated dependencies: pnpm update")
    elif outdated_count > 0:
        recommendations.append(f"Review {outdated_count} dependency updates (optional)")

    # Low score warning
    if score < 60:
        recommendations.append("⚠️ Low Ready to Code Score - address critical issues first")

    if not recommendations:
        recommendations.append("All set! Start coding immediately.")

    return recommendations


def _generate_today_recommendations(state: Dict[str, Any]) -> List[str]:
    """Generate today's focus recommendations."""
    recommendations = []

    # PR reviews
    github_data = state.get('github', {})
    prs = github_data.get('prs_needing_review', [])

    if prs:
        recommendations.append(f"Review {len(prs)} pending PRs")

    # Issue triage
    issues = github_data.get('issues_needing_triage', [])

    if issues:
        recommendations.append(f"Triage {len(issues)} open issues")

    # Check overnight changes
    recommendations.append("Review overnight commits and CI results")

    # Session restoration
    session_data = state.get('session', {})
    if session_data.get('restored', False):
        last_work = session_data.get('last_work_summary', 'previous work')
        recommendations.append(f"Continue: {last_work}")
    else:
        recommendations.append("Check STATUS.json for yesterday's context")

    return recommendations
