/**
 * Research Routes - Knowledge Base Management
 *
 * Part of Issue #142 (Research Index with Embeddings)
 * Parent: Epic #127 (Research Management System)
 *
 * Cloud-based research entry storage and semantic search.
 * Enables cross-project knowledge sharing for team tier.
 */

import { Hono } from 'hono';
import { Index } from '@upstash/vector';
import { Redis } from '@upstash/redis';
import type { Env, Variables, Tier } from '../types';

// =============================================================================
// TYPES
// =============================================================================

interface ResearchEntry {
  id: string;
  type: 'decision' | 'finding' | 'learning' | 'spike';
  title: string;
  content: string;
  context?: string;
  rationale?: string;
  alternatives?: string[];
  tags: string[];
  project: string;
  references?: string[];
  createdAt: string;
  updatedAt: string;
  userId: string;
  teamId?: string; // For team-shared entries
}

interface ResearchMetadata {
  type: string;
  title: string;
  tags: string[];
  project: string;
  userId: string;
  teamId?: string;
}

// =============================================================================
// ROUTES
// =============================================================================

const research = new Hono<{ Bindings: Env; Variables: Variables }>();

/**
 * Get user info from API key context.
 */
function getUserInfo(c: { get: (key: string) => unknown }): { userId: string; tier: Tier } {
  const apiKey = c.get('apiKey') as { userId: string; tier: Tier } | undefined;
  if (!apiKey) {
    throw new Error('No API key in context');
  }
  return { userId: apiKey.userId, tier: apiKey.tier };
}

/**
 * Check if research feature is available for tier.
 */
function canUseResearch(tier: Tier): boolean {
  return tier === 'pro' || tier === 'team';
}

/**
 * Check if team sharing is available.
 */
function canShareWithTeam(tier: Tier): boolean {
  return tier === 'team';
}

// =============================================================================
// CREATE / UPDATE RESEARCH ENTRY
// =============================================================================

/**
 * POST /v1/research
 *
 * Create or update a research entry.
 * Pro tier required for cloud storage.
 */
research.post('/', async (c) => {
  const { userId, tier } = getUserInfo(c);

  if (!canUseResearch(tier)) {
    return c.json({
      error: 'Research cloud sync requires Pro or Team tier',
      upgradeUrl: 'https://popkit.dev/pricing',
    }, 403);
  }

  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const body = await c.req.json<Partial<ResearchEntry>>();

  // Validate required fields
  if (!body.id || !body.type || !body.title || !body.content) {
    return c.json({ error: 'Missing required fields: id, type, title, content' }, 400);
  }

  // Validate type
  const validTypes = ['decision', 'finding', 'learning', 'spike'];
  if (!validTypes.includes(body.type)) {
    return c.json({ error: `Invalid type. Must be one of: ${validTypes.join(', ')}` }, 400);
  }

  const now = new Date().toISOString();
  const entry: ResearchEntry = {
    id: body.id,
    type: body.type as ResearchEntry['type'],
    title: body.title,
    content: body.content,
    context: body.context || '',
    rationale: body.rationale || '',
    alternatives: body.alternatives || [],
    tags: body.tags || [],
    project: body.project || 'default',
    references: body.references || [],
    createdAt: body.createdAt || now,
    updatedAt: now,
    userId,
    teamId: canShareWithTeam(tier) ? body.teamId : undefined,
  };

  // Store entry in Redis
  const entryKey = `popkit:research:${userId}:${entry.id}`;
  await redis.set(entryKey, JSON.stringify(entry));

  // Update user's research index
  await redis.sadd(`popkit:research:${userId}:index`, entry.id);

  // Update tag indexes
  for (const tag of entry.tags) {
    await redis.sadd(`popkit:research:${userId}:tag:${tag}`, entry.id);
  }

  // Update project index
  await redis.sadd(`popkit:research:${userId}:project:${entry.project}`, entry.id);

  // Generate embedding if Vector is configured
  let embeddingId: string | undefined;
  if (c.env.UPSTASH_VECTOR_REST_URL && c.env.UPSTASH_VECTOR_REST_TOKEN) {
    try {
      const index = new Index({
        url: c.env.UPSTASH_VECTOR_REST_URL,
        token: c.env.UPSTASH_VECTOR_REST_TOKEN,
      });

      // Combine searchable content
      const searchableText = [
        entry.title,
        entry.content,
        entry.context,
        entry.rationale,
      ].filter(Boolean).join('\n\n');

      // Upsert to vector index
      embeddingId = `research_${userId}_${entry.id}`;
      await index.upsert({
        id: embeddingId,
        data: searchableText,
        metadata: {
          type: entry.type,
          title: entry.title,
          tags: entry.tags,
          project: entry.project,
          userId,
          teamId: entry.teamId,
        } as ResearchMetadata,
      });
    } catch (e) {
      console.error('Failed to generate embedding:', e);
      // Continue without embedding - not a fatal error
    }
  }

  return c.json({
    status: 'created',
    id: entry.id,
    embeddingId,
  });
});

