#!/usr/bin/env python3
"""
Recording Analyzer - Analyze command execution recordings

Processes session recordings to generate insights about:
- Tool usage patterns
- Performance metrics
- Error rates
- Compliance with specifications
"""

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional


class RecordingAnalyzer:
    """Analyzes session recordings."""

    def __init__(self, recording_file: Path):
        self.recording_file = Path(recording_file)
        self.data = self._load_recording()
        self.events = self.data.get("events", [])
        self.session_id = self.data.get("session_id", "unknown")

    def _load_recording(self) -> Dict[str, Any]:
        """Load recording from file."""
        with open(self.recording_file) as f:
            return json.load(f)

    def get_timeline(self) -> List[Dict[str, Any]]:
        """Get chronological timeline of events."""
        return sorted(self.events, key=lambda e: e.get("sequence", 0))

    def get_tool_usage_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """Get breakdown of tool usage."""
        tool_calls = [e for e in self.events if e["type"] == "tool_call"]

        tools = defaultdict(lambda: {"count": 0, "total_duration_ms": 0, "errors": 0, "calls": []})

        for call in tool_calls:
            tool_name = call.get("tool_name", "unknown")
            tools[tool_name]["count"] += 1

            duration = call.get("duration_ms")
            if duration:
                tools[tool_name]["total_duration_ms"] += duration

            if call.get("error"):
                tools[tool_name]["errors"] += 1

            tools[tool_name]["calls"].append(call)

        # Calculate averages
        for tool, data in tools.items():
            if data["count"] > 0 and data["total_duration_ms"] > 0:
                data["avg_duration_ms"] = data["total_duration_ms"] / data["count"]

        return dict(tools)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        tool_calls = [e for e in self.events if e["type"] == "tool_call"]

        if not tool_calls:
            return {"error": "No tool calls found"}

        durations = [c.get("duration_ms", 0) for c in tool_calls if c.get("duration_ms")]

        start_time = None
        end_time = None

        for event in self.events:
            timestamp = event.get("timestamp")
            if timestamp:
                if start_time is None:
                    start_time = timestamp
                end_time = timestamp

        return {
            "total_tool_calls": len(tool_calls),
            "total_duration_ms": sum(durations),
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "min_duration_ms": min(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "session_start": start_time,
            "session_end": end_time,
        }

    def get_error_summary(self) -> Dict[str, Any]:
        """Get summary of errors."""
        tool_calls = [e for e in self.events if e["type"] == "tool_call"]
        errors = [c for c in tool_calls if c.get("error")]

        error_types = Counter()
        for error in errors:
            error_msg = str(error.get("error", "Unknown"))
            # Extract error type (first line or first 50 chars)
            error_type = error_msg.split("\n")[0][:50]
            error_types[error_type] += 1

        return {
            "total_errors": len(errors),
            "error_rate": len(errors) / len(tool_calls) if tool_calls else 0,
            "error_types": dict(error_types),
            "errors": errors,
        }

    def get_decision_summary(self) -> List[Dict[str, Any]]:
        """Get summary of user decisions."""
        return [e for e in self.events if e["type"] == "decision"]

    def get_skill_invocations(self) -> List[Dict[str, Any]]:
        """Get skill invocations."""
        return [e for e in self.events if e["type"] == "skill_invocation"]

    def generate_report(self, format: str = "markdown") -> str:
        """Generate analysis report."""
        if format == "markdown":
            return self._generate_markdown_report()
        elif format == "json":
            return self._generate_json_report()
        else:
            raise ValueError(f"Unknown format: {format}")

    def _generate_markdown_report(self) -> str:
        """Generate Markdown report."""
        tool_usage = self.get_tool_usage_breakdown()
        performance = self.get_performance_metrics()
        errors = self.get_error_summary()
        decisions = self.get_decision_summary()
        skills = self.get_skill_invocations()

        lines = []
        lines.append(f"# Recording Analysis: {self.session_id}")
        lines.append("")
        lines.append(f"**Recording File:** `{self.recording_file.name}`")
        lines.append(f"**Total Events:** {len(self.events)}")
        lines.append("")

        # Performance Summary
        lines.append("## Performance Summary")
        lines.append("")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        lines.append(f"| Total Tool Calls | {performance.get('total_tool_calls', 0)} |")
        lines.append(f"| Total Duration | {performance.get('total_duration_ms', 0):.0f}ms |")
        lines.append(f"| Avg Duration | {performance.get('avg_duration_ms', 0):.0f}ms |")
        lines.append(f"| Min Duration | {performance.get('min_duration_ms', 0):.0f}ms |")
        lines.append(f"| Max Duration | {performance.get('max_duration_ms', 0):.0f}ms |")
        lines.append("")

        # Tool Usage Breakdown
        lines.append("## Tool Usage Breakdown")
        lines.append("")
        lines.append("| Tool | Calls | Total Duration | Avg Duration | Errors |")
        lines.append("|------|-------|----------------|--------------|--------|")

        for tool, data in sorted(tool_usage.items(), key=lambda x: -x[1]["count"]):
            avg_dur = data.get("avg_duration_ms", 0)
            lines.append(
                f"| {tool} | {data['count']} | "
                f"{data['total_duration_ms']:.0f}ms | "
                f"{avg_dur:.0f}ms | "
                f"{data['errors']} |"
            )
        lines.append("")

        # Error Summary
        if errors["total_errors"] > 0:
            lines.append("## Error Summary")
            lines.append("")
            lines.append(f"**Total Errors:** {errors['total_errors']}")
            lines.append(f"**Error Rate:** {errors['error_rate']:.1%}")
            lines.append("")
            lines.append("**Error Types:**")
            for error_type, count in errors["error_types"].items():
                lines.append(f"- {error_type}: {count}")
            lines.append("")

        # Skill Invocations
        if skills:
            lines.append("## Skill Invocations")
            lines.append("")
            for skill in skills:
                lines.append(f"- **{skill.get('skill_name')}**")
                if skill.get("arguments"):
                    lines.append(f"  - Args: `{skill.get('arguments')}`")
            lines.append("")

        # Decisions
        if decisions:
            lines.append("## User Decisions")
            lines.append("")
            for decision in decisions:
                lines.append(f"### {decision.get('question', 'Unknown')}")
                lines.append(f"**Selected:** {decision.get('selected', 'Not answered')}")
                lines.append("")

        # Timeline
        lines.append("## Event Timeline")
        lines.append("")
        lines.append("| # | Type | Details | Duration |")
        lines.append("|---|------|---------|----------|")

        for event in self.get_timeline()[:20]:  # Show first 20 events
            event_type = event["type"]
            seq = event.get("sequence", 0)

            if event_type == "tool_call":
                tool_name = event.get("tool_name", "unknown")
                duration = event.get("duration_ms", 0)
                error = "ERROR" if event.get("error") else "OK"
                lines.append(f"| {seq} | Tool Call | {tool_name} [{error}] | {duration}ms |")

            elif event_type == "skill_invocation":
                skill_name = event.get("skill_name", "unknown")
                lines.append(f"| {seq} | Skill | {skill_name} | - |")

            elif event_type == "decision":
                question = event.get("question", "unknown")[:40]
                lines.append(f"| {seq} | Decision | {question}... | - |")

            elif event_type in ["session_start", "session_end"]:
                lines.append(f"| {seq} | {event_type.replace('_', ' ').title()} | - | - |")

        if len(self.events) > 20:
            lines.append("| ... | ... | ... | ... |")
            lines.append("")
            lines.append(f"*Showing first 20 of {len(self.events)} events*")

        lines.append("")
        return "\n".join(lines)

    def _generate_json_report(self) -> str:
        """Generate JSON report."""
        report = {
            "session_id": self.session_id,
            "recording_file": str(self.recording_file),
            "performance": self.get_performance_metrics(),
            "tool_usage": self.get_tool_usage_breakdown(),
            "errors": self.get_error_summary(),
            "decisions": self.get_decision_summary(),
            "skills": self.get_skill_invocations(),
            "timeline": self.get_timeline(),
        }
        return json.dumps(report, indent=2)


def analyze_recording(file_path: str, format: str = "markdown") -> str:
    """Analyze a recording file and return report."""
    analyzer = RecordingAnalyzer(Path(file_path))
    return analyzer.generate_report(format=format)


def list_recordings(recordings_dir: Optional[Path] = None) -> List[Path]:
    """List all available recordings."""
    if recordings_dir is None:
        recordings_dir = Path.home() / ".claude" / "popkit" / "recordings"

    if not recordings_dir.exists():
        return []

    return sorted(recordings_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python recording_analyzer.py <recording-file.json> [format]")
        print("\nAvailable recordings:")
        for recording in list_recordings()[:10]:
            print(f"  {recording.name}")
        sys.exit(1)

    file_path = sys.argv[1]
    format = sys.argv[2] if len(sys.argv) > 2 else "markdown"

    report = analyze_recording(file_path, format=format)
    print(report)
