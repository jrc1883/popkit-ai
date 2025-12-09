/**
 * Analytics Routes
 *
 * Part of Issue #74 (Analytics Dashboard) and #78 (Efficiency Metrics)
 *
 * Provides metrics and efficiency tracking for Pro/Team users.
 */

import { Hono } from 'hono';
import { Redis } from '@upstash/redis';
import type { Env, Variables } from '../types';

const analytics = new Hono<{ Bindings: Env; Variables: Variables }>();

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

/**
 * Get today's date string.
 */
function getToday(): string {
  return new Date().toISOString().split('T')[0];
}

// =============================================================================
// EFFICIENCY METRICS
// =============================================================================

/**
 * Record efficiency metrics.
 *
 * POST /analytics/efficiency
 * Body: {
 *   session_id: string,
 *   duplicates_skipped: number,
 *   patterns_matched: number,
 *   insights_shared: number,
 *   insights_received: number,
 *   tokens_estimated_saved: number,
 *   tool_calls: number,
 *   resolution_time_ms?: number
 * }
 */
analytics.post('/efficiency', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const prefix = getUserPrefix(c);
  const today = getToday();
  const body = await c.req.json<{
    session_id: string;
    duplicates_skipped?: number;
    patterns_matched?: number;
    insights_shared?: number;
    insights_received?: number;
    tokens_estimated_saved?: number;
    tool_calls?: number;
    resolution_time_ms?: number;
  }>();

  // Increment daily totals
  const pipeline: Promise<unknown>[] = [];

  if (body.duplicates_skipped) {
    pipeline.push(
      redis.hincrby(`${prefix}pop:analytics:${today}`, 'duplicates_skipped', body.duplicates_skipped)
    );
  }
  if (body.patterns_matched) {
    pipeline.push(
      redis.hincrby(`${prefix}pop:analytics:${today}`, 'patterns_matched', body.patterns_matched)
    );
  }
  if (body.insights_shared) {
    pipeline.push(
      redis.hincrby(`${prefix}pop:analytics:${today}`, 'insights_shared', body.insights_shared)
    );
  }
  if (body.insights_received) {
    pipeline.push(
      redis.hincrby(`${prefix}pop:analytics:${today}`, 'insights_received', body.insights_received)
    );
  }
  if (body.tokens_estimated_saved) {
    pipeline.push(
      redis.hincrby(`${prefix}pop:analytics:${today}`, 'tokens_saved', body.tokens_estimated_saved)
    );
  }
  if (body.tool_calls) {
    pipeline.push(
      redis.hincrby(`${prefix}pop:analytics:${today}`, 'tool_calls', body.tool_calls)
    );
  }

  // Track session
  pipeline.push(
    redis.hincrby(`${prefix}pop:analytics:${today}`, 'sessions', 1)
  );

  await Promise.all(pipeline);

  // Store session details
  if (body.session_id) {
    await redis.hset(`${prefix}pop:sessions:${today}`, {
      [body.session_id]: JSON.stringify({
        ...body,
        recorded_at: new Date().toISOString(),
      }),
    });
  }

  return c.json({ status: 'recorded' });
});

/**
 * Get efficiency summary.
 *
 * GET /analytics/efficiency/summary?days=7
 */
analytics.get('/efficiency/summary', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const prefix = getUserPrefix(c);
  const days = Math.min(parseInt(c.req.query('days') || '7'), 30);

  // Get data for each day
  const dailyData: Array<{
    date: string;
    metrics: Record<string, number>;
  }> = [];

  for (let i = 0; i < days; i++) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    const dateStr = date.toISOString().split('T')[0];

    const metrics = await redis.hgetall(`${prefix}pop:analytics:${dateStr}`) as Record<string, string> | null;

    if (metrics) {
      dailyData.push({
        date: dateStr,
        metrics: Object.fromEntries(
          Object.entries(metrics).map(([k, v]) => [k, parseInt(v as string, 10)])
        ),
      });
    }
  }

  // Calculate totals
  const totals = {
    sessions: 0,
    tool_calls: 0,
    duplicates_skipped: 0,
    patterns_matched: 0,
    insights_shared: 0,
    insights_received: 0,
    tokens_saved: 0,
  };

  for (const day of dailyData) {
    for (const [key, value] of Object.entries(day.metrics)) {
      if (key in totals) {
        (totals as Record<string, number>)[key] += value;
      }
    }
  }

  // Calculate derived metrics
  const avgToolCallsPerSession = totals.sessions > 0
    ? Math.round(totals.tool_calls / totals.sessions)
    : 0;

  const insightEfficiency = totals.insights_shared > 0
    ? Math.round((totals.insights_received / totals.insights_shared) * 100)
    : 0;

  return c.json({
    period: {
      days,
      start: dailyData[dailyData.length - 1]?.date,
      end: dailyData[0]?.date,
    },
    totals,
    derived: {
      avg_tool_calls_per_session: avgToolCallsPerSession,
      insight_efficiency_percent: insightEfficiency,
      tokens_saved_per_session: totals.sessions > 0
        ? Math.round(totals.tokens_saved / totals.sessions)
        : 0,
      dedup_rate: totals.insights_shared > 0
        ? Math.round((totals.duplicates_skipped / totals.insights_shared) * 100)
        : 0,
    },
    daily: dailyData,
  });
});

