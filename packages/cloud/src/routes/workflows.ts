/**
 * Workflow Routes
 *
 * Part of Issue #103 (Upstash Workflow for Power Mode v2)
 *
 * Durable workflow orchestration using Upstash Workflow.
 * Provides state tracking, coordination, and fault tolerance.
 *
 * DESIGN PHILOSOPHY:
 * These workflows are ORCHESTRATION ONLY - they track state and coordinate
 * multi-step processes, but the actual intelligent work happens in the local
 * Claude Code session. This avoids redundant Claude API calls (you're already
 * paying for Claude Code Max) and keeps the intelligence where it belongs.
 *
 * The workflows provide:
 * - Durable state persistence (survives crashes)
 * - Progress tracking (know which phase you're in)
 * - Coordination between phases
 * - Retry logic for reliability
 * - Async execution capability
 */

import { Hono } from 'hono';
import { serve } from '@upstash/workflow/hono';
import { Redis } from '@upstash/redis';
import type { Env, Variables, WorkflowPhaseResult, WorkflowStatus } from '../types';

const workflows = new Hono<{ Bindings: Env; Variables: Variables }>();

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

/**
 * Store workflow status in Redis for tracking.
 */
async function updateWorkflowStatus(
  redis: Redis,
  runId: string,
  status: Partial<WorkflowStatus>
): Promise<void> {
  const key = `workflow:status:${runId}`;
  const existing = await redis.get<WorkflowStatus>(key);
  const updated: WorkflowStatus = {
    runId,
    status: 'running',
    phases: [],
    startedAt: new Date().toISOString(),
    ...existing,
    ...status,
  };
  await redis.set(key, updated, { ex: 86400 }); // 24 hour TTL
}

// =============================================================================
// FEATURE DEVELOPMENT WORKFLOW
// =============================================================================

/**
 * 7-Phase Feature Development Workflow (Orchestration Only)
 *
 * This workflow TRACKS the phases of feature development but does NOT
 * perform the actual work. Your local Claude Code session does the work,
 * and this workflow:
 * - Tracks which phase you're in
 * - Stores results from each phase
 * - Provides durability (can resume if interrupted)
 * - Enables progress monitoring
 *
 * Phases:
 * 1. Discovery - Understand the request
 * 2. Exploration - Analyze codebase
 * 3. Questions - Clarify requirements
 * 4. Architecture - Design solution
 * 5. Implementation - Build the feature
 * 6. Review - Code review
 * 7. Summary - Document completion
 */
interface FeatureDevPayload {
  feature: string;
  projectPath: string;
  sessionId: string;
  userId: string;
  // Phase results provided by local Claude Code session
  phaseResults?: Record<string, string>;
}

workflows.post(
  '/feature-dev',
  serve<FeatureDevPayload>(
    async (context) => {
      const { feature, projectPath, sessionId, phaseResults = {} } = context.requestPayload;
      const phases: WorkflowPhaseResult[] = [];

      // Initialize Redis for status tracking
      const redis = new Redis({
        url: (context.env as unknown as Env).UPSTASH_REDIS_REST_URL,
        token: (context.env as unknown as Env).UPSTASH_REDIS_REST_TOKEN,
      });

      // Update initial status
      await updateWorkflowStatus(redis, context.workflowRunId, {
        status: 'running',
        currentPhase: 'discovery',
      });

      // Phase 1: Discovery
      const discovery = await context.run('phase-1-discovery', async () => {
        return {
          phase: 'discovery',
          status: 'complete' as const,
          output: phaseResults.discovery || `Ready for discovery: "${feature}"`,
          nextPhase: 'exploration',
        };
      });
      phases.push(discovery);
      await updateWorkflowStatus(redis, context.workflowRunId, { currentPhase: 'exploration', phases });

      // Phase 2: Exploration
      const exploration = await context.run('phase-2-exploration', async () => {
        return {
          phase: 'exploration',
          status: 'complete' as const,
          output: phaseResults.exploration || `Ready to explore: ${projectPath}`,
          nextPhase: 'questions',
        };
      });
      phases.push(exploration);
      await updateWorkflowStatus(redis, context.workflowRunId, { currentPhase: 'questions', phases });

      // Phase 3: Questions
      const questions = await context.run('phase-3-questions', async () => {
        return {
          phase: 'questions',
          status: phaseResults.questions ? 'complete' as const : 'needs_input' as const,
          output: phaseResults.questions || 'Awaiting clarification questions',
          nextPhase: 'architecture',
        };
      });
      phases.push(questions);
      await updateWorkflowStatus(redis, context.workflowRunId, { currentPhase: 'architecture', phases });

      // Phase 4: Architecture
      const architecture = await context.run('phase-4-architecture', async () => {
        return {
          phase: 'architecture',
          status: 'complete' as const,
          output: phaseResults.architecture || 'Ready for architecture design',
          nextPhase: 'implementation',
        };
      });
      phases.push(architecture);
      await updateWorkflowStatus(redis, context.workflowRunId, { currentPhase: 'implementation', phases });

      // Phase 5: Implementation
      const implementation = await context.run('phase-5-implementation', async () => {
        return {
          phase: 'implementation',
          status: 'complete' as const,
          output: phaseResults.implementation || 'Ready for implementation',
          nextPhase: 'review',
        };
      });
      phases.push(implementation);
      await updateWorkflowStatus(redis, context.workflowRunId, { currentPhase: 'review', phases });

      // Phase 6: Review
      const review = await context.run('phase-6-review', async () => {
        return {
          phase: 'review',
          status: 'complete' as const,
          output: phaseResults.review || 'Ready for code review',
          nextPhase: 'summary',
        };
      });
      phases.push(review);
      await updateWorkflowStatus(redis, context.workflowRunId, { currentPhase: 'summary', phases });

      // Phase 7: Summary
      const summary = await context.run('phase-7-summary', async () => {
        return {
          phase: 'summary',
          status: 'complete' as const,
          output: phaseResults.summary || `Feature "${feature}" workflow complete`,
        };
      });
      phases.push(summary);

      // Update final status
      await updateWorkflowStatus(redis, context.workflowRunId, {
        status: 'complete',
        currentPhase: undefined,
        phases,
        completedAt: new Date().toISOString(),
      });

      return {
        workflowId: context.workflowRunId,
        feature,
        sessionId,
        phases,
        status: 'complete',
        message: 'Workflow orchestration complete. Actual work performed by local Claude Code session.',
      };
    },
    {
      retries: 3,
    }
  )
);

