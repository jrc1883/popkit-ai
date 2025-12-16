# GitHub Issue Benchmark Tasks

## Overview

Real PopKit GitHub issues as benchmark tasks enable validation of PopKit's value proposition with actual development workflows instead of synthetic tasks.

**Goal:** Compare vanilla Claude vs PopKit on real-world issues across different complexities and types.

---

## Available Benchmark Tasks

| ID | Issue | Type | Complexity | Files | Description |
|----|-------|------|------------|-------|-------------|
| `github-issue-238-ip-scanner` | #238 | Bug Fix | Small | 1-2 | Exit code enforcement in publish workflow |
| `github-issue-237-workflow` | #237 | Feature | Medium | 3-5 | Interactive workflow benchmark support |
| `github-issue-239-cache` | #239 | Architecture | Medium | 3-4 | GitHub metadata caching system |

---

## Branch Isolation Strategy

To prevent cross-contamination between vanilla and PopKit benchmark runs, use **git worktree-based isolation**:

### Why Worktrees?

1. **Isolation** - Each run has completely separate working directory
2. **Clean state** - No git history/config contamination
3. **Parallel execution** - Can run vanilla and PopKit simultaneously
4. **Easy cleanup** - Remove worktree when done

### Setup Process

```bash
# 1. Create vanilla run worktree
git worktree add /tmp/benchmark-vanilla-238 origin/master
cd /tmp/benchmark-vanilla-238
git checkout -b benchmark/vanilla-issue-238

# 2. Create PopKit run worktree
git worktree add /tmp/benchmark-popkit-238 origin/master
cd /tmp/benchmark-popkit-238
git checkout -b benchmark/popkit-issue-238

# 3. Run benchmarks independently
# (each has isolated .git, working tree, and history)

# 4. Cleanup after comparison
git worktree remove /tmp/benchmark-vanilla-238
git worktree remove /tmp/benchmark-popkit-238
```

### Automated Runner Script

```typescript
// packages/benchmarks/src/runners/github-issue-runner.ts

export class GitHubIssueBenchmarkRunner {
  async runComparison(issueNumber: number): Promise<ComparisonResult> {
    const vanillaDir = `/tmp/benchmark-vanilla-${issueNumber}`;
    const popkitDir = `/tmp/benchmark-popkit-${issueNumber}`;

    try {
      // Setup worktrees
      await this.createWorktree(vanillaDir, `benchmark/vanilla-issue-${issueNumber}`);
      await this.createWorktree(popkitDir, `benchmark/popkit-issue-${issueNumber}`);

      // Run vanilla benchmark
      const vanillaResult = await this.runBenchmark(vanillaDir, 'vanilla', issueNumber);

      // Run PopKit benchmark
      const popkitResult = await this.runBenchmark(popkitDir, 'popkit', issueNumber);

      // Compare results
      return this.compareResults(vanillaResult, popkitResult);

    } finally {
      // Cleanup
      await this.removeWorktree(vanillaDir);
      await this.removeWorktree(popkitDir);
    }
  }

  private async createWorktree(path: string, branch: string): Promise<void> {
    await exec(`git worktree add ${path} origin/master`);
    await exec(`cd ${path} && git checkout -b ${branch}`);
  }

  private async removeWorktree(path: string): Promise<void> {
    await exec(`git worktree remove ${path}`);
  }
}
```

---

## Judging Rubric

### Scoring Dimensions

Each benchmark run is scored across 6 dimensions (0-10 scale):

#### 1. Correctness (Weight: 30%)

**Measures:** Does the solution solve the issue?

| Score | Criteria |
|-------|----------|
| 10 | All acceptance criteria met, all tests pass |
| 8 | Most criteria met, minor edge cases missed |
| 6 | Core functionality works, some criteria missing |
| 4 | Partial solution, significant gaps |
| 2 | Attempted but fundamentally broken |
| 0 | No solution or completely off-track |

**Automated Checks:**
- Unit tests pass: +3 points
- Integration tests pass: +3 points
- All acceptance criteria verified: +4 points

---

#### 2. Completeness (Weight: 20%)

**Measures:** Are all requested files/features implemented?

| Score | Criteria |
|-------|----------|
| 10 | All files created, all features implemented |
| 8 | All core files, 1-2 minor features missing |
| 6 | Most files, some features incomplete |
| 4 | Significant missing components |
| 2 | Only partial implementation |
| 0 | Nothing delivered |

**Automated Checks:**
- Required files exist: Count / Expected Count × 10
- Features implemented: Count / Expected Count × 10
- Average for final score

---

