/**
 * Agent Tools - Power Mode lite coordination
 *
 * Part of Issue #112 (Universal MCP Server)
 *
 * MCP tools for lightweight multi-agent coordination.
 */

import { z } from 'zod';
import type { PopKitConfig } from '../config.js';
import { getApiHeaders } from '../config.js';

// =============================================================================
// SCHEMAS
// =============================================================================

export const AgentCheckinInputSchema = z.object({
  agentId: z.string(),
  agentType: z.string(),
  sessionId: z.string(),
  state: z.object({
    phase: z.string().optional(),
    progress: z.number().min(0).max(1).optional(),
    currentTask: z.string().optional(),
    findings: z.number().optional(),
    filesModified: z.array(z.string()).optional(),
  }),
});

export const AgentBarrierInputSchema = z.object({
  sessionId: z.string(),
  barrier: z.string(),
  agentId: z.string(),
});

export const AgentBroadcastInputSchema = z.object({
  sessionId: z.string(),
  fromAgent: z.string(),
  message: z.object({
    type: z.enum(['DISCOVERY', 'INSIGHT', 'RESULT', 'PROGRESS', 'ALERT']),
    content: z.string(),
    relevantTo: z.array(z.string()).optional(),
    confidence: z.number().min(0).max(1).optional(),
  }),
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

export const agentTools: Tool[] = [
  {
    name: 'popkit_agent_checkin',
    description: 'Agent progress check-in for Power Mode coordination. Updates agent state and retrieves waiting messages.',
    inputSchema: {
      type: 'object',
      properties: {
        agentId: {
          type: 'string',
          description: 'Unique agent identifier',
        },
        agentType: {
          type: 'string',
          description: 'Type of agent (e.g., "code-reviewer", "test-writer")',
        },
        sessionId: {
          type: 'string',
          description: 'Power Mode session ID',
        },
        state: {
          type: 'object',
          properties: {
            phase: { type: 'string' },
            progress: { type: 'number' },
            currentTask: { type: 'string' },
            findings: { type: 'number' },
            filesModified: { type: 'array', items: { type: 'string' } },
          },
        },
      },
      required: ['agentId', 'agentType', 'sessionId', 'state'],
    },
    handler: async (args, config) => {
      const input = AgentCheckinInputSchema.parse(args);

      // Send check-in via broadcast
      const broadcastResponse = await fetch(`${config.apiUrl}/v1/messages/broadcast`, {
        method: 'POST',
        headers: getApiHeaders(config),
        body: JSON.stringify({
          type: 'PROGRESS',
          fromAgent: input.agentId,
          sessionId: input.sessionId,
          payload: {
            progress: input.state.progress || 0,
            currentTask: input.state.currentTask || 'working',
            filesModified: input.state.filesModified,
          },
          tags: [input.agentType, input.state.phase || 'unknown'],
          priority: 'normal',
        }),
      });

      // Poll for messages
      const pollResponse = await fetch(
        `${config.apiUrl}/v1/messages/poll/${input.agentId}?sessionId=${input.sessionId}&limit=10`,
        {
          method: 'GET',
          headers: getApiHeaders(config),
        }
      );

      let messages: unknown[] = [];
      if (pollResponse.ok) {
        const data = await pollResponse.json() as { messages?: unknown[] };
        messages = data.messages || [];
      }

      return {
        received: broadcastResponse.ok,
        messages,
        timestamp: new Date().toISOString(),
      };
    },
  },
  {
    name: 'popkit_agent_barrier',
    description: 'Request sync barrier across agents. Blocks until all agents acknowledge or timeout.',
    inputSchema: {
      type: 'object',
      properties: {
        sessionId: {
          type: 'string',
          description: 'Power Mode session ID',
        },
        barrier: {
          type: 'string',
          description: 'Barrier name (e.g., "phase-1-complete")',
        },
        agentId: {
          type: 'string',
          description: 'Agent acknowledging the barrier',
        },
      },
      required: ['sessionId', 'barrier', 'agentId'],
    },
    handler: async (args, config) => {
      const input = AgentBarrierInputSchema.parse(args);

      // Try to acknowledge existing barrier
      const ackResponse = await fetch(`${config.apiUrl}/v1/workflows/sync/ack/${input.barrier}`, {
        method: 'POST',
        headers: getApiHeaders(config),
        body: JSON.stringify({ agentId: input.agentId }),
      });

      if (ackResponse.ok) {
        return await ackResponse.json();
      }

      // If barrier doesn't exist, check status
      const statusResponse = await fetch(
        `${config.apiUrl}/v1/workflows/sync/status/${input.barrier}`,
        {
          method: 'GET',
          headers: getApiHeaders(config),
        }
      );

      if (statusResponse.ok) {
        return await statusResponse.json();
      }

      // Barrier not found
      return {
        status: 'not_found',
        barrier: input.barrier,
        message: 'Barrier not found. Create it first or proceed without waiting.',
      };
    },
  },
  {
    name: 'popkit_agent_broadcast',
    description: 'Broadcast message to other agents in the session.',
    inputSchema: {
      type: 'object',
      properties: {
        sessionId: {
          type: 'string',
          description: 'Power Mode session ID',
        },
        fromAgent: {
          type: 'string',
          description: 'Sending agent ID',
        },
        message: {
          type: 'object',
          properties: {
            type: {
              type: 'string',
              enum: ['DISCOVERY', 'INSIGHT', 'RESULT', 'PROGRESS', 'ALERT'],
            },
            content: { type: 'string' },
            relevantTo: { type: 'array', items: { type: 'string' } },
            confidence: { type: 'number' },
          },
          required: ['type', 'content'],
        },
      },
      required: ['sessionId', 'fromAgent', 'message'],
    },
    handler: async (args, config) => {
      const input = AgentBroadcastInputSchema.parse(args);

      // Map message type to payload structure
      const payload = {
        content: input.message.content,
        relevantTo: input.message.relevantTo || [],
        confidence: input.message.confidence || 0.8,
        category: input.message.type.toLowerCase(),
      };

      const response = await fetch(`${config.apiUrl}/v1/messages/broadcast`, {
        method: 'POST',
        headers: getApiHeaders(config),
        body: JSON.stringify({
          type: input.message.type,
          fromAgent: input.fromAgent,
          sessionId: input.sessionId,
          payload,
          tags: input.message.relevantTo || [],
          priority: input.message.type === 'ALERT' ? 'high' : 'normal',
        }),
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Broadcast failed: ${response.status} ${error}`);
      }

      const data = await response.json() as { messageId?: string };

      return {
        delivered: true,
        messageId: data.messageId,
        recipients: 'session',
      };
    },
  },
  {
    name: 'popkit_agent_search',
    description: 'Search for agents by capability using natural language.',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'Natural language description of needed capability',
        },
        topK: {
          type: 'number',
          description: 'Number of agents to return (default: 3)',
          default: 3,
        },
      },
      required: ['query'],
    },
    handler: async (args, config) => {
      const { query, topK = 3 } = z.object({
        query: z.string(),
        topK: z.number().default(3),
      }).parse(args);

      const response = await fetch(`${config.apiUrl}/v1/agents/search`, {
        method: 'POST',
        headers: getApiHeaders(config),
        body: JSON.stringify({ query, topK }),
      });

      if (!response.ok) {
        // Return fallback suggestions on error
        return {
          query,
          matches: [],
          fallback_to_keywords: true,
          message: 'Agent search unavailable',
        };
      }

      return await response.json();
    },
  },
];
