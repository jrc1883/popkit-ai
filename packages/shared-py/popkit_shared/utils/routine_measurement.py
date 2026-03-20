#!/usr/bin/env python3
"""
Routine Measurement Utility.

Tracks context usage, duration, and tool breakdown during routine execution.
Used when --measure flag is passed to /popkit:routine.
"""

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ToolCall:
    """Individual tool call record."""

    tool: str
    duration: float
    input_tokens: int
    output_tokens: int
    chars: int
    timestamp: float


@dataclass
class RoutineMeasurement:
    """Measurement data for a routine execution."""

    routine_id: str
    routine_name: str
    start_time: float
    end_time: Optional[float] = None
    tool_calls: List[ToolCall] = field(default_factory=list)

    @property
    def duration(self) -> float:
        """Total duration in seconds."""
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time

    @property
    def total_input_tokens(self) -> int:
        """Total estimated input tokens."""
        return sum(tc.input_tokens for tc in self.tool_calls)

    @property
    def total_output_tokens(self) -> int:
        """Total estimated output tokens."""
        return sum(tc.output_tokens for tc in self.tool_calls)

    @property
    def total_tokens(self) -> int:
        """Total estimated tokens (input + output)."""
        return self.total_input_tokens + self.total_output_tokens

    @property
    def total_chars(self) -> int:
        """Total characters processed."""
        return sum(tc.chars for tc in self.tool_calls)

    def tool_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """Breakdown by tool type."""
        breakdown = {}
        for tc in self.tool_calls:
            if tc.tool not in breakdown:
                breakdown[tc.tool] = {
                    "count": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "duration": 0.0,
                    "chars": 0,
                }
            breakdown[tc.tool]["count"] += 1
            breakdown[tc.tool]["input_tokens"] += tc.input_tokens
            breakdown[tc.tool]["output_tokens"] += tc.output_tokens
            breakdown[tc.tool]["duration"] += tc.duration
            breakdown[tc.tool]["chars"] += tc.chars

        # Sort by total tokens descending
        sorted_breakdown = dict(
            sorted(
                breakdown.items(),
                key=lambda x: x[1]["input_tokens"] + x[1]["output_tokens"],
                reverse=True,
            )
        )
        return sorted_breakdown

    def estimate_cost(self) -> Dict[str, float]:
        """Estimate API cost based on token usage.

        Uses Claude Sonnet 4.5 pricing:
        - Input: $3.00 per million tokens
        - Output: $15.00 per million tokens
        """
        input_cost = (self.total_input_tokens / 1_000_000) * 3.00
        output_cost = (self.total_output_tokens / 1_000_000) * 15.00
        total_cost = input_cost + output_cost

        return {
            "input": round(input_cost, 4),
            "output": round(output_cost, 4),
            "total": round(total_cost, 4),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "routine_id": self.routine_id,
            "routine_name": self.routine_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "total_tool_calls": len(self.tool_calls),
            "total_tokens": self.total_tokens,
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_chars": self.total_chars,
            "tool_breakdown": self.tool_breakdown(),
            "cost_estimate": self.estimate_cost(),
        }


class RoutineMeasurementTracker:
    """Singleton tracker for routine measurements."""

    _instance = None
    _measurement: Optional[RoutineMeasurement] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def start(self, routine_id: str, routine_name: str) -> None:
        """Start tracking a new routine."""
        self._measurement = RoutineMeasurement(
            routine_id=routine_id, routine_name=routine_name, start_time=time.time()
        )

    def track_tool_call(self, tool: str, content: str, duration: float = 0.0) -> None:
        """Track a tool call."""
        if self._measurement is None:
            return

        # Estimate tokens (rough: ~4 chars per token)
        chars = len(content)
        tokens = chars // 4

        # For tool calls, we estimate input vs output
        # Rough heuristic: 20% input (prompt), 80% output (result)
        input_tokens = int(tokens * 0.2)
        output_tokens = int(tokens * 0.8)

        tool_call = ToolCall(
            tool=tool,
            duration=duration,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            chars=chars,
            timestamp=time.time(),
        )
        self._measurement.tool_calls.append(tool_call)

    def stop(self) -> Optional[RoutineMeasurement]:
        """Stop tracking and return measurement."""
        if self._measurement is None:
            return None

        self._measurement.end_time = time.time()
        measurement = self._measurement
        self._measurement = None
        return measurement

    def is_active(self) -> bool:
        """Check if measurement is active."""
        return self._measurement is not None

    def get_current(self) -> Optional[RoutineMeasurement]:
        """Get current measurement (if active)."""
        return self._measurement


