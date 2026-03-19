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

import io
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

# Fix Windows console encoding for Unicode characters
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# Add shared-py to path for utilities
sys.path.insert(0, str(Path.home() / ".claude" / "popkit" / "packages" / "shared-py"))

try:
    from popkit_shared.utils.flag_profiles import ProfileManager
    from popkit_shared.utils.generic_state_capture import capture_project_state
    from popkit_shared.utils.routine_cache import RoutineCache
    from popkit_shared.utils.routine_measurement import RoutineMeasurement
    from popkit_shared.utils.session_branch_manager import (
        get_branch_history,
        get_current_branch as get_session_branch,
        list_branches as list_session_branches,
    )
    from popkit_shared.utils.session_recorder import (
        get_recorder,
        record_reasoning,
        record_recommendation,
    )

    HAS_SESSION_BRANCHES = True
    HAS_UTILITIES = True
except ImportError:
    HAS_UTILITIES = False
    HAS_SESSION_BRANCHES = False
    ProfileManager = None
    print(
        "[WARN] PopKit utilities not available - running in degraded mode",
        file=sys.stderr,
    )

# Try relative import (when used as package), fall back to direct import
try:
    from .report_generator import generate_nightly_report, generate_quick_summary
    from .sleep_score import calculate_sleep_score, get_score_interpretation
except ImportError:
    from report_generator import generate_nightly_report, generate_quick_summary
    from sleep_score import calculate_sleep_score, get_score_interpretation


