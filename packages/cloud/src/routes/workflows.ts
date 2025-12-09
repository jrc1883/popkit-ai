/**
 * Workflow Routes
 *
 * Part of Issue #103 (Upstash Workflow for Power Mode v2)
 * Phase 2: Claude API Integration
 *
 * Durable workflow execution using Upstash Workflow.
 * Provides orchestrated multi-agent coordination with fault tolerance.
 * Now with real Claude API calls for agent invocations.
 */

import { Hono } from 'hono';
import { serve } from '@upstash/workflow/hono';
import { Redis } from '@upstash/redis';
import type { Env, Variables, WorkflowPhaseResult, WorkflowStatus } from '../types';
import {
  invokeAgent,
  invokeAgentSemantic,
  runDiscoveryPhase,
  runExplorationPhase,
  runArchitecturePhase,
  runReviewPhase,
} from '../lib/claude';

const workflows = new Hono<{ Bindings: Env; Variables: Variables }>();

// =============================================================================
// FEATURE DEVELOPMENT WORKFLOW
// =============================================================================

/**
 * 7-Phase Feature Development Workflow
 *
 * Phases:
 * 1. Discovery - Understand the request
 * 2. Exploration - Analyze codebase
 * 3. Questions - Clarify requirements
 * 4. Architecture - Design solution
 * 5. Implementation - Build the feature
 * 6. Review - Code review
 * 7. Summary - Document completion
 *
 * Uses prompt chaining pattern - each phase output feeds the next.
 */
interface FeatureDevPayload {
  feature: string;
  projectPath: string;
  sessionId: string;
  userId: string;
  codebaseContext?: string;
  useClaude?: boolean; // Enable real Claude API calls
}

// Helper to store workflow status in Redis
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

