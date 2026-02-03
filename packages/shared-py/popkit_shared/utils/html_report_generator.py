#!/usr/bin/env python3
"""
Enhanced HTML Report Generator - Session Recording Reports

Generates comprehensive HTML reports from PopKit session recordings with:
- Unified timeline (main + sub-agents)
- Separate Description column for high-level task context
- Visual hierarchy with tree connectors for sub-agents
- Parallel execution grouping with brackets and labels
- Expandable agent responses with previews
- Agent name resolution (e.g., "code-reviewer (ADB1330)")
- Claude's reasoning and thinking blocks
- Token usage and cost analysis
- AI-generated session narratives
- Visual cost distribution charts
"""

import ast
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Transcript parser feature flag (for future use)
HAS_TRANSCRIPT_PARSER = False

# Import narrative generator for AI summaries
try:
    from narrative_generator import generate_narrative

    HAS_NARRATIVE_GENERATOR = True
except ImportError:
    HAS_NARRATIVE_GENERATOR = False


def parse_timestamp(ts_str: str) -> datetime:
    """Parse ISO 8601 timestamp string."""
    try:
        # Handle both with/without Z suffix
        if ts_str.endswith("Z"):
            ts_str = ts_str[:-1] + "+00:00"
        return datetime.fromisoformat(ts_str)
    except ValueError:
        try:
            # Fallback: try without microseconds
            return datetime.strptime(ts_str[:19], "%Y-%m-%dT%H:%M:%S")
        except:
            return datetime.min


def format_duration(duration_ms: Optional[int]) -> str:
    """Format duration in milliseconds to human-readable string."""
    if duration_ms is None:
        return "N/A"
    seconds = duration_ms / 1000
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes = seconds / 60
    return f"{minutes:.1f}m"


def clean_escaped_text(text: str) -> str:
    """Clean escaped characters from text."""
    # Replace common escape sequences
    text = text.replace("\\n", "\n")
    text = text.replace("\\r", "")
    text = text.replace("\\t", "    ")
    text = text.replace('\\"', '"')
    text = text.replace("\\'", "'")
    return text


def try_parse_python_structure(text: str) -> Optional[Any]:
    """Try to parse text as a Python literal structure."""
    try:
        cleaned = clean_escaped_text(text)
        parsed = ast.literal_eval(cleaned)
        return parsed
    except:
        return None


def try_parse_json(text: str) -> Optional[Any]:
    """Try to parse text as JSON."""
    try:
        return json.loads(text)
    except:
        return None


def pretty_print_structure(obj: Any) -> str:
    """Pretty print a Python/JSON structure."""
    return json.dumps(obj, indent=2, default=str)


def format_code_content(text: str) -> str:
    """Format content with syntax highlighting."""
    if not text:
        return "<em>empty</em>"

    # Try JSON parsing first
    parsed_json = try_parse_json(text)
    if parsed_json is not None:
        pretty = pretty_print_structure(parsed_json)
        return f'<pre class="code-block"><code class="language-json">{escape_html(pretty)}</code></pre>'

    # Clean escaped characters for plain text
    cleaned = clean_escaped_text(text)

    # Detect language for syntax highlighting
    language = detect_language(cleaned)

    return f'<pre class="code-block"><code class="language-{language}">{escape_html(cleaned)}</code></pre>'


def detect_language(text: str) -> str:
    """Detect programming language from content."""
    if any(kw in text for kw in ["import ", "from ", "def ", "class ", "if __name__"]):
        return "python"
    if any(sh in text for sh in ["#!/bin/", "cd ", "mkdir ", "git ", "npm ", "python "]):
        return "bash"
    if any(md in text for md in ["# ", "## ", "**", "```", "- ["]):
        return "markdown"
    return "python"


def make_file_link(file_path: str) -> str:
    """Convert file path to clickable link."""
    escaped_path = escape_html(file_path)
    # Use file:// protocol for browser compatibility
    # Convert backslashes to forward slashes for Windows paths
    url_path = file_path.replace("\\", "/")
    return f'<a href="file:///{url_path}" target="_blank" class="file-link">{escaped_path}</a>'


def format_params_inline(params: Dict[str, Any]) -> str:
    """Format key parameters for inline display."""
    if not params:
        return "<em>none</em>"

    key_params = []

    # File path (make it clickable)
    if "file_path" in params:
        file_path = params["file_path"]
        key_params.append(make_file_link(file_path))

    # Command
    if "command" in params:
        cmd = params["command"]
        if len(cmd) > 100:
            cmd_preview = cmd[:100] + "..."
        else:
            cmd_preview = cmd
        key_params.append(f"<code>{escape_html(cmd_preview)}</code>")

    # Description (tool's description parameter)
    if "description" in params:
        desc = params["description"]
        key_params.append(f"<br>{escape_html(desc)}")

    # Skill name
    if "skill" in params:
        skill = params["skill"]
        key_params.append(f"skill: {escape_html(skill)}")

    # Pattern (for Grep)
    if "pattern" in params:
        pattern = params["pattern"]
        key_params.append(f"pattern: <code>{escape_html(pattern)}</code>")

    return "<br>".join(key_params) if key_params else "<em>various params</em>"


def get_agent_name_from_type(subagent_type: str) -> str:
    """Extract friendly agent name from subagent_type."""
    # Examples:
    # "popkit-dev:code-reviewer" -> "code-reviewer"
    # "code-reviewer" -> "code-reviewer"
    if ":" in subagent_type:
        return subagent_type.split(":")[-1]
    return subagent_type


