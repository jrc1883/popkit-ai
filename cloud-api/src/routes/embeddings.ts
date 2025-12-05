/**
 * Embeddings Routes
 *
 * Part of Issue #70 (Embedding-Enhanced Check-ins)
 *
 * Server-side embedding generation using Voyage AI.
 * Users don't need their own Voyage API key.
 */

import { Hono } from 'hono';
import { Redis } from '@upstash/redis';
import type { Env, Variables } from '../types';

// Extend Env to include Voyage API key
interface EmbeddingsEnv extends Env {
  VOYAGE_API_KEY: string;
}

const embeddings = new Hono<{ Bindings: EmbeddingsEnv; Variables: Variables }>();

// Voyage API configuration
const VOYAGE_API_URL = 'https://api.voyageai.com/v1/embeddings';
const VOYAGE_MODEL = 'voyage-3-lite'; // Cheaper model for insights (512 dims)
const EMBEDDING_DIMENSIONS = 512;

// Cost tracking (voyage-3-lite: $0.00002 per 1K tokens)
const COST_PER_1K_TOKENS = 0.00002;

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
 * Get user-scoped key prefix.
 */
function getUserPrefix(c: { get: (key: string) => unknown }): string {
  const apiKey = c.get('apiKey') as { userId: string } | undefined;
  if (!apiKey) {
    throw new Error('No API key in context');
  }
  return `user:${apiKey.userId}:`;
}

/**
 * Generate embedding via Voyage AI.
 */
async function generateEmbedding(
  text: string,
  apiKey: string
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
      input_type: 'document',
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
 * Generate embedding for query (different input_type).
 */
async function generateQueryEmbedding(
  text: string,
  apiKey: string
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
      input_type: 'query',
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

// =============================================================================
// INSIGHT EMBEDDING
// =============================================================================

/**
 * Embed an insight and store it.
 *
 * POST /embeddings/insight
 * Body: { insight_id: string, content: string, summary?: string }
 *
 * Returns: { embedding: number[], tokens: number, cost: number, duplicate?: { id: string, similarity: number } }
 */
embeddings.post('/insight', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const prefix = getUserPrefix(c);
  const body = await c.req.json<{
    insight_id: string;
    content: string;
    summary?: string;
  }>();

  // Generate embedding
  const { embedding, tokens } = await generateEmbedding(
    body.content,
    c.env.VOYAGE_API_KEY
  );

  const cost = (tokens / 1000) * COST_PER_1K_TOKENS;

  // Check for duplicates (similarity > 0.90)
  const existingEmbeddings = await redis.hgetall(
    `${prefix}pop:insight_embeddings`
  ) as Record<string, string> | null;

  let duplicate: { id: string; similarity: number } | undefined;

  if (existingEmbeddings && typeof existingEmbeddings === 'object') {
    for (const [id, embeddingData] of Object.entries(existingEmbeddings)) {
      try {
        // Handle both string JSON and already-parsed arrays
        const existingEmbedding = typeof embeddingData === 'string'
          ? JSON.parse(embeddingData) as number[]
          : embeddingData as unknown as number[];

        if (!Array.isArray(existingEmbedding)) continue;

        const similarity = cosineSimilarity(embedding, existingEmbedding);

        if (similarity > 0.90) {
          duplicate = { id, similarity };
          break;
        }
      } catch {
        // Skip invalid embeddings
      }
    }
  }

  // If duplicate found, return without storing
  if (duplicate) {
    return c.json({
      status: 'duplicate',
      duplicate,
      tokens,
      cost,
    });
  }

  // Store embedding
  await redis.hset(`${prefix}pop:insight_embeddings`, {
    [body.insight_id]: JSON.stringify(embedding),
  });

  // Store summary for human readability
  if (body.summary) {
    await redis.hset(`${prefix}pop:insight_summaries`, {
      [body.insight_id]: body.summary,
    });
  }

  // Track usage for billing
  const today = new Date().toISOString().split('T')[0];
  await redis.hincrby(`${prefix}pop:embedding_usage:${today}`, 'tokens', tokens);
  await redis.hincrby(`${prefix}pop:embedding_usage:${today}`, 'requests', 1);

  return c.json({
    status: 'created',
    insight_id: body.insight_id,
    dimensions: EMBEDDING_DIMENSIONS,
    tokens,
    cost,
  });
});

// =============================================================================
// SEMANTIC SEARCH
// =============================================================================

/**
 * Search for similar insights.
 *
 * POST /embeddings/search
 * Body: { query: string, limit?: number, threshold?: number, exclude_ids?: string[] }
 *
 * Returns: { results: Array<{ id: string, summary: string, similarity: number }>, tokens: number }
 */
embeddings.post('/search', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const prefix = getUserPrefix(c);
  const body = await c.req.json<{
    query: string;
    limit?: number;
    threshold?: number;
    exclude_ids?: string[];
  }>();

  const limit = body.limit || 5;
  const threshold = body.threshold || 0.5;
  const excludeIds = new Set(body.exclude_ids || []);

  // Generate query embedding
  const { embedding: queryEmbedding, tokens } = await generateQueryEmbedding(
    body.query,
    c.env.VOYAGE_API_KEY
  );

  // Get all embeddings
  const existingEmbeddings = await redis.hgetall(
    `${prefix}pop:insight_embeddings`
  ) as Record<string, string> | null;

  const summaries = await redis.hgetall(
    `${prefix}pop:insight_summaries`
  ) as Record<string, string> | null;

  if (!existingEmbeddings || typeof existingEmbeddings !== 'object') {
    return c.json({ results: [], tokens });
  }

  // Calculate similarities
  const results: Array<{ id: string; summary: string; similarity: number }> = [];

  for (const [id, embeddingData] of Object.entries(existingEmbeddings)) {
    if (excludeIds.has(id)) continue;

    try {
      // Handle both string JSON and already-parsed arrays
      const embedding = typeof embeddingData === 'string'
        ? JSON.parse(embeddingData) as number[]
        : embeddingData as unknown as number[];

      if (!Array.isArray(embedding)) continue;

      const similarity = cosineSimilarity(queryEmbedding, embedding);

      if (similarity >= threshold) {
        results.push({
          id,
          summary: summaries?.[id] || id,
          similarity,
        });
      }
    } catch {
      // Skip invalid embeddings
    }
  }

  // Sort by similarity and limit
  results.sort((a, b) => b.similarity - a.similarity);
  const topResults = results.slice(0, limit);

  return c.json({
    results: topResults,
    tokens,
    cost: (tokens / 1000) * COST_PER_1K_TOKENS,
  });
});

