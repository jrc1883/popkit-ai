import { getRedis } from '../services/redis';
/**
 * Patterns Routes (Collective Learning)
 *
 * Part of Issue #71 (Collective Learning System)
 *
 * Server-side pattern storage and matching for community learning.
 * Anonymized patterns help users find solutions faster.
 */

import { Hono } from 'hono';
import type { Env, Variables } from '../types';

const patterns = new Hono<{ Bindings: Env; Variables: Variables }>();

// Voyage API for embeddings
const VOYAGE_API_URL = 'https://api.voyageai.com/v1/embeddings';
const VOYAGE_MODEL = 'voyage-3-lite';

// Pattern quality thresholds
const MIN_CONFIDENCE_THRESHOLD = 0.7;
const DUPLICATE_THRESHOLD = 0.92;

// =============================================================================
// TYPES
// =============================================================================

interface Pattern {
  id: string;
  trigger: string;           // What triggers this pattern (error description)
  solution: string;          // Anonymized solution approach
  context: {
    languages: string[];
    frameworks: string[];
    error_types: string[];
  };
  quality: {
    upvotes: number;
    downvotes: number;
    applications: number;
    successes: number;
  };
  created_at: string;
  content_hash: string;
}

// =============================================================================
// HELPERS
// =============================================================================

/**
 * Generate embedding via Voyage AI.
 */
