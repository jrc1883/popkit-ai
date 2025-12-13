# PopKit Cloud API Contract

**Version:** 2.0 (Multi-Model Support)
**Last Updated:** December 2025
**Purpose:** Define model-agnostic API endpoints for cross-platform PopKit integration

## Overview

This document defines the API contract for PopKit Cloud that enables:
1. **Client-agnostic operations** - Same endpoints work for Claude Code, Cursor, Continue, etc.
2. **Tool detection** - Cloud identifies calling client for analytics and routing
3. **Cross-model patterns** - Unified schema for patterns that work across all tools

---

## Client Identification

### Header-Based Detection

All PopKit clients MUST send identification headers:

```http
X-PopKit-Client: claude-code | cursor | continue | windsurf | copilot | gemini | unknown
X-PopKit-Client-Version: 1.0.0
X-PopKit-Plugin-Version: 0.2.1
```

### Detection Priority

1. **Explicit header** - `X-PopKit-Client` header (most reliable)
2. **User-Agent parsing** - Extract client from User-Agent
3. **Auth context** - Client type stored in API key metadata
4. **Default** - `unknown`

### Implementation

```typescript
// middleware/client-detection.ts
export interface ClientInfo {
  client: ClientType;
  clientVersion?: string;
  pluginVersion?: string;
  capabilities: string[];
}

export type ClientType =
  | 'claude-code'
  | 'cursor'
  | 'continue'
  | 'windsurf'
  | 'copilot'
  | 'gemini'
  | 'mcp-generic'  // Universal MCP client
  | 'unknown';

export function detectClient(c: Context): ClientInfo {
  const clientHeader = c.req.header('X-PopKit-Client');
  const clientVersion = c.req.header('X-PopKit-Client-Version');
  const pluginVersion = c.req.header('X-PopKit-Plugin-Version');

  const client = parseClientType(clientHeader);

  return {
    client,
    clientVersion,
    pluginVersion,
    capabilities: getClientCapabilities(client)
  };
}
```

### Client Capabilities

| Client | MCP | Hooks | Agents | Backgrounds | Skills |
|--------|-----|-------|--------|-------------|--------|
| claude-code | Yes | Yes | Yes | Yes | Yes |
| cursor | Yes | No | No | Limited | Via MCP |
| continue | Yes | No | No | No | Via MCP |
| windsurf | TBD | No | No | No | TBD |
| copilot | Partial | No | No | Yes | Via MCP |
| gemini | TBD | No | No | TBD | TBD |
| mcp-generic | Yes | No | No | No | Via MCP |

---

## Model-Agnostic Endpoints

### Core Endpoints (All Clients)

These endpoints work identically across all clients:

#### POST /v2/workflows/start

Start a tracked workflow session.

```json
// Request
{
  "goal": "Implement user authentication",
  "context": {
    "project": "my-app",
    "branch": "feature/auth"
  }
}

// Response
{
  "workflowId": "wf_abc123",
  "status": "started",
  "createdAt": "2025-12-13T10:00:00Z"
}
```

#### POST /v2/workflows/:id/checkpoint

Save workflow checkpoint.

```json
// Request
{
  "phase": "implementation",
  "progress": 0.5,
  "state": {
    "filesModified": ["src/auth.ts", "src/routes.ts"],
    "testsAdded": 3
  }
}

// Response
{
  "checkpointId": "cp_xyz789",
  "phase": "implementation",
  "savedAt": "2025-12-13T10:30:00Z"
}
```

#### POST /v2/workflows/:id/complete

Complete workflow.

```json
// Request
{
  "outcome": "success",
  "summary": "Added JWT authentication with login/logout",
  "metrics": {
    "filesChanged": 5,
    "linesAdded": 250,
    "testsAdded": 8
  }
}

// Response
{
  "status": "completed",
  "duration": "45m",
  "completedAt": "2025-12-13T10:45:00Z"
}
```

#### GET /v2/patterns/search

