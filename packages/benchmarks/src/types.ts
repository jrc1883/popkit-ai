/**
 * PopKit Benchmark Framework - Type Definitions
 *
 * Core interfaces for defining, executing, and measuring benchmark tasks.
 */

// =============================================================================
// Benchmark Task Definition
// =============================================================================

/**
 * Categories for benchmark tasks
 */
export type BenchmarkCategory = 'standard' | 'real-world' | 'novel';

/**
 * AI tools that can be benchmarked
 */
export type BenchmarkTool = 'claude' | 'cursor' | 'codex' | 'gemini';

/**
 * Modes for running benchmarks
 */
export type BenchmarkMode = 'vanilla' | 'popkit' | 'power';

/**
 * Supported programming languages for benchmark tasks
 */
export type ProgrammingLanguage =
  | 'typescript'
  | 'javascript'
  | 'python'
  | 'rust'
  | 'go'
  | 'java';

/**
 * Test case for validating benchmark output
 */
export interface TestCase {
  /** Unique identifier for the test */
  id: string;
  /** Human-readable name */
  name: string;
  /** Type of test */
  type: 'unit' | 'integration' | 'e2e' | 'snapshot';
  /** Command to run the test */
  command: string;
  /** Expected exit code (0 = success) */
  expectedExitCode?: number;
  /** Pattern to match in output for success */
  successPattern?: string;
  /** Pattern to match in output for failure */
  failurePattern?: string;
  /** Timeout in seconds */
  timeoutSeconds?: number;
}

/**
 * Quality check for assessing code output
 */
export interface QualityCheck {
  /** Unique identifier */
  id: string;
  /** Human-readable name */
  name: string;
  /** Type of quality check */
  type:
    | 'lint'           // ESLint, Prettier, etc.
    | 'typecheck'      // TypeScript compilation
    | 'security'       // Security audit
    | 'complexity'     // Cyclomatic complexity
    | 'coverage'       // Test coverage
    | 'custom';        // Custom validation
  /** Command to run the check */
  command: string;
  /** Threshold for passing (0-100 for scores, or specific values) */
  threshold?: number;
  /** Weight for overall quality score (0-1) */
  weight?: number;
}

/**
 * Expected baseline metrics for comparison
 */
export interface BaselineMetrics {
  /** Estimated token usage */
  tokenEstimate: number;
  /** Estimated tool calls */
  toolCallEstimate: number;
  /** Expected success rate (0-1) */
  successRate: number;
  /** Expected time in seconds */
  timeEstimate?: number;
  /** Expected quality score (0-10) */
  qualityEstimate?: number;
}

/**
 * Main benchmark task definition
 */
export interface BenchmarkTask {
  /** Unique identifier (e.g., "bouncing-balls", "todo-app") */
  id: string;
  /** Human-readable name */
  name: string;
  /** Short description of what the task tests */
  description: string;
  /** Task category */
  category: BenchmarkCategory;
  /** Primary programming language */
  language: ProgrammingLanguage;
  /** Version for tracking changes */
  version: string;

  // Setup
  /** Initial files to create in the workspace */
  initialFiles: Record<string, string>;
  /** npm/pip/cargo dependencies to install */
  dependencies: string[];
  /** Setup commands to run before execution */
  setupCommands?: string[];

  // Execution
  /** The prompt given to the AI tool */
  prompt: string;
  /** Additional context or constraints */
  context?: string;
  /** Maximum tokens allowed (for fair comparison) */
  maxTokens?: number;
  /** Timeout in seconds */
  timeoutSeconds: number;

  // Validation
  /** Test cases to validate output */
  tests: TestCase[];
  /** Quality checks to assess code */
  qualityChecks: QualityCheck[];

  // Expected outcomes
  /** Baseline metrics by mode for comparison */
  baseline?: {
    vanilla?: BaselineMetrics;
    popkit?: BaselineMetrics;
    power?: BaselineMetrics;
  };

  // Metadata
  /** Tags for filtering/categorization */
  tags?: string[];
  /** Author of the benchmark */
  author?: string;
  /** Creation date */
  createdAt?: string;
  /** Last modification date */
  updatedAt?: string;
}

// =============================================================================
// Benchmark Execution Results
// =============================================================================

/**
 * Message in the conversation during execution
 */
export interface ConversationMessage {
  /** Role of the message sender */
  role: 'user' | 'assistant' | 'system' | 'tool';
  /** Content of the message */
  content: string;
  /** Timestamp */
  timestamp: string;
  /** Token count for this message */
  tokens?: number;
  /** Tool call details if role is 'tool' */
  toolCall?: {
    name: string;
    input: Record<string, unknown>;
    output?: string;
    duration?: number;
  };
}

/**
 * Individual test result
 */
export interface TestResult {
  /** Test case ID */
  testId: string;
  /** Test name */
  name: string;
  /** Whether the test passed */
  passed: boolean;
  /** Actual exit code */
  exitCode: number;
  /** Output from the test */
  output: string;
  /** Error output if any */
  error?: string;
  /** Duration in milliseconds */
  durationMs: number;
}

