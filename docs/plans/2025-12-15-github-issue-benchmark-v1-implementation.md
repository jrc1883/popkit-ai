# GitHub Issue Benchmark System v1.0 Implementation Plan

> **For Claude:** Use executing-plans skill to implement this plan task-by-task.

**Goal:** Enable benchmarking of real PopKit GitHub issues comparing vanilla Claude Code vs PopKit locally without cloud dependencies.

**Architecture:** Git worktree isolation for parallel runs, TypeScript task schema extensions, automated quality scoring, standalone HTML reports.

**Tech Stack:** TypeScript, Node.js, git worktrees, HTML/CSS/JavaScript (no external dependencies)

**Design Document:** `docs/plans/2025-12-15-github-issue-benchmark-design.md`

**Related Issue:** #250

---

## Phase 1 Overview (v1.0 - Local Only)

**Timeline:** 2-3 weeks
**Deliverable:** Can benchmark GitHub issues locally with HTML reports

**Must Have:**
1. Git worktree isolation system
2. Task schema extension (`GitHubIssueBenchmark` type)
3. Basic automated scoring (tests + quality)
4. HTML report generation (standalone)
5. `/popkit:benchmark issue #N` command

**Success Criteria:**
- Can run: `/popkit:benchmark issue #237`
- Creates isolated worktrees with separate branches
- Generates shareable HTML report
- Shows clear winner with metrics
- Cleans up worktrees after completion

---

## Task 1: Extend TypeScript Types for GitHub Issues

**Files:**
- Modify: `packages/benchmarks/src/types.ts`
- Test: `packages/benchmarks/src/__tests__/types.test.ts` (create if needed)

### Step 1: Write type definition test

```typescript
// packages/benchmarks/src/__tests__/types.test.ts
import { GitHubIssueBenchmark } from '../types';

describe('GitHubIssueBenchmark', () => {
  it('should accept valid GitHub issue benchmark configuration', () => {
    const task: GitHubIssueBenchmark = {
      id: 'github-issue-237',
      name: 'PopKit Workflow Benchmark Testing',
      category: 'github-issue',
      language: 'typescript',
      version: '1.0.0',

      githubIssue: {
        repo: 'jrc1883/popkit',
        number: 237,
        url: 'https://github.com/jrc1883/popkit/issues/237'
      },

      executionModes: {
        vanilla: {
          prompt: 'Implement #237 - PopKit Workflow Benchmark Testing...'
        },
        popkitQuick: {
          command: '/popkit:dev "Implement #237"',
          responses: {
            "What's next?": "Create implementation plan",
            "Commit changes?": true
          }
        }
      },

      initialFiles: {},
      dependencies: [],
      setupCommands: [],
      prompt: '',
      context: '',
      maxTokens: 50000,
      timeoutSeconds: 300,
      tests: [],
      qualityChecks: [],
      successCriteria: [
        'Tests pass',
        'Type check passes'
      ],
      baseline: {
        vanilla: {
          tokenEstimate: 15000,
          toolCallEstimate: 25,
          successRate: 0.7,
          timeEstimate: 180,
          qualityEstimate: 7.5
        },
        popkit: {
          tokenEstimate: 10000,
          toolCallEstimate: 15,
          successRate: 0.9,
          timeEstimate: 120,
          qualityEstimate: 8.5
        }
      },
      tags: ['github-issue', 'benchmark'],
      author: 'PopKit Team',
      createdAt: new Date().toISOString()
    };

    expect(task.category).toBe('github-issue');
    expect(task.githubIssue.number).toBe(237);
    expect(task.executionModes.vanilla).toBeDefined();
  });
});
```

### Step 2: Run test to verify it fails

Run: `cd packages/benchmarks && npm test -- types.test.ts`
Expected: FAIL with "Type 'GitHubIssueBenchmark' does not exist"

### Step 3: Add type definitions

```typescript
// packages/benchmarks/src/types.ts

// Add to existing BenchmarkCategory type
export type BenchmarkCategory =
  | 'standard'
  | 'performance'
  | 'security'
  | 'github-issue';  // NEW

// Add new interface after BenchmarkTask
export interface GitHubIssueBenchmark extends BenchmarkTask {
  category: 'github-issue';

  githubIssue: {
    repo: string;
    number: number;
    url: string;
  };

  executionModes: {
    vanilla: {
      prompt: string;
    };
    popkitQuick?: {
      command: string;
      responses: Record<string, any>;
    };
    popkitFull?: {
      command: string;
      responses: Record<string, any>;
    };
    popkitBrainstorm?: {
      command: string;
      responses: Record<string, any>;
    };
  };

  successCriteria: string[];
}
```

### Step 4: Run test to verify it passes

Run: `cd packages/benchmarks && npm test -- types.test.ts`
Expected: PASS

### Step 5: Commit

```bash
git add packages/benchmarks/src/types.ts packages/benchmarks/src/__tests__/types.test.ts
git commit -m "feat(benchmarks): add GitHubIssueBenchmark type definition

Extends BenchmarkTask with:
- GitHub issue metadata (repo, number, URL)
- Multiple execution modes (vanilla, popkitQuick, popkitFull, popkitBrainstorm)
- Success criteria from issue acceptance criteria

Part of: #250 Phase 1 (v1.0)"
```

