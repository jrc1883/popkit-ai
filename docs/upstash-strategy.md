# PopKit + Upstash Strategy (2025)

## Executive Summary

PopKit's Upstash integration strategy spans three products: **Redis** (message streams), **Vector** (semantic search), and **QStash** (async jobs). This document outlines current offerings, pricing, and implementation roadmap.

---

## Part 1: Upstash Redis for Message Storage

### Current Pricing (2025 Update)

**Free Tier** ✅ (Ideal for development, small production)
- Storage: 256 MB
- Commands: 500K per month
- Bandwidth: 200 GB free per month
- Best for: Development, testing, prototyping

**Pay-as-You-Go** ✅ (Current PopKit implementation)
- Storage: Up to 100 GB
- Billing: By commands and bandwidth
- Bandwidth: $0.03 per GB beyond 200 GB/month
- No commitments, scales automatically

**Fixed Plans** (For higher throughput)
- Entry: 250 MB at $10/month
- Mid: 1 GB at $25/month
- High: 10 GB at $100/month
- Enterprise: Custom pricing
- Can add read replicas for $5/month each

**Prod Pack Add-on** (Enterprise features)
- Cost: $200/month per database
- Includes: Uptime SLA (99.9%), SOC 2 Type 2, RBAC, advanced monitoring

### Redis Streams for PopKit

**How it works**:
- Append-only log structure
- Each entry has unique ID and field-value pairs
- Entries can be deleted via XDEL or trimming
- Disk-based overflow beyond memory

**Proposed Streams Architecture**:

```
pop:telemetry:*
├─ pop:telemetry:tokens        # Token usage metrics
├─ pop:telemetry:agent-state   # Agent heartbeats
├─ pop:telemetry:boundary      # Boundary violations
└─ pop:telemetry:drift         # Drift alerts

pop:project-data:*
├─ pop:project-data:insights   # Insights shared
├─ pop:project-data:tasks      # Task assignments
├─ pop:project-data:results    # Handoffs
└─ pop:project-data:context    # Workflow context

pop:status:*
├─ pop:status:workflow         # Workflow state changes
├─ pop:status:alerts           # User-visible alerts
└─ pop:status:decisions        # Pending decisions
```

**Retention Policy**:
- Use XTRIM to limit stream size
- For Free Tier: Keep last 1000 entries per stream (≈ 1 day)
- For Pro Tier: Keep last 100K entries per stream (≈ 30 days)
- Archive to cold storage if needed (future)

**Command Budget**:
- Average message size: ~500 bytes
- Operations: XADD, XREAD, XTRIM
- Est. 500K/month free tier = ~40 messages/day per user
- Plenty of headroom for current use

---

## Part 2: Upstash Vector for Semantic Search

### Pricing (2025)

**Pay-as-You-Go**
- Cost: $0.40 per 100K operations
- Operations: Query, upsert, delete, fetch, range (all equal cost)
- Batch operations counted per vector
- Free tier: 20K operations/month

**Fixed Plan**
- Cost: $60/month
- Great for production with consistent load
- Predictable billing

### PopKit Vector Use Cases

**Current Status**: Research in progress (not yet implemented)

**Proposed Applications**:

1. **Insight Similarity** (Phase 2)
   - Find similar discoveries across sessions
   - "Similar issue found in project X"
   - Enable cross-project learning

2. **Agent Recommendation** (Phase 2)
   - Route queries to most relevant agent
   - Based on historical insights
   - Improve first-pass success

3. **Pattern Library** (Phase 3)
   - Build semantic index of patterns
   - Enable "smart suggestions"
   - Learn from all PopKit sessions

**Storage Estimate**:
- 1 session × 10 insights = 10 vectors
- 1000 sessions × 10 = 10K vectors
- Cost at $0.40/100K ops = ~$0.04 per 1000 sessions
- Very affordable for semantic enrichment

### Implementation Path

1. **Phase 1** (Current): Monitor Redis for messages
2. **Phase 2** (Q1 2026): Integrate Vector DB for insight similarity
3. **Phase 3** (Q2 2026): Build pattern library with semantic search
4. **Phase 4** (Q3 2026): ML-based recommendations

---

## Part 3: Upstash QStash for Async Jobs

### Overview

- Serverless message queue + job scheduler
- Perfect for: Cleanup jobs, scheduled reports, async processing
- Pricing: $0.35 per million messages

### PopKit QStash Use Cases

**Potential Applications**:

1. **Session Cleanup** (Daily, midnight UTC)
   - Archive old session data to cold storage
   - Trim Redis streams
   - Clean local JSON files

2. **Metrics Aggregation** (Hourly)
   - Summarize session metrics
   - Calculate team-wide statistics
   - Update analytics dashboard

3. **Pattern Analysis** (Weekly)
   - Find emerging patterns
   - Detect declining patterns
   - Update recommendations

4. **Data Export** (On-demand)
   - User requests data export
   - Generate CSV/JSON
   - Send via email (future)

**Cost Estimate**:
- Daily cleanup = 30 messages/month
- Hourly aggregation = 720 messages/month
- Weekly analysis = 4 messages/month
- Total = ~750 messages/month
- Cost: Negligible (free tier covers millions)

---

## Part 4: Upstash Workflows (Future)

**Overview**: Orchestrate multi-step async processes with built-in failure handling

**PopKit Workflow Ideas**:

1. **Session Complete Workflow**
   - Generate metrics report
   - Save to storage
   - Notify user
   - Update analytics

2. **Agent Coordination Workflow**
   - Wait for all agents to sync
   - Aggregate results
   - Format output
   - Store for history

3. **Team Sync Workflow**
   - Collect session data from all team members
   - Aggregate metrics
   - Generate team report
   - Distribute to stakeholders

---

## Part 5: Data Privacy & Compliance

### What's Stored in Upstash

**Telemetry** (Safe)
- Token counts, agent states, metrics
- No user PII, no API keys
- Can be encrypted at rest (via provider)

**Project Data** (Safe)
- Code context, file paths, patterns
- No passwords or secrets
- User's own project data

**Status Messages** (Safe)
- Workflow summaries, decisions
- No credentials or sensitive info

### What's NOT Stored

❌ `.env` files or secrets
❌ API tokens or keys
❌ User IDs (only session IDs)
❌ Email addresses
❌ Personal information

### Compliance Notes

- Upstash has SOC 2 Type 2 (available with Prod Pack)
- Data at rest encryption available
- GDPR compliant (EU data residency available)
- HIPAA available for healthcare

---

## Part 6: Free vs Pro Tier Implementation

### Tier Detection

```python
# In context_storage.py or new tier_detector.py

def get_user_tier() -> str:
    """Detect user's subscription tier"""
    # Check environment
    if UPSTASH_REDIS_REST_URL:
        return "pro"  # Pro users have Redis configured
    else:
        return "free"  # Free users use local JSON

def get_storage_backend() -> str:
    """Get appropriate storage backend"""
    tier = get_user_tier()

    if tier == "pro":
        return "upstash_redis"    # Streams, 30-day retention
    else:
        return "file_json"        # Local, 7-day retention
```

### Free Tier Implementation

**Storage**: `~/.popkit/messages/` (local JSON)

```json
{
  "messages": [
    {
      "id": "msg_123",
      "type": "HEARTBEAT",
      "category": "telemetry",
      "timestamp": "2025-12-15T10:30:45Z",
      "formatted": "🔵 code-explorer active (3:45m)"
    }
  ],
  "session_id": "sess_abc123",
  "created_at": "2025-12-15T10:00:00Z",
  "expires_at": "2025-12-22T10:00:00Z"  # 7 days
}
```

**Retention**: 7 days (auto-cleanup on startup)

**Capabilities**:
- ✅ View messages from current session
- ✅ Search within session (local grep)
- ✅ Export session as JSON
- ❌ Cross-session search
- ❌ Team sharing
- ❌ Semantic search

### Pro Tier Implementation

**Storage**: Upstash Redis Streams

```python
# Stream structure
redis.xadd(
    "pop:telemetry:tokens",
    {
        "session_id": "sess_abc123",
        "agent": "code-reviewer",
        "tokens": 2840,
        "model": "sonnet"
    }
)

# Query
messages = redis.xrange(
    "pop:telemetry:*",
    start="-",
    end="+",
    count=100
)
```

**Retention**: 30 days (via XTRIM)

**Capabilities**:
- ✅ All free tier features
- ✅ Cross-session search
- ✅ Team message sharing
- ✅ Advanced analytics
- ✅ API access to message history
- ✅ Workflow replay/debugging
- ❌ Vector search (separate product)

---

## Part 7: Pro Tier Monetization

### Upgrade Path

