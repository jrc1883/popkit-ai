#!/usr/bin/env python3
"""
Benchmark Runner - Main orchestration module for benchmark execution.

Orchestrates the execution of benchmark tasks comparing PopKit-enabled
Claude Code vs baseline Claude Code (without PopKit).

Architecture:
    1. Load task definition from YAML
    2. Create isolated git worktrees for each trial
    3. Execute trials with recording enabled (both configurations)
    4. Collect recordings for analysis
    5. Return paths to all recorded sessions

Usage:
    # Programmatic usage
    from benchmark_runner import BenchmarkRunner
    import yaml

    task_def = yaml.safe_load(Path("task.yml").read_text())
    runner = BenchmarkRunner(task_def, trials=5)

    # Run trials with PopKit enabled
    with_popkit_recordings = runner.run_with_popkit()

    # Run baseline trials (no PopKit)
    baseline_recordings = runner.run_baseline()

    # Get summary
    summary = runner.get_results_summary()

    # CLI usage
    python benchmark_runner.py task.yml --trials 5 --config all --verbose

Environment Variables:
    POPKIT_RECORD=true                     - Enable session recording
    POPKIT_BENCHMARK_MODE=true              - Enable automation mode
    POPKIT_BENCHMARK_RESPONSES=<path>       - Response file for automation
    POPKIT_RECORD_ID=<session-id>           - Session identifier
    POPKIT_COMMAND=<command-name>           - Command name for recording
    CLAUDE_DISABLE_PLUGINS=<plugins>        - Disable plugins (baseline mode)
    TEST_MODE=true                          - Enable test mode (mock execution)

Windows Support:
    Uses C:/temp/bench/ as base directory to avoid MAX_PATH issues.
    Shorter branch names (bench/<session-id>) to prevent path length errors.

Error Handling:
    - WorktreeExistsError: Worktree already exists (retry with cleanup)
    - GitError: Git operation failed (logged, trial skipped)
    - InsufficientTrialsError: Less than 50% trials succeeded (abort)
    - BenchmarkExecutionError: General execution failure

Trial Success Criteria:
    - Worktree created successfully
    - Task executed without errors
    - Recording file collected
    - Recording verified (valid JSON, required events)
"""

import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from codebase_manager import CodebaseManager, GitError, WorktreeExistsError


class BenchmarkExecutionError(Exception):
    """Raised when benchmark execution fails."""

    pass


class InsufficientTrialsError(Exception):
    """Raised when too many trials fail."""

    pass


