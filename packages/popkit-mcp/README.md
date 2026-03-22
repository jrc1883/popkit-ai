# PopKit MCP Server

Standalone MCP server that exposes PopKit skills, agents, and commands as MCP tools, resources, and prompts. Any MCP-compatible tool (Cursor, Codex CLI, Copilot, etc.) can connect to this server to use PopKit.

## MCP Tools

| Tool                  | Description                       |
| --------------------- | --------------------------------- |
| `popkit/run_skill`    | Invoke any PopKit skill by name   |
| `popkit/spawn_agent`  | Start an agent with a task        |
| `popkit/power_mode`   | Orchestrate multi-agent workflows |
| `popkit/get_context`  | Retrieve project context          |
| `popkit/health_check` | System status and diagnostics     |

## Usage

```bash
# stdio transport (default, for MCP clients)
popkit-mcp-server

# SSE transport
popkit-mcp-server --transport sse --port 8080

# Streamable HTTP transport
popkit-mcp-server --transport streamable-http --port 8080
```

## MCP Client Configuration

Add to your tool's MCP configuration:

```json
{
  "mcpServers": {
    "popkit": {
      "command": "python3",
      "args": ["-m", "popkit_mcp.server"]
    }
  }
}
```

## Requirements

- Python 3.11+
- `mcp` SDK (^1.12.0)
- PopKit packages installed
