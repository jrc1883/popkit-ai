#!/usr/bin/env python3
"""
Integration test for full benchmark suite execution.

Tests end-to-end workflow for running all 8 benchmark tasks.
"""

import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, Mock
import tempfile
import shutil
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared-py"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from benchmark_runner import BenchmarkRunner
from benchmark_analyzer import BenchmarkAnalyzer
from report_generator import ReportGenerator


class TestIntegrationFullSuite(unittest.TestCase):
    """Integration test for full benchmark suite"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.output_dir = self.temp_dir / "benchmark-results"

        # Create all 8 benchmark task definitions
        self.task_defs = [
            {
                "id": "jwt-authentication",
                "category": "feature-addition",
                "description": "Add JWT authentication",
                "user_prompt": "Implement JWT-based authentication for the API",
                "verification": ["npm test", "npm run lint"],
                "expected_outcomes": ["JWT middleware created", "All tests passing"],
                "estimated_duration_minutes": 20,
            },
            {
                "id": "dark-mode-implementation",
                "category": "feature-addition",
                "description": "Implement dark mode",
                "user_prompt": "Add dark mode toggle with theme persistence",
                "verification": ["npm test", "npm run lint"],
                "expected_outcomes": ["Theme toggle component", "CSS variables setup"],
                "estimated_duration_minutes": 15,
            },
            {
                "id": "race-condition-fix",
                "category": "bug-fix",
                "description": "Fix race condition in async handler",
                "user_prompt": "Resolve race condition in concurrent data access",
                "verification": ["npm test"],
                "expected_outcomes": [
                    "Mutex/lock implemented",
                    "Tests pass consistently",
                ],
                "estimated_duration_minutes": 25,
            },
            {
                "id": "memory-leak-fix",
                "category": "bug-fix",
                "description": "Fix memory leak in event handlers",
                "user_prompt": "Identify and fix memory leak in event listener cleanup",
                "verification": ["npm test", "npm run test:memory"],
                "expected_outcomes": [
                    "Event listeners cleaned up",
                    "Memory stable over time",
                ],
                "estimated_duration_minutes": 30,
            },
            {
                "id": "async-await-conversion",
                "category": "refactoring",
                "description": "Convert callbacks to async/await",
                "user_prompt": "Refactor promise chains to use async/await syntax",
                "verification": ["npm test", "npm run lint"],
                "expected_outcomes": ["Cleaner code", "Same functionality"],
                "estimated_duration_minutes": 20,
            },
            {
                "id": "extract-shared-utilities",
                "category": "refactoring",
                "description": "Extract shared utility functions",
                "user_prompt": "Move duplicate code into shared utilities module",
                "verification": ["npm test"],
                "expected_outcomes": ["Utils module created", "No duplication"],
                "estimated_duration_minutes": 15,
            },
            {
                "id": "security-vulnerability-scan",
                "category": "code-quality",
                "description": "Security audit and vulnerability fixes",
                "user_prompt": "Audit code for security issues and fix vulnerabilities",
                "verification": ["npm audit", "npm test"],
                "expected_outcomes": [
                    "No high/critical vulnerabilities",
                    "Security best practices",
                ],
                "estimated_duration_minutes": 35,
            },
            {
                "id": "performance-bottleneck-identification",
                "category": "code-quality",
                "description": "Identify and optimize performance bottlenecks",
                "user_prompt": "Profile application and optimize slow code paths",
                "verification": ["npm test", "npm run benchmark"],
                "expected_outcomes": ["Bottlenecks identified", "Performance improved"],
                "estimated_duration_minutes": 40,
            },
        ]

        # Write task definitions to files
        self.task_files = []
        for task_def in self.task_defs:
            task_file = self.temp_dir / f"{task_def['id']}.yml"
            task_file.write_text(yaml.dump(task_def))
            self.task_files.append(task_file)

    def tearDown(self):
        """Clean up test fixtures"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    # =========================================================================
    # FULL SUITE EXECUTION TESTS
    # =========================================================================

    @patch("benchmark_runner.CodebaseManager")
    @patch.dict("os.environ", {"TEST_MODE": "true"})
    def test_full_suite_all_tasks_success(self, mock_cm_class):
        """Test running all 8 tasks successfully"""
        # Mock CodebaseManager
        mock_cm = Mock()
        mock_cm.create_worktree.return_value = self.temp_dir / "worktree"
        mock_cm_class.return_value = mock_cm

        all_results = []

        # Run each task
        for task_def in self.task_defs:
            runner = BenchmarkRunner(
                task_def=task_def, trials=3, output_dir=self.output_dir, verbose=False
            )

            with_popkit_recordings = runner.run_with_popkit()
            baseline_recordings = runner.run_baseline()

            # Verify recordings collected
            self.assertEqual(len(with_popkit_recordings), 3)
            self.assertEqual(len(baseline_recordings), 3)

            # Store results
            all_results.append(
                {
                    "task_id": task_def["id"],
                    "with_popkit": with_popkit_recordings,
                    "baseline": baseline_recordings,
                }
            )

        # Verify all 8 tasks completed
        self.assertEqual(len(all_results), 8)

        # Verify all task IDs present
        task_ids = [r["task_id"] for r in all_results]
        self.assertEqual(len(set(task_ids)), 8)  # All unique
        self.assertIn("jwt-authentication", task_ids)
        self.assertIn("dark-mode-implementation", task_ids)
        self.assertIn("race-condition-fix", task_ids)
        self.assertIn("memory-leak-fix", task_ids)
        self.assertIn("async-await-conversion", task_ids)
        self.assertIn("extract-shared-utilities", task_ids)
        self.assertIn("security-vulnerability-scan", task_ids)
        self.assertIn("performance-bottleneck-identification", task_ids)

    @patch("benchmark_runner.CodebaseManager")
    @patch.dict("os.environ", {"TEST_MODE": "true"})
    def test_full_suite_aggregate_analysis(self, mock_cm_class):
        """Test aggregate statistical analysis across all tasks"""
        mock_cm = Mock()
        mock_cm.create_worktree.return_value = self.temp_dir / "worktree"
        mock_cm_class.return_value = mock_cm

        all_analyses = []

        # Run and analyze each task
        for task_def in self.task_defs:
            runner = BenchmarkRunner(
                task_def=task_def, trials=3, output_dir=self.output_dir
            )

            with_popkit_recordings = runner.run_with_popkit()
            baseline_recordings = runner.run_baseline()

            analyzer = BenchmarkAnalyzer(
                with_popkit_recordings=with_popkit_recordings,
                baseline_recordings=baseline_recordings,
            )

            # Mock RecordingAnalyzer for consistent test data
            with patch("benchmark_analyzer.RecordingAnalyzer") as mock_ra:
                mock_ra_instance = Mock()
                mock_ra_instance.get_token_count.return_value = 1000
                mock_ra_instance.get_tool_usage_breakdown.return_value = {"Read": 10}
                mock_ra_instance.get_file_modifications.return_value = 2
                mock_ra_instance.get_error_summary.return_value = {
                    "failed_tool_calls": 1
                }
                mock_ra_instance.get_performance_metrics.return_value = {
                    "duration_seconds": 120
                }
                mock_ra.return_value = mock_ra_instance

                with patch("benchmark_analyzer.subprocess.run") as mock_subprocess:
                    mock_subprocess.return_value = Mock(returncode=0)
                    results = analyzer.analyze()

            all_analyses.append(results)

        # Verify all 8 analyses completed
        self.assertEqual(len(all_analyses), 8)

        # Calculate aggregate metrics
        total_tasks = len(all_analyses)
        tasks_with_improvements = sum(
            1
            for analysis in all_analyses
            if "metrics" in analysis
            and any(m.get("improvement", 0) < 0 for m in analysis["metrics"].values())
        )

        # Verify aggregate statistics
        self.assertGreater(tasks_with_improvements, 0)
        improvement_rate = tasks_with_improvements / total_tasks
        self.assertGreaterEqual(improvement_rate, 0.0)
        self.assertLessEqual(improvement_rate, 1.0)

    @patch("benchmark_runner.CodebaseManager")
    @patch.dict("os.environ", {"TEST_MODE": "true"})
    def test_full_suite_category_breakdown(self, mock_cm_class):
        """Test results breakdown by task category"""
        mock_cm = Mock()
        mock_cm.create_worktree.return_value = self.temp_dir / "worktree"
        mock_cm_class.return_value = mock_cm

        category_results = {
            "feature-addition": [],
            "bug-fix": [],
            "refactoring": [],
            "code-quality": [],
        }

        # Run all tasks and organize by category
        for task_def in self.task_defs:
            runner = BenchmarkRunner(
                task_def=task_def, trials=3, output_dir=self.output_dir
            )

            _with_popkit_recordings = runner.run_with_popkit()
            _baseline_recordings = runner.run_baseline()

            category = task_def["category"]
            category_results[category].append({"task_id": task_def["id"], "trials": 3})

        # Verify category distribution
        self.assertEqual(len(category_results["feature-addition"]), 2)
        self.assertEqual(len(category_results["bug-fix"]), 2)
        self.assertEqual(len(category_results["refactoring"]), 2)
        self.assertEqual(len(category_results["code-quality"]), 2)

    @patch("benchmark_runner.CodebaseManager")
    @patch.dict("os.environ", {"TEST_MODE": "true"})
    def test_full_suite_with_some_task_failures(self, mock_cm_class):
        """Test suite continues even if some tasks fail"""
        mock_cm = Mock()
        # Task 3 and 5 will fail
        mock_cm.create_worktree.side_effect = [
            self.temp_dir / "worktree1",  # Task 1 - Success
            self.temp_dir / "worktree2",  # Task 1 - Success
            self.temp_dir / "worktree3",  # Task 1 - Success
            self.temp_dir / "worktree4",  # Task 1 - Success
            self.temp_dir / "worktree5",  # Task 1 - Success
            self.temp_dir / "worktree6",  # Task 1 - Success
            self.temp_dir / "worktree7",  # Task 2 - Success
            self.temp_dir / "worktree8",  # Task 2 - Success
            self.temp_dir / "worktree9",  # Task 2 - Success
            self.temp_dir / "worktree10",  # Task 2 - Success
            self.temp_dir / "worktree11",  # Task 2 - Success
            self.temp_dir / "worktree12",  # Task 2 - Success
            Exception("Failure"),  # Task 3 - Fail
            Exception("Failure"),  # Task 3 - Fail
            self.temp_dir / "worktree15",  # Task 3 - Success (1 out of 3)
            self.temp_dir / "worktree16",  # Task 3 - Success
            self.temp_dir / "worktree17",  # Task 3 - Success
            self.temp_dir / "worktree18",  # Task 3 - Success
        ]
        mock_cm_class.return_value = mock_cm

        completed_tasks = 0
        failed_tasks = 0

        # Run first 3 tasks (1 will have failures but still complete)
        for i, task_def in enumerate(self.task_defs[:3]):
            try:
                runner = BenchmarkRunner(
                    task_def=task_def, trials=3, output_dir=self.output_dir
                )

                with_popkit_recordings = runner.run_with_popkit()
                baseline_recordings = runner.run_baseline()

                # Tasks 1 and 2 should have all trials
                if i < 2:
                    self.assertEqual(len(with_popkit_recordings), 3)
                    self.assertEqual(len(baseline_recordings), 3)
                # Task 3 should have 1 successful with_popkit trial
                else:
                    self.assertEqual(len(with_popkit_recordings), 1)

                completed_tasks += 1

            except Exception:
                failed_tasks += 1

        # Even with some trial failures, tasks should complete
        self.assertEqual(completed_tasks, 3)
        self.assertEqual(failed_tasks, 0)

    @patch("benchmark_runner.CodebaseManager")
    @patch.dict("os.environ", {"TEST_MODE": "true"})
    def test_full_suite_report_generation(self, mock_cm_class):
        """Test comprehensive report generation for full suite"""
        mock_cm = Mock()
        mock_cm.create_worktree.return_value = self.temp_dir / "worktree"
        mock_cm_class.return_value = mock_cm

        all_reports = []

        # Run, analyze, and generate reports for all tasks
        for task_def in self.task_defs:
            runner = BenchmarkRunner(
                task_def=task_def, trials=3, output_dir=self.output_dir
            )

            with_popkit_recordings = runner.run_with_popkit()
            baseline_recordings = runner.run_baseline()

            analyzer = BenchmarkAnalyzer(
                with_popkit_recordings=with_popkit_recordings,
                baseline_recordings=baseline_recordings,
            )

            # Mock analysis results
            with patch("benchmark_analyzer.RecordingAnalyzer") as mock_ra:
                mock_ra_instance = Mock()
                mock_ra_instance.get_token_count.return_value = 1000
                mock_ra_instance.get_tool_usage_breakdown.return_value = {"Read": 10}
                mock_ra_instance.get_file_modifications.return_value = 2
                mock_ra_instance.get_error_summary.return_value = {
                    "failed_tool_calls": 1
                }
                mock_ra_instance.get_performance_metrics.return_value = {
                    "duration_seconds": 120
                }
                mock_ra.return_value = mock_ra_instance

                with patch("benchmark_analyzer.subprocess.run") as mock_subprocess:
                    mock_subprocess.return_value = Mock(returncode=0)
                    results = analyzer.analyze()

            # Generate reports
            generator = ReportGenerator(analysis_results=results, task_def=task_def)

            markdown_report = generator.generate_markdown()
            html_report = generator.generate_html()

            all_reports.append(
                {
                    "task_id": task_def["id"],
                    "markdown": markdown_report,
                    "html": html_report,
                }
            )

        # Verify all 8 reports generated
        self.assertEqual(len(all_reports), 8)

        # Verify each report contains task information
        for report in all_reports:
            self.assertIn(report["task_id"], report["markdown"])
            self.assertIn(report["task_id"], report["html"])
            self.assertIn("<!DOCTYPE html>", report["html"])

    @patch("benchmark_runner.CodebaseManager")
    @patch.dict("os.environ", {"TEST_MODE": "true"})
    def test_full_suite_duration_estimation(self, mock_cm_class):
        """Test that suite completes within reasonable time bounds"""
        mock_cm = Mock()
        mock_cm.create_worktree.return_value = self.temp_dir / "worktree"
        mock_cm_class.return_value = mock_cm

        import time

        start_time = time.time()

        # Run first 2 tasks (sample)
        for task_def in self.task_defs[:2]:
            runner = BenchmarkRunner(
                task_def=task_def, trials=3, output_dir=self.output_dir
            )

            runner.run_with_popkit()
            runner.run_baseline()

        elapsed = time.time() - start_time

        # In TEST_MODE, 2 tasks × 6 trials should complete in < 5 seconds
        self.assertLess(elapsed, 5.0)

        # Extrapolate: 8 tasks should complete in < 20 seconds (TEST_MODE)
        estimated_full_duration = elapsed * 4
        self.assertLess(estimated_full_duration, 20.0)

    @patch("benchmark_runner.CodebaseManager")
    @patch.dict("os.environ", {"TEST_MODE": "true"})
    def test_full_suite_artifact_organization(self, mock_cm_class):
        """Test that all artifacts are properly organized"""
        mock_cm = Mock()
        mock_cm.create_worktree.return_value = self.temp_dir / "worktree"
        mock_cm_class.return_value = mock_cm

        # Run 2 tasks
        for task_def in self.task_defs[:2]:
            runner = BenchmarkRunner(
                task_def=task_def, trials=3, output_dir=self.output_dir
            )

            runner.run_with_popkit()
            runner.run_baseline()

        # Verify output directory structure
        self.assertTrue(self.output_dir.exists())

        # Count recording files (2 tasks × 6 trials = 12 files)
        recording_files = list(self.output_dir.glob("*.json"))
        self.assertEqual(len(recording_files), 12)

        # Verify file naming convention
        for recording_file in recording_files:
            data = json.loads(recording_file.read_text())
            self.assertIn("session_id", data)
            self.assertIn("events", data)

    # =========================================================================
    # SUMMARY STATISTICS TESTS
    # =========================================================================

    @patch("benchmark_runner.CodebaseManager")
    @patch.dict("os.environ", {"TEST_MODE": "true"})
    def test_full_suite_summary_statistics(self, mock_cm_class):
        """Test calculation of summary statistics across all tasks"""
        mock_cm = Mock()
        mock_cm.create_worktree.return_value = self.temp_dir / "worktree"
        mock_cm_class.return_value = mock_cm

        all_summaries = []

        # Run all tasks and collect summaries
        for task_def in self.task_defs:
            runner = BenchmarkRunner(
                task_def=task_def, trials=3, output_dir=self.output_dir
            )

            runner.run_with_popkit()
            runner.run_baseline()

            summary = runner.get_results_summary()
            all_summaries.append(summary)

        # Calculate aggregate statistics
        total_trials_requested = sum(s["trials_requested"] for s in all_summaries)
        total_with_popkit_successful = sum(
            s["with_popkit"]["successful"] for s in all_summaries
        )
        total_baseline_successful = sum(
            s["baseline"]["successful"] for s in all_summaries
        )

        # Verify aggregate metrics
        self.assertEqual(total_trials_requested, 24)  # 8 tasks × 3 trials
        self.assertEqual(total_with_popkit_successful, 24)
        self.assertEqual(total_baseline_successful, 24)

        # Calculate success rates
        with_popkit_success_rate = total_with_popkit_successful / total_trials_requested
        baseline_success_rate = total_baseline_successful / total_trials_requested

        self.assertEqual(with_popkit_success_rate, 1.0)
        self.assertEqual(baseline_success_rate, 1.0)

    @patch("benchmark_runner.CodebaseManager")
    def test_full_suite_cleanup(self, mock_cm_class):
        """Test worktree cleanup after full suite"""
        mock_cm = Mock()
        mock_cm_class.return_value = mock_cm

        # Run 2 tasks
        for task_def in self.task_defs[:2]:
            runner = BenchmarkRunner(
                task_def=task_def, trials=3, output_dir=self.output_dir
            )

            # Cleanup after each task
            runner.cleanup_all_worktrees()

        # Verify cleanup called (2 tasks)
        self.assertEqual(mock_cm.cleanup_all_worktrees.call_count, 2)


if __name__ == "__main__":
    unittest.main()
