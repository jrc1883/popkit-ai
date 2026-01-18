#!/usr/bin/env python3
"""
Benchmark Analyzer - Statistical analysis for benchmark results.

Compares PopKit-enabled vs baseline Claude Code sessions across 6 metrics:
1. Context Usage (tokens)
2. Tool Calls
3. Backtracking (file edit reverts)
4. Error Recovery
5. Time to Complete
6. Code Quality (verification pass rate)

Calculates t-tests, Cohen's d effect sizes, and confidence intervals.

Usage:
    from benchmark_analyzer import BenchmarkAnalyzer, generate_summary_report
    from pathlib import Path

    # Collect recording file paths
    with_popkit_recordings = [
        Path("recordings/with-popkit-trial-1.json"),
        Path("recordings/with-popkit-trial-2.json"),
        Path("recordings/with-popkit-trial-3.json"),
    ]
    baseline_recordings = [
        Path("recordings/baseline-trial-1.json"),
        Path("recordings/baseline-trial-2.json"),
        Path("recordings/baseline-trial-3.json"),
    ]

    # Optional: verification results (code quality metric)
    verification_results = {
        "with_popkit": [True, True, True],  # All trials passed
        "baseline": [True, False, True],    # One trial failed
    }

    # Run analysis
    analyzer = BenchmarkAnalyzer(
        with_popkit_recordings,
        baseline_recordings,
        verification_results
    )
    results = analyzer.analyze()

    # Generate report
    report = generate_summary_report(results)
    print(report)

    # Access specific metrics
    context_usage = results["metrics"]["context_usage"]
    print(f"Context usage improvement: {context_usage['improvement_pct']:.1f}%")
    print(f"Effect size: {context_usage['effect_size']:.2f} ({context_usage['effect_size_label']})")
"""

import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy import stats

# Import RecordingAnalyzer for metrics extraction
try:
    from popkit_shared.utils.recording_analyzer import RecordingAnalyzer

    HAS_RECORDING_ANALYZER = True
except ImportError:
    HAS_RECORDING_ANALYZER = False
    RecordingAnalyzer = None  # For type checking