---

## Task 2: Git Worktree Isolation Utility

**Files:**
- Create: `packages/benchmarks/src/worktree.ts`
- Test: `packages/benchmarks/src/__tests__/worktree.test.ts`

### Step 1: Write failing test

```typescript
// packages/benchmarks/src/__tests__/worktree.test.ts
import { createBenchmarkWorktree, cleanupWorktree } from '../worktree';
import { execSync } from 'child_process';
import { existsSync, mkdtempSync } from 'fs';
import { join } from 'path';
import { tmpdir } from 'os';

describe('Worktree Management', () => {
  let testRepo: string;

  beforeEach(() => {
    // Create a test git repo
    testRepo = mkdtempSync(join(tmpdir(), 'bench-test-'));
    execSync('git init', { cwd: testRepo });
    execSync('git config user.email "test@test.com"', { cwd: testRepo });
    execSync('git config user.name "Test"', { cwd: testRepo });
    execSync('echo "test" > README.md', { cwd: testRepo });
    execSync('git add . && git commit -m "initial"', { cwd: testRepo });
  });

  it('should create isolated worktree with branch', async () => {
    const issueNumber = 237;
    const mode = 'vanilla';

    const worktree = await createBenchmarkWorktree(testRepo, issueNumber, mode);

    expect(worktree.path).toContain('bench-vanilla-237');
    expect(existsSync(worktree.path)).toBe(true);
    expect(worktree.branch).toMatch(/benchmark\/vanilla-issue-237-\d+/);

    // Verify branch exists
    const branches = execSync('git branch --all', { cwd: testRepo }).toString();
    expect(branches).toContain(worktree.branch);
  });

  it('should cleanup worktree and branch', async () => {
    const issueNumber = 237;
    const mode = 'popkit';

    const worktree = await createBenchmarkWorktree(testRepo, issueNumber, mode);
    expect(existsSync(worktree.path)).toBe(true);

    await cleanupWorktree(testRepo, worktree.path);

    expect(existsSync(worktree.path)).toBe(false);

    // Branch should still exist (for reference)
    const branches = execSync('git branch --all', { cwd: testRepo }).toString();
    expect(branches).toContain(worktree.branch);
  });
});
```

### Step 2: Run test to verify it fails

Run: `cd packages/benchmarks && npm test -- worktree.test.ts`
Expected: FAIL with "Cannot find module '../worktree'"

### Step 3: Implement worktree utilities

```typescript
// packages/benchmarks/src/worktree.ts
import { exec } from 'child_process';
import { promisify } from 'util';
import { join } from 'path';
import { tmpdir } from 'os';

const execAsync = promisify(exec);

export interface BenchmarkWorktree {
  path: string;
  branch: string;
}

export async function createBenchmarkWorktree(
  repoPath: string,
  issueNumber: number,
  mode: 'vanilla' | 'popkit'
): Promise<BenchmarkWorktree> {
  const timestamp = Date.now();
  const branchName = `benchmark/${mode}-issue-${issueNumber}-${timestamp}`;
  const worktreePath = join(tmpdir(), `bench-${mode}-${issueNumber}-${timestamp}`);

  // Create worktree
  await execAsync(
    `git worktree add ${worktreePath} -b ${branchName} origin/master`,
    { cwd: repoPath }
  );

  return {
    path: worktreePath,
    branch: branchName
  };
}

export async function cleanupWorktree(
  repoPath: string,
  worktreePath: string
): Promise<void> {
  // Remove worktree (keep branch for reference)
  await execAsync(`git worktree remove ${worktreePath}`, { cwd: repoPath });
}

export async function listWorktrees(repoPath: string): Promise<string[]> {
  const { stdout } = await execAsync('git worktree list --porcelain', { cwd: repoPath });
  const lines = stdout.split('\n');
  const worktrees: string[] = [];

  for (const line of lines) {
    if (line.startsWith('worktree ')) {
      worktrees.push(line.replace('worktree ', ''));
    }
  }

  return worktrees;
}
```

### Step 4: Run test to verify it passes

Run: `cd packages/benchmarks && npm test -- worktree.test.ts`
Expected: PASS

### Step 5: Commit

```bash
git add packages/benchmarks/src/worktree.ts packages/benchmarks/src/__tests__/worktree.test.ts
git commit -m "feat(benchmarks): add git worktree isolation utilities

Creates separate worktrees for vanilla and PopKit runs:
- createBenchmarkWorktree: Creates isolated workspace with branch
- cleanupWorktree: Removes worktree after completion
- listWorktrees: Lists active worktrees

Benefits:
- Complete isolation (no cross-contamination)
- Parallel execution (both run simultaneously)
- Space efficient (shared .git directory)

Part of: #250 Phase 1 (v1.0)"
```

---

## Task 3: Basic Automated Scoring Engine

**Files:**
- Create: `packages/benchmarks/src/scoring.ts`
- Test: `packages/benchmarks/src/__tests__/scoring.test.ts`

### Step 1: Write failing test

