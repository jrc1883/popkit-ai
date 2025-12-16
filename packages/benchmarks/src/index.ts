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
export {
  ClaudeRunner,
  BenchmarkExecutor,
  createExecutor,
  ConfigSwitcher,
  createConfigSwitcher,
  isPopKitAvailable,
} from './runners/index.js';
export type {
  ClaudeRunnerConfig,
  ExecutorConfig,
  BenchmarkRunResult,
  ConfigSwitcherOptions,
  ConfigSnapshot,
} from './runners/index.js';

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

// Behavior validation exports (Issue #258)
export type {
  BehaviorCapture,
  RoutingDecision,
  AgentInvocation,
  SkillExecution,
  PhaseTransition,
  WorkflowStatus,
  ToolPattern,
  SequenceAnalysis,
  UserDecision,
  AgentGroup,
  ToolCall,
  PerformanceMetrics,
} from './behavior/schema.js';
export { BehaviorCaptureService } from './behavior/capture.js';
export type {
  BehaviorExpectations,
  AgentExpectation,
  SkillExpectation,
  ToolExpectation,
  RoutingExpectation,
  WorkflowExpectation,
  PerformanceExpectation,
  DecisionExpectation,
  SequenceExpectation,
  BehaviorViolation,
  ValidationResult,
  ViolationSeverity,
} from './validator/expectations.js';
export { BehaviorValidator } from './validator/validator.js';
export { BehaviorReportGenerator, generateBehaviorReport } from './validator/report.js';
