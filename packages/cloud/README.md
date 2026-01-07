# PopKit Cloud API

Cloudflare Worker that provides the API gateway for PopKit Cloud, handling authentication, rate limiting, and Redis proxy operations.

## Architecture

```
Plugin (cloud_client.py)
         │
         ▼
   ┌─────────────────┐
   │ Cloudflare Edge │
   │   (this API)    │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │  Upstash Redis  │
   │    (US-East)    │
   └─────────────────┘
```

## Quick Start

### Prerequisites

- Node.js 18+
- Wrangler CLI (`npm i -g wrangler`)
- Upstash Redis account

### Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Configure Upstash secrets:
   ```bash
   wrangler secret put UPSTASH_REDIS_REST_URL
   wrangler secret put UPSTASH_REDIS_REST_TOKEN
   ```

3. Run locally:
   ```bash
   npm run dev
   ```

4. Deploy to Cloudflare:
   ```bash
   npm run deploy
   ```

## API Endpoints

### Public

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service info |
| `/v1/health` | GET | Health check |
| `/v1/health/detailed` | GET | Detailed health with Redis check |

### Protected (requires API key)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/redis/state` | POST | Push agent state |
| `/v1/redis/state/:agent_id` | GET | Get agent state |
| `/v1/redis/insights` | POST | Push insight |
| `/v1/redis/insights/search` | POST | Search insights |
| `/v1/redis/messages/:agent_id` | GET | Get messages |
| `/v1/redis/objective` | GET/POST | Get/set objective |
| `/v1/redis/patterns/search` | POST | Search patterns |
| `/v1/redis/publish` | POST | Publish to channel |
| `/v1/redis/subscribe` | POST | Poll channel messages |
| `/v1/usage` | GET | Current usage stats |
| `/v1/usage/history` | GET | Historical usage |

## Authentication

Include API key in Authorization header:

```
Authorization: Bearer pk_live_xxxxxxxxxxxxx
```

Key format:
- `pk_live_*` - Production keys
- `pk_test_*` - Sandbox keys (for development)

## Rate Limits

| Tier | Requests/min | Bandwidth/day |
|------|--------------|---------------|
| Free | 100 | 10 MB |
| Pro | 1,000 | 100 MB |
| Team | 10,000 | 1 GB |

Rate limit headers are included in all responses:
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`

## Data Isolation

All Redis keys are prefixed with `user:{userId}:` to ensure complete data isolation between users.

## Development

### Local Testing

```bash
# Start dev server
npm run dev

# Test health endpoint
curl http://localhost:8787/v1/health

# Test with API key
curl http://localhost:8787/v1/usage \
  -H "Authorization: Bearer pk_test_xxx"
```

### Type Checking

```bash
npm run typecheck
```

### Running Tests

```bash
npm test
```

## Deployment

### Cloudflare Workers

1. Login to Cloudflare:
   ```bash
   wrangler login
   ```

2. Set secrets:
   ```bash
   wrangler secret put UPSTASH_REDIS_REST_URL
   wrangler secret put UPSTASH_REDIS_REST_TOKEN
   ```

3. Deploy:
   ```bash
   npm run deploy
   ```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `UPSTASH_REDIS_REST_URL` | Yes | Upstash Redis REST URL |
| `UPSTASH_REDIS_REST_TOKEN` | Yes | Upstash Redis REST token |
| `ENVIRONMENT` | No | `development` or `production` |

## Security

- API keys are validated on every request
- Keys are stored as hashes in Redis
- All data is namespaced per user
- Rate limiting prevents abuse
- CORS configured for plugin access