def compute_session_token_usage(
    claude_dir: Path,
    subagent_stops: List[Dict],
    recording_start: str = None,
    recording_end: str = None,
) -> Dict[str, Any]:
    """
    Compute total token usage for the recording session ONLY.

    Parses transcripts and filters by recording window timestamps to exclude
    events outside the recording session.

    Args:
        claude_dir: Path to .claude directory
        subagent_stops: List of subagent_stop events
        recording_start: ISO timestamp when recording started
        recording_end: ISO timestamp when recording ended

    Returns dict with:
        - total_tokens: Total token count
        - input_tokens: Input tokens
        - output_tokens: Output tokens
        - cache_creation_input_tokens: Cache write tokens
        - cache_read_input_tokens: Cache read tokens
        - total_cost: Estimated cost in USD
        - per_agent: Dict mapping agent_id -> usage breakdown
        - context_percentage: Percentage of 200k context window
    """
    if not HAS_TRANSCRIPT_PARSER:
        return None

    # Parse timestamp boundaries
    # Recording timestamps are in LOCAL time (no timezone), transcripts are in UTC
    # Convert recording timestamps to UTC for comparison
    import time

    start_dt = None
    end_dt = None
    if recording_start:
        try:
            # Parse as naive (local) datetime
            start_local = datetime.fromisoformat(recording_start.replace("Z", "+00:00"))
            # If it's already timezone-aware (has Z), use it as-is
            if recording_start.endswith("Z") or "+" in recording_start:
                start_dt = start_local
            else:
                # Assume local time, convert to UTC
                start_dt = start_local.replace(tzinfo=timezone.utc).astimezone(timezone.utc)
                # Actually, we need to treat it as local time first
                # Get local timezone offset
                is_dst = time.daylight and time.localtime().tm_isdst > 0
                utc_offset = -(time.altzone if is_dst else time.timezone)
                from datetime import timedelta

                start_dt = start_local.replace(
                    tzinfo=timezone(timedelta(seconds=utc_offset))
                ).astimezone(timezone.utc)
            # Converted local time to UTC for comparison with transcript timestamps
        except Exception as e:
            print(f"Warning: Failed to parse recording_start: {e}")
            pass
    if recording_end:
        try:
            end_local = datetime.fromisoformat(recording_end.replace("Z", "+00:00"))
            if recording_end.endswith("Z") or "+" in recording_end:
                end_dt = end_local
            else:
                is_dst = time.daylight and time.localtime().tm_isdst > 0
                utc_offset = -(time.altzone if is_dst else time.timezone)
                from datetime import timedelta

                end_dt = end_local.replace(
                    tzinfo=timezone(timedelta(seconds=utc_offset))
                ).astimezone(timezone.utc)
            # Converted local time to UTC for comparison with transcript timestamps
        except Exception as e:
            print(f"Warning: Failed to parse recording_end: {e}")
            pass

    # Track per-agent usage
    per_agent = {}

    # Parse each sub-agent transcript
    for stop_event in subagent_stops:
        agent_id = stop_event.get("agent_id")
        if not agent_id:
            continue

        short_id = agent_id.split("-")[0] if "-" in agent_id else agent_id

        # Find transcript file
        transcript_file = None
        for project_dir in claude_dir.iterdir():
            if not project_dir.is_dir():
                continue

            candidate = project_dir / f"agent-{short_id}.jsonl"
            if candidate.exists():
                transcript_file = candidate
                break

        if not transcript_file:
            continue

        try:
            # Manually parse transcript to filter by timestamp
            input_tokens = 0
            output_tokens = 0
            cache_creation_tokens = 0
            cache_read_tokens = 0

            with open(transcript_file, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if not line.strip():
                        continue

                    try:
                        msg = json.loads(line)

                        # Get message timestamp (transcripts are in UTC with Z suffix)
                        msg_timestamp = msg.get("timestamp")
                        if msg_timestamp and start_dt and end_dt:
                            try:
                                # Parse transcript timestamp (UTC)
                                msg_dt = datetime.fromisoformat(
                                    msg_timestamp.replace("Z", "+00:00")
                                )
                                # Ensure it's timezone-aware (should already be UTC)
                                if msg_dt.tzinfo is None:
                                    msg_dt = msg_dt.replace(tzinfo=timezone.utc)

                                # Skip messages outside recording window
                                if msg_dt < start_dt or msg_dt > end_dt:
                                    continue
                            except Exception:
                                pass  # If we can't parse timestamp, include the message

                        # Extract token usage from this message
                        # Handle both direct role and nested message.role formats
                        message_obj = msg.get("message", msg)
                        if message_obj.get("role") == "assistant":
                            usage = message_obj.get("usage", {})
                            input_tokens += usage.get("input_tokens", 0)
                            output_tokens += usage.get("output_tokens", 0)
                            cache_creation_tokens += usage.get("cache_creation_input_tokens", 0)
                            cache_read_tokens += usage.get("cache_read_input_tokens", 0)
                    except json.JSONDecodeError:
                        continue

            # Calculate cost (Claude Sonnet 4.5 pricing)
            cost = (
                (input_tokens * 3.00 / 1_000_000)
                + (output_tokens * 15.00 / 1_000_000)
                + (cache_creation_tokens * 3.75 / 1_000_000)
                + (cache_read_tokens * 0.30 / 1_000_000)
            )

            total_tokens_agent = (
                input_tokens + output_tokens + cache_creation_tokens + cache_read_tokens
            )

            per_agent[agent_id] = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "cache_creation_input_tokens": cache_creation_tokens,
                "cache_read_input_tokens": cache_read_tokens,
                "total_tokens": total_tokens_agent,
                "cost": cost,
            }
        except Exception as e:
            print(f"Warning: Failed to parse tokens for agent {agent_id}: {e}")
            continue

    # Sum across all agents
    if not per_agent:
        return None

    total_input = sum(a["input_tokens"] for a in per_agent.values())
    total_output = sum(a["output_tokens"] for a in per_agent.values())
    total_cache_write = sum(a["cache_creation_input_tokens"] for a in per_agent.values())
    total_cache_read = sum(a["cache_read_input_tokens"] for a in per_agent.values())
    total_cost = sum(a["cost"] for a in per_agent.values())

    total_tokens = total_input + total_output + total_cache_write + total_cache_read

    # Calculate context percentage (assume 200k window)
    CONTEXT_WINDOW = 200_000
    context_percentage = (total_tokens / CONTEXT_WINDOW) * 100

    return {
        "input_tokens": total_input,
        "output_tokens": total_output,
        "cache_creation_input_tokens": total_cache_write,
        "cache_read_input_tokens": total_cache_read,
        "total_tokens": total_tokens,
        "total_cost": total_cost,
        "per_agent": per_agent,
        "context_percentage": context_percentage,
    }


