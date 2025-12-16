# Upstash + GitHub Gist Integration Architecture

**Status**: Design Phase
**Date**: 2025-12-16
**Target**: v2.0 Implementation (Q1 2026+)
**Branch**: `claude/explore-gist-integration-URSHW`

---

## Overview

This document details how to integrate GitHub Gists with PopKit's existing **Upstash stack** (Redis + Vector + QStash) to create a **managed intelligence layer** for pattern discovery, team collaboration, and cross-project learning.

**Key Principle**: Users keep gists on GitHub (free, permanent). PopKit adds the AI/sync layer via Upstash.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        PopKit Plugin                            │
│                    (All Claude Code clients)                    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Tier 1: Local Layer (Offline-First)                      │  │
│  │ • ~/.popkit/gists.json (metadata cache)                  │  │
│  │ • /popkit:gist create (GitHub → local save)              │  │
│  │ • /popkit:gist list (query local cache)                  │  │
│  │ • /popkit:gist search (local keyword match)              │  │
│  └──────────────────────────────────────────────────────────┘  │
│         │                                                       │
│         ├─ hook: on_gist_create → trigger sync                │
│         ├─ hook: on_file_save → detect patterns               │
│         └─ hook: on_error → recommend patterns                │
└─────────┼───────────────────────────────────────────────────────┘
          │
          │ HTTP + User Auth Token
          ▼
┌─────────────────────────────────────────────────────────────────┐
│              PopKit Cloud API (Cloudflare Workers)              │
│              packages/cloud/src/index.ts                        │
│                                                                 │
│ ┌──────────────────────────────────────────────────────────┐   │
│ │ /api/gists/sync        - Store gist in Upstash          │   │
│ │ /api/gists/search      - Semantic search via Vector      │   │
│ │ /api/gists/list        - Paginated gist list            │   │
│ │ /api/gists/team/share  - Team library management         │   │
│ │ /api/gists/metrics     - Usage analytics                │   │
│ └──────────────────────────────────────────────────────────┘   │
│                      │                                          │
│                      ├─ Rate Limit Check (Redis)              │
│                      ├─ GitHub Auth Validation                │
│                      └─ Permission Validation                 │
└──────────┬───────────────────────────────┬────────────────────┘
           │                               │
    ┌──────▼─────────────┐        ┌────────▼────────────┐
    │ GitHub API         │        │ Upstash Services    │
    │                    │        │                     │
    │ • Read gist        │        │ ┌─────────────────┐ │
    │ • Webhooks         │        │ │ Redis (Cache)   │ │
    │ • Rate limiting    │        │ │ • Gist metadata │ │
    │ • Auth tokens      │        │ │ • Rate limits   │ │
    │                    │        │ │ • Team state    │ │
    └────────────────────┘        │ └─────────────────┘ │
                                  │                     │
                                  │ ┌─────────────────┐ │
                                  │ │ Vector (Search) │ │
                                  │ │ • Embeddings    │ │
                                  │ │ • Semantic idx  │ │
                                  │ │ • Fast queries  │ │
                                  │ │ • Metadata      │ │
                                  │ └─────────────────┘ │
                                  │                     │
                                  │ ┌─────────────────┐ │
                                  │ │ QStash (Jobs)   │ │
                                  │ │ • Embed gists   │ │
                                  │ │ • Sync webhooks │ │
                                  │ │ • Cleanup tasks │ │
                                  │ └─────────────────┘ │
                                  └─────────────────────┘