```typescript
// packages/benchmarks/src/__tests__/scoring.test.ts
import { calculateQualityScore, ScoreComponents } from '../scoring';
import { ExecutionResult } from '../types';

describe('Automated Scoring', () => {
  it('should calculate quality score with all components', () => {
    const result: Partial<ExecutionResult> = {
      success: true,
      testResults: {
        total: 6,
        passed: 6,
        failed: 0,
        skipped: 0,
        results: []
      }
    };

    const components: ScoreComponents = {
      testsPass: true,              // 40%
      acceptanceCriteria: 100,      // 30% (all criteria met)
      codeQuality: 90,              // 20% (lint + type check)
      efficiency: 85                // 10% (time/tokens/cost)
    };

    const score = calculateQualityScore(components);

    // Expected: 40 + 30 + 18 + 8.5 = 96.5
    expect(score).toBeCloseTo(96.5, 1);
  });

  it('should heavily penalize failing tests', () => {
    const components: ScoreComponents = {
      testsPass: false,             // 0 (tests failed)
      acceptanceCriteria: 100,      // 30%
      codeQuality: 100,             // 20%
      efficiency: 100               // 10%
    };

    const score = calculateQualityScore(components);

    // Expected: 0 + 30 + 20 + 10 = 60 (failing grade)
    expect(score).toBe(60);
  });
});
```

### Step 2: Run test to verify it fails

Run: `cd packages/benchmarks && npm test -- scoring.test.ts`
Expected: FAIL with "Cannot find module '../scoring'"

### Step 3: Implement scoring engine

```typescript
// packages/benchmarks/src/scoring.ts

export interface ScoreComponents {
  testsPass: boolean;           // 40% weight
  acceptanceCriteria: number;   // 30% weight (0-100%)
  codeQuality: number;          // 20% weight (0-100)
  efficiency: number;           // 10% weight (0-100)
}

export function calculateQualityScore(components: ScoreComponents): number {
  const {
    testsPass,
    acceptanceCriteria,
    codeQuality,
    efficiency
  } = components;

  const score = (
    (testsPass ? 40 : 0) +
    (acceptanceCriteria * 0.3) +
    (codeQuality * 0.2) +
    (efficiency * 0.1)
  );

  return Math.round(score * 10) / 10; // Round to 1 decimal
}

export async function assessCodeQuality(
  workspacePath: string
): Promise<number> {
  let score = 100;

  // Check lint (if configured)
  try {
    const { execSync } = require('child_process');
    execSync('npm run lint', { cwd: workspacePath, stdio: 'pipe' });
  } catch (e) {
    score -= 30; // Lint errors
  }

  // Check type check (if TypeScript)
  try {
    const { execSync } = require('child_process');
    execSync('npx tsc --noEmit', { cwd: workspacePath, stdio: 'pipe' });
  } catch (e) {
    score -= 30; // Type errors
  }

  return Math.max(0, score);
}

export function calculateEfficiencyScore(
  duration: number,
  tokens: number,
  cost: number,
  baseline: { timeEstimate: number; tokenEstimate: number }
): number {
  let score = 100;

  // Time efficiency (faster = better)
  const timeRatio = duration / baseline.timeEstimate;
  if (timeRatio > 1.5) score -= 30; // 50% slower
  else if (timeRatio > 1.2) score -= 15; // 20% slower
  else if (timeRatio < 0.8) score += 10; // 20% faster (bonus)

  // Token efficiency (fewer = better)
  const tokenRatio = tokens / baseline.tokenEstimate;
  if (tokenRatio > 1.5) score -= 20; // 50% more tokens
  else if (tokenRatio > 1.2) score -= 10; // 20% more tokens

  return Math.max(0, Math.min(100, score));
}
```

### Step 4: Run test to verify it passes

Run: `cd packages/benchmarks && npm test -- scoring.test.ts`
Expected: PASS

### Step 5: Commit

```bash
git add packages/benchmarks/src/scoring.ts packages/benchmarks/src/__tests__/scoring.test.ts
git commit -m "feat(benchmarks): add automated quality scoring engine

Scoring components (weighted):
- Tests pass: 40%
- Acceptance criteria: 30%
- Code quality (lint + type): 20%
- Efficiency (time + tokens): 10%

Functions:
- calculateQualityScore: Computes overall score
- assessCodeQuality: Checks lint and type errors
- calculateEfficiencyScore: Compares to baseline

Part of: #250 Phase 1 (v1.0)"
```

---

## Task 4: HTML Report Generator

**Files:**
- Create: `packages/benchmarks/src/reports/html-generator.ts`
- Create: `packages/benchmarks/src/reports/templates/report.html`
- Test: `packages/benchmarks/src/__tests__/html-generator.test.ts`

### Step 1: Write failing test

