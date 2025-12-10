# Premium Feature Protection Strategy

**Date:** 2025-12-10
**Status:** Research Complete
**Related Issues:** #151, #152, #126

## Executive Summary

PopKit's premium features can be protected **without cloud AI execution** by leveraging:
1. Server-side template rendering (no AI costs)
2. Upstash's full security stack (Redis, QStash, Workflow, Vector)
3. Subscription validation on every request

This approach works with flat subscription pricing ($9/mo) while protecting IP.

## The Problem We're Solving

### Original Concern
Users could copy premium skill files, cancel subscription, keep IP forever.

### Cloud AI Concern (Why It Doesn't Work)
Cloud AI execution requires API keys:
- **My API key**: Expensive per-request costs ($0.05-0.15 each)
- **User's API key**: Double-charging (they pay for Claude Code Max)
- **Neither**: Works with $9/mo flat subscription

### Key Insight
Most premium features are **template-based**, not AI-based:
- MCP generator = TypeScript templates
- Morning generator = Health check templates
- Nightly generator = Cleanup templates
- Power Mode = Redis orchestration

**Only 1 of 6 premium skills might benefit from AI inference.**

## Recommended Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     PopKit Cloud                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Upstash   │  │   Upstash   │  │  Cloudflare Worker  │  │
│  │   Redis     │  │   Vector    │  │  (Template Engine)  │  │
│  │  (encrypted │  │  (semantic  │  │                     │  │
│  │  templates) │  │  matching)  │  │  POST /api/premium  │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│         │                │                   │              │
│         └────────────────┴───────────────────┘              │
│                          │                                  │
│                   QStash (secure delivery)                  │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
              ┌─────────────────────────┐
              │   User's Claude Code    │
              │   + PopKit Plugin       │
              │                         │
              │   POST project context  │
              │   GET rendered output   │
              └─────────────────────────┘
```

## Upstash Stack Utilization

### Currently Using (2 products)
1. **Redis**: Power Mode coordination
2. **Vector**: Tool embeddings (via Voyage AI)

### Expansion Plan (4 more products)

| Product | Purpose | Priority |
|---------|---------|----------|
| **QStash** | Secure async delivery, signature verification | P1 |
| **Workflow** | Multi-step template execution | P2 |
| **Search** | Template search, docs lookup | P3 |
| **Realtime** | Live collaboration (future) | P3 |

### Security Features Available

**Redis:**
- TLS encryption (always on)
- Encryption at rest (Prod Pack)
- Redis ACL (access control)
- VPC peering (Pro)

**QStash:**
- Automatic signature verification
- Upstash-Signature header
- Callback/failure callbacks
- Dead letter queue
- Encryption at rest (Prod Pack)

**Workflow:**
- Built-in request verification
- Signing keys (QSTASH_CURRENT_SIGNING_KEY, QSTASH_NEXT_SIGNING_KEY)
- Custom authorization support
- Context propagation

**Vector:**
- Namespace isolation (multi-tenant)
- Per-user data separation

## Implementation Phases

### Phase 1: Template-Based Generation (P1)

Convert premium skills to server-side templates:

```typescript
// packages/cloud/src/premium/mcp-generator.ts
export async function generateMCPServer(context: ProjectContext) {
  // 1. Validate subscription
  const isValid = await validateSubscription(context.userId);
  if (!isValid) throw new Error('Premium subscription required');

  // 2. Detect tech stack
  const stack = detectTechStack(context.files);

  // 3. Select templates
  const templates = getTemplatesForStack(stack);

  // 4. Render with substitution
  return renderTemplates(templates, {
    PROJECT_NAME: context.projectName,
    SERVICES: context.services,
    DATABASE: stack.database,
  });
}
```

### Phase 2: Vector-Guided Selection (P2)

Use embeddings for "smart" template selection:

```typescript
// packages/cloud/src/premium/template-selector.ts
export async function selectBestTemplates(context: ProjectContext) {
  // 1. Embed project description
  const embedding = await embedContext(context.description);

  // 2. Query Vector for similar templates
  const matches = await vectorIndex.query({
    vector: embedding,
    topK: 5,
    namespace: 'templates',
  });

  // 3. Combine matched templates
  return combineTemplates(matches);
}
```

### Phase 3: Workflow Orchestration (P3)

Complex multi-step generations:

```typescript
// packages/cloud/src/premium/workflows/mcp-workflow.ts
export const { POST } = serve(async (context) => {
  // Step 1: Analyze project
  const analysis = await context.run('analyze', async () => {
    return analyzeProject(context.requestPayload);
  });

  // Step 2: Generate base server
  const server = await context.run('generate-server', async () => {
    return generateServer(analysis);
  });

  // Step 3: Generate tools
  const tools = await context.run('generate-tools', async () => {
    return generateTools(analysis.services);
  });

  // Step 4: Package and return
  return packageOutput(server, tools);
});
```

## Cost Comparison

| Approach | Per Request | Monthly (1K) | Annual |
|----------|-------------|--------------|--------|
| Cloud AI (Claude) | $0.10 | $100 | $1,200 |
| Cloud AI (GPT-4o) | $0.05 | $50 | $600 |
| Template Render | $0.0001 | $0.10 | $1.20 |
| Vector + Template | $0.0003 | $0.30 | $3.60 |

**Template-based is 300-1000x cheaper.**

## Premium Skill Conversion Guide

### pop-mcp-generator

**Current:** Claude generates MCP server code
**Converted:** Template with substitution

Templates needed:
- `mcp-server-base.ts.template`
- `mcp-tools-{service}.ts.template` (one per service type)
- `mcp-health-checks.ts.template`

### pop-morning-generator

**Current:** Claude detects tech stack, generates checks
**Converted:** Pattern matching + templates

```typescript
const TECH_PATTERNS = {
  nextjs: ['next.config.js', 'next.config.ts'],
  prisma: ['prisma/schema.prisma'],
  redis: ['docker-compose.yml:redis'],
};

