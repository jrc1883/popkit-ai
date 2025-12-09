/**
 * PopKit Cloud API Types
 *
 * Part of Issue #69 (API Gateway & Authentication)
 */

export type Tier = 'free' | 'pro' | 'team';

export interface ApiKeyData {
  id: string;
  userId: string;
  tier: Tier;
  name: string;
  createdAt: string;
  lastUsedAt?: string;
}

export interface UserData {
  id: string;
  githubId?: string;
  githubUsername?: string;
  email?: string;
  tier: Tier;
  createdAt: string;
}

export interface UsageData {
  commandsToday: number;
  bytesSent: number;
  bytesReceived: number;
  lastReset: string;
}

export interface RateLimitResult {
  exceeded: boolean;
  remaining: number;
  reset: number;
}

export interface Env {
  UPSTASH_REDIS_REST_URL: string;
  UPSTASH_REDIS_REST_TOKEN: string;
  VOYAGE_API_KEY: string;
  ENVIRONMENT: string;
  // Upstash Vector (Issue #101)
  UPSTASH_VECTOR_REST_URL: string;
  UPSTASH_VECTOR_REST_TOKEN: string;
  // Upstash Workflow/QStash (Issue #103)
  QSTASH_TOKEN: string;
  QSTASH_CURRENT_SIGNING_KEY?: string;
  QSTASH_NEXT_SIGNING_KEY?: string;
  // Anthropic Claude API (optional - for future headless/background operations)
  ANTHROPIC_API_KEY?: string;
}

// =============================================================================
// WORKFLOW TYPES (Issue #103 Phase 2)
// =============================================================================

export interface ClaudeMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ClaudeResponse {
  content: Array<{ type: 'text'; text: string }>;
  model: string;
  usage: {
    input_tokens: number;
    output_tokens: number;
  };
}

export interface WorkflowPhaseResult {
  phase: string;
  status: 'complete' | 'needs_input' | 'failed' | 'skipped';
  output: string;
  agentUsed?: string;
  tokensUsed?: number;
  nextPhase?: string;
  error?: string;
}

export interface WorkflowStatus {
  runId: string;
  status: 'running' | 'complete' | 'failed' | 'waiting';
  currentPhase?: string;
  phases: WorkflowPhaseResult[];
  startedAt: string;
  completedAt?: string;
  error?: string;
}

export interface Variables {
  apiKey?: ApiKeyData;
  user?: UserData;
}
