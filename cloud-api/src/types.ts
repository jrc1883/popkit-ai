/**
 * PopKit Cloud API Types
 *
 * Part of Issue #69 (API Gateway & Authentication)
 */

export type Tier = 'free' | 'pro' | 'team';

export interface ApiKeyData {
  id: string;
  userId: string;
  tier: Tier;
  name: string;
  createdAt: string;
  lastUsedAt?: string;
}

export interface UserData {
  id: string;
  githubId?: string;
  githubUsername?: string;
  email?: string;
  tier: Tier;
  createdAt: string;
}

export interface UsageData {
  commandsToday: number;
  bytesSent: number;
  bytesReceived: number;
  lastReset: string;
}

export interface RateLimitResult {
  exceeded: boolean;
  remaining: number;
  reset: number;
}

export interface Env {
  UPSTASH_REDIS_REST_URL: string;
  UPSTASH_REDIS_REST_TOKEN: string;
  ENVIRONMENT: string;
}

export interface Variables {
  apiKey?: ApiKeyData;
  user?: UserData;
}
