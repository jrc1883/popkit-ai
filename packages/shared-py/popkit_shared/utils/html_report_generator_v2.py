#!/usr/bin/env python3
"""
HTML Report Generator V2 for Session Recordings

Redesigned for elegant, scannable timeline view with:
- Unified chronological timeline (all events together)
- Table-based compact view (no excessive expanding)
- Causal relationships (tool calls → sub-agents)
- Proper scrolling
- Clean, professional design
"""

import json
from datetime import datetime
from pathlib import Path


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
            max-width: 1400px;
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
        }}
        .timeline-section h2 {{
            padding: 20px;
            font-size: 18px;
            color: #c9d1d9;
            background: #21262d;
            margin: 0;
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
            text-decoration: none;
        }}
        .agent-link:hover {{
            text-decoration: underline;
        }}

        /* Expandable Details */
        .details-toggle {{
            color: #58a6ff;
            cursor: pointer;
            font-size: 12px;
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

        /* Scrollable Container */
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
        </div>

        <div class="timeline-section">
            <h2>📋 Unified Timeline ({len(sorted_events)} events)</h2>
            <div class="timeline-scroll">
                <table class="timeline-table">
                    <thead>
                        <tr>
                            <th style="width: 40px;">#</th>
                            <th style="width: 80px;">Time</th>
                            <th style="width: 150px;">Event Type</th>
                            <th>Description</th>
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
                        <td><span class="status-ok">✓ OK</span></td>
                    </tr>
"""

        elif event_type == "tool_call":
            tool_name = event.get("tool_name", "Unknown")
            params = event.get("parameters", {})
            error = event.get("error")
            duration = event.get("duration_ms", 0)

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
                    <br><span style="color: #8b949e; font-size: 12px;">{description}</span>
                """
            else:
                badge_html = '<span class="event-badge event-tool">Tool Call</span>'
                command = params.get("command", "")
                file_path = params.get("file_path", "")

                if command:
                    desc_text = command[:80] + ("..." if len(command) > 80 else "")
                elif file_path:
                    desc_text = file_path
                else:
                    desc_text = json.dumps(params)[:80]

                desc_html = f'<span class="tool-name">{tool_name}</span>'
                if desc_text:
                    desc_html += (
                        f'<br><span style="color: #8b949e; font-size: 12px;">{desc_text}</span>'
                    )

            status_html = (
                '<span class="status-error">✗ ERROR</span>'
                if error
                else f'<span class="status-ok">✓ {duration}ms</span>'
            )

            # Add details toggle
            details_id = f"details-{i}"
            desc_html += f'''
                <div class="details-toggle" onclick="toggleDetails('{details_id}')">⚙ View Parameters</div>
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

            desc_html = f"""
                <span class="agent-link">{agent_id}</span>
                <br><span style="color: #8b949e; font-size: 12px;">
                    Transcript: {"✓ Available" if transcript_available else "✗ Missing"}
                    {" • <code>agent-" + agent_id + ".jsonl</code>" if transcript_available else ""}
                </span>
                {relationship_html}
            """

            # Add details toggle (filter out internal timestamp field)
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
                        <td><span class="status-ok">✓ OK</span></td>
                    </tr>
"""

    html += """
                    </tbody>
                </table>
            </div>
        </div>
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
        print("Usage: python html_report_generator_v2.py <recording.json> <output.html>")
        sys.exit(1)

    recording_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])

    generate_html_report(recording_file, output_file)
