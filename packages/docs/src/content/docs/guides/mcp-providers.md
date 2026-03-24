---
title: MCP Provider Setup
description: Configure PopKit with Cursor, Codex CLI, Copilot, and other MCP clients
---

# MCP Provider Setup

PopKit works with any MCP-compatible AI coding tool. This guide covers setup for each provider.

## Prerequisites

Install the PopKit MCP server:

```bash
pip install popkit-mcp
```

Or use `uvx` for zero-install:

```bash
uvx popkit-mcp
```

---

## Cursor

Add to `~/.cursor/mcp.json` (global) or `.cursor/mcp.json` (per-project):

```json
{
  "mcpServers": {
    "popkit": {
      "command": "popkit-mcp",
      "args": ["--transport", "stdio"]
    }
  }
}
```

**Note:** Cursor has a limit of ~40 tools across all MCP servers. PopKit exposes tools selectively to stay within this limit.

---

## Codex CLI (OpenAI)

Add to `~/.codex/config.toml` (global) or `.codex/config.toml` (per-project):

```toml
[mcp_servers.popkit]
command = "popkit-mcp"
args = ["--transport", "stdio"]
```

Codex also reads `AGENTS.md` for agent rules — PopKit can generate these via `popkit-mcp --packages /path/to/packages`.

---

## GitHub Copilot CLI

Add to `~/.copilot/mcp-config.json` (global) or `.vscode/mcp.json` (per-project):

```json
{
  "mcpServers": {
    "popkit": {
      "command": "popkit-mcp",
      "args": ["--transport", "stdio"]
    }
  }
}
```

---

## VS Code (Generic MCP)

Add to `.vscode/mcp.json` (per-project):

```json
{
  "servers": {
    "popkit": {
      "command": "popkit-mcp",
      "args": ["--transport", "stdio"]
    }
  }
}
```

**Important:** VS Code uses `servers` as the root key, not `mcpServers` — even though other Microsoft tools use `mcpServers`.

---

## Claude Code

Claude Code users should install PopKit as a plugin instead of using MCP:

```bash
/plugin marketplace add jrc1883/popkit-claude
/plugin install popkit-core@popkit-claude
```

See [Installation](/getting-started/installation/) for full plugin setup.

---

## HTTP Transport (Advanced)

For debugging or remote setups, PopKit supports HTTP transports:

```bash
# Streamable HTTP (recommended for HTTP)
popkit-mcp --transport streamable-http --host 127.0.0.1 --port 8080

# SSE (Server-Sent Events)
popkit-mcp --transport sse --host 127.0.0.1 --port 8080
```

Then configure your MCP client to connect via HTTP instead of stdio.

---

## Config Reference

| Tool        | Format | Global Path                  | Per-Project Path     | Root Key          |
| ----------- | ------ | ---------------------------- | -------------------- | ----------------- |
| Cursor      | JSON   | `~/.cursor/mcp.json`         | `.cursor/mcp.json`   | `mcpServers`      |
| Codex CLI   | TOML   | `~/.codex/config.toml`       | `.codex/config.toml` | `[mcp_servers.*]` |
| Copilot CLI | JSON   | `~/.copilot/mcp-config.json` | `.vscode/mcp.json`   | `mcpServers`      |
| VS Code     | JSON   | User settings                | `.vscode/mcp.json`   | `servers`         |
| Claude Code | JSON   | `~/.claude.json`             | `.mcp.json`          | `mcpServers`      |

---

## Troubleshooting

### MCP server not detected

Verify the server starts correctly:

```bash
popkit-mcp --help
```

If the command isn't found, ensure `pip install popkit-mcp` installed to a directory on your `PATH`.

### Tools not appearing

Some clients limit the number of MCP tools. PopKit exposes tools selectively — use `--log-level DEBUG` to see which tools are registered:

```bash
popkit-mcp --transport stdio --log-level DEBUG
```
