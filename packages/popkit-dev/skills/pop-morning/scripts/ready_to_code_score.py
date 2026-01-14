#!/usr/bin/env python3
"""
Ready to Code Score Calculation

Calculates a 0-100 score indicating readiness to start development work.
Based on 6 dimensions: session restored, services healthy, dependencies updated,
branches synced, PRs reviewed, and issues triaged.
"""

from typing import Dict, Any, Tuple


def calculate_ready_to_code_score(state: Dict[str, Any]) -> Tuple[int, Dict[str, Dict[str, Any]]]:
    """
    Calculate Ready to Code Score (0-100) based on morning project state.

    Args:
        state: Project state dict with keys:
            - git: Git status (branch, remotes, commits behind)
            - github: GitHub data (PRs, issues)
            - services: Dev service status (running/stopped)
            - session: Session restore data
            - dependencies: Dependency check results

    Returns:
        Tuple of (score, breakdown) where:
        - score: Integer 0-100
        - breakdown: Dict of dimension scores with reasons
    """
    score = 0
    breakdown = {}

    # 1. Session Restored (20 points)
    # Check if we successfully restored previous session context
    session_data = state.get('session', {})
    if session_data.get('restored', False):
        score += 20
        breakdown['session_restored'] = {
            'points': 20,
            'max': 20,
            'status': '✅',
            'reason': 'Previous session context restored'
        }
    else:
        score += 0
        breakdown['session_restored'] = {
            'points': 0,
            'max': 20,
            'status': '❌',
            'reason': 'No session context found or restore failed'
        }

    # 2. Services Healthy (20 points)
    # Check if required dev services are running
    services_data = state.get('services', {})
    required_services = services_data.get('required_services', [])
    running_services = services_data.get('running_services', [])

    if not required_services:
        # No required services configured - full points
        score += 20
        breakdown['services_healthy'] = {
            'points': 20,
            'max': 20,
            'status': '✅',
            'reason': 'No dev services required'
        }
    else:
        # Check if all required services are running
        missing_services = [s for s in required_services if s not in running_services]
        if not missing_services:
            score += 20
            breakdown['services_healthy'] = {
                'points': 20,
                'max': 20,
                'status': '✅',
                'reason': f'All {len(required_services)} services running'
            }
        else:
            score += 10  # Partial credit
            breakdown['services_healthy'] = {
                'points': 10,
                'max': 20,
                'status': '⚠️',
                'reason': f'Missing: {", ".join(missing_services)}'
            }

    # 3. Dependencies Updated (15 points)
    # Check if package dependencies are up to date
    dependencies_data = state.get('dependencies', {})
    outdated_count = dependencies_data.get('outdated_count', 0)

    if outdated_count == 0:
        score += 15
        breakdown['dependencies_updated'] = {
            'points': 15,
            'max': 15,
            'status': '✅',
            'reason': 'All dependencies up to date'
        }
    elif outdated_count <= 3:
        score += 10  # Minor updates available
        breakdown['dependencies_updated'] = {
            'points': 10,
            'max': 15,
            'status': '⚠️',
            'reason': f'{outdated_count} minor updates available'
        }
    else:
        score += 0
        breakdown['dependencies_updated'] = {
            'points': 0,
            'max': 15,
            'status': '❌',
            'reason': f'{outdated_count} dependencies outdated'
        }

    # 4. Branches Synced (15 points)
    # Check if local main/master is up to date with remote
    git_data = state.get('git', {})
    behind_count = git_data.get('behind_remote', 0)
    stale_branches = git_data.get('stale_branches', 0)

    # Calculate branch sync score with stale branch penalty
    branch_score = 0
    if behind_count == 0:
        branch_score = 15
        sync_status = '✅'
        sync_reason = 'Up to date with remote'
    elif behind_count <= 5:
        branch_score = 10  # Few commits behind
        sync_status = '⚠️'
        sync_reason = f'{behind_count} commits behind remote'
    else:
        branch_score = 0
        sync_status = '❌'
        sync_reason = f'{behind_count} commits behind - sync needed'

    # Apply stale branch penalty (deduct 1 point per stale branch, max 5 points)
    if stale_branches > 0:
        penalty = min(stale_branches, 5)
        branch_score = max(0, branch_score - penalty)
        sync_reason += f'; {stale_branches} stale branch{"es" if stale_branches != 1 else ""}'
        if sync_status == '✅':
            sync_status = '⚠️'

    score += branch_score
    breakdown['branches_synced'] = {
        'points': branch_score,
        'max': 15,
        'status': sync_status,
        'reason': sync_reason
    }

    # 5. PRs Reviewed (15 points)
    # Check if there are PRs waiting for review
    github_data = state.get('github', {})
    prs_needing_review = github_data.get('prs_needing_review', [])

    if len(prs_needing_review) == 0:
        score += 15
        breakdown['prs_reviewed'] = {
            'points': 15,
            'max': 15,
            'status': '✅',
            'reason': 'No PRs pending review'
        }
    elif len(prs_needing_review) <= 2:
        score += 10  # Few PRs to review
        breakdown['prs_reviewed'] = {
            'points': 10,
            'max': 15,
            'status': '⚠️',
            'reason': f'{len(prs_needing_review)} PRs need review'
        }
    else:
        score += 0
        breakdown['prs_reviewed'] = {
            'points': 0,
            'max': 15,
            'status': '❌',
            'reason': f'{len(prs_needing_review)} PRs waiting - review backlog'
        }

    # 6. Issues Triaged (15 points)
    # Check if today's issues are assigned/prioritized
    issues_needing_triage = github_data.get('issues_needing_triage', [])

    if len(issues_needing_triage) == 0:
        score += 15
        breakdown['issues_triaged'] = {
            'points': 15,
            'max': 15,
            'status': '✅',
            'reason': 'All issues triaged'
        }
    elif len(issues_needing_triage) <= 3:
        score += 10  # Few issues to triage
        breakdown['issues_triaged'] = {
            'points': 10,
            'max': 15,
            'status': '⚠️',
            'reason': f'{len(issues_needing_triage)} issues need triage'
        }
    else:
        score += 0
        breakdown['issues_triaged'] = {
            'points': 0,
            'max': 15,
            'status': '❌',
            'reason': f'{len(issues_needing_triage)} issues need attention'
        }

    return score, breakdown


