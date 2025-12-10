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
  email: string;
  passwordHash?: string;
  name?: string;
  githubId?: string;
  githubUsername?: string;
  tier: Tier;
  stripeCustomerId?: string;
  stripeSubscriptionId?: string;
  createdAt: string;
  updatedAt?: string;
}

export interface SessionData {
  userId: string;
  createdAt: string;
  expiresAt: string;
}

export interface SignupRequest {
  email: string;
  password: string;
  name?: string;
  plan?: 'free' | 'pro';
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface AuthResponse {
  user: Omit<UserData, 'passwordHash'>;
  sessionToken: string;
  apiKey?: string;
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
  // Stripe (Issue #130)
  STRIPE_SECRET_KEY?: string;
  STRIPE_WEBHOOK_SECRET?: string;
  STRIPE_PRICE_PRO?: string;
  STRIPE_PRICE_TEAM?: string;
  // Email - Resend (Issue #133)
  RESEND_API_KEY?: string;
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

// =============================================================================
// INTER-AGENT MESSAGING TYPES (Issue #109)
// =============================================================================

/**
 * Message types for inter-agent communication.
 * Maps to protocol.py MessageType enum.
 */
export type AgentMessageType =
  // Knowledge sharing
  | 'DISCOVERY'      // Agent found something useful
  | 'INSIGHT'        // Agent shares knowledge
  | 'RESULT'         // Agent completed work
  // Coordination
  | 'SYNC_REQUEST'   // Request sync barrier
  | 'SYNC_ACK'       // Acknowledge sync
  | 'PROGRESS'       // Progress update
  | 'HEARTBEAT'      // Agent alive signal
  // Alerts
  | 'DRIFT_ALERT'    // Agent off track
  | 'HUMAN_REQUIRED' // Needs human decision
  | 'BOUNDARY_ALERT' // Approaching limits
  // Patterns (persistent)
  | 'PATTERN'        // Learned pattern to share
  | 'CORRECTION'     // User correction to remember;

/**
 * Message priority levels.
 */
export type MessagePriority = 'low' | 'normal' | 'high';

/**
 * Message retention tiers.
 */
export type RetentionTier = 'ephemeral' | 'session' | 'persistent' | 'memory';

/**
 * Core message structure for inter-agent communication.
 */
export interface AgentMessage {
  /** Unique message ID for deduplication */
  id: string;
  /** Message type */
  type: AgentMessageType;
  /** Sender agent ID */
  fromAgent: string;
  /** Target agent IDs (empty = use routing) */
  toAgents?: string[];
  /** Power Mode session ID */
  sessionId: string;
  /** ISO 8601 timestamp */
  timestamp: string;
  /** Type-specific payload */
  payload: AgentMessagePayload;
  /** Tags for routing/filtering */
  tags: string[];
  /** Message priority */
  priority: MessagePriority;
  /** Retention tier (determines TTL) */
  retention?: RetentionTier;
}

/**
 * Type-specific message payloads.
 */
export type AgentMessagePayload =
  | DiscoveryPayload
  | InsightPayload
  | ResultPayload
  | SyncPayload
  | ProgressPayload
  | AlertPayload
  | PatternPayload;

export interface DiscoveryPayload {
  content: string;
  filePath?: string;
  confidence: number;
}

export interface InsightPayload {
  content: string;
  relevantTo: string[];
  category: string;
}

export interface ResultPayload {
  summary: string;
  files: string[];
  metrics?: Record<string, number>;
}

export interface SyncPayload {
  barrier: string;
  phase: string;
  action: 'wait' | 'proceed' | 'timeout';
}

export interface ProgressPayload {
  progress: number; // 0.0 to 1.0
  currentTask: string;
  filesModified?: string[];
}

export interface AlertPayload {
  alertType: 'drift' | 'human_required' | 'boundary';
  description: string;
  severity: 'info' | 'warning' | 'critical';
  context?: Record<string, unknown>;
}

export interface PatternPayload {
  pattern: string;
  context: string;
  examples: string[];
  confidence: number;
}

/**
 * Retention configuration in seconds.
 */
export const RETENTION_TTL: Record<RetentionTier, number> = {
  ephemeral: 3600,        // 1 hour (session-bound)
  session: 86400,         // 24 hours
  persistent: 2592000,    // 30 days
  memory: 39420000,       // ~15 months (Upstash max)
};

/**
 * Default retention by message type.
 */
export const MESSAGE_RETENTION: Record<AgentMessageType, RetentionTier> = {
  HEARTBEAT: 'ephemeral',
  PROGRESS: 'ephemeral',
  SYNC_REQUEST: 'ephemeral',
  SYNC_ACK: 'ephemeral',
  DISCOVERY: 'session',
  INSIGHT: 'session',
  RESULT: 'session',
  DRIFT_ALERT: 'session',
  HUMAN_REQUIRED: 'session',
  BOUNDARY_ALERT: 'session',
  PATTERN: 'persistent',
  CORRECTION: 'memory',
};

/**
 * Stored message in Redis inbox.
 */
export interface StoredMessage extends AgentMessage {
  /** When message was received by Cloud API */
  receivedAt: string;
  /** Whether message has been read */
  read: boolean;
  /** Expiration timestamp */
  expiresAt: string;
}
