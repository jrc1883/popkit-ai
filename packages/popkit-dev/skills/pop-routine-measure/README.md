# Routine Measurement Dashboard - Quick Start

## Overview

The Routine Measurement Dashboard provides comprehensive metrics, cost analysis, and performance trends for routine executions.

## Quick Start

### 1. Create Measurements

Run any routine with the `--measure` flag:

```bash
/popkit:routine morning --measure
/popkit:routine nightly --measure
/popkit:routine morning run p-1 --measure
```

### 2. View Dashboard

```bash
# Latest measurement for any routine
/popkit:stats routine

# Specific routine
/popkit:stats routine morning
/popkit:stats routine nightly

# All measurements summary
/popkit:stats routine --all
```

## What You Get

### Summary Metrics

- Execution duration (seconds and minutes)
- Total tool calls
- Token usage (input/output)
- Character counts

### Token Breakdown

- Input tokens with percentage
- Output tokens with percentage
- Total tokens with k notation

### Cost Estimates

- Input cost (@$3.00/million tokens)
- Output cost (@$15.00/million tokens)
- Total cost (Claude Sonnet 4.5 pricing)

### Tool Analysis

- Per-tool breakdown (Bash, Read, Grep, Glob, etc.)
- Call counts
- Token usage per tool
- Duration per tool
- Character counts

### Comparison (when available)

- Duration change vs previous run
- Token usage change
- Cost change
- Tool call count change
- Percentage changes and indicators (↑↓→)

### Aggregate Statistics (--all)

- Average duration, tokens, cost
- Total duration, tokens, cost
- Trend analysis (first → latest)

## Data Storage

Measurements stored in:

```
.claude/popkit/measurements/
├── morning-pk_20251230_081532.json
├── morning-pk_20251229_081015.json
├── nightly-pk_20251228_200000.json
└── ...
```

## Implementation Details

### Files Created/Modified

1. **Skill Enhancement**: `packages/popkit-dev/skills/pop-routine-measure/SKILL.md`
   - Added dashboard visualization functions
   - Comparison logic
   - Aggregate statistics
   - Version bumped to 1.1.0

2. **Stats Command**: `packages/popkit-core/commands/stats.md`
   - Added `routine [name]` subcommand
   - Full documentation with examples
   - Integration instructions

3. **Routine Command**: `packages/popkit-dev/commands/routine.md`
   - Added "Viewing Measurements" section
   - Links to stats command and skill

## Testing

Test data created in `.claude/popkit/measurements/`:

- `morning-pk_20251230_081532.json` (latest)
- `morning-pk_20251229_081015.json` (previous for comparison)

Verified:
✓ Measurement file loading
✓ JSON parsing
✓ Dashboard data extraction
✓ Cost calculation
✓ Token breakdown
✓ Comparison logic

## Future Enhancements

### Phase 2: Direct Comparison

```bash
/popkit:stats routine morning --compare pk,p-1
```

### Phase 3: Trend Analysis

```bash
/popkit:stats routine morning --trend 7d
```

### Phase 4: Optimization Suggestions

```
Tool breakdown analysis:
- Bash: 50% of tokens → Suggestion: Cache git status
- Read: 25% of tokens → Suggestion: Use Grep for targeted reads
```

## Architecture

```
User runs: /popkit:routine morning --measure
    ↓
Hook: post-tool-use.py tracks all tool calls
    ↓
Storage: routine_measurement.py saves to JSON
    ↓
User views: /popkit:stats routine morning
    ↓
Skill: pop-routine-measure loads and visualizes
    ↓
Output: Dashboard with metrics, costs, trends
```

## Related

- **Command**: `/popkit:routine` - Execute routines with measurement
- **Command**: `/popkit:stats` - View statistics and measurements
- **Skill**: `pop-routine-measure` - Dashboard implementation
- **Utility**: `routine_measurement.py` - Core tracking logic
- **Hook**: `post-tool-use.py` - Automatic tool tracking

---

**Version**: 1.1.0
**Issue**: #628 (Routine Measurement Dashboard)
**Status**: Complete ✓
