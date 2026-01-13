#!/usr/bin/env python3
"""
Power Mode Skill - Stop Hook

Purpose: Save power mode execution report when skill completes.
Scope: Skill-scoped (power-mode skill only)
Trigger: Stop
Once: true (runs only once at skill completion)

This hook automatically saves a power mode execution report to document
the multi-agent collaboration session, including insights shared,
agents used, and results achieved.
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path


def load_insights(cwd):
    """Load insights from power mode session."""
    insights_path = Path(cwd) / ".claude" / "popkit" / "insights.json"

    if not insights_path.exists():
        return []

    try:
        with open(insights_path) as f:
            data = json.load(f)
            return data.get("insights", [])
    except:
        return []


def load_power_state(cwd):
    """Load power mode state."""
    state_path = Path(cwd) / ".claude" / "popkit" / "power-state.json"

    if not state_path.exists():
        return None

    try:
        with open(state_path) as f:
            return json.load(f)
    except:
        return None


def aggregate_insights(insights):
    """Aggregate insights by agent and phase."""
    by_agent = {}
    by_phase = {}

    for insight in insights:
        agent = insight.get("agent", "unknown")
        phase = insight.get("phase", "unknown")

        # By agent
        if agent not in by_agent:
            by_agent[agent] = []
        by_agent[agent].append(insight)

        # By phase
        if phase not in by_phase:
            by_phase[phase] = []
        by_phase[phase].append(insight)

    return {"byAgent": by_agent, "byPhase": by_phase, "total": len(insights)}


def generate_report(cwd, state, insights):
    """Generate power mode report."""
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Aggregate insights
    aggregated = aggregate_insights(insights)

    # Build report
    report = {
        "timestamp": timestamp,
        "objective": state.get("objective", {}) if state else {},
        "agents": list(aggregated["byAgent"].keys()),
        "phases": list(aggregated["byPhase"].keys()),
        "insights": {
            "total": aggregated["total"],
            "byAgent": {agent: len(items) for agent, items in aggregated["byAgent"].items()},
            "byPhase": {phase: len(items) for phase, items in aggregated["byPhase"].items()},
        },
        "status": state.get("status", "completed") if state else "completed",
        "duration": state.get("duration", "unknown") if state else "unknown",
    }

    # Add top insights (most recent 10)
    report["topInsights"] = insights[-10:] if len(insights) > 10 else insights

    return report


def save_report(cwd, report):
    """Save power mode report."""
    cwd_path = Path(cwd)

    # Ensure .claude/popkit directory exists
    reports_dir = cwd_path / ".claude" / "popkit"
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Save report with timestamp
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    report_path = reports_dir / f"power-mode-report-{timestamp}.json"

    try:
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        return str(report_path), None

    except Exception as e:
        return None, str(e)


def handle_stop_hook(data):
    """
    Save power mode report on skill completion.

    Args:
        data: {
            "skill": "power-mode",
            "context": {...}
        }

    Returns:
        {
            "decision": "allow",
            "message": "Optional status message"
        }
    """
    # Determine working directory
    cwd = os.getcwd()

    # Load power mode data
    state = load_power_state(cwd)
    insights = load_insights(cwd)

    # Generate report
    report = generate_report(cwd, state, insights)

    # Save report
    report_path, error = save_report(cwd, report)

    if error:
        return {"decision": "allow", "message": f"Failed to save power mode report: {error}"}

    # Build summary message
    agents_count = len(report["agents"])
    insights_count = report["insights"]["total"]

    message = f"Power mode report saved to {report_path}\n"
    message += f"- Agents: {agents_count}\n"
    message += f"- Insights: {insights_count}\n"
    message += f"- Phases: {len(report['phases'])}"

    return {"decision": "allow", "message": message}


if __name__ == "__main__":
    try:
        # Read input from stdin
        data = json.loads(sys.stdin.read())

        # Process the hook
        result = handle_stop_hook(data)

        # Write output to stdout
        print(json.dumps(result))
        sys.exit(0)

    except Exception as e:
        # On error, allow the operation
        error_result = {"decision": "allow", "message": f"Hook error (report not saved): {str(e)}"}
        print(json.dumps(error_result))
        sys.exit(0)
