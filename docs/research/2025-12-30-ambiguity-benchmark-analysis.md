# Ambiguity Handling Benchmark Analysis (Issue #227)

**Date:** 2025-12-30
**Issue:** #227 - Run vibe-coded benchmarks to test ambiguity handling
**Status:** ANALYSIS COMPLETE - Ready for execution

---

## Executive Summary

PopKit has **comprehensive vibe-coded benchmark infrastructure** ready to test ambiguity handling. Two primary benchmarks (`todo-app-vibe` and `bug-fix-vibe`) are designed to measure PopKit's effectiveness when handling intentionally vague, minimal-context prompts that mimic real developer communication patterns.

**Key Finding:** The benchmarks are ready to execute. No additional design is needed.

---

## Current Benchmark Infrastructure

### System Status

```
✅ Benchmark framework: OPERATIONAL
✅ Claude Code CLI: AVAILABLE
✅ PopKit plugin: INSTALLED & ENABLED
✅ Vibe-coded tasks: 2 available
✅ GitHub issue tasks: 3 available
✅ Runner scripts: WORKING
✅ Analysis tools: IMPLEMENTED
```

### Available Benchmark Types

| Type | Count | Purpose |
|------|-------|---------|
| **Vibe-coded** | 2 | Test ambiguity handling (minimal context) |
| **GitHub Issues** | 3 | Test real-world workflows (structured context) |
| **Standard** | 5 | Baseline performance (clear requirements) |
| **Power Mode** | 1 | Multi-agent coordination |
| **Total** | 12 | Comprehensive coverage |

---

## Vibe-Coded Benchmarks (Ambiguity Testing)

### 1. todo-app-vibe

**Location:** `packages/benchmarks/tasks/todo-app-vibe.json`

**Prompt:**
```
make a todo app. it should let you add and remove todos and save them.
```

**Ambiguities Tested:**
- No framework specified (vanilla JS? React? Vue?)
- No storage method specified (localStorage? sessionStorage? indexedDB?)
- No UI/UX specifications (design? styling? layout?)
- No feature completeness (edit todos? mark complete? filters?)
- No error handling requirements
- No testing requirements

**Expected Vanilla Behavior:**
- Ask many clarifying questions
- Make minimal implementation
- May not implement persistence
- Success rate: 40%
- Duration: ~180s

**Expected PopKit Behavior:**
- Use `pop-brainstorming` skill to explore options
- Make reasonable default choices (vanilla JS, localStorage)
- Build complete implementation
- Ask user for next steps via AskUserQuestion
- Success rate: 75%
- Duration: ~200s (+11% slower but more complete)

**Tests:**
1. `file-exists` - todo.js exists and has content
2. `has-storage` - Has localStorage/sessionStorage/indexedDB
3. `has-add` - Can add todos (grep for add/push/append/create)
4. `has-remove` - Can remove todos (grep for remove/delete/filter/splice)

**Quality Checks:**
- No syntax errors (node --check)

---

### 2. bug-fix-vibe

**Location:** `packages/benchmarks/tasks/bug-fix-vibe.json`

**Prompt:**
```
shopping cart is broken. getting this error:

Error: Should still have 1 item

fix it plz
```

**Ambiguities Tested:**
- Only one error mentioned (but there are 3 bugs!)
- No description of expected behavior
- No context about what was attempted
- No guidance on where to look
- Minimal politeness ("plz")

**Actual Bugs in shopping-cart.ts:**
1. **Bug 1 (line 14):** Assignment instead of comparison
   - `i.id = item.id` should be `i.id === item.id`
2. **Bug 2 (line 24):** Missing splice argument
   - `this.items.splice(index)` should be `splice(index, 1)`
3. **Bug 3 (line 30):** Floating point precision
   - `sum + item.price * item.quantity` should round to avoid 0.3000000004