def estimate_tokens(text: str) -> int:
    """Estimate token count from text (rough approximation)."""
    return len(text) // 4


def format_measurement_report(measurement: RoutineMeasurement) -> str:
    """Format a measurement report for display.

    Args:
        measurement: The measurement data

    Returns:
        Formatted report string
    """
    report_lines = []

    # Header
    report_lines.append("=" * 70)
    report_lines.append("Routine Measurement Report")
    report_lines.append("=" * 70)
    report_lines.append(f"Routine: {measurement.routine_name} ({measurement.routine_id})")
    report_lines.append(f"Duration: {measurement.duration:.2f}s")
    report_lines.append(f"Tool Calls: {len(measurement.tool_calls)}")
    report_lines.append("")

    # Token Summary
    report_lines.append("Context Usage:")
    report_lines.append(
        f"  Input Tokens:  {measurement.total_input_tokens:,} (~{measurement.total_input_tokens // 1000}k)"
    )
    report_lines.append(
        f"  Output Tokens: {measurement.total_output_tokens:,} (~{measurement.total_output_tokens // 1000}k)"
    )
    report_lines.append(
        f"  Total Tokens:  {measurement.total_tokens:,} (~{measurement.total_tokens // 1000}k)"
    )
    report_lines.append(f"  Characters:    {measurement.total_chars:,}")
    report_lines.append("")

    # Cost Estimate
    cost = measurement.estimate_cost()
    report_lines.append("Cost Estimate (Claude Sonnet 4.5):")
    report_lines.append(f"  Input:  ${cost['input']:.4f}")
    report_lines.append(f"  Output: ${cost['output']:.4f}")
    report_lines.append(f"  Total:  ${cost['total']:.4f}")
    report_lines.append("")

    # Tool Breakdown
    report_lines.append("Tool Breakdown:")
    report_lines.append("-" * 70)
    report_lines.append(f"{'Tool':<20} {'Calls':<8} {'Tokens':<12} {'Duration':<10} {'Chars':<12}")
    report_lines.append("-" * 70)

    breakdown = measurement.tool_breakdown()
    for tool, stats in breakdown.items():
        total_tokens = stats["input_tokens"] + stats["output_tokens"]
        report_lines.append(
            f"{tool:<20} "
            f"{stats['count']:<8} "
            f"{total_tokens:>10,}  "
            f"{stats['duration']:>8.2f}s "
            f"{stats['chars']:>10,}"
        )

    report_lines.append("=" * 70)

    return "\n".join(report_lines)


def save_measurement(measurement: RoutineMeasurement, output_dir: Optional[Path] = None) -> Path:
    """Save measurement data to JSON file.

    Args:
        measurement: The measurement data
        output_dir: Optional output directory (defaults to <plugin_data>/measurements/)

    Returns:
        Path to saved file
    """
    if output_dir is None:
        from .plugin_data import get_plugin_data_subdir

        output_dir = get_plugin_data_subdir("measurements")

    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename with timestamp
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"{measurement.routine_id}_{timestamp}.json"
    filepath = output_dir / filename

    # Save to JSON
    with open(filepath, "w") as f:
        json.dump(measurement.to_dict(), f, indent=2)

    return filepath


def check_measure_flag() -> bool:
    """Check if --measure flag is active.

    Returns:
        True if measurement should be active
    """
    # Check environment variable
    return os.environ.get("POPKIT_ROUTINE_MEASURE", "false").lower() == "true"


def enable_measurement() -> None:
    """Enable measurement mode via environment variable."""
    os.environ["POPKIT_ROUTINE_MEASURE"] = "true"


def disable_measurement() -> None:
    """Disable measurement mode."""
    os.environ["POPKIT_ROUTINE_MEASURE"] = "false"