```

---

## Part 1: Data Model

### Gist Entity in Upstash

**Redis Key Structure:**
```redis
gists:{gistId}                    # Main gist document (Hash)
gists:{userId}:list               # User's gist IDs (Sorted Set, by timestamp)
gists:{teamId}:list               # Team's shared gists (Sorted Set)
gist:metadata:{gistId}            # Quick metadata lookup
gist:search:vector:{gistId}        # Vector embedding ID (managed by Vector)
team:members:{teamId}              # Team members (Set)
```

### Gist Document Schema (Redis Hash)

```json
{
  "gistId": "abc123",
  "githubUrl": "https://gist.github.com/user/abc123",
  "rawUrl": "https://gist.githubusercontent.com/user/abc123/raw/...",
  "userId": "github-user-id",
  "ownerName": "GitHub username",
  "title": "React Hook Pattern",
  "description": "Custom hook for fetching data with caching",
  "language": "typescript",
  "content": "<full file content>",
  "contentHash": "sha256-hash",  # For change detection
  "visibility": "secret|public",  # Private or public gist
  "tags": ["react", "hooks", "fetch", "cache"],
  "confidence": 85,  # PopKit quality score (0-100)
  "usage_count": 23,  # Times used/copied
  "success_rate": 0.92,  # Successful uses vs failed
  "createdAt": "2025-12-16T10:00:00Z",
  "updatedAt": "2025-12-16T10:00:00Z",
  "syncedAt": "2025-12-16T10:05:00Z",
  "category": "patterns|templates|utilities",
  "relatedGists": ["gist-id-2", "gist-id-3"],  # Cross-references
  "vectorId": "vector-embedding-id",
  "teamId": "team-123",  # Null for personal
  "isPublic": false  # For discovery
}
```

### Vector Embeddings (Upstash Vector)

**Vector ID**: `vector:gist:{gistId}`

```json
{
  "id": "vector:gist:abc123",
  "values": [0.123, 0.456, ...],  # 1024-dim embeddings (e.g., Voyage AI)
  "metadata": {
    "gistId": "abc123",
    "title": "React Hook Pattern",
    "language": "typescript",
    "category": "patterns",
    "confidence": 85,
    "tags": "react,hooks,fetch,cache"
  }
}
```

---

## Part 2: Redis Storage Strategy

### Cache Layers

**Layer 1: Hot Cache (Redis String/Hash)**
- **TTL**: 24 hours (short-lived, frequent access)
- **Keys**: Recent gist metadata, popular patterns
- **Purpose**: Fast lookups without GitHub API calls
- **Size**: ~10KB per gist (metadata only)

```redis
# Example
SET gist:metadata:abc123 '{"title": "...","confidence": 85, ...}' EX 86400
ZADD gists:user:u123:list 1702800000 abc123 def456 ghi789
```

**Layer 2: Warm Cache (Redis Hash)**
- **TTL**: 7 days
- **Keys**: Full gist content, used in searches
- **Purpose**: Semantic search without re-fetching
- **Size**: ~50KB per gist (full content)

```redis
HSET gist:content:abc123 title "..." description "..." content "..." ttl 604800
```

**Layer 3: State (Redis Streams)**
- **TTL**: Permanent (until user deletes)
- **Keys**: Sync state, team permissions, usage metrics
- **Purpose**: Durable state for team collaboration
- **Usage**: Redis Streams for event sourcing

```redis
XADD gist:events:abc123 * action:synced timestamp:2025-12-16T10:05:00Z source:github
XADD team:members:team123 * userId:u1 action:added timestamp:...
```

### Rate Limiting with Redis

**Key Structure:**
```redis
ratelimit:{userId}:gists:month:2025-12    # Monthly gist quota (Incr)
ratelimit:{userId}:api:minute:2025-12-16-10-05  # API calls per minute
ratelimit:{teamId}:usage:day:2025-12-16   # Team daily quota
```

**Example**:
```python
# In packages/cloud/src/rate_limits.ts
async function checkGistQuota(userId, tier) {
  const key = `ratelimit:${userId}:gists:month:${getCurrentMonth()}`;
  const current = await redis.incr(key);
  const limit = RATE_LIMITS[tier].gists_per_month;

  if (current > limit) {
    return { allowed: false, current, limit };
  }

  // Reset monthly counter
  if (current === 1) {
    await redis.expire(key, 30 * 24 * 60 * 60); // 30 days
  }

  return { allowed: true, current, limit };
}
```

---

## Part 3: Vector Search Integration

### Embedding Strategy

**When to Generate Embeddings:**
1. On gist creation (`POST /api/gists/sync`)
2. On gist update (content changes)
3. Batch re-embedding (weekly optimization)
4. Never on search (use pre-computed vectors)

**Embedding Model**: Voyage AI (recommended)
```python
# packages/cloud/src/embeddings.ts
import Voyage from "@voyageai/voyage-ai";

