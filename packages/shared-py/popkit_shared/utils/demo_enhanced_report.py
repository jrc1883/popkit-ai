"""
Demo: Enhanced Recording Report with Reasoning & Token Analysis

Shows what the enhanced HTML report will include after Phase 2-3 integration.
"""

import json
import os
from pathlib import Path

from transcript_parser import TranscriptParser


def demo_enhanced_report():
    """Demonstrate enhanced recording report features"""

    # Load the recent recording
    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA")
    recordings_dir = (
        Path(plugin_data) / "recordings"
        if plugin_data
        else Path.home() / ".claude" / "popkit" / "recordings"
    )
    recordings = sorted(
        recordings_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True
    )

    if not recordings:
        print("[ERROR] No recordings found")
        return

    recording_file = recordings[0]
    print(f"Demo: Enhanced Report for {recording_file.name}")
    print("=" * 70)
    print()

    # Load recording data
    with open(recording_file) as f:
        recording = json.load(f)

    # Extract timestamps from recording
    start_time = recording.get("started_at")
    stop_time = recording.get("stopped_at")

    # Get transcript path from recording metadata (or fallback to current session)
    transcript_path = None
    for event in recording.get("events", []):
        if event.get("type") == "metadata" and "transcript_path" in event:
            transcript_path = Path(event["transcript_path"])
            break

    if not transcript_path:
        # Fallback to current session transcript
        # Look for most recent transcript in the projects directory
        projects_dir = Path.home() / ".claude" / "projects"
        if projects_dir.exists():
            transcripts = list(projects_dir.glob("*/*.jsonl"))
            if transcripts:
                transcript_path = max(transcripts, key=lambda p: p.stat().st_mtime)

        if not transcript_path:
            transcript_path = None  # Will be handled below

    if not transcript_path.exists():
        print("[WARN] Transcript not found, skipping reasoning analysis")
        parser = None
    else:
        # Parse transcript with timestamp filtering
        print("[INFO] Parsing transcript with time filter:")
        print(f"  Start: {start_time}")
        print(f"  Stop:  {stop_time}")
        print()
        parser = TranscriptParser(str(transcript_path), start_time=start_time, end_time=stop_time)

    # Section 1: Session Overview with Token Analysis
    print("## SESSION OVERVIEW")
    print("-" * 70)

    events = recording.get("events", [])
    tool_calls = [e for e in events if e.get("type") in ("tool_call_start", "tool_call_complete")]

    print(f"Total events: {len(events)}")
    print(f"Tool calls: {len(tool_calls)}")

    if parser:
        usage = parser.get_total_token_usage()
        cost = parser.calculate_cost(usage)

        print()
        print("TOKEN USAGE:")
        print(f"  Input tokens:        {usage.input_tokens:>12,}")
        print(f"  Output tokens:       {usage.output_tokens:>12,}")
        print(f"  Cache writes:        {usage.cache_creation_input_tokens:>12,}")
        print(f"  Cache reads:         {usage.cache_read_input_tokens:>12,}")
        print("  ----------------------------------------")
        print(f"  Total tokens:        {usage.total_tokens:>12,}")
        print()
        print(f"ESTIMATED COST: ${cost:.2f}")

        # Cache hit rate
        if usage.input_tokens + usage.cache_read_input_tokens > 0:
            cache_rate = (
                usage.cache_read_input_tokens
                / (usage.input_tokens + usage.cache_read_input_tokens)
                * 100
            )
            print(f"Cache hit rate: {cache_rate:.1f}%")

    print()
    print()

    # Section 2: Enhanced Tool Timeline
    print("## ENHANCED TOOL TIMELINE")
    print("-" * 70)

    # Show first 5 tool calls with reasoning
    tool_starts = [e for e in events if e.get("type") == "tool_call_start"][:5]

    for i, event in enumerate(tool_starts, 1):
        tool_name = event.get("tool_name")
        timestamp = (
            event.get("timestamp", "").split("T")[1][:8]
            if "T" in event.get("timestamp", "")
            else "N/A"
        )
        tool_use_id = event.get("tool_use_id")

        print(f"\n{i}. [{timestamp}] {tool_name}")

        if parser and tool_use_id:
            # Get reasoning
            reasoning = parser.get_reasoning_before_tool(tool_use_id)

            if reasoning["text"]:
                print("\n   CLAUDE'S REASONING:")
                # Show first text block
                text = reasoning["text"][0]
                lines = text.split("\n")
                for line in lines[:3]:  # First 3 lines
                    print(f"   > {line}")
                if len(lines) > 3:
                    print(f"   > ... ({len(lines) - 3} more lines)")

            if reasoning["thinking"]:
                print(f"\n   EXTENDED THINKING: ({len(reasoning['thinking'])} blocks)")
                # Show preview of first thinking block
                thinking = reasoning["thinking"][0]
                preview = thinking[:150].replace("\n", " ")
                print(f"   > {preview}...")

            # Get token usage for this tool
            tool_usage = parser.get_token_usage_for_tool(tool_use_id)
            if tool_usage:
                tool_cost = parser.calculate_cost(tool_usage)
                print(f"\n   TOKENS: {tool_usage.total_tokens:,} | COST: ${tool_cost:.4f}")

    print()
    print()

    # Section 3: Session Narrative (Would be AI-generated)
    print("## SESSION NARRATIVE (AI-Generated)")
    print("-" * 70)
    print("""
    This development session focused on building a transcript parser to extract
    Claude's reasoning and token usage from session recordings. The work proceeded
    through several phases:

    1. Investigation Phase: Examined transcript file format and structure
    2. Implementation Phase: Created TranscriptParser class with core methods
    3. Testing Phase: Validated parser with comprehensive test suite
    4. Integration Phase: Demonstrated enhanced reporting capabilities

    Key achievements:
    - Parsed 1,666 transcript entries successfully
    - Extracted 404 tool use events with reasoning
    - Implemented token usage tracking and cost calculation
    - Validated 99% cache hit rate optimization

    The session demonstrates efficient use of prompt caching, resulting in
    significant cost savings compared to uncached execution.
    """)

    print()
    print("=" * 70)
    print("This is what your enhanced recording reports will look like!")
    print("Next: Integrate transcript parser into html_report_generator.py")
    print("=" * 70)


if __name__ == "__main__":
    demo_enhanced_report()
