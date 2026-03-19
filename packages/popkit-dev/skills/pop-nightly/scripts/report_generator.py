#!/usr/bin/env python3
"""
Nightly Report Generator

Generates formatted markdown report for nightly routine with:
- Sleep Score headline
- Score breakdown table
- Uncommitted changes (if any)
- Recommendations before leaving
- Encouraging Bible verse (Issue #71)
- Next session actions
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Try relative import (when used as package), fall back to direct import
try:
    from .sleep_score import format_breakdown_table, get_score_interpretation
except ImportError:
    from sleep_score import format_breakdown_table, get_score_interpretation

# Import Bible verse utility (Issue #71)
try:
    # Add shared-py to path
    sys.path.insert(
        0, str(Path.home() / ".claude" / "popkit" / "packages" / "shared-py")
    )
    from popkit_shared.utils.bible_verses import get_nightly_verse

    HAS_BIBLE_VERSES = True
except ImportError:
    HAS_BIBLE_VERSES = False


def generate_nightly_report(
    score: int, breakdown: Dict[str, Dict[str, Any]], state: Dict[str, Any]
) -> str:
    """
    Generate comprehensive nightly routine report.

    Args:
        score: Sleep Score (0-100)
        breakdown: Score breakdown from calculate_sleep_score
        state: Full project state from capture_state

    Returns:
        Formatted markdown report string
    """
    interpretation = get_score_interpretation(score)
    git_state = state.get("git", {})
    github_state = state.get("github", {})
    services_state = state.get("services", {})

    report = []

    # Header
    report.append("# 🌙 Nightly Routine Report")
    report.append("")
    report.append(f"**Date**: {datetime.now().strftime('%Y-%m-%d')}")
    report.append(f"**Sleep Score**: {score}/100 {interpretation['emoji']}")
    report.append("")

    # Score interpretation
    report.append(
        f"**Grade**: {interpretation['grade']} - {interpretation['interpretation']}"
    )
    report.append("")

    # Score breakdown table
    report.append("## Score Breakdown")
    report.append("")
    report.append(format_breakdown_table(breakdown))
    report.append("")

    # Uncommitted changes section (if any)
    uncommitted_files = git_state.get("uncommitted_files_list", [])
    if uncommitted_files:
        report.append("## 📝 Uncommitted Changes")
        report.append("")
        report.append(f"**{len(uncommitted_files)} files need attention:**")
        report.append("")
        for file_info in uncommitted_files[:10]:  # Show max 10
            status = file_info.get("status", "?")
            path = file_info.get("path", "")
            status_label = {
                "M": "modified",
                "A": "added",
                "D": "deleted",
                "??": "untracked",
                "R": "renamed",
                "U": "unmerged",
            }.get(status, "changed")
            report.append(f"- `{path}` ({status_label})")

        if len(uncommitted_files) > 10:
            report.append(f"- ... and {len(uncommitted_files) - 10} more")
        report.append("")

    # Session branches section (if any unmerged)
    session_branches_data = state.get("session_branches", {})
    session_branches_list = session_branches_data.get("branches", [])
    unmerged_session = [
        b
        for b in session_branches_list
        if b.get("id") != "main" and not b.get("merged", False)
    ]
    if unmerged_session:
        report.extend(_generate_session_branches_section(state))

    # Stashes section (if any)
    stash_count = git_state.get("stashes", 0)
    if stash_count > 0:
        report.append("## 💾 Stashed Changes")
        report.append("")
        report.append(f"**{stash_count} stashes found**")
        report.append("")
        report.append("Consider reviewing and cleaning up old stashes:")
        report.append("```bash")
        report.append("git stash list")
        report.append("```")
        report.append("")

    # Running services (if any)
    running_services = services_state.get("running_services", [])
    if running_services:
        report.append("## 🔧 Running Services")
        report.append("")
        report.append(f"**{len(running_services)} services still running:**")
        report.append("")
        for service in running_services[:5]:  # Show max 5
            report.append(f"- {service}")
        report.append("")
        report.append("Consider stopping dev services before leaving.")
        report.append("")

    # CI status (if failed)
    ci_status = github_state.get("ci_status", {})
    if ci_status.get("conclusion") in ["failure", "skipped"]:
        report.append("## 🚨 CI Status")
        report.append("")
        conclusion = ci_status.get("conclusion", "unknown")
        status = ci_status.get("status", "unknown")
        created_at = ci_status.get("createdAt", "")

        report.append(f"**Latest CI run**: {conclusion} ({status})")
        if created_at:
            date = created_at.split("T")[0]
            report.append(f"**Created**: {date}")
        report.append("")

        if conclusion == "failure":
            report.append("⚠️ CI is failing. Consider fixing before tomorrow.")
        elif conclusion == "skipped":
            report.append("ℹ️ CI was skipped. May need manual trigger.")
        report.append("")

    # Recommendations
    report.append("## 📋 Recommendations")
    report.append("")

    recommendations_before = _generate_recommendations_before_leaving(
        score, breakdown, state
    )

    if recommendations_before:
        report.append("**Before Leaving:**")
        for rec in recommendations_before:
            report.append(f"- {rec}")
        report.append("")

    recommendations_next = _generate_recommendations_next_session(
        score, breakdown, state
    )

    if recommendations_next:
        report.append("**Next Morning:**")
        for rec in recommendations_next:
            report.append(f"- {rec}")
        report.append("")

    # Footer
    report.append("---")
    report.append("")
    report.append("STATUS.json updated ✅")
    report.append("Session state captured for tomorrow's resume.")
    report.append("")

    # Bible verse (Issue #71)
    if HAS_BIBLE_VERSES:
        verse = get_nightly_verse()
        if verse:
            report.append("## 🙏 Good Night")
            report.append("")
            report.append(verse)
            report.append("")
            report.append("Rest well! See you tomorrow.")
            report.append("")

    # Add PopKit Way ending: AskUserQuestion instructions
    report.append("## 🎯 Next Steps")
    report.append("")
    report.extend(_generate_ask_user_question_section(score, breakdown, state))

    return "\n".join(report)


def _generate_session_branches_section(state: Dict[str, Any]) -> List[str]:
    """Generate session branches section for nightly report."""
    session_branches_data = state.get("session_branches", {})
    branches_list = session_branches_data.get("branches", [])
    current_branch = session_branches_data.get("current_branch", "main")
    history = session_branches_data.get("history", [])

    unmerged = [
        b for b in branches_list if b.get("id") != "main" and not b.get("merged", False)
    ]

    if not unmerged:
        return []

    now = datetime.now(timezone.utc)

    # Determine which branches were active today
    today_str = datetime.now().strftime("%Y-%m-%d")
    active_today = set()
    for entry in history:
        at = entry.get("at", "")
        if today_str in at:
            if entry.get("to"):
                active_today.add(entry["to"])
            if entry.get("from"):
                active_today.add(entry["from"])
            if entry.get("branch"):
                active_today.add(entry["branch"])

    lines = [
        "## Session Branches",
        "",
    ]

    if active_today - {"main"}:
        lines.append(
            f"**Active during today**: {len(active_today - {'main'})} branch{'es' if len(active_today - {'main'}) != 1 else ''} used"
        )
    lines.append(
        f"**Unmerged**: {len(unmerged)} branch{'es' if len(unmerged) != 1 else ''}"
    )
    lines.append("")
    lines.append("| Branch | Reason | Age | Status |")
    lines.append("|--------|--------|-----|--------|")

    stale_branches = []
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
                    stale_branches.append((branch_id, int(age_days)))
            except (ValueError, TypeError):
                pass

        active_marker = " (current)" if branch_id == current_branch else ""
        lines.append(
            f"| {branch_id}{active_marker} | {reason} | {age_str} | {status} |"
        )

    lines.append("")

    # Recommendations
    if stale_branches:
        lines.append("**Cleanup recommended before leaving:**")
        for name, age in stale_branches:
            lines.append(f"- Merge or delete `{name}` ({age} days old)")
        lines.append("")

    # Check if currently on a non-main session branch
    if current_branch != "main":
        lines.append(
            f"**Note**: Currently on session branch `{current_branch}`. Consider merging before leaving."
        )
        lines.append("")

    return lines


def _generate_recommendations_before_leaving(
    score: int, breakdown: Dict[str, Dict[str, Any]], state: Dict[str, Any]
) -> List[str]:
    """Generate recommendations for actions before leaving."""
    recommendations = []
    git_state = state.get("git", {})

    # Uncommitted work
    if breakdown.get("uncommitted_work_saved", {}).get("points", 0) == 0:
        uncommitted_count = git_state.get("uncommitted_files", 0)
        recommendations.append(f"Commit or stash {uncommitted_count} uncommitted files")

    # Stashes
    stash_count = git_state.get("stashes", 0)
    if stash_count > 5:
        recommendations.append(
            f"Review {stash_count} stashes - consider cleaning up old ones"
        )

    # Services
    running_services = state.get("services", {}).get("running_services", [])
    if running_services:
        recommendations.append(f"Stop {len(running_services)} running dev services")

    # CI
    ci_status = state.get("github", {}).get("ci_status", {})
    if ci_status.get("conclusion") == "failure":
        recommendations.append("Investigate CI failure before leaving")

    # Session branch cleanup
    session_branches_data = state.get("session_branches", {})
    session_branches_list = session_branches_data.get("branches", [])
    unmerged_session = [
        b
        for b in session_branches_list
        if b.get("id") != "main" and not b.get("merged", False)
    ]
    current_session_branch = session_branches_data.get("current_branch", "main")

    if current_session_branch != "main":
        recommendations.append(
            f"Merge session branch `{current_session_branch}` or switch back to main"
        )

    stale_session = []
    now = datetime.now(timezone.utc)
    for b in unmerged_session:
        created = b.get("created")
        if created:
            try:
                created_dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if (now - created_dt).total_seconds() / 86400 > 3:
                    stale_session.append(b.get("id", "?"))
            except (ValueError, TypeError):
                pass
    if stale_session:
        names = ", ".join(stale_session[:3])
        recommendations.append(f"Clean up stale session branches: {names}")

    # Low score warning
    if score < 50:
        recommendations.append("⚠️ Low Sleep Score - spend a few minutes cleaning up")

    return recommendations


def _generate_recommendations_next_session(
    score: int, breakdown: Dict[str, Dict[str, Any]], state: Dict[str, Any]
) -> List[str]:
    """Generate recommendations for next morning."""
    recommendations = []

    # Always recommend morning routine
    recommendations.append("Run `/popkit:routine morning` to check overnight changes")

    # Check for pending PRs
    # (This would come from GitHub state if we capture PR data)

    # Check issues if they weren't updated today
    if breakdown.get("issues_updated", {}).get("points", 0) < 20:
        recommendations.append("Review and update open issues")

    # CI fixes
    ci_status = state.get("github", {}).get("ci_status", {})
    if ci_status.get("conclusion") in ["failure", "skipped"]:
        recommendations.append("Check CI status and fix if needed")

    # Stash cleanup
    stash_count = state.get("git", {}).get("stashes", 0)
    if stash_count > 5:
        recommendations.append("Clean up stash backlog")

    return recommendations


def generate_quick_summary(
    score: int, breakdown: Dict[str, Dict[str, Any]], state: Dict[str, Any]
) -> str:
    """
    Generate one-line quick summary for --quick flag.

    Args:
        score: Sleep Score (0-100)
        breakdown: Score breakdown
        state: Project state

    Returns:
        One-line summary string
    """
    interpretation = get_score_interpretation(score)
    git_state = state.get("git", {})

    issues = []

    # Collect issues
    uncommitted = git_state.get("uncommitted_files", 0)
    if uncommitted > 0:
        issues.append(f"{uncommitted} uncommitted")

    stashes = git_state.get("stashes", 0)
    if stashes > 5:
        issues.append(f"{stashes} stashes")

    ci_conclusion = state.get("github", {}).get("ci_status", {}).get("conclusion")
    if ci_conclusion == "failure":
        issues.append("CI failed")
    elif ci_conclusion == "skipped":
        issues.append("CI skipped")

    running_services = state.get("services", {}).get("running_services", [])
    if running_services:
        issues.append(f"{len(running_services)} services running")

    # Format summary
    if issues:
        issue_str = ", ".join(issues)
        return f"Sleep Score: {score}/100 {interpretation['emoji']} - {issue_str}"
    else:
        return f"Sleep Score: {score}/100 {interpretation['emoji']} - All clear!"


def _generate_ask_user_question_section(
    score: int, breakdown: Dict[str, Dict[str, Any]], state: Dict[str, Any]
) -> List[str]:
    """
    Generate AskUserQuestion instructions for Claude (The PopKit Way).

    This section tells Claude to invoke the AskUserQuestion tool with
    context-aware options based on the nightly report results.

    Args:
        score: Sleep Score (0-100)
        breakdown: Score breakdown from calculate_sleep_score()
        state: Full project state

    Returns:
        List of lines containing AskUserQuestion instructions for Claude
    """
    # Analyze state to determine appropriate options
    git_state = state.get("git", {})
    github_state = state.get("github", {})
    services_state = state.get("services", {})

    uncommitted_files = git_state.get("uncommitted_files", 0)
    running_services = services_state.get("running_services", [])
    ci_status = github_state.get("ci_status", {})
    ci_conclusion = ci_status.get("conclusion", "")

    # Build context-aware AskUserQuestion options
    options = []

    # Option 1: Commit and push (if uncommitted work)
    if uncommitted_files > 0:
        options.append(
            {
                "label": "Commit and push all changes (Recommended)",
                "description": f"Save {uncommitted_files} uncommitted file{'s' if uncommitted_files > 1 else ''}",
            }
        )

        # Alternative: Stash
        options.append(
            {
                "label": "Stash changes for tomorrow",
                "description": "Keep work-in-progress safe without committing",
            }
        )

    # Option 2: Stop services (if running)
    if running_services:
        services_list = ", ".join(running_services[:3])
        if len(running_services) > 3:
            services_list += f", +{len(running_services) - 3} more"

        options.append(
            {
                "label": "Stop all dev services (Recommended)",
                "description": f"Stop {len(running_services)} running service{'s' if len(running_services) > 1 else ''}: {services_list}",
            }
        )

    # Option 3: CI failure action
    if ci_conclusion == "failure":
        options.append(
            {
                "label": "Investigate CI failure",
                "description": "Check why the latest CI run failed",
            }
        )

    # Option 4: Clean shutdown (if score >= 70)
    if score >= 70:
        options.append(
            {
                "label": "End session (all clean)",
                "description": "Everything looks good, ready for tomorrow",
            }
        )
    else:
        # Low score - review recommendations
        options.append(
            {
                "label": "Review recommendations",
                "description": "Check what needs attention before leaving",
            }
        )

    # Always include "Other" option
    options.append({"label": "Other", "description": "I have something else in mind"})

    # Limit to 4 options (AskUserQuestion constraint)
    options = options[:4]

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
        '      "question": "What would you like to do before ending the day?",',
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


if __name__ == "__main__":
    # Test with sample data
    # Import directly (not relative) for standalone execution
    from sleep_score import calculate_sleep_score

    sample_state = {
        "git": {
            "uncommitted_files": 3,
            "uncommitted_files_list": [
                {
                    "status": "D",
                    "path": "apps/popkit/packages/websitebuild-popkit-test-beta.txt",
                },
                {"status": "M", "path": "pnpm-lock.yaml"},
                {"status": "??", "path": ".npmrc"},
            ],
            "merged_branches": 0,
            "stashes": 8,
        },
        "github": {
            "issues": [
                {
                    "number": 629,
                    "title": "Feature A",
                    "updatedAt": "2025-12-28T10:00:00Z",
                },
            ],
            "ci_status": {
                "conclusion": "skipped",
                "status": "completed",
                "createdAt": "2025-12-28T15:00:00Z",
            },
        },
        "services": {"running_services": [], "log_files": 0},
        "timestamp": "2025-12-28T15:30:00Z",
    }

    score, breakdown = calculate_sleep_score(sample_state)
    report = generate_nightly_report(score, breakdown, sample_state)

    print(report)
    print("\n" + "=" * 60 + "\n")
    print("QUICK SUMMARY:")
    print(generate_quick_summary(score, breakdown, sample_state))