const client = new Voyage({
  apiKey: env.VOYAGE_API_KEY,
});

async function embedGist(gistId: string, content: string) {
  // Combine title + description + content for richer embeddings
  const text = `${gist.title}\n\n${gist.description}\n\n${content}`;

  // Truncate to 4000 tokens for cost efficiency
  const truncated = text.substring(0, 12000);

  const response = await client.embed({
    model: "voyage-3",
    input: [truncated],
  });

  // Store in Upstash Vector
  await vector.upsert([{
    id: `vector:gist:${gistId}`,
    values: response.embeddings[0],
    metadata: {
      gistId,
      title: gist.title,
      language: gist.language,
      category: gist.category,
      confidence: gist.confidence,
      tags: gist.tags.join(","),
    }
  }]);

  return response.embeddings[0];
}
```

### Search Implementation

**Query Types:**

1. **Semantic Search** (Vector)
   ```typescript
   // "I need a function to cache async data"
   POST /api/gists/search
   {
     "query": "cache async fetch data",
     "type": "semantic",
     "filters": {
       "language": "typescript",
       "confidence": { "$gte": 80 },
       "tags": ["react", "hooks"]  // Optional
     },
     "topK": 10
   }
   ```

2. **Keyword Search** (Redis HGETALL + filter)
   ```typescript
   // Fast for simple searches
   POST /api/gists/search
   {
     "query": "react hook",
     "type": "keyword",
     "fields": ["title", "description", "tags"],
     "limit": 10
   }
   ```

3. **Filter Search** (Redis keys + pattern)
   ```typescript
   // "Show me all Python utility patterns"
   POST /api/gists/search
   {
     "filters": {
       "language": "python",
       "category": "utilities",
       "confidence": { "$gte": 75 }
     },
     "sort": "usage_count",
     "limit": 20
   }
   ```

**Implementation**:
```typescript
// packages/cloud/src/search.ts
async function searchGists(query: SearchQuery, userId: string) {
  const userTier = await getUserTier(userId);

  if (query.type === "semantic") {
    // Generate embedding for query
    const queryEmbedding = await voyageClient.embed({
      input: [query.query],
      model: "voyage-3"
    });

    // Vector semantic search
    const results = await vector.query(
      queryEmbedding.embeddings[0],
      {
        topK: query.topK || 10,
        filter: buildVectorFilter(query.filters, userId)
      }
    );

    return results.map(r => ({
      gistId: r.metadata.gistId,
      score: r.score,  // Cosine similarity
      ...r.metadata
    }));
  } else if (query.type === "keyword") {
    // Fast keyword search
    return keywordSearch(query, userId);
  }
}

// Filter builder for privacy (only user's gists + shared)
function buildVectorFilter(filters: object, userId: string) {
  return {
    "$and": [
      {
        "$or": [
          { "metadata.userId": userId },  // My gists
          { "metadata.isPublic": true },  // Public gists
          { "metadata.teamId": { "$in": userTeams } }  // Team gists
        ]
      },
      filters  // User-provided filters
    ]
  };
}
```

---

## Part 4: Cloud API Endpoints

### Authentication

All endpoints require GitHub token validation:
```typescript
// Middleware: packages/cloud/src/auth.ts
async function validateGitHubToken(req: Request) {
  const token = req.headers.authorization?.replace("Bearer ", "");

  if (!token) {
    return { valid: false, error: "Missing auth token" };
  }

  // Validate token against GitHub API
  const user = await github.getUser(token);
  return { valid: true, userId: user.id, username: user.login, token };
}
```

### Endpoint 1: Sync Gist

```typescript
POST /api/gists/sync

Request:
{
  "gistId": "abc123",
  "content": "...",
  "title": "React Hook Pattern",
  "description": "Custom hook for data fetching",
  "language": "typescript",
  "tags": ["react", "hooks", "fetch"],
  "visibility": "secret|public",
  "teamId": "team-123" (optional)
}

Response:
{
  "gistId": "abc123",
  "synced": true,
  "vectorId": "vector:gist:abc123",
  "cached": true,
  "message": "Gist synced and indexed for search"
}

