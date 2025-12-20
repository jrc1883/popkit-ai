import { getRedis } from '../services/redis';
import type { Redis } from '@upstash/redis';
/**
 * Usage Tracking Routes
 *
 * Part of Issue #69 (API Gateway & Authentication)
 * Extended for Issue #138 (Premium Feature Usage Tracking)
 */

import { Hono } from 'hono';
import type { Env, Variables, UsageData } from '../types';

const usage = new Hono<{ Bindings: Env; Variables: Variables }>();

// Rate limits per tier per feature category
const RATE_LIMITS: Record<string, Record<string, { daily: number; monthly: number }>> = {
  free: {
    default: { daily: 100, monthly: 3000 },
    'pop-embed-project': { daily: 10, monthly: 100 },
    'pop-pattern-share': { daily: 20, monthly: 500 },
  },
  pro: {
    default: { daily: -1, monthly: -1 }, // -1 = unlimited
    'pop-embed-project': { daily: 1000, monthly: 10000 },
    'pop-pattern-share': { daily: -1, monthly: -1 },
  },
  team: {
    default: { daily: -1, monthly: -1 },
    'pop-embed-project': { daily: -1, monthly: -1 },
    'pop-pattern-share': { daily: -1, monthly: -1 },
  },
};

/**
 * Get current usage statistics.
 *
 * GET /usage
 */
usage.get('/', async (c) => {
  const apiKey = c.get('apiKey');
  if (!apiKey) {
    return c.json({ error: 'Unauthorized' }, 401);
  }

  const redis = getRedis(c);

  const today = new Date().toISOString().split('T')[0];
  const key = `usage:${apiKey.id}:${today}`;

  const data = await redis.hgetall<UsageData>(key);

  const limits = {
    free: { commands: 100, bandwidth: 10 * 1024 * 1024 }, // 10MB
    pro: { commands: 1000, bandwidth: 100 * 1024 * 1024 }, // 100MB
    team: { commands: 10000, bandwidth: 1024 * 1024 * 1024 }, // 1GB
  };

  const tierLimits = limits[apiKey.tier] || limits.free;

  return c.json({
    tier: apiKey.tier,
    period: today,
    usage: {
      commands: data?.commandsToday || 0,
      bytesSent: data?.bytesSent || 0,
      bytesReceived: data?.bytesReceived || 0,
    },
    limits: tierLimits,
    remaining: {
      commands: tierLimits.commands - (data?.commandsToday || 0),
      bandwidth:
        tierLimits.bandwidth - ((data?.bytesSent || 0) + (data?.bytesReceived || 0)),
    },
  });
});

/**
 * Track usage (internal, called by middleware).
 */
export async function trackUsage(
  redis: Redis,
  apiKeyId: string,
  bytesSent: number,
  bytesReceived: number
): Promise<void> {
  const today = new Date().toISOString().split('T')[0];
  const key = `usage:${apiKeyId}:${today}`;

  await redis.hincrby(key, 'commandsToday', 1);
  await redis.hincrby(key, 'bytesSent', bytesSent);
  await redis.hincrby(key, 'bytesReceived', bytesReceived);

  // Expire after 90 days for historical data
  await redis.expire(key, 90 * 24 * 60 * 60);
}

/**
 * Get historical usage.
 *
 * GET /usage/history?days=30
 */
usage.get('/history', async (c) => {
  const apiKey = c.get('apiKey');
  if (!apiKey) {
    return c.json({ error: 'Unauthorized' }, 401);
  }

  const days = parseInt(c.req.query('days') || '30', 10);

  const redis = getRedis(c);

  const history: Array<{
    date: string;
    commands: number;
    bytesSent: number;
    bytesReceived: number;
  }> = [];

  const now = new Date();
  for (let i = 0; i < days; i++) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    const dateStr = date.toISOString().split('T')[0];
    const key = `usage:${apiKey.id}:${dateStr}`;

    const data = await redis.hgetall<UsageData>(key);

    history.push({
      date: dateStr,
      commands: data?.commandsToday || 0,
      bytesSent: data?.bytesSent || 0,
      bytesReceived: data?.bytesReceived || 0,
    });
  }

  return c.json({ history });
});

/**
 * Track feature usage (Issue #138).
 *
 * POST /usage/track
 * Body: { feature, tier, timestamp, project_id, success }
 */