// =============================================================================
// AGENT METRICS
// =============================================================================

/**
 * Record agent activity.
 *
 * POST /analytics/agent
 * Body: {
 *   agent_id: string,
 *   agent_name: string,
 *   session_id: string,
 *   tool_calls: number,
 *   duration_ms: number,
 *   task_completed: boolean
 * }
 */
analytics.post('/agent', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const prefix = getUserPrefix(c);
  const today = getToday();
  const body = await c.req.json<{
    agent_id: string;
    agent_name: string;
    session_id: string;
    tool_calls?: number;
    duration_ms?: number;
    task_completed?: boolean;
  }>();

  // Increment agent usage
  await redis.hincrby(`${prefix}pop:agent_usage:${today}`, body.agent_name, 1);

  // Track agent performance
  await redis.lpush(`${prefix}pop:agent_activity:${body.agent_name}`, JSON.stringify({
    session_id: body.session_id,
    tool_calls: body.tool_calls || 0,
    duration_ms: body.duration_ms || 0,
    task_completed: body.task_completed || false,
    recorded_at: new Date().toISOString(),
  }));

  // Trim to last 100 activities
  await redis.ltrim(`${prefix}pop:agent_activity:${body.agent_name}`, 0, 99);

  return c.json({ status: 'recorded' });
});

/**
 * Get agent metrics.
 *
 * GET /analytics/agents?days=7
 */
analytics.get('/agents', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const prefix = getUserPrefix(c);
  const days = Math.min(parseInt(c.req.query('days') || '7'), 30);

  // Aggregate agent usage over period
  const agentUsage: Record<string, number> = {};

  for (let i = 0; i < days; i++) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    const dateStr = date.toISOString().split('T')[0];

    const usage = await redis.hgetall(`${prefix}pop:agent_usage:${dateStr}`) as Record<string, string> | null;
    if (usage) {
      for (const [agent, count] of Object.entries(usage)) {
        agentUsage[agent] = (agentUsage[agent] || 0) + parseInt(count as string, 10);
      }
    }
  }

  // Sort by usage
  const sorted = Object.entries(agentUsage)
    .sort((a, b) => b[1] - a[1])
    .map(([agent, count]) => ({ agent, invocations: count }));

  return c.json({
    period_days: days,
    total_invocations: sorted.reduce((sum, a) => sum + a.invocations, 0),
    agents: sorted,
  });
});

// =============================================================================
// PATTERN METRICS
// =============================================================================

/**
 * Get pattern usage metrics.
 *
 * GET /analytics/patterns?days=7
 */
analytics.get('/patterns', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const prefix = getUserPrefix(c);

  // Get pattern stats
  const [
    totalPatterns,
    totalInsights,
    embeddingUsage,
  ] = await Promise.all([
    redis.get('pop:patterns:total_count'),
    redis.hlen(`${prefix}pop:insight_embeddings`),
    redis.hgetall(`${prefix}pop:embedding_usage:${getToday()}`),
  ]);

  // Get top patterns used by this user
  const userPatternUsage = await redis.hgetall(`${prefix}pop:pattern_usage`) as Record<string, string> | null;

  const topPatterns = userPatternUsage
    ? Object.entries(userPatternUsage)
        .map(([id, count]) => ({ id, uses: parseInt(count as string, 10) }))
        .sort((a, b) => b.uses - a.uses)
        .slice(0, 10)
    : [];

  return c.json({
    collective: {
      total_patterns: totalPatterns || 0,
    },
    user: {
      insights_stored: totalInsights,
      patterns_used: topPatterns,
      embedding_usage_today: embeddingUsage || {},
    },
  });
});

// =============================================================================
// POWER MODE METRICS
// =============================================================================

/**
 * Record Power Mode session.
 *
 * POST /analytics/power-mode
 * Body: {
 *   session_id: string,
 *   issue_number?: number,
 *   agents_count: number,
 *   phases_completed: number,
 *   total_phases: number,
 *   duration_ms: number,
 *   insights_exchanged: number,
 *   sync_barriers_hit: number
 * }
 */
