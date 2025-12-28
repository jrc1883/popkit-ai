#!/usr/bin/env python3
"""
Nightly Workflow Orchestrator

Main entry point for pop-nightly skill.
Coordinates all nightly routine steps:
1. Collect project state
2. Calculate Sleep Score
3. Generate nightly report
4. Capture session state (STATUS.json)
5. Present report to user
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

from .sleep_score import calculate_sleep_score, get_score_interpretation
from .report_generator import generate_nightly_report, generate_quick_summary


class NightlyWorkflow:
    """Orchestrates nightly routine execution."""

    def __init__(
        self,
        quick: bool = False,
        measure: bool = False,
        optimized: bool = False,
        no_cache: bool = False
    ):
        """
        Initialize nightly workflow.

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
            self.measurement = RoutineMeasurement('nightly')

        # Initialize cache if optimized mode
        self.cache = None
        if optimized and HAS_UTILITIES:
            self.cache = RoutineCache()

        # Get recorder for session recording
        self.recorder = get_recorder() if HAS_UTILITIES else None

    def run(self) -> Dict[str, Any]:
        """
        Execute complete nightly routine workflow.

        Returns:
            dict with keys:
            - score: Sleep Score (0-100)
            - report: Formatted report string
            - state: Full project state
            - breakdown: Score breakdown
        """
        if self.recorder:
            record_reasoning(
                'workflow_start',
                'Starting nightly routine workflow',
                {'quick': self.quick, 'optimized': self.optimized}
            )

        # Step 1: Collect project state
        print("[1/4] Collecting project state...", file=sys.stderr)
        state = self._collect_state()

        # Step 2: Calculate Sleep Score
        print("[2/4] Calculating Sleep Score...", file=sys.stderr)
        score, breakdown = calculate_sleep_score(state)

        if self.recorder:
            record_reasoning(
                'score_calculated',
                f'Sleep Score: {score}/100',
                {'score': score, 'breakdown': breakdown}
            )

        # Step 3: Generate report
        print("[3/4] Generating nightly report...", file=sys.stderr)
        if self.quick:
            report = generate_quick_summary(score, breakdown, state)
        else:
            report = generate_nightly_report(score, breakdown, state)

        # Step 4: Capture session state (STATUS.json)
        print("[4/4] Capturing session state...", file=sys.stderr)
        self._capture_session_state(score, breakdown, state)

        # Record recommendations
        if self.recorder:
            interpretation = get_score_interpretation(score)
            record_recommendation(
                'nightly_complete',
                interpretation['recommendation'],
                score,
                interpretation['interpretation']
            )

        # Finalize measurement
        if self.measurement:
            self.measurement.finalize({
                'sleep_score': score,
                'uncommitted_files': state.get('git', {}).get('uncommitted_files', 0),
                'stashes': state.get('git', {}).get('stashes', 0)
            })

        return {
            'score': score,
            'report': report,
            'state': state,
            'breakdown': breakdown
        }

    def _collect_state(self) -> Dict[str, Any]:
        """
        Collect complete project state.

        Uses cache if optimized mode enabled, otherwise collects fresh.
        """
        if HAS_UTILITIES:
            # Use capture_state utility
            if self.optimized and self.cache and not self.no_cache:
                # Try cache first
                cached_state = self.cache.get('nightly_state')
                if cached_state:
                    print("[CACHE] Using cached state", file=sys.stderr)
                    return cached_state

            # Collect fresh state
            state = capture_project_state()

            # Cache for next time if optimized
            if self.optimized and self.cache:
                self.cache.set('nightly_state', state, ttl=300)  # 5 min TTL

            return state
        else:
            # Fallback: manual state collection
            return self._collect_state_fallback()

    def _collect_state_fallback(self) -> Dict[str, Any]:
        """Fallback state collection without utilities."""
        import subprocess

        def run_command(cmd: str) -> str:
            """Run shell command and return output."""
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return result.stdout.strip()
            except Exception as e:
                print(f"[WARN] Command failed: {cmd} - {e}", file=sys.stderr)
                return ""

        # Git state
        git_state = {
            'branch': run_command('git rev-parse --abbrev-ref HEAD'),
            'uncommitted_files': len(run_command('git status --porcelain').splitlines()),
            'uncommitted_files_list': [
                {'status': line[:2].strip(), 'path': line[3:]}
                for line in run_command('git status --porcelain').splitlines()
            ],
            'stashes': int(run_command('git stash list | wc -l') or '0'),
            'merged_branches': int(run_command(
                'git branch --merged main | grep -v "^\\*" | grep -v "main" | wc -l'
            ) or '0')
        }

        # GitHub state (if gh CLI available)
        github_state = {}
        if run_command('which gh'):
            try:
                issues_json = run_command(
                    'gh issue list --state open --limit 5 --json number,title,updatedAt'
                )
                github_state['issues'] = json.loads(issues_json) if issues_json else []

                ci_json = run_command(
                    'gh run list --limit 1 --json conclusion,status,createdAt'
                )
                ci_data = json.loads(ci_json) if ci_json else []
                github_state['ci_status'] = ci_data[0] if ci_data else {}
            except json.JSONDecodeError:
                github_state = {'issues': [], 'ci_status': {}}

        # Services state
        running_services = run_command(
            'ps aux | grep -E "(node|npm|pnpm|redis|postgres|supabase)" | grep -v grep'
        ).splitlines()

        services_state = {
            'running_services': running_services,
            'log_files': int(run_command('ls ~/.claude/logs/*.log 2>/dev/null | wc -l') or '0')
        }

        return {
            'git': git_state,
            'github': github_state,
            'services': services_state,
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

        # Update with nightly routine data
        git_state = state.get('git', {})
        github_state = state.get('github', {})

        updated_status = {
            **existing_status,  # Preserve existing data
            'session_id': f"nightly-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'last_nightly_routine': {
                'executed_at': datetime.now().isoformat(),
                'sleep_score': f"{score}/100",
                'breakdown': breakdown
            },
            'git_status': {
                'current_branch': git_state.get('branch', 'unknown'),
                'last_commit': git_state.get('last_commit', 'unknown'),
                'uncommitted_files': git_state.get('uncommitted_files', 0),
                'files': [
                    f"{item['path']} ({item['status']})"
                    for item in git_state.get('uncommitted_files_list', [])[:10]
                ],
                'stashes': git_state.get('stashes', 0),
                'action_required': 'Commit or stash changes' if git_state.get('uncommitted_files', 0) > 0 else None
            },
            'metrics': {
                **existing_status.get('metrics', {}),
                'sleep_score': f"{score}/100"
            }
        }

        # Add recommendations
        interpretation = get_score_interpretation(score)
        updated_status['recommendations'] = {
            **existing_status.get('recommendations', {}),
            'before_leaving': self._get_before_leaving_recommendations(score, state),
            'next_session': [
                "Run /popkit:routine morning to check overnight changes",
                "Review and address items from nightly report"
            ]
        }

        # Write updated STATUS.json
        try:
            status_file.write_text(json.dumps(updated_status, indent=2))
            print("[OK] STATUS.json updated", file=sys.stderr)
        except Exception as e:
            print(f"[ERROR] Failed to update STATUS.json: {e}", file=sys.stderr)

    def _get_before_leaving_recommendations(
        self,
        score: int,
        state: Dict[str, Any]
    ) -> list:
        """Generate before-leaving recommendations."""
        recommendations = []
        git_state = state.get('git', {})

        if git_state.get('uncommitted_files', 0) > 0:
            recommendations.append(
                f"Commit or stash {git_state['uncommitted_files']} uncommitted files"
            )

        if git_state.get('stashes', 0) > 5:
            recommendations.append(
                f"Review {git_state['stashes']} stashes - consider cleanup"
            )

        if score < 60:
            recommendations.append(
                "⚠️ Low Sleep Score - address issues before leaving"
            )

        return recommendations if recommendations else ["All clear! Safe to close."]


def main():
    """Main entry point for nightly workflow."""
    import argparse

    parser = argparse.ArgumentParser(description='PopKit Nightly Routine')
    parser.add_argument('--quick', action='store_true', help='Quick one-line summary')
    parser.add_argument('--measure', action='store_true', help='Track performance metrics')
    parser.add_argument('--optimized', action='store_true', help='Use caching')
    parser.add_argument('--no-cache', action='store_true', help='Force fresh execution')

    args = parser.parse_args()

    # Run workflow
    workflow = NightlyWorkflow(
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
