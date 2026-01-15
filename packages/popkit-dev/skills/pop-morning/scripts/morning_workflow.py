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
from typing import Dict, Any

# Add shared-py to path for utilities
sys.path.insert(0, str(Path.home() / ".claude" / "popkit" / "packages" / "shared-py"))

try:
    from popkit_shared.utils.capture_state import capture_project_state
    from popkit_shared.utils.routine_measurement import RoutineMeasurement
    from popkit_shared.utils.routine_cache import RoutineCache
    from popkit_shared.utils.session_recorder import (
        get_recorder,
        record_reasoning,
        record_recommendation,
    )
    from popkit_shared.utils.flag_profiles import ProfileManager

    HAS_UTILITIES = True
except ImportError:
    HAS_UTILITIES = False
    ProfileManager = None
    print(
        "[WARN] PopKit utilities not available - running in degraded mode",
        file=sys.stderr,
    )

# Try relative import (when used as package), fall back to direct import
try:
    from .ready_to_code_score import (
        calculate_ready_to_code_score,
        get_score_interpretation,
    )
    from .morning_report_generator import (
        generate_morning_report,
        generate_quick_summary,
    )
except ImportError:
    from ready_to_code_score import (
        calculate_ready_to_code_score,
        get_score_interpretation,
    )
    from morning_report_generator import generate_morning_report, generate_quick_summary