def parse_agent_transcripts(claude_dir: Path, subagent_stops: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Parse agent transcript files to extract tool calls and reasoning.

    Returns a dict mapping agent_id -> list of events.
    """
    transcripts = {}

    for stop_event in subagent_stops:
        agent_id = stop_event.get("agent_id")
        if not agent_id:
            continue

        # Find matching transcript file
        # Format: agent-{short_id}.jsonl
        short_id = agent_id.split("-")[0] if "-" in agent_id else agent_id

        transcript_file = None
        # Search all project directories for this agent's transcript
        for project_dir in claude_dir.iterdir():
            if not project_dir.is_dir():
                continue

            candidate = project_dir / f"agent-{short_id}.jsonl"
            if candidate.exists():
                transcript_file = candidate
                break

        if not transcript_file:
            continue

        # Parse the transcript file directly
        events = []
        try:
            with open(transcript_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                        timestamp = entry.get("timestamp", "")
                        msg = entry.get("message", {})
                        msg_type = entry.get("type", "unknown")

                        if msg_type == "user":
                            content = msg.get("content", "")

                            # Check if content is a list (tool results) or string (prompt)
                            if isinstance(content, list):
                                # This is tool results, skip it (or handle separately)
                                continue
                            elif isinstance(content, str) and content.strip():
                                # This is an actual user prompt
                                events.append(
                                    {
                                        "agent_id": agent_id,
                                        "timestamp": timestamp,
                                        "parsed_timestamp": parse_timestamp(timestamp),
                                        "type": "subagent_prompt",
                                        "content": content,
                                    }
                                )
                        elif msg_type == "assistant":
                            content_blocks = msg.get("content", [])
                            for block in content_blocks:
                                if isinstance(block, dict):
                                    if block.get("type") == "tool_use":
                                        events.append(
                                            {
                                                "agent_id": agent_id,
                                                "timestamp": timestamp,
                                                "parsed_timestamp": parse_timestamp(timestamp),
                                                "type": "subagent_tool_call",
                                                "tool_name": block.get("name", "unknown"),
                                                "tool_use_id": block.get("id"),
                                                "parameters": block.get("input", {}),
                                            }
                                        )
                                    elif block.get("type") == "text":
                                        text = block.get("text", "")
                                        if text.strip():
                                            events.append(
                                                {
                                                    "agent_id": agent_id,
                                                    "timestamp": timestamp,
                                                    "parsed_timestamp": parse_timestamp(timestamp),
                                                    "type": "subagent_text",
                                                    "text": text,
                                                }
                                            )
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Warning: Failed to parse transcript for agent {agent_id}: {e}")
            continue

        transcripts[agent_id] = events

    return transcripts


def build_unified_timeline(
    main_events: List[Dict], transcripts: Dict[str, List[Dict]]
) -> List[Dict]:
    """
    Build a unified timeline merging main agent and sub-agent events.

    Sub-agent events are inserted after their corresponding Task launch,
    not after the subagent_stop event.

    Returns a flat list of events in chronological order, with sub-agent events
    nested under their launch points.
    """
    # Build a map of Task launches to their agent_ids
    # We'll use a simpler approach: match Task launches with available transcripts
    timeline = []
    used_transcripts = set()

    for i, event in enumerate(main_events):
        timeline.append({**event, "source": "main"})

        # If this is a Task tool launch, try to find matching sub-agent events
        if event.get("type") == "tool_call_start" and event.get("tool_name") == "Task":
            # Look ahead to find the corresponding subagent_stop event
            for future_event in main_events[i + 1 :]:
                if future_event.get("type") == "subagent_stop":
                    agent_id = future_event.get("agent_id")
                    if agent_id and agent_id in transcripts and agent_id not in used_transcripts:
                        # Insert sub-agent events here
                        sub_events = transcripts[agent_id]
                        for sub_event in sub_events:
                            timeline.append({**sub_event, "source": agent_id, "agent_id": agent_id})
                        used_transcripts.add(agent_id)
                        break
                elif (
                    future_event.get("type") == "tool_call_start"
                    and future_event.get("tool_name") == "Task"
                ):
                    # Hit another Task launch before finding a stop, break
                    break

    return timeline


def mark_subagent_scopes(events: List[Dict]) -> List[Dict]:
    """
    Mark events that occur within a sub-agent's scope for visual indentation.

    Adds 'in_subagent' flag and 'subagent_id' to events between launch and stop.
    """
    result = []
    active_subagents = []  # Stack of active sub-agent IDs

    for event in events:
        event_type = event.get("type")

        # Track sub-agent launches
        if event_type == "tool_call_start":
            params = event.get("parameters", {})
            if "subagent_type" in params:
                # This is a Task tool launching a sub-agent
                # We'll mark subsequent events as being in this sub-agent
                # Extract agent ID from the stop event
                pass

        # Mark events from sub-agents
        if event.get("source") != "main":
            event["in_subagent"] = True
            event["subagent_id"] = event.get("source")

        result.append(event)

    return result


def detect_parallel_batches(events: List[Dict]) -> List[Dict]:
    """
    Detect groups of tool calls that were launched in parallel.

    Adds 'parallel_batch_id' to events that are part of a parallel batch.
    """
    result = []
    batch_id = 0
    i = 0

    while i < len(events):
        event = events[i]

        # Check if this is a tool_call_start
        if event.get("type") == "tool_call_start":
            # Look ahead for consecutive tool_call_starts within 1 second
            batch = [event]
            event_time = parse_timestamp(event.get("timestamp", ""))

            j = i + 1
            while j < len(events):
                next_event = events[j]
                if next_event.get("type") != "tool_call_start":
                    break

                next_time = parse_timestamp(next_event.get("timestamp", ""))
                time_diff = abs((next_time - event_time).total_seconds())

                if time_diff <= 1.0:  # Within 1 second = parallel
                    batch.append(next_event)
                    j += 1
                else:
                    break

            # If we found a batch of 2 or more, mark them
            if len(batch) >= 2:
                batch_id += 1
                for idx, batch_event in enumerate(batch):
                    batch_event["parallel_batch_id"] = batch_id
                    batch_event["parallel_batch_index"] = idx
                    batch_event["parallel_batch_size"] = len(batch)
                    result.append(batch_event)
                i = j
            else:
                result.append(event)
                i += 1
        else:
            result.append(event)
            i += 1

    return result


def get_agent_color(source: str) -> Tuple[str, str]:
    """Get background and border color for agent badge."""
    if source == "main":
        return "#1e3a5f", "#58a6ff"
    else:
        # Sub-agents get purple theme
        return "#3d1e5f", "#a371f7"


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    if not isinstance(text, str):
        text = str(text)

    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&#x27;")
    return text


def parse_transcript_for_reasoning(
    data: Dict[str, Any], events: List[Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """
    Parse transcript data to extract reasoning blocks and token usage.

    Returns a dict mapping tool_use_id -> {reasoning, tokens, cost}
    """
    reasoning_lookup = {}

    if not data or not isinstance(data, dict):
        return reasoning_lookup

    messages = data.get("messages", [])

    for message in messages:
        if message.get("role") != "assistant":
            continue

        content = message.get("content", [])
        if not isinstance(content, list):
            continue

        # Extract thinking blocks
        thinking_blocks = []
        text_blocks = []
        tool_use_blocks = []

        for block in content:
            block_type = block.get("type")

            if block_type == "thinking":
                thinking_blocks.append(block.get("thinking", ""))
            elif block_type == "text":
                text_blocks.append(block.get("text", ""))
            elif block_type == "tool_use":
                tool_use_blocks.append(block)

        # Associate reasoning with tool uses
        for tool_block in tool_use_blocks:
            tool_use_id = tool_block.get("id")
            if not tool_use_id:
                continue

            # Get token usage from message
            usage = message.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            cache_creation = usage.get("cache_creation_input_tokens", 0)
            cache_read = usage.get("cache_read_input_tokens", 0)

            # Calculate cost (Claude Sonnet 4.5 pricing)
            # Input: $3/M, Output: $15/M, Cache Write: $3.75/M, Cache Read: $0.30/M
            cost = (
                (input_tokens * 3.00 / 1_000_000)
                + (output_tokens * 15.00 / 1_000_000)
                + (cache_creation * 3.75 / 1_000_000)
                + (cache_read * 0.30 / 1_000_000)
            )

            reasoning_lookup[tool_use_id] = {
                "reasoning": {"thinking": thinking_blocks, "text": text_blocks},
                "tokens": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "cache_creation_input_tokens": cache_creation,
                    "cache_read_input_tokens": cache_read,
                    "total_tokens": input_tokens + output_tokens + cache_creation + cache_read,
                },
                "cost": cost,
            }

    return reasoning_lookup


def generate_html_report(recording_file: Path, output_file: Path) -> None:
    """Generate enhanced HTML report from recording file."""

    # Load recording data
    with open(recording_file) as f:
        session_data = json.load(f)

    events = session_data.get("events", [])
    session_id = session_data.get("session_id", "unknown")
    started_at = session_data.get("started_at", "")
    stopped_at = session_data.get("stopped_at", "")

    # Calculate duration
    try:
        start_dt = parse_timestamp(started_at)
        # If stopped_at is missing, use the last event timestamp
        if stopped_at:
            end_dt = parse_timestamp(stopped_at)
        elif events:
            last_timestamp = events[-1].get("timestamp", started_at)
            end_dt = parse_timestamp(last_timestamp)
        else:
            end_dt = start_dt

        duration_sec = (end_dt - start_dt).total_seconds()
        # Sanity check - negative duration means bad timestamps
        if duration_sec < 0:
            duration_sec = 0.0
    except:
        duration_sec = 0.0

    # Count main tool calls (exclude sub-agent events)
    tool_calls = [e for e in events if e.get("type") == "tool_call_start"]
    tool_completes = [e for e in events if e.get("type") == "tool_call_complete"]
    subagent_stops = [e for e in events if e.get("type") == "subagent_stop"]

    # Build completion map for status checking
    # Match tool_call_start events with their corresponding tool_call_complete
    completion_map = {}

    # First pass: map tool_use_id from starts
    tool_use_to_seq = {}
    for start in tool_calls:
        tool_use_id = start.get("tool_use_id")
        seq = start.get("sequence")
        if tool_use_id and seq is not None:
            tool_use_to_seq[tool_use_id] = seq

    # Second pass: mark starts as complete if we find matching tool_use_id
    # Since completions don't have tool_use_id, we match by position
    pending_starts = []
    for event in events:
        if event.get("type") == "tool_call_start":
            pending_starts.append(event)
        elif event.get("type") == "tool_call_complete":
            # Match with the oldest pending start of the same tool type
            tool_name = event.get("tool_name")
            for i, start in enumerate(pending_starts):
                if start.get("tool_name") == tool_name:
                    # Mark this start as complete
                    start_seq = start.get("sequence")
                    if start_seq is not None:
                        completion_map[start_seq] = True
                    pending_starts.pop(i)
                    break

    # Calculate success rate
    errors = [e for e in tool_completes if e.get("error")]
    success_rate = (len(tool_completes) - len(errors)) / max(len(tool_completes), 1) * 100

    # Parse transcripts for reasoning and token data
    reasoning_lookup = {}
    total_tokens = None

    # Check if there's transcript data embedded or referenced
    # For now, we'll compute totals from reasoning_lookup after parsing

    # Parse agent transcripts if available
    claude_dir = Path.home() / ".claude" / "projects"
    transcripts = parse_agent_transcripts(claude_dir, subagent_stops)

    # Compute comprehensive session token usage (filtered by recording window)
    # Use computed end_dt if stopped_at is missing
    end_timestamp = stopped_at
    if not stopped_at and events:
        # Use last event timestamp
        end_timestamp = events[-1].get("timestamp", started_at)

    session_token_usage = compute_session_token_usage(
        claude_dir, subagent_stops, recording_start=started_at, recording_end=end_timestamp
    )

    # Also try to parse main agent transcript (session.jsonl or similar)
    # Main agent transcripts help populate token data for main tool calls
    for project_dir in claude_dir.iterdir():
        if not project_dir.is_dir():
            continue

        # Try common main session transcript names
        main_transcript_candidates = [
            project_dir / "session.jsonl",
            project_dir / "transcript.jsonl",
        ]

        for transcript_file in main_transcript_candidates:
            if transcript_file.exists():
                try:
                    messages = []
                    with open(transcript_file, encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            if line.strip():
                                msg = json.loads(line)
                                messages.append(msg)

                    # Parse reasoning from main session
                    transcript_data = {"messages": messages}
                    main_reasoning = parse_transcript_for_reasoning(transcript_data, events)
                    reasoning_lookup.update(main_reasoning)
                    break
                except:
                    continue

    # If we have transcripts, try to parse reasoning from them
    if transcripts:
        # For each sub-agent transcript, parse reasoning
        for agent_id, sub_events in transcripts.items():
            # Find the transcript file and parse it for reasoning
            short_id = agent_id.split("-")[0] if "-" in agent_id else agent_id

            for project_dir in claude_dir.iterdir():
                if not project_dir.is_dir():
                    continue

                transcript_file = project_dir / f"agent-{short_id}.jsonl"
                if not transcript_file.exists():
                    continue

                # Load transcript and parse reasoning
                try:
                    # Read all lines and construct a messages array
                    messages = []
                    with open(transcript_file) as f:
                        for line in f:
                            if line.strip():
                                msg = json.loads(line)
                                messages.append(msg)

                    # Parse reasoning from messages
                    transcript_data = {"messages": messages}
                    agent_reasoning = parse_transcript_for_reasoning(transcript_data, sub_events)
                    reasoning_lookup.update(agent_reasoning)
                except:
                    pass

                break

        # Calculate total tokens from all reasoning
        total_input = sum(r["tokens"]["input_tokens"] for r in reasoning_lookup.values())
        total_output = sum(r["tokens"]["output_tokens"] for r in reasoning_lookup.values())
        total_cache_write = sum(
            r["tokens"]["cache_creation_input_tokens"] for r in reasoning_lookup.values()
        )
        total_cache_read = sum(
            r["tokens"]["cache_read_input_tokens"] for r in reasoning_lookup.values()
        )

        total_tokens = {
            "input_tokens": total_input,
            "output_tokens": total_output,
            "cache_creation_input_tokens": total_cache_write,
            "cache_read_input_tokens": total_cache_read,
            "total_tokens": total_input + total_output + total_cache_write + total_cache_read,
        }
        total_cost = sum(v["cost"] for v in reasoning_lookup.values())

    # Generate AI narrative summary
    narrative_html = None
    if HAS_NARRATIVE_GENERATOR and reasoning_lookup:
        try:
            narrative_html = generate_narrative(
                recording_file, events, reasoning_lookup, total_tokens
            )
        except Exception as e:
            print(f"Warning: Failed to generate narrative: {e}")

    # Build unified timeline
    unified_timeline = build_unified_timeline(events, transcripts)
    unified_timeline = mark_subagent_scopes(unified_timeline)
    unified_timeline = detect_parallel_batches(unified_timeline)

    # Start HTML generation
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PopKit Session: {session_id}</title>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css" rel="stylesheet" />
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0d1117;
            color: #c9d1d9;
            padding: 20px;
            font-size: 14px;
        }}
        .container {{
            max-width: 1900px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            color: white;
            font-size: 24px;
            margin-bottom: 8px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        .stat-card {{
            background: #161b22;
            padding: 15px;
            border-radius: 8px;
            border-left: 3px solid #667eea;
        }}
        .stat-card .label {{
            color: #8b949e;
            font-size: 11px;
            text-transform: uppercase;
            margin-bottom: 6px;
            font-weight: 600;
        }}
        .stat-card .value {{
            font-size: 28px;
            font-weight: bold;
            color: #58a6ff;
        }}

        .timeline-section {{
            background: #161b22;
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 20px;
        }}
        .timeline-section h2 {{
            padding: 20px;
            font-size: 18px;
            color: #c9d1d9;
            background: #21262d;
            margin: 0;
        }}
        .timeline-scroll {{
            max-height: 1200px;
            overflow-y: auto;
            overflow-x: hidden;
        }}
        .timeline-scroll::-webkit-scrollbar {{
            width: 12px;
        }}
        .timeline-scroll::-webkit-scrollbar-track {{
            background: #0d1117;
        }}
        .timeline-scroll::-webkit-scrollbar-thumb {{
            background: #30363d;
            border-radius: 6px;
        }}

        /* NEW: Enhanced table layout with 7 columns */
        .timeline-table {{
            width: 100%;
            table-layout: fixed;
            border-collapse: collapse;
        }}
        .timeline-table th {{
            background: #21262d;
            padding: 12px;
            text-align: left;
            font-size: 12px;
            font-weight: 600;
            color: #8b949e;
            text-transform: uppercase;
            border-bottom: 1px solid #30363d;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        .timeline-table td {{
            padding: 12px;
            border-bottom: 1px solid #21262d;
            vertical-align: top;
            font-size: 12px;
            overflow: hidden;
        }}
        .timeline-table tr:hover {{
            background: #1c2128;
        }}

        /* NEW: Column width constraints (7 columns) */
        .timeline-table th:nth-child(1),
        .timeline-table td:nth-child(1) {{ width: 60px; }} /* # (wider for tree chars) */
        .timeline-table th:nth-child(2),
        .timeline-table td:nth-child(2) {{ width: 90px; }} /* Time */
        .timeline-table th:nth-child(3),
        .timeline-table td:nth-child(3) {{ width: 180px; }} /* Agent - widened for full labels */
        .timeline-table th:nth-child(4),
        .timeline-table td:nth-child(4) {{ width: 160px; }} /* Event Type */
        .timeline-table th:nth-child(5),
        .timeline-table td:nth-child(5) {{ width: 280px; }} /* Description (high-level) */
        .timeline-table th:nth-child(6),
        .timeline-table td:nth-child(6) {{ width: auto; min-width: 0; }} /* Tool/Details */
        .timeline-table th:nth-child(7),
        .timeline-table td:nth-child(7) {{ width: 110px; }} /* Status */

        /* NEW: Parallel batch styling */
        .parallel-batch-header {{
            background: #1e2a3a;
            padding: 8px 12px;
            margin: 4px 0;
            border-left: 3px solid #58a6ff;
            font-size: 11px;
            color: #8b949e;
            text-transform: uppercase;
            font-weight: 600;
        }}

        /* NEW: Tree connectors for visual hierarchy */
        .tree-connector {{
            color: #30363d;
            margin-right: 4px;
            font-family: monospace;
        }}

        .in-subagent {{
            border-left: 4px solid #a371f7 !important;
            background: rgba(163, 113, 247, 0.05);
        }}
        .in-subagent td:first-child {{
            padding-left: 25px;
        }}

        /* Code blocks - constrained to parent cell */
        .code-block {{
            margin: 8px 0;
            padding: 12px;
            background: #0d1117 !important;
            border-radius: 6px;
            border: 1px solid #30363d;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 11px;
            line-height: 1.6;
            max-height: 400px;
            overflow-y: auto;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            word-break: break-word;
            max-width: 100%;
        }}
        .code-block::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        .code-block::-webkit-scrollbar-track {{
            background: #161b22;
        }}
        .code-block::-webkit-scrollbar-thumb {{
            background: #30363d;
            border-radius: 4px;
        }}

        .text-preview {{
            color: #8b949e;
            font-size: 12px;
            line-height: 1.5;
            word-wrap: break-word;
        }}

        .file-link {{
            color: #79c0ff;
            text-decoration: none;
            border-bottom: 1px dotted #79c0ff;
            font-family: 'Consolas', monospace;
            word-break: break-all;
        }}
        .file-link:hover {{
            color: #a371f7;
            border-bottom-color: #a371f7;
        }}

        .event-badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            white-space: nowrap;
        }}
        .event-session {{ background: #6e7681; color: #fff; }}
        .event-tool {{ background: #238636; color: #fff; }}
        .event-subagent-launch {{ background: #1f6feb; color: #fff; }}
        .event-subagent-stop {{ background: #8b5cf6; color: #fff; }}
        .event-subagent-prompt {{ background: #5f3d1e; color: #fff; }}
        .event-subagent-text {{ background: #3d1e5f; color: #fff; }}
        .event-assistant {{ background: #1e5f3d; color: #fff; }}

        .status-ok {{ color: #3fb950; font-weight: 600; }}
        .status-error {{ color: #f85149; font-weight: 600; }}
        .status-na {{ color: #8b949e; }}

        .tool-name {{
            font-family: 'Consolas', monospace;
            color: #79c0ff;
            font-size: 13px;
            word-break: break-all;
        }}

        .agent-badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 600;
            font-family: 'Consolas', monospace;
            white-space: nowrap;
        }}

        /* NEW: Expandable response styling */
        .expand-btn {{
            background: #21262d;
            color: #58a6ff;
            border: 1px solid #30363d;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 11px;
            margin-top: 8px;
        }}
        .expand-btn:hover {{
            background: #30363d;
            border-color: #58a6ff;
        }}

        .response-preview {{
            color: #c9d1d9;
            font-size: 12px;
            margin-bottom: 8px;
            padding: 8px;
            background: #1c2128;
            border-radius: 4px;
            border-left: 3px solid #58a6ff;
        }}

        .response-expanded {{
            position: relative;
            left: -20px;
            width: calc(100% + 40px);
            margin: 10px 0;
            padding: 15px;
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 6px;
            overflow-x: auto;
            max-height: 600px;
            overflow-y: auto;
        }}

        .response-expanded pre {{
            margin: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}

        code {{
            font-family: 'Consolas', monospace;
            background: #161b22;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 11px;
            color: #79c0ff;
            word-break: break-all;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 PopKit Session Recording</h1>
            <div class="meta">Session ID: {session_id}</div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">Total Events</div>
                <div class="value">{len(events)}</div>
            </div>
            <div class="stat-card">
                <div class="label">Main Tool Calls</div>
                <div class="value">{len(tool_calls)}</div>
            </div>
            <div class="stat-card">
                <div class="label">Sub-Agents</div>
                <div class="value">{len(subagent_stops)}</div>
            </div>
            <div class="stat-card">
                <div class="label">Duration</div>
                <div class="value">{duration_sec:.1f}<span style="font-size: 14px; color: #8b949e;">s</span></div>
            </div>
            <div class="stat-card">
                <div class="label">Success Rate</div>
                <div class="value">{success_rate:.0f}<span style="font-size: 14px; color: #8b949e;">%</span></div>
            </div>
        </div>"""

    # Add comprehensive context usage section if available
    if session_token_usage:
        # Extract values from session_token_usage
        total_cost = session_token_usage["total_cost"]
        context_percentage = session_token_usage["context_percentage"]

        cache_hit_rate = 0
        if session_token_usage["input_tokens"] + session_token_usage["cache_read_input_tokens"] > 0:
            cache_hit_rate = (
                session_token_usage["cache_read_input_tokens"]
                / (
                    session_token_usage["input_tokens"]
                    + session_token_usage["cache_read_input_tokens"]
                )
                * 100
            )

        # Calculate cost breakdown percentages
        input_cost = session_token_usage["input_tokens"] * 3.00 / 1_000_000
        output_cost = session_token_usage["output_tokens"] * 15.00 / 1_000_000
        cache_write_cost = session_token_usage["cache_creation_input_tokens"] * 3.75 / 1_000_000
        cache_read_cost = session_token_usage["cache_read_input_tokens"] * 0.30 / 1_000_000

        # Calculate percentages for visual bar
        if total_cost > 0:
            input_pct = (input_cost / total_cost * 100) if total_cost > 0 else 0
            output_pct = (output_cost / total_cost * 100) if total_cost > 0 else 0
            cache_write_pct = (cache_write_cost / total_cost * 100) if total_cost > 0 else 0
            cache_read_pct = (cache_read_cost / total_cost * 100) if total_cost > 0 else 0
        else:
            input_pct = output_pct = cache_write_pct = cache_read_pct = 0

        # Calculate token distribution percentages
        total = session_token_usage["total_tokens"]
        if total > 0:
            input_token_pct = session_token_usage["input_tokens"] / total * 100
            output_token_pct = session_token_usage["output_tokens"] / total * 100
            cache_write_token_pct = session_token_usage["cache_creation_input_tokens"] / total * 100
            cache_read_token_pct = session_token_usage["cache_read_input_tokens"] / total * 100
        else:
            input_token_pct = output_token_pct = cache_write_token_pct = cache_read_token_pct = 0

        html += f"""
        <div class="timeline-section">
            <h2>📊 Context Usage & Cost Analysis</h2>
            <div style="background: #161b22; padding: 20px; border-radius: 8px; margin-bottom: 20px;">

                <!-- Context Window Usage -->
                <div style="margin-bottom: 25px; background: linear-gradient(135deg, #1f2937 0%, #111827 100%); padding: 20px; border-radius: 8px;">
                    <div style="color: #8b949e; font-size: 12px; margin-bottom: 12px;">SESSION CONTEXT CONSUMPTION</div>
                    <div style="display: flex; align-items: baseline; gap: 15px; margin-bottom: 8px;">
                        <div style="color: #58a6ff; font-size: 36px; font-weight: 700;">{context_percentage:.1f}%</div>
                        <div style="color: #8b949e; font-size: 14px;">of 200k context window</div>
                    </div>
                    <div style="background: #0d1117; height: 12px; border-radius: 6px; overflow: hidden; margin-bottom: 8px;">
                        <div style="background: linear-gradient(90deg, #58a6ff 0%, #a371f7 100%); height: 100%; width: {min(context_percentage, 100):.1f}%; transition: width 0.3s ease;"></div>
                    </div>
                    <div style="color: #8b949e; font-size: 12px;">
                        {session_token_usage["total_tokens"]:,} tokens consumed during this recording session
                    </div>
                </div>

                <!-- Cost Breakdown Bar -->
                <div style="margin-bottom: 25px;">
                    <div style="color: #8b949e; font-size: 12px; margin-bottom: 8px;">Cost Distribution</div>
                    <div style="display: flex; height: 30px; border-radius: 6px; overflow: hidden; background: #0d1117;">
                        <div style="background: #58a6ff; width: {input_pct:.1f}%; display: flex; align-items: center; justify-content: center; color: white; font-size: 10px; font-weight: 600;">
                            {input_pct:.0f}%
                        </div>
                        <div style="background: #f85149; width: {output_pct:.1f}%; display: flex; align-items: center; justify-content: center; color: white; font-size: 10px; font-weight: 600;">
                            {output_pct:.0f}%
                        </div>
                        <div style="background: #d29922; width: {cache_write_pct:.1f}%; display: flex; align-items: center; justify-content: center; color: white; font-size: 10px; font-weight: 600;">
                            {cache_write_pct:.0f}%
                        </div>
                        <div style="background: #3fb950; width: {cache_read_pct:.1f}%; display: flex; align-items: center; justify-content: center; color: white; font-size: 10px; font-weight: 600;">
                            {cache_read_pct:.0f}%
                        </div>
                    </div>
                    <div style="display: flex; gap: 15px; margin-top: 8px; font-size: 11px;">
                        <div><span style="display: inline-block; width: 10px; height: 10px; background: #58a6ff; border-radius: 2px;"></span> Input</div>
                        <div><span style="display: inline-block; width: 10px; height: 10px; background: #f85149; border-radius: 2px;"></span> Output</div>
                        <div><span style="display: inline-block; width: 10px; height: 10px; background: #d29922; border-radius: 2px;"></span> Cache Write</div>
                        <div><span style="display: inline-block; width: 10px; height: 10px; background: #3fb950; border-radius: 2px;"></span> Cache Read</div>
                    </div>
                </div>

                <!-- Detailed Metrics -->
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                    <div style="background: linear-gradient(135deg, #1f2937 0%, #111827 100%); padding: 15px; border-radius: 6px;">
                        <div style="color: #8b949e; font-size: 12px; margin-bottom: 8px;">Input Tokens</div>
                        <div style="color: #58a6ff; font-size: 20px; font-weight: 600; margin-bottom: 4px;">{session_token_usage["input_tokens"]:,}</div>
                        <div style="color: #8b949e; font-size: 11px;">{input_token_pct:.1f}% of total • ${input_cost:.4f}</div>
                    </div>
                    <div style="background: linear-gradient(135deg, #2d1f1f 0%, #1a1111 100%); padding: 15px; border-radius: 6px;">
                        <div style="color: #8b949e; font-size: 12px; margin-bottom: 8px;">Output Tokens</div>
                        <div style="color: #f85149; font-size: 20px; font-weight: 600; margin-bottom: 4px;">{session_token_usage["output_tokens"]:,}</div>
                        <div style="color: #8b949e; font-size: 11px;">{output_token_pct:.1f}% of total • ${output_cost:.4f}</div>
                    </div>
                    <div style="background: linear-gradient(135deg, #2d2519 0%, #1a1711 100%); padding: 15px; border-radius: 6px;">
                        <div style="color: #8b949e; font-size: 12px; margin-bottom: 8px;">Cache Write</div>
                        <div style="color: #d29922; font-size: 20px; font-weight: 600; margin-bottom: 4px;">{session_token_usage["cache_creation_input_tokens"]:,}</div>
                        <div style="color: #8b949e; font-size: 11px;">{cache_write_token_pct:.1f}% of total • ${cache_write_cost:.4f}</div>
                    </div>
                    <div style="background: linear-gradient(135deg, #1f2d1f 0%, #111a11 100%); padding: 15px; border-radius: 6px;">
                        <div style="color: #8b949e; font-size: 12px; margin-bottom: 8px;">Cache Read</div>
                        <div style="color: #3fb950; font-size: 20px; font-weight: 600; margin-bottom: 4px;">{session_token_usage["cache_read_input_tokens"]:,}</div>
                        <div style="color: #8b949e; font-size: 11px;">{cache_read_token_pct:.1f}% of total • ${cache_read_cost:.4f}</div>
                    </div>
                </div>

                <!-- Efficiency Metrics -->
                <div style="margin-top: 20px; display: grid; grid-template-columns: 1fr 1fr; gap: 15px;">
                    <div style="background: #161b22; padding: 15px; border-radius: 6px; border: 1px solid #30363d;">
                        <div style="color: #8b949e; font-size: 12px; margin-bottom: 8px;">Cache Efficiency</div>
                        <div style="display: flex; align-items: baseline; gap: 10px;">
                            <div style="color: #3fb950; font-size: 24px; font-weight: 600;">{cache_hit_rate:.1f}%</div>
                            <div style="color: #8b949e; font-size: 12px;">hit rate</div>
                        </div>
                        <div style="color: #8b949e; font-size: 11px; margin-top: 4px;">
                            {cache_hit_rate:.1f}% of input tokens served from cache
                        </div>
                    </div>
                    <div style="background: #161b22; padding: 15px; border-radius: 6px; border: 1px solid #30363d;">
                        <div style="color: #8b949e; font-size: 12px; margin-bottom: 8px;">Total Session Cost</div>
                        <div style="color: #58a6ff; font-size: 24px; font-weight: 600;">${total_cost:.2f}</div>
                        <div style="color: #8b949e; font-size: 11px; margin-top: 4px;">
                            {session_token_usage["total_tokens"]:,} tokens processed
                        </div>
                    </div>
                </div>
            </div>
        </div>"""

    # Add AI-generated narrative section
    if narrative_html:
        html += f"""
        <div class="timeline-section">
            <h2>📖 Session Narrative</h2>
            <div style="background: #161b22; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <div style="color: #c9d1d9; font-size: 14px; line-height: 1.7;">
                    {narrative_html}
                </div>
                <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #30363d;">
                    <div style="color: #8b949e; font-size: 11px; font-style: italic;">
                        ✨ AI-generated summary powered by Claude Sonnet 4.5
                    </div>
                </div>
            </div>
        </div>"""

    html += f"""
        <div class="timeline-section">
            <h2>🌐 Unified Timeline ({len(unified_timeline)} events)</h2>
            <div class="timeline-scroll">
                <table class="timeline-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Time</th>
                            <th>Agent</th>
                            <th>Event Type</th>
                            <th>Description</th>
                            <th>Tool/Details</th>
                            <th title="Input Tokens">In</th>
                            <th title="Output Tokens">Out</th>
                            <th title="Cache Read Tokens">C-R</th>
                            <th title="Cache Write Tokens">C-W</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    # Track current task description for grouping
    current_task_desc = None
    current_parallel_batch = None

    # Generate timeline rows
    for i, event in enumerate(unified_timeline, 1):
        timestamp = event.get("timestamp", "N/A")
        source = event.get("source", event.get("agent_id", "unknown"))
        event_type = event.get("type", "unknown")
        in_subagent = event.get("in_subagent", False)
        parallel_batch_id = event.get("parallel_batch_id")
        parallel_batch_index = event.get("parallel_batch_index", 0)
        parallel_batch_size = event.get("parallel_batch_size", 1)

        try:
            dt = parse_timestamp(timestamp)
            # Convert UTC to local time for sub-agent events
            if dt != datetime.min:
                # Check if timestamp has timezone info (UTC from transcripts)
                if dt.tzinfo is not None:
                    # Convert to local time
                    dt = dt.astimezone()
                time_str = dt.strftime("%H:%M:%S")
            else:
                time_str = "N/A"
        except:
            time_str = "N/A"

        bg_color, border_color = get_agent_color(source)

        # NEW: Resolve agent names
        if source == "main":
            agent_label = "MAIN"
        else:
            # Try to get friendly name from subagent_type
            agent_id = source
            short_id = agent_id[:7] if len(agent_id) > 7 else agent_id

            # Look for the agent launch event to get the type
            agent_name = None
            for e in events:
                if e.get("type") == "tool_call_start":
                    params = e.get("parameters", {})
                    if "subagent_type" in params:
                        # Check if this matches our agent somehow
                        # For now, use the subagent_type directly
                        subagent_type = params.get("subagent_type", "")
                        agent_name = get_agent_name_from_type(subagent_type)
                        break

            if agent_name:
                agent_label = f"{agent_name} ({short_id})"
            else:
                agent_label = short_id

        agent_badge = f'<span class="agent-badge" style="background: {bg_color}; color: {border_color}; border: 1px solid {border_color};">{agent_label}</span>'

        row_class = "in-subagent" if in_subagent else ""

        # NEW: Add tree connectors for visual hierarchy
        tree_prefix = ""
        if in_subagent:
            # Check if this is the last event from this sub-agent
            is_last = i == len(unified_timeline) or unified_timeline[i].get("source") != source

            if is_last:
                tree_prefix = '<span class="tree-connector">└─</span>'
            else:
                tree_prefix = '<span class="tree-connector">├─</span>'

        # NEW: Check if we need to add parallel batch header
        if parallel_batch_id and parallel_batch_id != current_parallel_batch:
            current_parallel_batch = parallel_batch_id
            html += f"""
                    <tr>
                        <td colspan="11" class="parallel-batch-header">
                            [PARALLEL BATCH #{parallel_batch_id}] {parallel_batch_size} tools launched together
                        </td>
                    </tr>
"""

        desc_html = ""  # High-level description
        tool_details_html = ""  # Specific tool/command info
        status_html = '<span class="status-ok">✓ OK</span>'
        badge_html = ""

        # Extract token data if available
        tokens_data = None
        tool_use_id = event.get("tool_use_id")
        if tool_use_id and tool_use_id in reasoning_lookup:
            tokens_data = reasoning_lookup[tool_use_id].get("tokens", {})

        if event_type == "session_start":
            badge_html = '<span class="event-badge event-session">Session Start</span>'
            desc_html = "Recording session initiated"
            tool_details_html = "<em>Session logging enabled</em>"

        elif event_type == "tool_call_start":
            tool_name = event.get("tool_name", "Unknown")
            params = event.get("parameters", {})
            tool_use_id = event.get("tool_use_id")

            # Extract description from params
            param_description = params.get("description", "")

            is_subagent_launch = "subagent_type" in params
            if is_subagent_launch:
                badge_html = (
                    '<span class="event-badge event-subagent-launch">Sub-Agent Launch</span>'
                )
                subagent_type = params.get("subagent_type", "unknown")
                task_desc = params.get("description", "")

                # Set current task description for sub-events to reference
                current_task_desc = task_desc

                desc_html = task_desc if task_desc else f"Launch {subagent_type}"
                tool_details_html = f'<span class="tool-name">Task</span> → {get_agent_name_from_type(subagent_type)}'
            else:
                badge_html = '<span class="event-badge event-tool">Tool Start</span>'

                # Use description as high-level, command as details
                desc_html = param_description if param_description else f"{tool_name} execution"
                tool_details_html = f'<span class="tool-name">{tool_name}</span>'

                # Add command/params as expandable
                params_display = format_params_inline(params)
                if params_display and params_display != "<em>none</em>":
                    tool_details_html += (
                        f'<br><small style="color: #8b949e;">{params_display}</small>'
                    )

                # Add reasoning and token info if available
                if tool_use_id and tool_use_id in reasoning_lookup:
                    reasoning_data = reasoning_lookup[tool_use_id]
                    reasoning = reasoning_data["reasoning"]
                    tokens = reasoning_data["tokens"]
                    cost = reasoning_data["cost"]

                    # Add expandable reasoning section
                    reasoning_id = f"reasoning_{i}"
                    tool_details_html += f'''
                    <div style="margin-top: 10px;">
                        <button onclick="document.getElementById('{reasoning_id}').style.display = document.getElementById('{reasoning_id}').style.display === 'none' ? 'block' : 'none'"
                                class="expand-btn">
                            💭 Show Claude's Reasoning
                        </button>
                        <div id="{reasoning_id}" style="display: none; margin-top: 10px; background: #161b22; padding: 12px; border-radius: 6px; border: 1px solid #30363d;">'''

                    # Add text blocks
                    if reasoning["text"]:
                        tool_details_html += '<div style="margin-bottom: 10px;"><strong style="color: #8b949e;">Reasoning:</strong></div>'
                        for text_block in reasoning["text"][:2]:
                            tool_details_html += f'<div style="color: #c9d1d9; margin-bottom: 8px; line-height: 1.5;">{escape_html(text_block[:300])}</div>'

                    # Add thinking preview
                    if reasoning["thinking"]:
                        tool_details_html += '<div style="margin-top: 10px;"><strong style="color: #8b949e;">Extended Thinking:</strong></div>'
                        thinking_preview = reasoning["thinking"][0][:200]
                        tool_details_html += f'<div style="color: #8b949e; font-style: italic; margin-top: 4px;">{escape_html(thinking_preview)}...</div>'

                    # Add token usage
                    if tokens:
                        tool_details_html += f"""<div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid #30363d;">
                            <div style="color: #8b949e; font-size: 11px; margin-bottom: 6px;">Token Usage:</div>
                            <div style="display: flex; gap: 15px; flex-wrap: wrap;">
                                <div><span style="color: #58a6ff;">Input:</span> {tokens["input_tokens"]:,}</div>
                                <div><span style="color: #58a6ff;">Output:</span> {tokens["output_tokens"]:,}</div>
                                <div><span style="color: #58a6ff;">Total:</span> {tokens["total_tokens"]:,}</div>
                                <div><span style="color: #3fb950;">Cost:</span> ${cost:.4f}</div>
                            </div>
                        </div>"""

                    tool_details_html += "</div></div>"

            # Check if this tool call has a completion
            seq = event.get("sequence")
            has_completion = completion_map.get(seq, False)
            # If session ended (has stopped_at or this isn't the last event), show as incomplete not running
            session_ended = bool(stopped_at) or (i < len(unified_timeline) - 1)
            if has_completion:
                status_html = '<span class="status-ok">✓ OK</span>'
            elif session_ended:
                status_html = '<span class="status-error">⚠ Incomplete</span>'
            else:
                status_html = '<span class="status-na">⏳ Running</span>'

        elif event_type == "tool_call_complete":
            tool_name = event.get("tool_name", "Unknown")
            error = event.get("error")
            duration = event.get("duration_ms")

            badge_html = '<span class="event-badge event-tool">Tool Complete</span>'
            desc_html = f"{tool_name} finished"
            tool_details_html = f'<span class="tool-name">{tool_name}</span>'
            status_html = (
                '<span class="status-error">✗ ERROR</span>'
                if error
                else f'<span class="status-ok">✓ {format_duration(duration)}</span>'
            )

        elif event_type == "subagent_stop":
            agent_id = event.get("agent_id", "unknown")
            badge_html = '<span class="event-badge event-subagent-stop">Sub-Agent Complete</span>'
            desc_html = "Task completed"
            tool_details_html = f"Agent <strong>{agent_id[:7]}</strong> finished"

        elif event_type == "subagent_user_message" or event_type == "subagent_prompt":
            badge_html = '<span class="event-badge event-subagent-prompt">SUBAGENT PROMPT</span>'
            content = event.get("content", "")

            # Use current task description
            desc_html = current_task_desc if current_task_desc else "Sub-agent task"

            # Show prompt content with preview
            if len(content) > 200:
                preview = content[:200] + "..."
                prompt_id = f"prompt_{i}"
                tool_details_html = f'''
                    <div class="response-preview">{escape_html(preview)}</div>
                    <button onclick="showModal('{prompt_id}')" class="expand-btn">
                        📄 View Full Prompt ({len(content)} chars)
                    </button>
                    <div id="{prompt_id}" class="modal-content" style="display: none;">
                        <h3 style="margin-top: 0;">Subagent Prompt</h3>
                        {format_code_content(content)}
                    </div>
                '''
            else:
                tool_details_html = f'<div class="response-preview">{escape_html(content)}</div>'

        elif event_type == "subagent_text":
            badge_html = '<span class="event-badge event-subagent-text">Assistant Text</span>'
            text = event.get("text", "")

            desc_html = "Agent response"

            # Only show expandable button if text > 150 chars
            if len(text) > 150:
                preview = text[:150] + "..."
                response_id = f"response_{i}"

                tool_details_html = f'''
                    <div class="response-preview">{escape_html(preview)}</div>
                    <button onclick="showModal('{response_id}')" class="expand-btn">
                        📄 View Full Response ({len(text)} chars)
                    </button>
                    <div id="{response_id}" class="modal-content" style="display: none;">
                        <h3 style="margin-top: 0;">Agent Response</h3>
                        {format_code_content(text)}
                    </div>
                '''
            else:
                # Text is short enough to display inline
                tool_details_html = f'<div class="response-preview">{escape_html(text)}</div>'

        elif event_type == "subagent_tool_call":
            badge_html = '<span class="event-badge event-tool">Tool Call</span>'
            tool_name = event.get("tool_name", "Unknown")
            params = event.get("parameters", {})

            param_description = params.get("description", "")
            desc_html = param_description if param_description else f"{tool_name} execution"
            tool_details_html = f'<span class="tool-name">{tool_name}</span><br><small style="color: #8b949e;">{format_params_inline(params)}</small>'

        elif event_type == "assistant_message":
            badge_html = '<span class="event-badge event-assistant">💬 Claude</span>'
            content = event.get("content", "")
            before_tool = event.get("before_tool", "")

            # Truncate long messages for timeline view
            if len(content) > 200:
                content_preview = content[:200] + "..."
            else:
                content_preview = content

            content_html = format_code_content(content_preview)
            desc_html = "Reasoning step"
            tool_details_html = f'<div style="color: #c9d1d9; font-style: italic; margin-bottom: 4px;">{content_html}</div>'
            if before_tool:
                tool_details_html += (
                    f'<small style="color: #8b949e;">→ Before {before_tool} call</small>'
                )
            status_html = '<span class="status-ok">💭 Reasoning</span>'

        else:
            badge_html = f'<span class="event-badge" style="background: #6e7681; color: #fff;">{event_type}</span>'
            desc_html = event_type
            tool_details_html = "<em>Unknown event</em>"

        # Add tree connector prefix for parallel batches
        row_number = f"{tree_prefix}{i}"
        if parallel_batch_id:
            if parallel_batch_index == 0:
                row_number += ' <span class="tree-connector">┬</span>'
            elif parallel_batch_index == parallel_batch_size - 1:
                row_number += ' <span class="tree-connector">└</span>'
            else:
                row_number += ' <span class="tree-connector">├</span>'

        # Format token cells
        if tokens_data:
            input_tokens_cell = f'<td style="text-align: right; color: #58a6ff;">{tokens_data.get("input_tokens", 0):,}</td>'
            output_tokens_cell = f'<td style="text-align: right; color: #f85149;">{tokens_data.get("output_tokens", 0):,}</td>'
            cache_read_cell = f'<td style="text-align: right; color: #3fb950;">{tokens_data.get("cache_read_input_tokens", 0):,}</td>'
            cache_write_cell = f'<td style="text-align: right; color: #d29922;">{tokens_data.get("cache_creation_input_tokens", 0):,}</td>'
        else:
            input_tokens_cell = '<td style="text-align: right; color: #6e7681;">-</td>'
            output_tokens_cell = '<td style="text-align: right; color: #6e7681;">-</td>'
            cache_read_cell = '<td style="text-align: right; color: #6e7681;">-</td>'
            cache_write_cell = '<td style="text-align: right; color: #6e7681;">-</td>'

        html += f'''
                    <tr class="{row_class}">
                        <td>{row_number}</td>
                        <td>{time_str}</td>
                        <td>{agent_badge}</td>
                        <td>{badge_html}</td>
                        <td>{desc_html}</td>
                        <td>{tool_details_html}</td>
                        {input_tokens_cell}
                        {output_tokens_cell}
                        {cache_read_cell}
                        {cache_write_cell}
                        <td>{status_html}</td>
                    </tr>
'''

    html += """
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Modal Overlay -->
    <div id="modal-overlay" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); z-index: 9998; overflow: auto;">
        <div id="modal-container" style="position: relative; max-width: 1200px; margin: 50px auto; background: #0d1117; border-radius: 12px; padding: 30px; border: 1px solid #30363d;">
            <button onclick="closeModal()" style="position: absolute; top: 15px; right: 15px; background: #21262d; border: 1px solid #30363d; color: #c9d1d9; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 14px;">✕ Close</button>
            <div id="modal-body"></div>
        </div>
    </div>

    <script>
        function toggleResponse(id) {
            const element = document.getElementById(id);
            if (element.style.display === 'none') {
                element.style.display = 'block';
            } else {
                element.style.display = 'none';
            }
        }

        function showModal(contentId) {
            const content = document.getElementById(contentId);
            const modal = document.getElementById('modal-overlay');
            const modalBody = document.getElementById('modal-body');

            if (content && modal && modalBody) {
                modalBody.innerHTML = content.innerHTML;
                modal.style.display = 'block';
                document.body.style.overflow = 'hidden';
            }
        }

        function closeModal() {
            const modal = document.getElementById('modal-overlay');
            modal.style.display = 'none';
            document.body.style.overflow = 'auto';
        }

        // Close modal on Escape key
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape') {
                closeModal();
            }
        });

        // Close modal on overlay click
        document.getElementById('modal-overlay').addEventListener('click', function(e) {
            if (e.target.id === 'modal-overlay') {
                closeModal();
            }
        });
    </script>

    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-python.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-json.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-bash.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-markdown.min.js"></script>
</body>
</html>
"""

    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8", errors="surrogatepass") as f:
        f.write(html)

    print(f"HTML report generated: {output_file}")
    print(f"Open in browser: file:///{output_file.as_posix()}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python html_report_generator.py <recording_file.json> [output_file.html]")
        print("ASCII-safe console output (no Unicode checkmarks)")
        sys.exit(1)

    recording_file = Path(sys.argv[1])

    if len(sys.argv) >= 3:
        output_file = Path(sys.argv[2])
    else:
        output_file = recording_file.with_suffix(".html")

    generate_html_report(recording_file, output_file)
