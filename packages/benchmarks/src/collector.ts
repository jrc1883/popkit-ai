/**
 * PopKit Benchmark Framework - Metrics Collector
 *
 * Collects metrics during benchmark execution and stores results.
 */

import { v4 as uuidv4 } from 'uuid';
import type { StorageAdapter, RunTracker, ToolCallRecord, TestResultRecord } from './storage/interface.js';
import type {
  BenchmarkResult,
  BenchmarkTool,
  BenchmarkMode,
  ComparisonReport,
  AggregateReport,
  ConversationMessage,
  TestResult,
  QualityCheckResult,
} from './types.js';

/**
 * Options for the MetricsCollector
 */
export interface MetricsCollectorOptions {
  /** Storage adapter to use */
  storage: StorageAdapter;
  /** Auto-initialize storage on construction */
  autoInit?: boolean;
}

/**
 * MetricsCollector - tracks benchmark execution and stores results
 */
export class MetricsCollector {
  private storage: StorageAdapter;
  private activeRuns: Map<string, RunTracker> = new Map();
  private initialized = false;

  constructor(options: MetricsCollectorOptions) {
    this.storage = options.storage;
    if (options.autoInit) {
      this.initialize().catch(console.error);
    }
  }

  /**
   * Initialize the collector (must be called before use)
   */
  async initialize(): Promise<void> {
    if (!this.initialized) {
      await this.storage.initialize();
      this.initialized = true;
    }
  }

  /**
   * Close the collector and storage
   */
  async close(): Promise<void> {
    await this.storage.close();
    this.initialized = false;
  }

  // =========================================================================
  // Run Management
  // =========================================================================

  /**
   * Start tracking a new benchmark run
   */
  startRun(
    taskId: string,
    tool: BenchmarkTool,
    mode: BenchmarkMode
  ): string {
    const runId = uuidv4();
    const tracker: RunTracker = {
      runId,
      taskId,
      tool,
      mode,
      startedAt: new Date(),
      tokensUsed: 0,
      inputTokens: 0,
      outputTokens: 0,
      toolCalls: [],
      testResults: [],
      logs: [],
    };
    this.activeRuns.set(runId, tracker);
    return runId;
  }

  /**
   * Get an active run tracker
   */
  getActiveRun(runId: string): RunTracker | undefined {
    return this.activeRuns.get(runId);
  }

  /**
   * Check if a run is active
   */
  isRunActive(runId: string): boolean {
    return this.activeRuns.has(runId);
  }

  // =========================================================================
  // Metrics Recording
  // =========================================================================

  /**
   * Record token usage for a run
   */
  recordTokenUsage(
    runId: string,
    tokens: number,
    type: 'input' | 'output' = 'output'
  ): void {
    const tracker = this.activeRuns.get(runId);
    if (!tracker) {
      throw new Error(`Run ${runId} not found or already completed`);
    }

    tracker.tokensUsed += tokens;
    if (type === 'input') {
      tracker.inputTokens += tokens;
    } else {
      tracker.outputTokens += tokens;
    }
  }

  /**
   * Record a tool call
   */
  recordToolCall(
    runId: string,
    toolName: string,
    durationMs: number,
    input?: Record<string, unknown>,
    output?: string
  ): void {
    const tracker = this.activeRuns.get(runId);
    if (!tracker) {
      throw new Error(`Run ${runId} not found or already completed`);
    }

    tracker.toolCalls.push({
      name: toolName,
      timestamp: new Date(),
      durationMs,
      input,
      output,
    });
  }

  /**
   * Record a test result
   */
  recordTestResult(
    runId: string,
    testId: string,
    testName: string,
    passed: boolean,
    durationMs: number,
    output?: string,
    error?: string
  ): void {
    const tracker = this.activeRuns.get(runId);
    if (!tracker) {
      throw new Error(`Run ${runId} not found or already completed`);
    }

    tracker.testResults.push({
      testId,
      name: testName,
      passed,
      timestamp: new Date(),
      durationMs,
      output,
      error,
    });
  }

  /**
   * Add a log entry
   */
  addLog(runId: string, message: string): void {
    const tracker = this.activeRuns.get(runId);
    if (!tracker) {
      throw new Error(`Run ${runId} not found or already completed`);
    }

    const timestamp = new Date().toISOString();
    tracker.logs.push(`[${timestamp}] ${message}`);
  }

  // =========================================================================
  // Run Completion
  // =========================================================================