class MorningWorkflow:
    """Orchestrates morning routine execution."""

    def __init__(
        self,
        quick: bool = False,
        measure: bool = False,
        optimized: bool = False,
        no_cache: bool = False,
        # New flags for profile system (Issue #105)
        simple: bool = False,
        skip_tests: bool = False,
        skip_services: bool = False,
        skip_deployments: bool = False,
        full: bool = False,
        no_nightly: bool = False,
    ):
        """
        Initialize morning workflow.

        Args:
            quick: Generate one-line summary instead of full report
            measure: Track performance metrics
            optimized: Use caching for efficiency
            no_cache: Force fresh execution (ignore cache)
            simple: Use markdown tables instead of ASCII dashboard
            skip_tests: Skip test execution
            skip_services: Skip service health checks
            skip_deployments: Skip deployment status check
            full: Include all checks (slower)
            no_nightly: Skip "From Last Night" section
        """
        self.quick = quick
        self.measure = measure
        self.optimized = optimized
        self.no_cache = no_cache
        self.simple = simple
        self.skip_tests = skip_tests
        self.skip_services = skip_services
        self.skip_deployments = skip_deployments
        self.full = full
        self.no_nightly = no_nightly

        # Initialize measurement if requested
        self.measurement = None
        if measure and HAS_UTILITIES:
            self.measurement = RoutineMeasurement("morning")

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
                "workflow_start",
                "Starting morning routine workflow",
                {"quick": self.quick, "optimized": self.optimized},
            )

        # Step 1: Restore previous session
        print("[1/5] Restoring previous session...", file=sys.stderr)
        session_data = self._restore_session()

        # Step 2: Collect current project state
        print("[2/5] Checking dev environment...", file=sys.stderr)
        state = self._collect_state()

        # Add session data to state
        state["session"] = session_data

        # Step 3: Calculate Ready to Code Score
        print("[3/5] Calculating Ready to Code Score...", file=sys.stderr)
        score, breakdown = calculate_ready_to_code_score(state)

        if self.recorder:
            record_reasoning(
                "score_calculated",
                f"Ready to Code Score: {score}/100",
                {"score": score, "breakdown": breakdown},
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
                "morning_complete",
                interpretation["recommendation"],
                score,
                interpretation["interpretation"],
            )

        # Finalize measurement
        if self.measurement:
            self.measurement.finalize(
                {
                    "ready_to_code_score": score,
                    "services_running": len(
                        state.get("services", {}).get("running_services", [])
                    ),
                    "commits_behind": state.get("git", {}).get("behind_remote", 0),
                }
            )

        return {
            "score": score,
            "report": report,
            "state": state,
            "breakdown": breakdown,
        }

    def _restore_session(self) -> Dict[str, Any]:
        """
        Restore previous session from STATUS.json.

        Returns:
            Dict with session data including 'restored' flag
        """
        status_file = Path("STATUS.json")
        session_data = {"restored": False}

        if status_file.exists():
            try:
                status = json.loads(status_file.read_text())

                # Extract last session info
                last_nightly = status.get("last_nightly_routine", {})
                git_status = status.get("git_status", {})

                session_data = {
                    "restored": True,
                    "last_nightly_score": last_nightly.get("sleep_score", "unknown"),
                    "last_nightly_time": last_nightly.get("executed_at", "unknown"),
                    "last_work_summary": git_status.get("action_required")
                    or "Check git status",
                    "previous_branch": git_status.get("current_branch", "unknown"),
                    "stashed_count": git_status.get("stashes", 0),
                }

                print(
                    f"[OK] Session restored from {status.get('timestamp', 'unknown')}",
                    file=sys.stderr,
                )

            except (json.JSONDecodeError, Exception) as e:
                print(f"[WARN] Could not restore session: {e}", file=sys.stderr)
                session_data = {"restored": False}
        else:
            print(
                "[WARN] No STATUS.json found - cannot restore session", file=sys.stderr
            )

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
                cached_state = self.cache.get("morning_state")
                if cached_state:
                    print("[CACHE] Using cached state", file=sys.stderr)
                    return cached_state

            # Collect fresh state
            state = capture_project_state()

            # Add morning-specific checks
            state = self._add_morning_checks(state)

            # Cache for next time if optimized
            if self.optimized and self.cache:
                self.cache.set("morning_state", state, ttl=300)  # 5 min TTL

            return state
        else:
            # Fallback: manual state collection
            return self._collect_state_fallback()

    def _add_morning_checks(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Add morning-specific checks to state."""
        import subprocess

        # Import git_utils from popkit-dev hooks
        hooks_path = Path(__file__).parents[3] / "popkit-dev" / "hooks"
        sys.path.insert(0, str(hooks_path))
        from git_utils import git_fetch_prune, count_stale_branches

        def run_command(cmd: list, stderr_redirect: bool = False) -> str:
            """
            Run command and return output.

            Args:
                cmd: Command as list of arguments
                stderr_redirect: If True, redirects stderr to stdout
            """
            try:
                if stderr_redirect:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=10,
                        stderr=subprocess.DEVNULL,
                    )
                else:
                    result = subprocess.run(
                        cmd, capture_output=True, text=True, timeout=10
                    )
                return result.stdout.strip()
            except Exception:
                return ""

        # Check how many commits behind remote
        git_data = state.get("git", {})
        branch = git_data.get("branch", "main")

        # Run git fetch --prune to clean up stale remote tracking branches
        prune_success, prune_message = git_fetch_prune()
        if prune_success:
            print(f"[OK] {prune_message}", file=sys.stderr)
        else:
            print(f"[WARN] {prune_message}", file=sys.stderr)

        # Check commits behind - SECURE: branch is passed as a separate argument
        behind_output = run_command(
            ["git", "rev-list", "--count", f"HEAD..origin/{branch}"]
        )
        try:
            git_data["behind_remote"] = int(behind_output) if behind_output else 0
        except ValueError:
            git_data["behind_remote"] = 0

        # Count stale local branches (whose remote tracking branches were deleted)
        git_data["stale_branches"] = count_stale_branches()

        # Check for outdated dependencies
        # This is a placeholder - would need actual implementation based on package manager
        deps_data = {"outdated_count": 0, "outdated_packages": []}

        # Try pnpm outdated (if available)
        # SECURE: stderr redirect handled via subprocess parameter
        pnpm_outdated = run_command(
            ["pnpm", "outdated", "--json"], stderr_redirect=True
        )
        if pnpm_outdated:
            try:
                outdated = json.loads(pnpm_outdated)
                deps_data["outdated_count"] = len(outdated)
                deps_data["outdated_packages"] = [
                    f"{name}: {info.get('current')} → {info.get('latest')}"
                    for name, info in list(outdated.items())[:10]
                ]
            except json.JSONDecodeError:
                pass

        state["dependencies"] = deps_data

        # Check PRs needing review
        github_data = state.get("github", {})
        try:
            prs_json = run_command(
                [
                    "gh",
                    "pr",
                    "list",
                    "--state",
                    "open",
                    "--json",
                    "number,title,updatedAt,reviewDecision",
                ]
            )
            if prs_json:
                prs = json.loads(prs_json)
                # PRs with no review decision or requested changes
                github_data["prs_needing_review"] = [
                    pr
                    for pr in prs
                    if pr.get("reviewDecision")
                    in [None, "REVIEW_REQUIRED", "CHANGES_REQUESTED"]
                ]
            else:
                github_data["prs_needing_review"] = []
        except (json.JSONDecodeError, Exception):
            github_data["prs_needing_review"] = []

        # Check issues needing triage (no assignee or no labels)
        try:
            issues_json = run_command(
                [
                    "gh",
                    "issue",
                    "list",
                    "--state",
                    "open",
                    "--json",
                    "number,title,assignees,labels",
                ]
            )
            if issues_json:
                issues = json.loads(issues_json)
                github_data["issues_needing_triage"] = [
                    issue
                    for issue in issues
                    if not issue.get("assignees") or not issue.get("labels")
                ]
            else:
                github_data["issues_needing_triage"] = []
        except (json.JSONDecodeError, Exception):
            github_data["issues_needing_triage"] = []

        state["github"] = github_data

        return state

    def _collect_state_fallback(self) -> Dict[str, Any]:
        """Fallback state collection without utilities."""
        import subprocess
        import shutil

        def run_command(cmd: list) -> str:
            """
            Run command and return output.

            Args:
                cmd: Command as list of arguments
            """
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                return result.stdout.strip()
            except Exception as e:
                print(f"[WARN] Command failed: {' '.join(cmd)} - {e}", file=sys.stderr)
                return ""

        # Git state
        run_command(["git", "fetch", "--quiet"])  # Fetch to get latest remote info

        branch = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
        # SECURE: branch is passed as separate argument, safe from injection
        behind_output = run_command(
            ["git", "rev-list", "--count", f"HEAD..origin/{branch}"]
        )

        try:
            behind_count = int(behind_output) if behind_output else 0
        except ValueError:
            behind_count = 0

        # Count stashes without pipes - SECURE
        stash_list = run_command(["git", "stash", "list"])
        stash_count = len(stash_list.splitlines()) if stash_list else 0

        git_state = {
            "branch": branch,
            "behind_remote": behind_count,
            "uncommitted_files": len(
                run_command(["git", "status", "--porcelain"]).splitlines()
            ),
            "stashes": stash_count,
        }

        # GitHub state (if gh CLI available)
        github_state = {"prs_needing_review": [], "issues_needing_triage": []}

        if shutil.which("gh"):
            try:
                prs_json = run_command(
                    [
                        "gh",
                        "pr",
                        "list",
                        "--state",
                        "open",
                        "--json",
                        "number,title,reviewDecision",
                    ]
                )
                if prs_json:
                    prs = json.loads(prs_json)
                    github_state["prs_needing_review"] = [
                        pr
                        for pr in prs
                        if pr.get("reviewDecision") in [None, "REVIEW_REQUIRED"]
                    ]

                issues_json = run_command(
                    [
                        "gh",
                        "issue",
                        "list",
                        "--state",
                        "open",
                        "--json",
                        "number,title,assignees",
                    ]
                )
                if issues_json:
                    issues = json.loads(issues_json)
                    github_state["issues_needing_triage"] = [
                        issue for issue in issues if not issue.get("assignees")
                    ]
            except json.JSONDecodeError:
                pass

        # Services state - SECURE: Use ps with specific arguments (no pipes)
        # Get list of running processes that match our patterns
        running_services = []
        for service_name in [
            "node",
            "npm",
            "pnpm",
            "redis-server",
            "postgres",
            "supabase",
        ]:
            try:
                result = subprocess.run(
                    ["pgrep", "-f", service_name],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if result.returncode == 0 and result.stdout.strip():
                    running_services.append(service_name)
            except Exception:
                pass

        services_state = {
            "running_services": running_services,
            "required_services": [],  # Would be configured per project
        }

        # Dependencies state (placeholder)
        dependencies_state = {"outdated_count": 0, "outdated_packages": []}

        return {
            "git": git_state,
            "github": github_state,
            "services": services_state,
            "dependencies": dependencies_state,
            "timestamp": datetime.now().isoformat(),
        }

    def _capture_session_state(
        self, score: int, breakdown: Dict[str, Dict[str, Any]], state: Dict[str, Any]
    ) -> None:
        """
        Capture session state to STATUS.json.

        This manually updates STATUS.json since we can't invoke
        the pop-session-capture skill from within Python.
        """
        status_file = Path("STATUS.json")

        # Load existing STATUS.json if it exists
        existing_status = {}
        if status_file.exists():
            try:
                existing_status = json.loads(status_file.read_text())
            except json.JSONDecodeError:
                print("[WARN] Could not parse existing STATUS.json", file=sys.stderr)

        # Update with morning routine data
        git_state = state.get("git", {})
        session_data = state.get("session", {})

        updated_status = {
            **existing_status,  # Preserve existing data
            "session_id": f"morning-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "last_morning_routine": {
                "executed_at": datetime.now().isoformat(),
                "ready_to_code_score": f"{score}/100",
                "breakdown": breakdown,
                "session_restored": session_data.get("restored", False),
            },
            "git_status": {
                "current_branch": git_state.get("branch", "unknown"),
                "commits_behind_remote": git_state.get("behind_remote", 0),
                "uncommitted_files": git_state.get("uncommitted_files", 0),
                "stashes": git_state.get("stashes", 0),
            },
            "metrics": {
                **existing_status.get("metrics", {}),
                "ready_to_code_score": f"{score}/100",
            },
        }

        # Add recommendations
        updated_status["recommendations"] = {
            **existing_status.get("recommendations", {}),
            "before_coding": self._get_setup_recommendations(score, state),
            "todays_focus": self._get_today_recommendations(state),
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

        services_data = state.get("services", {})
        required = services_data.get("required_services", [])
        running = services_data.get("running_services", [])
        missing = [s for s in required if s not in running]

        if missing:
            recommendations.append(f"Start dev services: {', '.join(missing)}")

        git_data = state.get("git", {})
        if git_data.get("behind_remote", 0) > 0:
            recommendations.append(
                f"Sync with remote: git pull ({git_data['behind_remote']} commits behind)"
            )

        if score < 60:
            recommendations.append(
                "⚠️ Low Ready to Code Score - address setup issues first"
            )

        return recommendations if recommendations else ["All set! Ready to code."]

    def _get_today_recommendations(self, state: Dict[str, Any]) -> list:
        """Generate today's focus recommendations."""
        recommendations = []

        github_data = state.get("github", {})
        prs = len(github_data.get("prs_needing_review", []))
        if prs > 0:
            recommendations.append(f"Review {prs} pending PRs")

        issues = len(github_data.get("issues_needing_triage", []))
        if issues > 0:
            recommendations.append(f"Triage {issues} open issues")

        recommendations.append("Check overnight commits and CI results")

        return recommendations


def print_profiles():
    """Print available profiles (Issue #105)."""
    if not ProfileManager:
        print("Error: ProfileManager not available", file=sys.stderr)
        sys.exit(1)

    print("\nAvailable Morning Routine Profiles:\n")

    for profile in ProfileManager.list_profiles("routine"):
        print(f"  {profile.name}")
        print(f"    {profile.description}")
        print(f"    Use case: {profile.use_case}")
        if profile.flags:
            flag_names = [f"--{k.replace('_', '-')}" for k in profile.flags.keys()]
            print(f"    Flags: {', '.join(flag_names)}")
        else:
            print("    Flags: (defaults)")
        print()


def print_detailed_help():
    """Print detailed help with examples (Issue #105)."""
    print("""
PopKit Morning Routine - Detailed Help

PROFILES:
  Use --profile <name> to apply a preset configuration:

  --profile minimal    Fast health check (< 10s)
  --profile standard   Normal daily routine (~20s)
  --profile thorough   Deep analysis with metrics (~60s)
  --profile ci         CI/CD optimized, JSON output

EXAMPLES:
  # Quick morning check (minimal profile)
  /popkit:routine morning --profile minimal

  # Standard morning with measurement
  /popkit:routine morning --measure

  # Thorough check with all validations
  /popkit:routine morning --profile thorough

  # CI/CD mode
  /popkit:routine morning --profile ci

  # Override profile flags
  /popkit:routine morning --profile minimal --measure

FLAGS:
  --quick              One-line summary instead of full report
  --measure            Track and report performance metrics
  --optimized          Use caching for efficiency
  --skip-tests         Skip running tests (faster)
  --skip-services      Skip service health checks
  --skip-deployments   Skip deployment status
  --full               Include all checks (slower)
  --simple             Markdown tables instead of ASCII dashboard

SMART DEFAULTS:
  --measure automatically enables --simple for parseable output
  --full overrides --optimized (thorough checks can't be cached)

See --help-full for complete documentation from routine.md.
""")


def print_full_help():
    """Print full documentation (Issue #105)."""
    print("""
PopKit Morning Routine - Complete Documentation

For complete documentation, see:
  packages/popkit-dev/commands/routine.md

Or use: /popkit:help routine
""")


def main():
    """Main entry point for morning workflow."""
    import argparse

    parser = argparse.ArgumentParser(
        description="PopKit Morning Routine",
        epilog="Use --help-detailed for detailed examples",
    )

    # Profile selection
    parser.add_argument(
        "--profile",
        choices=["minimal", "standard", "thorough", "ci"],
        help="Profile preset (minimal|standard|thorough|ci)",
    )

    # Individual flags (existing)
    parser.add_argument("--quick", action="store_true", help="Quick one-line summary")
    parser.add_argument(
        "--measure", action="store_true", help="Track performance metrics"
    )
    parser.add_argument("--optimized", action="store_true", help="Use caching")
    parser.add_argument("--no-cache", action="store_true", help="Force fresh execution")

    # New flags (documented but not yet fully implemented - Issue #105)
    parser.add_argument(
        "--simple", action="store_true", help="Markdown tables instead of ASCII"
    )
    parser.add_argument("--skip-tests", action="store_true", help="Skip test execution")
    parser.add_argument(
        "--skip-services", action="store_true", help="Skip service health checks"
    )
    parser.add_argument(
        "--skip-deployments", action="store_true", help="Skip deployment status"
    )
    parser.add_argument(
        "--full", action="store_true", help="Include all checks (slower)"
    )
    parser.add_argument(
        "--no-nightly", action="store_true", help="Skip nightly comparison"
    )

    # Help tiers (Issue #105)
    parser.add_argument(
        "--help-detailed", action="store_true", help="Show detailed examples"
    )
    parser.add_argument(
        "--help-full", action="store_true", help="Show full documentation"
    )

    # List profiles (Issue #105)
    parser.add_argument(
        "--list-profiles", action="store_true", help="List available profiles"
    )

    args = parser.parse_args()

    # Handle help tiers
    if args.help_detailed:
        print_detailed_help()
        sys.exit(0)

    if args.help_full:
        print_full_help()
        sys.exit(0)

    # List profiles
    if args.list_profiles:
        print_profiles()
        sys.exit(0)

    # Collect flags from args
    flags = {
        "quick": args.quick,
        "measure": args.measure,
        "optimized": args.optimized,
        "no_cache": args.no_cache,
        "simple": args.simple,
        "skip_tests": args.skip_tests,
        "skip_services": args.skip_services,
        "skip_deployments": args.skip_deployments,
        "full": args.full,
        "no_nightly": args.no_nightly,
    }

    # Apply profile if specified (Issue #105)
    if args.profile and ProfileManager:
        try:
            flags = ProfileManager.apply_profile(args.profile, flags, "routine")
            print(f"[PROFILE] Using '{args.profile}' profile", file=sys.stderr)
        except ValueError as e:
            print(f"[ERROR] {e}", file=sys.stderr)
            sys.exit(1)

    # Apply smart defaults (Issue #105)
    if ProfileManager:
        flags = ProfileManager.apply_smart_defaults(flags)

    # Run workflow with resolved flags
    workflow = MorningWorkflow(**flags)
    result = workflow.run()

    # Print report
    print(result["report"])

    # Exit with score as status (0-100)
    sys.exit(0 if result["score"] >= 70 else 1)


if __name__ == "__main__":
    main()
