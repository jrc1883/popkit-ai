/**
 * PopKit Self-Testing Framework - Behavior Schemas (Issue #258)
 *
 * TypeScript interfaces for behavioral validation of PopKit orchestration.
 * These schemas define the structure of behavioral data captured during
 * benchmark execution for validation against expected behavior.
 *
 * Design: docs/designs/self-testing-framework-design.md
 * Architecture: docs/designs/self-testing-architecture.md
 */

/**
 * Tool call record from agent execution
 */
export interface ToolCall {
  tool_name: string;
  tool_input: Record<string, unknown>;
  tool_output?: string;
  timestamp: string;
  agent_id?: string;
  agent_name?: string;
  error?: string;
}

/**
 * Routing decision made by agent orchestrator
 */
export interface RoutingDecision {
  trigger: {
    type: 'keyword' | 'file-pattern' | 'error-pattern' | 'intent-analysis' | 'manual';
    value: string;
    confidence: number;
  };
  candidates: AgentEvaluation[];
  selected: string[];
  confidence?: number;
  reasoning?: string;
  timestamp: string;
}

/**
 * Agent evaluation during routing
 */
export interface AgentEvaluation {
  agent: string;
  score: number;
  matched: string[];
  category?: string;
  reason?: string;
}

/**
 * Agent invocation record
 */
export interface AgentInvocation {
  agent_name: string;
  agent_id: string;
  prompt: string;
  invoked_by: 'hook' | 'user' | 'skill';
  background: boolean;
  effort?: 'low' | 'medium' | 'high';
  start_time: string;
  end_time?: string;
  status?: 'completed' | 'failed' | 'timeout' | 'cancelled';
  duration_ms?: number;
  exit_code?: number;
  error?: string;
  tool_calls?: number;
}

/**
 * Skill execution record
 */
export interface SkillExecution {
  skill_name: string;
  workflow_id?: string;
  invoked_by: 'agent' | 'command' | 'skill';
  activity_id?: string;
  start_time: string;
  end_time?: string;
  status: 'complete' | 'error' | 'cancelled';
  tool_calls: number;
  decisions_made: string[];
  error?: string;
  duration_ms?: number;
}

/**
 * Workflow phase transition
 */
export interface PhaseTransition {
  workflow_id: string;
  from_phase: string | null;
  to_phase: string;
  skill_name?: string;
  tool_calls_so_far: number;
  metadata?: Record<string, unknown>;
  timestamp: string;
}

/**
 * Workflow status tracking
 */
export interface WorkflowStatus {
  workflow_id: string;
  workflow_type: 'feature-dev' | 'issue-work' | 'plan-execute' | 'custom';
  current_phase: string;
  phases_completed: string[];
  total_phases: number;
  start_time: string;
  end_time?: string;
  status: 'active' | 'completed' | 'failed' | 'paused';
}

/**
 * Tool usage pattern detected
 */
export interface ToolPattern {
  pattern: string;
  sequence: string[];
  occurrences: number;
  first_seen: string;
  last_seen: string;
  success_rate?: number;
}

/**
 * Sequence analysis results
 */
export interface SequenceAnalysis {
  common_sequences: ToolPattern[];
  anti_patterns: ToolPattern[];
  efficiency_score: number;
  insights: string[];
}

/**
 * User decision made via AskUserQuestion
 */
export interface UserDecision {
  decision_id: string;
  question: string;
  selected_options: string[];
  skill_name?: string;
  workflow_id?: string;
  timestamp: string;
}

/**
 * Group of parallel agents
 */
export interface AgentGroup {
  group_id: string;
  agents: string[];
  coordination_type: 'mesh' | 'star' | 'chain' | 'independent';
  start_time: string;
  end_time?: string;
}

/**
 * Performance metrics
 */
export interface PerformanceMetrics {
  total_duration_ms: number;
  routing_time_ms: number;
  agent_execution_time_ms: number;
  skill_execution_time_ms: number;
  tool_call_count: number;
  agent_invocation_count: number;
  skill_invocation_count: number;
  parallel_efficiency?: number;
}

/**
 * Complete behavioral capture for a benchmark session
 */
export interface BehaviorCapture {
  metadata: {
    task_id: string;
    mode: 'vanilla' | 'popkit' | 'power';
    capture_version: string;
    timestamp: string;
    session_id: string;
    test_mode: boolean;
  };

  routing: {
    decisions: RoutingDecision[];
    agents_considered: AgentEvaluation[];
    agents_selected: string[];
    routing_strategy: 'keyword' | 'file-pattern' | 'error-pattern' | 'intent-analysis' | 'manual';
  };

  agents: {
    invocations: AgentInvocation[];
    total_invoked: number;
    agents_by_category: Record<string, number>;
    parallel_groups: AgentGroup[];
  };

  skills: {
    executions: SkillExecution[];
    total_executed: number;
    skills_by_type: Record<string, number>;
  };

  workflows: {
    active_workflows: WorkflowStatus[];
    phase_transitions: PhaseTransition[];
    total_workflows: number;
  };

  tools: {
    calls: ToolCall[];
    total_calls: number;
    calls_by_tool: Record<string, number>;
    patterns: ToolPattern[];
    sequence_analysis: SequenceAnalysis;
  };

  decisions: {
    user_decisions: UserDecision[];
    total_decisions: number;
  };

  performance: PerformanceMetrics;

  insights: string[];
  warnings: string[];
}
