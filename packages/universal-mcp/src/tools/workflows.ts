/**
 * Workflow Tools - Tracked workflow sessions
 *
 * Part of Issue #112 (Universal MCP Server)
 *
 * MCP tools for tracking development workflows with state persistence.
 */

import { z } from 'zod';
import type { PopKitConfig } from '../config.js';
import { getApiHeaders } from '../config.js';

// =============================================================================
// SCHEMAS
// =============================================================================

export const WorkflowStartInputSchema = z.object({
  goal: z.string().describe('Description of the development goal'),
  context: z.object({
    project: z.string().optional(),
    branch: z.string().optional(),
  }).optional(),
});

export const WorkflowCheckpointInputSchema = z.object({
  workflowId: z.string(),
  phase: z.string(),
  progress: z.number().min(0).max(1),
  state: z.record(z.unknown()).optional(),
});

export const WorkflowCompleteInputSchema = z.object({
  workflowId: z.string(),
  outcome: z.enum(['success', 'partial', 'failed', 'cancelled']),
  summary: z.string(),
  metrics: z.object({
    filesChanged: z.number().optional(),
    linesAdded: z.number().optional(),
    linesRemoved: z.number().optional(),
    testsAdded: z.number().optional(),
  }).optional(),
});

// =============================================================================
// TOOL DEFINITIONS
// =============================================================================

export interface Tool {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
  handler: (args: Record<string, unknown>, config: PopKitConfig) => Promise<unknown>;
}

export const workflowTools: Tool[] = [
  {
    name: 'popkit_workflow_start',
    description: 'Start a tracked workflow session. Enables progress tracking and durable state across sessions.',
    inputSchema: {
      type: 'object',
      properties: {
        goal: {
          type: 'string',
          description: 'Description of the development goal',
        },
        context: {
          type: 'object',
          properties: {
            project: { type: 'string' },
            branch: { type: 'string' },
          },
        },
      },
      required: ['goal'],
    },
    handler: async (args, config) => {
      const input = WorkflowStartInputSchema.parse(args);

      // Generate session ID
      const sessionId = `sess_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}`;

      const response = await fetch(`${config.apiUrl}/v1/workflows/feature-dev`, {
        method: 'POST',
        headers: {
          ...getApiHeaders(config),
          'Upstash-Workflow-Init': 'true',
        },
        body: JSON.stringify({
          feature: input.goal,
          projectPath: input.context?.project || process.cwd(),
          sessionId,
          userId: config.apiKey ? 'authenticated' : 'anonymous',
        }),
      });

      if (!response.ok) {
        // If workflow endpoint fails, return a local session
        return {
          workflowId: `local_${sessionId}`,
          status: 'started',
          goal: input.goal,
          createdAt: new Date().toISOString(),
          note: 'Running in local mode (cloud unavailable)',
        };
      }

      return await response.json();
    },
  },
  {
    name: 'popkit_workflow_checkpoint',
    description: 'Save a workflow checkpoint. Persists current state for recovery.',
    inputSchema: {
      type: 'object',
      properties: {
        workflowId: {
          type: 'string',
          description: 'ID of the active workflow',
        },
        phase: {
          type: 'string',
          description: 'Current phase name (e.g., "implementation", "review")',
        },
        progress: {
          type: 'number',
          description: 'Progress as decimal (0.0 to 1.0)',
        },
        state: {
          type: 'object',
          description: 'Arbitrary state to persist',
        },
      },
      required: ['workflowId', 'phase', 'progress'],
    },
    handler: async (args, config) => {
      const input = WorkflowCheckpointInputSchema.parse(args);

      // Handle local workflows
      if (input.workflowId.startsWith('local_')) {
        return {
          checkpointId: `cp_${Date.now().toString(36)}`,
          phase: input.phase,
          progress: input.progress,
          savedAt: new Date().toISOString(),
          note: 'Local checkpoint (not persisted to cloud)',
        };
      }

      const response = await fetch(`${config.apiUrl}/v1/workflows/update/${input.workflowId}`, {
        method: 'POST',
        headers: getApiHeaders(config),
        body: JSON.stringify({
          phase: input.phase,
          result: JSON.stringify(input.state || {}),
        }),
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Checkpoint failed: ${response.status} ${error}`);
      }

      return {
        ...(await response.json()),
        progress: input.progress,
        savedAt: new Date().toISOString(),
      };
    },
  },
  {
    name: 'popkit_workflow_complete',
    description: 'Complete a workflow with outcome and summary.',
    inputSchema: {
      type: 'object',
      properties: {
        workflowId: {
          type: 'string',
          description: 'ID of the workflow to complete',
        },
        outcome: {
          type: 'string',
          enum: ['success', 'partial', 'failed', 'cancelled'],
          description: 'Workflow outcome',
        },
        summary: {
          type: 'string',
          description: 'Summary of what was accomplished',
        },
        metrics: {
          type: 'object',
          properties: {
            filesChanged: { type: 'number' },
            linesAdded: { type: 'number' },
            linesRemoved: { type: 'number' },
            testsAdded: { type: 'number' },
          },
        },
      },
      required: ['workflowId', 'outcome', 'summary'],
    },
    handler: async (args, config) => {
      const input = WorkflowCompleteInputSchema.parse(args);

      // Handle local workflows
      if (input.workflowId.startsWith('local_')) {
        return {
          status: 'completed',
          outcome: input.outcome,
          summary: input.summary,
          completedAt: new Date().toISOString(),
          note: 'Local workflow completed',
        };
      }

      const response = await fetch(`${config.apiUrl}/v1/workflows/update/${input.workflowId}`, {
        method: 'POST',
        headers: getApiHeaders(config),
        body: JSON.stringify({
          phase: 'summary',
          result: JSON.stringify({
            outcome: input.outcome,
            summary: input.summary,
            metrics: input.metrics,
          }),
        }),
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Complete failed: ${response.status} ${error}`);
      }

      return {
        ...(await response.json()),
        status: 'completed',
        outcome: input.outcome,
        completedAt: new Date().toISOString(),
      };
    },
  },
  {
    name: 'popkit_workflow_status',
    description: 'Get the status of a workflow.',
    inputSchema: {
      type: 'object',
      properties: {
        workflowId: {
          type: 'string',
          description: 'ID of the workflow to check',
        },
      },
      required: ['workflowId'],
    },
    handler: async (args, config) => {
      const { workflowId } = z.object({ workflowId: z.string() }).parse(args);

      // Handle local workflows
      if (workflowId.startsWith('local_')) {
        return {
          workflowId,
          status: 'unknown',
          note: 'Local workflows are not tracked',
        };
      }

      const response = await fetch(`${config.apiUrl}/v1/workflows/status/${workflowId}`, {
        method: 'GET',
        headers: getApiHeaders(config),
      });

      if (!response.ok) {
        if (response.status === 404) {
          return { workflowId, status: 'not_found' };
        }
        const error = await response.text();
        throw new Error(`Status check failed: ${response.status} ${error}`);
      }

      return await response.json();
    },
  },
];
