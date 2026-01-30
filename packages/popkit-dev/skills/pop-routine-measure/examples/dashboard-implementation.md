# Dashboard Implementation

Complete Python implementation for viewing routine measurements.

## Full Implementation

```python
#!/usr/bin/env python3
"""
Routine Measurement Dashboard
Displays metrics, trends, and visualizations for routine measurements
"""
import json
import sys
from pathlib import Path
from datetime import datetime

# Add shared utilities
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / 'shared-py'))
from popkit_shared.utils.routine_measurement import estimate_tokens

def load_measurements(routine_name=None):
    """Load measurement files from disk."""
    measurements_dir = Path.cwd() / ".claude" / "popkit" / "measurements"

    if not measurements_dir.exists():
        return []

    measurements = []
    for file_path in sorted(measurements_dir.glob("*.json"), reverse=True):
        try:
            with open(file_path) as f:
                data = json.load(f)

            # Filter by routine name if provided
            if routine_name:
                # Match exact routine_name or routine_id
                if data.get("routine_name") != routine_name and data.get("routine_id") != routine_name:
                    continue

            measurements.append({
                "file": file_path.name,
                "data": data,
                "timestamp": datetime.fromtimestamp(data.get("start_time", 0))
            })
        except Exception as e:
            print(f"Warning: Failed to load {file_path}: {e}", file=sys.stderr)

    return measurements

def format_dashboard(measurement_data, previous_data=None):
    """Format a measurement dashboard."""
    data = measurement_data["data"]

    lines = []
    lines.append("=" * 80)
    lines.append("ROUTINE MEASUREMENT DASHBOARD".center(80))
    lines.append("=" * 80)

    # Header
    routine_name = data.get('routine_name', 'Unknown')
    routine_id = data.get('routine_id', 'N/A')
    lines.append(f"Routine: {routine_name} ({routine_id})")
    lines.append(f"Timestamp: {measurement_data['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"File: {measurement_data['file']}")
    lines.append("")

    # Summary Metrics
    lines.append("SUMMARY METRICS")
    lines.append("-" * 80)
    duration = data.get("duration", 0)
    lines.append(f"  Duration:     {duration:.2f}s ({duration/60:.1f} minutes)")
    lines.append(f"  Tool Calls:   {data.get('total_tool_calls', 0)}")
    lines.append(f"  Total Tokens: {data.get('total_tokens', 0):,}")
    lines.append(f"  Characters:   {data.get('total_chars', 0):,}")
    lines.append("")

    # Token Breakdown
    lines.append("TOKEN USAGE")
    lines.append("-" * 80)
    input_tokens = data.get("input_tokens", 0)
    output_tokens = data.get("output_tokens", 0)
    total_tokens = data.get("total_tokens", 0)

    in_pct = (input_tokens/total_tokens*100) if total_tokens else 0
    out_pct = (output_tokens/total_tokens*100) if total_tokens else 0

    lines.append(f"  Input Tokens:  {input_tokens:>10,}  ({input_tokens/1000:.1f}k)  [{in_pct:.1f}%]")
    lines.append(f"  Output Tokens: {output_tokens:>10,}  ({output_tokens/1000:.1f}k)  [{out_pct:.1f}%]")
    lines.append(f"  Total Tokens:  {total_tokens:>10,}  ({total_tokens/1000:.1f}k)")
    lines.append("")

    # Cost Estimate
    cost = data.get("cost_estimate", {})
    lines.append("COST ESTIMATE (Claude Sonnet 4.5)")
    lines.append("-" * 80)
    lines.append(f"  Input Cost:   ${cost.get('input', 0):.4f}  (@$3.00/million tokens)")
    lines.append(f"  Output Cost:  ${cost.get('output', 0):.4f}  (@$15.00/million tokens)")
    lines.append(f"  Total Cost:   ${cost.get('total', 0):.4f}")
    lines.append("")

    # Tool Breakdown
    lines.append("TOOL BREAKDOWN")
    lines.append("-" * 80)
    lines.append(f"{'Tool':<20} {'Calls':<8} {'Tokens':<12} {'Duration':<12} {'Chars':<12}")
    lines.append("-" * 80)

    tool_breakdown = data.get("tool_breakdown", {})
    for tool, stats in tool_breakdown.items():
        total_tool_tokens = stats.get("input_tokens", 0) + stats.get("output_tokens", 0)
        lines.append(
            f"{tool:<20} "
            f"{stats.get('count', 0):<8} "
            f"{total_tool_tokens:>10,}  "
            f"{stats.get('duration', 0):>10.2f}s "
            f"{stats.get('chars', 0):>10,}"
        )

    # Comparison with previous run
    if previous_data:
        lines.append("")
        lines.append("COMPARISON WITH PREVIOUS RUN")
        lines.append("-" * 80)
        prev = previous_data["data"]

        # Duration change
        prev_duration = prev.get("duration", 0)
        duration_change = duration - prev_duration
        duration_pct = (duration_change / prev_duration * 100) if prev_duration else 0
        duration_indicator = "↑" if duration_change > 0 else "↓" if duration_change < 0 else "→"
        lines.append(f"  Duration:     {duration_indicator} {abs(duration_change):.2f}s ({duration_pct:+.1f}%)")

        # Token change
        prev_tokens = prev.get("total_tokens", 0)
        token_change = total_tokens - prev_tokens
        token_pct = (token_change / prev_tokens * 100) if prev_tokens else 0
        token_indicator = "↑" if token_change > 0 else "↓" if token_change < 0 else "→"
        lines.append(f"  Tokens:       {token_indicator} {abs(token_change):,} ({token_pct:+.1f}%)")

        # Cost change
        prev_cost = prev.get("cost_estimate", {}).get("total", 0)
        cost_change = cost.get("total", 0) - prev_cost
        cost_pct = (cost_change / prev_cost * 100) if prev_cost else 0
        cost_indicator = "↑" if cost_change > 0 else "↓" if cost_change < 0 else "→"
        lines.append(f"  Cost:         {cost_indicator} ${abs(cost_change):.4f} ({cost_pct:+.1f}%)")

        # Tool call change
        prev_tool_calls = prev.get("total_tool_calls", 0)
        tool_call_change = data.get("total_tool_calls", 0) - prev_tool_calls
        tool_call_indicator = "↑" if tool_call_change > 0 else "↓" if tool_call_change < 0 else "→"
        lines.append(f"  Tool Calls:   {tool_call_indicator} {abs(tool_call_change)} tools")

    lines.append("=" * 80)

    return "\n".join(lines)

def show_all_measurements(routine_name=None):
    """Show summary of all measurements."""
    measurements = load_measurements(routine_name)

    if not measurements:
        if routine_name:
            print(f"No measurements found for routine: {routine_name}")
        else:
            print("No measurements found.")
        print("\nRun a routine with --measure flag to create measurements:")
        print("  /popkit:routine morning --measure")
        return

    lines = []
    lines.append("=" * 80)
    if routine_name:
        lines.append(f"ALL MEASUREMENTS: {routine_name}".center(80))
    else:
        lines.append("ALL ROUTINE MEASUREMENTS".center(80))
    lines.append("=" * 80)
    lines.append(f"Total Measurements: {len(measurements)}")
    lines.append("")
    lines.append(f"{'Date':<20} {'Routine':<15} {'Duration':<12} {'Tokens':<12} {'Cost':<10}")
    lines.append("-" * 80)

    for m in measurements:
        data = m["data"]
        routine_display = data.get('routine_id', 'unknown')[:14]
        lines.append(
            f"{m['timestamp'].strftime('%Y-%m-%d %H:%M:%S'):<20} "
            f"{routine_display:<15} "
            f"{data.get('duration', 0):>10.2f}s "
            f"{data.get('total_tokens', 0):>10,}  "
            f"${data.get('cost_estimate', {}).get('total', 0):>8.4f}"
        )

    # Calculate trends if multiple measurements
    if len(measurements) >= 2:
        lines.append("")
        lines.append("AGGREGATE STATISTICS")
        lines.append("-" * 80)

        # Averages
        avg_duration = sum(m["data"].get("duration", 0) for m in measurements) / len(measurements)
        avg_tokens = sum(m["data"].get("total_tokens", 0) for m in measurements) / len(measurements)
        avg_cost = sum(m["data"].get("cost_estimate", {}).get("total", 0) for m in measurements) / len(measurements)

        lines.append(f"  Average Duration: {avg_duration:.2f}s")
        lines.append(f"  Average Tokens:   {avg_tokens:,.0f}")
        lines.append(f"  Average Cost:     ${avg_cost:.4f}")

        # Totals
        total_duration = sum(m["data"].get("duration", 0) for m in measurements)
        total_tokens = sum(m["data"].get("total_tokens", 0) for m in measurements)
        total_cost = sum(m["data"].get("cost_estimate", {}).get("total", 0) for m in measurements)

        lines.append("")
        lines.append(f"  Total Duration:   {total_duration:.2f}s ({total_duration/60:.1f} minutes)")
        lines.append(f"  Total Tokens:     {total_tokens:,}")
        lines.append(f"  Total Cost:       ${total_cost:.4f}")

        # Trend (first vs last)
        first = measurements[-1]["data"]
        last = measurements[0]["data"]

        duration_trend = last.get("duration", 0) - first.get("duration", 0)
        token_trend = last.get("total_tokens", 0) - first.get("total_tokens", 0)

        lines.append("")
        lines.append("TREND (First → Latest)")
        lines.append("-" * 80)
        lines.append(f"  Duration Change:  {'+' if duration_trend > 0 else ''}{duration_trend:.2f}s")
        lines.append(f"  Token Change:     {'+' if token_trend > 0 else ''}{token_trend:,}")

    lines.append("=" * 80)

    print("\n".join(lines))

def main():
    """Main entry point for dashboard."""
    import argparse

    parser = argparse.ArgumentParser(description="Routine measurement dashboard")
    parser.add_argument("--routine", help="Filter by routine name/ID")
    parser.add_argument("--all", action="store_true", help="Show all measurements summary")
    parser.add_argument("--no-compare", action="store_true", help="Don't compare with previous run")

    args = parser.parse_args()

    # Load measurements
    measurements = load_measurements(args.routine)

    if not measurements:
        if args.routine:
            print(f"No measurements found for routine: {args.routine}")
        else:
            print("No measurements found.")
        print("\nRun a routine with --measure flag to create measurements:")
        print("  /popkit:routine morning --measure")
        return

    # Show all measurements summary
    if args.all:
        show_all_measurements(args.routine)
        return

    # Show latest measurement dashboard
    latest = measurements[0]
    previous = measurements[1] if len(measurements) > 1 and not args.no_compare else None

    dashboard = format_dashboard(latest, previous)
    print(dashboard)

    # Hint
    if len(measurements) > 1:
        print("")
        print(f"Tip: Use --all to see summary of all {len(measurements)} measurements")

if __name__ == "__main__":
    main()
```

## Usage

```bash
# View latest measurement for any routine
python examples/dashboard-implementation.py

# View measurements for specific routine
python examples/dashboard-implementation.py --routine morning

# View all measurements summary
python examples/dashboard-implementation.py --all

# View without comparison
python examples/dashboard-implementation.py --routine morning --no-compare
```