class BenchmarkRunner:
    """Orchestrates benchmark execution comparing PopKit vs baseline."""

    def __init__(
        self,
        task_def: Dict[str, Any],
        trials: int = 3,
        output_dir: Optional[Path] = None,
        verbose: bool = False,
    ):
        """
        Initialize benchmark runner.

        Args:
            task_def: Task definition dictionary (loaded from YAML)
            trials: Number of trials per configuration (default: 3)
            output_dir: Directory for output files (default: benchmark-results/)
            verbose: Enable verbose logging
        """
        self.task_def = task_def
        self.task_id = task_def["id"]
        self.trials = trials
        self.verbose = verbose

        # Setup output directory
        self.output_dir = output_dir or Path("benchmark-results")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize codebase manager with shorter base path for Windows
        # Use C:\temp\bench\ to avoid Windows MAX_PATH issues
        bench_base = Path("C:/temp/bench") if os.name == "nt" else None
        self.codebase_manager = CodebaseManager(base_dir=bench_base)

        # Recordings directory
        self.recordings_dir = Path.home() / ".claude" / "popkit" / "recordings"
        self.recordings_dir.mkdir(parents=True, exist_ok=True)

        # Track recordings
        self.with_popkit_recordings: List[Path] = []
        self.baseline_recordings: List[Path] = []

        self._log(f"[INFO] Initialized benchmark runner for task: {self.task_id}")
        self._log(f"[INFO] Trials per configuration: {trials}")
        self._log(f"[INFO] Output directory: {self.output_dir}")

    def run_with_popkit(self) -> List[Path]:
        """
        Run benchmark trials with PopKit enabled.

        Returns:
            List of paths to recording files

        Raises:
            InsufficientTrialsError: If less than 50% of trials succeed
        """
        self._log("\n" + "=" * 70)
        self._log("RUNNING TRIALS WITH POPKIT ENABLED")
        self._log("=" * 70)

        recordings = []
        failures = 0

        for trial_num in range(1, self.trials + 1):
            self._log(f"\n[INFO] Trial {trial_num}/{self.trials} (WITH PopKit)")
            self._log("-" * 70)

            try:
                recording_path = self._execute_trial(
                    trial_num=trial_num, with_popkit=True, baseline=False
                )

                if recording_path and recording_path.exists():
                    recordings.append(recording_path)
                    self._log(f"[SUCCESS] Trial {trial_num} completed")
                    self._log(f"[INFO] Recording: {recording_path}")
                else:
                    failures += 1
                    self._log(f"[WARN] Trial {trial_num} failed - no recording found")

            except Exception as e:
                failures += 1
                self._log(f"[ERROR] Trial {trial_num} failed: {e}")
                if self.verbose:
                    import traceback

                    traceback.print_exc()

        # Validate success rate
        success_rate = len(recordings) / self.trials
        self._log(
            f"\n[INFO] Completed {len(recordings)}/{self.trials} trials successfully"
        )
        self._log(f"[INFO] Success rate: {success_rate:.1%}")

        if success_rate < 0.5:
            raise InsufficientTrialsError(
                f"Less than 50% trials succeeded ({len(recordings)}/{self.trials})"
            )

        self.with_popkit_recordings = recordings
        return recordings

    def run_baseline(self) -> List[Path]:
        """
        Run benchmark trials without PopKit (baseline configuration).

        Returns:
            List of paths to recording files

        Raises:
            InsufficientTrialsError: If less than 50% of trials succeed
        """
        self._log("\n" + "=" * 70)
        self._log("RUNNING BASELINE TRIALS (WITHOUT POPKIT)")
        self._log("=" * 70)

        recordings = []
        failures = 0

        for trial_num in range(1, self.trials + 1):
            self._log(f"\n[INFO] Trial {trial_num}/{self.trials} (BASELINE)")
            self._log("-" * 70)

            try:
                recording_path = self._execute_trial(
                    trial_num=trial_num, with_popkit=False, baseline=True
                )

                if recording_path and recording_path.exists():
                    recordings.append(recording_path)
                    self._log(f"[SUCCESS] Trial {trial_num} completed")
                    self._log(f"[INFO] Recording: {recording_path}")
                else:
                    failures += 1
                    self._log(f"[WARN] Trial {trial_num} failed - no recording found")

            except Exception as e:
                failures += 1
                self._log(f"[ERROR] Trial {trial_num} failed: {e}")
                if self.verbose:
                    import traceback

                    traceback.print_exc()

        # Validate success rate
        success_rate = len(recordings) / self.trials
        self._log(
            f"\n[INFO] Completed {len(recordings)}/{self.trials} trials successfully"
        )
        self._log(f"[INFO] Success rate: {success_rate:.1%}")

        if success_rate < 0.5:
            raise InsufficientTrialsError(
                f"Less than 50% trials succeeded ({len(recordings)}/{self.trials})"
            )

        self.baseline_recordings = recordings
        return recordings

    def _execute_trial(
        self, trial_num: int, with_popkit: bool, baseline: bool
    ) -> Optional[Path]:
        """
        Execute a single benchmark trial.

        Args:
            trial_num: Trial number (1-based)
            with_popkit: Enable PopKit for this trial
            baseline: Is this a baseline trial (affects naming)

        Returns:
            Path to recording file, or None if trial failed
        """
        worktree_path = None
        session_id = str(uuid.uuid4())[:8]
        config_label = "with-popkit" if with_popkit else "baseline"

        try:
            # Step 1: Create isolated worktree
            self._log("[1/5] Creating worktree...")
            worktree_name_suffix = f"{config_label}-trial{trial_num}"
            # Use shorter branch name to avoid Windows path length issues
            short_branch_name = f"bench/{session_id}"
            worktree_path = self.codebase_manager.create_worktree(
                task_id=f"{self.task_id}-{worktree_name_suffix}",
                trial_num=trial_num,
                baseline_ref=self.task_def.get("initial_state", "HEAD"),
                branch_name=short_branch_name,
            )

            # Step 2: Setup environment
            self._log("[2/5] Configuring environment...")
            env = self._setup_environment(
                session_id=session_id,
                with_popkit=with_popkit,
                worktree_path=worktree_path,
            )

            # Step 3: Execute task
            self._log("[3/5] Executing task...")
            success = self._execute_task(
                worktree_path=worktree_path,
                env=env,
                session_id=session_id,
            )

            if not success:
                self._log("[WARN] Task execution failed")
                return None

            # Step 4: Collect recording
            self._log("[4/5] Collecting recording...")
            recording_path = self._collect_recording(session_id)

            if not recording_path:
                self._log(f"[WARN] Recording not found for session {session_id}")
                return None

            # Step 5: Verify recording
            self._log("[5/5] Verifying recording...")
            if not self._verify_recording(recording_path):
                self._log("[WARN] Recording verification failed")
                return None

            return recording_path

        except (WorktreeExistsError, GitError) as e:
            self._log(f"[ERROR] Git operation failed: {e}")
            return None

        finally:
            # Cleanup worktree
            if worktree_path:
                try:
                    self._log("[CLEANUP] Removing worktree...")
                    self.codebase_manager.cleanup_worktree(worktree_path, force=True)
                except Exception as e:
                    self._log(f"[WARN] Failed to cleanup worktree: {e}")

    def _setup_environment(
        self, session_id: str, with_popkit: bool, worktree_path: Path
    ) -> Dict[str, str]:
        """
        Setup environment variables for trial execution.

        Args:
            session_id: Unique session identifier
            with_popkit: Enable PopKit configuration
            worktree_path: Path to worktree

        Returns:
            Environment dictionary
        """
        env = os.environ.copy()

        # Enable recording
        env["POPKIT_RECORD"] = "true"
        env["POPKIT_RECORD_ID"] = session_id

        # Enable benchmark mode (automation)
        env["POPKIT_BENCHMARK_MODE"] = "true"

        # Set command name for recording
        config_label = "with-popkit" if with_popkit else "baseline"
        env["POPKIT_COMMAND"] = f"benchmark-{self.task_id}-{config_label}"

        # Load response file if exists
        response_file = (
            Path("packages/popkit-ops/tasks")
            / self.task_def.get("category", "feature-addition")
            / f"{self.task_id}-responses.json"
        )
        if response_file.exists():
            env["POPKIT_BENCHMARK_RESPONSES"] = str(response_file.absolute())
            self._log(f"[INFO] Using response file: {response_file}")

        # PopKit configuration
        if not with_popkit:
            # Disable PopKit plugins for baseline
            env["CLAUDE_DISABLE_PLUGINS"] = (
                "popkit-core,popkit-dev,popkit-ops,popkit-research"
            )
            self._log("[INFO] PopKit plugins disabled (baseline mode)")

        self._log(f"[INFO] Session ID: {session_id}")
        self._log(f"[INFO] Working directory: {worktree_path}")

        return env

    def _execute_task(
        self, worktree_path: Path, env: Dict[str, str], session_id: str
    ) -> bool:
        """
        Execute the benchmark task in the worktree.

        This is a mock implementation. In production, this would:
        1. Launch Claude Code CLI in the worktree
        2. Feed the user prompt from task_def
        3. Monitor for completion
        4. Return success/failure

        Args:
            worktree_path: Path to worktree
            env: Environment variables
            session_id: Session identifier

        Returns:
            True if task completed successfully
        """
        user_prompt = self.task_def.get("user_prompt", "")

        # MOCK: For now, we simulate task execution
        # In production, this would be:
        #   subprocess.run(['claude', '--prompt', user_prompt], cwd=worktree_path, env=env)

        self._log(f"[INFO] User prompt: {user_prompt[:100]}...")

        # Create a mock recording file for testing
        if os.getenv("TEST_MODE") == "true":
            self._create_mock_recording(session_id, worktree_path)
            return True

        # TODO: Real implementation
        # command = ['claude', '--prompt', user_prompt]
        # result = subprocess.run(
        #     command,
        #     cwd=worktree_path,
        #     env=env,
        #     capture_output=True,
        #     timeout=3600  # 1 hour timeout
        # )
        # return result.returncode == 0

        self._log("[WARN] Task execution not implemented (mock mode)")
        return False

    def _create_mock_recording(self, session_id: str, worktree_path: Path) -> None:
        """Create a mock recording for testing."""
        timestamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        command_name = f"benchmark-{self.task_id}"
        filename = f"{timestamp}-{command_name}-{session_id}.json"
        recording_path = self.recordings_dir / filename

        mock_recording = {
            "session_id": session_id,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "events": [
                {
                    "type": "session_start",
                    "sequence": 0,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "session_id": session_id,
                    "command": command_name,
                    "working_directory": str(worktree_path),
                },
                {
                    "type": "tool_call",
                    "sequence": 1,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "tool_name": "Read",
                    "parameters": {"file_path": "package.json"},
                    "result": "success",
                    "duration_ms": 50,
                },
                {
                    "type": "session_end",
                    "sequence": 2,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": "completed",
                    "total_events": 3,
                },
            ],
        }

        with open(recording_path, "w") as f:
            json.dump(mock_recording, f, indent=2)

        self._log(f"[MOCK] Created recording: {recording_path}")

    def _collect_recording(self, session_id: str) -> Optional[Path]:
        """
        Collect recording file for the given session.

        Args:
            session_id: Session identifier

        Returns:
            Path to recording file, or None if not found
        """
        # Look for recording file matching session ID
        for recording_file in self.recordings_dir.glob("*.json"):
            try:
                with open(recording_file, "r") as f:
                    data = json.load(f)
                    if data.get("session_id") == session_id:
                        return recording_file
            except (json.JSONDecodeError, IOError):
                continue

        return None

    def _verify_recording(self, recording_path: Path) -> bool:
        """
        Verify that recording file is valid and complete.

        Args:
            recording_path: Path to recording file

        Returns:
            True if recording is valid
        """
        try:
            with open(recording_path, "r") as f:
                data = json.load(f)

            # Check required fields
            if "session_id" not in data:
                self._log("[WARN] Missing session_id in recording")
                return False

            if "events" not in data or not isinstance(data["events"], list):
                self._log("[WARN] Missing or invalid events in recording")
                return False

            # Check for session_start and session_end events
            event_types = {e.get("type") for e in data["events"]}
            if "session_start" not in event_types:
                self._log("[WARN] Missing session_start event")
                return False

            if "session_end" not in event_types:
                self._log("[WARN] Missing session_end event")
                return False

            return True

        except (json.JSONDecodeError, IOError) as e:
            self._log(f"[WARN] Failed to verify recording: {e}")
            return False

    def cleanup_all_worktrees(self) -> None:
        """
        Cleanup all worktrees created for this task.

        This is a safety method to cleanup after failed runs.
        """
        self._log(f"[INFO] Cleaning up all worktrees for task: {self.task_id}")
        self.codebase_manager.cleanup_all_worktrees(task_id=self.task_id)

    def get_results_summary(self) -> Dict[str, Any]:
        """
        Get summary of benchmark results.

        Returns:
            Dictionary with summary statistics
        """
        return {
            "task_id": self.task_id,
            "task_description": self.task_def.get("description", ""),
            "trials": self.trials,
            "with_popkit_recordings": len(self.with_popkit_recordings),
            "baseline_recordings": len(self.baseline_recordings),
            "with_popkit_success_rate": len(self.with_popkit_recordings) / self.trials,
            "baseline_success_rate": len(self.baseline_recordings) / self.trials,
            "recordings": {
                "with_popkit": [str(p) for p in self.with_popkit_recordings],
                "baseline": [str(p) for p in self.baseline_recordings],
            },
        }

    def _log(self, message: str) -> None:
        """Log message to stdout."""
        print(message)