Rate Limit: 10 per minute (free), 100 per minute (pro)
Quota: 100 per month (free), unlimited (pro)
```

**Implementation**:
```typescript
// packages/cloud/src/routes/gists.ts
async function syncGist(req: Request, userId: string) {
  // 1. Check rate limits
  const canSync = await checkGistQuota(userId, userTier);
  if (!canSync.allowed) {
    return json({
      error: "Gist quota exceeded",
      current: canSync.current,
      limit: canSync.limit
    }, { status: 429 });
  }

  const { gistId, content, title, description, language, tags, visibility, teamId } = req.json();

  // 2. Validate GitHub gist ownership
  const gist = await github.getGist(gistId, userToken);
  if (gist.owner.id !== userId && !isTeamMember(teamId, userId)) {
    return json({ error: "Unauthorized" }, { status: 403 });
  }

  // 3. Store in Redis (cache)
  const gistData = {
    gistId,
    userId,
    title,
    description,
    language,
    tags,
    visibility,
    content,
    contentHash: sha256(content),
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    syncedAt: new Date().toISOString(),
    confidence: calculateConfidence(content),
    vectorId: null,
    teamId: teamId || null,
    isPublic: visibility === "public",
  };

  await redis.hset(`gist:${gistId}`, gistData);
  await redis.expire(`gist:${gistId}`, 7 * 24 * 60 * 60); // 7 days

  // 4. Queue embedding job (async)
  await qstash.publishJSON({
    url: `${env.API_URL}/jobs/embed-gist`,
    body: { gistId, content },
    headers: { authorization: `Bearer ${env.INTERNAL_TOKEN}` }
  });

  // 5. Return success
  return json({
    gistId,
    synced: true,
    cached: true,
    message: "Gist synced and queued for indexing"
  });
}
```

### Endpoint 2: Search Gists

```typescript
POST /api/gists/search

Request:
{
  "query": "cache async fetch",
  "type": "semantic|keyword",  // Default: semantic
  "filters": {
    "language": "typescript",
    "category": "patterns",
    "confidence": { "$gte": 80 },
    "tags": ["react", "hooks"]
  },
  "topK": 10,
  "offset": 0
}

Response:
{
  "results": [
    {
      "gistId": "abc123",
      "title": "React Hook Pattern",
      "description": "...",
      "language": "typescript",
      "score": 0.94,  // Similarity score
      "confidence": 85,
      "tags": ["react", "hooks", "fetch"],
      "usage_count": 23,
      "success_rate": 0.92,
      "url": "https://gist.github.com/..."
    }
  ],
  "total": 142,
  "took": 45  // milliseconds
}

Rate Limit: 50 per day (free), 5000 per day (pro)
Cost: ~0.1 cents per search (Vector API)
```

**Implementation**:
```typescript
async function searchGists(req: Request, userId: string) {
  const { query, type = "semantic", filters, topK = 10, offset = 0 } = req.json();

  // 1. Check rate limits
  const searches = await redis.incr(`ratelimit:${userId}:search:day:${today}`);
  const limit = RATE_LIMITS[userTier].search_per_day;

  if (searches > limit) {
    return json({
      error: "Search limit exceeded",
      current: searches,
      limit
    }, { status: 429 });
  }

  // 2. Execute search
  let results;
  if (type === "semantic") {
    // Generate embedding
    const embedding = await voyageClient.embed({
      input: [query],
      model: "voyage-3"
    });

    // Query Vector DB
    results = await vector.query(embedding.embeddings[0], {
      topK,
      filter: buildPrivacyFilter(userId, filters)
    });
  } else {
    // Keyword search
    results = await keywordSearch(query, filters, userId, topK, offset);
  }

  return json({
    results: results.map(r => ({
      gistId: r.metadata.gistId,
      score: r.score,
      ...r.metadata
    })),
    total: results.length,
    took: Date.now() - startTime
  });
}
```

### Endpoint 3: Team Share

```typescript
POST /api/gists/team/share

Request:
{
  "gistId": "abc123",
  "teamId": "team-123",
  "action": "share|unshare|permission"
}

