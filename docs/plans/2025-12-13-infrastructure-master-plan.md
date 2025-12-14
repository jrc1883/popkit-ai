# PopKit Infrastructure Master Plan

**Date:** 2025-12-13
**Status:** Draft
**Scope:** PopKit's own infrastructure + User deployment features

## Executive Summary

This plan consolidates two interconnected infrastructure needs:
1. **PopKit Cloud Infrastructure** - Hosting our own services (api.thehouseofdeals.com)
2. **User Deployment Features** - The `/popkit:deploy` command for user projects

Both share common technologies (Cloudflare, Upstash) and can be developed in parallel.

---

## Part 1: PopKit Cloud Infrastructure

### Current State

| Component | Status | Notes |
|-----------|--------|-------|
| Cloudflare Worker | Configured | `popkit-cloud-api` in wrangler.toml |
| Domain | Available | `thehouseofdeals.com` (testing only) |
| Upstash Redis | Configured | Need secrets in Worker |
| Upstash Vector | Configured | Need secrets in Worker |
| Upstash QStash | Configured | Need secrets in Worker |
| KV Namespace | Created | WAITLIST_KV (4f0137d8...) |

### Domain Architecture

```
thehouseofdeals.com (testing domain)
├── api.thehouseofdeals.com     → Cloudflare Worker (popkit-cloud-api)
├── mcp.thehouseofdeals.com     → MCP Server WebSocket endpoint (future)
├── docs.thehouseofdeals.com    → Documentation (Cloudflare Pages, optional)
└── status.thehouseofdeals.com  → Status page (optional)
```

**Future Production Domain:**
```
popkit.dev (or similar, when acquired)
├── api.popkit.dev
├── mcp.popkit.dev
├── docs.popkit.dev
└── status.popkit.dev
```

### Infrastructure Setup Steps

#### Phase 1: Domain Configuration (Cloudflare DNS)

```
# DNS Records to create in Cloudflare Dashboard
# (thehouseofdeals.com zone)

Type    Name    Content                          Proxy
----    ----    -------                          -----
CNAME   api     popkit-cloud-api.workers.dev     Yes
CNAME   mcp     popkit-mcp-server.workers.dev    Yes (future)
```

#### Phase 2: Worker Deployment

```bash
# In packages/cloud/
cd packages/cloud

# Set secrets (one-time)
npx wrangler secret put UPSTASH_REDIS_REST_URL
npx wrangler secret put UPSTASH_REDIS_REST_TOKEN
npx wrangler secret put UPSTASH_VECTOR_REST_URL
npx wrangler secret put UPSTASH_VECTOR_REST_TOKEN
npx wrangler secret put QSTASH_TOKEN

# Add custom domain route
# Edit wrangler.toml:
# routes = [
#   { pattern = "api.thehouseofdeals.com/*", zone_name = "thehouseofdeals.com" }
# ]

# Deploy
npx wrangler deploy
```

#### Phase 3: MCP Server Hosting (Future)

Options for hosting the Universal MCP Server:
1. **Cloudflare Worker** - WebSocket support via Durable Objects
2. **Fly.io** - Easy WebSocket, global edge deployment
3. **Railway** - Simple deployment, good for prototyping

**Recommendation:** Cloudflare Worker with Durable Objects for consistency with existing infra.

### API Endpoints Design

```
POST /api/v1/patterns/search     # Semantic pattern search
POST /api/v1/patterns/submit     # Submit new patterns (authenticated)
GET  /api/v1/health              # Health check

POST /api/v1/embeddings/create   # Generate embeddings
POST /api/v1/embeddings/search   # Search by embedding

POST /api/v1/bugs/report         # Bug reporting
GET  /api/v1/bugs/search         # Search known bugs

POST /api/v1/auth/login          # Authentication
POST /api/v1/auth/refresh        # Token refresh

# Premium endpoints
POST /api/v1/team/sync           # Team coordination
POST /api/v1/analytics/track     # Usage analytics
```

### Environment Variables Needed

