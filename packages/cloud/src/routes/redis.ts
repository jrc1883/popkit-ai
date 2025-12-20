/**
 * Redis Proxy Routes
 *
 * Part of Issue #69 (API Gateway & Authentication)
 *
 * Proxies Redis commands from the PopKit plugin to Upstash Redis.
 * Commands are scoped to the user's namespace for data isolation.
 */

import { Hono } from 'hono';
import { getRedis as getRedisClient } from '../services/redis';
import type { Env, Variables } from '../types';

const redis = new Hono<{ Bindings: Env; Variables: Variables }>();



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

// =============================================================================
// STATE MANAGEMENT
// =============================================================================

/**
 * Push agent state to Redis.
 *
 * POST /redis/state
 * Body: { agent_id: string, state: object, ttl?: number }
 */
redis.post('/state', async (c) => {
  const client = getRedisClient(c);
  const prefix = getUserPrefix(c);
  const body = await c.req.json<{
    agent_id: string;
    state: Record<string, unknown>;
    ttl?: number;
  }>();

  const key = `${prefix}pop:state:${body.agent_id}`;
  const ttl = body.ttl || 600; // 10 min default

  // Store state as hash
  await client.hset(key, body.state);
  await client.expire(key, ttl);

  return c.json({ success: true });
});

/**
 * Get agent state from Redis.
 *
 * GET /redis/state/:agent_id
 */
redis.get('/state/:agent_id', async (c) => {
  const client = getRedisClient(c);
  const prefix = getUserPrefix(c);
  const agentId = c.req.param('agent_id');

  const key = `${prefix}pop:state:${agentId}`;
  const state = await client.hgetall(key);

  return c.json({ state: state || {} });
});

// =============================================================================
// INSIGHTS
// =============================================================================

/**
 * Push an insight to Redis.
 *
 * POST /redis/insights
 * Body: { insight: object }
 */
redis.post('/insights', async (c) => {
  const client = getRedisClient(c);
  const prefix = getUserPrefix(c);
  const body = await c.req.json<{ insight: Record<string, unknown> }>();

  const key = `${prefix}pop:insights`;

  // Push to list, keep last 50
  await client.lpush(key, JSON.stringify(body.insight));
  await client.ltrim(key, 0, 49);

  return c.json({ success: true });
});

/**
 * Search insights by tags.
 *
 * POST /redis/insights/search
 * Body: { tags: string[], exclude_agent: string, limit?: number }
 */
redis.post('/insights/search', async (c) => {
  const client = getRedisClient(c);
  const prefix = getUserPrefix(c);
  const body = await c.req.json<{
    tags: string[];
    exclude_agent: string;
    limit?: number;
  }>();

  const key = `${prefix}pop:insights`;
  const limit = body.limit || 3;

  // Get all insights
  const rawInsights = await client.lrange(key, 0, -1);

  // Filter by tags and exclude agent
  const insights = rawInsights
    .map((raw) => {
      try {
        return JSON.parse(raw as string);
      } catch {
        return null;
      }
    })
    .filter((insight) => {
      if (!insight) return false;
      if (insight.from_agent === body.exclude_agent) return false;

      const insightTags = insight.relevance_tags || [];
      return body.tags.some((tag) => insightTags.includes(tag));
    })
    .slice(0, limit);

  return c.json({ insights });
});

// =============================================================================
// MESSAGES
// =============================================================================

/**
 * Get messages for an agent.
 *
 * GET /redis/messages/:agent_id
 */
redis.get('/messages/:agent_id', async (c) => {
  const client = getRedisClient(c);
  const prefix = getUserPrefix(c);
  const agentId = c.req.param('agent_id');

  const key = `${prefix}pop:messages:${agentId}`;

  // Get and clear messages (atomic pop)
  const messages: unknown[] = [];
  let msg = await client.lpop(key);
  while (msg) {
    try {
      messages.push(JSON.parse(msg as string));
    } catch {
      messages.push(msg);
    }
    msg = await client.lpop(key);
  }

  return c.json({ messages });
});

// =============================================================================
// OBJECTIVE
// =============================================================================