```typescript
// packages/benchmarks/src/__tests__/html-generator.test.ts
import { generateHTMLReport } from '../reports/html-generator';
import { ExecutionResult } from '../types';
import { readFileSync } from 'fs';

describe('HTML Report Generator', () => {
  it('should generate standalone HTML report', async () => {
    const vanillaResult: Partial<ExecutionResult> = {
      success: true,
      durationSeconds: 127,
      tokens: { total: 12400 },
      toolCalls: 23,
      testResults: { total: 6, passed: 5, failed: 1 }
    };

    const popkitResult: Partial<ExecutionResult> = {
      success: true,
      durationSeconds: 98,
      tokens: { total: 9800 },
      toolCalls: 18,
      testResults: { total: 6, passed: 6, failed: 0 }
    };

    const htmlPath = await generateHTMLReport({
      issueNumber: 237,
      vanilla: vanillaResult as ExecutionResult,
      popkit: popkitResult as ExecutionResult,
      outputDir: '/tmp/test-report'
    });

    const html = readFileSync(htmlPath, 'utf-8');

    // Should be standalone (no external dependencies)
    expect(html).not.toContain('<script src=');
    expect(html).not.toContain('<link rel="stylesheet" href=');

    // Should contain comparison data
    expect(html).toContain('Issue #237');
    expect(html).toContain('127s'); // Vanilla duration
    expect(html).toContain('98s');  // PopKit duration
    expect(html).toContain('PopKit'); // Winner indication
  });
});
```

### Step 2: Run test to verify it fails

Run: `cd packages/benchmarks && npm test -- html-generator.test.ts`
Expected: FAIL with "Cannot find module '../reports/html-generator'"

### Step 3: Create HTML template

```html
<!-- packages/benchmarks/src/reports/templates/report.html -->
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Benchmark Report: Issue #{{ISSUE_NUMBER}}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
      line-height: 1.6;
      color: #333;
      padding: 20px;
      max-width: 1200px;
      margin: 0 auto;
      background: #f5f5f5;
    }
    .header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 30px;
      border-radius: 8px;
      margin-bottom: 20px;
    }
    .header h1 { font-size: 2em; margin-bottom: 10px; }
    .header .subtitle { opacity: 0.9; font-size: 1.1em; }
    .summary {
      background: white;
      padding: 20px;
      border-radius: 8px;
      margin-bottom: 20px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .winner {
      font-size: 1.5em;
      font-weight: bold;
      color: #10b981;
      margin-bottom: 10px;
    }
    .scores {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 15px;
      margin-top: 15px;
    }
    .score-card {
      background: #f9fafb;
      padding: 15px;
      border-radius: 6px;
      border-left: 4px solid #667eea;
    }
    .score-card h3 { font-size: 0.9em; color: #666; margin-bottom: 5px; }
    .score-card .value { font-size: 1.8em; font-weight: bold; color: #333; }
    .comparison-table {
      background: white;
      padding: 20px;
      border-radius: 8px;
      margin-bottom: 20px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    table {
      width: 100%;
      border-collapse: collapse;
    }
    th, td {
      padding: 12px;
      text-align: left;
      border-bottom: 1px solid #e5e7eb;
    }
    th {
      background: #f9fafb;
      font-weight: 600;
      color: #374151;
    }
    .winner-cell {
      color: #10b981;
      font-weight: bold;
    }
    .loser-cell {
      color: #ef4444;
    }
    .tie-cell {
      color: #f59e0b;
    }
    .actions {
      background: white;
      padding: 20px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    button {
      background: #667eea;
      color: white;
      border: none;
      padding: 12px 24px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 1em;
      margin-right: 10px;
      margin-bottom: 10px;
    }
    button:hover {
      background: #5568d3;
    }
    @media print {
      body { background: white; }
      button { display: none; }
    }
  </style>
</head>
<body>
  <div class="header">
    <h1>PopKit vs Vanilla: Issue #{{ISSUE_NUMBER}}</h1>
    <div class="subtitle">{{ISSUE_TITLE}}</div>
  </div>

  <div class="summary">
    <div class="winner">🏆 Winner: {{WINNER}}</div>
    <div class="scores">
      <div class="score-card">
        <h3>Quality Score</h3>
        <div class="value">{{QUALITY_WINNER}}</div>
      </div>
      <div class="score-card">
        <h3>Speed</h3>
        <div class="value">{{SPEED_WINNER}}</div>
      </div>
      <div class="score-card">
        <h3>Cost</h3>
        <div class="value">{{COST_WINNER}}</div>
      </div>
      <div class="score-card">
        <h3>Tests Passed</h3>
        <div class="value">{{TESTS_WINNER}}</div>
      </div>
    </div>
  </div>

  <div class="comparison-table">
    <h2>Detailed Comparison</h2>
    <table>
      <thead>
        <tr>
          <th>Metric</th>
          <th>Vanilla</th>
          <th>PopKit</th>
          <th>Winner</th>
        </tr>
      </thead>
      <tbody>
        {{COMPARISON_ROWS}}
      </tbody>
    </table>
  </div>

  <div class="actions">
    <h2>Export Options</h2>
    <button onclick="window.print()">Print / Export as PDF</button>
    <button onclick="downloadJSON()">Download Raw Data</button>
    <button onclick="copyShareLink()">Copy Share Link</button>
  </div>

  <script>
    function downloadJSON() {
      const data = {{RAW_DATA}};
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'benchmark-issue-{{ISSUE_NUMBER}}.json';
      a.click();
    }

    function copyShareLink() {
      alert('Share link feature available in Pro tier');
    }
  </script>
</body>
</html>
```

