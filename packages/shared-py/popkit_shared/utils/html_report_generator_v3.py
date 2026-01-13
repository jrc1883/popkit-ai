#!/usr/bin/env python3
"""
HTML Report Generator V3 for Session Recordings

Enhanced with:
- Sub-agent transcript parsing and display
- Fixed "Nonems" duration bug
- Inline parameter display
- Attribution of tool calls to agents
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


def parse_timestamp(ts_str: str) -> datetime:
    """Parse ISO timestamp with optional timezone, return timezone-naive."""
    if not ts_str or ts_str == "N/A":
        return datetime.min
    try:
        # Try with timezone
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        # Convert to naive datetime for consistent comparison
        return dt.replace(tzinfo=None) if dt.tzinfo else dt
    except:
        try:
            # Try without timezone
            return datetime.fromisoformat(ts_str)
        except:
            return datetime.min


def parse_agent_transcript(transcript_path: Path) -> Dict[str, Any]:
    """Parse JSONL agent transcript file."""
    if not transcript_path.exists():
        return {"messages": [], "tool_calls": [], "error": "File not found"}

    messages = []
    tool_calls = []

    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                    msg = entry.get("message", {})

                    # Track message
                    messages.append(
                        {
                            "type": entry.get("type"),
                            "timestamp": entry.get("timestamp"),
                            "content": msg.get("content", [])
                            if isinstance(msg.get("content"), list)
                            else [{"type": "text", "text": str(msg.get("content", ""))}],
                        }
                    )

                    # Extract tool calls from assistant messages
                    if entry.get("type") == "assistant" and isinstance(msg.get("content"), list):
                        for item in msg["content"]:
                            if item.get("type") == "tool_use":
                                tool_calls.append(
                                    {
                                        "name": item.get("name"),
                                        "input": item.get("input", {}),
                                        "timestamp": entry.get("timestamp"),
                                    }
                                )
                except json.JSONDecodeError:
                    continue

        return {
            "messages": messages,
            "tool_calls": tool_calls,
            "message_count": len(messages),
            "tool_call_count": len(tool_calls),
        }
    except Exception as e:
        return {"messages": [], "tool_calls": [], "error": str(e)}


def format_duration(duration_ms: Optional[int]) -> str:
    """Format duration safely, handling None values."""
    if duration_ms is None:
        return "N/A"
    if duration_ms == 0:
        return "<1ms"
    if duration_ms >= 1000:
        return f"{duration_ms / 1000:.1f}s"
    return f"{duration_ms}ms"


def truncate_text(text: str, max_len: int = 80) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "..."


def format_params_inline(params: Dict[str, Any]) -> str:
    """Format key parameters for inline display."""
    if not params:
        return "<em>none</em>"

    # Show most relevant params
    key_params = []
    if "command" in params:
        key_params.append(f"cmd: {truncate_text(params['command'], 60)}")
    if "file_path" in params:
        key_params.append(f"file: {Path(params['file_path']).name}")
    if "subagent_type" in params:
        key_params.append(f"agent: {params['subagent_type']}")
    if "description" in params:
        key_params.append(f"desc: {truncate_text(params['description'], 50)}")
    if "pattern" in params:
        key_params.append(f"pattern: {truncate_text(params['pattern'], 40)}")

    if not key_params:
        # Fallback: show first param
        first_key = list(params.keys())[0]
        value = str(params[first_key])
        key_params.append(f"{first_key}: {truncate_text(value, 50)}")

    return "<br>".join(key_params)


def generate_html_report(recording_file: Path, output_file: Path) -> None:
    """Generate interactive HTML report from recording file."""

    # Load recording data
    with open(recording_file) as f:
        data = json.load(f)

    session_id = data.get("session_id", "unknown")
    events = data.get("events", [])

    # Sort all events chronologically
    for event in events:
        event["_parsed_timestamp"] = parse_timestamp(event.get("timestamp", ""))

    sorted_events = sorted(events, key=lambda e: e["_parsed_timestamp"])

    # Calculate stats
    tool_calls = [e for e in events if e.get("type") == "tool_call"]
    subagent_stops = [e for e in events if e.get("type") == "subagent_stop"]

    total_duration = sum(e.get("duration_ms") or 0 for e in tool_calls)
    error_count = sum(1 for e in tool_calls if e.get("error"))
    success_rate = ((len(tool_calls) - error_count) / len(tool_calls) * 100) if tool_calls else 100

    # Build sub-agent mapping (which Task tool call launched which sub-agent)
    subagent_map = {}
    for i, event in enumerate(sorted_events):
        if event.get("type") == "tool_call":
            params = event.get("parameters", {})
            if "subagent_type" in params:
                # This Task tool call will be followed by a subagent_stop
                # Find the next subagent_stop event
                for j in range(i + 1, len(sorted_events)):
                    if sorted_events[j].get("type") == "subagent_stop":
                        agent_id = sorted_events[j].get("agent_id")
                        subagent_map[agent_id] = {
                            "task_index": i,
                            "subagent_type": params.get("subagent_type"),
                            "description": params.get("description", ""),
                        }
                        break

    # Parse sub-agent transcripts
    claude_dir = Path.home() / ".claude" / "projects"

    subagent_transcripts = {}
    for sa in subagent_stops:
        agent_id = sa.get("agent_id", "unknown")

        # Try to find transcript file
        # Pattern: agent-{id}.jsonl
        transcript_file = None

        # Search in .claude/projects/
        for project_dir in claude_dir.glob("*"):
            candidate = project_dir / f"agent-{agent_id}.jsonl"
            if candidate.exists():
                transcript_file = candidate
                break

        if transcript_file:
            subagent_transcripts[agent_id] = parse_agent_transcript(transcript_file)

    # Total observable events (main + ALL sub-agent messages)
    total_observable = len(sorted_events) + sum(
        t.get("message_count", 0) for t in subagent_transcripts.values()
    )

    # Generate HTML
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PopKit Session: {session_id}</title>
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
            max-width: 1600px;
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
        .header .meta {{
            color: rgba(255,255,255,0.9);
            font-size: 13px;
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

        /* Unified Timeline Table */
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
            max-height: 800px;
            overflow-y: auto;
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
        .timeline-scroll::-webkit-scrollbar-thumb:hover {{
            background: #484f58;
        }}
        .timeline-table {{
            width: 100%;
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
        }}
        .timeline-table tr:hover {{
            background: #1c2128;
        }}

        /* Event Type Badges */
        .event-badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        .event-tool {{ background: #238636; color: #fff; }}
        .event-subagent-launch {{ background: #1f6feb; color: #fff; }}
        .event-subagent-stop {{ background: #8b5cf6; color: #fff; }}
        .event-session {{ background: #6e7681; color: #fff; }}

        /* Status Badges */
        .status-ok {{ color: #3fb950; font-weight: 600; }}
        .status-error {{ color: #f85149; font-weight: 600; }}
        .status-na {{ color: #8b949e; }}

        /* Tool Names */
        .tool-name {{
            font-family: 'Consolas', monospace;
            color: #79c0ff;
            font-size: 13px;
        }}

        /* Agent Links */
        .agent-link {{
            color: #a371f7;
            font-family: 'Consolas', monospace;
            font-size: 12px;
        }}

        /* Expandable Details */
        .details-toggle {{
            color: #58a6ff;
            cursor: pointer;
            font-size: 11px;
            margin-top: 6px;
            display: inline-block;
        }}
        .details-toggle:hover {{
            text-decoration: underline;
        }}
        .details-content {{
            display: none;
            margin-top: 10px;
            padding: 12px;
            background: #0d1117;
            border-radius: 6px;
            border: 1px solid #30363d;
        }}
        .details-content.active {{
            display: block;
        }}
        .details-content pre {{
            font-size: 11px;
            color: #8b949e;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}

        /* Relationship Indicator */
        .relationship {{
            color: #6e7681;
            font-size: 11px;
            font-style: italic;
        }}

        /* Sub-Agent Transcript Section */
        .transcript-section {{
            background: #161b22;
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 20px;
        }}
        .transcript-header {{
            padding: 15px;
            background: #21262d;
            border-bottom: 1px solid #30363d;
        }}
        .transcript-header h3 {{
            color: #c9d1d9;
            font-size: 14px;
            margin-bottom: 5px;
        }}
        .transcript-stats {{
            color: #8b949e;
            font-size: 12px;
        }}
        .transcript-content {{
            padding: 15px;
            max-height: 400px;
            overflow-y: auto;
        }}
        .message {{
            margin-bottom: 15px;
            padding: 10px;
            background: #0d1117;
            border-radius: 6px;
            border-left: 3px solid #30363d;
        }}
        .message.user {{
            border-left-color: #58a6ff;
        }}
        .message.assistant {{
            border-left-color: #3fb950;
        }}
        .message-type {{
            font-size: 10px;
            color: #8b949e;
            text-transform: uppercase;
            margin-bottom: 5px;
        }}
        .message-content {{
            color: #c9d1d9;
            font-size: 12px;
        }}
        .tool-call-item {{
            margin-top: 8px;
            padding: 8px;
            background: #161b22;
            border-radius: 4px;
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
                <div class="value">{len(sorted_events)}</div>
            </div>
            <div class="stat-card">
                <div class="label">Tool Calls</div>
                <div class="value">{len(tool_calls)}</div>
            </div>
            <div class="stat-card">
                <div class="label">Sub-Agents</div>
                <div class="value">{len(subagent_stops)}</div>
            </div>
            <div class="stat-card">
                <div class="label">Duration</div>
                <div class="value">{total_duration / 1000:.1f}<span style="font-size: 14px; color: #8b949e;">s</span></div>
            </div>
            <div class="stat-card">
                <div class="label">Success Rate</div>
                <div class="value">{success_rate:.0f}<span style="font-size: 14px; color: #8b949e;">%</span></div>
            </div>
            <div class="stat-card">
                <div class="label">Observable Events</div>
                <div class="value">{total_observable}</div>
            </div>
        </div>

        <div class="timeline-section">
            <h2>📋 Main Session Timeline ({len(sorted_events)} events)</h2>
            <div class="timeline-scroll">
                <table class="timeline-table">
                    <thead>
                        <tr>
                            <th style="width: 40px;">#</th>
                            <th style="width: 80px;">Time</th>
                            <th style="width: 150px;">Event Type</th>
                            <th>Description</th>
                            <th style="width: 200px;">Key Parameters</th>
                            <th style="width: 100px;">Status</th>
                        </tr>
                    </thead>
                    <tbody>
"""

    # Generate timeline rows
    for i, event in enumerate(sorted_events, 1):
        event_type = event.get("type", "unknown")
        timestamp = event.get("timestamp", "N/A")

        # Format timestamp
        try:
            dt = parse_timestamp(timestamp)
            time_str = dt.strftime("%H:%M:%S") if dt != datetime.min else "N/A"
        except:
            time_str = "N/A"

        # Generate row based on event type
        if event_type == "session_start":
            html += f"""
                    <tr>
                        <td>{i}</td>
                        <td>{time_str}</td>
                        <td><span class="event-badge event-session">Session Start</span></td>
                        <td>Recording session initiated</td>
                        <td><em>none</em></td>
                        <td><span class="status-ok">✓ OK</span></td>
                    </tr>
"""

        elif event_type == "tool_call":
            tool_name = event.get("tool_name", "Unknown")
            params = event.get("parameters", {})
            error = event.get("error")
            duration = event.get("duration_ms")

            # Check if this is a sub-agent launch
            is_subagent_launch = "subagent_type" in params

            if is_subagent_launch:
                subagent_type = params.get("subagent_type", "unknown")
                description = params.get("description", "")
                badge_html = (
                    '<span class="event-badge event-subagent-launch">Sub-Agent Launch</span>'
                )
                desc_html = f"""
                    <span class="tool-name">Task</span> → <span class="agent-link">{subagent_type}</span>
                """
            else:
                badge_html = '<span class="event-badge event-tool">Tool Call</span>'
                desc_html = f'<span class="tool-name">{tool_name}</span>'

            params_html = format_params_inline(params)
            status_html = (
                '<span class="status-error">✗ ERROR</span>'
                if error
                else f'<span class="status-ok">✓ {format_duration(duration)}</span>'
            )

            # Add details toggle
            details_id = f"details-{i}"
            desc_html += f'''
                <div class="details-toggle" onclick="toggleDetails('{details_id}')">⚙ View Full Event</div>
                <div id="{details_id}" class="details-content">
                    <strong>Parameters:</strong>
                    <pre>{json.dumps(params, indent=2)}</pre>
                    {f'<strong style="color: #f85149;">Error:</strong><pre>{json.dumps(error, indent=2) if isinstance(error, dict) else error}</pre>' if error else ""}
                </div>
            '''

            html += f"""
                    <tr>
                        <td>{i}</td>
                        <td>{time_str}</td>
                        <td>{badge_html}</td>
                        <td>{desc_html}</td>
                        <td style="font-size: 11px; color: #8b949e;">{params_html}</td>
                        <td>{status_html}</td>
                    </tr>
"""

        elif event_type == "subagent_stop":
            agent_id = event.get("agent_id", "unknown")
            transcript_available = event.get("transcript_available", False)

            # Find which Task call launched this
            relationship_html = ""
            if agent_id in subagent_map:
                task_info = subagent_map[agent_id]
                relationship_html = f'<br><span class="relationship">↳ Launched by event #{task_info["task_index"] + 1}</span>'

            # Get transcript info
            transcript_info = subagent_transcripts.get(agent_id, {})
            tool_count = transcript_info.get("tool_call_count", 0)
            msg_count = transcript_info.get("message_count", 0)

            desc_html = f"""
                <span class="agent-link">{agent_id}</span>
                <br><span style="color: #8b949e; font-size: 12px;">
                    Transcript: {"✓ Available" if transcript_available else "✗ Missing"}
                    {f" • {msg_count} messages, {tool_count} tool calls" if transcript_info else ""}
                </span>
                {relationship_html}
            """

            # Add details toggle
            details_id = f"details-{i}"
            event_data = {k: v for k, v in event.items() if k != "_parsed_timestamp"}
            desc_html += f'''
                <div class="details-toggle" onclick="toggleDetails('{details_id}')">📄 View Event Data</div>
                <div id="{details_id}" class="details-content">
                    <strong>Full Event:</strong>
                    <pre>{json.dumps(event_data, indent=2)}</pre>
                </div>
            '''

            html += f"""
                    <tr>
                        <td>{i}</td>
                        <td>{time_str}</td>
                        <td><span class="event-badge event-subagent-stop">Sub-Agent Complete</span></td>
                        <td>{desc_html}</td>
                        <td><em>see transcript below</em></td>
                        <td><span class="status-ok">✓ OK</span></td>
                    </tr>
"""

    html += """
                    </tbody>
                </table>
            </div>
        </div>
"""

    # Add sub-agent transcript sections
    for agent_id, transcript in subagent_transcripts.items():
        if transcript.get("error"):
            continue

        tool_count = transcript.get("tool_call_count", 0)
        msg_count = transcript.get("message_count", 0)

        html += f"""
        <div class="transcript-section">
            <div class="transcript-header">
                <h3>🤖 Sub-Agent Transcript: {agent_id}</h3>
                <div class="transcript-stats">{msg_count} messages • {tool_count} tool calls</div>
            </div>
            <div class="transcript-content">
"""

        # Show all messages
        for msg in transcript.get("messages", []):
            msg_type = msg.get("type", "unknown")
            content = msg.get("content", [])

            html += f"""
                <div class="message {msg_type}">
                    <div class="message-type">{msg_type}</div>
                    <div class="message-content">
"""

            for item in content:
                if item.get("type") == "text":
                    text = item.get("text", "")
                    html += f"<p>{truncate_text(text, 200)}</p>"
                elif item.get("type") == "tool_use":
                    tool_name = item.get("name", "unknown")
                    tool_input = item.get("input", {})
                    html += f"""
                        <div class="tool-call-item">
                            <strong>🔧 {tool_name}</strong>
                            <br><span style="color: #8b949e; font-size: 11px;">{format_params_inline(tool_input)}</span>
                        </div>
"""
                elif item.get("type") == "tool_result":
                    html += """
                        <div class="tool-call-item" style="border-left: 3px solid #3fb950;">
                            <strong>✓ Tool Result</strong>
                            <br><span style="color: #8b949e; font-size: 11px;">Success</span>
                        </div>
"""

            html += """
                    </div>
                </div>
"""

        html += """
            </div>
        </div>
"""

    html += """
    </div>

    <script>
        function toggleDetails(id) {
            const element = document.getElementById(id);
            element.classList.toggle('active');
        }
    </script>
</body>
</html>
"""

    # Write HTML file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"HTML report generated: {output_file}")
    print(f"Open in browser: file:///{output_file.as_posix()}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 3:
        print("Usage: python html_report_generator_v3.py <recording.json> <output.html>")
        sys.exit(1)

    recording_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])

    generate_html_report(recording_file, output_file)
