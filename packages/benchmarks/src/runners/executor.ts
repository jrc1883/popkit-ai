/**
 * PopKit Benchmark Framework - Unified Executor
 *
 * Orchestrates benchmark execution across multiple tools.
 */

import { v4 as uuidv4 } from 'uuid';
import type {
  ToolRunner,
  SupportedTool,
  RunnerConfig,
  ExecutionResult,
} from './interface.js';
import type {
  BenchmarkTask,
  BenchmarkMode,
  BenchmarkResult,
} from '../types.js';
import { MetricsCollector } from '../collector.js';
import { ClaudeRunner } from './claude-runner.js';

/**
 * Executor configuration
 */
export interface ExecutorConfig {
  /** Metrics collector for storing results */
  metricsCollector?: MetricsCollector;
  /** Runner configurations by tool */
  runnerConfigs?: Partial<Record<SupportedTool, RunnerConfig>>;
  /** Default timeout in milliseconds */
  defaultTimeoutMs?: number;
  /** Whether to run tests after execution */
  runTests?: boolean;
  /** Whether to run quality checks after execution */
  runQualityChecks?: boolean;
  /** Verbose logging */
  verbose?: boolean;
}

/**
 * Result from running a full benchmark
 */
export interface BenchmarkRunResult {
  /** Benchmark result (if saved to collector) */
  result?: BenchmarkResult;
  /** Raw execution result */
  execution: ExecutionResult;
  /** Run ID */
  runId: string;
  /** Task ID */
  taskId: string;
  /** Tool used */
  tool: SupportedTool;
  /** Mode used */
  mode: BenchmarkMode;
}

/**
 * Unified benchmark executor
 */
export class BenchmarkExecutor {
  private runners: Map<SupportedTool, ToolRunner> = new Map();
  private metricsCollector?: MetricsCollector;
  private config: ExecutorConfig;

  constructor(config: ExecutorConfig = {}) {
    this.config = {
      defaultTimeoutMs: 300000,
      runTests: true,
      runQualityChecks: true,
      verbose: false,
      ...config,
    };
    this.metricsCollector = config.metricsCollector;

    // Register default runners
    this.registerRunner(new ClaudeRunner());
  }

  /**
   * Register a tool runner
   */
  registerRunner(runner: ToolRunner): void {
    this.runners.set(runner.name, runner);
  }

  /**
   * Get a registered runner
   */
  getRunner(tool: SupportedTool): ToolRunner | undefined {
    return this.runners.get(tool);
  }

  /**
   * List available tools
   */
  async listAvailableTools(): Promise<SupportedTool[]> {
    const available: SupportedTool[] = [];
    for (const [tool, runner] of this.runners) {
      if (await runner.isAvailable()) {
        available.push(tool);
      }
    }
    return available;
  }

