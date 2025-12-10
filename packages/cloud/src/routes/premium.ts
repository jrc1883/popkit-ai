/**
 * Premium Feature Routes
 *
 * Part of Issue #152 (Server-Side Premium Skill Execution)
 *
 * Provides server-side generation for premium skills.
 * Templates are rendered server-side and returned to the user.
 * No AI inference required - pure template substitution.
 */

import { Hono } from 'hono';
import type { Env, Variables, ApiKeyData } from '../types';
import { generateMCPServer, type MCPGeneratorContext } from '../templates/mcp-generator';

const premium = new Hono<{ Bindings: Env; Variables: Variables }>();

/**
 * Check if user has premium access.
 */
function isPremiumTier(tier: string | undefined): boolean {
  return tier === 'pro' || tier === 'team';
}

/**
 * Get user API key from context.
 */
function getApiKey(c: { get: (key: string) => unknown }): ApiKeyData | undefined {
  return c.get('apiKey') as ApiKeyData | undefined;
}

// =============================================================================
// MCP GENERATOR
// =============================================================================

/**
 * Generate a custom MCP server for a project.
 *
 * POST /premium/generate/mcp
 * Body: {
 *   projectName: string,
 *   techStack: string[],
 *   services?: string[],
 *   devPort?: number,
 *   dbPort?: number,
 *   framework?: string,
 *   database?: string,
 *   includeEmbeddings?: boolean,
 *   includeRoutines?: boolean
 * }
 *
 * Returns: {
 *   success: true,
 *   files: [{ path: string, content: string }, ...],
 *   instructions: string,
 *   tools: string[]
 * }
 */
premium.post('/generate/mcp', async (c) => {
  const apiKey = getApiKey(c);

  // Require premium subscription
  if (!isPremiumTier(apiKey?.tier)) {
    return c.json(
      {
        error: 'Premium subscription required',
        tier: apiKey?.tier || 'none',
        upgrade_url: 'https://popkit.dev/pricing',
      },
      403
    );
  }

  try {
    const body = await c.req.json<MCPGeneratorContext>();

    // Validate required fields
    if (!body.projectName) {
      return c.json({ error: 'projectName is required' }, 400);
    }
    if (!body.techStack || !Array.isArray(body.techStack)) {
      return c.json({ error: 'techStack array is required' }, 400);
    }

    // Generate MCP server
    const result = generateMCPServer({
      projectName: body.projectName,
      techStack: body.techStack,
      services: body.services || [],
      devPort: body.devPort,
      dbPort: body.dbPort,
      framework: body.framework,
      database: body.database,
      includeEmbeddings: body.includeEmbeddings ?? true,
      includeRoutines: body.includeRoutines ?? true,
    });

    return c.json({
      success: true,
      ...result,
    });
  } catch (error) {
    console.error('MCP generation error:', error);
    return c.json(
      {
        error: 'Failed to generate MCP server',
        message: error instanceof Error ? error.message : String(error),
      },
      500
    );
  }
});

// =============================================================================
// SKILL EXECUTION ENDPOINTS
// =============================================================================

/**
 * List available premium skills.
 *
 * GET /premium/skills
 */
premium.get('/skills', async (c) => {
  const apiKey = getApiKey(c);

  return c.json({
    tier: apiKey?.tier || 'free',
    skills: [
      {
        id: 'mcp-generator',
        name: 'MCP Server Generator',
        description: 'Generate project-specific MCP servers with health checks, git tools, and more',
        endpoint: '/premium/generate/mcp',
        tier: 'pro',
        available: isPremiumTier(apiKey?.tier),
      },
      // Future skills can be added here
      {
        id: 'morning-generator',
        name: 'Custom Morning Routine',
        description: 'Generate project-specific morning health check routines',
        endpoint: '/premium/generate/morning',
        tier: 'pro',
        available: false, // Not yet implemented
        coming_soon: true,
      },
      {
        id: 'nightly-generator',
        name: 'Custom Nightly Routine',
        description: 'Generate project-specific nightly cleanup routines',
        endpoint: '/premium/generate/nightly',
        tier: 'pro',
        available: false, // Not yet implemented
        coming_soon: true,
      },
    ],
  });
});

/**
 * Check premium access status.
 *
 * GET /premium/status
 */
premium.get('/status', async (c) => {
  const apiKey = getApiKey(c);

  return c.json({
    tier: apiKey?.tier || 'free',
    isPremium: isPremiumTier(apiKey?.tier),
    userId: apiKey?.userId,
    features: {
      mcp_generator: isPremiumTier(apiKey?.tier),
      custom_routines: isPremiumTier(apiKey?.tier),
      priority_support: isPremiumTier(apiKey?.tier),
    },
    upgrade_url: isPremiumTier(apiKey?.tier) ? null : 'https://popkit.dev/pricing',
  });
});

export default premium;
