/**
 * PopKit Benchmark Framework
 *
 * Measure and compare AI coding assistant performance across tools and modes.
 */

// Type exports
export type {
  BenchmarkCategory,
  BenchmarkTool,
  BenchmarkMode,
  ProgrammingLanguage,
  TestCase,
  QualityCheck,
  BaselineMetrics,
  BenchmarkTask,
  ConversationMessage,
  TestResult,
  QualityCheckResult,
  BenchmarkResult,
  ComparisonMetric,
  ComparisonReport,
  AggregateReport,
} from './types.js';

// Schema exports
export {
  BenchmarkCategorySchema,
  BenchmarkToolSchema,
  BenchmarkModeSchema,
  ProgrammingLanguageSchema,
  TestCaseSchema,
  QualityCheckSchema,
  BaselineMetricsSchema,
  BenchmarkTaskSchema,
  ConversationMessageSchema,
  TestResultSchema,
  QualityCheckResultSchema,
  BenchmarkResultSchema,
  validateTask,
  safeValidateTask,
  validateResult,
  safeValidateResult,
} from './schemas.js';

// Loader exports
export { loadTask, loadAllTasks, getTaskPath } from './loader.js';

// Storage exports
export type {
  StorageAdapter,
  ResultFilters,
  RunTracker,
  ToolCallRecord,
  TestResultRecord,
} from './storage/index.js';
export { SQLiteAdapter } from './storage/index.js';

// Collector exports
export { MetricsCollector } from './collector.js';
export type { MetricsCollectorOptions, CompleteRunOptions } from './collector.js';

// Runner exports
export type {
  SupportedTool,
  ExecutionResult,
  TestExecutionResult,
  QualityExecutionResult,
  RunnerConfig,
  ToolRunner,
  RunnerCapabilities,
} from './runners/index.js';
export { ClaudeRunner, BenchmarkExecutor, createExecutor } from './runners/index.js';
export type { ClaudeRunnerConfig, ExecutorConfig, BenchmarkRunResult } from './runners/index.js';

// E2B exports (optional)
export { isE2BAvailable, defaultE2BConfig } from './e2b/index.js';
export type { E2BConfig } from './e2b/index.js';

// Report exports
export {
  // Formatters
  type FormatOptions,
  progressBar,
  formatPercent,
  formatNumber,
  formatDuration,
  calculateImprovement,
  MODE_NAMES,
  getColor,
  RESET_COLOR,
  formatResultSummary,
  createTable,
  createComparisonBox,
  // Markdown reports
  generateResultMarkdown,
  generateComparisonMarkdown,
  generateAggregateMarkdown,
  // HTML reports
  generateResultHtml,
  generateComparisonHtml,
  generateAggregateHtml,
} from './reports/index.js';