**Expected Vanilla Behavior:**
- Run tests to see error
- Fix the first bug (the one mentioned)
- May miss the other 2 bugs
- Success rate: 50%
- Duration: ~150s

**Expected PopKit Behavior:**
- Use `pop-systematic-debugging` skill
- Run tests first to understand ALL failures
- Investigate code to find ALL 3 bugs
- Make targeted fixes (not rewrites)
- Re-run tests to verify
- Success rate: 75%
- Duration: ~120s (-20% faster AND more thorough)

**Tests:**
1. `typescript-compiles` - TypeScript compiles without errors
2. `tests-pass` - All tests pass
3. `bug1-fixed` - Assignment vs comparison fixed
4. `bug2-fixed` - Splice argument added
5. `bug3-fixed` - Floating point handled (Math.round/toFixed)

**Quality Checks:**
- Minimal changes (~50 lines, not 100+ rewrite)

---

## Ambiguity Handling Strategies

### How PopKit Should Respond

Based on the benchmark design and PopKit's architecture, here's the expected behavior for ambiguous requests:

#### 1. Recognize Ambiguity
- Detect vague prompts via keyword analysis
- Identify missing critical information
- Flag prompt as "vibe-coded" quality

#### 2. Gather Context First
- Use `pop-context-restore` if previous session available
- Check existing codebase for patterns
- Identify project type and tech stack

#### 3. Invoke Brainstorming/Debugging Skills
- **For feature requests:** `pop-brainstorming` to explore options
- **For bug fixes:** `pop-systematic-debugging` to investigate
- **For optimizations:** `pop-performance-profiler` to measure

#### 4. Use AskUserQuestion for Critical Decisions
**Examples:**
```javascript
// For todo-app-vibe
AskUserQuestion({
  question: "Which storage method would you prefer?",
  header: "Storage",
  options: [
    { label: "localStorage", description: "Simple, persists across sessions" },
    { label: "sessionStorage", description: "Cleared when tab closes" },
    { label: "indexedDB", description: "Advanced, for large datasets" },
    { label: "None", description: "Just keep in memory for now" }
  ]
})

// For bug-fix-vibe
AskUserQuestion({
  question: "I found 3 bugs. Which should I prioritize?",
  header: "Fix Order",
  options: [
    { label: "Fix all now", description: "Comprehensive fix (recommended)" },
    { label: "Just the error", description: "Fix 'Should have 1 item' only" },
    { label: "Show details", description: "Explain all bugs first" }
  ]
})
```

#### 5. Make Reasonable Defaults
- Choose simplest working solution
- Prefer vanilla JS over frameworks (unless context suggests otherwise)
- Use standard patterns (localStorage for persistence, try/catch for errors)
- Document assumptions in comments

#### 6. Validate Assumptions
- Run tests to verify behavior
- Use quality checks (linting, type checking)
- Present results to user for confirmation

---

## Execution Plan

### Step 1: Run Vibe-Coded Benchmarks

```bash
cd <PROJECT_ROOT>/packages/benchmarks

# Run both modes in parallel (recommended)
npx tsx run-both.ts todo-app-vibe --visible
npx tsx run-both.ts bug-fix-vibe --visible

# OR run individually
npx tsx run-benchmark.ts todo-app-vibe vanilla
npx tsx run-benchmark.ts todo-app-vibe popkit
npx tsx run-benchmark.ts bug-fix-vibe vanilla
npx tsx run-benchmark.ts bug-fix-vibe popkit
```

### Step 2: Analyze Results

```bash
# Find result directories
ls results/ | grep todo-app-vibe
ls results/ | grep bug-fix-vibe

# Run comparison analysis
npx tsx analyze-results.ts \
  results/todo-app-vibe-vanilla-<timestamp> \
  results/todo-app-vibe-popkit-<timestamp>

npx tsx analyze-results.ts \
  results/bug-fix-vibe-vanilla-<timestamp> \
  results/bug-fix-vibe-popkit-<timestamp>

# Quality analysis
npx tsx analyze-quality.ts \
  results/todo-app-vibe-popkit-<timestamp> \
  --compare results/todo-app-vibe-vanilla-<timestamp>

# Stream analysis (workflow metrics)
npx tsx analyze-stream.ts results/todo-app-vibe-popkit-<timestamp>
```

