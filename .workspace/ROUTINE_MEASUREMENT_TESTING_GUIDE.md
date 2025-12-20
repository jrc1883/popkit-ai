# Routine Measurement Testing Guide

**Feature:** Context usage tracking for PopKit routines
**Date:** 2025-12-19
**Commits:** 233b0dab, 62d6f07d

## What Was Implemented

### 1. Core Measurement System
- `hooks/utils/routine_measurement.py` - Tracker with singleton pattern
- `hooks/post-tool-use.py` - Auto-capture tool calls
- `skills/pop-routine-measure/` - Skill documentation + tests

### 2. Command Integration
- `commands/routine.md` - Added `--measure` flag documentation
- Updated for both morning and nightly routines

### 3. Documentation Updates
- `README.md` - Added Routine Measurement section
- `CLAUDE.md` - Updated Unified Routine Management section

## Testing Checklist

### ✅ Unit Tests (Already Passing)

```bash
cd packages/plugin/skills/pop-routine-measure
python test_measurement.py
```

**Expected:** 4/4 tests passing
- Basic tracking
- Report formatting
- Data persistence
- Environment flag

### ⏳ Integration Tests (To Do)

#### Test 1: Basic Measurement

```bash
/popkit:routine morning --measure
```

**What to Look For:**
1. ✅ Normal routine output displays
2. ✅ Measurement report appears after routine completes
3. ✅ Report shows:
   - Duration (seconds)
   - Tool call count
   - Token estimates (input/output/total)
   - Cost estimate
   - Tool breakdown table
4. ✅ JSON file created in `.claude/popkit/measurements/`
5. ✅ Filename format: `{routine-id}_{timestamp}.json`

**Success Criteria:**
- Routine executes normally
- Measurement report displays formatted correctly
- JSON file exists and is valid
- No errors in console

#### Test 2: Nightly Routine Measurement

```bash
/popkit:routine nightly --measure
```

**What to Look For:**
- Same as Test 1, but for nightly routine
- Verify different routine ID in filename

#### Test 3: Specific Routine Measurement

```bash
/popkit:routine morning run pk --measure
```

**What to Look For:**
- Measures the universal `pk` routine
- Filename uses `pk_` prefix
- Different token counts than custom routine

#### Test 4: JSON Data Validation

```bash
# After running measurement
cat .claude/popkit/measurements/*.json | python -m json.tool
```

**Expected JSON Structure:**
```json
{
  "routine_id": "p-1",
  "routine_name": "PopKit Full Validation",
  "start_time": 1734567890.123,
  "end_time": 1734567902.456,
  "duration": 12.333,
  "total_tool_calls": 15,
  "total_tokens": 8023,
  "input_tokens": 1234,
  "output_tokens": 6789,
  "total_chars": 32092,
  "tool_breakdown": {
    "Bash": {
      "count": 8,
      "input_tokens": 691,
      "output_tokens": 2765,
      "duration": 2.34,
      "chars": 13824
    }
  },
  "cost_estimate": {
    "input": 0.0037,
    "output": 0.1018,
    "total": 0.1055
  }
}
```

#### Test 5: Without --measure Flag

```bash
/popkit:routine morning
```

**What to Look For:**
- ✅ Routine executes normally
- ✅ NO measurement report appears
- ✅ NO JSON file created
- ✅ No performance impact

**Success Criteria:**
- Default behavior unchanged when flag not used

#### Test 6: Multiple Measurements

```bash
/popkit:routine morning --measure
# Wait a few seconds
/popkit:routine morning --measure
```

**What to Look For:**
- ✅ Two separate JSON files created
- ✅ Different timestamps in filenames
- ✅ Can compare metrics between runs

#### Test 7: Error Handling

```bash
# Test with invalid routine
/popkit:routine morning run invalid-id --measure
```