### Step 4: Implement HTML generator

```typescript
// packages/benchmarks/src/reports/html-generator.ts
import { readFileSync, writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';
import { ExecutionResult } from '../types';
import { calculateQualityScore } from '../scoring';

interface HTMLReportOptions {
  issueNumber: number;
  vanilla: ExecutionResult;
  popkit: ExecutionResult;
  outputDir: string;
}

export async function generateHTMLReport(options: HTMLReportOptions): Promise<string> {
  const { issueNumber, vanilla, popkit, outputDir } = options;

  // Load template
  const templatePath = join(__dirname, 'templates', 'report.html');
  let html = readFileSync(templatePath, 'utf-8');

  // Calculate scores (simplified for now)
  const vanillaScore = (vanilla.testResults?.passed || 0) / (vanilla.testResults?.total || 1) * 10;
  const popkitScore = (popkit.testResults?.passed || 0) / (popkit.testResults?.total || 1) * 10;

  // Determine winner
  let winCount = 0;
  if (popkitScore > vanillaScore) winCount++;
  if (popkit.durationSeconds < vanilla.durationSeconds) winCount++;
  if ((popkit.usageDetails?.costUsd || 0) < (vanilla.usageDetails?.costUsd || 0)) winCount++;
  if ((popkit.testResults?.passed || 0) > (vanilla.testResults?.passed || 0)) winCount++;

  const winner = winCount >= 2 ? 'PopKit' : winCount === 0 ? 'Vanilla' : 'Tie';

  // Build comparison rows
  const rows = [
    buildRow('Duration', `${vanilla.durationSeconds}s`, `${popkit.durationSeconds}s`,
             popkit.durationSeconds < vanilla.durationSeconds ? 'PopKit' : 'Vanilla'),
    buildRow('Cost', `$${vanilla.usageDetails?.costUsd.toFixed(2)}`, `$${popkit.usageDetails?.costUsd.toFixed(2)}`,
             (popkit.usageDetails?.costUsd || 0) < (vanilla.usageDetails?.costUsd || 0) ? 'PopKit' : 'Vanilla'),
    buildRow('Quality Score', `${vanillaScore.toFixed(1)}/10`, `${popkitScore.toFixed(1)}/10`,
             popkitScore > vanillaScore ? 'PopKit' : 'Vanilla'),
    buildRow('Tests Passed', `${vanilla.testResults?.passed}/${vanilla.testResults?.total}`,
             `${popkit.testResults?.passed}/${popkit.testResults?.total}`,
             (popkit.testResults?.passed || 0) > (vanilla.testResults?.passed || 0) ? 'PopKit' : 'Vanilla'),
    buildRow('Tool Calls', `${vanilla.toolCalls}`, `${popkit.toolCalls}`,
             popkit.toolCalls < vanilla.toolCalls ? 'PopKit' : 'Vanilla')
  ].join('\n');

  // Replace placeholders
  html = html.replace(/\{\{ISSUE_NUMBER\}\}/g, issueNumber.toString());
  html = html.replace('{{ISSUE_TITLE}}', `Benchmark for issue ${issueNumber}`);
  html = html.replace('{{WINNER}}', winner);
  html = html.replace('{{QUALITY_WINNER}}', `${popkitScore.toFixed(1)} vs ${vanillaScore.toFixed(1)}`);
  html = html.replace('{{SPEED_WINNER}}', `${popkit.durationSeconds}s vs ${vanilla.durationSeconds}s`);
  html = html.replace('{{COST_WINNER}}', `$${popkit.usageDetails?.costUsd.toFixed(2)} vs $${vanilla.usageDetails?.costUsd.toFixed(2)}`);
  html = html.replace('{{TESTS_WINNER}}', `${popkit.testResults?.passed}/${popkit.testResults?.total}`);
  html = html.replace('{{COMPARISON_ROWS}}', rows);
  html = html.replace('{{RAW_DATA}}', JSON.stringify({ vanilla, popkit }));

  // Write file
  mkdirSync(outputDir, { recursive: true });
  const outputPath = join(outputDir, 'report.html');
  writeFileSync(outputPath, html);

  return outputPath;
}

function buildRow(metric: string, vanilla: string, popkit: string, winner: string): string {
  const winnerClass = winner === 'PopKit' ? 'winner-cell' : winner === 'Vanilla' ? 'loser-cell' : 'tie-cell';
  return `
    <tr>
      <td>${metric}</td>
      <td>${vanilla}</td>
      <td>${popkit}</td>
      <td class="${winnerClass}">${winner}</td>
    </tr>
  `;
}
```

### Step 5: Run test to verify it passes

Run: `cd packages/benchmarks && npm test -- html-generator.test.ts`
Expected: PASS

### Step 6: Commit

```bash
git add packages/benchmarks/src/reports/ packages/benchmarks/src/__tests__/html-generator.test.ts
git commit -m "feat(benchmarks): add standalone HTML report generator

Creates shareable HTML reports with:
- Executive summary (winner, key metrics)
- Detailed comparison table
- Export options (PDF, JSON)
- No external dependencies (fully self-contained)

Template features:
- Responsive design
- Print-friendly
- Interactive (download raw data)

Part of: #250 Phase 1 (v1.0)"
```

