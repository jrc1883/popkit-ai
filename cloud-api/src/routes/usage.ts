/**
 * Usage Tracking Routes
 *
 * Part of Issue #69 (API Gateway & Authentication)
 */

import { Hono } from 'hono';
import { Redis } from '@upstash/redis';
import type { Env, Variables, UsageData } from '../types';

const usage = new Hono<{ Bindings: Env; Variables: Variables }>();

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

  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

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

  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

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

export default usage;