// =============================================================================
// POWER MODE ORCHESTRATOR WORKFLOW
// =============================================================================

/**
 * Power Mode Orchestrator (Coordination Only)
 *
 * Coordinates multiple agents working on a complex task.
 * This workflow TRACKS agent coordination but does NOT invoke Claude API.
 * The actual agent work happens in local Claude Code sessions.
 *
 * What this provides:
 * - Agent registration and tracking
 * - Phase coordination (init → execute → aggregate → synthesize)
 * - Consensus tracking
 * - Durable state across sessions
 */
interface PowerModePayload {
  task: string;
  agents: string[];
  sessionId: string;
  userId: string;
  consensusThreshold?: number;
  // Agent results provided by local Claude Code sessions
  agentResults?: Array<{
    agent: string;
    output: string;
    confidence: number;
  }>;
}

interface AgentResult {
  agent: string;
  status: 'pending' | 'complete' | 'failed';
  output: string;
  confidence: number;
}

workflows.post(
  '/power-mode',
  serve<PowerModePayload>(
    async (context) => {
      const { task, agents, sessionId, consensusThreshold = 0.7, agentResults = [] } = context.requestPayload;

      // Initialize Redis for status tracking
      const redis = new Redis({
        url: (context.env as unknown as Env).UPSTASH_REDIS_REST_URL,
        token: (context.env as unknown as Env).UPSTASH_REDIS_REST_TOKEN,
      });

      // Step 1: Initialize coordinator
      const init = await context.run('init-coordinator', async () => {
        await updateWorkflowStatus(redis, context.workflowRunId, {
          status: 'running',
          currentPhase: 'initialization',
        });
        return {
          status: 'initialized',
          agents: agents,
          task: task,
          timestamp: new Date().toISOString(),
        };
      });

      // Step 2: Track agent assignments
      const assignments = await context.run('assign-agents', async () => {
        await updateWorkflowStatus(redis, context.workflowRunId, {
          currentPhase: 'agent-assignment',
        });

        // Create tracking entries for each agent
        const tracked: AgentResult[] = agents.map((agent) => {
          const result = agentResults.find((r) => r.agent === agent);
          return {
            agent,
            status: result ? 'complete' as const : 'pending' as const,
            output: result?.output || '',
            confidence: result?.confidence || 0,
          };
        });

        return tracked;
      });

      // Step 3: Aggregate results
      const aggregation = await context.run('aggregate-results', async () => {
        await updateWorkflowStatus(redis, context.workflowRunId, {
          currentPhase: 'aggregation',
        });

        const completedResults = assignments.filter((r) => r.status === 'complete');
        const avgConfidence = completedResults.length > 0
          ? completedResults.reduce((sum, r) => sum + r.confidence, 0) / completedResults.length
          : 0;

        return {
          consensus: avgConfidence >= consensusThreshold,
          avgConfidence,
          agentCount: agents.length,
          completedCount: completedResults.length,
          pendingCount: assignments.filter((r) => r.status === 'pending').length,
        };
      });

      // Step 4: Determine final status
      const synthesis = await context.run('synthesize', async () => {
        await updateWorkflowStatus(redis, context.workflowRunId, {
          currentPhase: 'synthesis',
        });

        const allComplete = aggregation.pendingCount === 0;

        return {
          task,
          status: !allComplete ? 'waiting_for_agents' :
                  aggregation.consensus ? 'consensus_reached' : 'needs_review',
          confidence: aggregation.avgConfidence,
          agentResults: assignments,
          message: !allComplete
            ? `Waiting for ${aggregation.pendingCount} agent(s) to complete`
            : aggregation.consensus
              ? 'Consensus reached among agents'
              : 'Results need human review - no consensus',
        };
      });

      // Update final status
      await updateWorkflowStatus(redis, context.workflowRunId, {
        status: synthesis.status === 'waiting_for_agents' ? 'waiting' : 'complete',
        currentPhase: undefined,
        completedAt: synthesis.status !== 'waiting_for_agents' ? new Date().toISOString() : undefined,
      });

      return {
        workflowId: context.workflowRunId,
        sessionId,
        ...synthesis,
      };
    },
    {
      retries: 2,
    }
  )
);