workflows.post(
  '/feature-dev',
  serve<FeatureDevPayload>(
    async (context) => {
      const { feature, projectPath, sessionId, codebaseContext, useClaude = false } = context.requestPayload;
      const phases: WorkflowPhaseResult[] = [];
      let totalTokens = 0;

      // Initialize Redis for status tracking
      const redis = new Redis({
        url: context.env.UPSTASH_REDIS_REST_URL,
        token: context.env.UPSTASH_REDIS_REST_TOKEN,
      });

      // Update initial status
      await updateWorkflowStatus(redis, context.workflowRunId, {
        status: 'running',
        currentPhase: 'discovery',
      });

      // Cast env for type safety
      const env = context.env as unknown as Env;

      // Phase 1: Discovery
      const discovery = await context.run('phase-1-discovery', async () => {
        if (useClaude && env.ANTHROPIC_API_KEY) {
          const result = await runDiscoveryPhase(env, feature, codebaseContext);
          totalTokens += result.tokensUsed;
          return {
            phase: 'discovery',
            status: 'complete' as const,
            output: result.response,
            agentUsed: result.agentUsed,
            tokensUsed: result.tokensUsed,
            nextPhase: 'exploration',
          };
        }
        return {
          phase: 'discovery',
          status: 'complete' as const,
          output: `Analyzed feature request: "${feature}"`,
          nextPhase: 'exploration',
        };
      });
      phases.push(discovery);
      await updateWorkflowStatus(redis, context.workflowRunId, { currentPhase: 'exploration', phases });

      // Phase 2: Exploration
      const exploration = await context.run('phase-2-exploration', async () => {
        if (useClaude && env.ANTHROPIC_API_KEY) {
          const result = await runExplorationPhase(env, feature, discovery.output, codebaseContext);
          totalTokens += result.tokensUsed;
          return {
            phase: 'exploration',
            status: 'complete' as const,
            output: result.response,
            agentUsed: result.agentUsed,
            tokensUsed: result.tokensUsed,
            nextPhase: 'questions',
          };
        }
        return {
          phase: 'exploration',
          status: 'complete' as const,
          output: `Explored codebase at ${projectPath}`,
          nextPhase: 'questions',
        };
      });
      phases.push(exploration);
      await updateWorkflowStatus(redis, context.workflowRunId, { currentPhase: 'questions', phases });

      // Phase 3: Questions (may require human input)
      const questions = await context.run('phase-3-questions', async () => {
        if (useClaude && env.ANTHROPIC_API_KEY) {
          const result = await invokeAgentSemantic(
            env,
            'clarify requirements and ask questions',
            `Based on the discovery and exploration, identify any clarifying questions needed before proceeding with architecture:\n\nDiscovery: ${discovery.output}\n\nExploration: ${exploration.output}`,
            discovery.output
          );
          totalTokens += result.tokensUsed;
          return {
            phase: 'questions',
            status: 'complete' as const,
            output: result.response,
            agentUsed: result.agentUsed,
            tokensUsed: result.tokensUsed,
            nextPhase: 'architecture',
          };
        }
        return {
          phase: 'questions',
          status: 'complete' as const,
          output: 'Clarifications gathered',
          nextPhase: 'architecture',
        };
      });
      phases.push(questions);
      await updateWorkflowStatus(redis, context.workflowRunId, { currentPhase: 'architecture', phases });

      // Phase 4: Architecture
      const architecture = await context.run('phase-4-architecture', async () => {
        if (useClaude && env.ANTHROPIC_API_KEY) {
          const result = await runArchitecturePhase(env, feature, exploration.output);
          totalTokens += result.tokensUsed;
          return {
            phase: 'architecture',
            status: 'complete' as const,
            output: result.response,
            agentUsed: result.agentUsed,
            tokensUsed: result.tokensUsed,
            nextPhase: 'implementation',
          };
        }
        return {
          phase: 'architecture',
          status: 'complete' as const,
          output: 'Architecture designed based on exploration and questions',
          nextPhase: 'implementation',
        };
      });
      phases.push(architecture);
      await updateWorkflowStatus(redis, context.workflowRunId, { currentPhase: 'implementation', phases });

      // Phase 5: Implementation (simulation - actual implementation happens client-side)
      const implementation = await context.run('phase-5-implementation', async () => {
        if (useClaude && env.ANTHROPIC_API_KEY) {
          const result = await invokeAgent(
            env,
            'code-architect',
            `Create a detailed implementation plan based on this architecture:\n\n${architecture.output}\n\nProvide step-by-step instructions for implementing each component.`,
            architecture.output
          );
          totalTokens += result.tokensUsed;
          return {
            phase: 'implementation',
            status: 'complete' as const,
            output: result.response,
            agentUsed: result.agentUsed,
            tokensUsed: result.tokensUsed,
            nextPhase: 'review',
          };
        }
        return {
          phase: 'implementation',
          status: 'complete' as const,
          output: 'Feature implemented according to architecture',
          nextPhase: 'review',
        };
      });
      phases.push(implementation);
      await updateWorkflowStatus(redis, context.workflowRunId, { currentPhase: 'review', phases });

      // Phase 6: Review
      const review = await context.run('phase-6-review', async () => {
        if (useClaude && env.ANTHROPIC_API_KEY) {
          const result = await runReviewPhase(env, implementation.output);
          totalTokens += result.tokensUsed;
          return {
            phase: 'review',
            status: 'complete' as const,
            output: result.response,
            agentUsed: result.agentUsed,
            tokensUsed: result.tokensUsed,
            nextPhase: 'summary',
          };
        }
        return {
          phase: 'review',
          status: 'complete' as const,
          output: 'Code review completed with 80+ confidence threshold',
          nextPhase: 'summary',
        };
      });
      phases.push(review);
      await updateWorkflowStatus(redis, context.workflowRunId, { currentPhase: 'summary', phases });

      // Phase 7: Summary
      const summary = await context.run('phase-7-summary', async () => {
        if (useClaude && env.ANTHROPIC_API_KEY) {
          const result = await invokeAgent(
            env,
            'default',
            `Summarize the feature development process for "${feature}":\n\n1. Discovery: ${discovery.output.slice(0, 200)}...\n2. Exploration: ${exploration.output.slice(0, 200)}...\n3. Architecture: ${architecture.output.slice(0, 200)}...\n4. Implementation: ${implementation.output.slice(0, 200)}...\n5. Review: ${review.output.slice(0, 200)}...\n\nProvide a concise summary of what was accomplished and any follow-up actions.`
          );
          totalTokens += result.tokensUsed;
          return {
            phase: 'summary',
            status: 'complete' as const,
            output: result.response,
            agentUsed: result.agentUsed,
            tokensUsed: result.tokensUsed,
          };
        }
        return {
          phase: 'summary',
          status: 'complete' as const,
          output: `Feature "${feature}" completed successfully`,
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
        totalTokensUsed: totalTokens,
        claudeEnabled: useClaude,
      };
    },
    {
      // Workflow options
      retries: 3,
    }
  )
);

// =============================================================================
// POWER MODE ORCHESTRATOR WORKFLOW
// =============================================================================

/**
 * Power Mode Orchestrator
 *
 * Coordinates multiple agents working in parallel on a complex task.
 * Uses orchestrator-workers pattern with real Claude API calls.
 */
interface PowerModePayload {
  task: string;
  agents: string[];
  sessionId: string;
  userId: string;
  consensusThreshold?: number;
  useClaude?: boolean; // Enable real Claude API calls
}

interface AgentResult {
  agent: string;
  status: 'complete' | 'failed';
  output: string;
  confidence: number;
  tokensUsed?: number;
  error?: string;
}

workflows.post(
  '/power-mode',
  serve<PowerModePayload>(
    async (context) => {
      const { task, agents, sessionId, consensusThreshold = 0.7, useClaude = false } = context.requestPayload;
      let totalTokens = 0;

      // Cast env for type safety
      const env = context.env as unknown as Env;

      // Initialize Redis for status tracking
      const redis = new Redis({
        url: env.UPSTASH_REDIS_REST_URL,
        token: env.UPSTASH_REDIS_REST_TOKEN,
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
        };
      });

      // Step 2: Distribute task to agents
      const agentResults = await context.run('distribute-tasks', async () => {
        await updateWorkflowStatus(redis, context.workflowRunId, {
          currentPhase: 'agent-execution',
        });

        if (useClaude && env.ANTHROPIC_API_KEY) {
          // Real Claude API calls for each agent
          const results: AgentResult[] = [];
          for (const agent of agents) {
            try {
              const result = await invokeAgent(
                env,
                agent,
                `You are working as part of a multi-agent team. Your specific role is: ${agent}\n\nTask: ${task}\n\nProvide your analysis and contribution. End with a confidence score (0.0-1.0) for your response.`
              );
              totalTokens += result.tokensUsed;

              // Extract confidence from response (look for "confidence: X.X" pattern)
              const confidenceMatch = result.response.match(/confidence[:\s]+([0-9.]+)/i);
              const confidence = confidenceMatch ? parseFloat(confidenceMatch[1]) : 0.8;

              results.push({
                agent,
                status: 'complete',
                output: result.response,
                confidence: Math.min(Math.max(confidence, 0), 1),
                tokensUsed: result.tokensUsed,
              });
            } catch (error) {
              results.push({
                agent,
                status: 'failed',
                output: '',
                confidence: 0,
                error: error instanceof Error ? error.message : 'Unknown error',
              });
            }
          }
          return results;
        }

        // Simulation mode
        return agents.map((agent) => ({
          agent,
          status: 'complete' as const,
          output: `Agent ${agent} processed task`,
          confidence: Math.random() * 0.3 + 0.7,
        }));
      });

      // Step 3: Aggregate results
      const aggregation = await context.run('aggregate-results', async () => {
        await updateWorkflowStatus(redis, context.workflowRunId, {
          currentPhase: 'aggregation',
        });

        const completedResults = agentResults.filter((r) => r.status === 'complete');
        const avgConfidence = completedResults.length > 0
          ? completedResults.reduce((sum, r) => sum + r.confidence, 0) / completedResults.length
          : 0;

        return {
          consensus: avgConfidence >= consensusThreshold,
          avgConfidence,
          agentCount: agents.length,
          completedCount: completedResults.length,
          failedCount: agentResults.length - completedResults.length,
        };
      });

      // Step 4: Final synthesis
      const synthesis = await context.run('synthesize', async () => {
        await updateWorkflowStatus(redis, context.workflowRunId, {
          currentPhase: 'synthesis',
        });

        if (useClaude && env.ANTHROPIC_API_KEY && aggregation.completedCount > 0) {
          // Synthesize agent responses
          const agentOutputs = agentResults
            .filter((r) => r.status === 'complete')
            .map((r) => `[${r.agent}] (confidence: ${r.confidence.toFixed(2)}):\n${r.output}`)
            .join('\n\n---\n\n');

          const result = await invokeAgent(
            env,
            'default',
            `You are the synthesis coordinator. Multiple agents have analyzed this task:\n\nTask: ${task}\n\nAgent Responses:\n${agentOutputs}\n\nProvide a unified synthesis that:\n1. Identifies consensus points\n2. Notes any disagreements\n3. Provides a final recommendation\n4. Assigns an overall confidence score`
          );
          totalTokens += result.tokensUsed;

          return {
            task,
            status: aggregation.consensus ? 'consensus_reached' : 'needs_review',
            confidence: aggregation.avgConfidence,
            synthesis: result.response,
            agentResults,
          };
        }

        return {
          task,
          status: aggregation.consensus ? 'consensus_reached' : 'needs_review',
          confidence: aggregation.avgConfidence,
          agentResults,
        };
      });

      // Update final status
      await updateWorkflowStatus(redis, context.workflowRunId, {
        status: 'complete',
        currentPhase: undefined,
        completedAt: new Date().toISOString(),
      });

      return {
        workflowId: context.workflowRunId,
        sessionId,
        ...synthesis,
        totalTokensUsed: totalTokens,
        claudeEnabled: useClaude,
      };
    },
    {
      retries: 2,
    }
  )
);

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
  const workflows: Array<{ runId: string; status: string; startedAt: string }> = [];

  for (const key of keys.slice(0, 20)) { // Limit to 20 most recent
    const status = await redis.get<WorkflowStatus>(key);
    if (status) {
      workflows.push({
        runId: status.runId,
        status: status.status,
        startedAt: status.startedAt,
      });
    }
  }

  // Sort by start time
  workflows.sort((a, b) => new Date(b.startedAt).getTime() - new Date(a.startedAt).getTime());

  return c.json({
    count: workflows.length,
    workflows,
  });
});

// =============================================================================
// WORKFLOW INFO
// =============================================================================

/**
 * GET /workflows
 *
 * List available workflows.
 */
workflows.get('/', async (c) => {
  return c.json({
    workflows: [
      {
        name: 'feature-dev',
        description: '7-phase feature development workflow',
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
      },
      {
        name: 'power-mode',
        description: 'Multi-agent parallel orchestration workflow',
        endpoint: '/v1/workflows/power-mode',
        pattern: 'orchestrator-workers',
      },
    ],
  });
});

export default workflows;