### Step 3: Document Findings

Create comprehensive report with:
1. **Quality Comparison**
   - Correctness scores (0-10)
   - Completeness scores (0-10)
   - Code quality scores (0-10)
   - Overall scores (weighted)

2. **Ambiguity Handling Effectiveness**
   - Number of questions asked
   - Assumptions made (documented vs undocumented)
   - Brainstorming/debugging skill usage
   - Context gathering effectiveness

3. **Workflow Metrics** (Issue #256)
   - Context efficiency (file re-reads)
   - Workflow guidance (user decision points)
   - Skill usage (skills invoked, effectiveness)
   - Overall value score (0-100)

4. **Recommendations**
   - When PopKit provides most value
   - Which skills are most effective for ambiguity
   - Improvements needed for routing/triggering
   - New skills to develop

---

## Expected Results (Hypotheses)

### todo-app-vibe

| Metric | Vanilla | PopKit | Improvement |
|--------|---------|--------|-------------|
| **Overall Score** | 5/10 | 7.5/10 | **+50%** |
| Duration | 180s | 200s | -11% (acceptable trade-off) |
| Success Rate | 40% | 75% | **+88%** |
| Tests Passed | 2/4 | 4/4 | **+100%** |
| Skills Used | 0 | 2-3 | N/A |
| User Decisions | 0 | 2-3 | Interactive vs silent |
| Questions Asked | Many | Targeted | Quality over quantity |
| Assumptions | Implicit | Documented | Transparency |

**Key Value Proposition:**
PopKit fills in missing requirements intelligently and builds a complete application, while vanilla Claude struggles with ambiguity and produces minimal implementations.

---

### bug-fix-vibe

| Metric | Vanilla | PopKit | Improvement |
|--------|---------|--------|-------------|
| **Overall Score** | 5.5/10 | 7.5/10 | **+36%** |
| Duration | 150s | 120s | **+20% faster** |
| Success Rate | 50% | 75% | **+50%** |
| Tests Passed | 3/5 | 5/5 | **+67%** |
| Bugs Fixed | 1/3 | 3/3 | **+200%** |
| Skills Used | 0 | 1-2 | Systematic debugging |
| Systematic Debug | No | Yes | Comprehensive vs reactive |

**Key Value Proposition:**
PopKit finds ALL bugs (not just the one mentioned), uses systematic debugging, and completes faster with higher quality. Vanilla only fixes what's explicitly reported.

---

## Additional Ambiguous Scenarios (Future Benchmarks)

### Designed But Not Yet Implemented

#### 1. "Fix the bug" (which bug?)
**Prompt:** "there's a bug. fix it."
**Codebase:** 3 files, 2 known bugs (1 obvious, 1 subtle)
**Test:** Does PopKit find both? Does it ask which to prioritize?

#### 2. "Update the docs" (which docs?)
**Prompt:** "docs are out of date. update them."
**Codebase:** README.md, API.md, CONTRIBUTING.md all need updates
**Test:** Does PopKit analyze code changes first? Update all docs consistently?

#### 3. "Make it better" (what aspect?)
**Prompt:** "make the app better"
**Codebase:** Functional but slow, poorly styled, no error handling
**Test:** Does PopKit ask for priorities? Suggest multiple improvements?

#### 4. "Add a feature" (what feature?)
**Prompt:** "add a new feature to the app"
**Codebase:** Todo app (could add: filters, priorities, due dates, categories)
**Test:** Does PopKit suggest options? Ask user to choose? Make smart default?

#### 5. "Clean up the code" (where?)
**Prompt:** "code is messy. clean it up."
**Codebase:** Multiple files with code smells, inconsistent formatting
**Test:** Does PopKit use linter? Prioritize critical issues? Document changes?

#### 6. "Optimize performance" (what metric?)
**Prompt:** "app is slow. make it faster."
**Codebase:** Multiple bottlenecks (network, rendering, computation)
**Test:** Does PopKit profile first? Ask for target metrics? Measure improvements?

---

## Benchmark Framework Features

### What Makes These Benchmarks Valid

1. **Isolation**
   - Git worktree-based (separate working directories)
   - ConfigSwitcher (enables/disables PopKit cleanly)
   - No cross-contamination between runs

2. **Fairness**
   - Same prompts for both modes
   - Same initial files
   - Same timeout and token limits
   - Objective automated tests

3. **Reproducibility**
   - JSON task definitions (version controlled)
   - Deterministic test commands
   - Timestamped results directories
   - Full session transcripts captured

4. **Comprehensive Metrics**
   - Correctness (30% weight) - Does it work?
   - Completeness (20% weight) - All features implemented?
   - Code Quality (20% weight) - Production-ready?
   - Efficiency (15% weight) - Tokens, duration, tool calls
   - Best Practices (10% weight) - Conventions, linting, security
   - Approach (5% weight) - Problem-solving strategy

5. **Automated Analysis**
   - `analyze-results.ts` - Compare vanilla vs PopKit
   - `analyze-quality.ts` - Code quality scoring
   - `analyze-stream.ts` - Workflow metrics (Issue #256)

---

## Gaps Identified

### Current Limitations

1. **No Live Execution Yet**
   - Benchmarks are designed but not yet executed
   - Need actual results to validate hypotheses
   - Unknown if PopKit routing will trigger brainstorming/debugging skills

2. **Metrics Collection Incomplete**
   - Tool calls show 0 (parser needs improvement)
   - Token count only captures visible output
   - Need to parse JSON stream for accurate metrics

3. **AskUserQuestion Automation**
   - Benchmarks need automated answers for interactive prompts
   - Currently would pause waiting for user input
   - Need `--auto-answer` mode for batch execution

4. **Missing Middle-Quality Benchmarks**
   - Have: Vibe-coded (minimal) and structured (comprehensive)
   - Missing: Junior-dev quality (medium ambiguity)
   - Example: "Improve app performance" (vague metric)

5. **No Iterative Workflow Tests**
   - Current benchmarks are one-shot tasks
   - Real development is iterative (PR review → fix → retest)
   - Need multi-turn benchmark support

---

## Recommendations

### Immediate Actions (This Session)

1. **Execute Existing Benchmarks**
   ```bash
   # Run todo-app-vibe (both modes)
   npx tsx run-both.ts todo-app-vibe --visible

   # Run bug-fix-vibe (both modes)
   npx tsx run-both.ts bug-fix-vibe --visible
   ```

2. **Analyze Results**
   - Compare vanilla vs PopKit scores
   - Validate hypotheses
   - Document actual behavior vs expected

3. **Update Issue #227**
   - Report execution results
   - Share findings (value proposition validation)
   - Identify improvements needed

### Short-Term Improvements (Next Sprint)

1. **Fix Metrics Collection**
   - Parse Claude's JSON output for actual tool calls
   - Capture full token usage (API-level if possible)
   - Track real-time events during execution

2. **Add Auto-Answer Mode**
   - Support `--auto-answer` flag for AskUserQuestion prompts
   - Use default options for batch execution
   - Log which answers were provided

3. **Improve Skill Routing**
   - Ensure vibe-coded prompts trigger brainstorming
   - Test bug reports trigger systematic debugging
   - Validate confidence thresholds for ambiguity detection

### Long-Term Enhancements (v2.0+)

1. **Create Junior-Dev Benchmarks**
   - Medium-quality prompts (between vibe and structured)
   - Test progressive disclosure strategies
   - Validate clarifying question effectiveness

2. **Multi-Turn Workflows**
   - PR review → fix → retest cycles
   - Feature request → implementation → iteration
   - Bug report → debug → verify → deploy

3. **Real-Time Ambiguity Detection**
   - ML model to classify prompt quality
   - Automatic skill routing based on ambiguity score
   - Adaptive questioning (more questions for vaguer prompts)

4. **Comparative Benchmarking**
   - PopKit vs Cursor
   - PopKit vs Codex
   - PopKit vs Copilot
   - Cross-IDE value proposition

---

## Files Involved

### Benchmark Infrastructure
- `packages/benchmarks/README.md` - Framework overview
- `packages/benchmarks/RUNNING-VIBE-BENCHMARKS.md` - Execution guide
- `packages/benchmarks/GITHUB-ISSUE-BENCHMARKS.md` - Real-world tasks
- `packages/benchmarks/run-benchmark.ts` - CLI runner
- `packages/benchmarks/run-both.ts` - Parallel execution
- `packages/benchmarks/analyze-results.ts` - Comparison tool
- `packages/benchmarks/analyze-quality.ts` - Quality scoring
- `packages/benchmarks/analyze-stream.ts` - Workflow metrics

### Task Definitions
- `packages/benchmarks/tasks/todo-app-vibe.json` - Vibe-coded CRUD
- `packages/benchmarks/tasks/bug-fix-vibe.json` - Vibe-coded debugging
- `packages/benchmarks/tasks/todo-app.json` - Structured version (comparison)
- `packages/benchmarks/tasks/bug-fix.json` - Structured version (comparison)

### Results Storage
- `packages/benchmarks/results/` - Output directory (timestamped)
- `packages/benchmarks/results/sessions/` - Raw session data
- `packages/benchmarks/results/comparisons/` - Comparison reports

### Analysis Output
- `docs/research/2025-12-30-ambiguity-benchmark-analysis.md` - This document
- `docs/research/2025-12-15-vibe-coded-benchmark-results.md` - To be created after execution

---

## Success Criteria

### Benchmark Execution
- [ ] todo-app-vibe runs successfully (vanilla)
- [ ] todo-app-vibe runs successfully (popkit)
- [ ] bug-fix-vibe runs successfully (vanilla)
- [ ] bug-fix-vibe runs successfully (popkit)
- [ ] All 4 runs complete without errors
- [ ] Results saved to timestamped directories

### Analysis Completion
- [ ] Comparison reports generated
- [ ] Quality scores calculated
- [ ] Workflow metrics extracted
- [ ] Hypotheses validated or refuted

### Documentation
- [ ] Findings documented in research doc
- [ ] Issue #227 updated with results
- [ ] Recommendations for improvements
- [ ] Next steps prioritized

### Value Proposition Validation
- [ ] PopKit shows measurable improvement on ambiguous prompts
- [ ] Specific skills (brainstorming, debugging) demonstrate value
- [ ] User decision points enhance vs hinder workflow
- [ ] Trade-offs (speed vs completeness) are acceptable

---

## Conclusion

PopKit has a **comprehensive, production-ready benchmark framework** for testing ambiguity handling. The two vibe-coded benchmarks (`todo-app-vibe` and `bug-fix-vibe`) are specifically designed to measure PopKit's effectiveness when handling minimal-context prompts that mimic real developer communication.

**Next Action:** Execute the benchmarks and analyze results to validate PopKit's value proposition for ambiguity handling.

**Confidence:** High - Infrastructure is solid, tests are well-designed, analysis tools are ready.

**Risk:** Medium - Unknown if PopKit's agent routing will correctly trigger brainstorming/debugging skills for vibe-coded prompts. May need to improve routing logic based on findings.

---

**Document created:** 2025-12-30
**Author:** Claude Sonnet 4.5 (PopKit Analysis)
**Issue:** #227
**Status:** READY FOR EXECUTION