const HEALTH_CHECK_TEMPLATES = {
  nextjs: 'templates/health/nextjs.md',
  prisma: 'templates/health/prisma.md',
  redis: 'templates/health/redis.md',
};
```

### pop-nightly-generator

**Current:** Claude detects artifacts, generates cleanup
**Converted:** Pattern matching + templates

Similar to morning generator - detect artifacts, select cleanup templates.

### pop-power-mode

**Current:** Already mostly template-based
**Protected by:** Redis access control, cloud coordinator

### pop-embed-project

**Current:** Sends items to Upstash Vector
**Protected by:** Vector namespace isolation, API key validation

## Security Checklist

- [ ] All premium endpoints require subscription validation
- [ ] QStash signature verification on all callbacks
- [ ] Redis ACL for template storage
- [ ] Vector namespaces per user/team
- [ ] Rate limiting on premium endpoints
- [ ] Audit logging for premium usage
- [ ] TLS for all data in transit
- [ ] Encryption at rest (Prod Pack)

## Migration Plan

1. **Week 1**: Create template structure for MCP generator
2. **Week 2**: Implement `/api/premium/generate` endpoint
3. **Week 3**: Add QStash secure delivery
4. **Week 4**: Convert morning/nightly generators
5. **Week 5**: Add Vector-based template selection
6. **Week 6**: Testing and documentation

## Open Questions

1. **Template versioning**: How to handle template updates?
   - Suggestion: Semantic versioning in Redis keys

2. **Offline fallback**: What if cloud is unavailable?
   - Suggestion: Graceful degradation with error message

3. **Enterprise custom templates**: Allow self-hosted templates?
   - Suggestion: Future enterprise tier feature

## Conclusion

The template-based approach:
- **Protects IP**: Templates never leave server
- **Eliminates AI costs**: Pure rendering
- **Enables flat pricing**: $9/mo works
- **Uses existing stack**: Upstash, Cloudflare Workers
- **Scales infinitely**: Serverless architecture

This is the recommended path forward for PopKit premium protection.