| Feature | Free | Pro | Enterprise |
|---------|------|-----|-----------|
| Local message storage | ✅ 7d | — | — |
| Redis streams | ❌ | ✅ 30d | ✅ 90d |
| Cross-session search | ❌ | ✅ | ✅ |
| Team sharing | ❌ | ✅ | ✅ |
| API access | ❌ | ✅ | ✅ |
| Vector search | ❌ | ✅* | ✅ |
| Analytics dashboard | ❌ | ✅ | ✅ |
| Data export (CSV/JSON) | ❌ | ✅ | ✅ |
| Audit logging | ❌ | ❌ | ✅ |
| Custom retention | ❌ | ❌ | ✅ |
| Dedicated support | ❌ | ❌ | ✅ |

*Vector search requires separate Upstash Vector subscription

### Pricing Strategy

**Pro Tier**: $9.99/month
- Covers Upstash overhead (~$2-3/month per active user)
- Provides sufficient margin for PopKit development
- Competitive with other AI dev tools

**Pro Tier Cost Breakdown**:
- Upstash Redis: ~$0 (free tier headroom) to $5/month (high volume)
- Upstash Vector: $0-5/month (optional, pay-as-you-go)
- QStash: Negligible (<$0.01/month)
- Cloud infrastructure: ~$2-3/month
- Margin/Development: ~$4-8/month

---

## Part 8: Implementation Roadmap

### Immediate (Phase 1: Q4 2025)
- ✅ Implement notification formatter
- ✅ Store messages to local JSON
- ✅ Free tier detection and fallback
- ✅ Session message retrieval

### Short-term (Phase 2: Q1 2026)
- Implement Upstash Redis connection
- Stream message storage (for Pro tier)
- Cross-session search
- Team message sharing
- API endpoints for message access

### Medium-term (Phase 3: Q2 2026)
- Upstash Vector integration
- Semantic similarity queries
- Pattern library
- Analytics dashboard

### Long-term (Phase 4: Q3+ 2026)
- QStash scheduled jobs
- Upstash Workflows
- Data export features
- Advanced audit logging

---

## Part 9: Key Decision Points

### 1. Data Residency
**Question**: Should data stay in user's region or centralized?

**PopKit Recommendation**: User's region preferred
- Lower latency
- Better privacy perception
- Upstash supports EU, US, Asia regions

### 2. Encryption at Rest
**Question**: Should we enable Upstash encryption?

**PopKit Recommendation**: Yes for Pro tier
- Included in Prod Pack ($200/month, optional)
- Protects against datacenter breaches
- Minimal performance impact

### 3. Schema Versioning
**Question**: How to handle message format changes?

**PopKit Recommendation**: Include version in every message
```json
{
  "version": "1.0",
  "type": "HEARTBEAT",
  "...": "..."
}
```

### 4. Message TTL vs Retention Policy
**Question**: Should messages auto-expire or manual cleanup?

**PopKit Recommendation**: Hybrid approach
- TTL for individual messages (7 days default)
- XTRIM for stream size management (keep last 100K entries)
- QStash job for archive/cleanup

---

## Part 10: Cost Projections

### Small Scale (1-10 users)
- Upstash: Free tier (256MB, 500K commands/month)
- Vector: Free tier (20K operations/month)
- QStash: Free tier
- **Total Cost**: $0

### Medium Scale (100 users)
- Upstash: Pay-as-you-go (~$10-20/month)
- Vector: Pay-as-you-go (~$5-10/month)
- QStash: Pay-as-you-go (<$1/month)
- **Total Cost**: ~$20/month infrastructure
- **Revenue**: 50 Pro users × $9.99 = ~$500/month (gross margin: 96%)

### Large Scale (1000+ users)
- Upstash: Fixed plan ($25-100/month)
- Vector: Fixed plan ($60/month)
- QStash: Fixed plan (optional)
- **Total Cost**: ~$150-200/month infrastructure
- **Revenue**: 500 Pro users × $9.99 = ~$5,000/month (gross margin: 97%)

---

## Next Steps

1. ✅ Research Upstash ecosystem (this document)
2. → Implement free tier with local JSON
3. → Create Pro tier Upstash integration (Phase 2)
4. → Build analytics dashboard (Phase 3)
5. → Add Vector search features (Phase 3)

---

## References

- [Upstash Redis Pricing](https://upstash.com/pricing/redis)
- [Upstash Redis Documentation](https://upstash.com/docs/redis/overall/pricing)
- [Upstash Vector Pricing](https://upstash.com/pricing/vector)
- [Upstash Vector Documentation](https://upstash.com/docs/vector/overall/whatisvector)
- [Redis Streams Beyond Memory](https://upstash.com/blog/redis-streams-beyond-memory)
