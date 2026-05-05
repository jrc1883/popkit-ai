---
title: Architecture
description: How PopKit works across AI coding tools — packages, providers, and MCP
---

# Architecture

PopKit is an LLM-agnostic orchestration engine. It installs once and works with any AI coding tool that supports MCP.

## The Problem

AI coding tools are converging on MCP as the universal tool layer, but no cross-tool plugin standard exists. Skills, workflows, and agents built for one tool don't transfer to another.

## PopKit's Approach

PopKit separates **what** (skills, agents, commands) from **how** (provider-specific integration). The same 50 skills, 24 agents, and 25 commands work whether you're using Claude Code, Cursor, Codex CLI, or Copilot.

```
┌─────────────────────────────────────────────┐
│              Your AI Coding Tool            │
│   (Claude Code, Cursor, Codex CLI, etc.)    │
└──────────────────┬──────────────────────────┘
                   │
          ┌────────┴────────┐
          │ Provider Adapter │
          └────────┬────────┘
                   │
┌──────────────────┴──────────────────────────┐
│              PopKit Core                     │
│   Skills · Agents · Commands · Hooks         │
│   (provider-agnostic behavior definitions)   │
└──────────────────────────────────────────────┘
```

## Packages

PopKit is distributed as 4 PyPI packages:

| Package           | What it provides                            | Install                     |
| ----------------- | ------------------------------------------- | --------------------------- |
| **popkit-shared** | Core utilities, providers, schemas, storage | `pip install popkit-shared` |
| **popkit-mcp**    | MCP server for non-Claude Code tools        | `pip install popkit-mcp`    |
| **popkit-cli**    | CLI for install, configure, manage          | `pip install popkit-cli`    |
| **popkit**        | Meta-package (all of the above)             | `pip install popkit[full]`  |

For Claude Code users, PopKit also installs as a plugin marketplace with 4 plugin packages: popkit-core, popkit-dev, popkit-ops, and popkit-research.

## Provider Adapters

Each AI coding tool has a dedicated adapter that translates PopKit's abstract capabilities into the tool's native format:

| Provider           | Integration Method          | Config                                      |
| ------------------ | --------------------------- | ------------------------------------------- |
| **Claude Code**    | Plugin marketplace (native) | `/plugin install popkit-core@popkit-ai` |
| **Cursor**         | MCP server (stdio)          | `~/.cursor/mcp.json`                        |
| **Codex CLI**      | MCP server (stdio)          | `~/.codex/config.toml`                      |
| **GitHub Copilot** | MCP server (stdio)          | `~/.copilot/mcp-config.json`                |
| **VS Code**        | MCP server (stdio)          | `.vscode/mcp.json`                          |
| **Generic MCP**    | Any MCP-compatible client   | Standard MCP config                         |

See [MCP Provider Setup](/guides/mcp-providers/) for configuration details.

## MCP Server

The `popkit-mcp` server exposes PopKit's capabilities as standard MCP primitives:

**Tools** (callable by the AI):

- `run_skill` — Returns a skill's prompt for the AI to follow
- `execute_skill` — Runs a skill's script server-side and returns results
- `spawn_agent` — Returns an agent's system prompt
- `power_mode` — Multi-agent coordination
- `get_context` — Project state (git, issues, session)
- `validate_command` — Safety checks before execution
- `health_check` — Server diagnostics
- `reload` — Hot-reload skills and agents

**Resources** (discoverable catalogs):

- `list_skills` — All available skills with descriptions
- `list_agents` — All available agents with tiers and triggers

## How It Works in Practice

**In Claude Code:** You use slash commands (`/popkit-dev:next`, `/popkit-dev:routine morning`). PopKit runs as a native plugin with full hook integration.

**In Cursor/Codex/Copilot:** You talk naturally ("run the morning routine", "what should I work on next?"). The AI calls PopKit's MCP tools automatically based on your request. There are no slash commands — the AI decides when to use PopKit.

The same skills and agents power both experiences. The difference is the interaction model, not the capabilities.

## Directory Structure

PopKit resolves its home directory through a compatibility chain:

```
~/.popkit/                    # POPKIT_HOME (preferred)
  popkit.yaml                 # Global config
  packages/                   # Installed packages
  providers/                  # Generated provider configs
  data/                       # Runtime state

~/.claude/plugins/            # Claude Code plugin location (legacy)
```

## What's Provider-Agnostic

About 90% of PopKit's codebase is already provider-agnostic:

- All 50 skill definitions (SKILL.md files with frontmatter)
- All 24 agent definitions (AGENT.md files with system prompts)
- All 25 command definitions
- Shared Python utilities (embedding, routing, state management)
- Hook logic (Python scripts with JSON stdin/stdout protocol)

The remaining 10% is provider-specific: env var names, tool invocation patterns, and hook registration formats.
