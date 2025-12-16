/**
 * PopKit Self-Testing Framework - Expectation Schemas (Issue #258)
 *
 * TypeScript interfaces defining expected behavior for benchmark tasks.
 * These schemas are compared against actual BehaviorCapture data to
 * validate PopKit orchestration behavior and generate violation reports.
 *
 * Design: docs/designs/self-testing-framework-design.md
 * Architecture: docs/designs/self-testing-architecture.md
 */

/**
 * Severity levels for expectation violations
 */
export type ViolationSeverity = 'critical' | 'major' | 'minor';

/**
 * Agent invocation expectation
 */
export interface AgentExpectation {
  agents: string[];
  reason: string;
  required: boolean; // true = critical violation, false = major violation
  invocationCount?: {
    exact?: number;
    min?: number;
    max?: number;
  };
}

/**
 * Skill execution expectation
 */
export interface SkillExpectation {
  skills: string[];
  reason: string;
  required: boolean;
  executionCount?: {
    exact?: number;
    min?: number;
    max?: number;
  };
}

/**
 * Tool usage pattern expectation
 */
export interface ToolExpectation {
  pattern: string; // Tool name or pattern (e.g., "Read", "Glob:*.tsx")
  reason: string;
  severity: ViolationSeverity;
  minOccurrences?: number;
  maxOccurrences?: number;
}

/**
 * Routing behavior expectation
 */
export interface RoutingExpectation {
  expectedTriggers?: {
    type: 'keyword' | 'file-pattern' | 'error-pattern' | 'intent-analysis' | 'manual';
    value: string;
    minimumConfidence?: number;
  }[];
  forbiddenTriggers?: {
    type: 'keyword' | 'file-pattern' | 'error-pattern' | 'intent-analysis' | 'manual';
    value: string;
    reason: string;
  }[];
  agentSelection?: {
    shouldConsider: string[];
    shouldNotConsider: string[];
    minimumCandidates?: number;
  };
}

/**
 * Workflow behavior expectation
 */
export interface WorkflowExpectation {
  workflowType?: 'feature-dev' | 'issue-work' | 'plan-execute' | 'custom';
  phases?: {
    expectedPhases: string[];
    phaseOrder?: string[];
    forbiddenPhases?: string[];
  };
  transitions?: {
    maxTransitions?: number;
    forbiddenTransitions?: Array<{
      from: string;
      to: string;
      reason: string;
    }>;
  };
}

/**
 * Performance expectation
 */
export interface PerformanceExpectation {
  maxRoutingTimeMs?: number;
  maxAgentExecutionTimeMs?: number;
  maxSkillExecutionTimeMs?: number;
  maxTotalDurationMs?: number;
  maxToolCalls?: number;
  maxAgentInvocations?: number;
  minParallelEfficiency?: number; // 0-100 score
}

/**
 * Decision-making expectation
 */
export interface DecisionExpectation {
  minimumDecisions?: number;
  maximumDecisions?: number;
  expectedQuestions?: Array<{
    pattern: string; // Regex pattern for question text
    reason: string;
  }>;
  forbiddenQuestions?: Array<{
    pattern: string;
    reason: string;
  }>;
}

/**
 * Tool sequence expectation
 */
export interface SequenceExpectation {
  expectedSequences?: Array<{
    sequence: string[];
    reason: string;
    minimumOccurrences?: number;
  }>;
  antiPatterns?: Array<{
    sequence: string[];
    reason: string;
    severity: ViolationSeverity;
  }>;
}

/**
 * Complete behavior expectations for a benchmark task
 */
export interface BehaviorExpectations {
  taskId: string;
  description: string;
  mode: 'vanilla' | 'popkit' | 'power';

  agents?: {
    shouldInvoke?: AgentExpectation[];
    shouldNotInvoke?: AgentExpectation[];
    exclusiveInvocation?: {
      agents: string[];
      reason: string;
    };
  };

  skills?: {
    shouldInvoke?: SkillExpectation[];
    shouldNotInvoke?: SkillExpectation[];
  };

  tools?: {
    expectedPatterns?: ToolExpectation[];
    forbiddenPatterns?: ToolExpectation[];
    sequences?: SequenceExpectation;
  };

  routing?: RoutingExpectation;

  workflows?: WorkflowExpectation;

  performance?: PerformanceExpectation;

  decisions?: DecisionExpectation;

  metadata?: {
    version: string;
    author?: string;
    created?: string;
    updated?: string;
    tags?: string[];
  };
}

/**
 * Violation record when expectations are not met
 */
export interface BehaviorViolation {
  category: 'agent' | 'skill' | 'tool' | 'routing' | 'workflow' | 'performance' | 'decision';
  severity: ViolationSeverity;
  expected: string;
  actual: string;
  reason: string;
  timestamp?: string;
  metadata?: Record<string, unknown>;
}

/**
 * Validation result summary
 */
export interface ValidationResult {
  taskId: string;
  mode: 'vanilla' | 'popkit' | 'power';
  timestamp: string;

  score: number; // 0-100
  passed: boolean; // true if score >= threshold (default 80)

  violations: {
    critical: BehaviorViolation[];
    major: BehaviorViolation[];
    minor: BehaviorViolation[];
  };

  summary: {
    totalViolations: number;
    criticalCount: number;
    majorCount: number;
    minorCount: number;
    passedChecks: number;
    totalChecks: number;
  };

  insights: string[];
  recommendations: string[];
}
