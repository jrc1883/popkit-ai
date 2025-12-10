/**
 * PopKit Benchmark Framework - Tool Runner Interface
 *
 * Defines the contract for AI tool runners that execute benchmark tasks.
 */

import type {
  BenchmarkTask,
  BenchmarkMode,
  BenchmarkResult,
  ConversationMessage,
} from '../types.js';

/**
 * Supported AI tools for benchmarking
 */
export type SupportedTool = 'claude' | 'cursor' | 'codex' | 'gemini';

/**
 * Result from executing a benchmark task
 */
export interface ExecutionResult {
  /** Whether execution completed successfully */
  success: boolean;
  /** Output files generated */
  outputFiles: Record<string, string>;
  /** Conversation transcript */
  conversation: ConversationMessage[];
  /** Token usage */
  tokens: {
    input: number;
    output: number;
    total: number;
  };
  /** Number of tool calls made */
  toolCalls: number;
  /** Execution duration in seconds */
  durationSeconds: number;
  /** Test results */
  testResults: TestExecutionResult[];
  /** Quality check results */
  qualityResults: QualityExecutionResult[];
  /** Error if execution failed */
  error?: {
    message: string;
    stack?: string;
  };
  /** Raw logs */
  logs: string[];
}

/**
 * Result from running a test
 */
export interface TestExecutionResult {
  testId: string;
  name: string;
  passed: boolean;
  exitCode: number;
  output: string;
  error?: string;
  durationMs: number;
}

/**
 * Result from running a quality check
 */
export interface QualityExecutionResult {
  checkId: string;
  name: string;
  passed: boolean;
  score: number;
  findings: string[];
  durationMs: number;
}

/**
 * Configuration for a tool runner
 */
export interface RunnerConfig {
  /** Tool-specific API key (if needed) */
  apiKey?: string;
  /** Base URL for API (if customizable) */
  baseUrl?: string;
  /** Request timeout in milliseconds */
  timeoutMs?: number;
  /** Maximum retries on failure */
  maxRetries?: number;
  /** Working directory for execution */
  workDir?: string;
  /** Environment variables to set */
  envVars?: Record<string, string>;
  /** Whether to enable verbose logging */
  verbose?: boolean;
}

/**
 * Tool runner interface - implemented by each AI tool runner
 */
export interface ToolRunner {
  /** Runner name (e.g., "claude", "cursor") */
  readonly name: SupportedTool;

  /** Human-readable description */
  readonly description: string;

  /** Whether this runner is available (dependencies installed, API key set) */
  isAvailable(): Promise<boolean>;

  /**
   * Setup the runner (install dependencies, verify configuration)
   */
  setup(config?: RunnerConfig): Promise<void>;

  /**
   * Execute a benchmark task
   *
   * @param task - The benchmark task to execute
   * @param mode - Execution mode (vanilla, popkit, power)
   * @returns Execution result
   */
  execute(task: BenchmarkTask, mode: BenchmarkMode): Promise<ExecutionResult>;

  /**
   * Cleanup after execution (remove temp files, close connections)
   */
  cleanup(): Promise<void>;

  /**
   * Get runner capabilities
   */
  getCapabilities(): RunnerCapabilities;
}

/**
 * Capabilities supported by a runner
 */
export interface RunnerCapabilities {
  /** Supported modes */
  modes: BenchmarkMode[];
  /** Supported programming languages */
  languages: string[];
  /** Whether streaming output is supported */
  streaming: boolean;
  /** Whether concurrent execution is supported */
  concurrent: boolean;
  /** Maximum concurrent executions */
  maxConcurrent?: number;
  /** Whether the runner can be used in CI environments */
  ciCompatible: boolean;
}

/**
 * Factory for creating tool runners
 */
export interface RunnerFactory {
  /**
   * Create a runner for a specific tool
   */
  create(tool: SupportedTool, config?: RunnerConfig): ToolRunner;

  /**
   * List available runners
   */
  listAvailable(): Promise<SupportedTool[]>;

  /**
   * Check if a specific runner is available
   */
  isAvailable(tool: SupportedTool): Promise<boolean>;
}
