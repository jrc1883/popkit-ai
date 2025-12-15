# GitHub Issue Benchmark System - Design Document

**Date:** 2025-12-15
**Author:** Claude Sonnet 4.5 (with Josep)
**Related Issues:** #250, #237, #220, #236
**Status:** Design Complete - Ready for Implementation

## Executive Summary

Extend PopKit's benchmark suite to use real GitHub issues as test cases, enabling fair comparison of vanilla Claude Code vs PopKit across actual development workflows with controlled variables for prompt quality, execution modes, and response patterns.

**Key Innovation:** Transform the issue backlog into a benchmark suite - every issue becomes a test case that validates PopKit's value while making progress on real work.

**Success Metrics:**
- Validate PopKit maintains 10/10 quality on real issues (not just synthetic tests)
- Quantify PopKit's speed advantage across different issue types
- Measure how different workflows (Quick vs Full vs Brainstorm) perform
- Test robustness across prompt quality levels (vibe coding → senior dev)

## Background & Motivation

### Current State

**Synthetic benchmarks work well:**
- Bouncing balls: PopKit 10/10, Vanilla 10/10 (equal quality)
- PopKit 14% faster (96s vs 112s)
- Equal cost ($0.24)
- Proven: With prompt parity, PopKit orchestration doesn't degrade quality

**Existing tasks:**
- `bouncing-balls.json` - Animation with physics
- `bug-fix.json` - Debug intentionally broken code
- `todo-app.json` - Build simple CRUD app
- `api-client.json` - HTTP client implementation
- `binary-search-tree.json` - Data structure implementation

**Limitations:**
- Synthetic = controlled but artificial
- Real issues = messy, complex, representative
- Need to validate on actual work we're doing anyway

### The Opportunity

**Issue backlog as test suite:**
```
PopKit has 250+ issues across:
- Bugs (small, well-defined)
- Features (medium complexity)
- Epics (large, multi-phase)
- Research (exploratory)
```

**Double value:**
1. Benchmark vanilla vs PopKit
2. Make actual progress on issues
3. Learn which workflows fit which issue types

### Learnings from Prompt Parity Investigation

**December 15, 2025 findings:**

Initially PopKit scored 3/10 vs Vanilla 10/10. Root cause: unfair comparison.
- PopKit received: "create bouncing balls animation" (4 words)
- Vanilla received: Full 6-point specification

After fixing prompt parity:
- PopKit: 10/10 quality, 96s duration, $0.24 cost
- Vanilla: 10/10 quality, 112s duration, $0.24 cost

**Lesson:** Benchmark design matters more than implementation. Always validate fairness first.

## Design Section 1: GitHub Issue Benchmark System

### Core Concept

Extend `packages/benchmarks/` to support real GitHub issues as test cases, comparing vanilla vs PopKit on actual development workflows.

### Branch Isolation Strategy

**Use git worktrees for parallel benchmark runs:**

```bash
# Benchmark infrastructure creates:
git worktree add /tmp/bench-vanilla-237 origin/master
git worktree add /tmp/bench-popkit-237 origin/master

# Each gets isolated branch:
cd /tmp/bench-vanilla-237
git checkout -b benchmark/vanilla-issue-237-{timestamp}

cd /tmp/bench-popkit-237
git checkout -b benchmark/popkit-issue-237-{timestamp}

# Run benchmarks in parallel (no cross-contamination)
# Cleanup: git worktree remove
```

**Benefits:**
- Shares .git directory (space efficient)
- Complete isolation (different branches)
- Parallel execution (faster results)
- Easy cleanup

### Issue-Based Task Schema

```typescript
interface GitHubIssueBenchmark extends BenchmarkTask {
  id: string;                    // "github-issue-237"
  name: string;                  // Issue title
  category: "github-issue";

  githubIssue: {
    repo: string;                // "jrc1883/popkit"
    number: number;              // 237
    url: string;                 // Full GitHub URL
  };

  // Support multiple execution modes
  executionModes: {
    vanilla: {
      prompt: string;            // Direct task description
    };
    popkitQuick: {
      command: string;           // "/popkit:dev \"task\""
      responses: Record<string, any>;  // Auto-responses
    };
    popkitFull?: {
      command: string;           // "/popkit:dev full \"task\""
      responses: Record<string, any>;
    };
    popkitBrainstorm?: {
      command: string;           // "/popkit:dev brainstorm \"idea\""
      responses: Record<string, any>;
    };
  };

  // Success validation
  successCriteria: string[];     // From issue acceptance criteria
  tests: BenchmarkTest[];        // Standard test suite
  qualityChecks: QualityCheck[]; // Code quality validation
}
```

### Judging Strategy (Hybrid Approach)

**Phase 1 - Automated Pre-Screening:**

```typescript
interface AutomatedScores {
  testsPass: boolean;          // 40% weight - Do tests pass?
  acceptanceCriteria: number;  // 30% weight - % criteria met (0-100)
  codeQuality: number;         // 20% weight - Lint, type check, assessors
  efficiency: number;          // 10% weight - Time, tokens, tool calls
}

// Automated scoring runs:
const score = (
  (testsPass ? 40 : 0) +
  (acceptanceCriteria * 0.3) +
  (codeQuality * 0.2) +
  (efficiency * 0.1)
);
```

