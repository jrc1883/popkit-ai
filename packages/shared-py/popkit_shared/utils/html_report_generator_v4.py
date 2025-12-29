#!/usr/bin/env python3
"""
HTML Report Generator V4 for Session Recordings

Fully Unified Timeline Approach:
- Merges main session events + all sub-agent messages chronologically
- Color-coded attribution (main vs each sub-agent)
- Shows complete execution flow in one timeline
- Detects orphaned sub-agent completions (launch missing)
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


def parse_timestamp(ts_str: str) -> datetime:
    """Parse ISO timestamp with optional timezone, return timezone-naive local time."""
    if not ts_str or ts_str == 'N/A':
        return datetime.min
    try:
        # Try with timezone
        dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        if dt.tzinfo:
            # Convert UTC to local time, then strip timezone
            return dt.astimezone().replace(tzinfo=None)
        return dt
    except:
        try:
            # Try without timezone (already local)
            return datetime.fromisoformat(ts_str)
        except:
            return datetime.min


def format_duration(duration_ms: Optional[int]) -> str:
    """Format duration safely, handling None values."""
    if duration_ms is None:
        return 'N/A'
    if duration_ms == 0:
        return '<1ms'
    if duration_ms >= 1000:
        return f'{duration_ms/1000:.1f}s'
    return f'{duration_ms}ms'


def truncate_text(text: str, max_len: int = 80) -> str:
    """Truncate text with ellipsis."""
    if len(text) <= max_len:
        return text
    return text[:max_len] + '...'


def format_params_inline(params: Dict[str, Any]) -> str:
    """Format key parameters for inline display."""
    if not params:
        return '<em>none</em>'

    # Show most relevant params
    key_params = []
    if 'command' in params:
        key_params.append(f"cmd: {truncate_text(params['command'], 60)}")
    if 'file_path' in params:
        key_params.append(f"file: {Path(params['file_path']).name}")
    if 'subagent_type' in params:
        key_params.append(f"agent: {params['subagent_type']}")
    if 'description' in params:
        key_params.append(f"desc: {truncate_text(params['description'], 50)}")
    if 'pattern' in params:
        key_params.append(f"pattern: {truncate_text(params['pattern'], 40)}")

    if not key_params:
        # Fallback: show first param
        first_key = list(params.keys())[0]
        value = str(params[first_key])
        key_params.append(f"{first_key}: {truncate_text(value, 50)}")

    return '<br>'.join(key_params)


def parse_agent_transcripts(claude_dir: Path, subagent_stops: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Parse all sub-agent JSONL transcripts and convert to unified event format.

    Returns: {agent_id: [events]}
    """
    transcripts = {}

    for sa in subagent_stops:
        agent_id = sa.get('agent_id', 'unknown')

        # Find transcript file
        transcript_file = None
        for project_dir in claude_dir.glob('*'):
            candidate = project_dir / f'agent-{agent_id}.jsonl'
            if candidate.exists():
                transcript_file = candidate
                break

        if not transcript_file:
            continue

        # Parse JSONL into unified events
        events = []
        try:
            with open(transcript_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        entry = json.loads(line)
                        timestamp = entry.get('timestamp', '')
                        msg = entry.get('message', {})
                        msg_type = entry.get('type', 'unknown')

                        # Create event based on message type
                        if msg_type == 'user':
                            # User prompt to sub-agent
                            content = msg.get('content', '')
                            events.append({
                                'agent_id': agent_id,
                                'timestamp': timestamp,
                                'parsed_timestamp': parse_timestamp(timestamp),
                                'type': 'subagent_user_message',
                                'content': content if isinstance(content, str) else str(content)
                            })

                        elif msg_type == 'assistant':
                            # Assistant response (may contain text + tool calls)
                            content = msg.get('content', [])
                            if not isinstance(content, list):
                                content = [{'type': 'text', 'text': str(content)}]

                            for item in content:
                                if item.get('type') == 'text':
                                    events.append({
                                        'agent_id': agent_id,
                                        'timestamp': timestamp,
                                        'parsed_timestamp': parse_timestamp(timestamp),
                                        'type': 'subagent_text',
                                        'text': item.get('text', '')
                                    })
                                elif item.get('type') == 'tool_use':
                                    events.append({
                                        'agent_id': agent_id,
                                        'timestamp': timestamp,
                                        'parsed_timestamp': parse_timestamp(timestamp),
                                        'type': 'subagent_tool_call',
                                        'tool_name': item.get('name'),
                                        'parameters': item.get('input', {})
                                    })

                        elif msg_type == 'user' and isinstance(msg.get('content'), list):
                            # Tool results
                            for item in msg.get('content', []):
                                if item.get('type') == 'tool_result':
                                    events.append({
                                        'agent_id': agent_id,
                                        'timestamp': timestamp,
                                        'parsed_timestamp': parse_timestamp(timestamp),
                                        'type': 'subagent_tool_result',
                                        'tool_use_id': item.get('tool_use_id'),
                                        'success': not item.get('is_error', False)
                                    })

                    except json.JSONDecodeError:
                        continue

        except Exception as e:
            print(f"Warning: Failed to parse transcript for {agent_id}: {e}")
            continue

        transcripts[agent_id] = events

    return transcripts


def build_unified_timeline(main_events: List[Dict], transcripts: Dict[str, List[Dict]]) -> List[Dict]:
    """
    Merge main session events with sub-agent events into one chronological timeline.

    Each event gets 'source' field: 'main' or agent_id
    """
    unified = []

    # Add main events
    for event in main_events:
        event['source'] = 'main'
        unified.append(event)

    # Add sub-agent events
    for agent_id, events in transcripts.items():
        unified.extend(events)

    # Sort by timestamp
    unified.sort(key=lambda e: e.get('parsed_timestamp', datetime.min))

    return unified


def detect_orphaned_completions(events: List[Dict]) -> List[str]:
    """
    Detect SubagentStop events that have no corresponding Task launch.
    Returns list of orphaned agent IDs.
    """
    launched = set()
    completed = set()

    for event in events:
        if event.get('type') == 'tool_call':
            params = event.get('parameters', {})
            # This is a hack - we don't know agent ID yet
            # Better approach: SubagentStart hook would record agent_id
            pass
        elif event.get('type') == 'subagent_stop':
            completed.add(event.get('agent_id'))

    # For now, just return completions that appear BEFORE any Task launch
    orphaned = []
    first_launch_time = None

    for event in events:
        if event.get('type') == 'tool_call' and 'subagent_type' in event.get('parameters', {}):
            first_launch_time = event.get('parsed_timestamp')
            break

    if first_launch_time:
        for event in events:
            if event.get('type') == 'subagent_stop':
                if event.get('parsed_timestamp') < first_launch_time:
                    orphaned.append(event.get('agent_id'))

    return orphaned


def get_agent_color(source: str) -> Tuple[str, str]:
    """
    Get color scheme for agent attribution.
    Returns (background_color, border_color)
    """
    if source == 'main':
        return '#1e3a5f', '#58a6ff'  # Dark blue bg, light blue border

    # Hash agent ID to consistent color
    colors = [
        ('#3d1e5f', '#a371f7'),  # Purple
        ('#1e5f3d', '#3fb950'),  # Green
        ('#5f3d1e', '#ff9b5e'),  # Orange
        ('#5f1e3d', '#ff6b9d'),  # Pink
        ('#1e5f5f', '#5ed9ff'),  # Cyan
    ]

    hash_val = sum(ord(c) for c in source) % len(colors)
    return colors[hash_val]


def generate_html_report(recording_file: Path, output_file: Path) -> None:
    """Generate fully unified HTML report from recording file."""

    # Load recording data
    with open(recording_file) as f:
        data = json.load(f)

    session_id = data.get('session_id', 'unknown')
    events = data.get('events', [])

    # Parse timestamps
    for event in events:
        event['parsed_timestamp'] = parse_timestamp(event.get('timestamp', ''))

    # Get sub-agent transcripts
    claude_dir = Path.home() / '.claude' / 'projects'
    subagent_stops = [e for e in events if e.get('type') == 'subagent_stop']
    transcripts = parse_agent_transcripts(claude_dir, subagent_stops)

    # Build unified timeline
    unified_timeline = build_unified_timeline(events, transcripts)

    # Detect issues
    orphaned = detect_orphaned_completions(events)

    # Calculate stats
    tool_calls = [e for e in events if e.get('type') == 'tool_call']
    total_duration = sum(e.get('duration_ms') or 0 for e in tool_calls)
    error_count = sum(1 for e in tool_calls if e.get('error'))
    success_rate = ((len(tool_calls) - error_count) / len(tool_calls) * 100) if tool_calls else 100

    # Generate HTML
    html = f'''<!DOCTYPE html>
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
            max-width: 1800px;
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

        /* Warning Banner */
        .warning-banner {{
            background: #5f3d1e;
            border-left: 4px solid #ff9b5e;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }}
        .warning-banner strong {{
            color: #ff9b5e;
        }}

        /* Unified Timeline */
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
        .timeline-scroll {{
            max-height: 1000px;
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

        /* Agent Attribution Badge */
        .agent-badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: 600;
            font-family: 'Consolas', monospace;
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
        .event-session {{ background: #6e7681; color: #fff; }}
        .event-tool {{ background: #238636; color: #fff; }}
        .event-subagent-launch {{ background: #1f6feb; color: #fff; }}
        .event-subagent-stop {{ background: #8b5cf6; color: #fff; }}
        .event-subagent-prompt {{ background: #5f3d1e; color: #fff; }}
        .event-subagent-text {{ background: #3d1e5f; color: #fff; }}
        .event-subagent-tool {{ background: #1e5f3d; color: #fff; }}
        .event-subagent-result {{ background: #1e5f5f; color: #fff; }}

        /* Status */
        .status-ok {{ color: #3fb950; font-weight: 600; }}
        .status-error {{ color: #f85149; font-weight: 600; }}
        .status-na {{ color: #8b949e; }}

        /* Tool names */
        .tool-name {{
            font-family: 'Consolas', monospace;
            color: #79c0ff;
            font-size: 13px;
        }}

        /* Expandable details */
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
                <div class="value">{len(unified_timeline)}</div>
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
                <div class="value">{total_duration/1000:.1f}<span style="font-size: 14px; color: #8b949e;">s</span></div>
            </div>
            <div class="stat-card">
                <div class="label">Success Rate</div>
                <div class="value">{success_rate:.0f}<span style="font-size: 14px; color: #8b949e;">%</span></div>
            </div>
            <div class="stat-card">
                <div class="label">Transcripts Found</div>
                <div class="value">{len(transcripts)}/{len(subagent_stops)}</div>
            </div>
        </div>
'''

    # Show warning for orphaned completions
    if orphaned:
        html += f'''
        <div class="warning-banner">
            <strong>⚠️ Warning:</strong> Found {len(orphaned)} sub-agent completion(s) without launch events: {', '.join(orphaned)}<br>
            <small>This usually means recording started after these agents were launched.</small>
        </div>
'''

    html += f'''
        <div class="timeline-section">
            <h2>🌐 Unified Timeline ({len(unified_timeline)} events across all agents)</h2>
            <div class="timeline-scroll">
                <table class="timeline-table">
                    <thead>
                        <tr>
                            <th style="width: 40px;">#</th>
                            <th style="width: 80px;">Time</th>
                            <th style="width: 100px;">Agent</th>
                            <th style="width: 150px;">Event Type</th>
                            <th>Description</th>
                            <th style="width: 100px;">Status</th>
                        </tr>
                    </thead>
                    <tbody>
'''

    # Generate unified timeline rows
    for i, event in enumerate(unified_timeline, 1):
        timestamp = event.get('timestamp', 'N/A')
        source = event.get('source', event.get('agent_id', 'unknown'))
        event_type = event.get('type', 'unknown')

        # Format timestamp
        try:
            dt = parse_timestamp(timestamp)
            time_str = dt.strftime('%H:%M:%S') if dt != datetime.min else 'N/A'
        except:
            time_str = 'N/A'

        # Agent attribution badge
        bg_color, border_color = get_agent_color(source)
        agent_label = 'MAIN' if source == 'main' else source[:7]
        agent_badge = f'<span class="agent-badge" style="background: {bg_color}; color: {border_color}; border: 1px solid {border_color};">{agent_label}</span>'

        # Event-specific rendering
        desc_html = ''
        status_html = '<span class="status-ok">✓ OK</span>'
        badge_html = ''

        if event_type == 'session_start':
            badge_html = '<span class="event-badge event-session">Session Start</span>'
            desc_html = 'Recording session initiated'

        elif event_type == 'tool_call':
            tool_name = event.get('tool_name', 'Unknown')
            params = event.get('parameters', {})
            error = event.get('error')
            duration = event.get('duration_ms')

            is_subagent_launch = 'subagent_type' in params
            if is_subagent_launch:
                badge_html = '<span class="event-badge event-subagent-launch">Sub-Agent Launch</span>'
                desc_html = f'<span class="tool-name">Task</span> → {params.get("subagent_type", "unknown")}<br><small style="color: #8b949e;">{truncate_text(params.get("description", ""), 80)}</small>'
            else:
                badge_html = '<span class="event-badge event-tool">Tool Call</span>'
                desc_html = f'<span class="tool-name">{tool_name}</span><br><small style="color: #8b949e;">{format_params_inline(params)}</small>'

            status_html = '<span class="status-error">✗ ERROR</span>' if error else f'<span class="status-ok">✓ {format_duration(duration)}</span>'

            # Details toggle
            details_id = f'details-{i}'
            desc_html += f'''
                <div class="details-toggle" onclick="toggleDetails('{details_id}')">⚙ View Full Event</div>
                <div id="{details_id}" class="details-content">
                    <strong>Parameters:</strong>
                    <pre>{json.dumps(params, indent=2)}</pre>
                    {f'<strong style="color: #f85149;">Error:</strong><pre>{json.dumps(error, indent=2) if isinstance(error, dict) else error}</pre>' if error else ''}
                </div>
            '''

        elif event_type == 'tool_call_start':
            # Tool call START (from pre-tool-use hook)
            tool_name = event.get('tool_name', 'Unknown')
            params = event.get('parameters', {})

            is_subagent_launch = 'subagent_type' in params
            if is_subagent_launch:
                badge_html = '<span class="event-badge event-subagent-launch">Sub-Agent Launch</span>'
                desc_html = f'<span class="tool-name">Task</span> → {params.get("subagent_type", "unknown")}<br><small style="color: #8b949e;">{truncate_text(params.get("description", ""), 80)}</small>'
            else:
                badge_html = '<span class="event-badge event-tool">Tool Start</span>'
                desc_html = f'<span class="tool-name">{tool_name}</span><br><small style="color: #8b949e;">{format_params_inline(params)}</small>'

            status_html = '<span class="status-na">⏳ Running</span>'

            # Details toggle
            details_id = f'details-{i}'
            desc_html += f'''
                <div class="details-toggle" onclick="toggleDetails('{details_id}')">⚙ View Parameters</div>
                <div id="{details_id}" class="details-content">
                    <strong>Parameters:</strong>
                    <pre>{json.dumps(params, indent=2)}</pre>
                </div>
            '''

        elif event_type == 'tool_call_complete':
            # Tool call COMPLETE (from post-tool-use hook)
            tool_name = event.get('tool_name', 'Unknown')
            error = event.get('error')
            duration = event.get('duration_ms')

            badge_html = '<span class="event-badge event-tool">Tool Complete</span>'
            desc_html = f'<span class="tool-name">{tool_name}</span> finished'
            status_html = '<span class="status-error">✗ ERROR</span>' if error else f'<span class="status-ok">✓ {format_duration(duration)}</span>'

            # Details toggle
            details_id = f'details-{i}'
            result = event.get('result', '')
            desc_html += f'''
                <div class="details-toggle" onclick="toggleDetails('{details_id}')">📄 View Result</div>
                <div id="{details_id}" class="details-content">
                    <strong>Result:</strong>
                    <pre>{truncate_text(str(result), 500)}</pre>
                    {f'<strong style="color: #f85149;">Error:</strong><pre>{error}</pre>' if error else ''}
                    <strong>Duration:</strong> {format_duration(duration)}
                </div>
            '''

        elif event_type == 'subagent_stop':
            agent_id = event.get('agent_id', 'unknown')
            badge_html = '<span class="event-badge event-subagent-stop">Sub-Agent Complete</span>'
            desc_html = f'Agent <strong>{agent_id}</strong> completed'
            if agent_id in orphaned:
                desc_html += '<br><span style="color: #ff9b5e;">⚠️ Launch not recorded (orphaned)</span>'

        elif event_type == 'subagent_user_message':
            badge_html = '<span class="event-badge event-subagent-prompt">User Prompt</span>'
            content = event.get('content', '')
            desc_html = f'<small style="color: #8b949e;">{truncate_text(content, 100)}</small>'

        elif event_type == 'subagent_text':
            badge_html = '<span class="event-badge event-subagent-text">Assistant Text</span>'
            text = event.get('text', '')
            desc_html = f'<small style="color: #8b949e;">{truncate_text(text, 100)}</small>'

        elif event_type == 'subagent_tool_call':
            badge_html = '<span class="event-badge event-subagent-tool">Tool Call</span>'
            tool_name = event.get('tool_name', 'Unknown')
            params = event.get('parameters', {})
            desc_html = f'<span class="tool-name">{tool_name}</span><br><small style="color: #8b949e;">{format_params_inline(params)}</small>'

        elif event_type == 'subagent_tool_result':
            badge_html = '<span class="event-badge event-subagent-result">Tool Result</span>'
            success = event.get('success', True)
            desc_html = '<small style="color: #3fb950;">Success</small>' if success else '<small style="color: #f85149;">Error</small>'

        else:
            badge_html = f'<span class="event-badge" style="background: #6e7681; color: #fff;">{event_type}</span>'
            desc_html = '<em>Unknown event</em>'

        html += f'''
                    <tr>
                        <td>{i}</td>
                        <td>{time_str}</td>
                        <td>{agent_badge}</td>
                        <td>{badge_html}</td>
                        <td>{desc_html}</td>
                        <td>{status_html}</td>
                    </tr>
'''

    html += '''
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
'''

    # Write HTML file
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'HTML report generated: {output_file}')
    print(f'Open in browser: file:///{output_file.as_posix()}')


if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print('Usage: python html_report_generator_v4.py <recording.json> <output.html>')
        sys.exit(1)

    recording_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2])

    generate_html_report(recording_file, output_file)