analytics.post('/power-mode', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const prefix = getUserPrefix(c);
  const today = getToday();
  const body = await c.req.json<{
    session_id: string;
    issue_number?: number;
    agents_count?: number;
    phases_completed?: number;
    total_phases?: number;
    duration_ms?: number;
    insights_exchanged?: number;
    sync_barriers_hit?: number;
  }>();

  // Increment daily counters
  await redis.hincrby(`${prefix}pop:power_mode:${today}`, 'sessions', 1);

  if (body.agents_count) {
    await redis.hincrby(`${prefix}pop:power_mode:${today}`, 'total_agents', body.agents_count);
  }
  if (body.insights_exchanged) {
    await redis.hincrby(`${prefix}pop:power_mode:${today}`, 'insights_exchanged', body.insights_exchanged);
  }
  if (body.duration_ms) {
    await redis.hincrby(`${prefix}pop:power_mode:${today}`, 'total_duration_ms', body.duration_ms);
  }

  // Store session details
  await redis.lpush(`${prefix}pop:power_mode_sessions`, JSON.stringify({
    ...body,
    date: today,
    recorded_at: new Date().toISOString(),
  }));

  // Trim to last 50 sessions
  await redis.ltrim(`${prefix}pop:power_mode_sessions`, 0, 49);

  return c.json({ status: 'recorded' });
});

/**
 * Get Power Mode metrics.
 *
 * GET /analytics/power-mode?days=7
 */
analytics.get('/power-mode', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const prefix = getUserPrefix(c);
  const days = Math.min(parseInt(c.req.query('days') || '7'), 30);

  // Aggregate over period
  const totals = {
    sessions: 0,
    total_agents: 0,
    insights_exchanged: 0,
    total_duration_ms: 0,
  };

  for (let i = 0; i < days; i++) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    const dateStr = date.toISOString().split('T')[0];

    const metrics = await redis.hgetall(`${prefix}pop:power_mode:${dateStr}`) as Record<string, string> | null;
    if (metrics) {
      for (const [key, value] of Object.entries(metrics)) {
        if (key in totals) {
          (totals as Record<string, number>)[key] += parseInt(value as string, 10);
        }
      }
    }
  }

  // Calculate derived
  const avgAgentsPerSession = totals.sessions > 0
    ? (totals.total_agents / totals.sessions).toFixed(1)
    : '0';

  const avgSessionDuration = totals.sessions > 0
    ? Math.round(totals.total_duration_ms / totals.sessions / 1000 / 60) // minutes
    : 0;

  const avgInsightsPerSession = totals.sessions > 0
    ? Math.round(totals.insights_exchanged / totals.sessions)
    : 0;

  return c.json({
    period_days: days,
    totals,
    derived: {
      avg_agents_per_session: parseFloat(avgAgentsPerSession),
      avg_session_duration_minutes: avgSessionDuration,
      avg_insights_per_session: avgInsightsPerSession,
    },
  });
});

// =============================================================================
// OVERVIEW
// =============================================================================

/**
 * Get overall analytics summary.
 *
 * GET /analytics/overview?days=7
 */
analytics.get('/overview', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const prefix = getUserPrefix(c);
  const days = Math.min(parseInt(c.req.query('days') || '7'), 30);
  const today = getToday();

  // Get various metrics
  const [
    todayEfficiency,
    totalInsights,
    todayEmbedding,
  ] = await Promise.all([
    redis.hgetall(`${prefix}pop:analytics:${today}`),
    redis.hlen(`${prefix}pop:insight_embeddings`),
    redis.hgetall(`${prefix}pop:embedding_usage:${today}`),
  ]);

  // Calculate week's efficiency
  let weekTokensSaved = 0;
  let weekSessions = 0;
  let weekPatterns = 0;

  for (let i = 0; i < days; i++) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    const dateStr = date.toISOString().split('T')[0];

    const metrics = await redis.hgetall(`${prefix}pop:analytics:${dateStr}`) as Record<string, string> | null;
    if (metrics) {
      weekTokensSaved += parseInt(metrics.tokens_saved || '0', 10);
      weekSessions += parseInt(metrics.sessions || '0', 10);
      weekPatterns += parseInt(metrics.patterns_matched || '0', 10);
    }
  }

  return c.json({
    period_days: days,
    today: {
      sessions: parseInt((todayEfficiency as Record<string, string>)?.sessions || '0', 10),
      tokens_saved: parseInt((todayEfficiency as Record<string, string>)?.tokens_saved || '0', 10),
      patterns_matched: parseInt((todayEfficiency as Record<string, string>)?.patterns_matched || '0', 10),
      embedding_tokens: parseInt((todayEmbedding as Record<string, string>)?.tokens || '0', 10),
    },
    period: {
      total_sessions: weekSessions,
      total_tokens_saved: weekTokensSaved,
      total_patterns_matched: weekPatterns,
      avg_tokens_saved_per_session: weekSessions > 0
        ? Math.round(weekTokensSaved / weekSessions)
        : 0,
    },
    storage: {
      insights_stored: totalInsights,
    },
  });
});

export default analytics;
