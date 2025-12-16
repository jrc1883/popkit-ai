# Running Vibe-Coded Benchmarks (Issue #257)

## Overview

Vibe-coded benchmarks test PopKit's ability to handle ambiguous requirements and minimal context - the way real developers often communicate ("make it work", "fix this error").

## Available Vibe Benchmarks

### 1. todo-app-vibe
**Prompt:** "make a todo app. it should let you add and remove todos and save them."

**Purpose:** Tests ability to:
- Handle vague requirements
- Make reasonable default decisions
- Fill in missing details (UI framework, storage method, etc.)
- Build a complete implementation from minimal context

**Expected Outcome:**
- Vanilla: Likely asks many clarifying questions or makes minimal implementation
- PopKit: Should use `pop-brainstorming` skill to fill gaps and make good assumptions

### 2. bug-fix-vibe
**Prompt:** "shopping cart is broken. getting this error:\n\nError: Should still have 1 item\n\nfix it plz"

**Purpose:** Tests ability to:
- Debug with only an error message (no detailed description)
- Investigate systematically to find root cause
- Make targeted fixes (not rewrites)
- Handle real-world debugging scenarios

**Expected Outcome:**
- Vanilla: May need guidance, might miss some bugs
- PopKit: Should use `pop-systematic-debugging` to investigate all issues

## Running the Benchmarks

### Prerequisites

1. **Claude Code CLI must be in PATH:**
   ```bash
   which claude  # Should return path to Claude Code CLI
   ```

2. **PopKit plugin installed:**
   ```bash
   claude plugin list | grep popkit
   ```

3. **Dependencies installed:**
   ```bash
   cd packages/benchmarks
   npm install
   ```

### Run Benchmarks

```bash
cd packages/benchmarks

# Run vanilla mode (no PopKit)
npx tsx run-benchmark.ts todo-app-vibe vanilla
npx tsx run-benchmark.ts bug-fix-vibe vanilla

# Run PopKit mode
npx tsx run-benchmark.ts todo-app-vibe popkit
npx tsx run-benchmark.ts bug-fix-vibe popkit

# Run both modes
npx tsx run-both.ts todo-app-vibe
npx tsx run-both.ts bug-fix-vibe
```

### Analyze Results

After running both modes, compare the results:

```bash
# Get result directories (they're timestamped)
ls results/ | grep todo-app-vibe

# Run comparison analysis
npx tsx analyze-results.ts \\
  results/todo-app-vibe-vanilla-<timestamp> \\
  results/todo-app-vibe-popkit-<timestamp>
```

This will generate:
- `results/comparison-report.txt` - Tool usage and cost comparison
- `results/workflow-metrics-report.txt` - Workflow value analysis (Issue #256)

## What to Look For

### Vanilla Mode Expected Behavior

**todo-app-vibe:**
- Many questions about requirements (framework? styling? features?)
- Minimal implementation (might just be basic HTML + JS)
- May not implement persistence
- Estimated: 180s, 40% success rate

**bug-fix-vibe:**
- Runs tests to see error
- May only fix the first bug (the one mentioned in error)
- Might miss the other 2 bugs
- Estimated: 150s, 50% success rate

### PopKit Mode Expected Behavior

**todo-app-vibe:**
- Uses `pop-brainstorming` to explore options
- Makes reasonable default choices (vanilla JS, localStorage)
- Builds complete implementation
- Asks user to choose next steps (testing, deployment, etc.)
- Estimated: 200s, 75% success rate

**bug-fix-vibe:**
- Uses `pop-systematic-debugging` skill
- Runs tests first to understand failure
- Investigates code to find ALL bugs (not just the one mentioned)
- Makes targeted fixes
- Re-runs tests to verify
- Estimated: 120s, 75% success rate

### Key Metrics to Compare

From the workflow metrics report (Issue #256):

1. **Context Efficiency:**
   - Files re-read multiple times (lower is better)
   - Context restorations (PopKit should restore from STATUS.json)

2. **Workflow Guidance:**
   - User decision points (PopKit should use AskUserQuestion)
   - Phase transitions (PopKit should follow workflows)
   - Workflow completeness (% of workflow completed)

3. **Skill Usage:**
   - Skills invoked (PopKit should invoke relevant skills)
   - Skill effectiveness score

4. **Overall Value:**
   - Overall score (0-100 composite)
   - Decisions supported
   - Workflow clarity gain

## Troubleshooting

### "spawn claude ENOENT"
Claude Code CLI is not in PATH. Install Claude Code and ensure `claude` command works:
```bash
claude --version
```

### "Plugin not found"
Install PopKit plugin:
```bash
claude plugin install popkit@popkit-claude
```

### Benchmark times out
Increase timeout in task JSON:
```json
"timeoutSeconds": 600
```

## Expected Results (Hypothesis)

### todo-app-vibe

| Metric | Vanilla | PopKit | Improvement |
|--------|---------|--------|-------------|
| Duration | 180s | 200s | -11% (acceptable) |
| Success Rate | 40% | 75% | +88% |
| Tests Passed | 2/4 | 4/4 | +100% |
| Skills Used | 0 | 2-3 | N/A |
| User Decisions | 0 | 2-3 | +100% |

**Key Value:** PopKit should fill in missing requirements and build a complete app, while vanilla struggles with ambiguity.

### bug-fix-vibe

| Metric | Vanilla | PopKit | Improvement |
|--------|---------|--------|-------------|
| Duration | 150s | 120s | +20% |
| Success Rate | 50% | 75% | +50% |
| Bugs Fixed | 1/3 | 3/3 | +200% |
| Skills Used | 0 | 1-2 | N/A |
| Systematic Debug | No | Yes | N/A |

**Key Value:** PopKit should find ALL bugs (not just the one mentioned), while vanilla only fixes what's explicitly reported.

## Next Steps

After running benchmarks and analyzing results:

1. **If PopKit performs better:**
   - Document specific skills/workflows that provided value
   - Use in marketing materials ("handles vibe-coded prompts 2x better")
   - Create more vibe benchmarks for other scenarios

2. **If PopKit performs same/worse:**
   - Investigate why skills weren't invoked
   - Improve routing/triggering for vague prompts
   - Add specific handlers for ambiguous requirements

3. **For workflow metrics:**
   - Share workflow-metrics-report.txt with team
   - Identify which metrics best represent "unmeasured value"
   - Use insights to improve skill effectiveness

## Related Issues

- #254: Fix benchmark runner bug (shell:true removal) ✅ COMPLETED
- #255: Add UI/design agent routing ✅ COMPLETED
- #256: Build workflow metrics analyzer ✅ COMPLETED
- #257: Run vibe-coded benchmarks 🔄 IN PROGRESS
- #258: Design self-testing framework ✅ COMPLETED
