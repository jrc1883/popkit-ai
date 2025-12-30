# Future Ambiguity Benchmark Scenarios

**Purpose:** Expand vibe-coded benchmark coverage to test PopKit's ambiguity handling across different types of developer requests.

**Status:** Designed but not yet implemented (awaiting results from current vibe-coded benchmarks)

---

## Scenario Categories

### 1. Feature Ambiguity
- Vague feature requests with no specifications
- Tests: Brainstorming, option presentation, smart defaults

### 2. Location Ambiguity
- Generic commands with no target specified
- Tests: Context analysis, scope detection, clarifying questions

### 3. Quality Ambiguity
- Improvement requests with no metrics
- Tests: Measurement, prioritization, iterative refinement

### 4. Scope Ambiguity
- Broad tasks with unclear boundaries
- Tests: Scope definition, phased execution, user checkpoints

---

## Scenario 1: "Fix the bug"

### Prompt
```
there's a bug. fix it.
```

### Setup
**Files:**
- `calculator.ts` - Has 2 bugs:
  - Bug 1 (obvious): Division by zero not handled
  - Bug 2 (subtle): Floating point precision in multiplication
- `calculator.test.ts` - 10 tests (8 passing, 2 failing)

**Ambiguities:**
- Which bug? (both tests fail, but error messages are different)
- Fix both or just one?
- Should I add more error handling?

### Expected Vanilla Behavior
- Run tests to see failures
- Fix the first failing test (division by zero)
- May or may not notice the second bug
- Success: 50% (1/2 bugs fixed)

### Expected PopKit Behavior
- Use `pop-systematic-debugging` to analyze all failures
- Present both bugs to user with AskUserQuestion:
  ```
  Question: "I found 2 bugs. How should I proceed?"
  Options:
    - Fix both now (recommended)
    - Fix division by zero first
    - Fix floating point first
    - Explain bugs in detail
  ```
- Fix both bugs
- Success: 100% (2/2 bugs fixed)

### Tests
1. `division-by-zero-fixed` - Throws error instead of Infinity
2. `floating-point-fixed` - Uses precision rounding
3. `all-tests-pass` - All 10 tests pass

### Baseline
- Vanilla: 50% success, 120s
- PopKit: 100% success, 90s (+80% faster, +100% more complete)

---

## Scenario 2: "Update the docs"

### Prompt
```
docs are out of date. update them.
```

### Setup
**Files:**
- `README.md` - Mentions v1.0.0 features (current is v2.0.0)
- `API.md` - Missing 3 new endpoints added in v1.5.0
- `CONTRIBUTING.md` - Build instructions reference old npm scripts
- `src/api.ts` - Current implementation (v2.0.0)

**Ambiguities:**
- Which docs? (3 files need updates)
- What changed? (need to analyze code)
- How much detail? (comprehensive or minimal)

### Expected Vanilla Behavior
- Update README.md only (most obvious)
- May not analyze code to find all changes
- Success: 33% (1/3 files updated)

### Expected PopKit Behavior
- Use `pop-documentation-maintainer` to analyze codebase
- Compare code to docs to find discrepancies
- Present findings:
  ```
  Question: "I found 3 documentation files needing updates. Priority?"
  Options:
    - Update all now (recommended)
    - README only (quick fix)
    - Show detailed changes first
  ```
- Update all 3 files consistently
- Success: 100% (3/3 files updated)

### Tests
1. `readme-updated` - Version number is 2.0.0
2. `api-docs-complete` - All 3 new endpoints documented
3. `contributing-current` - Build instructions match package.json
4. `consistency-check` - All docs reference same version

### Baseline
- Vanilla: 33% success, 180s
- PopKit: 100% success, 150s (+67% faster, +200% more complete)

---

## Scenario 3: "Make it better"

### Prompt
```
make the app better
```

### Setup
**Files:**
- `app.ts` - Functional todo app with issues:
  - Performance: Re-renders entire list on every change
  - UX: No loading states, no error messages
  - Code quality: No error handling, inconsistent formatting
- `styles.css` - Minimal styling, no responsive design

**Ambiguities:**
- Better how? (performance? UX? code quality? design?)
- What's the priority?
- How much change is acceptable?

### Expected Vanilla Behavior
- Make 1-2 obvious improvements (add some styling, fix formatting)
- No systematic analysis of issues
- Success: 30% (improved but not comprehensive)

### Expected PopKit Behavior
- Use `pop-code-quality-audit` to identify issues
- Categorize improvements:
  - Performance: 2 issues
  - UX: 3 issues
  - Code quality: 5 issues
  - Design: 4 issues
- Present options:
  ```
  Question: "I found 14 improvements across 4 categories. Focus?"
  Options:
    - All categories (comprehensive)
    - Performance first (fastest impact)
    - UX first (user-facing)
    - Show prioritized list
  ```
- Implement improvements based on user choice
- Success: 70% (systematic, targeted improvements)

### Tests
1. `performance-improved` - Renders only changed items
2. `error-handling` - Try/catch on all async operations
3. `loading-states` - Shows loading spinner during actions
4. `responsive-design` - Works on mobile screens

