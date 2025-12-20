import { getRedis } from '../services/redis';
import type { Redis } from '@upstash/redis';
/**
 * API Key Authentication Middleware
 *
 * Part of Issue #69 (API Gateway & Authentication)
 */

import { Context, Next } from 'hono';
import type { Env, Variables, ApiKeyData } from '../types';

/**
 * Validate API key from Authorization header.
 *
 * Expected format: Bearer pk_live_xxxxx or Bearer pk_test_xxxxx
 */
export async function authMiddleware(
  c: Context<{ Bindings: Env; Variables: Variables }>,
  next: Next
) {
  const authHeader = c.req.header('Authorization');

  if (!authHeader) {
    return c.json({ error: 'Authorization header required' }, 401);
  }

  const match = authHeader.match(/^Bearer (pk_(live|test)_[a-zA-Z0-9]+)$/);
  if (!match) {
    return c.json({ error: 'Invalid API key format' }, 401);
  }

  const apiKey = match[1];

  // Get Redis client
  const redis = getRedis(c);

  // Look up API key
  const keyData = await redis.hget<ApiKeyData>('popkit:keys', apiKey);

  if (!keyData) {
    return c.json({ error: 'Invalid API key' }, 401);
  }

  // Update last used timestamp
  await redis.hset('popkit:keys', {
    [apiKey]: JSON.stringify({
      ...keyData,
      lastUsedAt: new Date().toISOString(),
    }),
  });

  // Attach key data to context
  c.set('apiKey', keyData);

  await next();
}

/**
 * Create a new API key for a user.
 */
export async function createApiKey(
  redis: Redis,
  userId: string,
  name: string,
  tier: 'free' | 'pro' | 'team' = 'free'
): Promise<{ key: string; data: ApiKeyData }> {
  // Generate random key
  const randomPart = Array.from(crypto.getRandomValues(new Uint8Array(24)))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');

  const key = `pk_live_${randomPart}`;

  const data: ApiKeyData = {
    id: crypto.randomUUID(),
    userId,
    tier,
    name,
    createdAt: new Date().toISOString(),
  };

  // Store key (the key itself is used as the lookup)
  await redis.hset('popkit:keys', { [key]: JSON.stringify(data) });

  // Also store in user's key list
  await redis.sadd(`popkit:user:${userId}:keys`, key);

  return { key, data };
}

/**
 * Revoke an API key.
 */
export async function revokeApiKey(
  redis: Redis,
  apiKey: string,
  userId: string
): Promise<boolean> {
  const keyData = await redis.hget<ApiKeyData>('popkit:keys', apiKey);

  if (!keyData || keyData.userId !== userId) {
    return false;
  }

  await redis.hdel('popkit:keys', apiKey);
  await redis.srem(`popkit:user:${userId}:keys`, apiKey);

  return true;
}
