/**
 * Agent Discovery Routes
 *
 * Part of Issue #101 (Upstash Vector Integration)
 *
 * Semantic agent search using Upstash Vector.
 * Enables natural language queries like "optimize database" to find query-optimizer.
 */

import { Hono } from 'hono';
import { Index } from '@upstash/vector';
import type { Env, Variables } from '../types';

// Agent metadata stored in Upstash Vector
// Must extend Record<string, unknown> for Upstash Vector compatibility
interface AgentMetadata extends Record<string, unknown> {
  name: string;
  tier: 'tier-1-always-active' | 'tier-2-on-demand' | 'feature-workflow';
  keywords: string[];
  description: string;
}

const agents = new Hono<{ Bindings: Env; Variables: Variables }>();

// =============================================================================
// SEMANTIC AGENT SEARCH
// =============================================================================

/**
 * POST /agents/search
 *
 * Search for agents using natural language query.
 * Uses Upstash Vector with automatic embeddings (BAAI/bge-large-en-v1.5).
 *
 * Request:
 *   { query: string, topK?: number, minScore?: number, tier?: string }
 *
 * Response:
 *   {
 *     query: string,
 *     matches: Array<{ agent, score, tier, description, keywords }>,
 *     fallback_to_keywords: boolean
 *   }
 */
agents.post('/search', async (c) => {
  // Check if Vector is configured
  if (!c.env.UPSTASH_VECTOR_REST_URL || !c.env.UPSTASH_VECTOR_REST_TOKEN) {
    return c.json(
      {
        error: 'Vector search not configured',
        fallback_to_keywords: true,
      },
      503
    );
  }

  const index = new Index<AgentMetadata>({
    url: c.env.UPSTASH_VECTOR_REST_URL,
    token: c.env.UPSTASH_VECTOR_REST_TOKEN,
  });

  const body = await c.req.json<{
    query: string;
    topK?: number;
    minScore?: number;
    tier?: string;
  }>();

  if (!body.query || typeof body.query !== 'string') {
    return c.json({ error: 'Query is required' }, 400);
  }

  const topK = Math.min(body.topK || 3, 10); // Cap at 10
  const minScore = body.minScore ?? 0.3;

  // Build filter for tier if specified
  let filter: string | undefined;
  if (body.tier) {
    filter = `tier = '${body.tier}'`;
  }

  try {
    const results = await index.query({
      data: body.query, // Auto-embed with BGE model
      topK,
      includeMetadata: true,
      filter,
    });

    // Filter by minimum score and format response
    const matches = results
      .filter((r) => r.score >= minScore)
      .map((r) => ({
        agent: r.metadata?.name || String(r.id),
        score: Math.round(r.score * 1000) / 1000, // Round to 3 decimals
        tier: r.metadata?.tier,
        description: r.metadata?.description,
        keywords: r.metadata?.keywords,
      }));

    return c.json({
      query: body.query,
      matches,
      fallback_to_keywords: matches.length === 0,
    });
  } catch (error) {
    console.error('Vector search error:', error);
    return c.json(
      {
        error: 'Vector search failed',
        fallback_to_keywords: true,
      },
      500
    );
  }
});

// =============================================================================
// LIST INDEXED AGENTS
// =============================================================================

/**
 * GET /agents/list
 *
 * List all indexed agents.
 * Useful for debugging and verification.
 */
agents.get('/list', async (c) => {
  if (!c.env.UPSTASH_VECTOR_REST_URL || !c.env.UPSTASH_VECTOR_REST_TOKEN) {
    return c.json({ error: 'Vector search not configured' }, 503);
  }

  const index = new Index<AgentMetadata>({
    url: c.env.UPSTASH_VECTOR_REST_URL,
    token: c.env.UPSTASH_VECTOR_REST_TOKEN,
  });

  try {
    // Fetch all vectors (limited to 100)
    const results = await index.range({
      cursor: '0',
      limit: 100,
      includeMetadata: true,
    });

    const agentList = results.vectors.map((v) => ({
      id: v.id,
      name: v.metadata?.name as string | undefined,
      tier: v.metadata?.tier as string | undefined,
      description: ((v.metadata?.description as string | undefined)?.slice(0, 100) || '') + '...',
    }));

    // Group by tier
    const byTier = {
      'tier-1-always-active': agentList.filter((a) => a.tier === 'tier-1-always-active'),
      'tier-2-on-demand': agentList.filter((a) => a.tier === 'tier-2-on-demand'),
      'feature-workflow': agentList.filter((a) => a.tier === 'feature-workflow'),
    };

    return c.json({
      total: agentList.length,
      byTier: {
        'tier-1-always-active': byTier['tier-1-always-active'].length,
        'tier-2-on-demand': byTier['tier-2-on-demand'].length,
        'feature-workflow': byTier['feature-workflow'].length,
      },
      agents: agentList,
    });
  } catch (error) {
    console.error('List agents error:', error);
    return c.json({ error: 'Failed to list agents' }, 500);
  }
});

// =============================================================================
// AGENT INFO
// =============================================================================

/**
 * GET /agents/:name
 *
 * Get details for a specific agent.
 */
agents.get('/:name', async (c) => {
  if (!c.env.UPSTASH_VECTOR_REST_URL || !c.env.UPSTASH_VECTOR_REST_TOKEN) {
    return c.json({ error: 'Vector search not configured' }, 503);
  }

  const index = new Index<AgentMetadata>({
    url: c.env.UPSTASH_VECTOR_REST_URL,
    token: c.env.UPSTASH_VECTOR_REST_TOKEN,
  });

  const name = c.req.param('name');

  try {
    const result = await index.fetch([name], { includeMetadata: true });

    if (!result || result.length === 0 || !result[0]) {
      return c.json({ error: 'Agent not found' }, 404);
    }

    const agent = result[0];

    return c.json({
      id: agent.id,
      name: agent.metadata?.name,
      tier: agent.metadata?.tier,
      description: agent.metadata?.description,
      keywords: agent.metadata?.keywords,
    });
  } catch (error) {
    console.error('Fetch agent error:', error);
    return c.json({ error: 'Failed to fetch agent' }, 500);
  }
});

export default agents;
