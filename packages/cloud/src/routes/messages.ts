/**
 * Inter-Agent Messaging Routes
 *
 * Part of Issue #109 (Inter-Agent Communication Protocol)
 *
 * Provides QStash-based durable messaging for Power Mode agents:
 * - POST /publish - Send message via QStash
 * - POST /receive - QStash webhook endpoint
 * - GET /poll/:agentId - Poll inbox for messages
 * - DELETE /clear/:agentId - Clear agent inbox
 */

import { Hono } from 'hono';
import { Redis } from '@upstash/redis';
import { Client } from '@upstash/qstash';
import type { Env, Variables } from '../types';
import type {
  AgentMessage,
  StoredMessage,
  RetentionTier,
  AgentMessageType,
} from '../types';
import { RETENTION_TTL, MESSAGE_RETENTION } from '../types';

const app = new Hono<{ Bindings: Env; Variables: Variables }>();

// =============================================================================
// HELPERS
// =============================================================================

/**
 * Generate unique message ID.
 */
function generateMessageId(): string {
  return `msg_${Date.now()}_${Math.random().toString(36).slice(2, 11)}`;
}

/**
 * Get Redis client.
 */
function getRedis(env: Env): Redis {
  return new Redis({
    url: env.UPSTASH_REDIS_REST_URL,
    token: env.UPSTASH_REDIS_REST_TOKEN,
  });
}

/**
 * Get QStash client.
 */
function getQStash(env: Env): Client {
  return new Client({
    token: env.QSTASH_TOKEN,
  });
}

/**
 * Get inbox key for an agent.
 */
function inboxKey(agentId: string): string {
  return `pop:inbox:${agentId}`;
}

/**
 * Get session inbox key.
 */
function sessionInboxKey(sessionId: string): string {
  return `pop:session:${sessionId}:inbox`;
}

/**
 * Calculate TTL based on retention tier.
 */
function getTTL(message: AgentMessage): number {
  const tier = message.retention || MESSAGE_RETENTION[message.type] || 'session';
  return RETENTION_TTL[tier];
}

/**
 * Validate message structure.
 */
function validateMessage(body: unknown): AgentMessage | null {
  if (!body || typeof body !== 'object') return null;

  const msg = body as Record<string, unknown>;

  // Required fields
  if (
    typeof msg.type !== 'string' ||
    typeof msg.fromAgent !== 'string' ||
    typeof msg.sessionId !== 'string' ||
    !msg.payload ||
    !Array.isArray(msg.tags)
  ) {
    return null;
  }

  // Add defaults
  return {
    id: (msg.id as string) || generateMessageId(),
    type: msg.type as AgentMessageType,
    fromAgent: msg.fromAgent as string,
    toAgents: msg.toAgents as string[] | undefined,
    sessionId: msg.sessionId as string,
    timestamp: (msg.timestamp as string) || new Date().toISOString(),
    payload: msg.payload as AgentMessage['payload'],
    tags: msg.tags as string[],
    priority: (msg.priority as AgentMessage['priority']) || 'normal',
    retention: msg.retention as RetentionTier | undefined,
  };
}

// =============================================================================
// ROUTES
// =============================================================================

/**
 * POST /publish
 *
 * Publish a message to other agents via QStash.
 * QStash provides guaranteed delivery with automatic retries.
 */
app.post('/publish', async (c) => {
  const env = c.env;

  try {
    const body = await c.req.json();
    const message = validateMessage(body);

    if (!message) {
      return c.json({ error: 'Invalid message format' }, 400);
    }

    // Ensure message has ID
    if (!message.id) {
      message.id = generateMessageId();
    }

    const qstash = getQStash(env);

    // Determine webhook URL (this worker's /receive endpoint)
    const workerUrl = new URL(c.req.url);
    const receiveUrl = `${workerUrl.origin}/v1/messages/receive`;

    // Send via QStash for guaranteed delivery
    const response = await qstash.publishJSON({
      url: receiveUrl,
      body: message,
      retries: 3,
      // Add deduplication ID to prevent duplicates
      deduplicationId: message.id,
    });

    return c.json({
      success: true,
      messageId: message.id,
      qstashMessageId: response.messageId,
    });
  } catch (error) {
    console.error('Publish error:', error);
    return c.json(
      { error: 'Failed to publish message', details: String(error) },
      500
    );
  }
});

/**
 * POST /receive
 *
 * QStash webhook endpoint. Receives messages and stores in agent inboxes.
 */
