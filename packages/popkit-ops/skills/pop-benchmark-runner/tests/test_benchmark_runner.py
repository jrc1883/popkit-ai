#!/usr/bin/env python3
"""
Test suite for benchmark_runner.py

Tests benchmark orchestration and trial execution.
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared-py"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from benchmark_runner import BenchmarkRunner, InsufficientTrialsError


class TestBenchmarkRunner(unittest.TestCase):
    """Test BenchmarkRunner orchestration"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.output_dir = self.temp_dir / "benchmark-results"

        self.task_def = {
            "id": "test-task",
            "category": "test",
            "description": "Test task",
            "user_prompt": "Test prompt",
            "verification": ["npm test"],
            "expected_outcomes": ["Test passes"],
        }

        self.runner = BenchmarkRunner(
            task_def=self.task_def, trials=3, output_dir=self.output_dir, verbose=False
        )

    def tearDown(self):
        """Clean up test fixtures"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    # =========================================================================
    # INITIALIZATION TESTS
    # =========================================================================

    def test_init_basic(self):
        """Test basic initialization"""
        self.assertEqual(self.runner.task_def, self.task_def)
        self.assertEqual(self.runner.trials, 3)
        self.assertFalse(self.runner.verbose)
        self.assertTrue(self.output_dir.exists())

    def test_init_default_output_dir(self):
        """Test default output directory"""
        runner = BenchmarkRunner(task_def=self.task_def)
        self.assertEqual(runner.output_dir, Path("benchmark-results"))

    def test_init_creates_output_dir(self):
        """Test that output directory is created"""
        custom_output = self.temp_dir / "custom-output"
        BenchmarkRunner(task_def=self.task_def, output_dir=custom_output)
        self.assertTrue(custom_output.exists())

    # =========================================================================
    # RUN WITH POPKIT TESTS
    # =========================================================================

    @patch.object(BenchmarkRunner, "_execute_trial")
    def test_run_with_popkit_success(self, mock_trial):
        """Test successful run with PopKit"""
        # Mock successful trials
        mock_trial.side_effect = [
            Path("/recording1.json"),
            Path("/recording2.json"),
            Path("/recording3.json"),
        ]

        recordings = self.runner.run_with_popkit()

        self.assertEqual(len(recordings), 3)
        self.assertEqual(mock_trial.call_count, 3)

        # Verify PopKit was enabled in calls
        for call_args in mock_trial.call_args_list:
            self.assertTrue(call_args[1].get("with_popkit", False))

    @patch.object(BenchmarkRunner, "_execute_trial")
    def test_run_with_popkit_partial_failures(self, mock_trial):
        """Test run with some trial failures"""
        # 2 successes, 1 failure
        mock_trial.side_effect = [
            Path("/recording1.json"),
            None,  # Failed trial
            Path("/recording3.json"),
        ]

        recordings = self.runner.run_with_popkit()

        # Should return only successful recordings
        self.assertEqual(len(recordings), 2)

    @patch.object(BenchmarkRunner, "_execute_trial")
    def test_run_with_popkit_insufficient_trials(self, mock_trial):
        """Test run with too many failures"""
        # Only 1 success out of 3 (< 50%)
        mock_trial.side_effect = [
            None,  # Failed
            None,  # Failed
            Path("/recording3.json"),  # Success
        ]

        with self.assertRaises(InsufficientTrialsError):
            self.runner.run_with_popkit()

    # =========================================================================
    # RUN BASELINE TESTS
    # =========================================================================

    @patch.object(BenchmarkRunner, "_execute_trial")
    def test_run_baseline_success(self, mock_trial):
        """Test successful baseline run"""
        mock_trial.side_effect = [
            Path("/baseline1.json"),
            Path("/baseline2.json"),
            Path("/baseline3.json"),
        ]

        recordings = self.runner.run_baseline()

        self.assertEqual(len(recordings), 3)

        # Verify PopKit was disabled in calls
        for call_args in mock_trial.call_args_list:
            self.assertFalse(call_args[1].get("with_popkit", True))

    # =========================================================================
    # EXECUTE TRIAL TESTS
    # =========================================================================

    @patch.object(BenchmarkRunner, "_setup_environment")
    @patch.object(BenchmarkRunner, "_execute_task")
    @patch.object(BenchmarkRunner, "_collect_recording")
    @patch.object(BenchmarkRunner, "_verify_recording")
    @patch("benchmark_runner.CodebaseManager")
    def test_execute_trial_success(
        self, mock_cm_class, mock_verify, mock_collect, mock_execute, mock_setup
    ):
        """Test successful trial execution"""
        # Mock CodebaseManager
        mock_cm = Mock()
        mock_cm.create_worktree.return_value = self.temp_dir / "worktree"
        mock_cm_class.return_value = mock_cm

        # Mock successful execution
        mock_setup.return_value = {"POPKIT_RECORD": "true"}
        mock_execute.return_value = True
        recording_path = self.temp_dir / "recording.json"
        recording_path.touch()
        mock_collect.return_value = recording_path
        mock_verify.return_value = True

        recording = self.runner._execute_trial(
            trial_num=1, with_popkit=True, codebase_manager=mock_cm
        )

        self.assertEqual(recording, recording_path)

        # Verify workflow steps called
        mock_cm.create_worktree.assert_called_once()
        mock_setup.assert_called_once()
        mock_execute.assert_called_once()
        mock_collect.assert_called_once()
        mock_verify.assert_called_once()

    @patch.object(BenchmarkRunner, "_setup_environment")
    @patch("benchmark_runner.CodebaseManager")
    def test_execute_trial_worktree_failure(self, mock_cm_class, mock_setup):
        """Test trial failure during worktree creation"""
        mock_cm = Mock()
        mock_cm.create_worktree.side_effect = Exception("Git error")
        mock_cm_class.return_value = mock_cm

        recording = self.runner._execute_trial(
            trial_num=1, with_popkit=True, codebase_manager=mock_cm
        )

        self.assertIsNone(recording)

    @patch.object(BenchmarkRunner, "_setup_environment")
    @patch.object(BenchmarkRunner, "_execute_task")
    @patch("benchmark_runner.CodebaseManager")
    def test_execute_trial_execution_failure(self, mock_cm_class, mock_execute, mock_setup):
        """Test trial failure during task execution"""
        mock_cm = Mock()
        mock_cm.create_worktree.return_value = self.temp_dir / "worktree"
        mock_cm_class.return_value = mock_cm

        mock_setup.return_value = {}
        mock_execute.return_value = False  # Execution failed

        recording = self.runner._execute_trial(
            trial_num=1, with_popkit=True, codebase_manager=mock_cm
        )

        self.assertIsNone(recording)

    # =========================================================================
    # SETUP ENVIRONMENT TESTS
    # =========================================================================

    def test_setup_environment_with_popkit(self):
        """Test environment setup with PopKit enabled"""
        session_id = "test-session-123"

        env_vars = self.runner._setup_environment(
            session_id=session_id, with_popkit=True, worktree_path=Path("/worktree")
        )

        # Verify PopKit-specific environment variables
        self.assertEqual(env_vars["POPKIT_RECORD"], "true")
        self.assertEqual(env_vars["POPKIT_BENCHMARK_MODE"], "true")
        self.assertEqual(env_vars["POPKIT_RECORD_ID"], session_id)
        self.assertNotIn("CLAUDE_DISABLE_PLUGINS", env_vars)

    def test_setup_environment_baseline(self):
        """Test environment setup for baseline (no PopKit)"""
        session_id = "test-session-123"

        env_vars = self.runner._setup_environment(
            session_id=session_id, with_popkit=False, worktree_path=Path("/worktree")
        )

        # Verify PopKit disabled
        self.assertIn("CLAUDE_DISABLE_PLUGINS", env_vars)
        self.assertIn("popkit", env_vars["CLAUDE_DISABLE_PLUGINS"].lower())

    def test_setup_environment_test_mode(self):
        """Test environment setup in test mode"""
        session_id = "test-session-123"

        # Set test mode via env var
        with patch.dict("os.environ", {"TEST_MODE": "true"}):
            env_vars = self.runner._setup_environment(
                session_id=session_id, with_popkit=True, worktree_path=Path("/worktree")
            )

            self.assertEqual(env_vars["TEST_MODE"], "true")

    # =========================================================================
    # EXECUTE TASK TESTS
    # =========================================================================

    @patch("benchmark_runner.subprocess.run")
    def test_execute_task_mock_mode(self, mock_run):
        """Test task execution in mock mode"""
        # Mock mode (TEST_MODE env var set)
        with patch.dict("os.environ", {"TEST_MODE": "true"}):
            success = self.runner._execute_task(worktree_path=Path("/worktree"), env_vars={})

            # Should not actually run subprocess
            mock_run.assert_not_called()

            # Mock mode always succeeds
            self.assertTrue(success)

    # =========================================================================
    # RECORDING TESTS
    # =========================================================================

    def test_create_mock_recording(self):
        """Test mock recording creation"""
        session_id = "test-session-123"
        worktree_path = self.temp_dir / "worktree"

        self.runner._create_mock_recording(session_id, worktree_path)

        # Verify recording file created in recordings directory
        recordings_dir = Path.home() / ".claude" / "popkit" / "recordings"
        # Find the recording file (has timestamp prefix)
        recording_files = list(recordings_dir.glob(f"*{session_id}.json"))
        self.assertTrue(len(recording_files) > 0, f"No recording found in {recordings_dir}")

        recording_path = recording_files[0]
        self.assertTrue(recording_path.exists())

        # Verify content is valid JSON
        data = json.loads(recording_path.read_text())
        self.assertEqual(data["session_id"], session_id)
        self.assertIn("events", data)

        # Cleanup
        recording_path.unlink()

    def test_collect_recording_success(self):
        """Test successful recording collection"""
        session_id = "test-session-123"

        # Create mock recording file
        recording_path = Path(".claude/popkit/recordings") / f"{session_id}.json"
        recording_path.parent.mkdir(parents=True, exist_ok=True)
        recording_path.write_text('{"session_id": "test-session-123", "test": "data"}')

        try:
            collected_path = self.runner._collect_recording(session_id, with_popkit=True)

            # Should return path to recording
            self.assertIsNotNone(collected_path)
            self.assertTrue(collected_path.exists())
            # Should be in recordings directory (not copied)
            self.assertIn(".claude", str(collected_path))
        finally:
            # Cleanup
            if recording_path.exists():
                recording_path.unlink()
            if recording_path.parent.exists():
                recording_path.parent.rmdir()

    def test_collect_recording_not_found(self):
        """Test recording collection when file doesn't exist"""
        session_id = "nonexistent-session"

        collected_path = self.runner._collect_recording(session_id, with_popkit=True)

        self.assertIsNone(collected_path)

    def test_verify_recording_valid(self):
        """Test recording verification with valid file"""
        recording_path = self.temp_dir / "valid_recording.json"

        # Create valid recording with required events
        data = {
            "session_id": "test-123",
            "events": [
                {"type": "session_start", "sequence": 0},
                {"type": "tool_call", "sequence": 1, "tool_name": "Read"},
                {"type": "session_end", "sequence": 2},
            ],
        }
        recording_path.write_text(json.dumps(data))

        is_valid = self.runner._verify_recording(recording_path)

        self.assertTrue(is_valid)

    def test_verify_recording_invalid_json(self):
        """Test recording verification with invalid JSON"""
        recording_path = self.temp_dir / "invalid.json"
        recording_path.write_text("not valid json {")

        is_valid = self.runner._verify_recording(recording_path)

        self.assertFalse(is_valid)

    def test_verify_recording_missing_fields(self):
        """Test recording verification with missing required fields"""
        recording_path = self.temp_dir / "incomplete.json"

        # Missing 'events' field
        data = {"session_id": "test-123"}
        recording_path.write_text(json.dumps(data))

        is_valid = self.runner._verify_recording(recording_path)

        self.assertFalse(is_valid)

    # =========================================================================
    # RESULTS SUMMARY TESTS
    # =========================================================================

    @patch.object(BenchmarkRunner, "run_with_popkit")
    @patch.object(BenchmarkRunner, "run_baseline")
    def test_get_results_summary(self, mock_baseline, mock_popkit):
        """Test results summary generation"""
        # Mock recordings
        mock_popkit.return_value = [
            Path("/recording1.json"),
            Path("/recording2.json"),
            Path("/recording3.json"),
        ]
        mock_baseline.return_value = [Path("/baseline1.json"), Path("/baseline2.json")]

        # Execute runs
        self.runner.run_with_popkit()
        self.runner.run_baseline()

        summary = self.runner.get_results_summary()

        # Verify summary structure
        self.assertIn("task_id", summary)
        self.assertIn("trials_requested", summary)
        self.assertIn("with_popkit", summary)
        self.assertIn("baseline", summary)

        # Verify counts
        self.assertEqual(summary["with_popkit"]["successful"], 3)
        self.assertEqual(summary["baseline"]["successful"], 2)

    # =========================================================================
    # CLEANUP TESTS
    # =========================================================================

    @patch("benchmark_runner.CodebaseManager")
    def test_cleanup_all_worktrees(self, mock_cm_class):
        """Test worktree cleanup"""
        mock_cm = Mock()
        mock_cm_class.return_value = mock_cm

        self.runner.cleanup_all_worktrees()

        # Verify CodebaseManager cleanup called
        mock_cm.cleanup_all_worktrees.assert_called_once()

    # =========================================================================
    # LOGGING TESTS
    # =========================================================================

    def test_log_verbose_mode(self):
        """Test logging in verbose mode"""
        verbose_runner = BenchmarkRunner(task_def=self.task_def, trials=3, verbose=True)

        # Should not raise error
        verbose_runner._log("Test message")

    def test_log_quiet_mode(self):
        """Test logging in quiet mode"""
        # Should not raise error
        self.runner._log("Test message")


if __name__ == "__main__":
    unittest.main()
