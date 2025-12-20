import { getRedis } from '../services/redis';
import type { Redis } from '@upstash/redis';
/**
 * Rate Limiting Middleware
 *
 * Part of Issue #69 (API Gateway & Authentication)
 */

import { Context, Next } from 'hono';
import { Ratelimit } from '@upstash/ratelimit';
import type { Env, Variables, Tier, RateLimitResult } from '../types';

/**
 * Rate limits per tier (requests per minute).
 */
const RATE_LIMITS: Record<Tier, number> = {
  free: 100,
  pro: 1000,
  team: 10000,
};

/**
 * Rate limiting middleware using Upstash Ratelimit.
 */
export async function rateLimitMiddleware(
  c: Context<{ Bindings: Env; Variables: Variables }>,
  next: Next
) {
  const apiKeyData = c.get('apiKey');

  if (!apiKeyData) {
    // No API key means auth middleware didn't run - skip rate limiting
    return next();
  }

  const redis = getRedis(c);

  const limit = RATE_LIMITS[apiKeyData.tier] || RATE_LIMITS.free;

  const ratelimit = new Ratelimit({
    redis,
    limiter: Ratelimit.slidingWindow(limit, '1 m'),
    analytics: true,
  });

  const { success, remaining, reset } = await ratelimit.limit(apiKeyData.id);

  // Add rate limit headers
  c.header('X-RateLimit-Limit', limit.toString());
  c.header('X-RateLimit-Remaining', remaining.toString());
  c.header('X-RateLimit-Reset', reset.toString());

  if (!success) {
    return c.json(
      {
        error: 'Rate limit exceeded',
        remaining: 0,
        reset,
      },
      429
    );
  }

  await next();
}

/**
 * Check rate limit without consuming a request.
 */
export async function checkRateLimit(
  redis: Redis,
  apiKeyId: string,
  tier: Tier
): Promise<RateLimitResult> {
  const limit = RATE_LIMITS[tier] || RATE_LIMITS.free;
  const key = `ratelimit:${apiKeyId}`;

  const current = await redis.get<number>(key);
  const used = current || 0;
  const ttl = await redis.ttl(key);

  return {
    exceeded: used >= limit,
    remaining: Math.max(0, limit - used),
    reset: ttl > 0 ? ttl : 60,
  };
}