**What to Look For:**
- ✅ Error message displays
- ✅ No measurement report (since routine didn't run)
- ✅ No JSON file created

## Expected Metrics Range

Based on typical routine execution:

| Metric | Typical Range | Notes |
|--------|---------------|-------|
| Duration | 10-30s | Depends on checks enabled |
| Tool Calls | 10-25 | More if --full flag used |
| Input Tokens | 500-2k | Command + context |
| Output Tokens | 2k-10k | Tool results + analysis |
| Total Tokens | 3k-12k | Combined |
| Cost | $0.05-$0.20 | Per routine execution |

## Tool Breakdown Analysis

**Common Tools in Routines:**

| Tool | Typical Calls | Token % | What It Does |
|------|---------------|---------|--------------|
| `Bash` | 8-12 | 30-40% | git status, tests, lint |
| `Read` | 3-6 | 20-30% | Config files, STATUS.json |
| `Grep` | 2-4 | 10-15% | Search for TODOs, FIXMEs |
| `Skill` | 1-2 | 15-25% | Invoke sub-skills |
| `Write` | 0-1 | 5-10% | Update STATUS.json |

## Optimization Insights

After collecting measurements, analyze:

1. **High Token Tools**
   - If Bash > 50%: Cache git status results
   - If Read > 40%: Read fewer config files
   - If Grep > 30%: Reduce search patterns

2. **Long Duration Tools**
   - Identify slowest tools
   - Consider parallelization
   - Cache expensive operations

3. **Cost Reduction**
   - Compare pk vs custom routines
   - Identify unnecessary checks
   - Optimize frequently-run routines

## Troubleshooting

### Issue: No measurement report appears

**Solution:**
1. Check environment variable: `echo $POPKIT_ROUTINE_MEASURE`
2. Verify hook file exists: `ls hooks/post-tool-use.py`
3. Check for Python import errors in hook

### Issue: JSON file not created

**Solution:**
1. Verify directory exists: `mkdir -p .claude/popkit/measurements`
2. Check file permissions
3. Review measurement tracker logs

### Issue: Token counts seem wrong

**Expected:**
- Token estimation is approximate (~4 chars per token)
- Actual API tokens may vary ±20%
- This is for relative comparison, not billing accuracy

### Issue: Cost estimates too high/low

**Note:**
- Based on Claude Sonnet 4.5 pricing ($3/$15 per million)
- Doesn't account for caching or prompt caching
- Use for relative cost comparison, not absolute billing

## Success Indicators

✅ **Feature is working if:**
1. `--measure` flag recognized by command
2. Measurement report displays after routine
3. JSON files created in correct location
4. Token/cost estimates seem reasonable
5. No errors or warnings
6. Regular routine execution unaffected

❌ **Feature has issues if:**
1. Errors during measurement
2. JSON files malformed
3. Token counts always zero
4. Hook failures in stderr
5. Performance degradation without flag

## Performance Impact

**Expected:**
- With `--measure`: +5-10% execution time (hook overhead)
- Without `--measure`: 0% impact (environment variable check only)

## Next Steps After Testing

If all tests pass:

1. ✅ Test on different routine types (pk, custom, project-specific)
2. ✅ Collect baseline measurements for optimization
3. ✅ Compare routine configurations
4. ✅ Document optimization opportunities
5. ✅ Consider adding comparison mode (future enhancement)

## Files to Review

| File | Purpose | Location |
|------|---------|----------|
| Implementation | Tracker classes | `hooks/utils/routine_measurement.py` |
| Hook Integration | Auto-capture | `hooks/post-tool-use.py` |
| Skill Doc | Usage guide | `skills/pop-routine-measure/SKILL.md` |
| Unit Tests | Test suite | `skills/pop-routine-measure/test_measurement.py` |
| Command Doc | Flag documentation | `commands/routine.md` |
| Main README | Feature overview | `README.md` |
| Project Guide | Architecture notes | `CLAUDE.md` |

## Reporting Issues

If you find bugs:

1. Capture measurement JSON file
2. Note routine command used
3. Check `.claude/session-tokens.json` for errors
4. Create GitHub issue with:
   - Command executed
   - Expected vs actual behavior
   - JSON output (if applicable)
   - Error messages

---

**Status:** Ready for integration testing
**Last Updated:** 2025-12-19
**Author:** PopKit Development Team
