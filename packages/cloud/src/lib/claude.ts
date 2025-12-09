/**
 * Claude API Client
 *
 * Part of Issue #103 Phase 2 (Claude API Integration)
 *
 * Provides utilities for invoking Claude API within Upstash Workflows.
 * Supports agent-specific system prompts and semantic agent selection.
 */

import type { ClaudeMessage, ClaudeResponse, Env } from '../types';

// =============================================================================
// TYPES
// =============================================================================

interface ClaudeOptions {
  model?: string;
  maxTokens?: number;
  temperature?: number;
  systemPrompt?: string;
}

interface AgentInvocationResult {
  response: string;
  model: string;
  tokensUsed: number;
  agentUsed: string;
}

// =============================================================================
// CLAUDE API CLIENT
// =============================================================================

/**
 * Call Claude API directly.
 *
 * Uses fetch for Cloudflare Workers compatibility.
 */
export async function callClaude(
  apiKey: string,
  messages: ClaudeMessage[],
  options: ClaudeOptions = {}
): Promise<ClaudeResponse> {
  const {
    model = 'claude-sonnet-4-20250514',
    maxTokens = 4096,
    temperature = 0.7,
    systemPrompt,
  } = options;

  const requestBody: Record<string, unknown> = {
    model,
    max_tokens: maxTokens,
    temperature,
    messages,
  };

  if (systemPrompt) {
    requestBody.system = systemPrompt;
  }

  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify(requestBody),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Claude API error: ${response.status} - ${error}`);
  }

  return response.json();
}

// =============================================================================
// AGENT-SPECIFIC PROMPTS
// =============================================================================

/**
 * Agent system prompts for different phases/tasks.
 */
const AGENT_PROMPTS: Record<string, string> = {
  'code-explorer': `You are a code exploration specialist. Analyze codebases to understand:
- Architecture patterns and structure
- Key files and their responsibilities
- Dependencies and relationships
- Potential areas of concern

Provide thorough analysis with specific file references.`,

  'code-architect': `You are a software architect. Design solutions that:
- Follow established patterns in the codebase
- Consider scalability and maintainability
- Minimize breaking changes
- Provide clear implementation steps

Output actionable architecture decisions with rationale.`,

  'code-reviewer': `You are a senior code reviewer. Focus on:
- Security vulnerabilities (OWASP Top 10)
- Performance issues
- Code quality and maintainability
- Adherence to project conventions

Use confidence scoring (0-100) and only report issues with 80+ confidence.`,

  'test-writer-fixer': `You are a testing specialist. Handle:
- Unit test creation and fixes
- Integration test design
- Test coverage analysis
- Debugging test failures

Write tests that are reliable, fast, and maintainable.`,

  'bug-whisperer': `You are a debugging expert. Approach bugs by:
- Reproducing the issue systematically
- Tracing root causes through the codebase
- Identifying related issues
- Proposing minimal fixes

Think like a detective following evidence.`,

  'default': `You are a helpful AI assistant for software development tasks.
Focus on providing accurate, actionable guidance.`,
};

/**
 * Get system prompt for an agent.
 */
export function getAgentPrompt(agentName: string): string {
  return AGENT_PROMPTS[agentName] || AGENT_PROMPTS['default'];
}

// =============================================================================
// SEMANTIC AGENT SELECTION
// =============================================================================

interface AgentMatch {
  agent: string;
  score: number;
  tier?: string;
  description?: string;
}

/**
 * Find best agent for a task using semantic search.
 */
export async function findBestAgent(
  env: Env,
  taskDescription: string,
  preferredTier?: string
): Promise<AgentMatch | null> {
  if (!env.UPSTASH_VECTOR_REST_URL || !env.UPSTASH_VECTOR_REST_TOKEN) {
    return null;
  }

  // Import dynamically to avoid issues
  const { Index } = await import('@upstash/vector');

  const index = new Index({
    url: env.UPSTASH_VECTOR_REST_URL,
    token: env.UPSTASH_VECTOR_REST_TOKEN,
  });

  let filter: string | undefined;
  if (preferredTier) {
    filter = `tier = '${preferredTier}'`;
  }

  try {
    const results = await index.query({
      data: taskDescription,
      topK: 1,
      includeMetadata: true,
      filter,
    });

    if (results.length === 0 || results[0].score < 0.3) {
      return null;
    }

    const best = results[0];
    return {
      agent: (best.metadata?.name as string) || String(best.id),
      score: best.score,
      tier: best.metadata?.tier as string | undefined,
      description: best.metadata?.description as string | undefined,
    };
  } catch (error) {
    console.error('Agent search failed:', error);
    return null;
  }
}

// =============================================================================
// HIGH-LEVEL AGENT INVOCATION
// =============================================================================

/**
 * Invoke an agent with a task.
 *
 * This is the main entry point for workflow phases.
 */
export async function invokeAgent(
  env: Env,
  agentName: string,
  task: string,
  context?: string
): Promise<AgentInvocationResult> {
  const systemPrompt = getAgentPrompt(agentName);

  const messages: ClaudeMessage[] = [];

  if (context) {
    messages.push({
      role: 'user',
      content: `Context from previous phases:\n${context}`,
    });
    messages.push({
      role: 'assistant',
      content: 'I understand the context. What would you like me to do?',
    });
  }

  messages.push({
    role: 'user',
    content: task,
  });

  const response = await callClaude(env.ANTHROPIC_API_KEY, messages, {
    systemPrompt,
    maxTokens: 4096,
  });

  const responseText = response.content
    .filter((block) => block.type === 'text')
    .map((block) => block.text)
    .join('\n');

  return {
    response: responseText,
    model: response.model,
    tokensUsed: response.usage.input_tokens + response.usage.output_tokens,
    agentUsed: agentName,
  };
}

/**
 * Invoke the best agent for a task using semantic search.
 */
export async function invokeAgentSemantic(
  env: Env,
  taskDescription: string,
  task: string,
  context?: string,
  preferredTier?: string
): Promise<AgentInvocationResult> {
  const match = await findBestAgent(env, taskDescription, preferredTier);

  const agentName = match?.agent || 'default';

  const result = await invokeAgent(env, agentName, task, context);

  return {
    ...result,
    agentUsed: agentName,
  };
}

// =============================================================================
// PHASE-SPECIFIC HELPERS
// =============================================================================

/**
 * Run discovery phase - understand the feature request.
 */
export async function runDiscoveryPhase(
  env: Env,
  feature: string,
  projectContext?: string
): Promise<AgentInvocationResult> {
  const task = `Analyze this feature request and identify:
1. Core requirements
2. Potential scope
3. Key questions to clarify
4. Initial complexity assessment

Feature: "${feature}"

${projectContext ? `Project context:\n${projectContext}` : ''}`;

  return invokeAgentSemantic(env, 'understand requirements and scope', task);
}

/**
 * Run exploration phase - analyze codebase.
 */
export async function runExplorationPhase(
  env: Env,
  feature: string,
  discoveryContext: string,
  codebaseInfo?: string
): Promise<AgentInvocationResult> {
  const task = `Based on the discovery phase, explore the codebase to understand:
1. Existing patterns that could be reused
2. Files that will need modification
3. Dependencies to consider
4. Potential risks

Feature: "${feature}"

Discovery findings:
${discoveryContext}

${codebaseInfo ? `Codebase info:\n${codebaseInfo}` : ''}`;

  return invokeAgent(env, 'code-explorer', task, discoveryContext);
}

/**
 * Run architecture phase - design the solution.
 */
export async function runArchitecturePhase(
  env: Env,
  feature: string,
  explorationContext: string
): Promise<AgentInvocationResult> {
  const task = `Design the architecture for this feature:
1. Component structure
2. Data flow
3. API design (if applicable)
4. Testing strategy

Feature: "${feature}"

Based on exploration:
${explorationContext}`;

  return invokeAgent(env, 'code-architect', task, explorationContext);
}

/**
 * Run review phase - code review.
 */
export async function runReviewPhase(
  env: Env,
  implementationSummary: string
): Promise<AgentInvocationResult> {
  const task = `Review this implementation for:
1. Security vulnerabilities
2. Performance issues
3. Code quality
4. Test coverage

Only report issues with 80+ confidence.

Implementation:
${implementationSummary}`;

  return invokeAgent(env, 'code-reviewer', task);
}
