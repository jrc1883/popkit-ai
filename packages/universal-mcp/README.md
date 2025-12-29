# PopKit Universal MCP Server

Universal MCP (Model Context Protocol) server that works with any MCP-compatible AI coding tool.

## Supported Clients

| Client | Status | Notes |
|--------|--------|-------|
| Cursor | ✅ Supported | Full MCP support |
| Continue.dev | ✅ Supported | Full MCP support |
| Claude Code | ✅ Supported | Native plugin also available |
| Windsurf | 🔄 Pending | Awaiting MCP support |
| GitHub Copilot | 🔄 Partial | OpenAI adopted MCP in 2025 |

## Quick Start

### Install

```bash
npm install -g @popkit/mcp
```

Or run directly with npx:

```bash
npx @popkit/mcp
```

### Configure Your Client

See the [Setup Guides](./docs/) for client-specific instructions:

- [Cursor Setup](./docs/cursor-setup.md)
- [Continue Setup](./docs/continue-setup.md)
- [Claude Code Setup](./docs/claude-code-setup.md)

## Available Tools

### Pattern Tools (Collective Learning)

| Tool | Description |
|------|-------------|
| `popkit_pattern_search` | Search for solutions from the collective learning database |
| `popkit_pattern_submit` | Submit a new pattern to help others |
| `popkit_pattern_feedback` | Rate pattern quality |

### Workflow Tools (State Tracking)

| Tool | Description |
|------|-------------|
| `popkit_workflow_start` | Start a tracked workflow session |
| `popkit_workflow_checkpoint` | Save progress checkpoint |
| `popkit_workflow_complete` | Complete workflow with summary |
| `popkit_workflow_status` | Check workflow status |

### Memory Tools (Cross-Project Learning)

| Tool | Description |
|------|-------------|
| `popkit_memory_recall` | Recall learnings from previous sessions |
| `popkit_memory_store` | Store a learning for future recall |

### Agent Tools (Power Mode Lite)

| Tool | Description |
|------|-------------|
| `popkit_agent_checkin` | Agent progress check-in |
| `popkit_agent_barrier` | Sync barrier for coordination |
| `popkit_agent_broadcast` | Broadcast message to agents |
| `popkit_agent_search` | Search agents by capability |

### Quality Tools

| Tool | Description |
|------|-------------|
| `popkit_quality_check` | Run quality validation checks |
| `popkit_health_status` | Check PopKit Cloud status |

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `POPKIT_API_KEY` | Optional | API key for authenticated access |
| `POPKIT_API_URL` | Optional | Custom API URL (default: https://api.popkit.dev) |
| `POPKIT_CLIENT` | Optional | Override client detection |

### Getting an API Key

1. Sign up at [popkit.dev](https://popkit.dev)
2. Go to Settings > API Keys
3. Create a new key
4. Set `POPKIT_API_KEY` environment variable

Anonymous access works for basic features. An API key unlocks:
- Higher rate limits
- Persistent memory
- Team features
- Analytics

## Architecture

```
┌─────────────────┐     ┌─────────────────┐
│  Your AI Tool   │     │  PopKit Cloud   │
│  (Cursor, etc)  │     │  (api.popkit.dev)│
└────────┬────────┘     └────────┬────────┘
         │                       │
         │  MCP Protocol         │  REST API
         │  (stdio/SSE)          │
         │                       │
    ┌────▼────────────────────────▼────┐
    │    PopKit Universal MCP Server    │
    │    (@popkit/mcp)                  │
    ├───────────────────────────────────┤
    │  Tools:                           │
    │  - Pattern search/submit          │
    │  - Workflow tracking              │
    │  - Memory recall/store            │
    │  - Agent coordination             │
    │  - Quality checks                 │
    └───────────────────────────────────┘
```

## Local Development

```bash
# Clone the repo
git clone https://github.com/jrc1883/popkit.git
cd popkit/packages/universal-mcp

# Install dependencies
npm install

# Build
npm run build

# Run
npm start
```

## License

MIT - see [LICENSE](./LICENSE)

## Related

- [PopKit Claude Code Plugin](https://github.com/jrc1883/popkit-claude) - Native Claude Code plugin
- [PopKit Cloud API](https://api.popkit.dev) - Backend API documentation
- [MCP Specification](https://modelcontextprotocol.io) - Model Context Protocol
