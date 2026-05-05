---
title: Installation
description: How to install PopKit — Claude Code plugin, PyPI packages, or MCP server
---

# Installation

PopKit can be installed in three ways depending on your setup:

| Method                 | Best for                                   | Install command                             |
| ---------------------- | ------------------------------------------ | ------------------------------------------- |
| **Claude Code plugin** | Claude Code users                          | `/plugin marketplace add jrc1883/popkit-ai` |
| **PyPI (MCP server)**  | Cursor, Codex CLI, Copilot, any MCP client | `pip install popkit-mcp`                    |
| **PyPI (full)**        | Standalone CLI + all utilities             | `pip install popkit[full]`                  |

---

## Claude Code Plugin (Recommended)

### Step 1: Add the Marketplace (One-time Setup)

```bash
/plugin marketplace add jrc1883/popkit-ai
```

### Step 2: Install Plugins

Install all plugins for full functionality:

```bash
# Install all plugins
/plugin install popkit-core@popkit-ai
/plugin install popkit-dev@popkit-ai
/plugin install popkit-ops@popkit-ai
/plugin install popkit-research@popkit-ai
```

After installation, restart Claude Code and run `/popkit-dev:next` to get started.

---

## VS Code / GitHub Copilot (one-click)

[![Install in VS Code](https://img.shields.io/badge/VS_Code-Install_Server-0098FF?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=popkit&config=%7B%22command%22%3A%20%22popkit-mcp%22%2C%20%22args%22%3A%20%5B%22--transport%22%2C%20%22stdio%22%5D%7D) [![Install in VS Code Insiders](https://img.shields.io/badge/VS_Code_Insiders-Install_Server-24bfa5?style=flat-square&logo=visualstudiocode&logoColor=white)](https://insiders.vscode.dev/redirect/mcp/install?name=popkit&config=%7B%22command%22%3A%20%22popkit-mcp%22%2C%20%22args%22%3A%20%5B%22--transport%22%2C%20%22stdio%22%5D%7D&quality=insiders)

Requires `pip install popkit-mcp` first, then click the badge above.

---

## PyPI — MCP Server

Install the MCP server for use with Cursor, Codex CLI, GitHub Copilot, or any MCP-compatible client:

```bash
pip install popkit-mcp
```

### Usage

```bash
# Start with stdio transport (default for MCP clients)
popkit-mcp --transport stdio

# Start with HTTP transport for debugging
popkit-mcp --transport streamable-http --port 8080

# Specify custom packages directory
popkit-mcp --packages /path/to/popkit/packages
```

### MCP Client Configuration

**Cursor** — Add to `~/.cursor/mcp.json`:

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

**Codex CLI** — Add to `~/.codex/mcp.json`:

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

### Zero-install with uvx

If you have `uv` installed, you can run the MCP server without installing:

```bash
uvx popkit-mcp --transport stdio
```

---

## PyPI — Full Install

Install everything — CLI, shared utilities, and MCP server:

```bash
# Full install (CLI + utilities + MCP server)
pip install popkit[full]

# Or install specific components
pip install popkit           # CLI + shared utilities
pip install popkit[mcp]      # CLI + utilities + MCP server
pip install popkit-shared    # Core utilities only
pip install popkit-cli       # CLI only
```

### CLI Usage

After installing `popkit` or `popkit-cli`:

```bash
popkit --help
```

---

## For Local Development (Git Clone)

If you've cloned the repository for development and want to test local changes:

```bash
# Navigate to the repository root
cd /path/to/popkit-ai

# Install plugins from local directories
/plugin install ./packages/popkit-core
/plugin install ./packages/popkit-dev
/plugin install ./packages/popkit-ops
/plugin install ./packages/popkit-research
```

Restart Claude Code after installing local plugins.

**Note:** Local installations take precedence over marketplace installations.

---

## Version Requirements

PopKit requires **Claude Code 2.1.33+** for full feature support. Tested and verified through **CC 2.1.80**.

| Feature                      | Minimum    | Notes                                           |
| ---------------------------- | ---------- | ----------------------------------------------- |
| Core functionality           | 2.1.0      | Skill hot-reload, forked contexts               |
| Plugin auto-update control   | 2.1.2      | `FORCE_AUTOUPDATE_PLUGINS` env var              |
| Hook context injection       | 2.1.9      | PreToolUse `additionalContext`                  |
| Plugin SHA pinning           | 2.1.14     | Pin to specific git commits                     |
| Native task management       | 2.1.16     | Dependency tracking for agents                  |
| Agent memory                 | 2.1.32     | Automatic memory recording                      |
| Agent Teams                  | 2.1.32     | Native multi-agent collaboration                |
| Full feature support         | **2.1.33** | TeammateIdle/TaskCompleted hooks, memory scopes |
| PostCompact hook             | 2.1.76     | Hook fires after context compaction             |
| MCP elicitation support      | 2.1.76     | MCP servers can prompt users for input          |
| Elicitation hooks            | 2.1.76     | Elicitation + ElicitationResult hook events     |
| Worktree sparse paths        | 2.1.76     | `worktree.sparsePaths` config for worktrees     |
| `/effort` slash command      | 2.1.76     | Set agent effort level at runtime               |
| Opus 4.6 max output          | 2.1.77     | 64k default / 128k extended output tokens       |
| `claude plugin validate`     | 2.1.77     | Improved plugin validation checks               |
| Agent resume via SendMessage | 2.1.77     | `resume` replaced by `SendMessage` tool         |
| `/branch` slash command      | 2.1.77     | `/fork` renamed to `/branch`                    |
| StopFailure hook event       | 2.1.78     | Hook fires on abnormal agent stop               |
| `${CLAUDE_PLUGIN_DATA}` var  | 2.1.78     | Plugin-scoped persistent data directory         |
| Agent frontmatter extensions | 2.1.78     | `effort`, `maxTurns`, `disallowedTools`         |
| Multi-directory seed         | 2.1.79     | `CLAUDE_CODE_PLUGIN_SEED_DIR` accepts multiple  |
| 1M context support           | 2.1.79     | Opus 4.6 with 1M context window                 |

**Recommended**: Always use the latest Claude Code version for best compatibility.

**Python requirement**: Python 3.11+ for PyPI packages.

---

## Next Steps

- [Quick Start Guide](/getting-started/quick-start/)
- [Troubleshooting](/guides/troubleshooting/)
- [Core Concepts](/concepts/agents/)
