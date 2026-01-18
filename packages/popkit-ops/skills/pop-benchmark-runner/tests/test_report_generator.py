#!/usr/bin/env python3
"""
Test suite for report_generator.py

Tests report generation (markdown and HTML).
"""

import sys
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "shared-py"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from report_generator import ReportGenerator


class TestReportGenerator(unittest.TestCase):
    """Test ReportGenerator functionality"""

    def setUp(self):
        """Set up test fixtures"""
        self.task_def = {
            "id": "test-task",
            "name": "test-task",
            "category": "test",
            "description": "Test task description",
            "estimated_duration_minutes": 15,
        }

        self.analysis_results = {
            "task_id": "test-task",
            "timestamp": "2026-01-16T12:00:00",
            "summary": {
                "trials_per_config": 3,
                "total_duration": "5m 30s",
                "overall_effect_size": 1.35,
            },
            "metrics": {
                "context_usage": {
                    "popkit_mean": 1000,
                    "baseline_mean": 1500,
                    "popkit_std": 50,
                    "baseline_std": 75,
                    "popkit_values": [950, 1000, 1050],
                    "baseline_values": [1425, 1500, 1575],
                    "improvement_pct": -33.3,
                    "p_value": 0.001,
                    "is_significant": True,
                    "effect_size": 1.5,
                    "effect_size_label": "large",
                    "confidence_interval_95": {
                        "with_popkit": [950, 1050],
                        "baseline": [1425, 1575],
                    },
                },
                "tool_calls": {
                    "popkit_mean": 20,
                    "baseline_mean": 30,
                    "popkit_std": 2,
                    "baseline_std": 3,
                    "popkit_values": [18, 20, 22],
                    "baseline_values": [27, 30, 33],
                    "improvement_pct": -33.3,
                    "p_value": 0.01,
                    "is_significant": True,
                    "effect_size": 1.2,
                    "effect_size_label": "large",
                    "confidence_interval_95": {
                        "with_popkit": [18, 22],
                        "baseline": [27, 33],
                    },
                },
            },
        }

        self.generator = ReportGenerator(
            analysis_results=self.analysis_results, task_def=self.task_def
        )

    # =========================================================================
    # INITIALIZATION TESTS
    # =========================================================================

    def test_init(self):
        """Test report generator initialization"""
        self.assertEqual(self.generator.results, self.analysis_results)
        self.assertEqual(self.generator.task_def, self.task_def)

    # =========================================================================
    # MARKDOWN GENERATION TESTS
    # =========================================================================

    def test_generate_markdown_basic(self):
        """Test basic markdown report generation"""
        markdown = self.generator.generate_markdown()

        # Verify structure
        self.assertIn("# Benchmark Results", markdown)
        self.assertIn("test-task", markdown)
        self.assertIn("## Metric", markdown)  # Matches "## Metric Improvements"

        # Verify metrics included
        self.assertIn("context_usage", markdown)
        self.assertIn("tool_calls", markdown)

        # Verify improvements shown
        self.assertIn("-33.3%", markdown)

        # Verify statistical significance
        self.assertIn("p < 0.05", markdown)
        self.assertIn("large", markdown.lower())  # Large effect size

    def test_generate_markdown_with_all_metrics(self):
        """Test markdown with all 6 metrics"""
        # Add all metrics
        all_metrics = dict(self.analysis_results)
        all_metrics["metrics"]["backtracking"] = {
            "with_popkit": {"mean": 2},
            "baseline": {"mean": 8},
            "improvement": -75.0,
            "p_value": 0.002,
        }
        all_metrics["metrics"]["error_recovery"] = {
            "with_popkit": {"mean": 1},
            "baseline": {"mean": 5},
            "improvement": -80.0,
            "p_value": 0.001,
        }
        all_metrics["metrics"]["time_to_complete"] = {
            "with_popkit": {"mean": 300},
            "baseline": {"mean": 450},
            "improvement": -33.3,
            "p_value": 0.01,
        }
        all_metrics["metrics"]["code_quality"] = {
            "with_popkit": {"mean": 100},
            "baseline": {"mean": 85},
            "improvement": 17.6,
            "p_value": 0.05,
        }

        generator = ReportGenerator(all_metrics, self.task_def)
        markdown = generator.generate_markdown()

        # Verify all metrics present
        self.assertIn("backtracking", markdown)
        self.assertIn("error_recovery", markdown)
        self.assertIn("time_to_complete", markdown)
        self.assertIn("code_quality", markdown)

    def test_generate_markdown_no_metrics(self):
        """Test markdown with no metrics"""
        empty_results = {
            "task_id": "test-task",
            "timestamp": "2026-01-16T12:00:00",
            "metrics": {},
        }

        generator = ReportGenerator(empty_results, self.task_def)
        markdown = generator.generate_markdown()

        # Should not crash and contain task info
        self.assertIn("test-task", markdown)
        # With no metrics, the metrics table is empty but report still renders
        self.assertIn("Benchmark Results", markdown)

    # =========================================================================
    # HTML GENERATION TESTS
    # =========================================================================

    def test_generate_html_basic(self):
        """Test basic HTML report generation"""
        html = self.generator.generate_html()

        # Verify HTML structure
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("<html", html)  # May have lang attribute
        self.assertIn("<head>", html)
        self.assertIn("<body>", html)
        self.assertIn("</html>", html)

        # Verify content
        self.assertIn("test-task", html)
        self.assertIn("context_usage", html)
        self.assertIn("tool_calls", html)

    def test_generate_html_includes_charts(self):
        """Test HTML includes Chart.js visualizations"""
        html = self.generator.generate_html()

        # Verify Chart.js included
        self.assertIn("chart", html.lower())
        self.assertIn("canvas", html.lower())

    def test_generate_html_responsive(self):
        """Test HTML includes responsive meta tag"""
        html = self.generator.generate_html()

        # Verify responsive design
        self.assertIn("viewport", html)
        self.assertIn("width=device-width", html)

    # =========================================================================
    # FORMAT METRIC TESTS
    # =========================================================================

    def test_format_metric_tokens(self):
        """Test formatting token counts"""
        formatted = self.generator._format_metric(1500, "context_usage")

        self.assertIn("1,500", formatted)  # Comma-separated
        self.assertIn("token", formatted.lower())

    def test_format_metric_percentage(self):
        """Test formatting percentages"""
        formatted = self.generator._format_metric(85.5, "code_quality")

        self.assertIn("85.5", formatted)
        self.assertIn("%", formatted)

    def test_format_metric_count(self):
        """Test formatting counts"""
        formatted = self.generator._format_metric(25, "tool_calls")

        # Default format is numeric with 2 decimal places
        self.assertEqual(formatted, "25.00")

    def test_format_metric_time(self):
        """Test formatting time values"""
        formatted = self.generator._format_metric(125.5, "time_to_complete")

        # Time < 3600 is formatted as minutes
        self.assertIn("2.1m", formatted)

    def test_format_metric_negative_improvement(self):
        """Test formatting negative improvements (good for most metrics)"""
        # _format_metric doesn't add +/- signs, it just formats values
        # This test should use the percentage metric type
        formatted = self.generator._format_metric(33.3, "improvement_%")

        self.assertIn("33.3%", formatted)

    def test_format_metric_positive_improvement(self):
        """Test formatting positive improvements (good for code_quality)"""
        # _format_metric doesn't add +/- signs, it just formats values
        formatted = self.generator._format_metric(15.5, "rate")

        self.assertIn("15.5%", formatted)

    # =========================================================================
    # EFFECT SIZE INTERPRETATION TESTS
    # =========================================================================

    def test_interpret_effect_size_large(self):
        """Test large effect size interpretation"""
        interpretation = self.generator._interpret_effect_size(1.5)

        self.assertEqual(interpretation, "large")

    def test_interpret_effect_size_medium(self):
        """Test medium effect size interpretation"""
        interpretation = self.generator._interpret_effect_size(0.6)

        self.assertEqual(interpretation, "medium")

    def test_interpret_effect_size_small(self):
        """Test small effect size interpretation"""
        interpretation = self.generator._interpret_effect_size(0.3)

        self.assertEqual(interpretation, "small")

    def test_interpret_effect_size_negligible(self):
        """Test negligible effect size interpretation"""
        interpretation = self.generator._interpret_effect_size(0.1)

        self.assertEqual(interpretation, "negligible")

    def test_interpret_effect_size_boundary_large(self):
        """Test boundary case for large effect (exactly 0.8)"""
        interpretation = self.generator._interpret_effect_size(0.8)

        self.assertEqual(interpretation, "large")

    def test_interpret_effect_size_boundary_medium(self):
        """Test boundary case for medium effect (exactly 0.5)"""
        interpretation = self.generator._interpret_effect_size(0.5)

        self.assertEqual(interpretation, "medium")

    def test_interpret_effect_size_boundary_small(self):
        """Test boundary case for small effect (exactly 0.2)"""
        interpretation = self.generator._interpret_effect_size(0.2)

        self.assertEqual(interpretation, "small")

    def test_interpret_effect_size_negative(self):
        """Test negative effect sizes (absolute value used)"""
        interpretation = self.generator._interpret_effect_size(-1.2)

        self.assertEqual(interpretation, "large")  # abs(-1.2) = 1.2

    # =========================================================================
    # INTEGRATION TESTS
    # =========================================================================

    def test_generate_both_formats(self):
        """Test generating both markdown and HTML"""
        markdown = self.generator.generate_markdown()
        html = self.generator.generate_html()

        # Both should contain task info
        self.assertIn("test-task", markdown)
        self.assertIn("test-task", html)

        # Both should be valid format
        self.assertIn("#", markdown)  # Markdown headers
        self.assertIn("<", html)  # HTML tags

    def test_output_consistency(self):
        """Test that markdown and HTML show consistent data"""
        markdown = self.generator.generate_markdown()
        html = self.generator.generate_html()

        # Same improvement percentages in both
        self.assertIn("-33.3%", markdown)
        self.assertIn("-33.3", html)

        # Same metrics in both
        self.assertIn("context_usage", markdown.lower())
        self.assertIn("context_usage", html.lower())


if __name__ == "__main__":
    unittest.main()
