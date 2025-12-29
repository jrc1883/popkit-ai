/**
 * Memory Tools - Cross-project learning recall
 *
 * Part of Issue #112 (Universal MCP Server)
 *
 * MCP tools for storing and recalling learnings across projects.
 */

import { z } from 'zod';
import type { PopKitConfig } from '../config.js';
import { getApiHeaders } from '../config.js';

// =============================================================================
// SCHEMAS
// =============================================================================

export const MemoryRecallInputSchema = z.object({
  query: z.string().describe('What to recall (natural language)'),
  limit: z.number().min(1).max(10).default(5),
});

export const MemoryStoreInputSchema = z.object({
  key: z.string().describe('Unique key for this memory'),
  content: z.string().describe('Content to remember'),
  context: z.string().optional().describe('Context about when/where this was learned'),
  tags: z.array(z.string()).optional(),
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

export const memoryTools: Tool[] = [
  {
    name: 'popkit_memory_recall',
    description: 'Recall learnings from previous projects and sessions. Uses semantic search to find relevant memories.',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'What to recall (natural language)',
        },
        limit: {
          type: 'number',
          description: 'Maximum number of memories to return (default: 5)',
          default: 5,
        },
      },
      required: ['query'],
    },
    handler: async (args, config) => {
      const input = MemoryRecallInputSchema.parse(args);

      // Use pattern search as memory recall (patterns are a form of memory)
      const response = await fetch(`${config.apiUrl}/v1/patterns/search`, {
        method: 'POST',
        headers: getApiHeaders(config),
        body: JSON.stringify({
          query: input.query,
          limit: input.limit,
          threshold: 0.5, // Lower threshold for memory recall
        }),
      });

      if (!response.ok) {
        // Return empty on failure (non-critical)
        return {
          memories: [],
          message: 'Memory recall unavailable',
        };
      }

      const data = await response.json() as { results: Array<{ id: string; trigger: string; solution: string; similarity: number }> };

      // Transform patterns to memory format
      return {
        memories: data.results.map((p) => ({
          id: p.id,
          content: p.solution,
          context: p.trigger,
          relevance: p.similarity,
        })),
        count: data.results.length,
      };
    },
  },
  {
    name: 'popkit_memory_store',
    description: 'Store a learning for future recall. Helps build cross-project knowledge.',
    inputSchema: {
      type: 'object',
      properties: {
        key: {
          type: 'string',
          description: 'Unique key for this memory',
        },
        content: {
          type: 'string',
          description: 'Content to remember',
        },
        context: {
          type: 'string',
          description: 'Context about when/where this was learned',
        },
        tags: {
          type: 'array',
          items: { type: 'string' },
          description: 'Tags for categorization',
        },
      },
      required: ['key', 'content'],
    },
    handler: async (args, config) => {
      const input = MemoryStoreInputSchema.parse(args);

      // Store as a pattern
      const response = await fetch(`${config.apiUrl}/v1/patterns/submit`, {
        method: 'POST',
        headers: getApiHeaders(config),
        body: JSON.stringify({
          trigger: input.context || input.key,
          solution: input.content,
          context: {
            languages: input.tags?.filter((t) => ['typescript', 'javascript', 'python', 'rust', 'go'].includes(t.toLowerCase())),
            frameworks: input.tags?.filter((t) => ['react', 'vue', 'angular', 'nextjs', 'express', 'hono'].includes(t.toLowerCase())),
          },
        }),
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Memory store failed: ${response.status} ${error}`);
      }

      const data = await response.json() as { pattern_id?: string; status?: string };

      return {
        memoryId: data.pattern_id || `mem_${Date.now().toString(36)}`,
        stored: true,
        key: input.key,
      };
    },
  },
];
