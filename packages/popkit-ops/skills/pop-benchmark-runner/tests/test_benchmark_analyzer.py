#!/usr/bin/env python3
"""
Test suite for benchmark_analyzer.py

Tests statistical analysis of benchmark results.
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared-py"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from benchmark_analyzer import BenchmarkAnalyzer, generate_summary_report


class TestBenchmarkAnalyzer(unittest.TestCase):
    """Test BenchmarkAnalyzer statistical methods"""

    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = Path(tempfile.mkdtemp())

        # Create mock recordings
        self.with_popkit_recordings = self._create_mock_recordings("with_popkit", 3)
        self.baseline_recordings = self._create_mock_recordings("baseline", 3)

        self.analyzer = BenchmarkAnalyzer(
            with_popkit_recordings=self.with_popkit_recordings,
            baseline_recordings=self.baseline_recordings,
        )

    def tearDown(self):
        """Clean up test fixtures"""
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def _create_mock_recordings(self, prefix: str, count: int) -> list:
        """Create mock recording files"""
        recordings = []
        for i in range(count):
            path = self.temp_dir / f"{prefix}_{i}.json"
            data = {
                "session_id": f"{prefix}-session-{i}",
                "events": [
                    {"type": "tool_use", "tool": "Read"},
                    {"type": "tool_result", "status": "success"},
                ],
                "metadata": {
                    "tokens": 1000 + (i * 100),
                    "duration_seconds": 60 + (i * 10),
                },
            }
            path.write_text(json.dumps(data))
            recordings.append(path)
        return recordings

    # =========================================================================
    # INITIALIZATION TESTS
    # =========================================================================

    def test_init(self):
        """Test analyzer initialization"""
        self.assertEqual(len(self.analyzer.with_popkit_recordings), 3)
        self.assertEqual(len(self.analyzer.baseline_recordings), 3)

    # =========================================================================
    # ANALYSIS TESTS
    # =========================================================================

    @patch.object(BenchmarkAnalyzer, "_extract_metrics")
    @patch.object(BenchmarkAnalyzer, "_calculate_statistics")
    def test_analyze(self, mock_calc_stats, mock_extract):
        """Test main analyze method"""
        # Mock metric extraction - need all 6 metrics
        with_popkit_metrics = {
            "context_usage": [100, 110, 120],
            "tool_calls": [10, 12, 14],
            "backtracking": [2, 3, 2],
            "error_recovery": [1, 1, 2],
            "time_to_complete": [60, 65, 70],
            "code_quality": [100, 100, 100],
        }
        baseline_metrics = {
            "context_usage": [150, 160, 170],
            "tool_calls": [20, 22, 24],
            "backtracking": [5, 6, 5],
            "error_recovery": [3, 4, 3],
            "time_to_complete": [90, 95, 100],
            "code_quality": [90, 85, 90],
        }
        mock_extract.side_effect = [with_popkit_metrics, baseline_metrics]

        # Mock statistics calculation
        mock_calc_stats.return_value = {
            "p_value": 0.01,
            "is_significant": True,
            "effect_size": 1.5,
            "effect_size_label": "large",
            "ci_with_popkit": (90, 130),
            "ci_baseline": (140, 180),
        }

        results = self.analyzer.analyze()

        # Verify structure
        self.assertIn("metrics", results)
        self.assertIn("summary", results)

        # Verify both extractions called
        self.assertEqual(mock_extract.call_count, 2)

        # Verify statistics calculated
        mock_calc_stats.assert_called()

    # =========================================================================
    # METRIC EXTRACTION TESTS
    # =========================================================================

    @patch("benchmark_analyzer.RecordingAnalyzer")
    def test_extract_metrics(self, mock_analyzer_class):
        """Test metric extraction from recordings"""
        # Mock RecordingAnalyzer
        mock_analyzer = Mock()
        mock_analyzer_class.return_value = mock_analyzer

        # Mock metric values
        with patch.object(self.analyzer, "_extract_context_usage", return_value=100.0):
            with patch.object(self.analyzer, "_extract_tool_calls", return_value=20.0):
                with patch.object(self.analyzer, "_extract_backtracking", return_value=2.0):
                    with patch.object(self.analyzer, "_extract_error_recovery", return_value=1.0):
                        with patch.object(
                            self.analyzer,
                            "_extract_time_to_complete",
                            return_value=60.0,
                        ):
                            with patch.object(
                                self.analyzer,
                                "_extract_code_quality",
                                return_value=100.0,
                            ):
                                metrics = self.analyzer._extract_metrics(
                                    self.with_popkit_recordings
                                )

        # Verify all metrics extracted
        self.assertIn("context_usage", metrics)
        self.assertIn("tool_calls", metrics)
        self.assertIn("backtracking", metrics)
        self.assertIn("error_recovery", metrics)
        self.assertIn("time_to_complete", metrics)
        self.assertIn("code_quality", metrics)

        # Verify correct counts
        self.assertEqual(len(metrics["context_usage"]), 3)

    # =========================================================================
    # STATISTICS CALCULATION TESTS
    # =========================================================================

    def test_calculate_statistics_significant_difference(self):
        """Test statistics calculation with significant difference"""
        # Clearly different groups
        with_popkit = np.array([100, 110, 120])
        baseline = np.array([200, 210, 220])

        stats = self.analyzer._calculate_statistics(with_popkit, baseline)

        # Should show significant difference
        self.assertLess(stats["p_value"], 0.05)
        self.assertGreater(abs(stats["effect_size"]), 0.8)  # Large effect
        self.assertIn("ci_with_popkit", stats)
        self.assertIn("ci_baseline", stats)

    def test_calculate_statistics_no_difference(self):
        """Test statistics calculation with no difference"""
        # Identical groups
        with_popkit = np.array([100, 100, 100])
        baseline = np.array([100, 100, 100])

        stats = self.analyzer._calculate_statistics(with_popkit, baseline)

        # Should show no significant difference (p_value will be NaN for identical groups)
        self.assertTrue(np.isnan(stats["p_value"]) or stats["p_value"] == 1.0)
        self.assertEqual(stats["effect_size"], 0.0)

    def test_calculate_statistics_small_sample(self):
        """Test statistics with small sample sizes"""
        with_popkit = np.array([100])
        baseline = np.array([150])

        stats = self.analyzer._calculate_statistics(with_popkit, baseline)

        # Should handle small samples gracefully
        self.assertIsNotNone(stats["p_value"])
        self.assertIsNotNone(stats["effect_size"])

    def test_calculate_statistics_zero_variance(self):
        """Test statistics with zero variance"""
        # All identical values
        with_popkit = np.array([100, 100, 100])
        baseline = np.array([150, 150, 150])

        stats = self.analyzer._calculate_statistics(with_popkit, baseline)

        # Should handle zero variance
        self.assertIsNotNone(stats["p_value"])
        self.assertIsNotNone(stats["effect_size"])

    # =========================================================================
    # COHEN'S D TESTS
    # =========================================================================

    def test_cohens_d_large_effect(self):
        """Test Cohen's d with large effect size"""
        group1 = np.array([100, 110, 120])
        group2 = np.array([200, 210, 220])

        d = self.analyzer._cohens_d(group1, group2)

        # Large effect (> 0.8)
        self.assertGreater(abs(d), 0.8)

    def test_cohens_d_medium_effect(self):
        """Test Cohen's d with medium effect size"""
        group1 = np.array([100, 110, 120])
        # For d≈0.6 (medium): mean2 = 110 + 0.6*10 = 116
        group2 = np.array([106, 116, 126])

        d = self.analyzer._cohens_d(group1, group2)

        # Medium effect (0.5 - 0.8)
        self.assertGreater(abs(d), 0.5)
        self.assertLess(abs(d), 0.8)

    def test_cohens_d_small_effect(self):
        """Test Cohen's d with small effect size"""
        group1 = np.array([100, 110, 120])
        # For d≈0.3 (small): mean2 = 110 + 0.3*10 = 113
        group2 = np.array([103, 113, 123])

        d = self.analyzer._cohens_d(group1, group2)

        # Small effect (< 0.5)
        self.assertLess(abs(d), 0.5)

    def test_cohens_d_identical_groups(self):
        """Test Cohen's d with identical groups"""
        group1 = np.array([100, 110, 120])
        group2 = np.array([100, 110, 120])

        d = self.analyzer._cohens_d(group1, group2)

        self.assertEqual(d, 0.0)

    def test_cohens_d_zero_pooled_std(self):
        """Test Cohen's d with zero pooled standard deviation"""
        group1 = np.array([100, 100, 100])
        group2 = np.array([100, 100, 100])

        d = self.analyzer._cohens_d(group1, group2)

        # Should return 0 when pooled std is 0
        self.assertEqual(d, 0.0)

    # =========================================================================
    # CONFIDENCE INTERVAL TESTS
    # =========================================================================

    def test_confidence_interval_basic(self):
        """Test confidence interval calculation"""
        data = np.array([100, 110, 120, 130, 140])

        ci_lower, ci_upper = self.analyzer._confidence_interval(data)

        # CI should contain the mean
        mean = np.mean(data)
        self.assertLess(ci_lower, mean)
        self.assertGreater(ci_upper, mean)

        # CI should be reasonable width
        ci_width = ci_upper - ci_lower
        self.assertGreater(ci_width, 0)

    def test_confidence_interval_single_value(self):
        """Test confidence interval with single value"""
        data = np.array([100])

        ci_lower, ci_upper = self.analyzer._confidence_interval(data)

        # CI should equal the value (no variance)
        self.assertEqual(ci_lower, 100)
        self.assertEqual(ci_upper, 100)

    def test_confidence_interval_large_variance(self):
        """Test confidence interval with large variance"""
        data = np.array([10, 50, 90, 130, 170])

        ci_lower, ci_upper = self.analyzer._confidence_interval(data)

        # Wide CI expected
        ci_width = ci_upper - ci_lower
        self.assertGreater(ci_width, 50)

    def test_confidence_interval_small_variance(self):
        """Test confidence interval with small variance"""
        data = np.array([100, 101, 102, 99, 98])

        ci_lower, ci_upper = self.analyzer._confidence_interval(data)

        # Narrow CI expected
        ci_width = ci_upper - ci_lower
        self.assertLess(ci_width, 10)

    # =========================================================================
    # METRIC-SPECIFIC EXTRACTION TESTS
    # =========================================================================

    @patch("benchmark_analyzer.RecordingAnalyzer")
    def test_extract_context_usage(self, mock_analyzer_class):
        """Test context usage extraction"""
        mock_analyzer = Mock()
        # Mock get_tool_usage_breakdown to return structure with calls
        mock_analyzer.get_tool_usage_breakdown.return_value = {
            "Read": {
                "count": 2,
                "calls": [
                    {"input": "a" * 1000, "output": "b" * 1000},  # 2000 chars
                    {"input": "c" * 1000, "output": "d" * 1000},  # 2000 chars
                ],
            }
        }
        mock_analyzer_class.return_value = mock_analyzer

        recording_path = self.with_popkit_recordings[0]

        tokens = self.analyzer._extract_context_usage(recording_path, mock_analyzer)

        # Total chars = 4000, tokens ~= 4000 / 4 = 1000
        self.assertEqual(tokens, 1000)

    @patch("benchmark_analyzer.RecordingAnalyzer")
    def test_extract_tool_calls(self, mock_analyzer_class):
        """Test tool calls extraction"""
        mock_analyzer = Mock()
        # Match real RecordingAnalyzer structure: {"Tool": {"count": N, ...}, ...}
        mock_analyzer.get_tool_usage_breakdown.return_value = {
            "Read": {"count": 10, "total_duration_ms": 0, "errors": 0, "calls": []},
            "Write": {"count": 5, "total_duration_ms": 0, "errors": 0, "calls": []},
            "Edit": {"count": 3, "total_duration_ms": 0, "errors": 0, "calls": []},
        }

        tool_count = self.analyzer._extract_tool_calls(mock_analyzer)

        self.assertEqual(tool_count, 18)  # 10 + 5 + 3

    @patch("benchmark_analyzer.RecordingAnalyzer")
    def test_extract_backtracking(self, mock_analyzer_class):
        """Test backtracking extraction"""
        mock_analyzer = Mock()
        # Mock events with file edits (same file edited multiple times = backtracking)
        mock_analyzer.events = [
            {"type": "tool_call", "tool": "Edit", "file_path": "test.py"},
            {"type": "tool_call", "tool": "Edit", "file_path": "test.py"},  # backtrack
            {"type": "tool_call", "tool": "Write", "file_path": "other.py"},
            {"type": "tool_call", "tool": "Edit", "file_path": "test.py"},  # backtrack
        ]

        backtrack_count = self.analyzer._extract_backtracking(mock_analyzer)

        # test.py edited 3 times = 2 backtracks (edits after first)
        self.assertEqual(backtrack_count, 2)

    @patch("benchmark_analyzer.RecordingAnalyzer")
    def test_extract_error_recovery(self, mock_analyzer_class):
        """Test error recovery extraction"""
        mock_analyzer = Mock()
        # Match real RecordingAnalyzer structure: {"total_errors": N, "error_rate": ..., ...}
        mock_analyzer.get_error_summary.return_value = {
            "total_errors": 3,
            "error_rate": 0.15,
            "error_types": {},
            "errors": [],
        }

        error_count = self.analyzer._extract_error_recovery(mock_analyzer)

        self.assertEqual(error_count, 3)

    @patch("benchmark_analyzer.RecordingAnalyzer")
    def test_extract_time_to_complete(self, mock_analyzer_class):
        """Test time extraction"""
        mock_analyzer = Mock()
        # Match real RecordingAnalyzer structure: {"total_duration_ms": N, ...}
        # Test expects 120.5 seconds, so provide 120500 milliseconds
        mock_analyzer.get_performance_metrics.return_value = {
            "total_tool_calls": 10,
            "total_duration_ms": 120500,
            "avg_duration_ms": 12050,
            "min_duration_ms": 100,
            "max_duration_ms": 20000,
            "session_start": None,
            "session_end": None,
        }

        duration = self.analyzer._extract_time_to_complete(mock_analyzer)

        self.assertEqual(duration, 120.5)

    def test_extract_code_quality(self):
        """Test code quality extraction"""
        recording_path = self.with_popkit_recordings[0]

        # Mock verification command results
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(returncode=0)  # All tests pass

            quality_score = self.analyzer._extract_code_quality(recording_path)

            # Returns 1.0 for perfect score (0.0-1.0 range, not 0-100)
            self.assertEqual(quality_score, 1.0)

    def test_extract_code_quality_failures(self):
        """Test code quality with failed verifications"""
        recording_path = self.with_popkit_recordings[0]

        with patch("subprocess.run") as mock_run:
            # 2 pass, 1 fail
            mock_run.side_effect = [
                Mock(returncode=0),
                Mock(returncode=1),
                Mock(returncode=0),
            ]

            quality_score = self.analyzer._extract_code_quality(recording_path)

            # Should be 0.667 (2 out of 3 pass, 0.0-1.0 range)
            self.assertAlmostEqual(quality_score, 0.667, places=2)

    # =========================================================================
    # SUMMARY REPORT TESTS
    # =========================================================================

    def test_generate_summary_report(self):
        """Test summary report generation"""
        results = {
            "metrics": {
                "context_usage": {
                    "with_popkit": {
                        "mean": 1000,
                        "std": 50,
                        "values": [950, 1000, 1050],
                    },
                    "baseline": {"mean": 1500, "std": 75, "values": [1425, 1500, 1575]},
                    "improvement_pct": -33.3,
                    "p_value": 0.001,
                    "is_significant": True,
                    "effect_size": 1.5,
                    "effect_size_label": "large",
                    "confidence_interval_95": {
                        "with_popkit": [950, 1050],
                        "baseline": [1425, 1575],
                    },
                }
            },
            "summary": {
                "total_metrics": 1,
                "significant_metrics": 1,
                "large_effect_metrics": 1,
                "with_popkit_trials": 3,
                "baseline_trials": 3,
                "overall_effect_size": 1.5,
            },
        }

        report = generate_summary_report(results)

        # Verify report contains key information
        self.assertIn("test-task", report)
        self.assertIn("Context Usage", report)  # Title cased in report
        self.assertIn("-33.3%", report)
        self.assertIn("p < 0.05", report)  # Significant
        self.assertIn("large", report.lower())  # Large effect

    def test_generate_summary_report_empty_results(self):
        """Test summary report with minimal results"""
        results = {
            "metrics": {},
            "summary": {
                "total_metrics": 0,
                "significant_metrics": 0,
                "large_effect_metrics": 0,
                "with_popkit_trials": 0,
                "baseline_trials": 0,
                "overall_effect_size": 0.0,
            },
        }

        report = generate_summary_report(results)

        # Should not crash
        self.assertIn("test-task", report)


if __name__ == "__main__":
    unittest.main()
