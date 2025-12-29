/**
 * Pattern Tools - Cross-project pattern search and submission
 *
 * Part of Issue #112 (Universal MCP Server)
 *
 * MCP tools for accessing PopKit's collective learning system.
 */

import { z } from 'zod';
import type { PopKitConfig } from '../config.js';
import { getApiHeaders } from '../config.js';

// =============================================================================
// SCHEMAS
// =============================================================================

export const PatternSearchInputSchema = z.object({
  query: z.string().describe('Natural language description of the problem or error'),
  context: z.object({
    languages: z.array(z.string()).optional(),
    frameworks: z.array(z.string()).optional(),
  }).optional(),
  limit: z.number().min(1).max(20).default(5),
  threshold: z.number().min(0).max(1).default(0.7),
});

export const PatternSubmitInputSchema = z.object({
  trigger: z.string().min(10).describe('What triggers this pattern (error description)'),
  solution: z.string().min(10).describe('Anonymized solution approach'),
  context: z.object({
    languages: z.array(z.string()).optional(),
    frameworks: z.array(z.string()).optional(),
    error_types: z.array(z.string()).optional(),
  }).optional(),
});

export const PatternFeedbackInputSchema = z.object({
  patternId: z.string(),
  type: z.enum(['upvote', 'downvote', 'applied', 'success']),
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

export const patternTools: Tool[] = [
  {
    name: 'popkit_pattern_search',
    description: 'Search for solutions to coding problems from the PopKit collective learning database. Returns matching patterns with solutions.',
    inputSchema: {
      type: 'object',
      properties: {
        query: {
          type: 'string',
          description: 'Natural language description of the problem or error',
        },
        context: {
          type: 'object',
          properties: {
            languages: { type: 'array', items: { type: 'string' } },
            frameworks: { type: 'array', items: { type: 'string' } },
          },
        },
        limit: {
          type: 'number',
          description: 'Maximum number of results (default: 5)',
          default: 5,
        },
        threshold: {
          type: 'number',
          description: 'Minimum similarity threshold (default: 0.7)',
          default: 0.7,
        },
      },
      required: ['query'],
    },
    handler: async (args, config) => {
      const input = PatternSearchInputSchema.parse(args);

      const response = await fetch(`${config.apiUrl}/v1/patterns/search`, {
        method: 'POST',
        headers: getApiHeaders(config),
        body: JSON.stringify(input),
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Pattern search failed: ${response.status} ${error}`);
      }

      return await response.json();
    },
  },
  {
    name: 'popkit_pattern_submit',
    description: 'Submit a new pattern to the PopKit collective learning database. Patterns are anonymized and help others solve similar problems.',
    inputSchema: {
      type: 'object',
      properties: {
        trigger: {
          type: 'string',
          description: 'What triggers this pattern (error description)',
        },
        solution: {
          type: 'string',
          description: 'Anonymized solution approach',
        },
        context: {
          type: 'object',
          properties: {
            languages: { type: 'array', items: { type: 'string' } },
            frameworks: { type: 'array', items: { type: 'string' } },
            error_types: { type: 'array', items: { type: 'string' } },
          },
        },
      },
      required: ['trigger', 'solution'],
    },
    handler: async (args, config) => {
      const input = PatternSubmitInputSchema.parse(args);

      const response = await fetch(`${config.apiUrl}/v1/patterns/submit`, {
        method: 'POST',
        headers: getApiHeaders(config),
        body: JSON.stringify(input),
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Pattern submit failed: ${response.status} ${error}`);
      }

      return await response.json();
    },
  },
  {
    name: 'popkit_pattern_feedback',
    description: 'Provide feedback on a pattern. Helps improve pattern quality scores.',
    inputSchema: {
      type: 'object',
      properties: {
        patternId: {
          type: 'string',
          description: 'ID of the pattern to provide feedback on',
        },
        type: {
          type: 'string',
          enum: ['upvote', 'downvote', 'applied', 'success'],
          description: 'Type of feedback',
        },
      },
      required: ['patternId', 'type'],
    },
    handler: async (args, config) => {
      const input = PatternFeedbackInputSchema.parse(args);

      const response = await fetch(`${config.apiUrl}/v1/patterns/${input.patternId}/feedback`, {
        method: 'POST',
        headers: getApiHeaders(config),
        body: JSON.stringify({ type: input.type }),
      });

      if (!response.ok) {
        const error = await response.text();
        throw new Error(`Pattern feedback failed: ${response.status} ${error}`);
      }

      return await response.json();
    },
  },
];