// =============================================================================
// UPDATE WORKFLOW PHASE
// =============================================================================

/**
 * POST /workflows/update/:runId
 *
 * Update a workflow with results from local Claude Code session.
 * This allows the local session to push results back to the workflow.
 */
workflows.post('/update/:runId', async (c) => {
  const runId = c.req.param('runId');
  const body = await c.req.json<{
    phase?: string;
    result?: string;
    agentResults?: Array<{ agent: string; output: string; confidence: number }>;
  }>();

  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const status = await redis.get<WorkflowStatus>(`workflow:status:${runId}`);

  if (!status) {
    return c.json({ error: 'Workflow not found' }, 404);
  }

  // Update the specific phase if provided
  if (body.phase && body.result) {
    const phaseIndex = status.phases.findIndex((p) => p.phase === body.phase);
    if (phaseIndex >= 0) {
      status.phases[phaseIndex].output = body.result;
      status.phases[phaseIndex].status = 'complete';
    }
  }

  await redis.set(`workflow:status:${runId}`, status, { ex: 86400 });

  return c.json({
    runId,
    updated: true,
    currentPhase: status.currentPhase,
    phases: status.phases.map((p) => ({ phase: p.phase, status: p.status })),
  });
});

// =============================================================================
// WORKFLOW STATUS
// =============================================================================

/**
 * GET /workflows/status/:runId
 *
 * Check status of a running workflow from Redis.
 */
workflows.get('/status/:runId', async (c) => {
  const runId = c.req.param('runId');

  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const status = await redis.get<WorkflowStatus>(`workflow:status:${runId}`);

  if (!status) {
    return c.json({
      runId,
      status: 'unknown',
      message: 'Workflow not found or status expired',
    }, 404);
  }

  return c.json(status);
});

/**
 * GET /workflows/list
 *
 * List recent workflow runs.
 */
workflows.get('/list', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  // Scan for workflow status keys
  const keys = await redis.keys('workflow:status:*');
  const workflowList: Array<{ runId: string; status: string; startedAt: string }> = [];

  for (const key of keys.slice(0, 20)) { // Limit to 20 most recent
    const status = await redis.get<WorkflowStatus>(key);
    if (status) {
      workflowList.push({
        runId: status.runId,
        status: status.status,
        startedAt: status.startedAt,
      });
    }
  }

  // Sort by start time
  workflowList.sort((a, b) => new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime());

  return c.json({
    count: workflowList.length,
    workflows: workflowList,
  });
});

// =============================================================================
// WORKFLOW INFO
// =============================================================================

/**
 * GET /workflows
 *
 * List available workflows and their purpose.
 */
workflows.get('/', async (c) => {
  return c.json({
    description: 'Orchestration-only workflows for PopKit. These track state and coordinate multi-step processes. The actual intelligent work happens in your local Claude Code session.',
    workflows: [
      {
        name: 'feature-dev',
        description: '7-phase feature development workflow (orchestration)',
        endpoint: '/v1/workflows/feature-dev',
        phases: [
          'discovery',
          'exploration',
          'questions',
          'architecture',
          'implementation',
          'review',
          'summary',
        ],
        note: 'Tracks phases - actual work done by local Claude Code',
      },
      {
        name: 'power-mode',
        description: 'Multi-agent coordination workflow (orchestration)',
        endpoint: '/v1/workflows/power-mode',
        pattern: 'orchestrator-workers',
        note: 'Coordinates agents - actual work done by local Claude Code sessions',
      },
    ],
    endpoints: {
      'POST /workflows/feature-dev': 'Start feature development workflow',
      'POST /workflows/power-mode': 'Start power mode coordination',
      'POST /workflows/update/:runId': 'Update workflow with results from local session',
      'GET /workflows/status/:runId': 'Check workflow status',
      'GET /workflows/list': 'List recent workflows',
    },
  });
});

export default workflows;
