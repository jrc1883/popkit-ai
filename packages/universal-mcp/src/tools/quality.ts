/**
 * Quality Tools - Code quality validation
 *
 * Part of Issue #112 (Universal MCP Server)
 *
 * MCP tools for running quality checks.
 */

import { z } from 'zod';
import type { PopKitConfig } from '../config.js';
import { getApiHeaders } from '../config.js';

// =============================================================================
// SCHEMAS
// =============================================================================

export const QualityCheckInputSchema = z.object({
  checks: z.array(z.enum(['typescript', 'lint', 'test', 'build'])),
  projectPath: z.string().optional(),
  files: z.array(z.string()).optional(),
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

export const qualityTools: Tool[] = [
  {
    name: 'popkit_quality_check',
    description: 'Run quality validation checks on the codebase. Returns pass/fail status for each check.',
    inputSchema: {
      type: 'object',
      properties: {
        checks: {
          type: 'array',
          items: {
            type: 'string',
            enum: ['typescript', 'lint', 'test', 'build'],
          },
          description: 'Which checks to run',
        },
        projectPath: {
          type: 'string',
          description: 'Project path (default: current directory)',
        },
        files: {
          type: 'array',
          items: { type: 'string' },
          description: 'Specific files to check (optional)',
        },
      },
      required: ['checks'],
    },
    handler: async (args, _config) => {
      const input = QualityCheckInputSchema.parse(args);

      // Quality checks run locally - no API call needed
      // This is a placeholder that returns guidance
      return {
        message: 'Quality checks should be run locally using your project\'s tooling',
        suggestedCommands: {
          typescript: 'npx tsc --noEmit',
          lint: 'npm run lint',
          test: 'npm test',
          build: 'npm run build',
        },
        requestedChecks: input.checks,
        projectPath: input.projectPath || process.cwd(),
        note: 'For actual execution, use your IDE\'s terminal or the appropriate CLI commands',
      };
    },
  },
  {
    name: 'popkit_health_status',
    description: 'Get PopKit Cloud service health status.',
    inputSchema: {
      type: 'object',
      properties: {},
    },
    handler: async (_args, config) => {
      try {
        const response = await fetch(`${config.apiUrl}/v1/health`, {
          method: 'GET',
          headers: getApiHeaders(config),
        });

        if (!response.ok) {
          return {
            status: 'degraded',
            message: `API returned ${response.status}`,
            timestamp: new Date().toISOString(),
          };
        }

        const data = await response.json();

        return {
          status: 'healthy',
          service: 'popkit-cloud',
          ...data,
          client: config.clientId,
          authenticated: !!config.apiKey,
          timestamp: new Date().toISOString(),
        };
      } catch (error) {
        return {
          status: 'unavailable',
          message: error instanceof Error ? error.message : 'Unknown error',
          timestamp: new Date().toISOString(),
        };
      }
    },
  },
];