**Phase 2 - Human Review:**

Manual review when:
- Scores are close (< 10 point difference)
- Both fail tests (need to understand why)
- New issue type (establish baseline)

Human scores on 1-10 scale:
- **Correctness:** Does it solve the issue?
- **Completeness:** All acceptance criteria met?
- **Code quality:** Follows patterns, maintainable?
- **Approach:** Right solution strategy?

**Phase 3 - Leverage PopKit Assessors (Future):**

```bash
# Use existing agent ecosystem for automated judging
/popkit:assess anthropic-engineer  # Claude Code best practices
/popkit:assess security-auditor    # Security vulnerabilities
/popkit:assess performance-tester  # Performance issues
/popkit:assess code-reviewer       # Code quality
/popkit:assess ux-reviewer         # User experience
```

This allows sophisticated quality assessment without exposing scoring logic to users.

## Design Section 2: Multiple Execution Modes

### The Variable Matrix

We're not just comparing "vanilla vs PopKit" - we're testing different **workflows** across different **contexts**:

```
Execution Modes:
├── Vanilla Claude Code
│   └── Direct implementation (no orchestration)
│
├── PopKit Quick Mode
│   └── /popkit:dev "task" (5-step minimal ceremony)
│   └── Steps: Understand → Find → Fix → Verify → Commit
│
├── PopKit Full Mode
│   └── /popkit:dev full "task" (7-phase with subagents)
│   └── Phases: Discovery → Exploration → Questions → Architecture → Implementation → Review → Summary
│   └── Subagents: code-explorer, code-architect, code-reviewer
│
└── PopKit Brainstorming → Planning → Implementation
    └── /popkit:dev brainstorm "idea"
    └── Then: /popkit:plan write
    └── Then: /popkit:plan execute
    └── Multi-phase with context handoff between skills
```

### Interactive Prompt Handling

**Challenge:** Both vanilla and PopKit use `AskUserQuestion` for user input.