// =============================================================================
// BATCH EMBEDDING
// =============================================================================

/**
 * Embed multiple insights in batch.
 *
 * POST /embeddings/batch
 * Body: { insights: Array<{ id: string, content: string, summary?: string }> }
 *
 * Returns: { created: number, duplicates: number, tokens: number, cost: number }
 */
embeddings.post('/batch', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const prefix = getUserPrefix(c);
  const body = await c.req.json<{
    insights: Array<{ id: string; content: string; summary?: string }>;
  }>();

  // Limit batch size
  const insights = body.insights.slice(0, 20);

  let created = 0;
  let duplicates = 0;
  let totalTokens = 0;

  // Get existing embeddings for dedup
  const existingEmbeddings = await redis.hgetall<Record<string, string>>(
    `${prefix}pop:insight_embeddings`
  );

  const existingVectors: Array<{ id: string; embedding: number[] }> = [];
  if (existingEmbeddings) {
    for (const [id, embeddingJson] of Object.entries(existingEmbeddings)) {
      try {
        existingVectors.push({
          id,
          embedding: JSON.parse(embeddingJson) as number[],
        });
      } catch {
        // Skip invalid
      }
    }
  }

  // Process each insight
  for (const insight of insights) {
    try {
      const { embedding, tokens } = await generateEmbedding(
        insight.content,
        c.env.VOYAGE_API_KEY
      );
      totalTokens += tokens;

      // Check for duplicates
      let isDuplicate = false;
      for (const existing of existingVectors) {
        if (cosineSimilarity(embedding, existing.embedding) > 0.90) {
          isDuplicate = true;
          duplicates++;
          break;
        }
      }

      if (!isDuplicate) {
        // Store embedding
        await redis.hset(`${prefix}pop:insight_embeddings`, {
          [insight.id]: JSON.stringify(embedding),
        });

        if (insight.summary) {
          await redis.hset(`${prefix}pop:insight_summaries`, {
            [insight.id]: insight.summary,
          });
        }

        // Add to existing for next dedup check
        existingVectors.push({ id: insight.id, embedding });
        created++;
      }
    } catch (e) {
      // Continue on individual failures
      console.error(`Failed to embed ${insight.id}:`, e);
    }
  }

  // Track usage
  const today = new Date().toISOString().split('T')[0];
  await redis.hincrby(`${prefix}pop:embedding_usage:${today}`, 'tokens', totalTokens);
  await redis.hincrby(`${prefix}pop:embedding_usage:${today}`, 'requests', insights.length);

  return c.json({
    created,
    duplicates,
    tokens: totalTokens,
    cost: (totalTokens / 1000) * COST_PER_1K_TOKENS,
  });
});

// =============================================================================
// USAGE STATS
// =============================================================================

/**
 * Get embedding usage statistics.
 *
 * GET /embeddings/usage
 */
embeddings.get('/usage', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const prefix = getUserPrefix(c);
  const today = new Date().toISOString().split('T')[0];

  // Get today's usage
  const todayUsage = await redis.hgetall<{ tokens: string; requests: string }>(
    `${prefix}pop:embedding_usage:${today}`
  );

  // Get total insight count
  const insightCount = await redis.hlen(`${prefix}pop:insight_embeddings`);

  const tokens = parseInt(todayUsage?.tokens || '0', 10);
  const requests = parseInt(todayUsage?.requests || '0', 10);

  return c.json({
    today: {
      tokens,
      requests,
      cost: (tokens / 1000) * COST_PER_1K_TOKENS,
    },
    total_insights: insightCount,
    model: VOYAGE_MODEL,
    dimensions: EMBEDDING_DIMENSIONS,
  });
});

export default embeddings;
