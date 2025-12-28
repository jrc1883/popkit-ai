# PopKit Cloud - Environment Variable Loading Guide

> **Part of Epic #528**: Workspace-Level Environment Variable Management
> **Migration Phase**: 3.1 (Pilot App)
> **Technology**: Cloudflare Workers + Wrangler CLI

---

## Quick Start

### 1. Copy the Template

```bash
cd apps/popkit/packages/cloud
cp .dev.vars.template .dev.vars
```

### 2. Fill in Your Upstash Credentials

Edit `.dev.vars` with your actual values:

```bash
# Get from https://console.upstash.com/redis
UPSTASH_REDIS_REST_URL=https://YOUR-INSTANCE.upstash.io
UPSTASH_REDIS_REST_TOKEN=YOUR_TOKEN_HERE

# Get from https://console.upstash.com/vector
UPSTASH_VECTOR_REST_URL=https://YOUR-VECTOR-DB.upstash.io
UPSTASH_VECTOR_REST_TOKEN=YOUR_TOKEN_HERE

# (Optional) Get from https://console.upstash.com/qstash
QSTASH_TOKEN=YOUR_QSTASH_TOKEN_HERE
```

### 3. Start Development Server

```bash
pnpm dev
# OR: wrangler dev
```

---

## Environment Variable Hierarchy

Cloudflare Workers uses a different loading pattern than traditional Node.js apps:

### Loading Order (Last Wins)

1. **`wrangler.toml` [vars]** - Committed defaults (lowest priority)
2. **`.dev.vars`** - Local development secrets (gitignored, **highest priority** for local)
3. **`wrangler secret`** - Production secrets (encrypted, **highest priority** for deployed)

### Why Different from Other Apps?

**Node.js Apps** (like OPTIMUS, AIProxy):
- Use `dotenv` to load `.env` files explicitly
- Load multiple files in sequence (workspace → app)
- Process.env accessible immediately

**Cloudflare Workers** (PopKit Cloud):
- Wrangler CLI handles environment loading automatically
- No `dotenv` package (runs in V8 isolates, not Node.js)
- Environment accessed via `env` parameter in handlers

---

## File Purposes

| File | Purpose | Committed? | Contains |
|------|---------|------------|----------|
| `wrangler.toml` | Worker configuration | ✅ Yes | Public config (ports, routes, KV bindings) |
| `wrangler.toml [vars]` | Non-sensitive defaults | ✅ Yes | ENVIRONMENT=production, rate limits |
| `.env.defaults` | App metadata | ✅ Yes | APP_NAME, APP_VERSION, feature flags |
| `.dev.vars.template` | Template for secrets | ✅ Yes | Documentation of required variables |
| `.dev.vars` | **Local dev secrets** | ❌ No | Your actual Upstash credentials |

---

## Required Variables

### Upstash Redis (REQUIRED)

**Purpose**: Pattern storage, Power Mode coordination, inter-agent messaging

```bash
UPSTASH_REDIS_REST_URL=https://YOUR-INSTANCE.upstash.io
UPSTASH_REDIS_REST_TOKEN=AXF...YOUR_TOKEN
```

