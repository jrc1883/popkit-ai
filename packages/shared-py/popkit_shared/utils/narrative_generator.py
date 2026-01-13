#!/usr/bin/env python3
"""
Narrative Generator for Session Recordings

Generates natural language narratives that explain development sessions
using Claude API to analyze tool calls, reasoning, and outcomes.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def build_timeline_summary(
    events: List[Dict[str, Any]], reasoning_lookup: Dict[str, Dict[str, Any]]
) -> str:
    """Build a concise timeline summary for narrative generation."""
    timeline_items = []

    for event in events:
        if event.get("type") == "tool_call_start":
            tool_name = event.get("tool_name", "Unknown")
            tool_use_id = event.get("tool_use_id")
            timestamp = event.get("timestamp", "")

            # Extract time
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                time_str = dt.strftime("%H:%M:%S")
            except:
                time_str = "N/A"

            item = {"time": time_str, "tool": tool_name, "parameters": event.get("parameters", {})}

            # Add reasoning if available
            if tool_use_id and tool_use_id in reasoning_lookup:
                reasoning_data = reasoning_lookup[tool_use_id]
                reasoning = reasoning_data["reasoning"]

                # Include first text block as context
                if reasoning.get("text"):
                    item["reasoning_preview"] = reasoning["text"][0][:200]

                # Include thinking preview
                if reasoning.get("thinking"):
                    item["thinking_preview"] = reasoning["thinking"][0][:200]

            timeline_items.append(item)

    # Limit to most significant events (first 10 + last 5)
    if len(timeline_items) > 15:
        timeline_items = timeline_items[:10] + ["..."] + timeline_items[-5:]

    return json.dumps(timeline_items, indent=2)


def generate_narrative_with_api(
    session_data: Dict[str, Any],
    events: List[Dict[str, Any]],
    reasoning_lookup: Dict[str, Dict[str, Any]],
    total_tokens: Optional[Dict[str, int]] = None,
) -> str:
    """
    Generate narrative using Claude API.

    If API key not available, returns a template narrative.
    """
    # Check for API key
    api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        return generate_template_narrative(session_data, events, total_tokens)

    # Build timeline summary
    timeline = build_timeline_summary(events, reasoning_lookup)

    # Calculate session stats
    tool_calls = [e for e in events if e.get("type") == "tool_call_start"]
    errors = [e for e in events if e.get("type") == "tool_call_complete" and e.get("error")]

    # Get session timestamps
    start_time = session_data.get("started_at", "")
    end_time = session_data.get("stopped_at", "")

    try:
        start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        duration_minutes = (end_dt - start_dt).total_seconds() / 60
    except:
        duration_minutes = 0

    # Build prompt for Claude
    prompt = f"""Generate a concise narrative explanation of this development session.

Session Context:
- Duration: {duration_minutes:.1f} minutes
- Tool calls: {len(tool_calls)}
- Errors: {len(errors)}

Timeline of events (with Claude's reasoning):
{timeline}
"""

    if total_tokens:
        prompt += f"""
Token Usage:
- Input: {total_tokens["input_tokens"]:,}
- Output: {total_tokens["output_tokens"]:,}
- Cache reads: {total_tokens["cache_read_input_tokens"]:,}
- Total: {total_tokens["total_tokens"]:,}
"""

    prompt += """
Create a narrative that:
1. Explains what the session was trying to accomplish
2. Describes the approach Claude took (what decisions were made)
3. Highlights key tools used and why
4. Notes any errors or challenges encountered
5. Summarizes the outcome

Write in present tense, 3-4 paragraphs max. Be specific and technical.
Focus on the "why" and "how" of the decision-making process.
"""

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)

        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )

        narrative = response.content[0].text
        return narrative.strip()

    except ImportError:
        print("Warning: anthropic package not installed, using template narrative")
        return generate_template_narrative(session_data, events, total_tokens)
    except Exception as e:
        print(f"Warning: Failed to generate narrative with API: {e}")
        return generate_template_narrative(session_data, events, total_tokens)


def generate_template_narrative(
    session_data: Dict[str, Any],
    events: List[Dict[str, Any]],
    total_tokens: Optional[Dict[str, int]] = None,
) -> str:
    """Generate a template narrative when API is unavailable."""

    tool_calls = [e for e in events if e.get("type") == "tool_call_start"]
    errors = [e for e in events if e.get("type") == "tool_call_complete" and e.get("error")]

    # Count tool types
    tool_types = {}
    for event in tool_calls:
        tool_name = event.get("tool_name", "Unknown")
        tool_types[tool_name] = tool_types.get(tool_name, 0) + 1

    # Get top 3 tools
    top_tools = sorted(tool_types.items(), key=lambda x: x[1], reverse=True)[:3]
    tools_str = ", ".join([f"{name} ({count}x)" for name, count in top_tools])

    # Calculate duration
    start_time = session_data.get("started_at", "")
    end_time = session_data.get("stopped_at", "")

    try:
        start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        duration_minutes = (end_dt - start_dt).total_seconds() / 60
    except:
        duration_minutes = 0

    narrative = f"""This development session spanned {duration_minutes:.1f} minutes and involved {len(tool_calls)} tool calls across multiple operations.

The primary tools used were {tools_str}, indicating a focus on code analysis, file operations, and development workflows."""

    if errors:
        narrative += f"\n\nThe session encountered {len(errors)} error(s) during execution, which required debugging and recovery steps."
    else:
        narrative += "\n\nAll tool calls completed successfully without errors."

    if total_tokens and total_tokens["total_tokens"] > 0:
        cache_rate = 0
        if total_tokens["input_tokens"] + total_tokens["cache_read_input_tokens"] > 0:
            cache_rate = (
                total_tokens["cache_read_input_tokens"]
                / (total_tokens["input_tokens"] + total_tokens["cache_read_input_tokens"])
                * 100
            )

        narrative += f"\n\nThe session processed {total_tokens['total_tokens']:,} tokens with a {cache_rate:.1f}% cache hit rate, demonstrating efficient use of prompt caching for cost optimization."

    narrative += "\n\n*Note: AI-generated narrative requires ANTHROPIC_API_KEY environment variable. This is a template summary.*"

    return narrative


def generate_session_narrative(
    recording_file: Path,
    events: List[Dict[str, Any]],
    reasoning_lookup: Dict[str, Dict[str, Any]],
    total_tokens: Optional[Dict[str, int]] = None,
) -> str:
    """
    Generate a natural language narrative for a recording session.

    Args:
        recording_file: Path to recording JSON file
        events: List of recording events
        reasoning_lookup: Dictionary of reasoning data by tool_use_id
        total_tokens: Optional token usage summary

    Returns:
        Narrative text (HTML formatted)
    """
    with open(recording_file) as f:
        session_data = json.load(f)

    narrative = generate_narrative_with_api(session_data, events, reasoning_lookup, total_tokens)

    # Format as HTML
    # Convert paragraphs to HTML
    paragraphs = narrative.split("\n\n")
    html_paragraphs = [
        f'<p style="margin-bottom: 12px; line-height: 1.6;">{p.strip()}</p>'
        for p in paragraphs
        if p.strip()
    ]

    return "\n".join(html_paragraphs)


# Convenience function
def generate_narrative(
    recording_file: Path,
    events: List[Dict[str, Any]],
    reasoning_lookup: Dict[str, Dict[str, Any]],
    total_tokens: Optional[Dict[str, int]] = None,
) -> str:
    """Convenience wrapper for generate_session_narrative."""
    return generate_session_narrative(recording_file, events, reasoning_lookup, total_tokens)
