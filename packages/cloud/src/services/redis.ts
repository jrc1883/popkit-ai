/**
 * Redis Client Factory
 *
 * Part of Epic #518, Issue #521 - DRY Refactoring
 * Eliminates 70+ duplicate Redis instantiations across route handlers.
 */

import { Redis } from '@upstash/redis';
import type { Context } from 'hono';
import type { Env } from '../types';

let redisInstance: Redis | null = null;

/**
 * Get a singleton Redis client instance.
 * 
 * @param c - Hono context with Bindings containing Redis credentials
 * @returns Redis client instance
 */
export function getRedis(c: Context<{ Bindings: Env }>): Redis {
  if (!redisInstance) {
    redisInstance = new Redis({
      url: c.env.UPSTASH_REDIS_REST_URL,
      token: c.env.UPSTASH_REDIS_REST_TOKEN,
    });
  }
  return redisInstance;
}
