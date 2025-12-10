/**
 * Team Coordination Routes
 *
 * Part of Issue #2 (Team Coordination Features) - PRIVATE REPO
 *
 * Implements multi-developer Power Mode coordination for Team tier ($29/mo).
 *
 * Features:
 * - Team creation and member management
 * - Shared Power Mode sessions
 * - Team-scoped insights and patterns
 * - Activity tracking across team members
 */

import { Hono } from 'hono';
import { Redis } from '@upstash/redis';
import type { Env, Variables, ApiKeyData } from '../types';

const teams = new Hono<{ Bindings: Env; Variables: Variables }>();

// =============================================================================
// TYPES
// =============================================================================

interface Team {
  id: string;
  name: string;
  ownerId: string;
  createdAt: string;
  memberCount: number;
  settings: {
    allowMemberInvites: boolean;
    shareInsightsAcrossProjects: boolean;
    patternVisibility: 'private' | 'team-only';
  };
  // Index signature for Redis hgetall compatibility
  [key: string]: unknown;
}

interface TeamMember {
  userId: string;
  role: 'owner' | 'admin' | 'member';
  joinedAt: string;
  invitedBy: string;
  lastActiveAt?: string;
}

interface TeamSession {
  sessionId: string;
  teamId: string;
  projectPath: string;
  startedAt: string;
  objective?: string;
  activeAgents: Array<{
    agentId: string;
    agentName: string;
    userId: string;
    userName: string;
    startedAt: string;
    currentTask?: string;
    progress: number;
  }>;
  sharedInsights: number;
  filesModified: string[];
  // Index signature for Redis hgetall compatibility
  [key: string]: unknown;
}

// =============================================================================
// TIER CHECK MIDDLEWARE
// =============================================================================

/**
 * Middleware to ensure user is on Team tier.
 */
async function requireTeamTier(
  c: any,
  next: any
) {
  const apiKey = c.get('apiKey') as ApiKeyData;

  if (apiKey.tier !== 'team') {
    return c.json(
      {
        error: 'Team tier required',
        message: 'Team coordination features require the Team tier ($29/mo)',
        upgradeUrl: 'https://popkit.dev/pricing',
      },
      403
    );
  }

  await next();
}

// Apply tier check to all team routes
teams.use('*', requireTeamTier);

// =============================================================================
// TEAM CRUD
// =============================================================================

/**
 * POST /v1/teams
 * Create a new team.
 */
teams.post('/', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const apiKey = c.get('apiKey') as ApiKeyData;
  const body = await c.req.json<{ name: string }>();

  if (!body.name || body.name.length < 2) {
    return c.json({ error: 'Team name required (min 2 characters)' }, 400);
  }

  // Check if user already owns a team
  const existingTeamId = await redis.get<string>(`popkit:user:${apiKey.userId}:team`);
  if (existingTeamId) {
    return c.json({ error: 'User already owns a team', teamId: existingTeamId }, 409);
  }

  const teamId = crypto.randomUUID();
  const team: Team = {
    id: teamId,
    name: body.name,
    ownerId: apiKey.userId,
    createdAt: new Date().toISOString(),
    memberCount: 1,
    settings: {
      allowMemberInvites: true,
      shareInsightsAcrossProjects: true,
      patternVisibility: 'team-only',
    },
  };

  // Store team
  await redis.hset(`popkit:team:${teamId}`, team as any);

  // Store owner as first member
  const ownerMember: TeamMember = {
    userId: apiKey.userId,
    role: 'owner',
    joinedAt: new Date().toISOString(),
    invitedBy: apiKey.userId,
  };
  await redis.hset(`popkit:team:${teamId}:members`, {
    [apiKey.userId]: JSON.stringify(ownerMember),
  });

  // Link user to team
  await redis.set(`popkit:user:${apiKey.userId}:team`, teamId);

  return c.json({ team }, 201);
});

/**
 * GET /v1/teams/:teamId
 * Get team details.
 */