// =============================================================================
// GET RESEARCH ENTRY
// =============================================================================

/**
 * GET /v1/research/:id
 *
 * Get a single research entry.
 */
research.get('/:id', async (c) => {
  const { userId, tier } = getUserInfo(c);
  const entryId = c.req.param('id');

  if (!canUseResearch(tier)) {
    return c.json({
      error: 'Research cloud sync requires Pro or Team tier',
      upgradeUrl: 'https://popkit.dev/pricing',
    }, 403);
  }

  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const entryJson = await redis.get<string>(`popkit:research:${userId}:${entryId}`);
  if (!entryJson) {
    return c.json({ error: 'Entry not found' }, 404);
  }

  const entry = JSON.parse(entryJson) as ResearchEntry;
  return c.json({ entry });
});

// =============================================================================
// LIST RESEARCH ENTRIES
// =============================================================================

/**
 * GET /v1/research
 *
 * List research entries with optional filters.
 * Query params: type, project, tag, limit
 */
research.get('/', async (c) => {
  const { userId, tier } = getUserInfo(c);

  if (!canUseResearch(tier)) {
    return c.json({
      error: 'Research cloud sync requires Pro or Team tier',
      upgradeUrl: 'https://popkit.dev/pricing',
    }, 403);
  }

  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const type = c.req.query('type');
  const project = c.req.query('project');
  const tag = c.req.query('tag');
  const limit = parseInt(c.req.query('limit') || '20', 10);

  // Get entry IDs based on filters
  let entryIds: string[];

  if (tag) {
    entryIds = await redis.smembers(`popkit:research:${userId}:tag:${tag}`) as string[];
  } else if (project) {
    entryIds = await redis.smembers(`popkit:research:${userId}:project:${project}`) as string[];
  } else {
    entryIds = await redis.smembers(`popkit:research:${userId}:index`) as string[];
  }

  // Fetch entries
  const entries: ResearchEntry[] = [];
  for (const id of entryIds.slice(0, limit * 2)) { // Fetch extra for filtering
    const entryJson = await redis.get<string>(`popkit:research:${userId}:${id}`);
    if (entryJson) {
      const entry = JSON.parse(entryJson) as ResearchEntry;

      // Apply type filter
      if (type && entry.type !== type) continue;

      entries.push(entry);
      if (entries.length >= limit) break;
    }
  }

  // Sort by updatedAt (newest first)
  entries.sort((a, b) => b.updatedAt.localeCompare(a.updatedAt));

  return c.json({
    entries,
    total: entryIds.length,
    hasMore: entryIds.length > limit,
  });
});

// =============================================================================
// DELETE RESEARCH ENTRY
// =============================================================================

/**
 * DELETE /v1/research/:id
 *
 * Delete a research entry.
 */
research.delete('/:id', async (c) => {
  const { userId, tier } = getUserInfo(c);
  const entryId = c.req.param('id');

  if (!canUseResearch(tier)) {
    return c.json({
      error: 'Research cloud sync requires Pro or Team tier',
      upgradeUrl: 'https://popkit.dev/pricing',
    }, 403);
  }

  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  // Get entry first to clean up indexes
  const entryJson = await redis.get<string>(`popkit:research:${userId}:${entryId}`);
  if (!entryJson) {
    return c.json({ error: 'Entry not found' }, 404);
  }

  const entry = JSON.parse(entryJson) as ResearchEntry;

  // Delete entry
  await redis.del(`popkit:research:${userId}:${entryId}`);

  // Remove from indexes
  await redis.srem(`popkit:research:${userId}:index`, entryId);
  for (const tag of entry.tags) {
    await redis.srem(`popkit:research:${userId}:tag:${tag}`, entryId);
  }
  await redis.srem(`popkit:research:${userId}:project:${entry.project}`, entryId);

  // Remove from vector index
  if (c.env.UPSTASH_VECTOR_REST_URL && c.env.UPSTASH_VECTOR_REST_TOKEN) {
    try {
      const index = new Index({
        url: c.env.UPSTASH_VECTOR_REST_URL,
        token: c.env.UPSTASH_VECTOR_REST_TOKEN,
      });
      await index.delete(`research_${userId}_${entryId}`);
    } catch {
      // Ignore vector deletion errors
    }
  }

  return c.json({ status: 'deleted', id: entryId });
});

// =============================================================================
// SEMANTIC SEARCH
// =============================================================================