| Variable | Source | Purpose |
|----------|--------|---------|
| `UPSTASH_REDIS_REST_URL` | Upstash Console | Pattern storage, sessions |
| `UPSTASH_REDIS_REST_TOKEN` | Upstash Console | Auth for Redis |
| `UPSTASH_VECTOR_REST_URL` | Upstash Console | Semantic search |
| `UPSTASH_VECTOR_REST_TOKEN` | Upstash Console | Auth for Vector |
| `QSTASH_TOKEN` | Upstash Console | Durable workflows |
| `JWT_SECRET` | Generate | User authentication |
| `STRIPE_SECRET_KEY` | Stripe Dashboard | Billing (future) |

---

## Part 2: User Deployment Features (/popkit:deploy)

### Existing Design

Full design exists at: `docs/plans/2025-12-10-deploy-command-design.md`

Key points:
- 5 subcommands: `init`, `setup`, `validate`, `execute`, `rollback`
- 4 targets: Docker, npm/PyPI, Vercel/Netlify, GitHub Releases
- Premium feature gating
- 8 implementation epics defined

### Implementation Priority

Given that PopKit infrastructure uses similar technologies, we can:
1. Build Cloudflare skills first (benefits both PopKit and users)
2. Implement Docker deployment (most requested)
3. Add Vercel/Netlify (common for frontend projects)

### Skills to Create

#### 1. pop-cloudflare-worker-deploy

```yaml
# skills/pop-cloudflare-worker-deploy/SKILL.md
name: Cloudflare Worker Deployment
description: Deploy a project as a Cloudflare Worker
triggers:
  - "deploy to cloudflare"
  - "cloudflare worker"
  - "wrangler deploy"
```

Features:
- Detect if wrangler.toml exists
- Guide through wrangler init if needed
- Set secrets from environment
- Deploy with custom domain routing
- Verify deployment health

#### 2. pop-cloudflare-pages-deploy

```yaml
name: Cloudflare Pages Deployment
description: Deploy static sites/SPAs to Cloudflare Pages
triggers:
  - "deploy to pages"
  - "cloudflare pages"
  - "static site deploy"
```

Features:
- Auto-detect framework (Next.js, Vite, etc.)
- Configure build settings
- Deploy via wrangler pages
- Custom domain setup

#### 3. pop-cloudflare-dns-manage

```yaml
name: Cloudflare DNS Management
description: Manage DNS records via Cloudflare API
triggers:
  - "add dns record"
  - "configure domain"
  - "cloudflare dns"
```

Features:
- List zones and records
- Add/update/delete records
- Proxy status management
- SSL/TLS configuration

### Command Structure

```
/popkit:deploy
├── init                    # Initialize deployment config
├── setup <target>          # Configure specific target
│   ├── docker
│   ├── vercel
│   ├── netlify
│   ├── cloudflare-worker
│   ├── cloudflare-pages
│   ├── npm
│   └── github-release
├── validate                # Pre-deploy validation
├── execute [--target]      # Run deployment
└── rollback [--target]     # Emergency rollback
```

---

## Part 3: Shared Infrastructure Components

### Cloudflare API Integration

Both PopKit infra and user deployment need Cloudflare API access:

```typescript
// packages/plugin/hooks/utils/cloudflare_api.py
// Shared utilities for Cloudflare operations

class CloudflareAPI:
    def __init__(self, api_token: str, account_id: str):
        self.api_token = api_token
        self.account_id = account_id
        self.base_url = "https://api.cloudflare.com/client/v4"

    def list_zones(self) -> List[Zone]: ...
    def get_zone(self, zone_id: str) -> Zone: ...
    def create_dns_record(self, zone_id: str, record: DNSRecord) -> DNSRecord: ...
    def deploy_worker(self, worker_name: str, script: str) -> Deployment: ...
    def set_worker_secret(self, worker_name: str, key: str, value: str): ...
```

### Upstash Integration (Already Exists)

Located in `packages/plugin/hooks/utils/context_storage.py`:
- Redis client for patterns, sessions
- Vector client for embeddings
- QStash client for workflows

### MCP Server Tools

The Universal MCP Server (`packages/universal-mcp/`) already provides:
- 15 tools for cross-platform use
- Pattern search, health checks
- Git integration, quality tools

---

## Part 4: Implementation Roadmap

### Sprint 1: PopKit Infrastructure (This Week)

