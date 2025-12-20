import { getRedis } from '../services/redis';
/**
 * Authentication Routes
 *
 * Part of Issue #129 (Auth Routes: Signup, Login, Sessions)
 * Parent: Epic #125 (User Signup & Billing)
 */

import { Hono } from 'hono';
import type {
  Env,
  Variables,
  UserData,
  SessionData,
  SignupRequest,
  LoginRequest,
  AuthResponse,
} from '../types';
import { createApiKey } from '../middleware/auth';
import { sendEmail, generateWelcomeEmail } from '../services/email';

const auth = new Hono<{ Bindings: Env; Variables: Variables }>();

// =============================================================================
// CONSTANTS
// =============================================================================

const SESSION_TTL_SECONDS = 7 * 24 * 60 * 60; // 7 days
const MIN_PASSWORD_LENGTH = 8;

// =============================================================================
// HELPERS
// =============================================================================

/**
 * Generate a random session token.
 */
function generateSessionToken(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(32));
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
}

/**
 * Generate a user ID.
 */
function generateUserId(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(12));
  return (
    'usr_' +
    Array.from(bytes)
      .map((b) => b.toString(16).padStart(2, '0'))
      .join('')
  );
}

/**
 * Hash a password using Web Crypto API (PBKDF2).
 * Note: In production, consider using Argon2id via wasm or external service.
 */
async function hashPassword(password: string): Promise<string> {
  const encoder = new TextEncoder();
  const salt = crypto.getRandomValues(new Uint8Array(16));

  const keyMaterial = await crypto.subtle.importKey(
    'raw',
    encoder.encode(password),
    'PBKDF2',
    false,
    ['deriveBits']
  );

  const hash = await crypto.subtle.deriveBits(
    {
      name: 'PBKDF2',
      salt,
      iterations: 100000,
      hash: 'SHA-256',
    },
    keyMaterial,
    256
  );

  // Format: algorithm$iterations$salt$hash
  const saltHex = Array.from(salt)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');
  const hashHex = Array.from(new Uint8Array(hash))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');

  return `pbkdf2$100000$${saltHex}$${hashHex}`;
}

/**
 * Verify a password against a hash.
 */
async function verifyPassword(password: string, storedHash: string): Promise<boolean> {
  const parts = storedHash.split('$');
  if (parts.length !== 4 || parts[0] !== 'pbkdf2') {
    return false;
  }

  const iterations = parseInt(parts[1], 10);
  const salt = new Uint8Array(
    parts[2].match(/.{2}/g)!.map((byte) => parseInt(byte, 16))
  );
  const expectedHash = parts[3];

  const encoder = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey(
    'raw',
    encoder.encode(password),
    'PBKDF2',
    false,
    ['deriveBits']
  );

  const hash = await crypto.subtle.deriveBits(
    {
      name: 'PBKDF2',
      salt,
      iterations,
      hash: 'SHA-256',
    },
    keyMaterial,
    256
  );

  const hashHex = Array.from(new Uint8Array(hash))
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('');

  return hashHex === expectedHash;
}

/**
 * Validate email format.
 */
function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Strip sensitive fields from user data.
 */
function sanitizeUser(user: UserData): Omit<UserData, 'passwordHash'> {
  const { passwordHash, ...safeUser } = user;
  return safeUser;
}

// =============================================================================
// ROUTES
// =============================================================================

/**
 * POST /v1/auth/signup
 *
 * Create a new user account.
 */
auth.post('/signup', async (c) => {
  const body = await c.req.json<SignupRequest>();

  // Validate input
  if (!body.email || !body.password) {
    return c.json({ error: 'Email and password are required' }, 400);
  }

  if (!isValidEmail(body.email)) {
    return c.json({ error: 'Invalid email format' }, 400);
  }

  if (body.password.length < MIN_PASSWORD_LENGTH) {
    return c.json(
      { error: `Password must be at least ${MIN_PASSWORD_LENGTH} characters` },
      400
    );
  }

  const email = body.email.toLowerCase().trim();

  // Get Redis client
  const redis = getRedis(c);

  // Check if email already exists
  const existingUserId = await redis.get<string>(`popkit:email:${email}`);
  if (existingUserId) {
    return c.json({ error: 'Email already registered' }, 409);
  }

  // Create user
  const userId = generateUserId();
  const now = new Date().toISOString();

  const user: UserData = {
    id: userId,
    email,
    passwordHash: await hashPassword(body.password),
    name: body.name,
    tier: 'free',
    createdAt: now,
    updatedAt: now,
  };

  // Store user as JSON string
  await redis.set(`popkit:user:${userId}`, JSON.stringify(user));

  // Create email -> userId index
  await redis.set(`popkit:email:${email}`, userId);

  // Create session
  const sessionToken = generateSessionToken();
  const session: SessionData = {
    userId,
    createdAt: now,
    expiresAt: new Date(Date.now() + SESSION_TTL_SECONDS * 1000).toISOString(),
  };
  await redis.set(`popkit:session:${sessionToken}`, JSON.stringify(session), {
    ex: SESSION_TTL_SECONDS,
  });

  // Create default API key
  const { key: apiKey } = await createApiKey(redis, userId, 'Default Key', 'free');

  // Send welcome email (non-blocking)
  if (c.env.RESEND_API_KEY) {
    const welcomeEmail = generateWelcomeEmail({
      email,
      apiKey,
      tier: body.plan || 'free',
    });
    sendEmail(c.env.RESEND_API_KEY, welcomeEmail).catch((err) => {
      console.error('Failed to send welcome email:', err);
    });
  }

  const response: AuthResponse = {
    user: sanitizeUser(user),
    sessionToken,
    apiKey,
  };

  return c.json(response, 201);
});