/**
 * POST /v1/research/search
 *
 * Semantic search across research entries.
 * Body: { query: string, type?: string, project?: string, limit?: number }
 */
research.post('/search', async (c) => {
  const { userId, tier } = getUserInfo(c);

  if (!canUseResearch(tier)) {
    return c.json({
      error: 'Research cloud sync requires Pro or Team tier',
      upgradeUrl: 'https://popkit.dev/pricing',
    }, 403);
  }

  if (!c.env.UPSTASH_VECTOR_REST_URL || !c.env.UPSTASH_VECTOR_REST_TOKEN) {
    return c.json({ error: 'Vector search not configured' }, 503);
  }

  const body = await c.req.json<{
    query: string;
    type?: string;
    project?: string;
    limit?: number;
    minScore?: number;
  }>();

  if (!body.query) {
    return c.json({ error: 'Missing required field: query' }, 400);
  }

  const limit = body.limit || 5;
  const minScore = body.minScore || 0.6;

  const index = new Index({
    url: c.env.UPSTASH_VECTOR_REST_URL,
    token: c.env.UPSTASH_VECTOR_REST_TOKEN,
  });

  // Build filter for user's entries
  let filter = `userId = "${userId}"`;

  if (body.type) {
    filter += ` AND type = "${body.type}"`;
  }

  if (body.project) {
    filter += ` AND project = "${body.project}"`;
  }

  // Query vector index
  const results = await index.query({
    data: body.query,
    topK: limit,
    includeMetadata: true,
    filter,
  });

  // Fetch full entries for results
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  interface SearchResultItem {
    entry: ResearchEntry;
    score: number;
    rank: number;
  }

  const searchResults: SearchResultItem[] = [];

  for (let i = 0; i < results.length; i++) {
    const result = results[i];
    if (result.score < minScore) continue;

    // Extract entry ID from vector ID (format: research_userId_entryId)
    const vectorId = result.id as string;
    const entryId = vectorId.replace(`research_${userId}_`, '');

    const entryJson = await redis.get<string>(`popkit:research:${userId}:${entryId}`);
    if (entryJson) {
      const entry = JSON.parse(entryJson) as ResearchEntry;
      searchResults.push({
        entry,
        score: result.score,
        rank: searchResults.length + 1,
      });
    }
  }

  return c.json({
    results: searchResults,
    query: body.query,
    total: searchResults.length,
  });
});

// =============================================================================
// TAGS AND STATS
// =============================================================================

/**
 * GET /v1/research/tags
 *
 * Get all tags with counts.
 */
research.get('/meta/tags', async (c) => {
  const { userId, tier } = getUserInfo(c);

  if (!canUseResearch(tier)) {
    return c.json({
      error: 'Research cloud sync requires Pro or Team tier',
      upgradeUrl: 'https://popkit.dev/pricing',
    }, 403);
  }

  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  // Get all entry IDs
  const entryIds = await redis.smembers(`popkit:research:${userId}:index`) as string[];

  // Count tags across all entries
  const tagCounts: Record<string, number> = {};

  for (const id of entryIds) {
    const entryJson = await redis.get<string>(`popkit:research:${userId}:${id}`);
    if (entryJson) {
      const entry = JSON.parse(entryJson) as ResearchEntry;
      for (const tag of entry.tags) {
        tagCounts[tag] = (tagCounts[tag] || 0) + 1;
      }
    }
  }

  return c.json({ tags: tagCounts });
});

/**
 * GET /v1/research/stats
 *
 * Get research statistics.
 */
research.get('/meta/stats', async (c) => {
  const { userId, tier } = getUserInfo(c);

  if (!canUseResearch(tier)) {
    return c.json({
      error: 'Research cloud sync requires Pro or Team tier',
      upgradeUrl: 'https://popkit.dev/pricing',
    }, 403);
  }

  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  // Get all entry IDs
  const entryIds = await redis.smembers(`popkit:research:${userId}:index`) as string[];

  // Count by type
  const byType: Record<string, number> = {
    decision: 0,
    finding: 0,
    learning: 0,
    spike: 0,
  };

  const projects = new Set<string>();
  const tags = new Set<string>();

  for (const id of entryIds) {
    const entryJson = await redis.get<string>(`popkit:research:${userId}:${id}`);
    if (entryJson) {
      const entry = JSON.parse(entryJson) as ResearchEntry;
      byType[entry.type] = (byType[entry.type] || 0) + 1;
      projects.add(entry.project);
      entry.tags.forEach(t => tags.add(t));
    }
  }

  return c.json({
    total: entryIds.length,
    byType,
    projects: projects.size,
    tags: tags.size,
  });
});

export default research;