  /**
   * Complete a benchmark run and save results
   */
  async completeRun(
    runId: string,
    options: CompleteRunOptions
  ): Promise<BenchmarkResult> {
    const tracker = this.activeRuns.get(runId);
    if (!tracker) {
      throw new Error(`Run ${runId} not found or already completed`);
    }

    const completedAt = new Date();
    const durationSeconds = (completedAt.getTime() - tracker.startedAt.getTime()) / 1000;

    // Calculate metrics
    const testsPassed = tracker.testResults.filter((t) => t.passed).length;
    const testsTotal = tracker.testResults.length;
    const testsPassedRatio = testsTotal > 0 ? testsPassed / testsTotal : 0;

    // Build test results
    const testResults: TestResult[] = tracker.testResults.map((t) => ({
      testId: t.testId,
      name: t.name,
      passed: t.passed,
      exitCode: t.passed ? 0 : 1,
      output: t.output || '',
      error: t.error,
      durationMs: t.durationMs,
    }));

    // Build result object
    const result: BenchmarkResult = {
      runId,
      taskId: tracker.taskId,
      tool: tracker.tool as BenchmarkTool,
      mode: tracker.mode as BenchmarkMode,
      startedAt: tracker.startedAt.toISOString(),
      completedAt: completedAt.toISOString(),
      durationSeconds,
      tokensUsed: tracker.tokensUsed,
      inputTokens: tracker.inputTokens,
      outputTokens: tracker.outputTokens,
      toolCalls: tracker.toolCalls.length,
      success: options.success,
      testsPassedRatio,
      codeQualityScore: options.codeQualityScore ?? 0,
      securityIssues: options.securityIssues ?? 0,
      contextPrecision: options.contextPrecision ?? 0,
      firstAttemptSuccess: options.firstAttemptSuccess ?? options.success,
      iterationsNeeded: options.iterationsNeeded ?? 1,
      conversation: options.conversation ?? [],
      outputFiles: options.outputFiles ?? {},
      testResults,
      qualityResults: options.qualityResults ?? [],
      logs: tracker.logs,
      errored: options.errored ?? false,
      errorMessage: options.errorMessage,
      errorStack: options.errorStack,
    };

    // Save to storage
    await this.storage.saveResult(result);

    // Remove from active runs
    this.activeRuns.delete(runId);

    return result;
  }

  /**
   * Abort a run without saving
   */
  abortRun(runId: string): boolean {
    return this.activeRuns.delete(runId);
  }

  // =========================================================================
  // Reporting
  // =========================================================================

  /**
   * Get comparison report for a task
   */
  async getComparison(taskId: string): Promise<ComparisonReport | null> {
    return this.storage.getComparison(taskId);
  }

  /**
   * Get aggregate report across all tasks
   */
  async getAggregateReport(): Promise<AggregateReport> {
    return this.storage.getAggregateReport();
  }

  /**
   * Get results for a specific task
   */
  async getResultsByTask(taskId: string): Promise<BenchmarkResult[]> {
    return this.storage.getResultsByTask(taskId);
  }

  /**
   * Get a specific result
   */
  async getResult(runId: string): Promise<BenchmarkResult | null> {
    return this.storage.getResult(runId);
  }

  /**
   * List all tasks with results
   */
  async listTasks(): Promise<string[]> {
    return this.storage.listTasks();
  }

  /**
   * Get count of stored results
   */
  async getResultCount(): Promise<number> {
    return this.storage.getResultCount();
  }

  // =========================================================================
  // Utilities
  // =========================================================================

  /**
   * Format a comparison report as a string
   */
  formatComparison(report: ComparisonReport): string {
    const lines: string[] = [
      `\n┌─────────────────────────────────────────────────────────────┐`,
      `│         Benchmark Comparison: ${report.taskId.padEnd(28)}│`,
      `├─────────────────────────────────────────────────────────────┤`,
    ];

    const { summary } = report;
    lines.push(`│ Best Mode: ${summary.bestMode.padEnd(47)}│`);
    lines.push(`│ Token Savings: ${summary.tokenSavingsPercent.toFixed(1)}%`.padEnd(62) + '│');
    lines.push(`│ Success Rate Improvement: +${summary.successRateImprovement.toFixed(1)} pp`.padEnd(62) + '│');
    lines.push(`│ Quality Improvement: +${summary.qualityImprovement.toFixed(1)} pts`.padEnd(62) + '│');
    lines.push(`└─────────────────────────────────────────────────────────────┘`);

    return lines.join('\n');
  }

  /**
   * Format comparison as markdown table
   */
  formatComparisonMarkdown(report: ComparisonReport): string {
    const lines: string[] = [
      `## Benchmark: ${report.taskId}\n`,
      `| Mode | Tokens | Tool Calls | Success | Quality |`,
      `|------|--------|------------|---------|---------|`,
    ];

    // Would need to pull actual data from modeComparisons
    // This is simplified for now
    lines.push(`| **Best: ${report.summary.bestMode}** | - | - | - | - |`);
    lines.push('');
    lines.push(`**Token Savings:** ${report.summary.tokenSavingsPercent.toFixed(1)}%`);
    lines.push(`**Success Rate Improvement:** +${report.summary.successRateImprovement.toFixed(1)} pp`);
    lines.push(`**Quality Improvement:** +${report.summary.qualityImprovement.toFixed(1)} pts`);

    return lines.join('\n');
  }
}

/**
 * Options for completing a run
 */
export interface CompleteRunOptions {
  /** Overall success (all tests passed) */
  success: boolean;
  /** Code quality score (0-10) */
  codeQualityScore?: number;
  /** Number of security issues found */
  securityIssues?: number;
  /** Context precision (0-1) */
  contextPrecision?: number;
  /** Whether task was completed on first attempt */
  firstAttemptSuccess?: boolean;
  /** Number of iterations/retries needed */
  iterationsNeeded?: number;
  /** Full conversation transcript */
  conversation?: ConversationMessage[];
  /** Final output files */
  outputFiles?: Record<string, string>;
  /** Quality check results */
  qualityResults?: QualityCheckResult[];
  /** Whether the run errored out */
  errored?: boolean;
  /** Error message if errored */
  errorMessage?: string;
  /** Error stack trace */
  errorStack?: string;
}