Response:
{
  "gistId": "abc123",
  "teamId": "team-123",
  "shared": true,
  "members": 5,
  "message": "Gist shared with team"
}

Rate Limit: Unlimited (pro/team only)
Cost: Storage in Redis Streams
```

**Implementation**:
```typescript
async function shareWithTeam(req: Request, userId: string) {
  const { gistId, teamId, action } = req.json();

  // 1. Verify user is team admin
  const isAdmin = await isTeamAdmin(teamId, userId);
  if (!isAdmin) {
    return json({ error: "Only team admins can share" }, { status: 403 });
  }

  // 2. Get gist
  const gist = await redis.hgetall(`gist:${gistId}`);
  if (!gist) {
    return json({ error: "Gist not found" }, { status: 404 });
  }

  // 3. Update gist teamId
  if (action === "share") {
    gist.teamId = teamId;
    gist.updatedAt = new Date().toISOString();
    await redis.hset(`gist:${gistId}`, gist);

    // Record event
    await redis.xadd(`team:events:${teamId}`, "*", {
      gistId,
      action: "gist_shared",
      sharedBy: userId,
      timestamp: new Date().toISOString()
    });
  }

  // 4. Return team members who now have access
  const members = await redis.smembers(`team:members:${teamId}`);

  return json({
    gistId,
    teamId,
    shared: true,
    members: members.length,
    message: `Gist shared with ${members.length} team members`
  });
}
```

---

## Part 5: Hook Integration (Plugin Side)

### Hook: On Gist Create

```python
# packages/plugin/hooks/on-gist-create.py
#!/usr/bin/env python3

import json
import os
import subprocess
from datetime import datetime

def handle_gist_created(event):
    """
    Triggered when user creates a gist via /popkit:gist create
    Syncs to cloud + generates embeddings
    """
    gist_id = event.get("gistId")
    gist_url = event.get("githubUrl")
    content = event.get("content")

    # 1. Store locally
    home = os.path.expanduser("~")
    gists_file = f"{home}/.popkit/gists.json"

    if not os.path.exists(gists_file):
        gists = []
    else:
        with open(gists_file) as f:
            gists = json.load(f)

    gists.append({
        "gistId": gist_id,
        "url": gist_url,
        "createdAt": datetime.now().isoformat(),
        "synced": False
    })

    with open(gists_file, "w") as f:
        json.dump(gists, f, indent=2)

    # 2. If online, sync to cloud
    token = os.getenv("POPKIT_CLOUD_TOKEN")
    if token:
        sync_gist_to_cloud(gist_id, content, token)

    return { "success": True, "synced": bool(token) }

def sync_gist_to_cloud(gist_id, content, token):
    """Push gist to PopKit Cloud for semantic indexing"""
    api_url = "https://api.thehouseofdeals.com/api/gists/sync"

    response = subprocess.run([
        "curl", "-X", "POST", api_url,
        "-H", f"Authorization: Bearer {token}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({
            "gistId": gist_id,
            "content": content,
            "syncedAt": datetime.now().isoformat()
        })
    ], capture_output=True, text=True)

    return json.loads(response.stdout)

# Read stdin
stdin_data = json.load(sys.stdin)
result = handle_gist_created(stdin_data)
json.dump(result, sys.stdout)
```

### Hook: On Error (Pattern Recommendation)

```python
# packages/plugin/hooks/on-error.py
#!/usr/bin/env python3

def handle_error(event):
    """
    When error occurs, check if any saved patterns could help
    """
    error_message = event.get("message")
    error_type = event.get("type")
    file_language = event.get("language")

    # 1. Check local gists first (offline)
    relevant_local = search_local_gists(error_message, file_language)

    if relevant_local:
        return {
            "suggestion": "I found patterns that might help:",
            "gists": relevant_local,
            "source": "local"
        }

    # 2. If online, search cloud
    token = os.getenv("POPKIT_CLOUD_TOKEN")
    if token:
        relevant_cloud = search_cloud_gists(error_message, file_language, token)
        if relevant_cloud:
            return {
                "suggestion": "Found patterns from your pattern library:",
                "gists": relevant_cloud,
                "source": "cloud"
            }

    return { "suggestion": None }

