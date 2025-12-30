#!/usr/bin/env python3
"""
Morning Workflow Orchestrator

Main entry point for pop-morning skill.
Coordinates all morning routine steps:
1. Restore previous session
2. Check dev environment (services, dependencies, sync)
3. Calculate Ready to Code Score
4. Generate morning report
5. Capture session state (STATUS.json)
6. Present report to user
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add shared-py to path for utilities
sys.path.insert(0, str(Path.home() / '.claude' / 'popkit' / 'packages' / 'shared-py'))

try:
    from popkit_shared.utils.capture_state import capture_project_state
    from popkit_shared.utils.routine_measurement import RoutineMeasurement
    from popkit_shared.utils.routine_cache import RoutineCache
    from popkit_shared.utils.session_recorder import (
        get_recorder,
        record_reasoning,
        record_recommendation
    )
    HAS_UTILITIES = True
except ImportError:
    HAS_UTILITIES = False
    print("[WARN] PopKit utilities not available - running in degraded mode", file=sys.stderr)

# Try relative import (when used as package), fall back to direct import
try:
    from .ready_to_code_score import calculate_ready_to_code_score, get_score_interpretation
    from .morning_report_generator import generate_morning_report, generate_quick_summary
except ImportError:
    from ready_to_code_score import calculate_ready_to_code_score, get_score_interpretation
    from morning_report_generator import generate_morning_report, generate_quick_summary


class MorningWorkflow:
    """Orchestrates morning routine execution."""

    def __init__(
        self,
        quick: bool = False,
        measure: bool = False,
        optimized: bool = False,
        no_cache: bool = False
    ):
        """
        Initialize morning workflow.

        Args:
            quick: Generate one-line summary instead of full report
            measure: Track performance metrics
            optimized: Use caching for efficiency
            no_cache: Force fresh execution (ignore cache)
        """
        self.quick = quick
        self.measure = measure
        self.optimized = optimized
        self.no_cache = no_cache

        # Initialize measurement if requested
        self.measurement = None
        if measure and HAS_UTILITIES:
            self.measurement = RoutineMeasurement('morning')

        # Initialize cache if optimized mode
        self.cache = None
        if optimized and HAS_UTILITIES:
            self.cache = RoutineCache()

        # Get recorder for session recording
        self.recorder = get_recorder() if HAS_UTILITIES else None

    def run(self) -> Dict[str, Any]:
        """
        Execute complete morning routine workflow.

        Returns:
            dict with keys:
            - score: Ready to Code Score (0-100)
            - report: Formatted report string
            - state: Full project state
            - breakdown: Score breakdown
        """
        if self.recorder:
            record_reasoning(
                'workflow_start',
                'Starting morning routine workflow',
                {'quick': self.quick, 'optimized': self.optimized}
            )

        # Step 1: Restore previous session
        print("[1/5] Restoring previous session...", file=sys.stderr)
        session_data = self._restore_session()

        # Step 2: Collect current project state
        print("[2/5] Checking dev environment...", file=sys.stderr)
        state = self._collect_state()

        # Add session data to state
        state['session'] = session_data

        # Step 3: Calculate Ready to Code Score
        print("[3/5] Calculating Ready to Code Score...", file=sys.stderr)
        score, breakdown = calculate_ready_to_code_score(state)

        if self.recorder:
            record_reasoning(
                'score_calculated',
                f'Ready to Code Score: {score}/100',
                {'score': score, 'breakdown': breakdown}
            )

        # Step 4: Generate report
        print("[4/5] Generating morning report...", file=sys.stderr)
        if self.quick:
            report = generate_quick_summary(score, breakdown, state)
        else:
            report = generate_morning_report(score, breakdown, state)

        # Step 5: Capture session state (STATUS.json)
        print("[5/5] Capturing session state...", file=sys.stderr)
        self._capture_session_state(score, breakdown, state)

        # Record recommendations
        if self.recorder:
            interpretation = get_score_interpretation(score)
            record_recommendation(
                'morning_complete',
                interpretation['recommendation'],
                score,
                interpretation['interpretation']
            )

        # Finalize measurement
        if self.measurement:
            self.measurement.finalize({
                'ready_to_code_score': score,
                'services_running': len(state.get('services', {}).get('running_services', [])),
                'commits_behind': state.get('git', {}).get('behind_remote', 0)
            })

        return {
            'score': score,
            'report': report,
            'state': state,
            'breakdown': breakdown
        }

    def _restore_session(self) -> Dict[str, Any]:
        """
        Restore previous session from STATUS.json.

        Returns:
            Dict with session data including 'restored' flag
        """
        status_file = Path('STATUS.json')
        session_data = {'restored': False}

        if status_file.exists():
            try:
                status = json.loads(status_file.read_text())

                # Extract last session info
                last_nightly = status.get('last_nightly_routine', {})
                git_status = status.get('git_status', {})

                session_data = {
                    'restored': True,
                    'last_nightly_score': last_nightly.get('sleep_score', 'unknown'),
                    'last_nightly_time': last_nightly.get('executed_at', 'unknown'),
                    'last_work_summary': git_status.get('action_required') or 'Check git status',
                    'previous_branch': git_status.get('current_branch', 'unknown'),
                    'stashed_count': git_status.get('stashes', 0)
                }

                print(f"[OK] Session restored from {status.get('timestamp', 'unknown')}", file=sys.stderr)

            except (json.JSONDecodeError, Exception) as e:
                print(f"[WARN] Could not restore session: {e}", file=sys.stderr)
                session_data = {'restored': False}
        else:
            print("[WARN] No STATUS.json found - cannot restore session", file=sys.stderr)

        return session_data

    def _collect_state(self) -> Dict[str, Any]:
        """
        Collect complete project state including:
        - Git status (branch, sync, commits behind)
        - GitHub data (PRs, issues)
        - Services (running/stopped)
        - Dependencies (outdated packages)

        Uses cache if optimized mode enabled, otherwise collects fresh.
        """
        if HAS_UTILITIES:
            # Use capture_state utility
            if self.optimized and self.cache and not self.no_cache:
                # Try cache first
                cached_state = self.cache.get('morning_state')
                if cached_state:
                    print("[CACHE] Using cached state", file=sys.stderr)
                    return cached_state

            # Collect fresh state
            state = capture_project_state()

            # Add morning-specific checks
            state = self._add_morning_checks(state)

            # Cache for next time if optimized
            if self.optimized and self.cache:
                self.cache.set('morning_state', state, ttl=300)  # 5 min TTL

            return state
        else:
            # Fallback: manual state collection
            return self._collect_state_fallback()

    def _add_morning_checks(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Add morning-specific checks to state."""
        import subprocess
        import shlex

        def run_command(cmd: str, use_shell: bool = False) -> str:
            """
            Run command and return output.

            Args:
                cmd: Command string
                use_shell: True if command needs shell features (pipes, redirection)
            """
            try:
                if use_shell:
                    # Only use shell=True when needed for pipes/redirection
                    result = subprocess.run(
                        cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                else:
                    # Safe list-based execution
                    result = subprocess.run(
                        shlex.split(cmd),
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                return result.stdout.strip()
            except Exception:
                return ""

        # Check how many commits behind remote
        git_data = state.get('git', {})
        branch = git_data.get('branch', 'main')

        # Fetch to get latest remote info (silent)
        run_command('git fetch --quiet')

        # Check commits behind
        behind_output = run_command(f'git rev-list --count HEAD..origin/{branch}')
        try:
            git_data['behind_remote'] = int(behind_output) if behind_output else 0
        except ValueError:
            git_data['behind_remote'] = 0

        # Check for outdated dependencies
        # This is a placeholder - would need actual implementation based on package manager
        deps_data = {
            'outdated_count': 0,
            'outdated_packages': []
        }

        # Try pnpm outdated (if available)
        # Uses shell redirection, so needs shell=True
        pnpm_outdated = run_command('pnpm outdated --json 2>/dev/null', use_shell=True)
        if pnpm_outdated:
            try:
                outdated = json.loads(pnpm_outdated)
                deps_data['outdated_count'] = len(outdated)
                deps_data['outdated_packages'] = [
                    f"{name}: {info.get('current')} → {info.get('latest')}"
                    for name, info in list(outdated.items())[:10]
                ]
            except json.JSONDecodeError:
                pass

        state['dependencies'] = deps_data

        # Check PRs needing review
        github_data = state.get('github', {})
        try:
            prs_json = run_command('gh pr list --state open --json number,title,updatedAt,reviewDecision')
            if prs_json:
                prs = json.loads(prs_json)
                # PRs with no review decision or requested changes
                github_data['prs_needing_review'] = [
                    pr for pr in prs
                    if pr.get('reviewDecision') in [None, 'REVIEW_REQUIRED', 'CHANGES_REQUESTED']
                ]
            else:
                github_data['prs_needing_review'] = []
        except (json.JSONDecodeError, Exception):
            github_data['prs_needing_review'] = []

        # Check issues needing triage (no assignee or no labels)
        try:
            issues_json = run_command('gh issue list --state open --json number,title,assignees,labels')
            if issues_json:
                issues = json.loads(issues_json)
                github_data['issues_needing_triage'] = [
                    issue for issue in issues
                    if not issue.get('assignees') or not issue.get('labels')
                ]
            else:
                github_data['issues_needing_triage'] = []
        except (json.JSONDecodeError, Exception):
            github_data['issues_needing_triage'] = []

        state['github'] = github_data

        return state

    def _collect_state_fallback(self) -> Dict[str, Any]:
        """Fallback state collection without utilities."""
        import subprocess
        import shlex

        def run_command(cmd: str, use_shell: bool = False) -> str:
            """
            Run command and return output.

            Args:
                cmd: Command string
                use_shell: True if command needs shell features (pipes, redirection)
            """
            try:
                if use_shell:
                    # Only use shell=True when needed for pipes/redirection
                    result = subprocess.run(
                        cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                else:
                    # Safe list-based execution
                    result = subprocess.run(
                        shlex.split(cmd),
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                return result.stdout.strip()
            except Exception as e:
                print(f"[WARN] Command failed: {cmd} - {e}", file=sys.stderr)
                return ""

        # Git state
        run_command('git fetch --quiet')  # Fetch to get latest remote info

        branch = run_command('git rev-parse --abbrev-ref HEAD')
        behind_output = run_command(f'git rev-list --count HEAD..origin/{branch}')

        try:
            behind_count = int(behind_output) if behind_output else 0
        except ValueError:
            behind_count = 0

        git_state = {
            'branch': branch,
            'behind_remote': behind_count,
            'uncommitted_files': len(run_command('git status --porcelain').splitlines()),
            # Pipe requires shell=True
            'stashes': int(run_command('git stash list | wc -l', use_shell=True) or '0')
        }

        # GitHub state (if gh CLI available)
        github_state = {
            'prs_needing_review': [],
            'issues_needing_triage': []
        }

        if run_command('which gh'):
            try:
                prs_json = run_command('gh pr list --state open --json number,title,reviewDecision')
                if prs_json:
                    prs = json.loads(prs_json)
                    github_state['prs_needing_review'] = [
                        pr for pr in prs
                        if pr.get('reviewDecision') in [None, 'REVIEW_REQUIRED']
                    ]

                issues_json = run_command('gh issue list --state open --json number,title,assignees')
                if issues_json:
                    issues = json.loads(issues_json)
                    github_state['issues_needing_triage'] = [
                        issue for issue in issues
                        if not issue.get('assignees')
                    ]
            except json.JSONDecodeError:
                pass

        # Services state
        # Pipes require shell=True
        running_services_output = run_command(
            'ps aux | grep -E "(node|npm|pnpm|redis|postgres|supabase)" | grep -v grep',
            use_shell=True
        )
        running_services = [
            line.split()[-1] for line in running_services_output.splitlines()
        ] if running_services_output else []

        services_state = {
            'running_services': running_services,
            'required_services': []  # Would be configured per project
        }

        # Dependencies state (placeholder)
        dependencies_state = {
            'outdated_count': 0,
            'outdated_packages': []
        }

        return {
            'git': git_state,
            'github': github_state,
            'services': services_state,
            'dependencies': dependencies_state,
            'timestamp': datetime.now().isoformat()
        }

    def _capture_session_state(
        self,
        score: int,
        breakdown: Dict[str, Dict[str, Any]],
        state: Dict[str, Any]
    ) -> None:
        """
        Capture session state to STATUS.json.

        This manually updates STATUS.json since we can't invoke
        the pop-session-capture skill from within Python.
        """
        status_file = Path('STATUS.json')

        # Load existing STATUS.json if it exists
        existing_status = {}
        if status_file.exists():
            try:
                existing_status = json.loads(status_file.read_text())
            except json.JSONDecodeError:
                print("[WARN] Could not parse existing STATUS.json", file=sys.stderr)

        # Update with morning routine data
        git_state = state.get('git', {})
        github_state = state.get('github', {})
        session_data = state.get('session', {})

        updated_status = {
            **existing_status,  # Preserve existing data
            'session_id': f"morning-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'last_morning_routine': {
                'executed_at': datetime.now().isoformat(),
                'ready_to_code_score': f"{score}/100",
                'breakdown': breakdown,
                'session_restored': session_data.get('restored', False)
            },
            'git_status': {
                'current_branch': git_state.get('branch', 'unknown'),
                'commits_behind_remote': git_state.get('behind_remote', 0),
                'uncommitted_files': git_state.get('uncommitted_files', 0),
                'stashes': git_state.get('stashes', 0)
            },
            'metrics': {
                **existing_status.get('metrics', {}),
                'ready_to_code_score': f"{score}/100"
            }
        }

        # Add recommendations
        interpretation = get_score_interpretation(score)
        updated_status['recommendations'] = {
            **existing_status.get('recommendations', {}),
            'before_coding': self._get_setup_recommendations(score, state),
            'todays_focus': self._get_today_recommendations(state)
        }

        # Write updated STATUS.json
        try:
            status_file.write_text(json.dumps(updated_status, indent=2))
            print("[OK] STATUS.json updated", file=sys.stderr)
        except Exception as e:
            print(f"[ERROR] Failed to update STATUS.json: {e}", file=sys.stderr)

    def _get_setup_recommendations(self, score: int, state: Dict[str, Any]) -> list:
        """Generate setup recommendations before coding."""
        recommendations = []

        services_data = state.get('services', {})
        required = services_data.get('required_services', [])
        running = services_data.get('running_services', [])
        missing = [s for s in required if s not in running]

        if missing:
            recommendations.append(f"Start dev services: {', '.join(missing)}")

        git_data = state.get('git', {})
        if git_data.get('behind_remote', 0) > 0:
            recommendations.append(f"Sync with remote: git pull ({git_data['behind_remote']} commits behind)")

        if score < 60:
            recommendations.append("⚠️ Low Ready to Code Score - address setup issues first")

        return recommendations if recommendations else ["All set! Ready to code."]

    def _get_today_recommendations(self, state: Dict[str, Any]) -> list:
        """Generate today's focus recommendations."""
        recommendations = []

        github_data = state.get('github', {})
        prs = len(github_data.get('prs_needing_review', []))
        if prs > 0:
            recommendations.append(f"Review {prs} pending PRs")

        issues = len(github_data.get('issues_needing_triage', []))
        if issues > 0:
            recommendations.append(f"Triage {issues} open issues")

        recommendations.append("Check overnight commits and CI results")

        return recommendations


def main():
    """Main entry point for morning workflow."""
    import argparse

    parser = argparse.ArgumentParser(description='PopKit Morning Routine')
    parser.add_argument('--quick', action='store_true', help='Quick one-line summary')
    parser.add_argument('--measure', action='store_true', help='Track performance metrics')
    parser.add_argument('--optimized', action='store_true', help='Use caching')
    parser.add_argument('--no-cache', action='store_true', help='Force fresh execution')

    args = parser.parse_args()

    # Run workflow
    workflow = MorningWorkflow(
        quick=args.quick,
        measure=args.measure,
        optimized=args.optimized,
        no_cache=args.no_cache
    )

    result = workflow.run()

    # Print report
    print(result['report'])

    # Exit with score as status (0-100)
    sys.exit(0 if result['score'] >= 70 else 1)


if __name__ == '__main__':
    main()