/**
 * Individual quality check result
 */
export interface QualityCheckResult {
  /** Check ID */
  checkId: string;
  /** Check name */
  name: string;
  /** Whether the check passed */
  passed: boolean;
  /** Score from 0-100 */
  score: number;
  /** Detailed findings */
  findings: string[];
  /** Duration in milliseconds */
  durationMs: number;
}

/**
 * Complete result from a benchmark run
 */
export interface BenchmarkResult {
  /** Unique run identifier */
  runId: string;
  /** Task that was executed */
  taskId: string;
  /** Tool used */
  tool: BenchmarkTool;
  /** Mode of execution */
  mode: BenchmarkMode;

  // Timing
  /** When the run started */
  startedAt: string;
  /** When the run completed */
  completedAt: string;
  /** Total duration in seconds */
  durationSeconds: number;

  // Core metrics
  /** Total tokens used */
  tokensUsed: number;
  /** Input tokens */
  inputTokens: number;
  /** Output tokens */
  outputTokens: number;
  /** Number of tool calls made */
  toolCalls: number;
  /** Overall success (all tests passed) */
  success: boolean;

  // Detailed metrics
  /** Ratio of tests passed (0-1) */
  testsPassedRatio: number;
  /** Overall code quality score (0-10) */
  codeQualityScore: number;
  /** Number of security issues found */
  securityIssues: number;

  // Efficiency metrics
  /** Relevant vs. irrelevant context ratio (0-1) */
  contextPrecision: number;
  /** Whether task was completed on first attempt */
  firstAttemptSuccess: boolean;
  /** Number of iterations/retries needed */
  iterationsNeeded: number;

  // Raw data
  /** Full conversation transcript */
  conversation: ConversationMessage[];
  /** Final output files */
  outputFiles: Record<string, string>;
  /** Test results */
  testResults: TestResult[];
  /** Quality check results */
  qualityResults: QualityCheckResult[];
  /** Execution logs */
  logs: string[];

  // Error handling
  /** Whether the run errored out */
  errored: boolean;
  /** Error message if errored */
  errorMessage?: string;
  /** Error stack trace */
  errorStack?: string;
}

// =============================================================================
// Comparison and Reporting
// =============================================================================

/**
 * Comparison between different modes/tools
 */
export interface ComparisonMetric {
  /** Baseline value */
  baseline: number;
  /** Compared value */
  compared: number;
  /** Absolute difference */
  difference: number;
  /** Percentage change */
  percentChange: number;
  /** Whether improvement (lower is better for tokens, higher for success) */
  improved: boolean;
}

/**
 * Full comparison report for a task
 */
export interface ComparisonReport {
  /** Task being compared */
  taskId: string;
  /** Timestamp of report generation */
  generatedAt: string;
  /** Runs included in comparison */
  runIds: string[];

  /** Comparisons by mode */
  modeComparisons: {
    /** Vanilla vs. PopKit */
    vanillaVsPopkit?: {
      tokens: ComparisonMetric;
      toolCalls: ComparisonMetric;
      successRate: ComparisonMetric;
      quality: ComparisonMetric;
      time: ComparisonMetric;
    };
    /** Vanilla vs. Power Mode */
    vanillaVsPower?: {
      tokens: ComparisonMetric;
      toolCalls: ComparisonMetric;
      successRate: ComparisonMetric;
      quality: ComparisonMetric;
      time: ComparisonMetric;
    };
    /** PopKit vs. Power Mode */
    popkitVsPower?: {
      tokens: ComparisonMetric;
      toolCalls: ComparisonMetric;
      successRate: ComparisonMetric;
      quality: ComparisonMetric;
      time: ComparisonMetric;
    };
  };

  /** Summary statistics */
  summary: {
    /** Best performing mode */
    bestMode: BenchmarkMode;
    /** Token savings vs. vanilla */
    tokenSavingsPercent: number;
    /** Success rate improvement */
    successRateImprovement: number;
    /** Quality score improvement */
    qualityImprovement: number;
  };
}

/**
 * Aggregate report across multiple tasks
 */
export interface AggregateReport {
  /** Report title */
  title: string;
  /** Generation timestamp */
  generatedAt: string;
  /** Number of tasks included */
  taskCount: number;
  /** Number of runs included */
  runCount: number;

  /** Average improvements */
  averages: {
    /** Average token reduction */
    tokenReduction: number;
    /** Average success rate improvement */
    successRateImprovement: number;
    /** Average quality improvement */
    qualityImprovement: number;
    /** Average time savings */
    timeSavings: number;
  };

  /** Per-task breakdowns */
  tasks: {
    taskId: string;
    taskName: string;
    comparison: ComparisonReport;
  }[];

  /** Statistical confidence */
  confidence: {
    /** Sample size sufficient */
    sufficientSamples: boolean;
    /** Statistical significance p-value */
    pValue?: number;
    /** Confidence interval */
    confidenceInterval?: [number, number];
  };
}
