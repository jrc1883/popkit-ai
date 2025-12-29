/**
 * PopKit Benchmark Framework - Runners Module
 *
 * Tool runners for executing benchmarks across AI coding assistants.
 */

// Interface exports
export type {
  SupportedTool,
  ExecutionResult,
  TestExecutionResult,
  QualityExecutionResult,
  RunnerConfig,
  ToolRunner,
  RunnerCapabilities,
  RunnerFactory,
} from './interface.js';

// Runner exports
export { ClaudeRunner } from './claude-runner.js';
export type { ClaudeRunnerConfig } from './claude-runner.js';

// Config switcher exports
export {
  ConfigSwitcher,
  createConfigSwitcher,
  isPopKitAvailable,
} from './config-switcher.js';
export type { ConfigSwitcherOptions, ConfigSnapshot } from './config-switcher.js';

// Executor exports
export { BenchmarkExecutor, createExecutor } from './executor.js';
export type { ExecutorConfig, BenchmarkRunResult } from './executor.js';
