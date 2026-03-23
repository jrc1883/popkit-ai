# PopKit v2.0: LLM-Agnostic Orchestration Engine

PopKit installs once on a developer's machine and automatically integrates with any AI coding tool they use.

## Why

The March 2026 market has converged: MCP is the universal tool layer (538+ clients, 97M monthly SDK downloads). Every major AI coding tool — Claude Code, Cursor, Codex CLI, Copilot, Windsurf, Junie — supports MCP. No cross-tool plugin packaging standard exists yet. PopKit is positioned to fill that gap.

Analysis shows **88-90% of PopKit's codebase is already provider-agnostic** — the workflows, skills, agents, and shared utilities are pure behavior definitions. The coupling to Claude Code is thin: hook protocols, env vars, and tool invocation patterns.

## Architecture

```
~/.popkit/                          # POPKIT_HOME
  popkit.yaml                       # Global config
  packages/                         # Installed PopKit packages
    popkit-core/ popkit-dev/ popkit-ops/ popkit-research/ shared-py/
  providers/                        # Generated adapter output
    claude-code/                    # Symlinks to ~/.claude/plugins/
    cursor/                         # Generated MCP + rules configs
    codex/                          # Generated Codex plugin manifest
    generic-mcp/                    # Standalone MCP server config
  data/                             # Runtime state
  bin/
    popkit                          # CLI entry point
    popkit-mcp-server               # Standalone MCP server
```

## Phase 1: MCP Server + Foundation (Current)

- **MCP Server** (`packages/popkit-mcp/`) — exposes 50 skills, 24 agents, 25 commands as MCP tools, resources, and prompts
- **Provider Abstraction** (`popkit_shared/providers/`) — adapter interface with Claude Code passthrough and generic MCP adapters
- **POPKIT_HOME** — cross-platform home directory with backward-compatible resolution chain
- **CLI Skeleton** (`packages/popkit-cli/`) — `popkit install`, `popkit provider list/wire`, `popkit mcp start`
- **Universal Manifests** (`popkit-package.yaml`) — declarative package format with abstract tool categories

## Phase 2: Dual-Mode Install

- `claude plugin add popkit-core` (unchanged)
- `pip install popkit-cli && popkit install && popkit provider wire`

## Phase 3: Provider Adapters

Cursor, Codex CLI, Copilot, generic MCP — each gets a dedicated adapter.

## Phase 4: Orchestration

Task routing, cross-provider context sync, provider selection logic.
