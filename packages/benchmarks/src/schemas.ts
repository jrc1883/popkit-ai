/**
 * PopKit Benchmark Framework - Zod Validation Schemas
 *
 * Runtime validation for benchmark tasks and results.
 */

import { z } from 'zod';

// =============================================================================
// Enums and Primitives
// =============================================================================

export const BenchmarkCategorySchema = z.enum(['standard', 'real-world', 'novel']);

export const BenchmarkToolSchema = z.enum(['claude', 'cursor', 'codex', 'gemini']);

export const BenchmarkModeSchema = z.enum(['vanilla', 'popkit', 'power']);

export const ProgrammingLanguageSchema = z.enum([
  'typescript',
  'javascript',
  'python',
  'rust',
  'go',
  'java',
]);

// =============================================================================
// Test Case and Quality Check Schemas
// =============================================================================

export const TestCaseSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  type: z.enum(['unit', 'integration', 'e2e', 'snapshot']),
  command: z.string().min(1),
  expectedExitCode: z.number().int().optional(),
  successPattern: z.string().optional(),
  failurePattern: z.string().optional(),
  timeoutSeconds: z.number().positive().optional(),
});

export const QualityCheckSchema = z.object({
  id: z.string().min(1),
  name: z.string().min(1),
  type: z.enum(['lint', 'typecheck', 'security', 'complexity', 'coverage', 'custom']),
  command: z.string().min(1),
  threshold: z.number().optional(),
  weight: z.number().min(0).max(1).optional(),
});

export const BaselineMetricsSchema = z.object({
  tokenEstimate: z.number().int().positive(),
  toolCallEstimate: z.number().int().nonnegative(),
  successRate: z.number().min(0).max(1),
  timeEstimate: z.number().positive().optional(),
  qualityEstimate: z.number().min(0).max(10).optional(),
});

// =============================================================================
// Benchmark Task Schema
// =============================================================================

export const BenchmarkTaskSchema = z.object({
  id: z
    .string()
    .min(1)
    .regex(/^[a-z0-9-]+$/, 'ID must be lowercase alphanumeric with hyphens'),
  name: z.string().min(1).max(100),
  description: z.string().min(10).max(500),
  category: BenchmarkCategorySchema,
  language: ProgrammingLanguageSchema,
  version: z.string().regex(/^\d+\.\d+\.\d+$/, 'Version must be semver format'),

  // Setup
  initialFiles: z.record(z.string(), z.string()),
  dependencies: z.array(z.string()),
  setupCommands: z.array(z.string()).optional(),

  // Execution
  prompt: z.string().min(10),
  context: z.string().optional(),
  maxTokens: z.number().int().positive().optional(),
  timeoutSeconds: z.number().int().positive().min(10).max(3600),

  // Validation
  tests: z.array(TestCaseSchema).min(1),
  qualityChecks: z.array(QualityCheckSchema),

  // Baseline
  baseline: z
    .object({
      vanilla: BaselineMetricsSchema.optional(),
      popkit: BaselineMetricsSchema.optional(),
      power: BaselineMetricsSchema.optional(),
    })
    .optional(),

  // Metadata
  tags: z.array(z.string()).optional(),
  author: z.string().optional(),
  createdAt: z.string().datetime().optional(),
  updatedAt: z.string().datetime().optional(),
});

// =============================================================================
// Result Schemas
// =============================================================================

export const ConversationMessageSchema = z.object({
  role: z.enum(['user', 'assistant', 'system', 'tool']),
  content: z.string(),
  timestamp: z.string().datetime(),
  tokens: z.number().int().nonnegative().optional(),
  toolCall: z
    .object({
      name: z.string(),
      input: z.record(z.unknown()),
      output: z.string().optional(),
      duration: z.number().nonnegative().optional(),
    })
    .optional(),
});

export const TestResultSchema = z.object({
  testId: z.string(),
  name: z.string(),
  passed: z.boolean(),
  exitCode: z.number().int(),
  output: z.string(),
  error: z.string().optional(),
  durationMs: z.number().nonnegative(),
});

export const QualityCheckResultSchema = z.object({
  checkId: z.string(),
  name: z.string(),
  passed: z.boolean(),
  score: z.number().min(0).max(100),
  findings: z.array(z.string()),
  durationMs: z.number().nonnegative(),
});

export const BenchmarkResultSchema = z.object({
  runId: z.string().uuid(),
  taskId: z.string(),
  tool: BenchmarkToolSchema,
  mode: BenchmarkModeSchema,

  // Timing
  startedAt: z.string().datetime(),
  completedAt: z.string().datetime(),
  durationSeconds: z.number().nonnegative(),

  // Core metrics
  tokensUsed: z.number().int().nonnegative(),
  inputTokens: z.number().int().nonnegative(),
  outputTokens: z.number().int().nonnegative(),
  toolCalls: z.number().int().nonnegative(),
  success: z.boolean(),

  // Detailed metrics
  testsPassedRatio: z.number().min(0).max(1),
  codeQualityScore: z.number().min(0).max(10),
  securityIssues: z.number().int().nonnegative(),

  // Efficiency metrics
  contextPrecision: z.number().min(0).max(1),
  firstAttemptSuccess: z.boolean(),
  iterationsNeeded: z.number().int().positive(),

  // Raw data
  conversation: z.array(ConversationMessageSchema),
  outputFiles: z.record(z.string(), z.string()),
  testResults: z.array(TestResultSchema),
  qualityResults: z.array(QualityCheckResultSchema),
  logs: z.array(z.string()),

  // Error handling
  errored: z.boolean(),
  errorMessage: z.string().optional(),
  errorStack: z.string().optional(),
});

// =============================================================================
// Type Exports (inferred from schemas)
// =============================================================================

export type BenchmarkTaskInput = z.input<typeof BenchmarkTaskSchema>;
export type BenchmarkTaskOutput = z.output<typeof BenchmarkTaskSchema>;
export type BenchmarkResultInput = z.input<typeof BenchmarkResultSchema>;
export type BenchmarkResultOutput = z.output<typeof BenchmarkResultSchema>;

// =============================================================================
// Validation Functions
// =============================================================================

/**
 * Validate a benchmark task definition
 */
export function validateTask(task: unknown): BenchmarkTaskOutput {
  return BenchmarkTaskSchema.parse(task);
}

/**
 * Safely validate a task, returning result or error
 */
export function safeValidateTask(task: unknown): {
  success: boolean;
  data?: BenchmarkTaskOutput;
  error?: z.ZodError;
} {
  const result = BenchmarkTaskSchema.safeParse(task);
  if (result.success) {
    return { success: true, data: result.data };
  }
  return { success: false, error: result.error };
}

/**
 * Validate a benchmark result
 */
export function validateResult(result: unknown): BenchmarkResultOutput {
  return BenchmarkResultSchema.parse(result);
}

/**
 * Safely validate a result, returning result or error
 */
export function safeValidateResult(result: unknown): {
  success: boolean;
  data?: BenchmarkResultOutput;
  error?: z.ZodError;
} {
  const parsed = BenchmarkResultSchema.safeParse(result);
  if (parsed.success) {
    return { success: true, data: parsed.data };
  }
  return { success: false, error: parsed.error };
}