def search_local_gists(query, language):
    """Full-text search in local gists"""
    # Implementation: read ~/.popkit/gists.json, keyword match
    pass

def search_cloud_gists(query, language, token):
    """Semantic search via cloud API"""
    # Implementation: POST /api/gists/search
    pass
```

---

## Part 6: Rate Limiting & Monetization

### Free Tier

```
Gist Storage:        100 per month
Search Requests:     50 per day
API Calls:          10 per minute
Semantic Search:    NO (use local/keyword)
Team Sharing:       NO (personal only)
Storage Duration:   30 days
```

### Pro Tier ($20/month)

```
Gist Storage:        10,000 per month (unlimited)
Search Requests:     5,000 per day
API Calls:          100 per minute
Semantic Search:    YES (Upstash Vector)
Team Sharing:       YES (up to 5 people)
Storage Duration:   Unlimited
Analytics:          Basic usage stats
```

### Team Tier ($100/month + $10/user)

```
Gist Storage:        Unlimited
Search Requests:     Unlimited
API Calls:          1,000 per minute
Semantic Search:    YES (full power)
Team Sharing:       YES (unlimited people)
Storage Duration:   Unlimited
Analytics:          Advanced team insights
Audit Logs:         Full activity history
```

**Implementation**:
```typescript
// packages/cloud/src/rate_limits.ts

const RATE_LIMITS = {
  free: {
    gists_per_month: 100,
    search_per_day: 50,
    api_calls_per_minute: 10,
    has_semantic_search: false,
    has_team_sharing: false,
  },
  pro: {
    gists_per_month: 10000,
    search_per_day: 5000,
    api_calls_per_minute: 100,
    has_semantic_search: true,
    has_team_sharing: true,
    max_team_members: 5,
  },
  team: {
    gists_per_month: -1,  // unlimited
    search_per_day: -1,
    api_calls_per_minute: 1000,
    has_semantic_search: true,
    has_team_sharing: true,
    max_team_members: -1,
  }
};

async function enforceRateLimit(userId: string, action: string) {
  const tier = await getUserTier(userId);
  const limit = RATE_LIMITS[tier][action];

  if (tier === "free" && action === "semantic_search") {
    return { allowed: false, reason: "Upgrade to Pro for semantic search" };
  }

  // Check quota
  const current = await incrementQuota(userId, action);
  if (current > limit && limit > 0) {
    return { allowed: false, current, limit };
  }

  return { allowed: true };
}
```

---

## Part 7: Upstash Integration Checklist

### Redis Configuration

```bash
# Set these secrets in Cloudflare Wrangler
wrangler secret put UPSTASH_REDIS_REST_URL
# https://[your-id].upstash.io

wrangler secret put UPSTASH_REDIS_REST_TOKEN
# [your-token]
```

**Redis client for Cloudflare Workers**:
```typescript
// packages/cloud/src/redis.ts
import { Redis } from "@upstash/redis";

export const redis = new Redis({
  url: env.UPSTASH_REDIS_REST_URL,
  token: env.UPSTASH_REDIS_REST_TOKEN,
});

// Usage:
await redis.hset(`gist:${gistId}`, gistData);
await redis.incr(`ratelimit:${userId}:gists:month:${month}`);
```

### Vector Configuration

```bash
wrangler secret put UPSTASH_VECTOR_REST_URL
# https://[your-id]-vector.upstash.io

wrangler secret put UPSTASH_VECTOR_REST_TOKEN
# [your-token]

# Optional: Voyage AI for embeddings
wrangler secret put VOYAGE_API_KEY
# [your-voyage-api-key]
```

**Vector client for Cloudflare Workers**:
```typescript
// packages/cloud/src/vector.ts
import { Index } from "@upstash/vector";
import Voyage from "@voyageai/voyage-ai";

export const vector = new Index({
  url: env.UPSTASH_VECTOR_REST_URL,
  token: env.UPSTASH_VECTOR_REST_TOKEN,
});

export const voyage = new Voyage({
  apiKey: env.VOYAGE_API_KEY,
});

