/**
 * PopKit Cloud API Gateway
 *
 * Part of Issue #69 (API Gateway & Authentication)
 *
 * Main entry point for the Cloudflare Worker.
 * Provides Redis proxy and authentication for PopKit Cloud.
 */

import { Hono } from 'hono';
import { cors } from 'hono/cors';
import { logger } from 'hono/logger';
import type { Env, Variables } from './types';
import { authMiddleware } from './middleware/auth';
import { rateLimitMiddleware } from './middleware/ratelimit';
import healthRoutes from './routes/health';
import redisRoutes from './routes/redis';
import usageRoutes from './routes/usage';
import embeddingsRoutes from './routes/embeddings';

const app = new Hono<{ Bindings: Env; Variables: Variables }>();

// =============================================================================
// GLOBAL MIDDLEWARE
// =============================================================================

// CORS for plugin requests
app.use(
  '*',
  cors({
    origin: '*',
    allowMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowHeaders: ['Authorization', 'Content-Type', 'X-PopKit-Version'],
    exposeHeaders: ['X-RateLimit-Limit', 'X-RateLimit-Remaining', 'X-RateLimit-Reset'],
  })
);

// Request logging
app.use('*', logger());

// =============================================================================
// PUBLIC ROUTES (no auth required)
// =============================================================================

// Root endpoint
app.get('/', (c) => {
  return c.json({
    service: 'popkit-cloud',
    version: '0.1.0',
    docs: 'https://popkit.dev/docs/cloud',
  });
});

// Health check (public)
app.route('/v1/health', healthRoutes);

// =============================================================================
// PROTECTED ROUTES (auth required)
// =============================================================================

// Apply auth middleware to /v1/* routes (except health)
app.use('/v1/redis/*', authMiddleware);
app.use('/v1/usage/*', authMiddleware);
app.use('/v1/embeddings/*', authMiddleware);

// Apply rate limiting after auth
app.use('/v1/redis/*', rateLimitMiddleware);
app.use('/v1/embeddings/*', rateLimitMiddleware);

// Mount protected routes
app.route('/v1/redis', redisRoutes);
app.route('/v1/usage', usageRoutes);
app.route('/v1/embeddings', embeddingsRoutes);

// =============================================================================
// ERROR HANDLING
// =============================================================================

app.onError((err, c) => {
  console.error('Request error:', err);

  if (err.message === 'Unauthorized') {
    return c.json({ error: 'Unauthorized' }, 401);
  }

  if (err.message === 'Rate limit exceeded') {
    return c.json({ error: 'Rate limit exceeded' }, 429);
  }

  return c.json(
    {
      error: 'Internal server error',
      message: c.env.ENVIRONMENT === 'development' ? err.message : undefined,
    },
    500
  );
});

app.notFound((c) => {
  return c.json({ error: 'Not found' }, 404);
});

// =============================================================================
// EXPORT
// =============================================================================

export default app;
