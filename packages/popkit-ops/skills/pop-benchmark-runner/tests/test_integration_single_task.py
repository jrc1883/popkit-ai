#!/usr/bin/env python3
"""
Integration test for single task execution.

Tests end-to-end benchmark workflow for a single task.
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared-py"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from benchmark_analyzer import BenchmarkAnalyzer
from benchmark_runner import BenchmarkRunner
from report_generator import ReportGenerator


class TestIntegrationSingleTask(unittest.TestCase):
    """Integration test for single task benchmark"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.output_dir = self.temp_dir / "benchmark-results"

        # Create realistic task definition
        self.task_def = {
            "id": "jwt-authentication",
            "category": "feature-addition",
            "description": "Add JWT authentication",
            "user_prompt": "Implement JWT-based authentication for the API",
            "verification": ["npm test", "npm run lint"],
            "expected_outcomes": [
                "JWT middleware created",
                "Login endpoint implemented",
                "All tests passing",
            ],
            "estimated_duration_minutes": 20,
        }

        # Write task definition to file
        self.task_file = self.temp_dir / "task.yml"
        self.task_file.write_text(yaml.dump(self.task_def))

    def tearDown(self):
        """Clean up test fixtures"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    # =========================================================================
    # END-TO-END WORKFLOW TESTS
    # =========================================================================

    @patch("benchmark_runner.CodebaseManager")
    @patch.dict("os.environ", {"TEST_MODE": "true"})
    def test_single_task_complete_workflow(self, mock_cm_class):
        """Test complete workflow: run → analyze → report"""
        # Mock CodebaseManager
        mock_cm = Mock()
        mock_cm.create_worktree.return_value = self.temp_dir / "worktree"
        mock_cm_class.return_value = mock_cm

        # Step 1: Run benchmark
        runner = BenchmarkRunner(
            task_def=self.task_def, trials=3, output_dir=self.output_dir, verbose=False
        )

        with_popkit_recordings = runner.run_with_popkit()
        baseline_recordings = runner.run_baseline()

        # Verify recordings collected
        self.assertEqual(len(with_popkit_recordings), 3)
        self.assertEqual(len(baseline_recordings), 3)
        self.assertTrue(all(r.exists() for r in with_popkit_recordings))
        self.assertTrue(all(r.exists() for r in baseline_recordings))

        # Step 2: Analyze results
        analyzer = BenchmarkAnalyzer(
            with_popkit_recordings=with_popkit_recordings,
            baseline_recordings=baseline_recordings,
        )

        # Mock RecordingAnalyzer for analysis
        with patch("benchmark_analyzer.RecordingAnalyzer") as mock_ra:
            mock_ra_instance = Mock()
            mock_ra_instance.get_token_count.return_value = 1000
            mock_ra_instance.get_tool_usage_breakdown.return_value = {"Read": 10}
            mock_ra_instance.get_file_modifications.return_value = 2
            mock_ra_instance.get_error_summary.return_value = {"failed_tool_calls": 1}
            mock_ra_instance.get_performance_metrics.return_value = {"duration_seconds": 120}
            mock_ra.return_value = mock_ra_instance

            with patch("benchmark_analyzer.subprocess.run") as mock_subprocess:
                mock_subprocess.return_value = Mock(returncode=0)

                results = analyzer.analyze()

        # Verify analysis results
        self.assertIn("task_id", results)
        self.assertIn("metrics", results)
        self.assertEqual(results["task_id"], "jwt-authentication")

        # Step 3: Generate reports
        generator = ReportGenerator(analysis_results=results, task_def=self.task_def)

        markdown_report = generator.generate_markdown()
        html_report = generator.generate_html()

        # Verify reports generated
        self.assertIsNotNone(markdown_report)
        self.assertIsNotNone(html_report)
        self.assertIn("jwt-authentication", markdown_report)
        self.assertIn("jwt-authentication", html_report)

        # Step 4: Verify cleanup
        runner.cleanup_all_worktrees()

        # Verify summary
        summary = runner.get_results_summary()
        self.assertEqual(summary["task_id"], "jwt-authentication")
        self.assertEqual(summary["trials_requested"], 3)

    @patch("benchmark_runner.CodebaseManager")
    @patch.dict("os.environ", {"TEST_MODE": "true"})
    def test_single_task_with_failures(self, mock_cm_class):
        """Test workflow with some trial failures"""
        # Mock CodebaseManager with some failures
        mock_cm = Mock()
        mock_cm.create_worktree.side_effect = [
            self.temp_dir / "worktree1",  # Success
            Exception("Git error"),  # Failure
            self.temp_dir / "worktree3",  # Success
            self.temp_dir / "worktree4",  # Success
            self.temp_dir / "worktree5",  # Success
            self.temp_dir / "worktree6",  # Success
        ]
        mock_cm_class.return_value = mock_cm

        runner = BenchmarkRunner(task_def=self.task_def, trials=3, output_dir=self.output_dir)

        # Run with some failures
        with_popkit_recordings = runner.run_with_popkit()
        baseline_recordings = runner.run_baseline()

        # Should have 2 successful with_popkit (1 failed)
        self.assertEqual(len(with_popkit_recordings), 2)
        # Should have 3 successful baseline
        self.assertEqual(len(baseline_recordings), 3)

    @patch("benchmark_runner.CodebaseManager")
    @patch.dict("os.environ", {"TEST_MODE": "true"})
    def test_single_task_performance_metrics(self, mock_cm_class):
        """Test that performance metrics are realistic"""
        mock_cm = Mock()
        mock_cm.create_worktree.return_value = self.temp_dir / "worktree"
        mock_cm_class.return_value = mock_cm

        runner = BenchmarkRunner(task_def=self.task_def, trials=3, output_dir=self.output_dir)

        # Run benchmarks
        with_popkit_recordings = runner.run_with_popkit()
        baseline_recordings = runner.run_baseline()

        # Verify all recordings have required structure
        for recording_path in with_popkit_recordings + baseline_recordings:
            data = json.loads(recording_path.read_text())

            self.assertIn("session_id", data)
            self.assertIn("events", data)
            self.assertIn("metadata", data)

            # Verify metadata includes performance data
            metadata = data["metadata"]
            self.assertIn("tokens", metadata)
            self.assertIn("duration_seconds", metadata)

            # Verify realistic values
            self.assertGreater(metadata["tokens"], 0)
            self.assertGreater(metadata["duration_seconds"], 0)


if __name__ == "__main__":
    unittest.main()