### Quality Metrics
- Lighthouse score improvement (+30 points)
- Code coverage (+20%)
- Linter warnings (-100%)

### Baseline
- Vanilla: 30% improvement, 300s, random fixes
- PopKit: 70% improvement, 240s, systematic approach (+133% value, +20% faster)

---

## Scenario 4: "Add a feature"

### Prompt
```
add a new feature to the app
```

### Setup
**Files:**
- `todo-app.ts` - Basic todo app (add, remove, list todos)
- Potential features:
  - Filters (active, completed, all)
  - Priorities (high, medium, low)
  - Due dates (with reminders)
  - Categories/tags
  - Search

**Ambiguities:**
- Which feature? (5+ options)
- User needs unknown
- Scope unknown (MVP vs full implementation)

### Expected Vanilla Behavior
- Pick a random feature (likely filters, most common)
- Implement without asking
- Success: 40% (works but may not be what user wanted)

### Expected PopKit Behavior
- Use `pop-brainstorming` to explore feature options
- Analyze existing codebase to see what's missing
- Present options:
  ```
  Question: "What feature would you like to add?"
  Options:
    - Filters (show active/completed)
    - Priorities (high/medium/low)
    - Due dates (with calendar picker)
    - Categories (organize todos)
    - Search (find by keyword)
    - Show popular choices
  ```
- Implement chosen feature
- Ask about MVP vs full implementation
- Success: 85% (user gets what they want)

### Tests
1. Feature exists (depends on choice)
2. Feature works correctly
3. Doesn't break existing functionality
4. Has tests for new feature

### Baseline
- Vanilla: 40% success, 200s, feature may not match intent
- PopKit: 85% success, 180s, user-driven choice (+112% satisfaction, +10% faster)

---

## Scenario 5: "Clean up the code"

### Prompt
```
code is messy. clean it up.
```

### Setup
**Files:**
- `messy.ts` - 200 lines with code smells:
  - Inconsistent formatting (tabs vs spaces, semicolons missing)
  - Long functions (80+ lines)
  - Duplicated code (3 similar functions)
  - Magic numbers (hardcoded values)
  - No type annotations
  - Commented-out code
- `.eslintrc.json` - Linter config (currently ignored)

**Ambiguities:**
- What level of cleanup? (formatting only? refactoring?)
- What's acceptable to change? (behavior must stay same)
- Should I add tests first? (to ensure no regressions)

### Expected Vanilla Behavior
- Run linter and fix auto-fixable issues (formatting)
- May do some manual cleanup
- Success: 40% (superficial cleanup only)

### Expected PopKit Behavior
- Use `pop-refactoring-expert` to analyze code smells
- Categorize issues:
  - Auto-fixable (linter): 15 issues
  - Manual refactoring: 8 issues
  - Architectural changes: 3 issues
- Present strategy:
  ```
  Question: "Code cleanup strategy?"
  Options:
    - Auto-fix only (safe, fast)
    - Auto-fix + refactoring (recommended)
    - Full cleanup including architecture
    - Show detailed plan first
  ```
- Run linter, extract functions, remove duplication
- Add tests if missing
- Success: 80% (thorough, safe cleanup)

### Tests
1. `linter-passes` - No linter warnings
2. `tests-pass` - All existing tests still pass
3. `coverage-maintained` - Code coverage didn't drop
4. `complexity-reduced` - Cyclomatic complexity lower

### Quality Metrics
- Linter warnings: 30 → 0
- Average function length: 35 lines → 15 lines
- Code duplication: 15% → 3%
- Type coverage: 40% → 95%

### Baseline
- Vanilla: 40% cleanup, 150s, formatting only
- PopKit: 80% cleanup, 180s, comprehensive refactoring (+100% thoroughness, -17% slower but worth it)

---

## Scenario 6: "Optimize performance"

### Prompt
```
app is slow. make it faster.
```

### Setup
**Files:**
- `slow-app.ts` - Multiple bottlenecks:
  - Network: Fetching data in loop (N+1 query problem)
  - Rendering: Re-rendering entire list on every keystroke
  - Computation: Expensive calculation in render function
  - Memory: Creating new objects unnecessarily
- `performance.json` - Baseline metrics (page load: 3s, interaction: 500ms)

**Ambiguities:**
- What's slow? (need to measure)
- Target metrics? (how fast is fast enough?)
- Trade-offs? (complexity vs speed)

### Expected Vanilla Behavior
- Make 1-2 obvious optimizations (debounce input, batch requests)
- No measurement before/after
- Success: 30% improvement (guessing, not measuring)

### Expected PopKit Behavior
- Use `pop-performance-profiler` to measure baseline
- Identify bottlenecks (sorted by impact):
  1. Network (3s) - Biggest impact
  2. Rendering (400ms) - Medium impact
  3. Computation (80ms) - Small impact
  4. Memory (20ms) - Tiny impact
- Present findings:
  ```
  Question: "Performance bottlenecks found. Strategy?"
  Options:
    - Fix all (comprehensive)
    - Top 2 issues (80/20 rule)
    - Network only (quick win)
    - Show detailed analysis
  ```
