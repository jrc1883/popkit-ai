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
import patternsRoutes from './routes/patterns';
import privacyRoutes from './routes/privacy';
import analyticsRoutes from './routes/analytics';
import teamsRoutes from './routes/teams';
import projectsRoutes from './routes/projects';
import agentsRoutes from './routes/agents';
import workflowsRoutes from './routes/workflows';
import messagesRoutes from './routes/messages';
import authRoutes from './routes/auth';
import billingRoutes from './routes/billing';
import researchRoutes from './routes/research';

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

// Auth routes (public - no auth required for signup/login)
app.route('/v1/auth', authRoutes);

// Billing webhook (public - uses Stripe signature verification)
app.post('/v1/billing/webhook', billingRoutes);

// =============================================================================
// PROTECTED ROUTES (auth required)
// =============================================================================

// Apply auth middleware to /v1/* routes (except health)
app.use('/v1/redis/*', authMiddleware);
app.use('/v1/usage/*', authMiddleware);
app.use('/v1/embeddings/*', authMiddleware);
app.use('/v1/patterns/*', authMiddleware);
app.use('/v1/privacy/*', authMiddleware);
app.use('/v1/analytics/*', authMiddleware);
app.use('/v1/teams/*', authMiddleware);
app.use('/v1/projects/*', authMiddleware);
app.use('/v1/agents/*', authMiddleware);
app.use('/v1/workflows/*', authMiddleware);
app.use('/v1/messages/*', authMiddleware);
app.use('/v1/billing/*', authMiddleware);
app.use('/v1/research/*', authMiddleware);

// Apply rate limiting after auth
app.use('/v1/redis/*', rateLimitMiddleware);
app.use('/v1/embeddings/*', rateLimitMiddleware);
app.use('/v1/patterns/*', rateLimitMiddleware);
app.use('/v1/agents/*', rateLimitMiddleware);
app.use('/v1/messages/*', rateLimitMiddleware);
// No rate limit on privacy endpoints (they're rarely called)

// Mount protected routes
app.route('/v1/redis', redisRoutes);
app.route('/v1/usage', usageRoutes);
app.route('/v1/embeddings', embeddingsRoutes);
app.route('/v1/patterns', patternsRoutes);
app.route('/v1/privacy', privacyRoutes);
app.route('/v1/analytics', analyticsRoutes);
app.route('/v1/teams', teamsRoutes);
app.route('/v1/projects', projectsRoutes);
app.route('/v1/agents', agentsRoutes);
app.route('/v1/workflows', workflowsRoutes);
app.route('/v1/messages', messagesRoutes);
app.route('/v1/billing', billingRoutes);
app.route('/v1/research', researchRoutes);

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