def main():
    """Test benchmark runner functionality."""
    import argparse
    import yaml

    parser = argparse.ArgumentParser(description="Benchmark Runner")
    parser.add_argument("task_file", help="Path to task YAML file")
    parser.add_argument(
        "--trials", type=int, default=3, help="Number of trials (default: 3)"
    )
    parser.add_argument(
        "--config", choices=["all", "popkit", "baseline"], default="all"
    )
    parser.add_argument(
        "--cleanup", action="store_true", help="Cleanup worktrees after run"
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument(
        "--test-mode", action="store_true", help="Enable test mode (mock execution)"
    )

    args = parser.parse_args()

    # Enable test mode
    if args.test_mode:
        os.environ["TEST_MODE"] = "true"

    # Load task definition
    task_file = Path(args.task_file)
    if not task_file.exists():
        print(f"[ERROR] Task file not found: {task_file}")
        sys.exit(1)

    with open(task_file, "r") as f:
        task_def = yaml.safe_load(f)

    # Create runner
    runner = BenchmarkRunner(task_def, trials=args.trials, verbose=args.verbose)

    try:
        # Run benchmarks
        if args.config in ["all", "popkit"]:
            with_popkit = runner.run_with_popkit()
            print(f"\n[SUCCESS] Collected {len(with_popkit)} PopKit recordings")

        if args.config in ["all", "baseline"]:
            baseline = runner.run_baseline()
            print(f"\n[SUCCESS] Collected {len(baseline)} baseline recordings")

        # Print summary
        summary = runner.get_results_summary()
        print("\n" + "=" * 70)
        print("BENCHMARK RESULTS SUMMARY")
        print("=" * 70)
        print(json.dumps(summary, indent=2))

        # Optionally cleanup
        if args.cleanup:
            runner.cleanup_all_worktrees()

    except (InsufficientTrialsError, BenchmarkExecutionError) as e:
        print(f"\n[ERROR] Benchmark failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n[INFO] Benchmark interrupted by user")
        runner.cleanup_all_worktrees()
        sys.exit(130)


if __name__ == "__main__":
    main()