teams.get('/:teamId', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const { teamId } = c.req.param();
  const apiKey = c.get('apiKey') as ApiKeyData;

  // Check membership
  const memberData = await redis.hget<string>(`popkit:team:${teamId}:members`, apiKey.userId);
  if (!memberData) {
    return c.json({ error: 'Not a member of this team' }, 403);
  }

  // Get team
  const team = await redis.hgetall<Team>(`popkit:team:${teamId}`);
  if (!team) {
    return c.json({ error: 'Team not found' }, 404);
  }

  return c.json({ team });
});

// =============================================================================
// MEMBER MANAGEMENT
// =============================================================================

/**
 * POST /v1/teams/:teamId/members
 * Add a member to the team.
 */
teams.post('/:teamId/members', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const { teamId } = c.req.param();
  const apiKey = c.get('apiKey') as ApiKeyData;
  const body = await c.req.json<{ userId: string; role?: 'admin' | 'member' }>();

  // Check caller is admin/owner
  const callerMemberData = await redis.hget<string>(`popkit:team:${teamId}:members`, apiKey.userId);
  if (!callerMemberData) {
    return c.json({ error: 'Not a member of this team' }, 403);
  }

  const callerMember = JSON.parse(callerMemberData) as TeamMember;
  if (callerMember.role !== 'owner' && callerMember.role !== 'admin') {
    return c.json({ error: 'Only admins can add members' }, 403);
  }

  // Check target is on team tier
  const targetKeys = await redis.smembers(`popkit:user:${body.userId}:keys`);
  if (!targetKeys || targetKeys.length === 0) {
    return c.json({ error: 'User not found or has no API key' }, 404);
  }

  // Add member
  const newMember: TeamMember = {
    userId: body.userId,
    role: body.role || 'member',
    joinedAt: new Date().toISOString(),
    invitedBy: apiKey.userId,
  };

  await redis.hset(`popkit:team:${teamId}:members`, {
    [body.userId]: JSON.stringify(newMember),
  });

  // Link user to team
  await redis.set(`popkit:user:${body.userId}:team`, teamId);

  // Update member count
  await redis.hincrby(`popkit:team:${teamId}`, 'memberCount', 1);

  return c.json({ member: newMember }, 201);
});

/**
 * GET /v1/teams/:teamId/members
 * List team members.
 */
teams.get('/:teamId/members', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const { teamId } = c.req.param();
  const apiKey = c.get('apiKey') as ApiKeyData;

  // Check membership
  const memberData = await redis.hget<string>(`popkit:team:${teamId}:members`, apiKey.userId);
  if (!memberData) {
    return c.json({ error: 'Not a member of this team' }, 403);
  }

  // Get all members
  const allMembers = await redis.hgetall<Record<string, string>>(`popkit:team:${teamId}:members`);
  const members = Object.entries(allMembers || {}).map(([userId, data]) => ({
    ...JSON.parse(data),
    userId,
  }));

  return c.json({ members });
});

/**
 * DELETE /v1/teams/:teamId/members/:userId
 * Remove a member from the team.
 */
teams.delete('/:teamId/members/:userId', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const { teamId, userId } = c.req.param();
  const apiKey = c.get('apiKey') as ApiKeyData;

  // Check caller is admin/owner or removing self
  const callerMemberData = await redis.hget<string>(`popkit:team:${teamId}:members`, apiKey.userId);
  if (!callerMemberData) {
    return c.json({ error: 'Not a member of this team' }, 403);
  }

  const callerMember = JSON.parse(callerMemberData) as TeamMember;
  const isSelf = apiKey.userId === userId;
  const isAdmin = callerMember.role === 'owner' || callerMember.role === 'admin';

  if (!isSelf && !isAdmin) {
    return c.json({ error: 'Cannot remove other members' }, 403);
  }

  // Cannot remove owner
  const targetMemberData = await redis.hget<string>(`popkit:team:${teamId}:members`, userId);
  if (!targetMemberData) {
    return c.json({ error: 'Member not found' }, 404);
  }

  const targetMember = JSON.parse(targetMemberData) as TeamMember;
  if (targetMember.role === 'owner') {
    return c.json({ error: 'Cannot remove team owner' }, 400);
  }

  // Remove member
  await redis.hdel(`popkit:team:${teamId}:members`, userId);
  await redis.del(`popkit:user:${userId}:team`);
  await redis.hincrby(`popkit:team:${teamId}`, 'memberCount', -1);

  return c.json({ success: true });
});