class NightlyWorkflow:
    """Orchestrates nightly routine execution."""

    def __init__(
        self,
        quick: bool = False,
        measure: bool = False,
        optimized: bool = False,
        no_cache: bool = False,
        # New flags for profile system (Issue #105)
        simple: bool = False,
        skip_cleanup: bool = False,
        skip_ip_scan: bool = False,
        no_morning: bool = False,
    ):
        """
        Initialize nightly workflow.

        Args:
            quick: Generate one-line summary instead of full report
            measure: Track performance metrics
            optimized: Use caching for efficiency
            no_cache: Force fresh execution (ignore cache)
            simple: Use markdown tables instead of ASCII dashboard
            skip_cleanup: Skip auto-cleanup actions
            skip_ip_scan: Skip IP leak scan
            no_morning: Skip "Since This Morning" section
        """
        self.quick = quick
        self.measure = measure
        self.optimized = optimized
        self.no_cache = no_cache
        self.simple = simple
        self.skip_cleanup = skip_cleanup
        self.skip_ip_scan = skip_ip_scan
        self.no_morning = no_morning

        # Initialize measurement if requested
        self.measurement = None
        if measure and HAS_UTILITIES:
            self.measurement = RoutineMeasurement("nightly")

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
                "workflow_start",
                "Starting nightly routine workflow",
                {"quick": self.quick, "optimized": self.optimized},
            )

        # Step 1: Collect project state
        print("[1/4] Collecting project state...", file=sys.stderr)
        state = self._collect_state()

        # Step 1b: Collect session branch data
        state["session_branches"] = self._collect_session_branches()

        # Step 2: Calculate Sleep Score
        print("[2/4] Calculating Sleep Score...", file=sys.stderr)
        score, breakdown = calculate_sleep_score(state)

        if self.recorder:
            record_reasoning(
                "score_calculated",
                f"Sleep Score: {score}/100",
                {"score": score, "breakdown": breakdown},
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
                "nightly_complete",
                interpretation["recommendation"],
                score,
                interpretation["interpretation"],
            )

        # Finalize measurement
        if self.measurement:
            self.measurement.finalize(
                {
                    "sleep_score": score,
                    "uncommitted_files": state.get("git", {}).get(
                        "uncommitted_files", 0
                    ),
                    "stashes": state.get("git", {}).get("stashes", 0),
                }
            )

        return {
            "score": score,
            "report": report,
            "state": state,
            "breakdown": breakdown,
        }

    def _collect_session_branches(self) -> Dict[str, Any]:
        """
        Collect session branch data from STATUS.json.

        Returns:
            Dict with keys:
            - branches: List of branch dicts
            - current_branch: Current session branch ID
            - history: Recent branch history entries
        """
        if not HAS_SESSION_BRANCHES:
            return {"branches": [], "current_branch": "main", "history": []}

        try:
            branches = list_session_branches()
            branch_id, _ = get_session_branch()
            history = get_branch_history(limit=50)
            print(
                f"[OK] Session branches: {len(branches)} total, current: {branch_id}",
                file=sys.stderr,
            )
            return {
                "branches": branches,
                "current_branch": branch_id,
                "history": history,
            }
        except Exception as e:
            print(
                f"[WARN] Could not load session branches: {e}",
                file=sys.stderr,
            )
            return {"branches": [], "current_branch": "main", "history": []}

    def _collect_state(self) -> Dict[str, Any]:
        """
        Collect complete project state.

        Uses cache if optimized mode enabled, otherwise collects fresh.
        """
        if HAS_UTILITIES:
            # Use capture_state utility
            if self.optimized and self.cache and not self.no_cache:
                # Try cache first
                cached_state = self.cache.get("nightly_state")
                if cached_state:
                    print("[CACHE] Using cached state", file=sys.stderr)
                    return cached_state

            # Collect fresh state
            state = capture_project_state()

            # Cache for next time if optimized
            if self.optimized and self.cache:
                self.cache.set("nightly_state", state, ttl=300)  # 5 min TTL

            return state
        else:
            # Fallback: manual state collection
            return self._collect_state_fallback()

    def _collect_state_fallback(self) -> Dict[str, Any]:
        """Fallback state collection without utilities."""
        import shutil
        import subprocess

        # Import git_utils from popkit-dev hooks
        # __file__ is in packages/popkit-dev/skills/pop-nightly/scripts/
        # parents[3] gets us to popkit-dev/
        popkit_dev_root = Path(__file__).parents[3]  # packages/popkit-dev
        hooks_path = popkit_dev_root / "hooks"
        sys.path.insert(0, str(hooks_path))
        from git_utils import count_stale_branches, git_fetch_prune

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

        # Run git fetch --prune to clean up stale remote tracking branches
        prune_success, prune_message = git_fetch_prune()
        if prune_success:
            print(f"[OK] {prune_message}", file=sys.stderr)
        else:
            print(f"[WARN] {prune_message}", file=sys.stderr)

        # Git state - all commands use list-based arguments (SECURE)
        status_output = run_command(["git", "status", "--porcelain"])

        # Count stashes without pipes - SECURE
        stash_list = run_command(["git", "stash", "list"])
        stash_count = len(stash_list.splitlines()) if stash_list else 0

        # Count merged branches - SECURE (use Python to filter instead of shell pipes)
        all_branches = run_command(["git", "branch", "--merged", "main"])
        merged_count = 0
        if all_branches:
            for line in all_branches.splitlines():
                line = line.strip()
                if line and not line.startswith("*") and line != "main":
                    merged_count += 1

        git_state = {
            "branch": run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"]),
            "uncommitted_files": len(status_output.splitlines())
            if status_output
            else 0,
            "uncommitted_files_list": [
                {"status": line[:2].strip(), "path": line[3:]}
                for line in status_output.splitlines()
            ]
            if status_output
            else [],
            "stashes": stash_count,
            "merged_branches": merged_count,
            "stale_branches": count_stale_branches(),
        }

        # GitHub state (if gh CLI available)
        github_state = {}
        if shutil.which("gh"):
            try:
                issues_json = run_command(
                    [
                        "gh",
                        "issue",
                        "list",
                        "--state",
                        "open",
                        "--limit",
                        "5",
                        "--json",
                        "number,title,updatedAt",
                    ]
                )
                github_state["issues"] = json.loads(issues_json) if issues_json else []

                ci_json = run_command(
                    [
                        "gh",
                        "run",
                        "list",
                        "--limit",
                        "1",
                        "--json",
                        "conclusion,status,createdAt",
                    ]
                )
                ci_data = json.loads(ci_json) if ci_json else []
                github_state["ci_status"] = ci_data[0] if ci_data else {}
            except json.JSONDecodeError:
                github_state = {"issues": [], "ci_status": {}}

        # Services state - SECURE: Use pgrep instead of shell pipes
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
            except (subprocess.SubprocessError, FileNotFoundError):
                # Skip services that can't be checked
                pass

        # Count log files - SECURE: Use Python glob instead of shell
        log_count = 0
        try:
            log_dir = Path.home() / ".claude" / "logs"
            if log_dir.exists():
                log_count = len(list(log_dir.glob("*.log")))
        except (IOError, PermissionError):
            # Skip if log directory is inaccessible
            pass

        services_state = {"running_services": running_services, "log_files": log_count}

        return {
            "git": git_state,
            "github": github_state,
            "services": services_state,
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
                existing_status = json.loads(status_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                print(
                    f"[WARN] Could not parse existing STATUS.json: {e}", file=sys.stderr
                )

        # Update with nightly routine data
        git_state = state.get("git", {})

        updated_status = {
            **existing_status,  # Preserve existing data
            "session_id": f"nightly-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}",
            "timestamp": datetime.now().isoformat(),
            "last_nightly_routine": {
                "executed_at": datetime.now().isoformat(),
                "sleep_score": f"{score}/100",
                "breakdown": breakdown,
            },
            "git_status": {
                "current_branch": git_state.get("branch", "unknown"),
                "last_commit": git_state.get("last_commit", "unknown"),
                "uncommitted_files": git_state.get("uncommitted_files", 0),
                "files": [
                    f"{item['path']} ({item['status']})"
                    for item in git_state.get("uncommitted_files_list", [])[:10]
                ],
                "stashes": git_state.get("stashes", 0),
                "action_required": "Commit or stash changes"
                if git_state.get("uncommitted_files", 0) > 0
                else None,
            },
            "metrics": {
                **existing_status.get("metrics", {}),
                "sleep_score": f"{score}/100",
            },
        }

        # Add recommendations
        updated_status["recommendations"] = {
            **existing_status.get("recommendations", {}),
            "before_leaving": self._get_before_leaving_recommendations(score, state),
            "next_session": [
                "Run /popkit:routine morning to check overnight changes",
                "Review and address items from nightly report",
            ],
        }

        # Write updated STATUS.json
        try:
            status_file.write_text(
                json.dumps(updated_status, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            print("[OK] STATUS.json updated", file=sys.stderr)
        except Exception as e:
            print(f"[ERROR] Failed to update STATUS.json: {e}", file=sys.stderr)

    def _get_before_leaving_recommendations(
        self, score: int, state: Dict[str, Any]
    ) -> list:
        """Generate before-leaving recommendations."""
        recommendations = []
        git_state = state.get("git", {})

        if git_state.get("uncommitted_files", 0) > 0:
            recommendations.append(
                f"Commit or stash {git_state['uncommitted_files']} uncommitted files"
            )

        if git_state.get("stashes", 0) > 5:
            recommendations.append(
                f"Review {git_state['stashes']} stashes - consider cleanup"
            )

        if score < 60:
            recommendations.append("⚠️ Low Sleep Score - address issues before leaving")

        return recommendations if recommendations else ["All clear! Safe to close."]


def print_profiles():
    """Print available profiles (Issue #105)."""
    if not ProfileManager:
        print("Error: ProfileManager not available", file=sys.stderr)
        sys.exit(1)

    print("\nAvailable Nightly Routine Profiles:\n")

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
PopKit Nightly Routine - Detailed Help

PROFILES:
  Use --profile <name> to apply a preset configuration:

  --profile minimal    Fast cleanup (< 10s)
  --profile standard   Normal end-of-day routine (~20s)
  --profile thorough   Deep cleanup with metrics (~60s)
  --profile ci         CI/CD optimized

EXAMPLES:
  # Quick nightly check (minimal profile)
  /popkit:routine nightly --profile minimal

  # Standard nightly with measurement
  /popkit:routine nightly --measure

  # Thorough cleanup with all checks
  /popkit:routine nightly --profile thorough

  # CI/CD mode
  /popkit:routine nightly --profile ci

FLAGS:
  --quick              One-line summary instead of full report
  --measure            Track and report performance metrics
  --optimized          Use caching for efficiency
  --skip-cleanup       Skip auto-cleanup actions
  --skip-ip-scan       Skip IP leak scan
  --simple             Markdown tables instead of ASCII dashboard

SMART DEFAULTS:
  --measure automatically enables --simple for parseable output

See --help-full for complete documentation from routine.md.
""")


def print_full_help():
    """Print full documentation (Issue #105)."""
    print("""
PopKit Nightly Routine - Complete Documentation

For complete documentation, see:
  packages/popkit-dev/commands/routine.md

Or use: /popkit:help routine
""")


def main():
    """Main entry point for nightly workflow."""
    import argparse

    parser = argparse.ArgumentParser(
        description="PopKit Nightly Routine",
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
    parser.add_argument(
        "--skip-cleanup", action="store_true", help="Skip auto-cleanup actions"
    )
    parser.add_argument("--skip-ip-scan", action="store_true", help="Skip IP leak scan")
    parser.add_argument(
        "--no-morning", action="store_true", help="Skip morning comparison"
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
        "skip_cleanup": args.skip_cleanup,
        "skip_ip_scan": args.skip_ip_scan,
        "no_morning": args.no_morning,
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
    workflow = NightlyWorkflow(**flags)
    result = workflow.run()

    # Print report
    print(result["report"])

    # Exit with score as status (0-100)
    sys.exit(0 if result["score"] >= 70 else 1)


if __name__ == "__main__":
    main()