---

## Task 5: Benchmark Command Implementation

**Files:**
- Create: `packages/plugin/commands/benchmark.md`
- Modify: `packages/plugin/.claude-plugin/plugin.json` (add command trigger)

### Step 1: Write command documentation

```markdown
<!-- packages/plugin/commands/benchmark.md -->
---
description: Benchmark GitHub issues comparing vanilla Claude Code vs PopKit
---

# /popkit:benchmark - GitHub Issue Benchmarking

## Overview

Compare vanilla Claude Code vs PopKit on real GitHub issues to validate PopKit's value proposition.

## Usage

\`\`\`bash
# Basic usage
/popkit:benchmark issue #237

# With specific modes
/popkit:benchmark issue #237 --modes quick,full

# With prompt quality variations
/popkit:benchmark issue #237 --prompts vibe,junior,senior
\`\`\`

## How It Works

1. **Create Isolated Worktrees**
   - Vanilla: `/tmp/bench-vanilla-237-{timestamp}`
   - PopKit: `/tmp/bench-popkit-237-{timestamp}`
   - Each gets separate branch

2. **Run Benchmarks in Parallel**
   - Both execute simultaneously
   - No cross-contamination
   - Real-time progress tracking

3. **Quality Assessment**
   - Tests pass (40%)
   - Acceptance criteria (30%)
   - Code quality (20%)
   - Efficiency (10%)

4. **Generate HTML Report**
   - Standalone (no dependencies)
   - Side-by-side comparison
   - Exportable (PDF, JSON)

5. **Cleanup**
   - Remove worktrees
   - Keep branches for reference

## Output

\`\`\`
🔬 Running Benchmark: Issue #237
================================================================================

Setup:
  • Creating isolated worktrees...
  • Branch: benchmark/vanilla-237-1734288000
  • Branch: benchmark/popkit-237-1734288000

Running Tests:
  Vanilla:  ████████░░░░░░░░ 58% | 7.2k tokens | $0.18 | 73s
  PopKit:   ██████████░░░░░░ 67% | 5.8k tokens | $0.14 | 67s

Final Results:
  ✓ Vanilla complete (127s, $0.31, 12.4k tokens)
  ✓ PopKit complete (98s, $0.24, 9.8k tokens)

Quality Assessment:
  📊 Vanilla: 8/10 (tests pass, some quality issues)
  📊 PopKit: 9/10 (tests pass, high quality)

🏆 Winner: PopKit (4/5 metrics)

View HTML report:
  packages/benchmarks/results/issue-237-{timestamp}/report.html

Cleanup worktrees? [Y/n]
\`\`\`

## Implementation

This command:
1. Loads GitHub issue metadata
2. Creates task configuration
3. Spawns benchmark runner
4. Tracks progress in real-time
5. Generates HTML report
6. Offers cleanup

## Related Commands

- `/popkit:stats benchmark` - View benchmark history
- `/popkit:issue view #N` - View issue details

## See Also

- Design: `docs/plans/2025-12-15-github-issue-benchmark-design.md`
- Issue: #250
\`\`\`
```

### Step 2: Add command trigger to plugin.json

```json
// packages/plugin/.claude-plugin/plugin.json

{
  "name": "popkit",
  "version": "0.2.4",
  "description": "AI-powered development workflow system",
  "commands": [
    {
      "name": "benchmark",
      "description": "Benchmark GitHub issues comparing vanilla vs PopKit",
      "triggers": ["benchmark", "bench"]
    }
  ]
}
```

### Step 3: Commit

```bash
git add packages/plugin/commands/benchmark.md packages/plugin/.claude-plugin/plugin.json
git commit -m "feat(plugin): add /popkit:benchmark command

Enables benchmarking of GitHub issues comparing vanilla vs PopKit.

Features:
- Git worktree isolation
- Parallel execution
- Real-time progress tracking
- HTML report generation
- Automatic cleanup

Usage:
  /popkit:benchmark issue #237
  /popkit:benchmark issue #237 --modes quick,full

Part of: #250 Phase 1 (v1.0)"
```

---

## Task 6: Create First GitHub Issue Benchmark Task

**Files:**
- Create: `packages/benchmarks/tasks/github-issues/issue-237.json`

### Step 1: Create task definition