#### 3. Code Quality (Weight: 20%)

**Measures:** Is the code production-ready?

| Score | Criteria |
|-------|----------|
| 10 | Excellent: Clean, well-documented, robust error handling |
| 8 | Good: Minor style issues, adequate documentation |
| 6 | Acceptable: Works but lacks polish |
| 4 | Poor: Brittle code, minimal documentation |
| 2 | Very poor: Code smells, no error handling |
| 0 | Unusable code |

**Automated Checks:**
- Type hints/annotations: +2 points
- Error handling (try/catch): +2 points
- Documentation/comments: +2 points
- Follows conventions: +2 points
- No code smells (linter): +2 points

---

#### 4. Efficiency (Weight: 15%)

**Measures:** How efficiently was the task completed?

| Metric | Weight | Formula |
|--------|--------|---------|
| **Tokens Used** | 40% | `max(0, 10 - (actual / baseline) × 5)` |
| **Duration** | 30% | `max(0, 10 - (actual / baseline) × 5)` |
| **Tool Calls** | 30% | `max(0, 10 - (actual / baseline) × 5)` |

**Example:**
```
Baseline: 40,000 tokens, 400s, 50 tool calls
Actual: 30,000 tokens, 300s, 35 tool calls

Token Score: max(0, 10 - (30000/40000) × 5) = max(0, 10 - 3.75) = 6.25
Duration Score: max(0, 10 - (300/400) × 5) = max(0, 10 - 3.75) = 6.25
Tool Calls Score: max(0, 10 - (35/50) × 5) = max(0, 10 - 3.5) = 6.5

Efficiency Score: 6.25 × 0.4 + 6.25 × 0.3 + 6.5 × 0.3 = 6.325
```

---

#### 5. Following Best Practices (Weight: 10%)

**Measures:** Does code follow language/framework conventions?

| Score | Criteria |
|-------|----------|
| 10 | Follows all conventions, uses modern patterns |
| 8 | Mostly conventional, minor deviations |
| 6 | Acceptable but dated patterns |
| 4 | Several convention violations |
| 2 | Ignores conventions |
| 0 | Anti-patterns present |

**Automated Checks:**
- Linter passes: +5 points
- Security scan clean: +3 points
- Complexity within limits: +2 points

---

#### 6. Approach & Strategy (Weight: 5%)

**Measures:** Did the approach demonstrate good problem-solving?

| Score | Criteria |
|-------|----------|
| 10 | Excellent planning, systematic exploration, smart decisions |
| 8 | Good approach, minor missteps recovered |
| 6 | Adequate but inefficient exploration |
| 4 | Trial-and-error without clear strategy |
| 2 | Chaotic, repeated mistakes |
| 0 | No clear approach |

**Manual Evaluation:**
- Reviewed by human scorer
- Based on transcript analysis
- Considers: planning, exploration, recovery, decision quality

---

### Overall Score Calculation

```
Overall Score =
  Correctness × 0.30 +
  Completeness × 0.20 +
  Code Quality × 0.20 +
  Efficiency × 0.15 +
  Best Practices × 0.10 +
  Approach × 0.05
```

**Example:**

| Dimension | Score | Weight | Weighted |
|-----------|-------|--------|----------|
| Correctness | 9 | 30% | 2.70 |
| Completeness | 8 | 20% | 1.60 |
| Code Quality | 9 | 20% | 1.80 |
| Efficiency | 6.3 | 15% | 0.95 |
| Best Practices | 8 | 10% | 0.80 |
| Approach | 9 | 5% | 0.45 |
| **TOTAL** | - | - | **8.30** |

---

## Comparison Report Format

```markdown
# Benchmark Comparison: Issue #238 - IP Leak Scanner

## Executive Summary

**Winner:** PopKit (+1.5 points, 18% improvement)

| Metric | Vanilla | PopKit | Improvement |
|--------|---------|--------|-------------|
| **Overall Score** | 7.0 | 8.5 | +21% |
| Duration | 180s | 120s | -33% |
| Tokens | 25,000 | 18,000 | -28% |
| Quality | 7/10 | 9/10 | +29% |

---

## Detailed Breakdown

### Correctness (Weight: 30%)

| Criteria | Vanilla | PopKit |
|----------|---------|--------|
| Exit code enforcement | ✅ Yes | ✅ Yes |
| --skip-ip-scan flag | ❌ No | ✅ Yes |
| Error messages | ⚠️ Basic | ✅ Helpful |
| Tests pass | ✅ 8/10 | ✅ 10/10 |
| **Score** | **7/10** | **10/10** |

**Winner:** PopKit (+3 points)

---

### Efficiency (Weight: 15%)

| Metric | Vanilla | PopKit | Delta |
|--------|---------|--------|-------|
| Tokens | 25,000 | 18,000 | -28% |
| Duration | 180s | 120s | -33% |
| Tool Calls | 30 | 22 | -27% |
| **Score** | **6.0/10** | **7.5/10** |

**Winner:** PopKit (+1.5 points)

---

### Code Quality (Weight: 20%)

**Vanilla:**
```bash
# Basic implementation, minimal error handling
if python ip_scanner.py; then
    echo "Scan passed"
