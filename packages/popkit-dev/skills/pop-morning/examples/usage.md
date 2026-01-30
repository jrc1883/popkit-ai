# Usage Examples

## Basic Usage

```bash
/popkit:routine morning
# → Runs default morning routine
# → Calculates Ready to Code Score
# → Updates STATUS.json
# → Shows report
```

## With Measurement

```bash
/popkit:routine morning --measure
# → Runs morning routine
# → Tracks performance metrics
# → Saves to .claude/popkit/measurements/
```

## Quick Summary

```bash
/popkit:routine morning quick
# → Shows one-line summary
# → Ready to Code Score: 75/100 👍 - redis down, 3 commits behind
```

## With Optimization

```bash
/popkit:routine morning --optimized
# → Uses caching for GitHub/service data
# → Reduces token usage by 40-96%
```

## Files Modified

1. **STATUS.json** - Session state updated with:
   - Ready to Code score
   - Session restoration status
   - Dev environment state
   - Morning routine timestamp
   - Recommendations

2. **.claude/popkit/measurements/** (if --measure used)
   - Performance metrics
   - Tool call breakdown
   - Duration and token usage