/**
 * POST /v1/auth/login
 *
 * Authenticate an existing user.
 */
auth.post('/login', async (c) => {
  const body = await c.req.json<LoginRequest>();

  // Validate input
  if (!body.email || !body.password) {
    return c.json({ error: 'Email and password are required' }, 400);
  }

  const email = body.email.toLowerCase().trim();

  // Get Redis client
  const redis = getRedis(c);

  // Look up user by email
  const userId = await redis.get<string>(`popkit:email:${email}`);
  if (!userId) {
    return c.json({ error: 'Invalid email or password' }, 401);
  }

  // Get user data
  const userJson = await redis.get<string>(`popkit:user:${userId}`);
  if (!userJson) {
    return c.json({ error: 'Invalid email or password' }, 401);
  }
  const user: UserData = JSON.parse(userJson);
  if (!user.passwordHash) {
    return c.json({ error: 'Invalid email or password' }, 401);
  }

  // Verify password
  const valid = await verifyPassword(body.password, user.passwordHash);
  if (!valid) {
    return c.json({ error: 'Invalid email or password' }, 401);
  }

  // Create session
  const sessionToken = generateSessionToken();
  const now = new Date().toISOString();
  const session: SessionData = {
    userId,
    createdAt: now,
    expiresAt: new Date(Date.now() + SESSION_TTL_SECONDS * 1000).toISOString(),
  };
  await redis.set(`popkit:session:${sessionToken}`, JSON.stringify(session), {
    ex: SESSION_TTL_SECONDS,
  });

  const response: AuthResponse = {
    user: sanitizeUser(user),
    sessionToken,
  };

  return c.json(response);
});

/**
 * POST /v1/auth/logout
 *
 * Invalidate a session.
 */
auth.post('/logout', async (c) => {
  const authHeader = c.req.header('Authorization');
  if (!authHeader) {
    return c.json({ error: 'No session to logout' }, 400);
  }

  const match = authHeader.match(/^Bearer (session_[a-zA-Z0-9]+|[a-f0-9]{64})$/);
  if (!match) {
    return c.json({ error: 'Invalid session format' }, 400);
  }

  const sessionToken = match[1];

  // Get Redis client
  const redis = getRedis(c);

  // Delete session
  await redis.del(`popkit:session:${sessionToken}`);

  return c.json({ success: true });
});

/**
 * GET /v1/auth/me
 *
 * Get current user from session.
 */
auth.get('/me', async (c) => {
  const authHeader = c.req.header('Authorization');
  if (!authHeader) {
    return c.json({ error: 'Authorization required' }, 401);
  }

  // Support both session tokens and API keys
  const sessionMatch = authHeader.match(/^Bearer ([a-f0-9]{64})$/);
  const apiKeyMatch = authHeader.match(/^Bearer (pk_(live|test)_[a-zA-Z0-9]+)$/);

  const redis = getRedis(c);

  let userId: string | null = null;

  if (sessionMatch) {
    // Session token auth
    const sessionToken = sessionMatch[1];
    const sessionJson = await redis.get<string>(`popkit:session:${sessionToken}`);
    if (!sessionJson) {
      return c.json({ error: 'Session expired or invalid' }, 401);
    }
    const session: SessionData = JSON.parse(sessionJson);
    userId = session.userId;
  } else if (apiKeyMatch) {
    // API key auth
    const apiKey = apiKeyMatch[1];
    const keyData = await redis.hget<string>('popkit:keys', apiKey);
    if (!keyData) {
      return c.json({ error: 'Invalid API key' }, 401);
    }
    const parsed = typeof keyData === 'string' ? JSON.parse(keyData) : keyData;
    userId = parsed.userId;
  } else {
    return c.json({ error: 'Invalid authorization format' }, 401);
  }

  if (!userId) {
    return c.json({ error: 'User not found' }, 404);
  }

  // Get user data
  const userJson = await redis.get<string>(`popkit:user:${userId}`);
  if (!userJson) {
    return c.json({ error: 'User not found' }, 404);
  }
  const user: UserData = JSON.parse(userJson);

  return c.json({ user: sanitizeUser(user) });
});

export default auth;