// Usage:
const embedding = await voyage.embed({
  input: [content],
  model: "voyage-3"
});

await vector.upsert([{
  id: `vector:gist:${gistId}`,
  values: embedding.embeddings[0],
  metadata: { gistId, title, language, tags: tags.join(",") }
}]);
```

### QStash Configuration (Background Jobs)

```bash
wrangler secret put QSTASH_TOKEN
# [your-qstash-token]
```

**QStash for async embedding**:
```typescript
// packages/cloud/src/jobs.ts
import { Client } from "@upstash/qstash";

const qstash = new Client({
  token: env.QSTASH_TOKEN,
});

// Schedule embedding job when gist is synced
await qstash.publishJSON({
  url: `${env.API_URL}/jobs/embed-gist`,
  body: { gistId, content },
  headers: { authorization: `Bearer ${env.INTERNAL_TOKEN}` }
});

// Job handler
export async function embedGistJob(req: Request) {
  const { gistId, content } = await req.json();

  // 1. Generate embedding
  const embedding = await voyage.embed({ input: [content] });

  // 2. Store in Vector DB
  await vector.upsert([{
    id: `vector:gist:${gistId}`,
    values: embedding.embeddings[0],
    metadata: { gistId }
  }]);

  return json({ success: true });
}
```

---

## Part 8: Cost Analysis

### Monthly Cost Estimate (1000 users, 10K gists)

| Service | Usage | Cost |
|---------|-------|------|
| **Upstash Redis** | 10GB storage, 1M reads/month | $120 |
| **Upstash Vector** | 10K vectors, 50K searches/month | $150 |
| **Upstash QStash** | 500 jobs/month | $5 |
| **Voyage AI Embeddings** | 1000 embeddings/month @ $0.01/1K | $10 |
| **Cloudflare Workers** | 10M requests/month | $50 |
| **GitHub API** | Included (webhooks, API calls) | $0 |
| **Total** | | **~$335/month** |

**Revenue Model** (assuming 2% free → pro conversion):
- 1000 free users → 20 pro @ $20/month = $400/month
- 2 team plans @ $100/month = $200/month
- **Total revenue**: $600/month → **Net profit: $265/month**

---

## Part 9: Implementation Timeline

### v2.0 Phase 1: Cloud Backend (4 weeks)

**Week 1:**
- [ ] Create `/packages/cloud/routes/gists.ts`
- [ ] Implement Redis data model
- [ ] Add rate limiting logic

**Week 2:**
- [ ] Integrate Upstash Vector
- [ ] Implement embedding pipeline (QStash job)
- [ ] Build search endpoints

**Week 3:**
- [ ] Add team sharing features
- [ ] Implement privacy filters
- [ ] Add usage analytics

**Week 4:**
- [ ] Load testing & optimization
- [ ] Webhook integration (GitHub)
- [ ] Error handling & edge cases

### v2.0 Phase 2: Feature Expansion (3 weeks)

**Week 5:**
- [ ] Hook system improvements (plugin-side)
- [ ] Auto-pattern detection
- [ ] Confidence scoring

**Week 6:**
- [ ] Dashboard/analytics UI
- [ ] Pattern recommendations
- [ ] Team collaboration features

**Week 7:**
- [ ] Performance optimization
- [ ] Documentation
- [ ] Beta testing

---

## Summary

This architecture provides:

1. **Three-Tier Caching**: Local (offline) → Redis (hot) → Vector (intelligent search)
2. **Monetization-Ready**: Rate limits enforced at cloud API level
3. **Team-Friendly**: Redis Streams for sync, permissions-based access
4. **Scalable**: Upstash handles 10K+ gists without infrastructure cost
5. **Intelligent**: Semantic search via Vector embeddings
6. **Privacy-First**: GitHub tokens managed by users, cloud stores only metadata + anonymized embeddings

**Next Steps:**
1. Finalize v1.0 quick wins (local-only gist skills)
2. Design cloud API contract (endpoints, auth, rate limits)
3. Prototype Upstash integration in staging environment
4. Build team collaboration features
5. Launch v2.0 with semantic search and monetization