// =============================================================================
// TEAM SESSIONS (Power Mode)
// =============================================================================

/**
 * GET /v1/teams/:teamId/sessions
 * List active team Power Mode sessions.
 */
teams.get('/:teamId/sessions', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const { teamId } = c.req.param();
  const apiKey = c.get('apiKey') as ApiKeyData;

  // Check membership
  const memberData = await redis.hget<string>(`popkit:team:${teamId}:members`, apiKey.userId);
  if (!memberData) {
    return c.json({ error: 'Not a member of this team' }, 403);
  }

  // Get active sessions
  const sessionKeys = await redis.keys(`popkit:team:${teamId}:session:*`);
  const sessions: TeamSession[] = [];

  for (const key of sessionKeys || []) {
    const session = await redis.hgetall<TeamSession>(key);
    if (session) {
      sessions.push(session);
    }
  }

  return c.json({ sessions });
});

/**
 * POST /v1/teams/:teamId/sessions
 * Start or join a team Power Mode session.
 */
teams.post('/:teamId/sessions', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const { teamId } = c.req.param();
  const apiKey = c.get('apiKey') as ApiKeyData;
  const body = await c.req.json<{
    sessionId: string;
    projectPath: string;
    objective?: string;
    agentId: string;
    agentName: string;
  }>();

  // Check membership
  const memberData = await redis.hget<string>(`popkit:team:${teamId}:members`, apiKey.userId);
  if (!memberData) {
    return c.json({ error: 'Not a member of this team' }, 403);
  }

  const sessionKey = `popkit:team:${teamId}:session:${body.sessionId}`;

  // Check if session exists
  const existingSession = await redis.exists(sessionKey);

  if (existingSession) {
    // Join existing session
    const session = await redis.hgetall<TeamSession>(sessionKey);
    if (!session) {
      return c.json({ error: 'Session not found' }, 404);
    }

    // Add agent to session
    const newAgent = {
      agentId: body.agentId,
      agentName: body.agentName,
      userId: apiKey.userId,
      userName: apiKey.name || 'Unknown',
      startedAt: new Date().toISOString(),
      progress: 0,
    };

    const activeAgents = session.activeAgents || [];
    activeAgents.push(newAgent);

    await redis.hset(sessionKey, { activeAgents: JSON.stringify(activeAgents) });

    return c.json({ action: 'joined', session: { ...session, activeAgents } });
  }

  // Create new session
  const newSession: TeamSession = {
    sessionId: body.sessionId,
    teamId,
    projectPath: body.projectPath,
    startedAt: new Date().toISOString(),
    objective: body.objective,
    activeAgents: [
      {
        agentId: body.agentId,
        agentName: body.agentName,
        userId: apiKey.userId,
        userName: apiKey.name || 'Unknown',
        startedAt: new Date().toISOString(),
        progress: 0,
      },
    ],
    sharedInsights: 0,
    filesModified: [],
  };

  await redis.hset(sessionKey, {
    ...newSession,
    activeAgents: JSON.stringify(newSession.activeAgents),
    filesModified: JSON.stringify(newSession.filesModified),
  } as any);

  // Set TTL (sessions expire after 2 hours of inactivity)
  await redis.expire(sessionKey, 7200);

  return c.json({ action: 'created', session: newSession }, 201);
});

/**
 * PATCH /v1/teams/:teamId/sessions/:sessionId
 * Update session state (agent progress, files modified, etc.)
 */
