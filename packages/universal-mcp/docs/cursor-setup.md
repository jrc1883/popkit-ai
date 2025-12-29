# PopKit Setup for Cursor

This guide explains how to set up PopKit's Universal MCP Server in Cursor.

## Prerequisites

- Cursor IDE installed
- Node.js 18+ installed
- (Optional) PopKit API key for full features

## Setup

### Step 1: Install the MCP Server

```bash
npm install -g @popkit/mcp
```

### Step 2: Configure Cursor

Create or edit `.cursor/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "popkit": {
      "command": "npx",
      "args": ["@popkit/mcp"],
      "env": {
        "POPKIT_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

Or for global configuration, edit `~/.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "popkit": {
      "command": "popkit-mcp",
      "env": {
        "POPKIT_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

### Step 3: Restart Cursor

Restart Cursor to load the MCP configuration.

## Usage

### Pattern Search

Ask Cursor to search for patterns:

```
Search PopKit patterns for "how to handle authentication in Next.js"
```

This will call `popkit_pattern_search` and return relevant patterns from the collective.

### Workflow Tracking

Start a tracked workflow:

```
Start a PopKit workflow for "Implement user dashboard"
```

Save checkpoints as you work:

```
Save a PopKit checkpoint at the "implementation" phase with 50% progress
```

### Memory Recall

Recall learnings from previous sessions:

```
Recall PopKit memories about "rate limiting approaches"
```

## Troubleshooting

### MCP Server Not Found

If you see "MCP server not found":

1. Verify installation: `npx @popkit/mcp --version`
2. Check the path in your mcp.json
3. Try using the full path to the executable

### Authentication Errors

If you see authentication errors:

1. Verify your API key is correct
2. Check the key hasn't expired
3. Try without API key (anonymous mode)

### Connection Issues

If the server can't connect:

1. Check your internet connection
2. Verify `https://api.popkit.dev` is accessible
3. Check for firewall/proxy issues

## Advanced Configuration

### Custom API URL

For self-hosted PopKit Cloud:

```json
{
  "mcpServers": {
    "popkit": {
      "command": "popkit-mcp",
      "env": {
        "POPKIT_API_URL": "https://your-instance.example.com",
        "POPKIT_API_KEY": "your-key"
      }
    }
  }
}
```

### Environment Variables via Interpolation

Cursor supports environment variable interpolation:

```json
{
  "mcpServers": {
    "popkit": {
      "command": "popkit-mcp",
      "env": {
        "POPKIT_API_KEY": "${env:POPKIT_API_KEY}"
      }
    }
  }
}
```

Then set `POPKIT_API_KEY` in your shell environment.

## Available Tools

After setup, these tools are available in Cursor:

| Tool | Example Prompt |
|------|----------------|
| `popkit_pattern_search` | "Search patterns for React optimization" |
| `popkit_pattern_submit` | "Submit this solution as a pattern" |
| `popkit_workflow_start` | "Start a workflow for this feature" |
| `popkit_workflow_checkpoint` | "Save checkpoint at 75% progress" |
| `popkit_memory_recall` | "Recall memories about caching" |
| `popkit_memory_store` | "Remember this approach" |
| `popkit_agent_search` | "Find an agent for security review" |
| `popkit_health_status` | "Check PopKit status" |

## Resources

- [Cursor MCP Documentation](https://docs.cursor.com/mcp)
- [PopKit Documentation](https://popkit.dev/docs)
- [Get API Key](https://popkit.dev/account)