  /**
   * Run a benchmark with a specific tool and mode
   */
  async runBenchmark(
    task: BenchmarkTask,
    tool: SupportedTool,
    mode: BenchmarkMode
  ): Promise<BenchmarkRunResult> {
    const runner = this.runners.get(tool);
    if (!runner) {
      throw new Error(`Runner for tool '${tool}' not registered`);
    }

    if (!(await runner.isAvailable())) {
      throw new Error(`Runner for tool '${tool}' is not available`);
    }

    const runId = uuidv4();

    if (this.config.verbose) {
      console.log(`[Executor] Starting benchmark ${task.id} with ${tool} (${mode})`);
    }

    // Setup runner
    const runnerConfig = this.config.runnerConfigs?.[tool];
    await runner.setup(runnerConfig);

    try {
      // Start metrics collection
      let metricsRunId: string | undefined;
      if (this.metricsCollector) {
        metricsRunId = this.metricsCollector.startRun(task.id, tool, mode);
      }

      // Execute benchmark
      const execution = await runner.execute(task, mode);

      // Record metrics
      if (this.metricsCollector && metricsRunId) {
        this.metricsCollector.recordTokenUsage(
          metricsRunId,
          execution.tokens.input,
          'input'
        );
        this.metricsCollector.recordTokenUsage(
          metricsRunId,
          execution.tokens.output,
          'output'
        );

        for (const test of execution.testResults) {
          this.metricsCollector.recordTestResult(
            metricsRunId,
            test.testId,
            test.name,
            test.passed,
            test.durationMs,
            test.output,
            test.error
          );
        }

        // Complete and save
        const result = await this.metricsCollector.completeRun(metricsRunId, {
          success: execution.success,
          codeQualityScore: this.calculateQualityScore(execution.qualityResults),
          securityIssues: 0,
          contextPrecision: 0.8, // Placeholder
          firstAttemptSuccess: execution.success,
          iterationsNeeded: 1,
          conversation: execution.conversation,
          outputFiles: execution.outputFiles,
          qualityResults: execution.qualityResults,
          errored: !!execution.error,
          errorMessage: execution.error?.message,
          errorStack: execution.error?.stack,
        });

        return {
          result,
          execution,
          runId,
          taskId: task.id,
          tool,
          mode,
        };
      }

      return {
        execution,
        runId,
        taskId: task.id,
        tool,
        mode,
      };
    } finally {
      await runner.cleanup();
    }
  }

  /**
   * Run a benchmark across all modes for comparison
   */
  async runComparison(
    task: BenchmarkTask,
    tool: SupportedTool,
    modes: BenchmarkMode[] = ['vanilla', 'popkit', 'power']
  ): Promise<BenchmarkRunResult[]> {
    const results: BenchmarkRunResult[] = [];

    for (const mode of modes) {
      const result = await this.runBenchmark(task, tool, mode);
      results.push(result);
    }

    return results;
  }

  /**
   * Run a benchmark across all available tools
   */
  async runCrossToolComparison(
    task: BenchmarkTask,
    mode: BenchmarkMode = 'popkit'
  ): Promise<BenchmarkRunResult[]> {
    const availableTools = await this.listAvailableTools();
    const results: BenchmarkRunResult[] = [];

    for (const tool of availableTools) {
      try {
        const result = await this.runBenchmark(task, tool, mode);
        results.push(result);
      } catch (error) {
        if (this.config.verbose) {
          console.error(`[Executor] Failed with ${tool}:`, error);
        }
      }
    }

    return results;
  }

  /**
   * Run a full matrix comparison (all tools × all modes)
   */
  async runFullMatrix(
    task: BenchmarkTask,
    tools?: SupportedTool[],
    modes: BenchmarkMode[] = ['vanilla', 'popkit', 'power']
  ): Promise<Map<string, BenchmarkRunResult>> {
    const results = new Map<string, BenchmarkRunResult>();
    const availableTools = tools || (await this.listAvailableTools());

    for (const tool of availableTools) {
      for (const mode of modes) {
        const key = `${tool}:${mode}`;
        try {
          const result = await this.runBenchmark(task, tool, mode);
          results.set(key, result);
        } catch (error) {
          if (this.config.verbose) {
            console.error(`[Executor] Failed ${key}:`, error);
          }
        }
      }
    }

    return results;
  }

  /**
   * Calculate quality score from quality results
   */
  private calculateQualityScore(
    results: ExecutionResult['qualityResults']
  ): number {
    if (results.length === 0) return 0;

    const totalScore = results.reduce((sum, r) => sum + r.score, 0);
    const avgScore = totalScore / results.length;

    // Convert from 0-100 to 0-10
    return avgScore / 10;
  }
}

/**
 * Create a pre-configured executor with metrics collection
 */
export function createExecutor(
  metricsCollector?: MetricsCollector,
  config?: Omit<ExecutorConfig, 'metricsCollector'>
): BenchmarkExecutor {
  return new BenchmarkExecutor({
    ...config,
    metricsCollector,
  });
}
