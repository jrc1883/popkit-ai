/**
 * PopKit Benchmark Framework - Storage Interface
 *
 * Abstract storage layer for benchmark results.
 */

import type { BenchmarkResult, ComparisonReport, AggregateReport } from '../types.js';

/**
 * Storage adapter interface for benchmark results
 */
export interface StorageAdapter {
  /** Initialize storage (create tables, etc.) */
  initialize(): Promise<void>;

  /** Close storage connection */
  close(): Promise<void>;

  /** Save a benchmark run result */
  saveResult(result: BenchmarkResult): Promise<void>;

  /** Get a result by run ID */
  getResult(runId: string): Promise<BenchmarkResult | null>;

  /** Get all results for a task */
  getResultsByTask(taskId: string): Promise<BenchmarkResult[]>;

  /** Get results filtered by task, tool, and/or mode */
  queryResults(filters: ResultFilters): Promise<BenchmarkResult[]>;

  /** Delete a result */
  deleteResult(runId: string): Promise<boolean>;

  /** Delete all results for a task */
  deleteResultsByTask(taskId: string): Promise<number>;

  /** Get comparison report for a task */
  getComparison(taskId: string): Promise<ComparisonReport | null>;

  /** Get aggregate report across all tasks */
  getAggregateReport(): Promise<AggregateReport>;

  /** Get list of all task IDs with results */
  listTasks(): Promise<string[]>;

  /** Get count of results */
  getResultCount(filters?: ResultFilters): Promise<number>;
}

/**
 * Filters for querying results
 */
export interface ResultFilters {
  taskId?: string;
  tool?: string;
  mode?: string;
  success?: boolean;
  minDate?: Date;
  maxDate?: Date;
  limit?: number;
  offset?: number;
}

/**
 * Run tracking data for in-progress benchmarks
 */
export interface RunTracker {
  runId: string;
  taskId: string;
  tool: string;
  mode: string;
  startedAt: Date;
  tokensUsed: number;
  inputTokens: number;
  outputTokens: number;
  toolCalls: ToolCallRecord[];
  testResults: TestResultRecord[];
  logs: string[];
}

/**
 * Tool call record
 */
export interface ToolCallRecord {
  name: string;
  timestamp: Date;
  durationMs: number;
  input?: Record<string, unknown>;
  output?: string;
}

/**
 * Test result record
 */
export interface TestResultRecord {
  testId: string;
  name: string;
  passed: boolean;
  timestamp: Date;
  durationMs: number;
  output?: string;
  error?: string;
}