app.post('/receive', async (c) => {
  const env = c.env;

  try {
    // Verify QStash signature in production
    if (env.ENVIRONMENT !== 'development') {
      const signature = c.req.header('Upstash-Signature');
      if (!signature) {
        console.warn('Missing QStash signature');
        // In production, you'd verify the signature here
        // For now, we'll proceed but log it
      }
    }

    const body = await c.req.json();
    const message = validateMessage(body);

    if (!message) {
      return c.json({ error: 'Invalid message format' }, 400);
    }

    const redis = getRedis(env);
    const ttl = getTTL(message);
    const now = new Date();
    const expiresAt = new Date(now.getTime() + ttl * 1000).toISOString();

    // Create stored message
    const storedMessage: StoredMessage = {
      ...message,
      receivedAt: now.toISOString(),
      read: false,
      expiresAt,
    };

    // Determine target inboxes
    const targets: string[] = [];

    if (message.toAgents && message.toAgents.length > 0) {
      // Explicit targets
      targets.push(...message.toAgents.map(inboxKey));
    } else {
      // Store in session inbox for all agents to poll
      targets.push(sessionInboxKey(message.sessionId));
    }

    // Store message in each target inbox
    const pipeline = redis.pipeline();

    for (const target of targets) {
      // Add to list (newest first)
      pipeline.lpush(target, JSON.stringify(storedMessage));
      // Trim to keep inbox manageable (max 100 messages)
      pipeline.ltrim(target, 0, 99);
      // Set TTL on the inbox
      pipeline.expire(target, ttl);
    }

    await pipeline.exec();

    return c.json({
      success: true,
      messageId: message.id,
      deliveredTo: targets.length,
    });
  } catch (error) {
    console.error('Receive error:', error);
    return c.json(
      { error: 'Failed to process message', details: String(error) },
      500
    );
  }
});

/**
 * GET /poll/:agentId
 *
 * Poll inbox for messages. Returns unread messages.
 *
 * Query params:
 * - sessionId: Filter by session (required)
 * - limit: Max messages to return (default 10)
 * - markRead: Whether to mark messages as read (default true)
 */
app.get('/poll/:agentId', async (c) => {
  const env = c.env;
  const agentId = c.req.param('agentId');
  const sessionId = c.req.query('sessionId');
  const limit = parseInt(c.req.query('limit') || '10', 10);
  const markRead = c.req.query('markRead') !== 'false';

  if (!sessionId) {
    return c.json({ error: 'sessionId query parameter required' }, 400);
  }

  try {
    const redis = getRedis(env);

    // Check both agent-specific and session-wide inboxes
    const agentInbox = inboxKey(agentId);
    const sessionInbox = sessionInboxKey(sessionId);

    // Get messages from both inboxes
    const [agentMessages, sessionMessages] = await Promise.all([
      redis.lrange(agentInbox, 0, limit - 1),
      redis.lrange(sessionInbox, 0, limit - 1),
    ]);

    // Parse and deduplicate messages
    const seenIds = new Set<string>();
    const messages: StoredMessage[] = [];

    const parseMessages = (raw: unknown[]) => {
      for (const item of raw) {
        try {
          const msg: StoredMessage =
            typeof item === 'string' ? JSON.parse(item) : (item as StoredMessage);

          // Skip duplicates
          if (seenIds.has(msg.id)) continue;
          seenIds.add(msg.id);

          // Skip messages from self
          if (msg.fromAgent === agentId) continue;

          // Skip expired messages
          if (new Date(msg.expiresAt) < new Date()) continue;

          messages.push(msg);
        } catch {
          // Skip malformed messages
        }
      }
    };

    parseMessages(agentMessages as unknown[]);
    parseMessages(sessionMessages as unknown[]);

    // Sort by timestamp (newest first) and limit
    messages.sort(
      (a, b) =>
        new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );
    const result = messages.slice(0, limit);

    // Mark as read if requested (by removing from inbox)
    if (markRead && result.length > 0) {
      // For simplicity, we'll let messages naturally expire
      // A full implementation would track read state per agent
    }

    return c.json({
      messages: result,
      count: result.length,
      hasMore: messages.length > limit,
    });
  } catch (error) {
    console.error('Poll error:', error);
    return c.json(
      { error: 'Failed to poll messages', details: String(error) },
      500
    );
  }
});

/**
 * DELETE /clear/:agentId
 *
 * Clear an agent's inbox.
 */
app.delete('/clear/:agentId', async (c) => {
  const env = c.env;
  const agentId = c.req.param('agentId');

  try {
    const redis = getRedis(env);
    const key = inboxKey(agentId);

    await redis.del(key);

    return c.json({ success: true, cleared: agentId });
  } catch (error) {
    console.error('Clear error:', error);
    return c.json(
      { error: 'Failed to clear inbox', details: String(error) },
      500
    );
  }
});

/**
 * POST /broadcast
 *
 * Broadcast a message to all agents in a session.
 * Stores in session inbox for all to poll.
 */
app.post('/broadcast', async (c) => {
  const env = c.env;

  try {
    const body = await c.req.json();
    const message = validateMessage(body);

    if (!message) {
      return c.json({ error: 'Invalid message format' }, 400);
    }

    // Ensure no explicit targets (broadcast goes to all)
    message.toAgents = undefined;

    // Ensure message has ID
    if (!message.id) {
      message.id = generateMessageId();
    }

    const redis = getRedis(env);
    const ttl = getTTL(message);
    const now = new Date();
    const expiresAt = new Date(now.getTime() + ttl * 1000).toISOString();

    const storedMessage: StoredMessage = {
      ...message,
      receivedAt: now.toISOString(),
      read: false,
      expiresAt,
    };

    const key = sessionInboxKey(message.sessionId);

    // Store directly in session inbox
    await redis
      .pipeline()
      .lpush(key, JSON.stringify(storedMessage))
      .ltrim(key, 0, 99)
      .expire(key, ttl)
      .exec();

    return c.json({
      success: true,
      messageId: message.id,
      broadcast: true,
    });
  } catch (error) {
    console.error('Broadcast error:', error);
    return c.json(
      { error: 'Failed to broadcast message', details: String(error) },
      500
    );
  }
});

export default app;