```json
{
  "id": "github-issue-237",
  "name": "PopKit Workflow Benchmark Testing",
  "description": "Enable benchmarking of PopKit workflows by handling interactive AskUserQuestion prompts programmatically",
  "category": "github-issue",
  "language": "typescript",
  "version": "1.0.0",

  "githubIssue": {
    "repo": "jrc1883/popkit",
    "number": 237,
    "url": "https://github.com/jrc1883/popkit/issues/237"
  },

  "executionModes": {
    "vanilla": {
      "prompt": "Implement #237 - PopKit Workflow Benchmark Testing\n\nCurrent state: packages/benchmarks/ only supports vanilla vs popkit-enabled mode\nProblem: Can't test actual workflows like /popkit:dev full because they use AskUserQuestion\nSolution needed: Environment variable POPKIT_BENCHMARK_MODE + response file system\n\nFiles to modify:\n- packages/benchmarks/src/types.ts (add workflowCommand field)\n- packages/plugin/hooks/utils/benchmark_responses.py (new utility)\n- packages/plugin/skills/pop-*/SKILL.md (add benchmark mode handling)\n\nAcceptance criteria in issue body. See design doc:\ndocs/plans/2025-12-15-popkit-workflow-benchmark-design.md"
    },
    "popkitQuick": {
      "command": "/popkit:dev \"Implement #237 - PopKit Workflow Benchmark Testing. Enable benchmarking of interactive workflows by adding POPKIT_BENCHMARK_MODE environment variable and response file system. See docs/plans/2025-12-15-popkit-workflow-benchmark-design.md\"",
      "responses": {
        "What's next?": "Create implementation plan",
        "Commit changes?": true,
        "Continue?": "Yes"
      }
    }
  },

  "initialFiles": {},
  "dependencies": [],
  "setupCommands": [],

  "prompt": "",
  "context": "This is a TypeScript/Python task. Requires understanding of benchmark system and PopKit skills.",
  "maxTokens": 50000,
  "timeoutSeconds": 600,

  "tests": [
    {
      "id": "type-check",
      "name": "TypeScript compiles",
      "type": "unit",
      "command": "cd packages/benchmarks && npx tsc --noEmit",
      "successPattern": "",
      "expectedExitCode": 0
    },
    {
      "id": "benchmark-mode-var",
      "name": "POPKIT_BENCHMARK_MODE support added",
      "type": "unit",
      "command": "grep -r 'POPKIT_BENCHMARK_MODE' packages/plugin/hooks/utils/ || echo 'FAIL'",
      "successPattern": "benchmark_responses"
    }
  ],

  "qualityChecks": [
    {
      "id": "no-syntax-errors",
      "name": "No syntax errors",
      "type": "custom",
      "command": "cd packages/benchmarks && npm run lint 2>&1 || echo 'Has errors'",
      "weight": 1.0
    }
  ],

  "successCriteria": [
    "Task schema supports workflowCommand and benchmarkResponses",
    "Benchmark runner sets POPKIT_BENCHMARK_MODE environment variable",
    "benchmark_responses.py utility created",
    "Can run workflows in benchmark mode without human interaction"
  ],

  "baseline": {
    "vanilla": {
      "tokenEstimate": 20000,
      "toolCallEstimate": 30,
      "successRate": 0.65,
      "timeEstimate": 240,
      "qualityEstimate": 7.0
    },
    "popkit": {
      "tokenEstimate": 12000,
      "toolCallEstimate": 18,
      "successRate": 0.85,
      "timeEstimate": 150,
      "qualityEstimate": 8.5
    }
  },

  "tags": ["github-issue", "benchmark", "typescript", "python"],
  "author": "PopKit Team",
  "createdAt": "2025-12-15T00:00:00Z"
}
```

### Step 2: Commit

```bash
git add packages/benchmarks/tasks/github-issues/issue-237.json
git commit -m "feat(benchmarks): add first GitHub issue benchmark task

Issue #237: PopKit Workflow Benchmark Testing

Test case features:
- Real PopKit issue as benchmark
- Vanilla vs PopKit Quick Mode comparison
- Automated response handling
- Success criteria from issue

This validates:
- GitHub issue benchmark system works
- Task schema handles real issues
- Scoring engine assesses quality correctly

Part of: #250 Phase 1 (v1.0)"
```

---

## Task 7: Integration Testing & Documentation

**Files:**
- Create: `packages/benchmarks/README.md`
- Create: `packages/benchmarks/docs/running-benchmarks.md`
- Create: `packages/benchmarks/docs/creating-tasks.md`

### Step 1: Create main README

```markdown
# PopKit Benchmark Suite

Measure PopKit's value by comparing vanilla Claude Code vs PopKit on real development tasks.

## Quick Start

\`\`\`bash
# Run a GitHub issue benchmark
/popkit:benchmark issue #237

# Run synthetic benchmark
cd packages/benchmarks
npx tsx run-benchmark.ts bouncing-balls vanilla
npx tsx run-benchmark.ts bouncing-balls popkit

# Analyze results
npx tsx analyze-quality.ts results/bouncing-balls-popkit-{timestamp} \\
  --compare results/bouncing-balls-vanilla-{timestamp}
\`\`\`

## Benchmark Types

### Synthetic Benchmarks
- `bouncing-balls` - Animation with physics
- `bug-fix` - Debug broken code
- `todo-app` - Build CRUD app
- `api-client` - HTTP client implementation
- `binary-search-tree` - Data structure

### GitHub Issue Benchmarks (v1.0+)
- Real PopKit issues as test cases
- Validates PopKit on actual work
- Double value: benchmark + progress

## Results

### December 15, 2025 - Bouncing Balls (Prompt Parity Fixed)

| Metric | Vanilla | PopKit | Winner |
|--------|---------|--------|--------|
| Quality | 10/10 | 10/10 | Tie |
| Duration | 112s | 96s | PopKit |
| Cost | $0.24 | $0.24 | Tie |

**Key finding:** With prompt parity, PopKit achieves equal quality 14% faster.

## Documentation

- [Running Benchmarks](docs/running-benchmarks.md)
- [Creating Tasks](docs/creating-tasks.md)
- [Design Document](../../docs/plans/2025-12-15-github-issue-benchmark-design.md)

## Related Issues

- #250 - GitHub Issue Benchmark Tasks
- #237 - PopKit Workflow Benchmark Testing
- #220 - PopKit Benchmark Suite
- #236 - Benchmark System Development Context
\`\`\`
```