- Optimize based on user choice
- Re-measure to verify improvements
- Success: 70% improvement (measured, validated)

### Tests
1. `load-time-improved` - Page load < 1.5s (was 3s)
2. `interaction-improved` - Time to interactive < 200ms (was 500ms)
3. `no-regressions` - All functionality still works
4. `lighthouse-score` - Performance score > 90

### Quality Metrics
- Page load: 3s → 1.2s (-60%)
- Time to interactive: 500ms → 150ms (-70%)
- Network requests: 50 → 5 (-90%)
- Lighthouse score: 65 → 92 (+42%)

### Baseline
- Vanilla: 30% improvement, 200s, unmeasured
- PopKit: 70% improvement, 180s, measured and validated (+133% value, +10% faster)

---

## Implementation Priority

Based on value and complexity:

| Priority | Scenario | Complexity | Value | Rationale |
|----------|----------|------------|-------|-----------|
| **P0** | Fix the bug | Low | High | Tests existing systematic debugging |
| **P1** | Add a feature | Low | High | Tests brainstorming and user choice |
| **P2** | Update the docs | Medium | High | Tests code analysis and consistency |
| **P3** | Optimize performance | Medium | Medium | Tests measurement and validation |
| **P4** | Clean up code | Medium | Medium | Tests refactoring expertise |
| **P5** | Make it better | High | Low | Too open-ended, hard to measure |

---

## Task JSON Template

```json
{
  "id": "fix-the-bug-vibe",
  "name": "Bug Fix (Ultra-Vague)",
  "description": "Fix bugs with only 'there's a bug' as guidance. Tests systematic debugging.",
  "category": "standard",
  "language": "typescript",
  "version": "1.0.0",
  "promptQuality": "vibe-coded",

  "initialFiles": {
    "calculator.ts": "...",
    "calculator.test.ts": "..."
  },
  "dependencies": ["typescript", "tsx"],
  "setupCommands": ["npm install"],

  "prompt": "there's a bug. fix it.",

  "context": "Tests ability to find ALL bugs with minimal guidance.",
  "maxTokens": 40000,
  "timeoutSeconds": 300,

  "tests": [
    {
      "id": "division-by-zero-fixed",
      "name": "Division by zero handled",
      "type": "unit",
      "command": "grep -q 'throw.*Error' calculator.ts && echo 'PASS' || echo 'FAIL'",
      "successPattern": "PASS"
    },
    {
      "id": "floating-point-fixed",
      "name": "Floating point precision handled",
      "type": "unit",
      "command": "grep -qE '(toFixed|Math.round)' calculator.ts && echo 'PASS' || echo 'FAIL'",
      "successPattern": "PASS"
    },
    {
      "id": "all-tests-pass",
      "name": "All calculator tests pass",
      "type": "integration",
      "command": "npm test 2>&1 | grep -q '10 passed' && echo 'PASS' || echo 'FAIL'",
      "successPattern": "PASS"
    }
  ],

  "baseline": {
    "vanilla": {
      "tokenEstimate": 12000,
      "toolCallEstimate": 12,
      "successRate": 0.50,
      "timeEstimate": 120,
      "qualityEstimate": 5.5,
      "notes": "Will fix 1/2 bugs, may miss subtle floating point issue"
    },
    "popkit": {
      "tokenEstimate": 10000,
      "toolCallEstimate": 10,
      "successRate": 1.00,
      "timeEstimate": 90,
      "qualityEstimate": 8.5,
      "notes": "Should find and fix all bugs systematically"
    }
  },

  "tags": ["vibe-coded", "ultra-ambiguous", "debugging", "multi-bug"],
  "author": "PopKit Benchmark Team",
  "createdAt": "2025-12-30T00:00:00Z"
}
```

---

## Success Criteria

For each scenario, success is measured by:

1. **Correctness** (30%) - All tests pass
2. **Completeness** (20%) - All ambiguities resolved
3. **Code Quality** (20%) - Production-ready implementation
4. **Efficiency** (15%) - Reasonable token/time usage
5. **Best Practices** (10%) - Follows conventions
6. **Approach** (5%) - Systematic problem-solving

**Overall Goal:** PopKit should score 70%+ across all scenarios, demonstrating consistent value for ambiguous requests.

---

## Next Steps

1. **Wait for current vibe-coded results**
   - todo-app-vibe execution
   - bug-fix-vibe execution
   - Analyze actual vs expected behavior

2. **Validate approach**
   - Did brainstorming trigger correctly?
   - Did AskUserQuestion work as expected?
   - Did systematic debugging find all bugs?

3. **Implement P0 scenarios**
   - "Fix the bug" (highest priority)
   - "Add a feature" (high value, low complexity)

4. **Iterate based on findings**
   - Improve routing if skills didn't trigger
   - Refine prompts if too ambiguous/clear
   - Add more scenarios for coverage gaps

---

**Created:** 2025-12-30
**Author:** Claude Sonnet 4.5 (PopKit Research)
**Status:** DESIGNED - Awaiting current vibe-coded benchmark results
**Related:** Issue #227, docs/research/2025-12-30-ambiguity-benchmark-analysis.md