usage.post('/track', async (c) => {
  const apiKey = c.get('apiKey');
  if (!apiKey) {
    return c.json({ error: 'Unauthorized' }, 401);
  }

  const body = await c.req.json<{
    feature: string;
    tier: string;
    timestamp: string;
    project_id: string;
    success: boolean;
  }>();

  const { feature, project_id, success } = body;

  const redis = getRedis(c);

  const today = new Date().toISOString().split('T')[0];
  const month = today.substring(0, 7); // YYYY-MM

  // Track daily feature usage
  const dailyKey = `feature:${apiKey.id}:${feature}:${today}`;
  await redis.incr(dailyKey);
  await redis.expire(dailyKey, 30 * 24 * 60 * 60); // 30 day TTL

  // Track monthly feature usage
  const monthlyKey = `feature:${apiKey.id}:${feature}:${month}`;
  await redis.incr(monthlyKey);
  await redis.expire(monthlyKey, 90 * 24 * 60 * 60); // 90 day TTL

  // Track total feature usage (for analytics)
  const totalKey = `feature:total:${feature}`;
  await redis.incr(totalKey);

  // Track per-project usage (privacy: project_id is already hashed)
  if (project_id) {
    const projectKey = `project:${project_id}:features:${today}`;
    await redis.hincrby(projectKey, feature, 1);
    await redis.expire(projectKey, 30 * 24 * 60 * 60);
  }

  // Track success/failure rate
  if (success) {
    await redis.incr(`feature:${apiKey.id}:${feature}:success`);
  } else {
    await redis.incr(`feature:${apiKey.id}:${feature}:failure`);
  }

  return c.json({ status: 'tracked' });
});

/**
 * Get usage summary for account (Issue #138).
 *
 * GET /usage/summary
 */
usage.get('/summary', async (c) => {
  const apiKey = c.get('apiKey');
  if (!apiKey) {
    return c.json({ error: 'Unauthorized' }, 401);
  }

  const redis = getRedis(c);

  const today = new Date().toISOString().split('T')[0];
  const month = today.substring(0, 7);

  // Get all feature usage for today
  const featurePattern = `feature:${apiKey.id}:*:${today}`;
  const keys = await redis.keys(featurePattern);

  const features: Record<string, { today: number; month: number }> = {};

  for (const key of keys) {
    const parts = key.split(':');
    const feature = parts[2];
    const dailyCount = (await redis.get<number>(key)) || 0;

    const monthlyKey = `feature:${apiKey.id}:${feature}:${month}`;
    const monthlyCount = (await redis.get<number>(monthlyKey)) || 0;

    features[feature] = {
      today: dailyCount,
      month: monthlyCount,
    };
  }

  // Get general API usage
  const usageKey = `usage:${apiKey.id}:${today}`;
  const usageData = await redis.hgetall<UsageData>(usageKey);

  return c.json({
    tier: apiKey.tier,
    period: {
      today,
      month,
    },
    api: {
      commands_today: usageData?.commandsToday || 0,
      bytes_sent: usageData?.bytesSent || 0,
      bytes_received: usageData?.bytesReceived || 0,
    },
    features,
    limits: RATE_LIMITS[apiKey.tier] || RATE_LIMITS.free,
  });
});

/**
 * Check rate limits for a feature (Issue #138).
 *
 * GET /usage/limits?feature=<feature_name>
 */
usage.get('/limits', async (c) => {
  const apiKey = c.get('apiKey');
  if (!apiKey) {
    return c.json({ error: 'Unauthorized' }, 401);
  }

  const feature = c.req.query('feature') || 'default';

  const redis = getRedis(c);

  const today = new Date().toISOString().split('T')[0];
  const month = today.substring(0, 7);

  // Get current usage
  const dailyKey = `feature:${apiKey.id}:${feature}:${today}`;
  const monthlyKey = `feature:${apiKey.id}:${feature}:${month}`;

  const currentDaily = (await redis.get<number>(dailyKey)) || 0;
  const currentMonthly = (await redis.get<number>(monthlyKey)) || 0;

  // Get limits for this tier and feature
  const tierLimits = RATE_LIMITS[apiKey.tier] || RATE_LIMITS.free;
  const featureLimits = tierLimits[feature] || tierLimits.default;

  // Calculate reset times
  const now = new Date();
  const endOfDay = new Date(now);
  endOfDay.setUTCHours(23, 59, 59, 999);

  const endOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59, 999);

  // Check if allowed
  const dailyAllowed = featureLimits.daily === -1 || currentDaily < featureLimits.daily;
  const monthlyAllowed = featureLimits.monthly === -1 || currentMonthly < featureLimits.monthly;
  const allowed = dailyAllowed && monthlyAllowed;

  const dailyRemaining =
    featureLimits.daily === -1 ? -1 : Math.max(0, featureLimits.daily - currentDaily);
  const monthlyRemaining =
    featureLimits.monthly === -1 ? -1 : Math.max(0, featureLimits.monthly - currentMonthly);

  // Set rate limit headers (Issue #139)
  c.header('X-RateLimit-Limit', String(featureLimits.daily));
  c.header('X-RateLimit-Remaining', String(dailyRemaining));
  c.header('X-RateLimit-Reset', endOfDay.toISOString());
  c.header('X-RateLimit-Feature', feature);
  c.header('X-RateLimit-Tier', apiKey.tier);

  if (!allowed) {
    c.status(429);
  }

  return c.json({
    allowed,
    tier: apiKey.tier,
    feature,
    current: {
      daily: currentDaily,
      monthly: currentMonthly,
    },
    limit: {
      daily: featureLimits.daily,
      monthly: featureLimits.monthly,
    },
    remaining: {
      daily: dailyRemaining,
      monthly: monthlyRemaining,
    },
    reset_at: {
      daily: endOfDay.toISOString(),
      monthly: endOfMonth.toISOString(),
    },
  });
});

export default usage;
