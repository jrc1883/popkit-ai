#!/usr/bin/env python3
"""
HTML Report Generator for Session Recordings

Generates interactive HTML forensics reports with:
- Collapsible event sections
- Decision flow visualization
- Context file tracking
- Recommendation scoring
- Command compliance verification
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


def generate_html_report(recording_file: Path, output_file: Path) -> None:
    """Generate interactive HTML report from recording file."""

    # Load recording data
    with open(recording_file) as f:
        data = json.load(f)

    session_id = data.get('session_id', 'unknown')
    events = data.get('events', [])

    # Analyze events by type
    tool_calls = [e for e in events if e.get('type') == 'tool_call']
    file_reads = [e for e in events if e.get('type') == 'file_read']
    reasoning_steps = [e for e in events if e.get('type') == 'reasoning']
    recommendations = [e for e in events if e.get('type') == 'recommendation']
    decisions = [e for e in events if e.get('type') == 'decision']

    # Calculate stats
    total_duration = sum(e.get('duration_ms', 0) for e in tool_calls)
    error_count = sum(1 for e in tool_calls if e.get('error'))
    success_rate = ((len(tool_calls) - error_count) / len(tool_calls) * 100) if tool_calls else 100

    # Generate HTML
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PopKit Recording: {session_id}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: white;
            font-size: 28px;
            margin-bottom: 10px;
        }}
        .header .meta {{
            color: rgba(255,255,255,0.8);
            font-size: 14px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #2d2d2d;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .stat-card .label {{
            color: #888;
            font-size: 12px;
            text-transform: uppercase;
            margin-bottom: 8px;
        }}
        .stat-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
        }}
        .section {{
            background: #2d2d2d;
            padding: 25px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .section h2 {{
            color: #667eea;
            margin-bottom: 20px;
            font-size: 20px;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .section h2:hover {{
            color: #764ba2;
        }}
        .section h2::after {{
            content: "▼";
            font-size: 14px;
            transition: transform 0.3s;
        }}
        .section.collapsed h2::after {{
            transform: rotate(-90deg);
        }}
        .section-content {{
            max-height: 2000px;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }}
        .section.collapsed .section-content {{
            max-height: 0;
        }}
        .event-flow {{
            position: relative;
            padding-left: 40px;
        }}
        .event-flow::before {{
            content: '';
            position: absolute;
            left: 15px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: linear-gradient(180deg, #667eea, #764ba2);
        }}
        .event-item {{
            position: relative;
            margin-bottom: 30px;
            padding: 15px;
            background: #383838;
            border-radius: 6px;
        }}
        .event-item::before {{
            content: '';
            position: absolute;
            left: -32px;
            top: 20px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #667eea;
            border: 3px solid #2d2d2d;
        }}
        .event-type {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            text-transform: uppercase;
            font-weight: bold;
            margin-bottom: 8px;
        }}
        .type-tool_call {{ background: #4ec9b0; color: #000; }}
        .type-reasoning {{ background: #dcdcaa; color: #000; }}
        .type-file_read {{ background: #c586c0; color: #000; }}
        .type-recommendation {{ background: #f48771; color: #000; }}
        .type-decision {{ background: #569cd6; color: #000; }}
        .event-details {{
            margin-top: 10px;
            font-size: 14px;
            line-height: 1.6;
        }}
        .context-file {{
            display: inline-block;
            padding: 2px 6px;
            background: #c586c0;
            color: #000;
            border-radius: 3px;
            font-family: monospace;
            font-size: 12px;
            margin-right: 5px;
        }}
        .priority-badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }}
        .priority-high {{ background: #f48771; color: #000; }}
        .priority-medium {{ background: #dcdcaa; color: #000; }}
        .priority-low {{ background: #569cd6; color: #000; }}
        .duration-bar {{
            background: #383838;
            height: 20px;
            border-radius: 4px;
            overflow: hidden;
            position: relative;
            margin-top: 8px;
        }}
        .duration-fill {{
            background: linear-gradient(90deg, #667eea, #764ba2);
            height: 100%;
            transition: width 0.3s ease;
        }}
        .collapsible {{
            cursor: pointer;
            background: #383838;
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            border-left: 3px solid #667eea;
        }}
        .collapsible:hover {{
            background: #444;
        }}
        .collapsible-content {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease;
            background: #2a2a2a;
            margin-top: 5px;
            border-radius: 4px;
        }}
        .collapsible-content.active {{
            max-height: 1000px;
            padding: 15px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📹 PopKit Command Recording</h1>
        <div class="meta">
            Session ID: {session_id} | Recorded: {recording_file.name}
        </div>
    </div>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="label">Total Events</div>
            <div class="value">{len(events)}</div>
        </div>
        <div class="stat-card">
            <div class="label">Tool Calls</div>
            <div class="value">{len(tool_calls)}</div>
        </div>
        <div class="stat-card">
            <div class="label">Total Duration</div>
            <div class="value">{total_duration/1000:.1f}<span style="font-size: 16px; color: #888;">s</span></div>
        </div>
        <div class="stat-card">
            <div class="label">Success Rate</div>
            <div class="value">{success_rate:.0f}<span style="font-size: 16px; color: #888;">%</span></div>
        </div>
    </div>
'''

    # Context Files Section
    if file_reads:
        html += f'''
    <div class="section">
        <h2>📂 Context Files Read ({len(file_reads)})</h2>
        <div class="section-content">
'''
        for fr in file_reads:
            file_path = fr.get('file_path', 'unknown')
            summary = fr.get('content_summary', 'No summary')
            relevant = fr.get('relevant', True)
            relevance_badge = '✓ Relevant' if relevant else '✗ Skipped'

            html += f'''
            <div class="event-item">
                <span class="context-file">{file_path}</span>
                <span style="color: {'#4ec9b0' if relevant else '#888'}; margin-left: 10px;">{relevance_badge}</span>
                <div class="event-details">{summary}</div>
            </div>
'''
        html += '''
        </div>
    </div>
'''

    # Decision Flow Section
    html += f'''
    <div class="section">
        <h2>🧠 Decision Flow ({len(reasoning_steps)} steps, {len(recommendations)} recommendations)</h2>
        <div class="section-content">
            <div class="event-flow">
'''

    # Combine reasoning, recommendations, and decisions in chronological order
    flow_events = sorted(
        reasoning_steps + recommendations + decisions,
        key=lambda e: e.get('sequence', 0)
    )

    for event in flow_events:
        event_type = event.get('type', 'unknown')

        if event_type == 'reasoning':
            step = event.get('step', 'Unknown step')
            reasoning = event.get('reasoning', '')
            data = event.get('data', {})

            html += f'''
                <div class="event-item">
                    <span class="event-type type-reasoning">REASONING</span>
                    <div class="event-details">
                        <strong>{step}</strong><br>
                        {reasoning}
                        {f'<pre style="margin-top: 10px; color: #888;">{json.dumps(data, indent=2)}</pre>' if data else ''}
                    </div>
                </div>
'''

        elif event_type == 'recommendation':
            command = event.get('command', 'Unknown command')
            score = event.get('priority_score', 0)
            reason = event.get('reason', '')

            # Determine priority level
            if score >= 80:
                priority = 'high'
            elif score >= 50:
                priority = 'medium'
            else:
                priority = 'low'

            html += f'''
                <div class="event-item">
                    <span class="event-type type-recommendation">RECOMMENDATION</span>
                    <span class="priority-badge priority-{priority}">Priority: {score}</span>
                    <div class="event-details">
                        <code style="background: #383838; padding: 3px 6px; border-radius: 3px;">{command}</code><br>
                        {reason}
                    </div>
                </div>
'''

    html += '''
            </div>
        </div>
    </div>
'''

    # Tool Calls Timeline
    html += f'''
    <div class="section">
        <h2>⚙️ Tool Execution Timeline ({len(tool_calls)} calls)</h2>
        <div class="section-content">
            <div class="event-flow">
'''

    max_duration = max((e.get('duration_ms', 0) for e in tool_calls), default=1)

    for i, tc in enumerate(tool_calls, 1):
        tool_name = tc.get('tool_name', 'Unknown')
        params = tc.get('parameters', {})
        duration = tc.get('duration_ms', 0)
        error = tc.get('error')
        status = 'ERROR' if error else 'OK'
        status_color = '#f48771' if error else '#4ec9b0'

        # Calculate progress bar width
        bar_width = (duration / max_duration * 100) if max_duration > 0 else 0

        html += f'''
                <div class="event-item">
                    <span class="event-type type-tool_call">{tool_name}</span>
                    <span style="color: {status_color}; font-weight: bold; margin-left: 10px;">{status}</span>
                    <div class="event-details">
                        <strong>Duration:</strong> {duration}ms
                        <div class="duration-bar">
                            <div class="duration-fill" style="width: {bar_width}%;"></div>
                        </div>
                        <div class="collapsible" onclick="toggleCollapsible(this)">
                            📋 Parameters & Result (click to expand)
                        </div>
                        <div class="collapsible-content">
                            <strong>Parameters:</strong>
                            <pre>{json.dumps(params, indent=2)}</pre>
                            {'<strong style="color: #f48771;">Error:</strong><br>' + error if error else ''}
                        </div>
                    </div>
                </div>
'''

    html += '''
            </div>
        </div>
    </div>
'''

    # JavaScript for interactivity
    html += '''
    <script>
        // Toggle sections
        document.querySelectorAll('.section h2').forEach(header => {
            header.addEventListener('click', function() {
                this.parentElement.classList.toggle('collapsed');
            });
        });

        // Toggle collapsible content
        function toggleCollapsible(element) {
            const content = element.nextElementSibling;
            content.classList.toggle('active');
        }

        // Add copy-to-clipboard for session ID
        document.querySelector('.header .meta').style.cursor = 'pointer';
        document.querySelector('.header .meta').addEventListener('click', function() {
            const sessionId = this.textContent.match(/Session ID: ([^ ]+)/)[1];
            navigator.clipboard.writeText(sessionId);
            alert('Session ID copied to clipboard!');
        });
    </script>
</body>
</html>
'''

    # Write HTML file (UTF-8 encoding for Windows compatibility)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(html, encoding='utf-8')


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python html_report_generator.py <recording.json> [output.html]")
        sys.exit(1)

    recording_file = Path(sys.argv[1])
    output_file = Path(sys.argv[2]) if len(sys.argv) > 2 else recording_file.with_suffix('.html')

    generate_html_report(recording_file, output_file)
    print(f"HTML report generated: {output_file}")
    print(f"Open in browser: file://{output_file.absolute()}")