class BenchmarkAnalyzer:
    """Analyzes benchmark recordings and calculates statistics."""

    def __init__(
        self,
        with_popkit_recordings: List[Path],
        baseline_recordings: List[Path],
        verification_results: Optional[Dict[str, List[bool]]] = None,
    ):
        """Initialize analyzer.

        Args:
            with_popkit_recordings: List of recording file paths (with PopKit)
            baseline_recordings: List of recording file paths (baseline)
            verification_results: Optional dict with {"with_popkit": [bool], "baseline": [bool]}
        """
        self.with_popkit_recordings = [Path(p) for p in with_popkit_recordings]
        self.baseline_recordings = [Path(p) for p in baseline_recordings]
        self.verification_results = verification_results or {}

        # Validate inputs
        if not self.with_popkit_recordings:
            raise ValueError("No with_popkit recordings provided")
        if not self.baseline_recordings:
            raise ValueError("No baseline recordings provided")

        # Import here to avoid circular dependencies
        try:
            sys.path.insert(
                0, str(Path(__file__).parent.parent.parent.parent.parent / "shared-py")
            )
            from popkit_shared.utils.recording_analyzer import RecordingAnalyzer

            self.RecordingAnalyzer = RecordingAnalyzer
        except ImportError as e:
            raise ImportError(f"Failed to import RecordingAnalyzer: {e}")

    def analyze(self) -> Dict[str, Any]:
        """Run full analysis and return results.

        Returns:
            Dictionary with metrics, statistics, and summary
        """
        print("[INFO] Extracting metrics from recordings...")

        # Extract metrics from both configurations
        with_popkit_metrics = self._extract_metrics(self.with_popkit_recordings)
        baseline_metrics = self._extract_metrics(self.baseline_recordings)

        print("[INFO] Calculating statistics...")

        # Calculate statistics for each metric
        results = {"metrics": {}, "summary": {}}

        metric_names = [
            "context_usage",
            "tool_calls",
            "backtracking",
            "error_recovery",
            "time_to_complete",
            "code_quality",
        ]

        significant_count = 0
        large_effect_count = 0
        effect_sizes = []

        for metric in metric_names:
            with_popkit_values = with_popkit_metrics[metric]
            baseline_values = baseline_metrics[metric]

            # Calculate statistics
            stats_result = self._calculate_statistics(
                with_popkit_values, baseline_values
            )

            # Calculate improvement percentage
            if np.mean(baseline_values) != 0:
                improvement_pct = (
                    (np.mean(with_popkit_values) - np.mean(baseline_values))
                    / np.mean(baseline_values)
                ) * 100
            else:
                improvement_pct = 0.0

            # Store results (convert numpy types to native Python)
            results["metrics"][metric] = {
                "with_popkit": {
                    "mean": float(np.mean(with_popkit_values)),
                    "std": float(np.std(with_popkit_values, ddof=1)),
                    "values": [float(v) for v in with_popkit_values],
                },
                "baseline": {
                    "mean": float(np.mean(baseline_values)),
                    "std": float(np.std(baseline_values, ddof=1)),
                    "values": [float(v) for v in baseline_values],
                },
                "improvement_pct": float(improvement_pct),
                "p_value": float(stats_result["p_value"])
                if not np.isnan(stats_result["p_value"])
                else None,
                "is_significant": bool(stats_result["is_significant"]),
                "effect_size": float(stats_result["effect_size"]),
                "effect_size_label": stats_result["effect_size_label"],
                "confidence_interval_95": {
                    "with_popkit": [float(x) for x in stats_result["ci_with_popkit"]],
                    "baseline": [float(x) for x in stats_result["ci_baseline"]],
                },
            }

            # Track summary statistics
            if bool(stats_result["is_significant"]):
                significant_count += 1
            if float(stats_result["effect_size"]) >= 0.8:
                large_effect_count += 1
            effect_sizes.append(float(stats_result["effect_size"]))

        # Calculate overall summary
        results["summary"] = {
            "total_metrics": len(metric_names),
            "significant_metrics": significant_count,
            "large_effect_metrics": large_effect_count,
            "overall_effect_size": float(np.mean(effect_sizes)),
            "with_popkit_trials": len(self.with_popkit_recordings),
            "baseline_trials": len(self.baseline_recordings),
        }

        return results

    def _extract_metrics(self, recordings: List[Path]) -> Dict[str, List[float]]:
        """Extract all 6 metrics from recordings.

        Args:
            recordings: List of recording file paths

        Returns:
            Dictionary with metric name -> list of values
        """
        metrics = defaultdict(list)

        for recording_path in recordings:
            try:
                analyzer = self.RecordingAnalyzer(recording_path)

                # Metric 1: Context Usage (tokens)
                context_usage = self._extract_context_usage(recording_path, analyzer)
                metrics["context_usage"].append(context_usage)

                # Metric 2: Tool Calls
                tool_calls = self._extract_tool_calls(analyzer)
                metrics["tool_calls"].append(tool_calls)

                # Metric 3: Backtracking (files edited multiple times)
                backtracking = self._extract_backtracking(analyzer)
                metrics["backtracking"].append(backtracking)

                # Metric 4: Error Recovery (error count)
                error_recovery = self._extract_error_recovery(analyzer)
                metrics["error_recovery"].append(error_recovery)

                # Metric 5: Time to Complete (milliseconds)
                time_to_complete = self._extract_time_to_complete(analyzer)
                metrics["time_to_complete"].append(time_to_complete)

                # Metric 6: Code Quality (verification pass rate)
                code_quality = self._extract_code_quality(recording_path)
                metrics["code_quality"].append(code_quality)

            except Exception as e:
                print(
                    f"[WARN] Failed to extract metrics from {recording_path.name}: {e}"
                )
                continue

        # Validate we got at least some data
        if not metrics["context_usage"]:
            raise ValueError("Failed to extract any metrics from recordings")

        return dict(metrics)

    def _extract_context_usage(self, recording_path: Path, analyzer: Any) -> float:
        """Extract context usage (total tokens).

        Uses rough estimation: sum of all tool call result characters / 4.
        More accurate than counting events, less accurate than API billing.
        """
        tool_usage = analyzer.get_tool_usage_breakdown()

        total_chars = 0
        for tool, data in tool_usage.items():
            # Estimate characters from tool calls
            for call in data.get("calls", []):
                # Count input + output characters
                if "input" in call:
                    total_chars += len(str(call["input"]))
                if "output" in call:
                    total_chars += len(str(call["output"]))

        # Convert to tokens (rough: 4 chars per token)
        tokens = total_chars / 4
        return tokens

    def _extract_tool_calls(self, analyzer: Any) -> float:
        """Extract total tool calls count."""
        tool_usage = analyzer.get_tool_usage_breakdown()
        total_calls = sum(data["count"] for data in tool_usage.values())
        return float(total_calls)

    def _extract_backtracking(self, analyzer: Any) -> float:
        """Extract backtracking count (files edited multiple times).

        Analyzes tool calls to find files that were edited/written multiple times.
        """
        file_edits = defaultdict(int)

        for event in analyzer.events:
            if event.get("type") != "tool_call":
                continue

            tool_name = event.get("tool_name", "")
            if tool_name not in ["Write", "Edit"]:
                continue

            # Extract file path from input
            input_data = event.get("input", {})
            if isinstance(input_data, dict):
                file_path = input_data.get("file_path")
            else:
                # Try to parse from string input
                try:
                    input_dict = json.loads(str(input_data))
                    file_path = input_dict.get("file_path")
                except Exception:
                    file_path = None

            if file_path:
                file_edits[file_path] += 1

        # Count files edited more than once
        backtracking_count = sum(1 for count in file_edits.values() if count > 1)
        return float(backtracking_count)

    def _extract_error_recovery(self, analyzer: Any) -> float:
        """Extract error recovery metric (total errors encountered)."""
        error_summary = analyzer.get_error_summary()
        return float(error_summary["total_errors"])

    def _extract_time_to_complete(self, analyzer: Any) -> float:
        """Extract time to complete (milliseconds)."""
        performance = analyzer.get_performance_metrics()
        return float(performance.get("total_duration_ms", 0))

    def _extract_code_quality(self, recording_path: Path) -> float:
        """Extract code quality metric (verification pass rate).

        Args:
            recording_path: Path to recording file

        Returns:
            Pass rate (0.0 to 1.0)
        """
        # Check if we have pre-computed verification results
        recording_name = recording_path.name

        # Determine configuration from path or filename
        if "with-popkit" in str(recording_path).lower():
            config = "with_popkit"
        elif "baseline" in str(recording_path).lower():
            config = "baseline"
        else:
            # Default to checking both
            config = None

        if config and config in self.verification_results:
            results = self.verification_results[config]
            if results:
                # Get result for this trial (by index)
                trial_idx = len(
                    [
                        p
                        for p in recording_path.parent.glob("*.json")
                        if p < recording_path
                    ]
                )
                if trial_idx < len(results):
                    return 1.0 if results[trial_idx] else 0.0

        # Default to 1.0 (assume passing if no verification data)
        return 1.0

    def _calculate_statistics(
        self, with_popkit_values: List[float], baseline_values: List[float]
    ) -> Dict[str, Any]:
        """Calculate t-test, Cohen's d, and confidence intervals.

        Args:
            with_popkit_values: Metric values from with-PopKit trials
            baseline_values: Metric values from baseline trials

        Returns:
            Dictionary with p_value, effect_size, confidence intervals
        """
        # Convert to numpy arrays
        with_popkit = np.array(with_popkit_values)
        baseline = np.array(baseline_values)

        # Independent samples t-test
        try:
            t_statistic, p_value = stats.ttest_ind(with_popkit, baseline)
        except Exception:
            # Handle edge cases (e.g., identical values)
            t_statistic = 0.0
            p_value = np.nan

        # Cohen's d effect size
        effect_size = self._cohens_d(with_popkit, baseline)

        # Effect size label
        if effect_size < 0.2:
            effect_label = "negligible"
        elif effect_size < 0.5:
            effect_label = "small"
        elif effect_size < 0.8:
            effect_label = "medium"
        else:
            effect_label = "large"

        # 95% confidence intervals
        ci_with_popkit = self._confidence_interval(with_popkit, confidence=0.95)
        ci_baseline = self._confidence_interval(baseline, confidence=0.95)

        # Determine significance (handle NaN)
        is_significant = not np.isnan(p_value) and p_value < 0.05

        return {
            "p_value": p_value,
            "is_significant": is_significant,
            "effect_size": effect_size,
            "effect_size_label": effect_label,
            "ci_with_popkit": ci_with_popkit,
            "ci_baseline": ci_baseline,
        }

    @staticmethod
    def _cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
        """Calculate Cohen's d effect size.

        Formula: d = (mean1 - mean2) / pooled_std

        Args:
            group1: First group values
            group2: Second group values

        Returns:
            Effect size (absolute value)
        """
        mean1, mean2 = np.mean(group1), np.mean(group2)
        std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)

        # Pooled standard deviation
        n1, n2 = len(group1), len(group2)
        pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))

        # Avoid division by zero
        if pooled_std == 0:
            return 0.0

        # Effect size (absolute value)
        d = abs((mean1 - mean2) / pooled_std)
        return d

    @staticmethod
    def _confidence_interval(
        data: np.ndarray, confidence: float = 0.95
    ) -> Tuple[float, float]:
        """Calculate confidence interval for mean.

        Formula: mean ± (SEM × t_critical)

        Args:
            data: Data values
            confidence: Confidence level (default 0.95 for 95%)

        Returns:
            Tuple of (lower_bound, upper_bound)
        """
        mean = np.mean(data)
        sem = stats.sem(data)  # Standard error of mean
        t_critical = stats.t.ppf((1 + confidence) / 2, len(data) - 1)
        margin_of_error = sem * t_critical

        return (mean - margin_of_error, mean + margin_of_error)