/**
 * Get current objective.
 *
 * GET /redis/objective
 */
redis.get('/objective', async (c) => {
  const client = getRedisClient(c);
  const prefix = getUserPrefix(c);

  const key = `${prefix}pop:objective`;
  const objective = await client.get(key);

  if (!objective) {
    return c.json({ objective: null });
  }

  try {
    return c.json({ objective: JSON.parse(objective as string) });
  } catch {
    return c.json({ objective });
  }
});

/**
 * Set current objective.
 *
 * POST /redis/objective
 * Body: { objective: object, ttl?: number }
 */
redis.post('/objective', async (c) => {
  const client = getRedisClient(c);
  const prefix = getUserPrefix(c);
  const body = await c.req.json<{
    objective: Record<string, unknown>;
    ttl?: number;
  }>();

  const key = `${prefix}pop:objective`;
  const ttl = body.ttl || 3600; // 1 hour default

  await client.setex(key, ttl, JSON.stringify(body.objective));

  return c.json({ success: true });
});

// =============================================================================
// PATTERNS
// =============================================================================

/**
 * Search patterns by context.
 *
 * POST /redis/patterns/search
 * Body: { context: string }
 */
redis.post('/patterns/search', async (c) => {
  const client = getRedisClient(c);
  const prefix = getUserPrefix(c);
  const body = await c.req.json<{ context: string }>();

  const key = `${prefix}pop:patterns`;

  // Get all patterns and filter by context
  const rawPatterns = await client.lrange(key, 0, -1);

  const patterns = rawPatterns
    .map((raw) => {
      try {
        return JSON.parse(raw as string);
      } catch {
        return null;
      }
    })
    .filter((pattern) => {
      if (!pattern) return false;
      const patternContext = pattern.context || '';
      return patternContext.includes(body.context) || body.context.includes(patternContext);
    });

  return c.json({ patterns });
});

// =============================================================================
// PUB/SUB (HTTP polling-based)
// =============================================================================

/**
 * Publish to a channel.
 *
 * POST /redis/publish
 * Body: { channel: string, message: object }
 */
redis.post('/publish', async (c) => {
  const client = getRedisClient(c);
  const prefix = getUserPrefix(c);
  const body = await c.req.json<{
    channel: string;
    message: Record<string, unknown>;
  }>();

  // Store in a list for the channel (since Upstash REST doesn't support true pub/sub)
  const key = `${prefix}pop:channel:${body.channel}`;

  await client.lpush(
    key,
    JSON.stringify({
      ...body.message,
      timestamp: new Date().toISOString(),
    })
  );

  // Keep last 100 messages per channel
  await client.ltrim(key, 0, 99);

  // Set TTL of 1 hour
  await client.expire(key, 3600);

  return c.json({ success: true });
});

/**
 * Subscribe to channels (polling-based).
 *
 * POST /redis/subscribe
 * Body: { channels: string[], since?: string }
 */
redis.post('/subscribe', async (c) => {
  const client = getRedisClient(c);
  const prefix = getUserPrefix(c);
  const body = await c.req.json<{
    channels: string[];
    since?: string;
  }>();

  const sinceTime = body.since ? new Date(body.since).getTime() : 0;
  const messages: Array<{ channel: string; message: unknown }> = [];

  for (const channel of body.channels) {
    const key = `${prefix}pop:channel:${channel}`;
    const rawMessages = await client.lrange(key, 0, 49);

    for (const raw of rawMessages) {
      try {
        const msg = JSON.parse(raw as string);
        const msgTime = new Date(msg.timestamp).getTime();

        if (msgTime > sinceTime) {
          messages.push({ channel, message: msg });
        }
      } catch {
        // Skip invalid messages
      }
    }
  }

  // Sort by timestamp
  messages.sort((a, b) => {
    const aTime = new Date((a.message as { timestamp: string }).timestamp).getTime();
    const bTime = new Date((b.message as { timestamp: string }).timestamp).getTime();
    return aTime - bTime;
  });

  return c.json({
    messages,
    timestamp: new Date().toISOString(),
  });
});

export default redis;
