/**
 * Project Registry Routes
 *
 * Part of Issue #93 (Multi-Project Dashboard)
 *
 * Provides project registration, tracking, and discovery for
 * cross-project observability and multi-project management.
 */

import { Hono } from 'hono';
import { Redis } from '@upstash/redis';
import type { Env, Variables } from '../types';

const projects = new Hono<{ Bindings: Env; Variables: Variables }>();

/**
 * Project registration data structure stored in Redis.
 */
interface ProjectInfo {
  // Identity
  id: string;             // Unique project ID (hash of path)
  name: string;           // Project name (from package.json or directory)
  path: string;           // Anonymized path hint (last 2 segments)

  // Status
  health_score: number;   // 0-100 health score from morning routine
  last_active: string;    // ISO timestamp of last activity
  session_count: number;  // Total sessions recorded

  // Usage metrics
  tool_calls: number;     // Total tool calls
  agents_used: string[];  // Recent agents triggered
  commands_used: string[];// Recent commands executed

  // Power Mode info
  power_mode_active: boolean;
  active_agents: number;

  // Registration
  registered_at: string;  // First registration timestamp
  popkit_version: string; // Plugin version
  platform: string;       // win32, darwin, linux
}

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

// =============================================================================
// PROJECT REGISTRATION
// =============================================================================

/**
 * Register or update a project.
 *
 * POST /projects/register
 * Body: {
 *   project_id: string,
 *   name: string,
 *   path_hint?: string,
 *   health_score?: number,
 *   popkit_version: string,
 *   platform: string
 * }
 */
projects.post('/register', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const prefix = getUserPrefix(c);
  const body = await c.req.json<{
    project_id: string;
    name: string;
    path_hint?: string;
    health_score?: number;
    popkit_version: string;
    platform: string;
  }>();

  const projectKey = `${prefix}pop:projects:${body.project_id}`;
  const now = new Date().toISOString();

  // Check if project exists
  const existing = await redis.hgetall<ProjectInfo>(projectKey);

  const projectInfo: Partial<ProjectInfo> = {
    id: body.project_id,
    name: body.name,
    path: body.path_hint || '',
    health_score: body.health_score || (existing?.health_score || 0),
    last_active: now,
    session_count: (existing?.session_count || 0) + 1,
    tool_calls: existing?.tool_calls || 0,
    agents_used: existing?.agents_used || [],
    commands_used: existing?.commands_used || [],
    power_mode_active: false,
    active_agents: 0,
    registered_at: existing?.registered_at || now,
    popkit_version: body.popkit_version,
    platform: body.platform,
  };

  // Store project info
  await redis.hset(projectKey, projectInfo);

  // Add to project index
  await redis.sadd(`${prefix}pop:projects:index`, body.project_id);

  // Set TTL (30 days of inactivity = removal)
  await redis.expire(projectKey, 30 * 24 * 60 * 60);

  return c.json({
    status: 'registered',
    project_id: body.project_id,
    session_count: projectInfo.session_count,
  });
});

/**
 * Update project activity (called by check-in hook).
 *
 * POST /projects/:id/activity
 * Body: {
 *   tool_name?: string,
 *   agent_name?: string,
 *   command_name?: string,
 *   health_score?: number,
 *   power_mode?: { active: boolean, agent_count: number }
 * }
 */
projects.post('/:id/activity', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const prefix = getUserPrefix(c);
  const projectId = c.req.param('id');
  const body = await c.req.json<{
    tool_name?: string;
    agent_name?: string;
    command_name?: string;
    health_score?: number;
    power_mode?: { active: boolean; agent_count: number };
  }>();

  const projectKey = `${prefix}pop:projects:${projectId}`;
  const now = new Date().toISOString();

  // Get existing project
  const existing = await redis.hgetall<ProjectInfo>(projectKey);
  if (!existing) {
    return c.json({ error: 'Project not found' }, 404);
  }

  // Update activity
  const updates: Record<string, unknown> = {
    last_active: now,
    tool_calls: (existing.tool_calls || 0) + 1,
  };

  if (body.agent_name) {
    const agents = new Set(existing.agents_used || []);
    agents.add(body.agent_name);
    // Keep only last 10 agents
    updates.agents_used = Array.from(agents).slice(-10);
  }

  if (body.command_name) {
    const commands = new Set(existing.commands_used || []);
    commands.add(body.command_name);
    // Keep only last 10 commands
    updates.commands_used = Array.from(commands).slice(-10);
  }

  if (body.health_score !== undefined) {
    updates.health_score = body.health_score;
  }

  if (body.power_mode) {
    updates.power_mode_active = body.power_mode.active;
    updates.active_agents = body.power_mode.agent_count;
  }

  await redis.hset(projectKey, updates);

  // Refresh TTL
  await redis.expire(projectKey, 30 * 24 * 60 * 60);

  return c.json({ status: 'updated' });
});

