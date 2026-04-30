> Archived from stale local branch `feat/mcp-gateway-routing` during branch cleanup on 2026-04-30. Treat status/checklists as historical unless revalidated.

# PopKit v2.0 — Phases 2-4 Design

**Date:** 2026-03-21
**Status:** Validated via brainstorming session
**Branch:** feat/v2-mcp-provider-foundation (Phase 1 committed)

---

## Phase 1 (DONE): Foundation

Committed as `52d8bcd` on `feat/v2-mcp-provider-foundation`:

- MCP server package (popkit-mcp) — 5 tools, dynamic resources/prompts
- Provider abstraction layer (shared-py/providers/) — adapter ABC, Claude Code + generic MCP
- CLI skeleton (popkit-cli) — install, provider list/wire, mcp start
- POPKIT_HOME cross-platform resolution (home.py, updated plugin_data.py)
- Universal manifests (popkit-package.yaml) for all 4 packages
- 68 new tests, 1597 total passing

---

## Phase 2: Full MCP End-to-End + Cursor Validation

### 2a. MCP Server Hardening

**Goal:** Server works reliably with real MCP clients.

- [ ] Test stdio transport with MCP inspector (`mcp dev`)
- [ ] Test SSE transport for browser/debug clients
- [ ] Add `--host` binding for network access control
- [ ] Graceful shutdown on SIGTERM/SIGINT
- [ ] Error handling: tool failures return structured errors, not tracebacks
- [ ] Missing packages degrade gracefully
- [ ] Cache `build_registry()` result at startup, add `popkit/reload` tool
- [ ] In-memory file content caching with mtime checks
- [ ] Add `popkit/execute_skill` tool — runs workflow engine server-side (for clients that can't interpret SKILL.md)
- [ ] Keep `popkit/run_skill` as prompt-return (for capable LLMs)
- [ ] Write integration tests using MCP Python SDK test client

### 2b. Cursor Provider Adapter

**Goal:** A Cursor user runs `popkit provider wire` and can invoke PopKit skills/agents from Cursor.

**Config strategy: Global + project**

- MCP server connection → `~/.cursor/mcp.json` (global, works in every project)
- Agent rules → `.cursor/rules/` (per-project, when explicitly wired)
- Matches Cursor's own architecture (global vs project config, project wins)

**Files to create:**

- `packages/shared-py/popkit_shared/providers/cursor.py` — `CursorAdapter(ProviderAdapter)`
  - Detection: `.cursor/` dir, `cursor` on PATH
  - `generate_config()`: creates `mcp.json` entry + `.cursorrules` files from AGENT.md
  - `install()`: writes global MCP config, project rules
  - Tool mappings already drafted in `tool_mapping.py`

**Safety hooks as MCP tools:**

- Cursor doesn't have Claude Code's hook system
- Expose validation logic as MCP tools: `popkit/validate_command`, `popkit/check_security`
- Generated `.cursor/rules/popkit-safety.mdc` instructs Cursor to call validation before dangerous operations

### 2c. Dual-Mode pip Install

**Packaging strategy: Pattern 2+5 hybrid**

Two PyPI packages:

1. `popkit-mcp` — standalone MCP server, zero-config for Cursor/Codex users
   - `uvx popkit-mcp` or in mcp.json: `"command": "uvx", "args": ["popkit-mcp"]`
   - Includes: server.py, tool_registry, resources, prompts + popkit-shared dependency

2. `popkit` — full CLI with pip extras
   - `pip install popkit` → CLI + core package
   - `pip install popkit[full]` → CLI + all packages (core, dev, ops, research)
   - Entry point: `popkit` command

**Install flow:**

```
pip install popkit          # or: pip install popkit[full]
popkit install              # creates ~/.popkit/, symlinks packages
popkit provider wire        # detects Cursor/CC/Codex, generates configs
```

**Files to create/modify:**

- Root `pyproject.toml` for the `popkit` meta-package
- `packages/popkit-mcp/pyproject.toml` — update for standalone PyPI publishing
- `packages/popkit-cli/popkit_cli/commands/install.py` — add GitHub release download
- New: `packages/popkit-cli/popkit_cli/commands/update.py`

### 2d. Hook Protocol Normalization

**Goal:** Hooks produce provider-agnostic responses.

- [ ] Extend `StatelessHook` with `provider` property and `respond()` method returning `HookResponse`
- [ ] Backward compatible: raw JSON output still works (Claude Code passthrough)
- [ ] For Cursor: expose hook logic as MCP tools (`popkit/validate_command`, `popkit/check_security`)
- [ ] For generic MCP: hooks run inside `execute_skill` flow
- [ ] Generate `.cursor/rules/popkit-safety.mdc` from hook definitions

---

## Phase 3: Provider Adapters

Repeat the Cursor pattern for each tool:

| Adapter         | Config Location                                   | Rules Equivalent          | Priority        |
| --------------- | ------------------------------------------------- | ------------------------- | --------------- |
| **Codex CLI**   | `~/.codex/config.toml`                            | `AGENTS.md` generation    | High            |
| **Copilot**     | `~/.copilot/mcp-config.json` + `.vscode/mcp.json` | `copilot-instructions.md` | Medium          |
| **Generic MCP** | Standalone server config                          | N/A (MCP tools only)      | High (fallback) |

Each adapter: detect → generate global MCP config → generate per-project rules → install/uninstall.

**Additional deliverables:**

- systemd/launchd service files for MCP server daemon
- Docker container for MCP server
- Harden generic MCP adapter with startup scripts

---

## Phase 4: Orchestration & Routing

### Decision: NEEDS RESEARCH

Phase 4's routing/coordination layer requires a dedicated deep-dive audit before committing to a direction.

**Existing infrastructure to audit:**

- `semantic_router.py` — NLP-based agent routing with embedding similarity
- `embedding_store.py` — SQLite vector storage with cosine similarity
- `redis_interface.py` — Abstract Redis client (Upstash, local, ElastiCache)
- `voyage_client.py` — Voyage AI embeddings
- `cloud_agent_search.py` — Upstash Vector cloud search
- `expertise_manager.py` — Agent expertise tracking
- `upstash_telemetry.py` — Telemetry backend
- `research_index.py` — Knowledge indexing

**Questions to resolve in research:**

1. Is the semantic router's logic sound? Can it route between providers, not just agents?
2. What's the state of the embedding/vector infrastructure — does it actually work end-to-end?
3. Can Redis caches serve as shared agent knowledge stores (patterns, bugs, embeddings)?
4. Is LSP integration feasible for code-aware routing decisions?
5. What role does E2B play in sandboxed agent execution?
6. How does Optimus's routing compare — can patterns be ported?

**Vision (from Joseph):**
Agents at hook points report to Redis caches (patterns, bugs, knowledge). Embeddings enable semantic matching. LSPs provide code intelligence. Routing is fully automatic — PopKit picks the best provider+agent for each task.

**Action:** Schedule dedicated research session to audit existing code, test it, and design the v2 routing architecture.

---

## Implementation Order

1. **Phase 2a** — MCP hardening (prove the server works)
2. **Phase 2b** — Cursor adapter (prove cross-tool value)
3. **Phase 2c** — pip install (unlock non-Claude-Code users)
4. **Phase 2d** — Hook normalization (safety across providers)
5. **Phase 3** — Codex + Copilot adapters
6. **Phase 4** — Research first, then routing engine

---

## Key Design Decisions Made

1. **MCP tools: both prompt-return and execute** — `run_skill` returns SKILL.md for capable LLMs, `execute_skill` runs workflow engine server-side
2. **Cursor config: global + project** — MCP server global, agent rules per-project
3. **Packaging: Pattern 2+5 hybrid** — `popkit-mcp` as standalone PyPI (uvx), `popkit` with pip extras
4. **Hooks for non-CC: MCP tools + rules** — Expose validation as MCP tools, Cursor rules enforce calling them
5. **Phase 4 routing: needs research** — Existing semantic_router/embedding infrastructure needs audit before deciding build-on vs rebuild

---

## Sources

- [Cursor MCP Docs](https://cursor.com/docs/context/mcp)
- [VS Code MCP Servers](https://code.visualstudio.com/docs/copilot/customization/mcp-servers)
- [One MCP Config for All Tools (chezmoi)](https://dev.to/dotwee/one-mcp-configuration-for-codex-claude-cursor-and-copilot-with-chezmoi-925)
- [Distributing MCP Servers (Speakeasy)](https://www.speakeasy.com/mcp/distributing-mcp-servers)
- [Python Packaging: Creating Plugins](https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/)
- [GitHub MCP Server Installation](https://github.com/github/github-mcp-server/blob/main/docs/installation-guides/install-cursor.md)
- [MCP Configuration Best Practices (TrueFoundry)](https://www.truefoundry.com/blog/mcp-servers-in-cursor-setup-configuration-and-security-guide)