fi
git subtree split...
```

**PopKit:**
```bash
# Robust implementation with clear messages
if [[ \"$SKIP_IP_SCAN\" != \"true\" ]]; then
    python ip_scanner.py packages/plugin/ --pre-publish
    if [[ $? -ne 0 ]]; then
        echo \"❌ Publish blocked by IP leak scanner.\"
        echo \"Review findings above.\"
        echo \"To override: $0 --skip-ip-scan\"
        exit 1
    fi
fi
```

| Aspect | Vanilla | PopKit |
|--------|---------|--------|
| Error Handling | ⚠️ Basic | ✅ Comprehensive |
| User Messages | ⚠️ Minimal | ✅ Clear & Helpful |
| Documentation | ❌ None | ✅ README |
| **Score** | **6/10** | **9/10** |

**Winner:** PopKit (+3 points)

---

## Conclusion

PopKit demonstrated superior performance across all dimensions:

1. **Correctness** - Implemented all features including --skip-ip-scan flag
2. **Efficiency** - 28% fewer tokens, 33% faster completion
3. **Quality** - Better error handling, user-friendly messages, documentation

**Recommendation:** PopKit provides measurable value for bug fix workflows.
```

---

## Running GitHub Issue Benchmarks

### Command Line

```bash
# Run single issue benchmark (both modes)
npx tsx run-benchmark.ts github-issue-238

# Run specific mode only
npx tsx run-benchmark.ts github-issue-238 vanilla
npx tsx run-benchmark.ts github-issue-238 popkit

# Run all GitHub issue benchmarks
npx tsx run-benchmark.ts --category github-issue

# Generate comparison report
npx tsx generate-report.ts github-issue-238 --format markdown
```

### Programmatic API

```typescript
import { GitHubIssueBenchmarkRunner } from './runners/github-issue-runner';

const runner = new GitHubIssueBenchmarkRunner();

// Run comparison
const result = await runner.runComparison(238);

// Generate report
const report = await runner.generateReport(result);

console.log(report);
```

---

## Adding New GitHub Issue Benchmarks

### Selection Criteria

Choose issues that:
1. **Have clear acceptance criteria** - Testable success metrics
2. **Vary in complexity** - Small (1-2 files), Medium (3-5 files), Large (6+ files)
3. **Represent real work** - Actual PopKit development tasks
4. **Test different skills** - Bug fixes, features, refactoring, architecture

### Creation Process

1. **Select issue** - Review closed/open issues for good candidates
2. **Extract requirements** - Pull acceptance criteria, success metrics
3. **Simplify scope** - Remove dependencies on external services
4. **Create task JSON** - Follow schema in existing tasks
5. **Write tests** - Automated validation of correctness
6. **Define baseline** - Expected metrics for vanilla/PopKit
7. **Validate** - Test both modes to ensure fairness

### Task JSON Template

See `tasks/github-issue-239-cache.json` for complete example.

---

## Quality Assurance

### Before Adding Task

- [ ] Issue has clear acceptance criteria
- [ ] Requirements are self-contained (no external APIs)
- [ ] Baseline metrics are realistic
- [ ] Tests verify all acceptance criteria
- [ ] Task JSON validates against schema
- [ ] Both vanilla and PopKit modes complete successfully
- [ ] Judging rubric applies fairly to both modes

### After Benchmark Run

- [ ] Results match baseline expectations (±20%)
- [ ] Winner is clear and explainable
- [ ] No bugs or errors in task setup
- [ ] Report is comprehensive and actionable

---

## Future Enhancements

- [ ] Automated scorer (ML-based quality assessment)
- [ ] Multi-turn benchmarks (PR review → fix → retest)
- [ ] Team collaboration benchmarks (multi-agent coordination)
- [ ] Performance regression tracking (monitor trends)
- [ ] Public leaderboard (compare PopKit versions)

---

**Created:** 2025-12-15
**Author:** PopKit Benchmark Team
**Status:** Active - 3 benchmark tasks available
