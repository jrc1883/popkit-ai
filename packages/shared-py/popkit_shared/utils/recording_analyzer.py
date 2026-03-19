#!/usr/bin/env python3
"""
Recording Analyzer - Analyze command execution recordings

Processes session recordings to generate insights about:
- Tool usage patterns
- Performance metrics
- Error rates
- Compliance with specifications

Supports TWO recording formats:
1. PopKit JSON format - Aggregated event stream from hooks
2. Claude Code JSONL format - Native transcript files

This enables benchmarking WITH PopKit (uses #1) vs WITHOUT PopKit (uses #2).
"""

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import TranscriptParser for JSONL support
try:
    from popkit_shared.utils.transcript_parser import TranscriptParser

    HAS_TRANSCRIPT_PARSER = True
except ImportError:
    HAS_TRANSCRIPT_PARSER = False


class RecordingAnalyzer:
    """Analyzes session recordings (both PopKit JSON and Claude Code JSONL)."""

    def __init__(self, recording_file: Path):
        self.recording_file = Path(recording_file)
        self.data = self._load_recording()
        self.events = self.data.get("events", [])
        self.session_id = self.data.get("session_id", "unknown")
        self.metadata = self.data.get("metadata", {})
        self.format_type = self._detect_format()

    def _detect_format(self) -> str:
        """Detect recording format: 'popkit_json' or 'claude_jsonl'"""
        if self.recording_file.suffix == ".jsonl":
            return "claude_jsonl"
        else:
            return "popkit_json"

    def _load_recording(self) -> Dict[str, Any]:
        """Load recording from file - handles both PopKit JSON and Claude JSONL formats."""
        if self.recording_file.suffix == ".jsonl":
            return self._load_claude_jsonl()
        else:
            return self._load_popkit_json()

    def _load_popkit_json(self) -> Dict[str, Any]:
        """Load PopKit's aggregated JSON format (current default)."""
        with open(self.recording_file) as f:
            return json.load(f)

    def _load_claude_jsonl(self) -> Dict[str, Any]:
        """
        Load Claude Code's native JSONL transcript and convert to PopKit-compatible format.

        Uses TranscriptParser to extract:
        - Token usage (for context_usage metric)
        - Tool uses (for tool_calls metric)
        - Performance data (for time_to_complete metric)

        Returns a dict with the same structure as PopKit JSON for compatibility.
        """
        if not HAS_TRANSCRIPT_PARSER:
            raise ImportError(
                "TranscriptParser not available. Cannot parse Claude JSONL format. "
                "Ensure transcript_parser.py is in popkit_shared/utils/"
            )

        # Parse the JSONL transcript
        parser = TranscriptParser(str(self.recording_file))

        # Extract data
        tool_uses = parser.get_all_tool_uses()
        total_usage = parser.get_total_token_usage()

        # Convert to PopKit event structure
        events = []

        # Session start event
        events.append(
            {
                "type": "session_start",
                "sequence": 0,
                "timestamp": self._get_first_timestamp(parser),
            }
        )

        # Convert tool uses to tool_call events
        for idx, tool_use in enumerate(tool_uses, start=1):
            events.append(
                {
                    "type": "tool_call",
                    "sequence": idx,
                    "tool_name": tool_use["tool_name"],
                    "tool_use_id": tool_use["tool_use_id"],
                    "parameters": tool_use["input"],
                    "timestamp": self._get_tool_timestamp(parser, tool_use["tool_use_id"]),
                    "duration_ms": None,  # JSONL doesn't track individual durations
                    "error": None,  # Would need to parse tool_result blocks
                }
            )

        # Session end event
        events.append(
            {
                "type": "session_end",
                "sequence": len(events),
                "timestamp": self._get_last_timestamp(parser),
            }
        )

        # Build metadata with actual token counts
        metadata = {
            "total_input_tokens": total_usage.input_tokens,
            "total_output_tokens": total_usage.output_tokens,
            "cache_creation_input_tokens": total_usage.cache_creation_input_tokens,
            "cache_read_input_tokens": total_usage.cache_read_input_tokens,
            "total_tokens": total_usage.total_tokens,
            "format": "claude_jsonl",
        }

        return {
            "session_id": self._extract_session_id_from_path(),
            "events": events,
            "metadata": metadata,
            "started_at": self._get_first_timestamp(parser),
            "stopped_at": self._get_last_timestamp(parser),
        }

    def _get_first_timestamp(self, parser: Any) -> str:
        """Extract first timestamp from JSONL entries."""
        if parser.entries:
            return parser.entries[0].get("timestamp", "")
        return ""

    def _get_last_timestamp(self, parser: Any) -> str:
        """Extract last timestamp from JSONL entries."""
        if parser.entries:
            return parser.entries[-1].get("timestamp", "")
        return ""

    def _get_tool_timestamp(self, parser: Any, tool_use_id: str) -> str:
        """Find timestamp for a specific tool use."""
        for entry in parser.entries:
            if entry.get("type") != "assistant":
                continue

            message = entry.get("message", {})
            content = message.get("content", [])

            for block in content:
                if block.get("type") == "tool_use" and block.get("id") == tool_use_id:
                    return entry.get("timestamp", "")

        return ""

    def _extract_session_id_from_path(self) -> str:
        """Extract session ID from JSONL file path."""
        # Claude Code JSONL files are typically named like: <session-uuid>.jsonl
        return self.recording_file.stem  # filename without extension

    def get_timeline(self) -> List[Dict[str, Any]]:
        """Get chronological timeline of events."""
        return sorted(self.events, key=lambda e: e.get("sequence", 0))

    def get_tool_usage_breakdown(self) -> Dict[str, Dict[str, Any]]:
        """Get breakdown of tool usage.

        Works with both PopKit JSON (has duration_ms, error fields) and
        Claude JSONL (converted format with None values for these fields).
        """
        tool_calls = [e for e in self.events if e["type"] == "tool_call"]

        tools = defaultdict(lambda: {"count": 0, "total_duration_ms": 0, "errors": 0, "calls": []})

        for call in tool_calls:
            tool_name = call.get("tool_name", "unknown")
            tools[tool_name]["count"] += 1

            # Duration may be None for JSONL format
            duration = call.get("duration_ms")
            if duration is not None:
                tools[tool_name]["total_duration_ms"] += duration

            # Error may be None for JSONL format
            error = call.get("error")
            if error:
                tools[tool_name]["errors"] += 1

            tools[tool_name]["calls"].append(call)

        # Calculate averages (only if we have duration data)
        for tool, data in tools.items():
            if data["count"] > 0 and data["total_duration_ms"] > 0:
                data["avg_duration_ms"] = data["total_duration_ms"] / data["count"]
            else:
                # No duration data available (likely JSONL format)
                data["avg_duration_ms"] = 0

        return dict(tools)

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics.

        Works with both formats:
        - PopKit JSON: Has per-tool duration_ms
        - Claude JSONL: Calculate session duration from timestamps
        """
        tool_calls = [e for e in self.events if e["type"] == "tool_call"]

        if not tool_calls:
            return {"error": "No tool calls found"}

        # Try to get durations (PopKit JSON format)
        durations = [c.get("duration_ms", 0) for c in tool_calls if c.get("duration_ms")]

        # Extract session timestamps
        start_time = None
        end_time = None

        for event in self.events:
            timestamp = event.get("timestamp")
            if timestamp:
                if start_time is None:
                    start_time = timestamp
                end_time = timestamp

        # Calculate session duration if timestamps available (for JSONL format)
        session_duration_ms = None
        if start_time and end_time:
            try:
                from datetime import datetime

                start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
                session_duration_ms = int((end_dt - start_dt).total_seconds() * 1000)
            except Exception:
                # Duration calculation failed - leave session_duration_ms as 0
                pass

        return {
            "total_tool_calls": len(tool_calls),
            "total_duration_ms": sum(durations) if durations else (session_duration_ms or 0),
            "avg_duration_ms": sum(durations) / len(durations) if durations else 0,
            "min_duration_ms": min(durations) if durations else 0,
            "max_duration_ms": max(durations) if durations else 0,
            "session_start": start_time,
            "session_end": end_time,
            "session_duration_ms": session_duration_ms,  # Total session time (JSONL)
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

    def get_token_count(self) -> int:
        """Get total token count from session.

        Returns total tokens (input + output + cache) from metadata if available,
        otherwise estimates from tool call data.

        For Claude JSONL format: Uses actual token counts from TranscriptParser.
        For PopKit JSON format: Uses metadata from Claude Code 2.1.6+ or estimates.

        Returns:
            Total token count for the session
        """
        # For JSONL format, metadata.total_tokens is pre-calculated by TranscriptParser
        if self.format_type == "claude_jsonl" and self.metadata:
            total = self.metadata.get("total_tokens", 0)
            if total > 0:
                return total

        # Try to get actual token counts from metadata (Claude Code 2.1.6+)
        if self.metadata:
            input_tokens = self.metadata.get("total_input_tokens", 0)
            output_tokens = self.metadata.get("total_output_tokens", 0)
            cache_creation = self.metadata.get("cache_creation_input_tokens", 0)
            cache_read = self.metadata.get("cache_read_input_tokens", 0)

            # If we have ANY token data, calculate total (including cache tokens)
            if input_tokens or output_tokens or cache_creation or cache_read:
                return input_tokens + output_tokens + cache_creation + cache_read

            # Alternative: check for context_window data
            context_window = self.metadata.get("context_window", {})
            if context_window:
                input_tokens = context_window.get("total_input_tokens", 0)
                output_tokens = context_window.get("total_output_tokens", 0)
                cache_creation = context_window.get("cache_creation_input_tokens", 0)
                cache_read = context_window.get("cache_read_input_tokens", 0)
                if input_tokens or output_tokens or cache_creation or cache_read:
                    return input_tokens + output_tokens + cache_creation + cache_read

        # Fallback: estimate from tool call character counts
        # This is less accurate but works for older recordings without metadata
        total_chars = 0
        tool_usage = self.get_tool_usage_breakdown()

        for tool, data in tool_usage.items():
            for call in data.get("calls", []):
                # Estimate characters from parameters and results
                params = str(call.get("parameters", ""))
                result = str(call.get("result", ""))
                total_chars += len(params) + len(result)

        # Rough conversion: ~4 characters per token
        estimated_tokens = total_chars // 4
        return estimated_tokens

    def get_file_modifications(self) -> int:
        """Get count of file modifications (for backtracking detection).

        Counts how many times files were edited or written during the session.
        Multiple edits to the same file count separately.

        Returns:
            Number of file modification operations
        """
        modification_count = 0

        for event in self.events:
            if event.get("type") != "tool_call":
                continue

            tool_name = event.get("tool_name", "")
            if tool_name in ["Write", "Edit", "MultiEdit"]:
                modification_count += 1

        return modification_count

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
        from .plugin_data import get_global_plugin_data_dir

        recordings_dir = get_global_plugin_data_dir() / "recordings"

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