// =============================================================================
// PROJECT LISTING
// =============================================================================

/**
 * List all registered projects for the user.
 *
 * GET /projects
 * Query: ?active_only=true (only show projects active in last 24h)
 */
projects.get('/', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const prefix = getUserPrefix(c);
  const activeOnly = c.req.query('active_only') === 'true';

  // Get all project IDs
  const projectIds = await redis.smembers(`${prefix}pop:projects:index`);
  if (!projectIds || projectIds.length === 0) {
    return c.json({ projects: [], count: 0 });
  }

  // Fetch all project data
  const projectList: ProjectInfo[] = [];
  const now = new Date();
  const dayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);

  for (const id of projectIds) {
    const project = await redis.hgetall<ProjectInfo>(`${prefix}pop:projects:${id}`);
    if (project) {
      // Filter by activity if requested
      if (activeOnly) {
        const lastActive = new Date(project.last_active);
        if (lastActive < dayAgo) continue;
      }
      projectList.push(project);
    }
  }

  // Sort by last_active (most recent first)
  projectList.sort((a, b) =>
    new Date(b.last_active).getTime() - new Date(a.last_active).getTime()
  );

  return c.json({
    projects: projectList,
    count: projectList.length,
    total: projectIds.length,
  });
});

/**
 * Get summary statistics across all projects.
 * NOTE: Must be defined BEFORE /:id to avoid route conflict.
 *
 * GET /projects/summary
 */
projects.get('/summary', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const prefix = getUserPrefix(c);

  // Get all project IDs
  const projectIds = await redis.smembers(`${prefix}pop:projects:index`);
  if (!projectIds || projectIds.length === 0) {
    return c.json({
      total_projects: 0,
      active_projects_24h: 0,
      total_tool_calls: 0,
      total_sessions: 0,
      avg_health_score: 0,
      power_mode_active: 0,
    });
  }

  const now = new Date();
  const dayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);

  let activeCount = 0;
  let totalToolCalls = 0;
  let totalSessions = 0;
  let healthScoreSum = 0;
  let healthCount = 0;
  let powerModeActive = 0;

  for (const id of projectIds) {
    const project = await redis.hgetall<ProjectInfo>(`${prefix}pop:projects:${id}`);
    if (project) {
      const lastActive = new Date(project.last_active);
      if (lastActive >= dayAgo) {
        activeCount++;
      }

      totalToolCalls += project.tool_calls || 0;
      totalSessions += project.session_count || 0;

      if (project.health_score > 0) {
        healthScoreSum += project.health_score;
        healthCount++;
      }

      if (project.power_mode_active) {
        powerModeActive++;
      }
    }
  }

  return c.json({
    total_projects: projectIds.length,
    active_projects_24h: activeCount,
    total_tool_calls: totalToolCalls,
    total_sessions: totalSessions,
    avg_health_score: healthCount > 0 ? Math.round(healthScoreSum / healthCount) : 0,
    power_mode_active: powerModeActive,
  });
});

/**
 * Get a specific project's details.
 * NOTE: Must be defined AFTER /summary to avoid route conflict.
 *
 * GET /projects/:id
 */
projects.get('/:id', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const prefix = getUserPrefix(c);
  const projectId = c.req.param('id');

  const project = await redis.hgetall<ProjectInfo>(
    `${prefix}pop:projects:${projectId}`
  );

  if (!project) {
    return c.json({ error: 'Project not found' }, 404);
  }

  return c.json(project);
});

// =============================================================================
// PROJECT REMOVAL
// =============================================================================

/**
 * Unregister a project.
 *
 * DELETE /projects/:id
 */
projects.delete('/:id', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const prefix = getUserPrefix(c);
  const projectId = c.req.param('id');

  // Remove from index
  await redis.srem(`${prefix}pop:projects:index`, projectId);

  // Delete project data
  await redis.del(`${prefix}pop:projects:${projectId}`);

  return c.json({ status: 'deleted', project_id: projectId });
});

export default projects;