**Get from**: [console.upstash.com/redis](https://console.upstash.com/redis)
**Free Tier**: 10,000 commands/day

### Upstash Vector (REQUIRED for semantic search)

**Purpose**: Semantic agent search, pattern matching, embeddings

```bash
UPSTASH_VECTOR_REST_URL=https://YOUR-VECTOR-DB.upstash.io
UPSTASH_VECTOR_REST_TOKEN=eyJ...YOUR_TOKEN
```

**Get from**: [console.upstash.com/vector](https://console.upstash.com/vector)
**Free Tier**: 10,000 queries/day
**Related**: Issue #101 - Semantic Agent Discovery

### QStash (OPTIONAL - for durable workflows)

**Purpose**: Scheduled jobs, durable workflows, async task execution

```bash
QSTASH_TOKEN=eyJ...YOUR_TOKEN
```

**Get from**: [console.upstash.com/qstash](https://console.upstash.com/qstash)
**Free Tier**: 100 messages/day
**Related**: Issue #103 - Durable Workflow System

---

## Accessing Variables in Code

### In Request Handlers

```typescript
export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    // Access environment variables via env parameter
    const redisUrl = env.UPSTASH_REDIS_REST_URL;
    const redisToken = env.UPSTASH_REDIS_REST_TOKEN;

    // Feature flags from .env.defaults
    const semanticSearchEnabled = env.FEATURE_SEMANTIC_SEARCH === 'true';

    // ...
  }
}
```

### In Durable Objects

```typescript
export class MyDurableObject {
  constructor(private state: DurableObjectState, private env: Env) {}

  async fetch(request: Request) {
    // Access via this.env
    const vectorUrl = this.env.UPSTASH_VECTOR_REST_URL;
    // ...
  }
}
```

---

## Development Workflow

### Local Development

```bash
cd apps/popkit/packages/cloud

# 1. Install dependencies
pnpm install

# 2. Copy env template
cp .dev.vars.template .dev.vars

# 3. Fill in credentials (edit .dev.vars)

# 4. Start dev server
pnpm dev
```

**Wrangler automatically loads `.dev.vars`** - no code changes needed!

### Testing

```bash
# With local server running on :8787
curl http://localhost:8787/health

# Test Redis connection
curl http://localhost:8787/api/pattern-storage/test

# Test Vector search
curl http://localhost:8787/api/semantic-search/test
```

---

## Production Deployment

### DO NOT commit `.dev.vars`!

It's already in `.gitignore`:

```gitignore
.dev.vars
.env
.env.local
```

### Setting Production Secrets

Use `wrangler secret put` to set encrypted secrets:

```bash
cd apps/popkit/packages/cloud

# Set Redis credentials
wrangler secret put UPSTASH_REDIS_REST_URL
# Paste value when prompted

wrangler secret put UPSTASH_REDIS_REST_TOKEN
# Paste value when prompted

# Set Vector credentials
wrangler secret put UPSTASH_VECTOR_REST_URL
wrangler secret put UPSTASH_VECTOR_REST_TOKEN

# (Optional) Set QStash token
wrangler secret put QSTASH_TOKEN
```

Secrets are:
- ✅ Encrypted at rest
- ✅ Never appear in logs
- ✅ Scoped to specific Worker
- ✅ Managed via Cloudflare dashboard

### Deploy

```bash
wrangler deploy
```

---

## Security Best Practices

### 1. Separate Databases by Environment

Create different Upstash databases for each environment:

| Environment | Redis DB | Vector DB | QStash |
|-------------|----------|-----------|--------|
| **Development** | `popkit-dev` | `popkit-vector-dev` | Shared (free tier) |
| **Staging** | `popkit-staging` | `popkit-vector-staging` | Shared |
| **Production** | `popkit-prod` | `popkit-vector-prod` | Dedicated |

### 2. Rotate Tokens Regularly

- Upstash allows generating new tokens
- Update `.dev.vars` locally
- Update `wrangler secret` for production

### 3. Enable IP Whitelisting (Production)

In Upstash console:
- Go to your database → Settings → Security
- Add Cloudflare Workers IPs
- See: [developers.cloudflare.com/workers/platform/limits](https://developers.cloudflare.com/workers/platform/limits)

### 4. Monitor Usage

Track usage at:
- [console.upstash.com](https://console.upstash.com)
- Cloudflare dashboard → Workers → Analytics

---

## Troubleshooting

### Error: "UPSTASH_REDIS_REST_URL is not defined"

**Problem**: Missing environment variable

**Solution**:
1. Check `.dev.vars` exists and contains the variable
2. Restart `wrangler dev` (changes require restart)
3. Verify variable name matches exactly (case-sensitive)

### Error: "Failed to connect to Redis"

**Problem**: Invalid credentials or network issue

**Solution**:
1. Verify credentials at [console.upstash.com/redis](https://console.upstash.com/redis)
2. Test connection directly:
   ```bash
   curl $UPSTASH_REDIS_REST_URL/get/test \
     -H "Authorization: Bearer $UPSTASH_REDIS_REST_TOKEN"
   ```
3. Check Upstash database status (not paused)

### Wrangler dev not loading `.dev.vars`

**Problem**: File exists but variables not accessible

**Solution**:
1. Ensure file is named exactly `.dev.vars` (not `.dev.vars.txt`)
2. Check file is in same directory as `wrangler.toml`
3. Restart `wrangler dev`
4. Verify with: `console.log(Object.keys(env))`

### Variables work locally but not in production

**Problem**: Forgot to set wrangler secrets

**Solution**:
```bash
wrangler secret put UPSTASH_REDIS_REST_URL
wrangler secret put UPSTASH_REDIS_REST_TOKEN
wrangler secret put UPSTASH_VECTOR_REST_URL
wrangler secret put UPSTASH_VECTOR_REST_TOKEN
```

---

## Comparison: Node.js vs Cloudflare Workers

| Aspect | Node.js Apps (OPTIMUS, AIProxy) | Cloudflare Workers (PopKit Cloud) |
|--------|--------------------------------|-----------------------------------|
| **Runtime** | Node.js (full) | V8 Isolates (lightweight) |
| **Env Loading** | `dotenv` package, explicit | Wrangler CLI, automatic |
| **Local Dev** | `.env.local` | `.dev.vars` |
| **Production** | `.env` or hosting platform | `wrangler secret put` |
| **Access** | `process.env.VAR` | `env.VAR` (handler parameter) |
| **Hierarchy** | Multi-file (workspace → app) | Single-file (`.dev.vars` wins) |

---

## Related Documentation

- **Monorepo Guide**: `../../docs/ENVIRONMENT_MANAGEMENT.md`
- **Cloudflare Docs**: [developers.cloudflare.com/workers](https://developers.cloudflare.com/workers)
- **Wrangler Docs**: [developers.cloudflare.com/workers/wrangler](https://developers.cloudflare.com/workers/wrangler)
- **Upstash Docs**: [docs.upstash.com](https://docs.upstash.com)

---

## Migration Notes

**Date**: December 26, 2025
**Issue**: #537 (Phase 3.1 - PopKit Pilot Migration)
**Parent Epic**: #528 (Workspace-Level Environment Variable Management)

PopKit was migrated as the pilot app to validate the migration process. Key learnings:

- ✅ Cloudflare Workers pattern different from Node.js
- ✅ `.dev.vars` simpler than multi-file hierarchy
- ✅ Wrangler secrets provide excellent production security
- ✅ Upstash free tiers sufficient for development

**Recommendation**: Document Cloudflare Workers pattern separately from Node.js/Python patterns in monorepo guide.
