---
title: Installation
description: How to install PopKit plugins for Claude Code
---

# Installation

PopKit is published as a GitHub-based marketplace. Install it in two steps:

## Step 1: Add the Marketplace (One-time Setup)

```bash
/plugin marketplace add jrc1883/popkit-claude
```

## Step 2: Install Plugins

Install all plugins for full functionality:

```bash
# Install all plugins
/plugin install popkit-core@popkit-claude
/plugin install popkit-dev@popkit-claude
/plugin install popkit-ops@popkit-claude
/plugin install popkit-research@popkit-claude
```

After installation, restart Claude Code and run `/popkit-dev:next` to get started.

## For Local Development (Git Clone)

If you've cloned this repository for development and want to test local changes:

```bash
# Navigate to the repository root
cd /path/to/popkit-claude

# Install plugins from local directories
/plugin install ./packages/popkit-core
/plugin install ./packages/popkit-dev
/plugin install ./packages/popkit-ops
/plugin install ./packages/popkit-research
```

Restart Claude Code after installing local plugins.

**Note:** Local installations take precedence over marketplace installations.

## Version Requirements

PopKit requires **Claude Code 2.1.33+** for full feature support. Tested and verified through **CC 2.1.79**.

| Feature                        | Minimum    | Notes                                           |
| ------------------------------ | ---------- | ----------------------------------------------- |
| Core functionality             | 2.1.0      | Skill hot-reload, forked contexts               |
| Plugin auto-update control     | 2.1.2      | `FORCE_AUTOUPDATE_PLUGINS` env var              |
| Hook context injection         | 2.1.9      | PreToolUse `additionalContext`                  |
| Plugin SHA pinning             | 2.1.14     | Pin to specific git commits                     |
| Native task management         | 2.1.16     | Dependency tracking for agents                  |
| Agent memory                   | 2.1.32     | Automatic memory recording                      |
| Agent Teams                    | 2.1.32     | Native multi-agent collaboration                |
| Full feature support           | **2.1.33** | TeammateIdle/TaskCompleted hooks, memory scopes |
| PostCompact hook               | 2.1.76     | Hook fires after context compaction             |
| MCP elicitation support        | 2.1.76     | MCP servers can prompt users for input          |
| Elicitation hooks              | 2.1.76     | Elicitation + ElicitationResult hook events     |
| Worktree sparse paths          | 2.1.76     | `worktree.sparsePaths` config for worktrees     |
| `/effort` slash command        | 2.1.76     | Set agent effort level at runtime               |
| Opus 4.6 max output            | 2.1.77     | 64k default / 128k extended output tokens       |
| `claude plugin validate`       | 2.1.77     | Improved plugin validation checks               |
| Agent resume via SendMessage   | 2.1.77     | `resume` replaced by `SendMessage` tool         |
| `/branch` slash command        | 2.1.77     | `/fork` renamed to `/branch`                    |
| StopFailure hook event         | 2.1.78     | Hook fires on abnormal agent stop               |
| `${CLAUDE_PLUGIN_DATA}` var    | 2.1.78     | Plugin-scoped persistent data directory         |
| Agent frontmatter extensions   | 2.1.78     | `effort`, `maxTurns`, `disallowedTools`         |
| Multi-directory seed           | 2.1.79     | `CLAUDE_CODE_PLUGIN_SEED_DIR` accepts multiple  |
| 1M context support             | 2.1.79     | Opus 4.6 with 1M context window                 |

**Recommended**: Always use the latest Claude Code version for best compatibility.

## Next Steps

- [Quick Start Guide](/getting-started/quick-start/)
- [Core Concepts](/concepts/agents/)
