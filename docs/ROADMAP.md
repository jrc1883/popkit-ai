# PopKit Roadmap

**Last Updated:** 2026-04-30
**Current Version:** 1.0.0-beta.13
**Current Focus:** v2 LLM-agnostic orchestration engine — multi-provider support, PyPI publishing, documentation.

## Principles

- Keep public documentation user-facing and low-noise.
- Keep implementation planning in issues/PRs (or private planning systems), not long-lived markdown snapshots.
- Prefer stable docs over status tables that go stale quickly.

## Completed (v2 Phase 1-3)

1. MCP server (`popkit-mcp`) — exposes skills, agents, commands as MCP tools.
2. Provider adapters — Claude Code, Cursor, Codex CLI, Copilot, generic MCP.
3. PyPI publishing — `popkit`, `popkit-shared`, `popkit-mcp`, `popkit-cli` all live on PyPI.
4. CLI tool (`popkit-cli`) — install, configure, manage PopKit across AI coding tools.
5. Hook normalization — cross-platform consistency for all hook events.

## Near-Term Priorities

1. Documentation quality — consolidate and update all docs for v2 architecture.
2. Provider validation — real-world testing with Cursor, Codex CLI, Copilot.
3. Phase 4: Semantic routing audit — optimize embedding search, deploy cloud backend.
4. Onboarding DX (Issue #49) — streamline first-run experience.

## Future

- PopKit Cloud backend (Upstash Vector for semantic agent discovery).
- Rename from `popkit-claude` to `popkit` (repo and brand).
- Cross-platform installer (auto-detect and wire into installed AI tools).
- See `docs/VISION.md` for the full architectural direction.

## Source Of Truth

- Active work: GitHub Issues and PRs.
- User docs: `packages/docs` (deployed to popkit.unjoe.me).
- Vision: `docs/VISION.md`.
- Architecture deep dives: `docs/AGENT_ROUTING_GUIDE.md`, `docs/POWER_MODE_ASYNC.md`, `docs/MCP_WILDCARD_PERMISSIONS.md`.
