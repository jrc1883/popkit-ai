import { getRedis } from '../services/redis';
/**
 * Health Check Routes
 *
 * Part of Issue #69 (API Gateway & Authentication)
 */

import { Hono } from 'hono';
import type { Env, Variables } from '../types';

const health = new Hono<{ Bindings: Env; Variables: Variables }>();

/**
 * Basic health check - no auth required.
 */
health.get('/', async (c) => {
  const apiKeyData = c.get('apiKey');

  const response: Record<string, unknown> = {
    status: 'ok',
    service: 'popkit-cloud',
    version: '1.0.0-beta.1',
    timestamp: new Date().toISOString(),
  };

  // If authenticated, include user info
  if (apiKeyData) {
    response.user = {
      id: apiKeyData.userId,
      tier: apiKeyData.tier,
    };
  }

  return c.json(response);
});

/**
 * Detailed health check - checks Redis connectivity.
 */
health.get('/detailed', async (c) => {
  const checks: Record<string, { status: string; latency?: number; error?: string }> = {};

  // Check Redis
  try {
    const redis = getRedis(c);

    const start = Date.now();
    await redis.ping();
    const latency = Date.now() - start;

    checks.redis = { status: 'ok', latency };
  } catch (e) {
    checks.redis = {
      status: 'error',
      error: e instanceof Error ? e.message : 'Unknown error',
    };
  }

  const allOk = Object.values(checks).every((check) => check.status === 'ok');

  return c.json({
    status: allOk ? 'ok' : 'degraded',
    checks,
    timestamp: new Date().toISOString(),
  });
});

export default health;