### Step 2: Commit documentation

```bash
git add packages/benchmarks/README.md packages/benchmarks/docs/
git commit -m "docs(benchmarks): add comprehensive documentation

Documentation includes:
- Quick start guide
- Benchmark types overview
- Latest results and findings
- Links to related docs and issues

Part of: #250 Phase 1 (v1.0)"
```

---

## Task 8: End-to-End Testing

**Files:**
- Test all components together
- Verify worktree isolation works
- Confirm HTML reports generate correctly

### Step 1: Run first benchmark manually

```bash
# Manually test the system
cd packages/benchmarks

# Create worktrees
node -e "
const { createBenchmarkWorktree } = require('./dist/worktree');
createBenchmarkWorktree(process.cwd(), 237, 'vanilla').then(console.log);
createBenchmarkWorktree(process.cwd(), 237, 'popkit').then(console.log);
"

# Verify worktrees exist
git worktree list

# Run a simple task in each
# (Manual verification)

# Generate HTML report
node -e "
const { generateHTMLReport } = require('./dist/reports/html-generator');
generateHTMLReport({
  issueNumber: 237,
  vanilla: { /* mock data */ },
  popkit: { /* mock data */ },
  outputDir: './results/test-report'
}).then(console.log);
"

# Open report in browser
# Verify it's standalone and looks correct

# Cleanup
git worktree remove /tmp/bench-vanilla-237-*
git worktree remove /tmp/bench-popkit-237-*
```

### Step 2: Document any issues found

Create issues for any bugs discovered during testing.

### Step 3: Commit integration test notes

```bash
git add packages/benchmarks/docs/testing-notes.md
git commit -m "docs(benchmarks): add integration testing notes

Verified:
- Worktree isolation works correctly
- HTML reports generate properly
- Cleanup functions as expected

Part of: #250 Phase 1 (v1.0)"
```

---

## Success Criteria Checklist

### Must Have (v1.0):
- [ ] `GitHubIssueBenchmark` type defined and tested
- [ ] Git worktree isolation working
- [ ] Automated scoring engine implemented
- [ ] HTML report generator creates standalone reports
- [ ] `/popkit:benchmark` command documented
- [ ] First GitHub issue task created (issue-237.json)
- [ ] Documentation complete
- [ ] Manual end-to-end test passes

### Validation Tests:
- [ ] Can run: `node -e "require('./dist/worktree').createBenchmarkWorktree(...).then(console.log)"`
- [ ] Can generate HTML report that opens in browser
- [ ] Worktrees isolate correctly (no cross-contamination)
- [ ] Cleanup removes worktrees but keeps branches
- [ ] HTML report is fully self-contained (no external deps)

---

## Next Steps After Phase 1

Once v1.0 is complete:

1. **Validate with real benchmarks**
   - Run 3-5 GitHub issue benchmarks
   - Document results
   - Identify improvements needed

2. **Prepare for Phase 2 (v1.1)**
   - Implement #237 (interactive workflow support)
   - Add benchmark response system
   - Test prompt quality variations

3. **Plan Phase 3 (v1.2)**
   - Cloud integration design
   - Upstash Redis setup
   - Share link generation

---

## Implementation Notes

### TDD Approach
Every task follows:
1. Write failing test
2. Run test (verify it fails)
3. Write minimal implementation
4. Run test (verify it passes)
5. Commit

### Commit Messages
Use conventional commits:
- `feat(benchmarks):` - New features
- `fix(benchmarks):` - Bug fixes
- `docs(benchmarks):` - Documentation
- `test(benchmarks):` - Tests only

### File Organization
```
packages/benchmarks/
├── src/
│   ├── types.ts             (Task 1)
│   ├── worktree.ts          (Task 2)
│   ├── scoring.ts           (Task 3)
│   ├── reports/
│   │   ├── html-generator.ts     (Task 4)
│   │   └── templates/report.html (Task 4)
│   └── __tests__/
│       ├── types.test.ts
│       ├── worktree.test.ts
│       ├── scoring.test.ts
│       └── html-generator.test.ts
├── tasks/
│   └── github-issues/
│       └── issue-237.json   (Task 6)
├── docs/
│   ├── running-benchmarks.md    (Task 7)
│   └── creating-tasks.md        (Task 7)
└── README.md                (Task 7)
```

---

**Status:** Ready for implementation
**Estimated Time:** 2-3 weeks
**Related Issue:** #250
**Design:** `docs/plans/2025-12-15-github-issue-benchmark-design.md`