def get_score_interpretation(score: int) -> Dict[str, str]:
    """
    Get human-readable interpretation of Ready to Code Score.

    Args:
        score: Ready to Code Score (0-100)

    Returns:
        Dict with 'grade', 'emoji', 'interpretation', and 'recommendation'
    """
    if score >= 90:
        return {
            'grade': 'A+',
            'emoji': '🌟',
            'interpretation': 'Excellent - Fully ready to code',
            'recommendation': 'Everything is set up perfectly. Start coding immediately!'
        }
    elif score >= 80:
        return {
            'grade': 'A',
            'emoji': '✅',
            'interpretation': 'Very Good - Almost ready',
            'recommendation': 'Minor setup needed but good to start coding.'
        }
    elif score >= 70:
        return {
            'grade': 'B',
            'emoji': '👍',
            'interpretation': 'Good - Ready with minor issues',
            'recommendation': 'Address minor issues as you code or during breaks.'
        }
    elif score >= 60:
        return {
            'grade': 'C',
            'emoji': '⚠️',
            'interpretation': 'Fair - Some setup needed',
            'recommendation': 'Spend 10-15 minutes on setup before starting.'
        }
    elif score >= 50:
        return {
            'grade': 'D',
            'emoji': '🔧',
            'interpretation': 'Poor - Significant setup required',
            'recommendation': 'Fix critical issues before coding (services, sync).'
        }
    else:
        return {
            'grade': 'F',
            'emoji': '❌',
            'interpretation': 'Not Ready - Major issues',
            'recommendation': 'Focus on environment setup before attempting to code.'
        }


def format_breakdown_table(breakdown: Dict[str, Dict[str, Any]]) -> str:
    """
    Format breakdown as markdown table.

    Args:
        breakdown: Score breakdown from calculate_ready_to_code_score()

    Returns:
        Markdown table string
    """
    lines = [
        "| Check | Points | Status |",
        "|-------|--------|--------|"
    ]

    # Define display order
    order = [
        ('session_restored', 'Session Restored'),
        ('services_healthy', 'Services Healthy'),
        ('dependencies_updated', 'Dependencies Updated'),
        ('branches_synced', 'Branches Synced'),
        ('prs_reviewed', 'PRs Reviewed'),
        ('issues_triaged', 'Issues Triaged')
    ]

    for key, display_name in order:
        if key in breakdown:
            item = breakdown[key]
            points_str = f"{item['points']}/{item['max']}"
            status = f"{item['status']} {item['reason']}"
            lines.append(f"| {display_name} | {points_str} | {status} |")

    return "\n".join(lines)