| Task | Priority | Effort |
|------|----------|--------|
| Configure DNS records in Cloudflare | P0 | 1 hour |
| Add route to wrangler.toml | P0 | 30 min |
| Set secrets via wrangler | P0 | 30 min |
| Deploy popkit-cloud-api | P0 | 1 hour |
| Verify API health endpoint | P0 | 30 min |

### Sprint 2: Cloudflare Skills (Next)

| Task | Priority | Effort |
|------|----------|--------|
| Create pop-cloudflare-worker-deploy skill | P1 | 4 hours |
| Create pop-cloudflare-pages-deploy skill | P1 | 4 hours |
| Create pop-cloudflare-dns-manage skill | P2 | 3 hours |
| Add Cloudflare API utility module | P1 | 2 hours |

### Sprint 3: Deploy Command (Following)

| Task | Priority | Effort |
|------|----------|--------|
| Create /popkit:deploy command shell | P1 | 2 hours |
| Implement `deploy init` | P1 | 3 hours |
| Implement `deploy setup cloudflare-worker` | P1 | 4 hours |
| Implement `deploy validate` | P1 | 3 hours |
| Implement `deploy execute` | P1 | 4 hours |

### Sprint 4: Additional Targets

| Task | Priority | Effort |
|------|----------|--------|
| Docker deployment target | P1 | 6 hours |
| Vercel deployment target | P2 | 4 hours |
| Netlify deployment target | P2 | 4 hours |
| npm publish target | P2 | 3 hours |

---

## Part 5: Security Considerations

### Secrets Management

| Secret Type | Storage | Access |
|-------------|---------|--------|
| Cloudflare API Token | Env var / wrangler secrets | Plugin hooks |
| Upstash tokens | wrangler secrets | Cloud API only |
| User deploy tokens | User's env vars | Never stored by PopKit |

### API Authentication

```
PopKit Cloud API Authentication Flow:
1. User registers via /auth/register (email + password)
2. Login returns JWT token
3. Token included in Authorization header
4. Premium features check entitlements
```

### Rate Limiting

```
# In Cloudflare Worker
Free tier: 100 requests/hour
Pro tier: 1000 requests/hour
Team tier: 10000 requests/hour
```

---

## Part 6: GitHub Issues to Create

### Epic: PopKit Cloud Deployment (#NEW)

Child issues:
1. Configure DNS records for api.thehouseofdeals.com
2. Add custom domain route to wrangler.toml
3. Deploy cloud API to production
4. Create health check monitoring

### Epic: Cloudflare Integration Skills (#NEW)

Child issues:
1. Create pop-cloudflare-worker-deploy skill
2. Create pop-cloudflare-pages-deploy skill
3. Create pop-cloudflare-dns-manage skill
4. Add cloudflare_api.py utility module

### Existing Epic: User Deployment Features

From deploy command design - 8 epics already defined.

---

## Decision Points

### 1. Testing Domain vs Production Domain

**Current Plan:** Use thehouseofdeals.com for all testing
**Future:** Acquire popkit.dev (or similar) for production launch

**Migration Path:**
1. All infrastructure works with environment-based domain config
2. When ready to launch, update DNS and wrangler.toml
3. No code changes needed

### 2. MCP Server Hosting

**Options:**
- A) Cloudflare Workers (Durable Objects for WebSocket)
- B) Fly.io (native WebSocket support)
- C) Railway (simple, good for prototyping)

**Recommendation:** Start with npm package only, add hosted option in v1.1

### 3. Premium Feature Gating

**For Testing:** All features enabled (no payment check)
**For Launch:** Stripe integration for Pro/Team tiers

---

## Next Steps

1. **Immediate:** Deploy PopKit Cloud API to api.thehouseofdeals.com
2. **This Week:** Create Cloudflare integration skills
3. **Next Week:** Implement /popkit:deploy command shell
4. **Following:** Add deployment targets one by one

---

## Appendix: Useful Commands

```bash
# Cloudflare Workers
npx wrangler deploy                    # Deploy worker
npx wrangler secret put SECRET_NAME    # Add secret
npx wrangler tail                      # Live logs
npx wrangler dev                       # Local development

# DNS (via wrangler or dashboard)
# Add CNAME: api -> popkit-cloud-api.workers.dev

# Verify deployment
curl https://api.thehouseofdeals.com/health
```