async function generateEmbedding(
  text: string,
  apiKey: string,
  inputType: 'document' | 'query' = 'document'
): Promise<{ embedding: number[]; tokens: number }> {
  const response = await fetch(VOYAGE_API_URL, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: VOYAGE_MODEL,
      input: [text],
      input_type: inputType,
    }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Voyage API error: ${response.status} ${error}`);
  }

  const data = await response.json() as {
    data: Array<{ embedding: number[] }>;
    usage: { total_tokens: number };
  };

  return {
    embedding: data.data[0].embedding,
    tokens: data.usage.total_tokens,
  };
}

/**
 * Cosine similarity between two vectors.
 */
function cosineSimilarity(a: number[], b: number[]): number {
  if (a.length !== b.length) return 0;

  let dotProduct = 0;
  let normA = 0;
  let normB = 0;

  for (let i = 0; i < a.length; i++) {
    dotProduct += a[i] * b[i];
    normA += a[i] * a[i];
    normB += b[i] * b[i];
  }

  const magnitude = Math.sqrt(normA) * Math.sqrt(normB);
  return magnitude === 0 ? 0 : dotProduct / magnitude;
}

/**
 * Generate content hash for deduplication.
 */
function generateContentHash(trigger: string, solution: string): string {
  const content = `${trigger.toLowerCase().trim()}::${solution.toLowerCase().trim()}`;
  // Simple hash using charCode sum (good enough for dedup)
  let hash = 0;
  for (let i = 0; i < content.length; i++) {
    hash = ((hash << 5) - hash) + content.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash).toString(36);
}

/**
 * Calculate pattern quality score.
 */
function calculateQualityScore(quality: Pattern['quality']): number {
  const { upvotes, downvotes, applications, successes } = quality;

  if (applications === 0) return 0.5; // Neutral for new patterns

  const successRate = successes / applications;
  const voteRatio = upvotes / Math.max(1, upvotes + downvotes);

  return (successRate * 0.7) + (voteRatio * 0.3);
}

// =============================================================================
// SUBMIT PATTERN
// =============================================================================

/**
 * Submit a new pattern to the collective.
 *
 * POST /patterns/submit
 * Body: {
 *   trigger: string,        // Error/issue description
 *   solution: string,       // Solution approach
 *   context: { languages, frameworks, error_types }
 * }
 */
patterns.post('/submit', async (c) => {
  const redis = getRedis(c);

  const body = await c.req.json<{
    trigger: string;
    solution: string;
    context?: {
      languages?: string[];
      frameworks?: string[];
      error_types?: string[];
    };
  }>();

  // Validate input
  if (!body.trigger || !body.solution) {
    return c.json({ error: 'trigger and solution are required' }, 400);
  }

  if (body.trigger.length < 10 || body.solution.length < 10) {
    return c.json({ error: 'trigger and solution must be at least 10 characters' }, 400);
  }

  // Generate content hash for dedup
  const contentHash = generateContentHash(body.trigger, body.solution);

  // Check if pattern already exists by hash
  const existingByHash = await redis.hget('pop:patterns:hashes', contentHash);
  if (existingByHash) {
    return c.json({
      status: 'duplicate',
      existing_id: existingByHash,
      reason: 'exact_match',
    });
  }

  // Generate embedding for semantic dedup
  const combinedText = `${body.trigger}\n\n${body.solution}`;
  const { embedding, tokens } = await generateEmbedding(
    combinedText,
    c.env.VOYAGE_API_KEY
  );

  // Check for semantic duplicates
  const existingEmbeddings = await redis.hgetall('pop:patterns:embeddings') as Record<string, string> | null;

  if (existingEmbeddings && typeof existingEmbeddings === 'object') {
    for (const [id, embData] of Object.entries(existingEmbeddings)) {
      try {
        const existingEmb = typeof embData === 'string'
          ? JSON.parse(embData) as number[]
          : embData as unknown as number[];

        if (!Array.isArray(existingEmb)) continue;

        const similarity = cosineSimilarity(embedding, existingEmb);
        if (similarity > DUPLICATE_THRESHOLD) {
          return c.json({
            status: 'duplicate',
            existing_id: id,
            similarity,
            reason: 'semantic_match',
          });
        }
      } catch {
        // Skip invalid embeddings
      }
    }
  }

  // Generate pattern ID
  const patternId = `pat-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 6)}`;

  // Create pattern
  const pattern: Pattern = {
    id: patternId,
    trigger: body.trigger,
    solution: body.solution,
    context: {
      languages: body.context?.languages || [],
      frameworks: body.context?.frameworks || [],
      error_types: body.context?.error_types || [],
    },
    quality: {
      upvotes: 0,
      downvotes: 0,
      applications: 0,
      successes: 0,
    },
    created_at: new Date().toISOString(),
    content_hash: contentHash,
  };

  // Store pattern, embedding, and hash
  await Promise.all([
    redis.hset('pop:patterns:data', { [patternId]: JSON.stringify(pattern) }),
    redis.hset('pop:patterns:embeddings', { [patternId]: JSON.stringify(embedding) }),
    redis.hset('pop:patterns:hashes', { [contentHash]: patternId }),
  ]);

  // Track stats
  await redis.incr('pop:patterns:total_count');

  return c.json({
    status: 'created',
    pattern_id: patternId,
    tokens,
  });
});

// =============================================================================
// SEARCH PATTERNS
// =============================================================================

/**
 * Search for matching patterns.
 *
 * POST /patterns/search
 * Body: {
 *   query: string,          // Error/issue to search for
 *   context?: { languages, frameworks },
 *   limit?: number,
 *   threshold?: number
 * }
 */
patterns.post('/search', async (c) => {
  const redis = getRedis(c);

  const body = await c.req.json<{
    query: string;
    context?: {
      languages?: string[];
      frameworks?: string[];
    };
    limit?: number;
    threshold?: number;
  }>();

  const limit = Math.min(body.limit || 5, 20);
  const threshold = body.threshold || MIN_CONFIDENCE_THRESHOLD;

  // Generate query embedding
  const { embedding: queryEmbedding, tokens } = await generateEmbedding(
    body.query,
    c.env.VOYAGE_API_KEY,
    'query'
  );

  // Get all embeddings
  const [allEmbeddings, allPatterns] = await Promise.all([
    redis.hgetall('pop:patterns:embeddings') as Promise<Record<string, string> | null>,
    redis.hgetall('pop:patterns:data') as Promise<Record<string, string> | null>,
  ]);

  if (!allEmbeddings || !allPatterns) {
    return c.json({ results: [], tokens, message: 'No patterns in database' });
  }

  // Calculate similarities
  const results: Array<{
    id: string;
    trigger: string;
    solution: string;
    similarity: number;
    quality_score: number;
    context: Pattern['context'];
  }> = [];

  for (const [id, embData] of Object.entries(allEmbeddings)) {
    try {
      const emb = typeof embData === 'string'
        ? JSON.parse(embData) as number[]
        : embData as unknown as number[];

      if (!Array.isArray(emb)) continue;

      const similarity = cosineSimilarity(queryEmbedding, emb);
      if (similarity < threshold) continue;

      // Get pattern data
      const patternData = allPatterns[id];
      if (!patternData) continue;

      const pattern = typeof patternData === 'string'
        ? JSON.parse(patternData) as Pattern
        : patternData as Pattern;

      // Context filtering (boost matching contexts)
      let contextBoost = 0;
      if (body.context?.languages?.length) {
        const langMatch = pattern.context.languages.some(l =>
          body.context?.languages?.includes(l)
        );
        if (langMatch) contextBoost += 0.05;
      }
      if (body.context?.frameworks?.length) {
        const fwMatch = pattern.context.frameworks.some(f =>
          body.context?.frameworks?.includes(f)
        );
        if (fwMatch) contextBoost += 0.05;
      }

      const qualityScore = calculateQualityScore(pattern.quality);
      const finalScore = similarity + contextBoost;

      results.push({
        id: pattern.id,
        trigger: pattern.trigger,
        solution: pattern.solution,
        similarity: finalScore,
        quality_score: qualityScore,
        context: pattern.context,
      });
    } catch {
      // Skip invalid entries
    }
  }

  // Sort by similarity * quality, then take top N
  results.sort((a, b) => {
    const scoreA = a.similarity * (0.5 + a.quality_score * 0.5);
    const scoreB = b.similarity * (0.5 + b.quality_score * 0.5);
    return scoreB - scoreA;
  });

  return c.json({
    results: results.slice(0, limit),
    tokens,
    total_patterns: Object.keys(allPatterns).length,
  });
});

// =============================================================================
// FEEDBACK
// =============================================================================

/**
 * Provide feedback on a pattern.
 *
 * POST /patterns/:id/feedback
 * Body: { type: 'upvote' | 'downvote' | 'applied' | 'success' }
 */
patterns.post('/:id/feedback', async (c) => {
  const redis = getRedis(c);

  const patternId = c.req.param('id');
  const body = await c.req.json<{
    type: 'upvote' | 'downvote' | 'applied' | 'success';
  }>();

  // Get pattern
  const patternData = await redis.hget('pop:patterns:data', patternId);
  if (!patternData) {
    return c.json({ error: 'Pattern not found' }, 404);
  }

  const pattern = typeof patternData === 'string'
    ? JSON.parse(patternData) as Pattern
    : patternData as Pattern;

  // Update quality metrics
  switch (body.type) {
    case 'upvote':
      pattern.quality.upvotes++;
      break;
    case 'downvote':
      pattern.quality.downvotes++;
      break;
    case 'applied':
      pattern.quality.applications++;
      break;
    case 'success':
      pattern.quality.successes++;
      break;
  }

  // Save updated pattern
  await redis.hset('pop:patterns:data', {
    [patternId]: JSON.stringify(pattern),
  });

  return c.json({
    status: 'ok',
    quality_score: calculateQualityScore(pattern.quality),
  });
});

// =============================================================================
// STATS
// =============================================================================

/**
 * Get collective learning stats.
 *
 * GET /patterns/stats
 */
patterns.get('/stats', async (c) => {
  const redis = getRedis(c);

  const [totalCount, allPatterns] = await Promise.all([
    redis.get('pop:patterns:total_count'),
    redis.hgetall('pop:patterns:data') as Promise<Record<string, string> | null>,
  ]);

  // Calculate aggregate stats
  let totalUpvotes = 0;
  let totalApplications = 0;
  let totalSuccesses = 0;
  const languages: Record<string, number> = {};
  const frameworks: Record<string, number> = {};

  if (allPatterns) {
    for (const patternData of Object.values(allPatterns)) {
      try {
        const pattern = typeof patternData === 'string'
          ? JSON.parse(patternData) as Pattern
          : patternData as Pattern;

        totalUpvotes += pattern.quality.upvotes;
        totalApplications += pattern.quality.applications;
        totalSuccesses += pattern.quality.successes;

        for (const lang of pattern.context.languages) {
          languages[lang] = (languages[lang] || 0) + 1;
        }
        for (const fw of pattern.context.frameworks) {
          frameworks[fw] = (frameworks[fw] || 0) + 1;
        }
      } catch {
        // Skip invalid
      }
    }
  }

  return c.json({
    total_patterns: totalCount || 0,
    total_upvotes: totalUpvotes,
    total_applications: totalApplications,
    success_rate: totalApplications > 0
      ? (totalSuccesses / totalApplications * 100).toFixed(1) + '%'
      : 'N/A',
    top_languages: Object.entries(languages)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([lang, count]) => ({ language: lang, patterns: count })),
    top_frameworks: Object.entries(frameworks)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([fw, count]) => ({ framework: fw, patterns: count })),
  });
});

// =============================================================================
// TOP PATTERNS
// =============================================================================

/**
 * Get top patterns by quality score.
 *
 * GET /patterns/top?limit=10
 */
patterns.get('/top', async (c) => {
  const redis = getRedis(c);

  const limit = Math.min(parseInt(c.req.query('limit') || '10'), 100);

  const allPatterns = await redis.hgetall('pop:patterns:data') as Record<string, string> | null;

  if (!allPatterns) {
    return c.json({ patterns: [] });
  }

  const patternsWithScores: Array<{
    id: string;
    trigger: string;
    solution: string;
    quality_score: number;
    applications: number;
    context: Pattern['context'];
  }> = [];

  for (const patternData of Object.values(allPatterns)) {
    try {
      const pattern = typeof patternData === 'string'
        ? JSON.parse(patternData) as Pattern
        : patternData as Pattern;

      patternsWithScores.push({
        id: pattern.id,
        trigger: pattern.trigger,
        solution: pattern.solution,
        quality_score: calculateQualityScore(pattern.quality),
        applications: pattern.quality.applications,
        context: pattern.context,
      });
    } catch {
      // Skip invalid
    }
  }

  // Sort by quality score * applications (to surface proven patterns)
  patternsWithScores.sort((a, b) => {
    const scoreA = a.quality_score * Math.log(a.applications + 1);
    const scoreB = b.quality_score * Math.log(b.applications + 1);
    return scoreB - scoreA;
  });

  return c.json({
    patterns: patternsWithScores.slice(0, limit),
  });
});

export default patterns;