Search cross-project patterns.

```json
// Request (query params)
?query=authentication&limit=10&min_confidence=0.7

// Response
{
  "patterns": [
    {
      "id": "pat_123",
      "pattern": "JWT authentication with refresh tokens",
      "context": "Next.js API routes",
      "examples": ["src/pages/api/auth/login.ts"],
      "confidence": 0.92,
      "usageCount": 47,
      "source": {
        "client": "claude-code",
        "anonymized": true
      }
    }
  ],
  "total": 156
}
```

#### POST /v2/patterns/submit

Submit a new pattern.

```json
// Request
{
  "pattern": "Use server actions for form submissions",
  "context": "Next.js 14 forms",
  "examples": ["src/app/actions.ts:15-30"],
  "category": "best-practice",
  "tags": ["nextjs", "forms", "server-actions"]
}

// Response
{
  "patternId": "pat_456",
  "status": "submitted",
  "willBeAnonymized": true
}
```

#### GET /v2/memory/recall

Recall cross-project learnings.

```json
// Request (query params)
?query=how to handle rate limiting&limit=5

// Response
{
  "memories": [
    {
      "id": "mem_789",
      "content": "Use Redis sliding window for rate limiting",
      "context": "API security",
      "relevance": 0.95,
      "sourceProject": "anonymized",
      "learnedAt": "2025-12-10T..."
    }
  ]
}
```

#### POST /v2/memory/store

Store a learning for future recall.

```json
// Request
{
  "key": "rate-limiting-approach",
  "content": "Sliding window with Redis sorted sets",
  "context": "Implemented in project X",
  "tags": ["redis", "rate-limiting", "api"]
}

// Response
{
  "memoryId": "mem_abc",
  "stored": true
}
```

### Agent Coordination (Power Mode Lite)

These endpoints enable lightweight multi-agent coordination:

#### POST /v2/agents/checkin

Agent progress check-in.

```json
// Request
{
  "agentId": "agent_001",
  "agentType": "code-reviewer",
  "sessionId": "sess_xyz",
  "state": {
    "phase": "reviewing",
    "progress": 0.75,
    "findings": 3
  }
}

// Response
{
  "received": true,
  "messages": [
    // Any messages waiting for this agent
  ]
}
```

#### POST /v2/agents/barrier

Request sync barrier across agents.

```json
// Request
{
  "sessionId": "sess_xyz",
  "barrier": "phase-1-complete",
  "agentId": "agent_001"
}

// Response
{
  "status": "waiting", // or "proceed" when all agents ready
  "agentsReady": 2,
  "agentsTotal": 3
}
```

#### POST /v2/agents/broadcast

Broadcast message to other agents.

```json
// Request
{
  "sessionId": "sess_xyz",
  "fromAgent": "agent_001",
  "message": {
    "type": "INSIGHT",
    "content": "Found SQL injection vulnerability in auth.ts:45"
  }
}

// Response
{
  "delivered": true,
  "recipients": ["agent_002", "agent_003"]
}
```

### Quality Gates

#### POST /v2/quality/check

Run quality validation.

```json
// Request
{
  "checks": ["typescript", "lint", "test"],
  "projectPath": "/path/to/project",
  "files": ["src/auth.ts", "src/routes.ts"]
}

// Response
{
  "status": "pass", // or "fail"
  "results": {
    "typescript": {"status": "pass", "errors": 0},
    "lint": {"status": "pass", "warnings": 2},
    "test": {"status": "pass", "passed": 15, "failed": 0}
  }
}
```

#### GET /v2/health

Project health status.

```json
// Response
{
  "service": "popkit-cloud",
  "status": "healthy",
  "version": "2.0.0",
  "capabilities": {
    "workflows": true,
    "patterns": true,
    "memory": true,
    "agents": true,
    "quality": true
  }
}
```

---

## Cross-Model Pattern Schema

### Pattern Structure

All patterns use this unified schema:

```typescript
interface Pattern {
  // Identity
  id: string;
  version: number;

  // Content
  pattern: string;           // Natural language description
  context: string;           // When/where to apply
  examples: PatternExample[];

  // Metadata
  category: PatternCategory;
  tags: string[];
  confidence: number;        // 0.0 to 1.0
  usageCount: number;

  // Source (anonymized)
  source: {
    client: ClientType;
    language?: string;
    framework?: string;
    anonymized: boolean;
  };

  // Timestamps
  createdAt: string;
  updatedAt: string;
  lastUsedAt?: string;
}

interface PatternExample {
  code?: string;
  file?: string;
  description: string;
}

type PatternCategory =
  | 'architecture'
  | 'best-practice'
  | 'security'
  | 'performance'
  | 'testing'
  | 'debugging'
  | 'refactoring'
  | 'documentation'
  | 'workflow';
```

### Cross-Platform Compatibility

Patterns are stored in a format that works across all clients:

| Field | Claude Code | Cursor | Continue | Notes |
|-------|-------------|--------|----------|-------|
| pattern | Used in skills | Shown in chat | Shown in chat | Natural language |
| examples.code | Can execute | Display only | Display only | Code snippets |
| examples.file | Full paths | Relative paths | Relative paths | Adapt per client |
| tags | Routing | Search | Search | Shared taxonomy |

---

## MCP Tool Mapping

For MCP clients (Cursor, Continue), map API endpoints to MCP tools:

| MCP Tool | API Endpoint |
|----------|--------------|
| `popkit_workflow_start` | POST /v2/workflows/start |
| `popkit_workflow_checkpoint` | POST /v2/workflows/:id/checkpoint |
| `popkit_workflow_complete` | POST /v2/workflows/:id/complete |
| `popkit_pattern_search` | GET /v2/patterns/search |
| `popkit_pattern_submit` | POST /v2/patterns/submit |
| `popkit_memory_recall` | GET /v2/memory/recall |
| `popkit_memory_store` | POST /v2/memory/store |
| `popkit_agent_checkin` | POST /v2/agents/checkin |
| `popkit_agent_barrier` | POST /v2/agents/barrier |
| `popkit_agent_broadcast` | POST /v2/agents/broadcast |
| `popkit_quality_check` | POST /v2/quality/check |
| `popkit_health_status` | GET /v2/health |

---

## Versioning

### API Versions

| Version | Status | Features |
|---------|--------|----------|
| v1 | Stable | Current Claude Code-specific API |
| v2 | Beta | Multi-model support (this document) |

### Migration Path

1. v1 endpoints continue to work unchanged
2. v2 endpoints add multi-model capabilities
3. Claude Code plugin can use either
4. MCP server uses v2 endpoints

### Breaking Changes Policy

- v1 will remain stable for 12 months after v2 GA
- Deprecation notices 6 months before removal
- New features only added to v2

---

## Rate Limits

| Tier | Requests/min | Patterns/day | Memory/day |
|------|--------------|--------------|------------|
| Free | 60 | 100 | 50 |
| Pro | 300 | 1000 | 500 |
| Team | 1000 | 10000 | 5000 |

---

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Retry after 60 seconds.",
    "retryAfter": 60
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| UNAUTHORIZED | 401 | Invalid or missing API key |
| FORBIDDEN | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |
| INVALID_REQUEST | 400 | Malformed request |
| SERVER_ERROR | 500 | Internal server error |

---

## Implementation Checklist

- [ ] Add client detection middleware
- [ ] Create v2 route namespace
- [ ] Implement workflow endpoints
- [ ] Implement pattern endpoints with cross-model schema
- [ ] Implement memory endpoints
- [ ] Implement agent coordination endpoints
- [ ] Update types.ts with new interfaces
- [ ] Add MCP tool mapping documentation
- [ ] Create migration guide for v1 → v2

---

*This document is part of PopKit's Multi-Model Foundation epic (#111)*