def generate_summary_report(results: Dict[str, Any]) -> str:
    """Generate human-readable summary report.

    Args:
        results: Analysis results from BenchmarkAnalyzer.analyze()

    Returns:
        Formatted markdown summary
    """
    lines = []
    lines.append("# Benchmark Analysis Summary")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    summary = results["summary"]
    lines.append(
        f"- **Trials**: {summary['with_popkit_trials']} with PopKit, {summary['baseline_trials']} baseline"
    )
    lines.append(
        f"- **Significant Metrics**: {summary['significant_metrics']}/{summary['total_metrics']}"
    )
    lines.append(
        f"- **Large Effect Metrics**: {summary['large_effect_metrics']}/{summary['total_metrics']}"
    )
    lines.append(f"- **Overall Effect Size**: {summary['overall_effect_size']:.2f}")
    lines.append("")

    lines.append("## Metrics Comparison")
    lines.append("")
    lines.append(
        "| Metric | With PopKit | Baseline | Improvement | p-value | Effect Size |"
    )
    lines.append(
        "|--------|-------------|----------|-------------|---------|-------------|"
    )

    metrics = results["metrics"]
    for metric_name, data in metrics.items():
        metric_label = metric_name.replace("_", " ").title()
        with_popkit_mean = data["with_popkit"]["mean"]
        baseline_mean = data["baseline"]["mean"]
        improvement = data["improvement_pct"]
        p_value = data["p_value"]
        effect_size = data["effect_size"]
        effect_label = data["effect_size_label"]

        # Format improvement with sign
        improvement_str = f"{improvement:+.1f}%"

        # Add significance marker
        sig_marker = "*" if data["is_significant"] else ""

        # Format p-value (handle None)
        p_value_str = f"{p_value:.4f}" if p_value is not None else "N/A"

        lines.append(
            f"| {metric_label} | {with_popkit_mean:.0f} | {baseline_mean:.0f} | "
            f"{improvement_str}{sig_marker} | {p_value_str} | {effect_size:.2f} ({effect_label}) |"
        )

    lines.append("")
    lines.append("*p < 0.05 indicates statistical significance")
    lines.append("")

    return "\n".join(lines)