**Solution:** Benchmark response system (from #237 design)

```typescript
// Task definition includes responses
interface BenchmarkTask {
  benchmarkResponses: Record<string, any>;
}

// Example:
{
  "benchmarkResponses": {
    "What's next?": "Create implementation plan",
    "Commit changes?": true,
    "Which approach?": "Automated scoring"
  }
}
```

**Implementation:**
1. Benchmark runner sets `POPKIT_BENCHMARK_MODE=true` environment variable
2. Creates response file: `/tmp/benchmark-responses-{id}.json`
3. Skills check for benchmark mode and auto-respond
4. No human interaction required during benchmark

**Critical for fairness:** Both vanilla and PopKit receive **identical responses**.

### Response Parity Principle

```typescript
// CORRECT - Fair comparison
const sharedResponses = {
  "Continue?": "Yes",
  "Commit changes?": true,
  "Which approach?": "Quick implementation"
};

vanillaBenchmark.responses = sharedResponses;
popkitBenchmark.responses = sharedResponses;

// WRONG - Unfair comparison
vanilla.responses = { "Continue?": "Yes" };
popkit.responses = { "Continue?": "Yes, and create a PR the PopKit way" };  // ❌
```

### Baseline Testing Strategy

**Phase 1 - Controlled Baselines:**

```
Test A: Vanilla vs PopKit Quick (same minimal prompt)
  └─> Validates: Basic orchestration value

Test B: Vanilla vs PopKit Full (same rich prompt)
  └─> Validates: Subagent orchestration value

Test C: Vanilla vs PopKit Brainstorm+Plan
  └─> Validates: Multi-phase workflow value
```

**Phase 2 - Workflow Comparison:**

```
Test D: PopKit Quick vs Full (same prompt)
  └─> Determines: When to use which workflow

Test E: PopKit Full vs Brainstorm+Plan (same prompt)
  └─> Determines: Complex vs exploratory approach
```

**Phase 3 - Robustness Testing:**

```
Test F: All modes with prompt quality variations
  └─> Determines: How each handles vague vs detailed prompts
```

## Design Section 3: Prompt Quality as a Test Variable

### The Core Insight

We're testing how vanilla vs PopKit handle different **levels of user expertise and context**.

**Hypothesis:** PopKit orchestration compensates for vague prompts by asking clarifying questions and exploring the codebase, while vanilla struggles without sufficient context.

### Prompt Specificity Levels

```typescript
type PromptQuality = "vibe-coding" | "junior-dev" | "senior-dev";

interface PromptVariation {
  level: PromptQuality;
  prompt: string;
  contextProvided: {
    fileLocations: boolean;
    issueLinks: boolean;
    errorMessages: boolean;
    requirements: boolean;
    designDocs: boolean;
  };
}
```

### Example: Issue #237 with Different Prompt Qualities

**Vibe Coding (minimal context):**
```
User: "Just make benchmarking work with PopKit workflows"
```

Context provided:
- ❌ No file paths
- ❌ No acceptance criteria
- ❌ No current state understanding
- ❌ Ambiguous requirements
- ❌ No links to design docs

**Junior Dev (medium context):**
```
User: "Fix issue #237 - add support for PopKit workflow benchmarking.
The benchmark runner needs to handle interactive prompts somehow."
```

Context provided:
- ✅ Issue number reference
- ✅ General problem identified
- ❌ Missing implementation details
- ❌ No file locations
- ❌ No design doc reference

**Senior Dev (rich context):**
```
User: "Implement #237 - PopKit Workflow Benchmark Testing

Current state: packages/benchmarks/ only supports vanilla vs popkit-enabled mode
Problem: Can't test actual workflows like /popkit:dev full because they use AskUserQuestion
Solution needed: Environment variable POPKIT_BENCHMARK_MODE + response file system

Files to modify:
- packages/benchmarks/src/types.ts (add workflowCommand field)
- packages/plugin/hooks/utils/benchmark_responses.py (new utility)
- packages/plugin/skills/pop-*/SKILL.md (add benchmark mode handling)

Acceptance criteria in issue body. See design doc:
docs/plans/2025-12-15-popkit-workflow-benchmark-design.md"
```

Context provided:
- ✅ Issue number + full context
- ✅ Current state understanding
- ✅ Problem statement
- ✅ Proposed solution
- ✅ Specific file paths
- ✅ Clear implementation steps
- ✅ Links to design docs

### Testable Hypotheses

**Hypothesis 1: PopKit compensates for vague prompts**
```
Vibe coding:
  Vanilla → Struggles, asks for clarification or guesses wrong
  PopKit  → Orchestrates discovery, asks targeted questions, explores codebase

Junior dev:
  Vanilla → Does okay with some backtracking
  PopKit  → Slightly better, fewer false starts

Senior dev:
  Vanilla → Executes well with clear direction
  PopKit  → Executes well, potentially faster due to orchestration
```

**Hypothesis 2: Context efficiency**
```
Vibe coding:
  Vanilla → Fails faster (fewer tokens but incomplete)
  PopKit  → Uses more tokens (discovery) but completes correctly

Junior dev:
  Vanilla → Similar token usage
  PopKit  → Similar or slightly less (efficient exploration)

Senior dev:
  Vanilla → Efficient with clear direction
  PopKit  → More efficient (orchestration optimizes tool calls)
```

**Hypothesis 3: Error recovery**
```
Vibe coding:
  Vanilla → Frequent backtracking, rewrites code
  PopKit  → Asks clarifying questions early, fewer rewrites

Junior dev:
  Vanilla → Some iteration needed
  PopKit  → Less iteration (better initial understanding)

Senior dev:
  Vanilla → Clean execution
  PopKit  → Clean execution
```

### Testing Matrix

```typescript
// For each issue, test all combinations:
const testMatrix = [
  { mode: "vanilla",        prompt: "vibe-coding" },
  { mode: "vanilla",        prompt: "junior-dev" },
  { mode: "vanilla",        prompt: "senior-dev" },
  { mode: "popkit-quick",   prompt: "vibe-coding" },
  { mode: "popkit-quick",   prompt: "junior-dev" },
  { mode: "popkit-quick",   prompt: "senior-dev" },
  { mode: "popkit-full",    prompt: "vibe-coding" },
  { mode: "popkit-full",    prompt: "junior-dev" },
  { mode: "popkit-full",    prompt: "senior-dev" },
];

// 9 benchmark runs per issue
// Identifies: Which mode handles which prompt quality best
```

### Real Example: This Conversation

**What user COULD have said (vibe coding):**
```
"continue"
```

**What user ACTUALLY said (senior dev):**
```
"The example is not quite right. It's not like the quality of the user
response back to us in the sense of whether or not they're satisfied...

[7 paragraphs of specific clarification, examples, and context]

...So the point that this can illustrate is like Popkit or Claude works
best when you give it specific instructions."
```

**Impact:**
- Rich context → Correct understanding, proper design
- Minimal context ("continue") → Would have built wrong thing

**This is exactly what we should benchmark!**

## Design Section 4: Benchmarking as a Product Feature

### Vision: User-Facing Benchmarking

Benchmarking isn't just internal tooling - it's a **premium feature** that helps users optimize their own workflows.

### User Value Proposition

**For individual developers:**
- "Am I using PopKit effectively?"
- "Should I use Quick Mode or Full Mode for this type of work?"
- "Is my prompt style wasting tokens?"

**For teams:**
- "How does our team's PopKit usage compare to best practices?"
- "Which workflows are most cost-effective for our project types?"
- "Are we getting ROI from PopKit Pro/Team subscription?"

### Tiered Feature Access

```typescript
interface BenchmarkingTiers {
  free: {
    benchmarksPerMonth: 2;
    features: [
      "Compare own approaches (Quick vs Full)",
      "Basic metrics (time, tokens, cost)",
      "HTML report export",
      "Results stored locally 30 days"
    ];
    limitations: [
      "No cloud upload/sharing",
      "No team comparison",
      "No historical trends"
    ];
  };

  pro: {
    benchmarksPerMonth: "unlimited";
    features: [
      "All Free features",
      "Cloud upload and sharing",
      "Historical trend analysis",
      "Custom quality assessors",
      "Prompt optimization suggestions",
      "Results stored in cloud 1 year"
    ];
    cost: "$9/month";
  };

  team: {
    benchmarksPerMonth: "unlimited";
    features: [
      "All Pro features",
      "Team performance dashboard",
      "Private benchmark tasks (not shared)",
      "Custom scoring rubrics",
      "Results stored indefinitely",
      "SOC2 compliance"
    ];
    cost: "$29/month per team";
  };
}
```

### Infrastructure Architecture

**Why cloud-based execution?**

Cannot run locally because:
1. Users don't have multiple Claude instances for parallel runs
2. Python hook utilities (scoring logic) shouldn't be exposed client-side
3. Comparative analysis needs historical data (cloud storage)
4. Resource-intensive (embeddings, pattern matching, assessors)

**Cloud architecture:**
```
User's Claude Code
    ↓ (POST /api/benchmark)
PopKit Cloud API (api.thehouseofdeals.com)
    ↓
Cloudflare Workers (orchestrate benchmark jobs)
    ↓
Upstash Redis (session coordination, results storage)
Upstash QStash (async job queue)
    ↓
Isolated Workers (run vanilla + popkit in parallel)
    ↓
Assessor Agents (score results - private code)
    ↓
Results returned to user + stored (anonymized)
```

### Security & Privacy Model

**Public GitHub repo exposure concerns:**

Current risk:
- Hook utilities (`packages/plugin/hooks/utils/*.py`) contain scoring logic
- Assessor agents have quality detection patterns
- Revealing these patterns weakens competitive advantage

**Solution - Cloud-Only Execution:**

```
PopKit Plugin (public: jrc1883/popkit-claude)
├── Commands & Skills (SAFE - declarative only)
├── Agent configs (SAFE - routing only)
└── Hook stubs (SAFE - call cloud API for scoring)

PopKit Cloud (private: jrc1883/popkit)
├── packages/cloud/src/assessors/ (scoring engine - PRIVATE)
├── packages/plugin/hooks/utils/ (full logic - PRIVATE)
└── Quality detection patterns (algorithms - PRIVATE)
```

**Data privacy by tier:**

```typescript
Free tier:
  - Anonymized results contribute to collective learning
  - No personally identifiable information
  - Results aggregated across users

Pro tier:
  - Results private by default
  - Opt-in to share anonymously
  - Can request full data export

Team tier:
  - Fully private, never shared
  - Can delete anytime
  - SOC2 compliant storage
```

**Local storage protection:**

```typescript
// Free tier - Basic metrics only (SAFE to expose)
{
  qualityScore: 9,
  winner: "popkit",
  metrics: { duration: 98, cost: 0.24 }
}

// Pro tier - Detailed but obfuscated (PROTECTED)
{
  qualityScore: 9,
  issueCount: 2,
  categories: ["physics", "performance"],
  // Detection patterns NOT included
}

// Team tier - Full transparency (PRIVATE)
{
  qualityScore: 9,
  issues: [...],           // Full details
  scoringRubric: {...},    // How we scored
  assessorOutput: {...},   // Raw assessor results
  // Available but never leaves user's infrastructure
}
```

### User Experience (Slash Command)

**Basic usage:**
```bash
# Benchmark a GitHub issue
/popkit:benchmark issue #237

# Benchmark with specific modes
/popkit:benchmark issue #237 --modes quick,full

# Benchmark with prompt quality variations
/popkit:benchmark issue #237 --prompts vibe,junior,senior

# Compare your own attempts
/popkit:benchmark issue #237 --compare-self
```

**Output format:**
```
🔬 Running Benchmark: Issue #237
================================================================================

Setup:
  • Creating isolated worktrees...
  • Branch: benchmark/vanilla-237-1734288000
  • Branch: benchmark/popkit-237-1734288000

Running Tests (Real-time tracking):
  Vanilla:  ████████░░░░░░░░ 58% | 7.2k tokens | $0.18 | 73s elapsed
  PopKit:   ██████████░░░░░░ 67% | 5.8k tokens | $0.14 | 67s elapsed

  Current leader: PopKit (faster, cheaper)

Final Results:
  ✓ Vanilla complete (127s, $0.31, 12.4k tokens)
  ✓ PopKit complete (98s, $0.24, 9.8k tokens)

Quality Assessment:
  📊 Vanilla: 8/10 (tests pass, some quality issues)
  📊 PopKit: 9/10 (tests pass, high quality)

Detailed Comparison:
┌─────────────────┬─────────┬─────────┬──────────┐
│ Metric          │ Vanilla │ PopKit  │ Winner   │
├─────────────────┼─────────┼─────────┼──────────┤
│ Duration        │ 127s    │ 98s     │ PopKit   │
│ Cost            │ $0.31   │ $0.24   │ PopKit   │
│ Quality Score   │ 8/10    │ 9/10    │ PopKit   │
│ Tests Passed    │ 5/6     │ 6/6     │ PopKit   │
│ Tool Calls      │ 23      │ 18      │ PopKit   │
└─────────────────┴─────────┴─────────┴──────────┘

🏆 Winner: PopKit (4/5 metrics)

View detailed analysis:
  • HTML Report: packages/benchmarks/results/issue-237-{timestamp}/report.html
  • Vanilla branch: benchmark/vanilla-237-1734288000
  • PopKit branch: benchmark/popkit-237-1734288000

Next steps:
  [Upload to cloud] [Create PR] [Cleanup worktrees] [Cancel]
```

### Rich HTML Export

**Standalone HTML report (no external dependencies):**

```html
<!DOCTYPE html>
<html>
<head>
  <title>Benchmark Report: Issue #237</title>
  <style>
    /* Embedded CSS for responsive design */
    /* Charts, tables, code diffs */
  </style>
  <script>
    /* Embedded JavaScript for interactivity */
    /* No external libraries required */
  </script>
</head>
<body>
  <!-- Executive Summary -->
  <section class="summary">
    <h1>PopKit vs Vanilla: Issue #237</h1>
    <div class="winner">Winner: PopKit (4/5 metrics)</div>
    <div class="scores">
      Quality: 9/10 vs 8/10 | Speed: 98s vs 127s | Cost: $0.24 vs $0.31
    </div>
  </section>

  <!-- Interactive Comparison Charts -->
  <section class="charts">
    <canvas id="metricsChart"></canvas>
    <canvas id="tokenUsageChart"></canvas>
  </section>

  <!-- Side-by-Side Code Diffs -->
  <section class="code-comparison">
    <div class="vanilla">
      <h3>Vanilla Implementation</h3>
      <pre><code>/* vanilla code */</code></pre>
    </div>
    <div class="popkit">
      <h3>PopKit Implementation</h3>
      <pre><code>/* popkit code */</code></pre>
    </div>
  </section>

  <!-- Quality Issues Breakdown -->
  <section class="quality">
    <table class="issues">
      <tr>
        <th>Category</th>
        <th>Vanilla</th>
        <th>PopKit</th>
      </tr>
      <!-- Issue details -->
    </table>
  </section>

  <!-- Export Options -->
  <section class="actions">
    <button onclick="exportJSON()">Download Raw Data</button>
    <button onclick="exportPDF()">Export as PDF</button>
    <button onclick="shareLink()">Generate Share Link (Pro)</button>
  </section>
</body>
</html>
```

**Features:**
- Open directly in browser (file://)
- Fully self-contained (no CDN dependencies)
- Responsive design (works on mobile)
- Print-friendly (PDF export)
- Shareable (email, Slack, GitHub)

**Pro tier - Cloud upload:**
```bash
# After benchmark, optionally upload
Upload results to PopKit Cloud for sharing? [y/N] y

Uploading to Upstash...
✓ Report available at: https://bench.popkit.dev/shared/abc123

Share this link with your team or embed in documentation.
Expires: 30 days (Pro tier)
Privacy: Unlisted (only accessible via link)
```

### VHS Tape Integration (Highlight Reels)

**Purpose:** Marketing, documentation, education

**Strategy:** Record key moments only, not entire benchmark run

**VHS tape structure:**
```tape
# benchmark-issue-237-highlights.tape
Output benchmark-issue-237.gif

Set FontSize 14
Set Width 1200
Set Height 800
Set Theme "Dracula"

# Scene 1: Command execution (2s)
Type "/popkit:benchmark issue #237"
Enter
Sleep 2s

# Scene 2: Key moment - PopKit routing decision (3s)
# Highlight: "Routing to Quick Mode (5-step process)"
Screenshot "popkit-routing.png"
Sleep 3s

# Scene 3: Tool usage efficiency (5s)
# Highlight: "PopKit: 18 tool calls | Vanilla: 23 tool calls"
Screenshot "tool-efficiency.png"
Sleep 5s

# Scene 4: Real-time token tracking (5s)
# Highlight: "PopKit ahead: 5.8k tokens vs 7.2k tokens"
Screenshot "token-tracking.png"
Sleep 5s

# Scene 5: Final results table (3s)
Screenshot "winner-popkit.png"
Sleep 3s

# Total: 18 seconds (not 127 seconds!)
```

**Key moments to capture:**
1. Workflow routing decision (Quick vs Full)
2. Tool call efficiency (fewer Read/Write operations)
3. Real-time token tracking (cost savings visible)
4. Quality assessment results
5. Winner announcement

**Use cases:**
- README.md demo GIF
- Social media (Twitter, LinkedIn)
- Documentation (how to run benchmarks)
- Sales/marketing (PopKit value prop)

### Cloud Storage (Simplified Approach)

**Phase 1 - Basic Cloud Storage (v1.2):**

```
Upstash Redis (already used for Power Mode)
└── Store benchmark summaries only

Structure:
  user:{userId}:benchmarks → List of benchmark IDs
  benchmark:{id} → {
    issueNumber: 237,
    winner: "popkit",
    qualityScores: { vanilla: 8, popkit: 9 },
    timestamp: "2025-12-15T...",
    shareLink: "https://bench.popkit.dev/shared/abc123",
    expiresAt: "2025-01-15T..."  // 30 days for Pro
  }
```

**Simple usage:**
```bash
# View recent benchmarks
/popkit:stats benchmark

Output:
Recent Benchmarks:
  #237 - PopKit won (9 vs 8) - 2 days ago
  #106 - Vanilla won (10 vs 7) - 1 week ago
  #220 - Tie (8 vs 8) - 2 weeks ago

Total benchmarks: 3/2 this month (Free tier limit reached)
Upgrade to Pro for unlimited: /popkit:upgrade pro
```

**Phase 2 - Upstash Vector (FUTURE - SKIP FOR NOW):**

Only add when you need:
- "Find similar benchmarks to this issue"
- "What approach worked best for bug fixes?"
- Collective learning from anonymized patterns

Not needed for v1.0-1.2.

**Phase 3 - Advanced Analytics (MUCH LATER):**

Only build when you have:
- Lots of benchmark data (100+ runs)
- Clear patterns emerging
- Team tier customers requesting it

Not needed for v1.0-1.2.

## Design Section 6: Implementation Roadmap

### Phase 1: Foundation (v1.0 - Local Only)

**Timeline:** 2-3 weeks
**Goal:** Get GitHub issue benchmarks working locally without cloud dependencies

**Must Have:**
1. Git worktree isolation system
   - Create separate branches for each run
   - Cleanup after completion

2. Task schema extension
   - `GitHubIssueBenchmark` type
   - Multiple execution mode support
   - Success criteria from issue

3. Basic automated scoring
   - Tests pass (40% weight)
   - Acceptance criteria met (30% weight)
   - Code quality (20% weight - lint, type check)
   - Efficiency (10% weight - time, tokens, cost)

4. HTML report generation
   - Standalone (no external dependencies)
   - Side-by-side comparison
   - Interactive charts
   - Exportable (PDF, JSON)

5. `/popkit:benchmark` command
   - Run benchmarks locally
   - Real-time progress tracking
   - Results summary in terminal

**Deliverables:**
```bash
# Works entirely locally
/popkit:benchmark issue #237

# Creates:
packages/benchmarks/results/issue-237-{mode}-{timestamp}/
├── session.json          # Raw metrics
├── quality-analysis.json # Scores
├── report.html          # Rich visual report
├── code-diff.patch      # Code changes
└── stream-raw.jsonl     # Full transcript
```

**Success Criteria:**
- Can benchmark at least 3 different PopKit issues
- HTML reports are shareable (open in any browser)
- Takes < 5 minutes to run a benchmark
- Results clearly show winner with justification
- No cloud dependencies required

**Skip for v1.0:**
- Cloud upload/sharing
- Historical trends
- Team features
- Upstash Vector
- Advanced analytics

### Phase 2: Interactive Workflows (v1.1)

**Timeline:** 1-2 weeks
**Goal:** Support PopKit's interactive workflows (builds on #237)
**Dependency:** Requires #237 implementation first

**Must Have:**
1. Benchmark response system from #237
   - `POPKIT_BENCHMARK_MODE` environment variable
   - Response file creation and parsing
   - Auto-answer `AskUserQuestion` prompts

2. Support all PopKit workflows
   - `/popkit:dev "task"` (Quick Mode)
   - `/popkit:dev full "task"` (Full Mode)
   - `/popkit:dev brainstorm "idea"` (Brainstorm → Plan → Execute)

3. Prompt quality variations
   - Vibe coding (minimal context)
   - Junior dev (medium context)
   - Senior dev (rich context)

4. Real-time token tracking
   - Live progress bars
   - Token count updates
   - Cost estimation
   - Side-by-side comparison during run

**Real-time tracking UX:**
```
Running Tests:
  Vanilla:  ████████░░░░░░░░ 58% | 7.2k tokens | $0.18 | 73s elapsed
  PopKit:   ██████████░░░░░░ 67% | 5.8k tokens | $0.14 | 67s elapsed

  Current leader: PopKit (faster, cheaper)
```

**This unlocks:**
- Testing different PopKit workflows against vanilla
- Measuring workflow efficiency (Quick vs Full vs Brainstorm)
- Validating orchestration value with real data
- Testing hypothesis about prompt quality compensation

### Phase 3: Cloud Integration (v1.2 - Pro Feature)

**Timeline:** 1-2 weeks
**Goal:** Enable sharing and basic history
**Dependency:** Requires Cloudflare Workers + Upstash setup

**Must Have:**
1. Cloud API endpoint
   - POST /api/benchmark/upload
   - Authentication (Pro tier validation)
   - Rate limiting (tier-based)

2. Upstash Redis storage
   - Benchmark summary storage
   - User history tracking
   - Share link generation

3. Share link system
   - Generate unique URLs (bench.popkit.dev/shared/{id})
   - 30-day expiration (Pro tier)
   - Unlisted (only accessible via link)

4. Historical queries
   - `/popkit:stats benchmark` command
   - View recent runs
   - Tier limit tracking

5. Tier enforcement
   - Free: 2 benchmarks/month
   - Pro: Unlimited
   - Team: Unlimited + private

**Cloud API flow:**
```typescript
// User uploads results (Pro tier only)
POST /api/benchmark/upload
Authorization: Bearer {popkit-pro-token}

Request:
{
  issueNumber: 237,
  results: {
    vanilla: { qualityScore: 8, duration: 127, ... },
    popkit: { qualityScore: 9, duration: 98, ... }
  },
  sharePublicly: false  // Pro users control privacy
}

Response:
{
  shareUrl: "https://bench.popkit.dev/shared/abc123",
  expiresAt: "2025-01-15T...",
  storedUntil: "2026-01-01T..."  // 1 year for Pro
}
```

### Phase 4: VHS Demo Highlights (v1.3)

**Timeline:** 1 week
**Goal:** Marketing and education materials

**Must Have:**
1. VHS tape generation
   - Extract key moments from benchmark runs
   - Generate .tape files automatically
   - Configurable scenes

2. Highlight selection algorithm
   - Workflow routing decisions (Quick vs Full)
   - Tool call efficiency (fewer operations)
   - Quality assessment results
   - Winner announcement

3. Automated rendering
   - Generate GIFs from .tape files
   - Multiple formats (GIF, MP4, WebM)
   - Optimized for web (< 5MB)

4. Template library
   - Quick Mode demo
   - Full Mode demo
   - Prompt quality comparison
   - Cost savings showcase

**VHS output:**
```bash
# Generate demo from benchmark
/popkit:benchmark issue #237 --demo

# Creates:
packages/plugin/assets/demos/
├── benchmark-237-full.tape      # Complete run
├── benchmark-237-highlights.tape # Key moments only (18s)
├── benchmark-237-highlights.gif  # Rendered GIF
└── benchmark-237-metadata.json   # Scene timings
```

### What We're NOT Building (Deferred to v2.0+)

**Phase 2 - Upstash Vector (Future):**
- ❌ Similarity search ("Find similar benchmarks")
- ❌ Pattern recognition ("What works for bug fixes?")
- ❌ Collective learning from anonymized results
- **Why defer:** Need critical mass of benchmark data first (100+)

**Phase 3 - Advanced Analytics (Future):**
- ❌ Trend analysis over time
- ❌ Team performance dashboards
- ❌ Custom scoring rubrics
- ❌ Workflow optimization suggestions
- **Why defer:** Build foundation first, validate with usage, then add based on real needs

**Rationale:** Ship v1.0-1.3 to validate the core concept, gather real usage data, then iterate based on actual user needs rather than assumptions.

### Complete Implementation Order

```
1. Phase 1 (v1.0) - 2-3 weeks
   └─> Foundation: Local benchmarks working
   └─> Deliverable: Can benchmark GitHub issues locally
   └─> Validation: Run 3-5 issues, document results

2. Phase 2 (v1.1) - 1-2 weeks
   └─> Interactive: Workflow testing working
   └─> Dependency: #237 (PopKit Workflow Benchmarking) must complete first
   └─> Deliverable: Can test Quick vs Full vs Brainstorm modes
   └─> Validation: Compare workflows on same issue

3. Phase 3 (v1.2) - 1-2 weeks
   └─> Cloud: Sharing and history working
   └─> Dependency: Cloudflare Workers + Upstash configured
   └─> Deliverable: Pro users can upload and share results
   └─> Validation: Upload 5 benchmarks, verify sharing works

4. Phase 4 (v1.3) - 1 week
   └─> Demos: VHS highlights working
   └─> Deliverable: Automated demo generation
   └─> Validation: Generate 3 demo GIFs for marketing

Total timeline: 5-8 weeks to complete benchmark system
```

### Relationship to Existing Issues

```
#250 (this design) - GitHub Issue Benchmark Tasks
  ├─> Depends on #237 - PopKit Workflow Benchmark Testing
  │   └─> Must implement benchmark response system first
  │
  ├─> Extends #220 - PopKit Benchmark Suite
  │   └─> Adds GitHub issues as new task category
  │
  └─> Uses infrastructure from #236 - Benchmark System Context
      └─> Leverages existing runner, metrics collection, reporting

Implementation dependency chain:
  1. #237 first (interactive workflow support)
  2. #250 second (GitHub issue integration)
  3. Both feed into #220 (complete benchmark suite)
```

## Acceptance Criteria

### Must Have (v1.0):
- [ ] Can run: `/popkit:benchmark issue #237`
- [ ] Creates isolated worktrees for each run
- [ ] Generates HTML report with side-by-side comparison
- [ ] Shows clear winner with metric breakdown
- [ ] Cleans up worktrees after completion
- [ ] Works entirely locally (no cloud required)

### Must Have (v1.1):
- [ ] Supports `/popkit:dev`, `/popkit:dev full`, `/popkit:dev brainstorm`
- [ ] Auto-answers interactive prompts via benchmark response system
- [ ] Tests prompt quality variations (vibe/junior/senior)
- [ ] Real-time token tracking during runs

### Must Have (v1.2):
- [ ] Pro users can upload results to cloud
- [ ] Generates shareable links (bench.popkit.dev/shared/{id})
- [ ] Enforces tier limits (Free: 2/month, Pro: unlimited)
- [ ] `/popkit:stats benchmark` shows history

### Must Have (v1.3):
- [ ] Generates VHS tape highlights (< 20 seconds)
- [ ] Automated GIF rendering
- [ ] Template library for common demos

### Nice to Have (Future):
- [ ] Upstash Vector similarity search
- [ ] Team performance dashboards
- [ ] Custom scoring rubrics
- [ ] Trend analysis over time

## Security & Privacy Considerations

### Code Exposure Protection

**Problem:** Scoring algorithms in public repo reveal competitive advantage

**Solution:**
```
Scoring logic stays in private monorepo (jrc1883/popkit)
├── packages/cloud/src/assessors/  (PRIVATE)
├── packages/plugin/hooks/utils/   (PRIVATE)
└── Quality detection patterns      (PRIVATE)

Public plugin repo (jrc1883/popkit-claude)
├── Commands (declarative only)
├── Skills (prompts, no logic)
└── Hook stubs (call cloud API)
```

### Data Privacy by Tier

```
Free:
  - Anonymized results contribute to collective learning
  - No PII (personally identifiable information)
  - Cannot be traced back to user

Pro:
  - Results private by default
  - Opt-in to share anonymously
  - Full data export available
  - Stored 1 year

Team:
  - Fully private, never shared
  - Can delete anytime
  - SOC2 compliant
  - Stored indefinitely
```

### Local Storage Security

```typescript
// What gets stored locally (safe to expose):
{
  qualityScore: 9,
  winner: "popkit",
  metrics: { duration: 98, cost: 0.24 },
  issueCategories: ["physics", "performance"]
  // Detection patterns NOT included
}

// What stays in cloud (protected):
{
  scoringAlgorithm: "...",      // How we calculate quality
  detectionPatterns: [...],     // Regex, heuristics
  assessorPrompts: "...",       // How we judge code
  weights: { tests: 0.4, ... }  // Scoring weights
}
```

## Next Steps

### Immediate (After Design Approval):
1. Create implementation plan for Phase 1 (v1.0)
   - Break down into tasks
   - Estimate effort
   - Assign priorities

2. Set up development environment
   - Ensure git worktree support
   - Test benchmark isolation
   - Validate cleanup procedures

3. Create first GitHub issue benchmark task
   - Select simple issue (bug fix)
   - Define success criteria
   - Write test cases

### Short Term (First Sprint):
1. Implement worktree isolation system
2. Extend task schema for GitHub issues
3. Build basic automated scoring
4. Generate first HTML report

### Medium Term (Phase 1 Complete):
1. Run 3-5 real issue benchmarks
2. Document results and findings
3. Validate hypotheses about prompt quality
4. Prepare for Phase 2 (interactive workflows)

### Long Term (Full System):
1. Implement Phases 2-4
2. Launch as Pro tier feature
3. Gather user feedback
4. Iterate based on real usage patterns

## Open Questions

1. **Issue selection criteria:** Which issues make good benchmarks?
   - Clear acceptance criteria?
   - Medium complexity (not too simple/complex)?
   - Representative of real work?

2. **Human review process:** How to scale manual review?
   - Review all benchmarks initially?
   - Only review close calls (<10 point difference)?
   - Spot-check random sample?

3. **Cost management:** How to control cloud benchmark costs?
   - Time limits per benchmark?
   - Token limits?
   - Abort if quality score drops below threshold?

4. **Marketing:** How to showcase benchmark results?
   - Public leaderboard (anonymized)?
   - Case studies from real issues?
   - Video demos vs GIF highlights?

## Appendix: Related Documents

- **Prompt Parity Investigation:** `docs/research/2025-12-15-prompt-parity-investigation.md`
- **Benchmark Quality Improvements:** `docs/research/2025-12-15-popkit-quality-improvements.md`
- **Final Benchmark Analysis:** `docs/research/2025-12-15-final-benchmark-analysis.md`
- **PopKit Workflow Benchmark Design:** `docs/plans/2025-12-15-popkit-workflow-benchmark-design.md` (#237)

## Conclusion

This design transforms PopKit's issue backlog into a comprehensive benchmark suite, validating PopKit's value proposition while making real progress on development work. By testing across multiple dimensions (execution modes, prompt quality, response patterns), we gain deep insights into when and how PopKit adds value compared to vanilla Claude Code.

**Key innovations:**
1. Real issues as test cases (not synthetic benchmarks)
2. Prompt quality as a test variable (vibe → junior → senior)
3. Multiple execution modes (Quick vs Full vs Brainstorm)
4. Benchmarking as a product feature (Free/Pro/Team tiers)
5. Security-first approach (scoring in cloud, not exposed locally)

**Expected outcome:** Quantifiable proof that PopKit maintains quality while improving efficiency, with clear guidance on which workflows fit which scenarios.

---

**Status:** Design complete - ready for implementation planning
**Next:** Create detailed implementation plan for Phase 1 (v1.0)