teams.patch('/:teamId/sessions/:sessionId', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const { teamId, sessionId } = c.req.param();
  const apiKey = c.get('apiKey') as ApiKeyData;
  const body = await c.req.json<{
    agentId: string;
    progress?: number;
    currentTask?: string;
    filesModified?: string[];
    insightShared?: boolean;
  }>();

  // Check membership
  const memberData = await redis.hget<string>(`popkit:team:${teamId}:members`, apiKey.userId);
  if (!memberData) {
    return c.json({ error: 'Not a member of this team' }, 403);
  }

  const sessionKey = `popkit:team:${teamId}:session:${sessionId}`;
  const session = await redis.hgetall<any>(sessionKey);

  if (!session) {
    return c.json({ error: 'Session not found' }, 404);
  }

  // Parse stored JSON
  const activeAgents = JSON.parse(session.activeAgents || '[]');
  const filesModified = JSON.parse(session.filesModified || '[]');

  // Update agent
  const agentIndex = activeAgents.findIndex((a: any) => a.agentId === body.agentId);
  if (agentIndex >= 0) {
    if (body.progress !== undefined) {
      activeAgents[agentIndex].progress = body.progress;
    }
    if (body.currentTask !== undefined) {
      activeAgents[agentIndex].currentTask = body.currentTask;
    }
  }

  // Update files modified
  if (body.filesModified) {
    for (const file of body.filesModified) {
      if (!filesModified.includes(file)) {
        filesModified.push(file);
      }
    }
  }

  // Update insights count
  let sharedInsights = parseInt(session.sharedInsights || '0', 10);
  if (body.insightShared) {
    sharedInsights++;
  }

  // Save updates
  await redis.hset(sessionKey, {
    activeAgents: JSON.stringify(activeAgents),
    filesModified: JSON.stringify(filesModified),
    sharedInsights: sharedInsights.toString(),
  });

  // Refresh TTL
  await redis.expire(sessionKey, 7200);

  return c.json({
    session: {
      ...session,
      activeAgents,
      filesModified,
      sharedInsights,
    },
  });
});

// =============================================================================
// TEAM INSIGHTS
// =============================================================================

/**
 * GET /v1/teams/:teamId/insights
 * Get team insights pool.
 */
teams.get('/:teamId/insights', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const { teamId } = c.req.param();
  const apiKey = c.get('apiKey') as ApiKeyData;
  const limit = parseInt(c.req.query('limit') || '50', 10);

  // Check membership
  const memberData = await redis.hget<string>(`popkit:team:${teamId}:members`, apiKey.userId);
  if (!memberData) {
    return c.json({ error: 'Not a member of this team' }, 403);
  }

  // Get recent insights
  const insights = await redis.lrange(`popkit:team:${teamId}:insights`, 0, limit - 1);

  return c.json({
    insights: insights.map((i) => (typeof i === 'string' ? JSON.parse(i) : i)),
  });
});

/**
 * POST /v1/teams/:teamId/insights
 * Share an insight with the team.
 */
teams.post('/:teamId/insights', async (c) => {
  const redis = new Redis({
    url: c.env.UPSTASH_REDIS_REST_URL,
    token: c.env.UPSTASH_REDIS_REST_TOKEN,
  });

  const { teamId } = c.req.param();
  const apiKey = c.get('apiKey') as ApiKeyData;
  const body = await c.req.json<{
    type: string;
    content: string;
    context?: Record<string, any>;
    sessionId?: string;
  }>();

  // Check membership
  const memberData = await redis.hget<string>(`popkit:team:${teamId}:members`, apiKey.userId);
  if (!memberData) {
    return c.json({ error: 'Not a member of this team' }, 403);
  }

  const insight = {
    id: crypto.randomUUID(),
    type: body.type,
    content: body.content,
    context: body.context,
    sessionId: body.sessionId,
    userId: apiKey.userId,
    userName: apiKey.name,
    createdAt: new Date().toISOString(),
  };

  // Add to team insights (keep last 500)
  await redis.lpush(`popkit:team:${teamId}:insights`, JSON.stringify(insight));
  await redis.ltrim(`popkit:team:${teamId}:insights`, 0, 499);

  return c.json({ insight }, 201);
});

export default teams;