def main():
    """Test the benchmark analyzer with sample data."""
    import tempfile

    # Create sample recording files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Sample with-PopKit recordings
        with_popkit_recordings = []
        for i in range(3):
            recording_path = tmpdir / f"with-popkit-{i}.json"
            recording_data = {
                "session_id": f"with-popkit-{i}",
                "events": [
                    {
                        "type": "tool_call",
                        "tool_name": "Read",
                        "input": {"file_path": "test.py"},
                        "output": "x" * 1000,
                        "duration_ms": 100,
                    },
                    {
                        "type": "tool_call",
                        "tool_name": "Write",
                        "input": {"file_path": "test.py", "content": "code"},
                        "output": "Success",
                        "duration_ms": 50,
                    },
                ],
            }
            recording_path.write_text(json.dumps(recording_data))
            with_popkit_recordings.append(recording_path)

        # Sample baseline recordings
        baseline_recordings = []
        for i in range(3):
            recording_path = tmpdir / f"baseline-{i}.json"
            recording_data = {
                "session_id": f"baseline-{i}",
                "events": [
                    {
                        "type": "tool_call",
                        "tool_name": "Read",
                        "input": {"file_path": "test.py"},
                        "output": "x" * 2000,
                        "duration_ms": 150,
                    },
                    {
                        "type": "tool_call",
                        "tool_name": "Write",
                        "input": {"file_path": "test.py", "content": "code"},
                        "output": "Success",
                        "duration_ms": 75,
                    },
                    {
                        "type": "tool_call",
                        "tool_name": "Write",
                        "input": {"file_path": "test.py", "content": "code2"},
                        "output": "Success",
                        "duration_ms": 50,
                        "error": "SyntaxError",
                    },
                ],
            }
            recording_path.write_text(json.dumps(recording_data))
            baseline_recordings.append(recording_path)

        # Run analysis
        analyzer = BenchmarkAnalyzer(with_popkit_recordings, baseline_recordings)
        results = analyzer.analyze()

        # Print results
        print(generate_summary_report(results))
        print("\nFull results:")
        print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
