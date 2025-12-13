# PopKit Setup for Continue.dev

This guide explains how to set up PopKit's Universal MCP Server in Continue.dev.

## Prerequisites

- VS Code or JetBrains IDE with Continue extension
- Node.js 18+ installed
- (Optional) PopKit API key for full features

## Setup

### Step 1: Install the MCP Server

```bash
npm install -g @popkit/mcp
```

### Step 2: Configure Continue

Continue has full MCP support and can import configs from other tools.

#### Option A: Native Configuration

Edit `~/.continue/config.json`:

```json
{
  "mcpServers": [
    {
      "name": "popkit",
      "command": "popkit-mcp",
      "env": {
        "POPKIT_API_KEY": "your-api-key-here"
      }
    }
  ]
}
```

#### Option B: Import from Claude Desktop/Cursor

If you have PopKit configured in Claude Desktop or Cursor, Continue can import it automatically:

1. Open Continue settings
2. Go to MCP Servers
3. Click "Import from other tools"
4. Select the source (Claude Desktop, Cursor, or Cline)

### Step 3: Restart Continue

Restart your IDE to load the MCP configuration.

## Usage

### In Chat

Use natural language to invoke PopKit tools:

```
Use PopKit to search for patterns about "database connection pooling"
```

### In Agent Mode

Continue's agent mode can use PopKit tools autonomously:

```
Start a PopKit workflow and implement user authentication
```

The agent will:
1. Call `popkit_workflow_start`
2. Implement the feature
3. Call `popkit_workflow_checkpoint` at milestones
4. Call `popkit_workflow_complete` when done

### Pattern Search

```
Search the PopKit collective for "Next.js API error handling"
```

### Memory Recall

```
What has PopKit learned about GraphQL pagination?
```

## Configuration Options

### Local MCP Server

For local development:

```json
{
  "mcpServers": [
    {
      "name": "popkit-local",
      "command": "node",
      "args": ["/path/to/popkit/packages/universal-mcp/dist/index.js"],
      "env": {
        "POPKIT_API_URL": "http://localhost:8787",
        "POPKIT_API_KEY": "dev-key"
      }
    }
  ]
}
```

### Docker-based Server

```json
{
  "mcpServers": [
    {
      "name": "popkit-docker",
      "command": "docker",
      "args": ["run", "-i", "--rm", "popkit/mcp-server"],
      "env": {
        "POPKIT_API_KEY": "your-key"
      }
    }
  ]
}
```

### Remote Server (SSE)

For hosted MCP servers:

```json
{
  "mcpServers": [
    {
      "name": "popkit-remote",
      "transport": {
        "type": "sse",
        "url": "https://mcp.popkit.dev/sse"
      }
    }
  ]
}
```

## Troubleshooting

### MCP Server Not Starting

1. Check Node.js version: `node --version` (need 18+)
2. Verify installation: `which popkit-mcp`
3. Test manually: `popkit-mcp` should output connection info

### Tools Not Appearing

1. Restart Continue completely
2. Check the MCP server logs in Continue's output panel
3. Verify the config.json syntax is valid

### Connection Errors

1. Check network connectivity
2. Verify API URL is accessible
3. Check firewall/proxy settings

## Available Tools

| Tool | Description |
|------|-------------|
| `popkit_pattern_search` | Search collective patterns |
| `popkit_pattern_submit` | Submit new patterns |
| `popkit_pattern_feedback` | Rate patterns |
| `popkit_workflow_start` | Start tracked workflow |
| `popkit_workflow_checkpoint` | Save checkpoint |
| `popkit_workflow_complete` | Complete workflow |
| `popkit_workflow_status` | Check workflow status |
| `popkit_memory_recall` | Recall learnings |
| `popkit_memory_store` | Store learnings |
| `popkit_agent_checkin` | Agent coordination |
| `popkit_agent_barrier` | Sync barrier |
| `popkit_agent_broadcast` | Broadcast to agents |
| `popkit_agent_search` | Search agents |
| `popkit_quality_check` | Quality validation |
| `popkit_health_status` | Service health |

## Continue Hub

PopKit will be available on Continue Hub for one-click installation:

1. Open Continue Hub
2. Search for "PopKit"
3. Click Install
4. Enter your API key when prompted

## Resources

- [Continue MCP Documentation](https://docs.continue.dev/customize/deep-dives/mcp)
- [Continue Hub](https://hub.continue.dev)
- [PopKit Documentation](https://popkit.dev/docs)
- [Get API Key](https://popkit.dev/account)
