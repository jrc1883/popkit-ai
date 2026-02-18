#!/usr/bin/env python3
"""
Benchmark Orchestrator - Spawns and monitors parallel benchmark trials

Orchestrates benchmark execution by:
1. Spawning separate Claude Code windows for WITH PopKit and BASELINE trials
2. Monitoring trial progress via recording files
3. Collecting results when trials complete
4. Generating and opening HTML report

User sees both trials working side-by-side in separate windows.

Usage:
    from benchmark_orchestrator import BenchmarkOrchestrator

    orchestrator = BenchmarkOrchestrator(
        task_id="jwt-authentication",
        trials=3,
        verbose=True
    )
    orchestrator.run()

    # Opens windows, monitors, generates report, opens in browser
"""

import json
import os
import platform
import subprocess
import sys
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared-py"))

from benchmark_analyzer import BenchmarkAnalyzer
from codebase_manager import CodebaseManager
from report_generator import ReportGenerator


class BenchmarkOrchestrator:
    """Orchestrates parallel benchmark trials in separate windows."""

    TASK_CATEGORIES = (
        "feature-addition",
        "bug-fixing",
        "refactoring",
        "code-review",
        "performance",
    )

    def __init__(
        self,
        task_id: str,
        trials: int = 3,
        parallel: bool = True,
        verbose: bool = False,
        output_dir: Optional[Path] = None,
    ):
        """
        Initialize orchestrator.

        Args:
            task_id: Task identifier (e.g., "jwt-authentication")
            trials: Number of trials per configuration
            parallel: Run WITH PopKit and BASELINE in parallel
            verbose: Enable verbose logging
            output_dir: Directory for benchmark results
        """
        self.task_id = task_id
        self.trials = trials
        self.parallel = parallel
        self.verbose = verbose

        # Output directory
        self.output_dir = output_dir or Path.cwd() / "benchmark-results"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Recording directories
        self.popkit_recordings_dir = Path.home() / ".claude" / "popkit" / "recordings"
        self.claude_projects_dir = Path.home() / ".claude" / "projects"

        # Task definition
        self.task_definition_path: Optional[Path] = None
        self.task_def = self._load_task_definition()

        # Response file
        self.response_file = self._find_response_file()

        # Codebase manager
        self.codebase_manager = CodebaseManager()

        # Tracking
        self.active_sessions: Dict[str, Dict] = {}
        self.completed_sessions: List[str] = []
        self.failed_sessions: List[str] = []

    def _candidate_task_paths(self) -> List[Path]:
        """Build candidate task definition paths for both flat and nested layouts."""
        task_paths: List[Path] = []
        tasks_root = Path("packages/popkit-ops/tasks")

        for category in self.TASK_CATEGORIES:
            category_dir = tasks_root / category
            task_paths.append(category_dir / f"{self.task_id}.yml")
            task_paths.append(category_dir / self.task_id / "task.yml")

        # Backward-compatible local tasks layout.
        task_paths.append(Path("tasks") / f"{self.task_id}.yml")
        task_paths.append(Path("tasks") / self.task_id / "task.yml")
        return task_paths

    def _candidate_response_paths(self) -> List[Path]:
        """Build candidate response file paths, preferring alongside loaded task definition."""
        response_paths: List[Path] = []

        if self.task_definition_path:
            if self.task_definition_path.name == "task.yml":
                response_paths.append(
                    self.task_definition_path.parent / "responses.json"
                )
            else:
                response_paths.append(
                    self.task_definition_path.with_name(
                        f"{self.task_id}-responses.json"
                    )
                )

        tasks_root = Path("packages/popkit-ops/tasks")
        for category in self.TASK_CATEGORIES:
            category_dir = tasks_root / category
            response_paths.append(category_dir / f"{self.task_id}-responses.json")
            response_paths.append(category_dir / self.task_id / "responses.json")

        # Backward-compatible local tasks layout.
        response_paths.append(Path("tasks") / f"{self.task_id}-responses.json")
        response_paths.append(Path("tasks") / self.task_id / "responses.json")

        # Preserve order, remove duplicates.
        unique_paths: List[Path] = []
        seen = set()
        for path in response_paths:
            normalized = str(path)
            if normalized in seen:
                continue
            seen.add(normalized)
            unique_paths.append(path)

        return unique_paths

    def _load_task_definition(self) -> dict:
        """Load task definition from YAML file."""
        import yaml

        for path in self._candidate_task_paths():
            if not path.exists():
                continue

            with open(path, encoding="utf-8") as f:
                task_def = yaml.safe_load(f)

            self.task_definition_path = path
            if isinstance(task_def, dict):
                task_def["__task_path__"] = str(path)
            return task_def

        raise FileNotFoundError(f"Task definition not found for: {self.task_id}")

    def _find_response_file(self) -> Optional[Path]:
        """Find response file for task."""
        for path in self._candidate_response_paths():
            if path.exists():
                return path
        return None

    def run(self) -> Path:
        """
        Run orchestrated benchmark.

        Returns:
            Path to HTML report
        """
        self._print_header()

        # Run trials
        for trial_num in range(1, self.trials + 1):
            self._print(f"\n{'=' * 70}")
            self._print(f"TRIAL {trial_num}/{self.trials}")
            self._print(f"{'=' * 70}\n")

            if self.parallel:
                self._run_trial_parallel(trial_num)
            else:
                self._run_trial_sequential(trial_num)

        # Analyze results
        self._print(f"\n{'=' * 70}")
        self._print("ANALYZING RESULTS")
        self._print(f"{'=' * 70}\n")
        report_path = self._analyze_and_report()

        # Open report
        self._print("\n🎉 Opening report in browser...")
        webbrowser.open(f"file:///{report_path}")

        self._print("\n✅ Benchmark complete!")
        self._print(f"   Report: {report_path}")

        return report_path

    def _run_trial_parallel(self, trial_num: int):
        """Run WITH PopKit and BASELINE trials in parallel."""
        # Spawn both trials
        with_popkit_session = self._spawn_trial(trial_num, with_popkit=True)
        baseline_session = self._spawn_trial(trial_num, with_popkit=False)

        # Monitor until both complete
        self._print("⏳ Monitoring trials...")
        self._monitor_trials([with_popkit_session, baseline_session])

    def _run_trial_sequential(self, trial_num: int):
        """Run WITH PopKit and BASELINE trials sequentially."""
        # WITH PopKit first
        with_popkit_session = self._spawn_trial(trial_num, with_popkit=True)
        self._print("⏳ Waiting for WITH PopKit trial...")
        self._monitor_trials([with_popkit_session])

        # BASELINE second
        baseline_session = self._spawn_trial(trial_num, with_popkit=False)
        self._print("⏳ Waiting for BASELINE trial...")
        self._monitor_trials([baseline_session])

    def _spawn_trial(self, trial_num: int, with_popkit: bool) -> str:
        """
        Spawn a trial in a new Claude Code window.

        Args:
            trial_num: Trial number
            with_popkit: Enable PopKit for this trial

        Returns:
            session_id for tracking
        """
        config_label = "with" if with_popkit else "base"
        session_id = f"{self.task_id}-{config_label}-{trial_num}"

        self._print(
            f"▶ Trial {trial_num} {'WITH PopKit' if with_popkit else 'BASELINE'}"
        )
        self._print(f"  Session ID: {session_id}")

        # Create worktree
        worktree_path = self._create_worktree(trial_num, with_popkit)
        self._print(f"  Worktree: {worktree_path}")

        # Build environment
        env = self._build_environment(session_id, with_popkit, worktree_path)

        # Get prompt and augment with benchmark instructions
        base_prompt = self.task_def.get("user_prompt", "")
        prompt = self._augment_prompt_for_benchmark(base_prompt)

        # Spawn window
        self._spawn_window(prompt, env, worktree_path, session_id)

        # Track session
        self.active_sessions[session_id] = {
            "trial_num": trial_num,
            "with_popkit": with_popkit,
            "worktree_path": worktree_path,
            "started_at": time.time(),
        }

        self._print("  ✓ Window launched")

        return session_id

    def _create_worktree(self, trial_num: int, with_popkit: bool) -> Path:
        """Create isolated worktree for trial."""
        config_label = "with" if with_popkit else "base"
        branch_name = f"bench-{self.task_id}-{config_label}-{trial_num}"

        return self.codebase_manager.create_worktree(
            task_id=f"{self.task_id}-{config_label}",
            trial_num=trial_num,
            baseline_ref="HEAD",
            branch_name=branch_name,
        )

    def _augment_prompt_for_benchmark(self, base_prompt: str) -> str:
        """Add benchmark-specific instructions to prompt for autonomous execution."""
        benchmark_instructions = """

IMPORTANT BENCHMARK INSTRUCTIONS:
This is an automated benchmark test. You must work COMPLETELY AUTONOMOUSLY without asking any questions or requesting approvals.

For all decisions:
- Choose the most reasonable/recommended option
- Follow standard best practices
- Auto-approve all reasonable actions (tests, installs, builds, linting)
- Make implementation decisions based on the task requirements
- Do NOT use AskUserQuestion - make decisions directly
- Do NOT ask for permission - proceed with standard operations

For this specific task:
- Use the specifications provided in the task description
- Follow standard patterns for this type of implementation
- Test your work when complete
- Fix any issues that arise

Work efficiently and complete the task without human intervention.
"""
        return base_prompt + benchmark_instructions

    def _build_environment(
        self, session_id: str, with_popkit: bool, worktree_path: Path
    ) -> Dict[str, str]:
        """Build environment variables for trial."""
        env = os.environ.copy()

        # Enable recording
        env["POPKIT_RECORD"] = "true"
        env["POPKIT_RECORD_ID"] = session_id

        # Enable benchmark mode
        env["POPKIT_BENCHMARK_MODE"] = "true"

        # Disable security filters for benchmarks (prevent false positives)
        env["POPKIT_SECURITY_FILTERS"] = "off"

        # Set response file
        if self.response_file:
            env["POPKIT_BENCHMARK_RESPONSES"] = str(self.response_file.absolute())

        # Disable PopKit for baseline
        if not with_popkit:
            env["CLAUDE_DISABLE_PLUGINS"] = (
                "popkit-core,popkit-dev,popkit-ops,popkit-research"
            )

        return env

    def _spawn_window(
        self, prompt: str, env: Dict[str, str], worktree_path: Path, session_id: str
    ):
        """Spawn new Claude Code window (platform-specific)."""
        # Escape prompt for shell
        escaped_prompt = prompt.replace('"', '\\"').replace("'", "\\'")

        system = platform.system()

        try:
            if system == "Windows":
                # Windows: Create batch file with environment embedded
                # This ensures PATH and other env vars are available in spawned window
                batch_file = self.output_dir / f"launch-{session_id}.bat"

                with open(batch_file, "w") as f:
                    # Write environment variables
                    for key, value in env.items():
                        # Escape special chars for batch
                        safe_value = value.replace("%", "%%").replace('"', '""')
                        f.write(f'set "{key}={safe_value}"\n')

                    # Change to worktree and run claude
                    f.write(f'cd /d "{worktree_path}"\n')
                    f.write(f'claude "{escaped_prompt}"\n')
                    f.write("pause\n")  # Keep window open after completion

                # Spawn new window running the batch file
                cmd = [
                    "cmd",
                    "/c",
                    "start",
                    f"Claude Benchmark - {session_id}",
                    "cmd",
                    "/k",
                    str(batch_file),
                ]
                subprocess.Popen(cmd)

            elif system == "Darwin":
                # Mac: Use osascript to open new Terminal window
                script = f"""
                tell application "Terminal"
                    do script "cd '{worktree_path}' && claude '{escaped_prompt}'"
                    activate
                end tell
                """
                subprocess.Popen(["osascript", "-e", script], env=env)

            else:
                # Linux: Try gnome-terminal, then fallback to xterm
                try:
                    cmd = [
                        "gnome-terminal",
                        "--title",
                        f"Claude Benchmark - {session_id}",
                        "--",
                        "bash",
                        "-c",
                        f"cd '{worktree_path}' && claude '{escaped_prompt}'; exec bash",
                    ]
                    subprocess.Popen(cmd, env=env)
                except FileNotFoundError:
                    # Fallback to xterm
                    cmd = [
                        "xterm",
                        "-T",
                        f"Claude Benchmark - {session_id}",
                        "-e",
                        f"cd '{worktree_path}' && claude '{escaped_prompt}'; bash",
                    ]
                    subprocess.Popen(cmd, env=env)

        except Exception as e:
            self._print(f"  [ERROR] Failed to spawn window: {e}")
            raise

    def _monitor_trials(self, session_ids: List[str], timeout: int = 3600):
        """Monitor trials until they complete."""
        start_time = time.time()
        completed = set()

        while len(completed) < len(session_ids):
            for session_id in session_ids:
                if session_id in completed:
                    continue

                # Check for recording
                recording_path = self._find_recording(session_id)
                if recording_path and self._is_complete(recording_path):
                    duration = (
                        time.time() - self.active_sessions[session_id]["started_at"]
                    )
                    self._print(f"  ✓ {session_id} completed ({duration:.0f}s)")
                    completed.add(session_id)
                    self.completed_sessions.append(session_id)

            # Timeout check
            if time.time() - start_time > timeout:
                remaining = set(session_ids) - completed
                self._print(f"  [WARN] Trials timed out: {remaining}")
                self.failed_sessions.extend(remaining)
                break

            # Poll every 3 seconds
            time.sleep(3)

    def _find_recording(self, session_id: str) -> Optional[Path]:
        """Find recording file for session."""
        # Check PopKit recordings (WITH PopKit trials)
        if self.popkit_recordings_dir.exists():
            for recording in self.popkit_recordings_dir.glob("*.json"):
                try:
                    with open(recording) as f:
                        data = json.load(f)
                        if data.get("session_id") == session_id:
                            return recording
                except Exception:
                    continue

        # Check Claude projects (BASELINE trials)
        if self.claude_projects_dir.exists():
            for project_dir in self.claude_projects_dir.iterdir():
                if not project_dir.is_dir():
                    continue

                for jsonl_file in project_dir.glob("*.jsonl"):
                    if session_id in jsonl_file.stem:
                        return jsonl_file

        return None

    def _is_complete(self, recording_path: Path) -> bool:
        """Check if recording is complete."""
        try:
            if recording_path.suffix == ".jsonl":
                # JSONL: Check if file has content
                with open(recording_path) as f:
                    lines = f.readlines()
                    return len(lines) > 0

            else:
                # JSON: Check for session_end event
                with open(recording_path) as f:
                    data = json.load(f)
                    event_types = {e.get("type") for e in data.get("events", [])}
                    return "session_end" in event_types

        except Exception:
            return False

    def _analyze_and_report(self) -> Path:
        """Analyze results and generate HTML report."""
        # Collect recordings
        with_popkit_recordings = []
        baseline_recordings = []

        for session_id in self.completed_sessions:
            recording = self._find_recording(session_id)
            if not recording:
                continue

            if self.active_sessions[session_id]["with_popkit"]:
                with_popkit_recordings.append(recording)
            else:
                baseline_recordings.append(recording)

        self._print(f"  WITH PopKit: {len(with_popkit_recordings)} recordings")
        self._print(f"  BASELINE: {len(baseline_recordings)} recordings")

        # Analyze
        analyzer = BenchmarkAnalyzer(
            with_popkit_recordings=with_popkit_recordings,
            baseline_recordings=baseline_recordings,
        )

        results = analyzer.analyze()

        # Generate report
        timestamp = datetime.now().strftime("%Y-%m-%d")
        report_name = f"{self.task_id}-{timestamp}"

        generator = ReportGenerator(
            analysis_results=results, task_def=self.task_def, output_dir=self.output_dir
        )

        html_path = generator.generate_html(filename=f"{report_name}.html")

        self._print(f"  ✓ Report generated: {html_path}")

        return html_path

    def _print_header(self):
        """Print orchestrator header."""
        self._print(f"\n{'=' * 70}")
        self._print("🚀 PopKit Benchmark Suite - Orchestrator Mode")
        self._print(f"{'=' * 70}")
        self._print(f"\nTask: {self.task_id}")
        self._print(f"Trials: {self.trials} per configuration")
        self._print(f"Total sessions: {self.trials * 2}")
        self._print(f"Mode: {'Parallel' if self.parallel else 'Sequential'}")
        if self.response_file:
            self._print(f"Response file: {self.response_file.name}")
        else:
            self._print("Response file: NOT FOUND (may ask questions)")
        self._print(f"\n{'=' * 70}\n")

    def _print(self, message: str):
        """Print message if verbose or always for important messages."""
        if self.verbose or any(
            x in message
            for x in ["▶", "✓", "✅", "🚀", "🎉", "📊", "[ERROR]", "[WARN]"]
        ):
            print(message)
            sys.stdout.flush()


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="PopKit Benchmark Orchestrator")
    parser.add_argument("task_id", help="Task identifier (e.g., jwt-authentication)")
    parser.add_argument(
        "--trials", type=int, default=3, help="Trials per configuration"
    )
    parser.add_argument(
        "--sequential",
        action="store_true",
        help="Run trials sequentially (not parallel)",
    )
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    parser.add_argument("--output-dir", type=Path, help="Output directory")

    args = parser.parse_args()

    orchestrator = BenchmarkOrchestrator(
        task_id=args.task_id,
        trials=args.trials,
        parallel=not args.sequential,
        verbose=args.verbose,
        output_dir=args.output_dir,
    )

    orchestrator.run()


if __name__ == "__main__":
    main()
