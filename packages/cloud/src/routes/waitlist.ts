/**
 * Waitlist Routes
 *
 * Pre-launch email capture for users interested in premium features.
 * Used when POPKIT_BILLING_LIVE=false to collect launch notifications.
 */

import { Hono } from 'hono';
import type { Env, Variables } from '../types';

const app = new Hono<{ Bindings: Env; Variables: Variables }>();

// =============================================================================
// TYPES
// =============================================================================

interface WaitlistSignup {
  email: string;
  feature: string;
  timestamp: string;
  tier?: string;
}

interface WaitlistEntry extends WaitlistSignup {
  id: string;
  created_at: string;
  ip_address?: string;
  user_agent?: string;
}

// =============================================================================
// ROUTES
// =============================================================================

/**
 * POST /v1/waitlist/signup
 *
 * Capture email for premium feature waitlist
 * Public endpoint - no auth required
 */
app.post('/signup', async (c) => {
  try {
    const body = await c.req.json<WaitlistSignup>();
    const { email, feature, timestamp, tier = 'free' } = body;

    // Validate email format
    const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    if (!email || !emailRegex.test(email)) {
      return c.json({ error: 'Invalid email address' }, 400);
    }

    // Validate feature name
    if (!feature || feature.trim().length === 0) {
      return c.json({ error: 'Feature name is required' }, 400);
    }

    // Get request metadata
    const ip = c.req.header('CF-Connecting-IP') || c.req.header('X-Forwarded-For') || 'unknown';
    const userAgent = c.req.header('User-Agent') || 'unknown';

    // Generate unique ID
    const id = crypto.randomUUID();
    const created_at = new Date().toISOString();

    const entry: WaitlistEntry = {
      id,
      email: email.toLowerCase().trim(),
      feature,
      timestamp,
      tier,
      created_at,
      ip_address: ip,
      user_agent: userAgent,
    };

    // Store in KV (waitlist namespace)
    // Key format: waitlist:{email}:{feature}
    const key = `waitlist:${entry.email}:${feature}`;
    await c.env.WAITLIST_KV.put(key, JSON.stringify(entry), {
      metadata: {
        email: entry.email,
        feature,
        tier,
        created_at,
      },
    });

    // Also store in a list for easy retrieval (optional)
    // Key format: waitlist:all:{timestamp}:{id}
    const listKey = `waitlist:all:${created_at}:${id}`;
    await c.env.WAITLIST_KV.put(listKey, JSON.stringify(entry));

    // Log signup for analytics (if D1 database is available)
    if (c.env.DB) {
      try {
        await c.env.DB.prepare(
          `INSERT INTO waitlist_signups (id, email, feature, tier, created_at, ip_address, user_agent)
           VALUES (?, ?, ?, ?, ?, ?, ?)`
        )
          .bind(id, entry.email, feature, tier, created_at, ip, userAgent)
          .run();
      } catch (dbError) {
        // Don't fail if database insert fails
        console.error('Failed to log waitlist signup to DB:', dbError);
      }
    }

    return c.json(
      {
        success: true,
        message: 'Successfully added to waitlist',
        id,
      },
      201
    );
  } catch (error) {
    console.error('Waitlist signup error:', error);
    return c.json({ error: 'Failed to process signup' }, 500);
  }
});

/**
 * GET /v1/waitlist/list
 *
 * List all waitlist signups (admin only)
 * Requires auth
 */
app.get('/list', async (c) => {
  try {
    // Check if user is admin (you can add proper admin auth later)
    const apiKey = c.req.header('Authorization')?.replace('Bearer ', '');
    if (!apiKey) {
      return c.json({ error: 'Unauthorized' }, 401);
    }

    // Get all waitlist entries from KV
    const list = await c.env.WAITLIST_KV.list({ prefix: 'waitlist:all:' });
    const entries: WaitlistEntry[] = [];

    for (const key of list.keys) {
      const value = await c.env.WAITLIST_KV.get(key.name);
      if (value) {
        entries.push(JSON.parse(value));
      }
    }

    // Sort by created_at descending
    entries.sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());

    return c.json({
      total: entries.length,
      entries,
    });
  } catch (error) {
    console.error('Waitlist list error:', error);
    return c.json({ error: 'Failed to retrieve waitlist' }, 500);
  }
});

/**
 * GET /v1/waitlist/stats
 *
 * Get waitlist statistics
 * Public endpoint
 */
app.get('/stats', async (c) => {
  try {
    // Get count from KV metadata
    const list = await c.env.WAITLIST_KV.list({ prefix: 'waitlist:all:' });

    // Group by feature
    const byFeature: Record<string, number> = {};
    const byTier: Record<string, number> = {};

    for (const key of list.keys) {
      const metadata = key.metadata as { feature?: string; tier?: string } | null;
      if (metadata?.feature) {
        byFeature[metadata.feature] = (byFeature[metadata.feature] || 0) + 1;
      }
      if (metadata?.tier) {
        byTier[metadata.tier] = (byTier[metadata.tier] || 0) + 1;
      }
    }

    return c.json({
      total: list.keys.length,
      by_feature: byFeature,
      by_tier: byTier,
    });
  } catch (error) {
    console.error('Waitlist stats error:', error);
    return c.json({ error: 'Failed to retrieve stats' }, 500);
  }
});

export default app;
