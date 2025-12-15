# Cross-Platform CLI Investigation

**Branch**: `claude/research-cli-tools-Dg3ui`
**Epic**: #240 | **Issue**: #243
**Date**: 2025-12-15
**Status**: Complete Analysis

---

## Executive Summary

The cross-platform CLI investigation examines PopKit's evolution from Claude Code-specific plugin to **unified platform supporting multiple IDEs, models, and deployment targets** via the **Textual framework**.

### Recommendation: **DEFER TO v2.0** (Strategic Expansion)

Cross-platform CLI is foundational for PopKit's stated vision but introduces significant complexity and infrastructure dependencies that are **not critical for v1.0 marketplace launch**.

---

## 1. What Exists Today (Master)

### Current: Claude Code Plugin Only

**Architecture**:
- Single-IDE plugin (`jrc1883/popkit-claude`)
- 30 agents, 66 skills, 24 commands
- Hooks: SessionStart, UserPromptSubmit, PreToolUse, PostToolUse
- Power Mode: Redis or file-based coordination

**Constraints**:
- ❌ Can't use in VS Code, Cursor, Windsurf
- ❌ Can't use in terminal, CI/CD, scripts
- ❌ Can't use with GPT, Gemini (Claude-only)
- ❌ Can't orchestrate across multiple IDEs

### Future Vision (from CLAUDE.md)

> PopKit will evolve to support:
> - Multiple AI models (Claude, GPT, Gemini, local LLMs)
> - Multiple IDEs (VS Code, Cursor, Windsurf, JetBrains)
> - **Standalone CLI (installable via pip/npm/bun)**
> - Shared cloud backend for cross-project learning

---

## 2. What's New in Branch

### Textual-Based Standalone CLI

**Key Innovation**: Using Textual (Python TUI framework) for:
- Cross-platform terminal UI (Windows, macOS, Linux)
- Rich widgets (buttons, trees, data tables, text areas)
- 16.7M color support, mouse input, animations
- MIT licensed, production-ready
- Real-world adoption: Posting, Toolong, Memray, Harlequin

### Multi-IDE Architecture Pattern

```
┌─────────────────────────────────────────────┐
│ PopKit Unified Platform                     │
├─────────────────────────────────────────────┤
│  Claude Code | VS Code | Cursor | CLI      │
│  Plugin      | (MCP)   | (MCP)  | (Textual)│
│       └──────────┬──────────┘              │
│         [MCP Router / Orchestration]       │
│                  │                          │
│      PopKit Cloud API (Cloudflare)        │
│      • Model routing (Claude/GPT/Gemini)   │
│      • Agent orchestration                 │
│      • Pattern storage & learning          │
│      • Cross-IDE synchronization           │
└─────────────────────────────────────────────┘
```

### MCP Server Integration

**Model Context Protocol (MCP)** as cross-IDE bridge:
- **VS Code**: MCP support via Chat > MCP option
- **Cursor**: `.cursor/mcp.json` configuration
- **Windsurf**: `~/.codeium/windsurf/mcp_config.json`
- **JetBrains**: 2025.2+ integrated MCP server

**PopKit Pattern**: MCP template already exists in `packages/plugin/templates/mcp-server/`

---

## 3. Dependencies

### Infrastructure Gaps (Blocking v1.0)

| Dependency | Status | Required for CLI |
|------------|--------|-----------------|
| Textual framework | ✅ Exists | Yes |
| MCP server pattern | ⚠️ Partial | Extend |
| Cross-platform auth | ❌ Missing | **Build new** |
| Session sync | ❌ Missing | **Build new** |
| Model routing | ❌ Missing | **Build new** |

### Related Branches

- **#241 Multi-Model Dispatch**: Required for model abstraction
- **#242 Async Orchestration**: Enables background tasks
- **#244 Skill Structure**: Should decouple from Claude Code hooks

---

## 4. Integration Complexity

### Effort Estimate

| Phase | Effort | Timeline |
|-------|--------|----------|
| v1.0 Placeholder | Low | 1-2 weeks |
| v2.0 Phase 1 (CLI) | High | 6-8 weeks |
| v2.0 Phase 2 (Multi-IDE) | High | 8-10 weeks |
| v2.0 Phase 3 (Distribution) | Medium | 4-6 weeks |
| **Total v2.0** | **Epic** | **4-6 months** |

### Files Affected

**v1.0**: 2-3 documentation files only

**v2.0**: 40-60 new + 15-25 modified

---

## 5. Value Proposition

### Problems Solved

**Current Limitations**:
1. ❌ Can't use PopKit in VS Code, Cursor, Windsurf
2. ❌ Can't use in terminals, CI/CD pipelines
3. ❌ Can't use with other models (GPT, Gemini)
4. ❌ Can't orchestrate across multiple IDEs

**CLI Enables**:
1. ✅ Works in any IDE (via MCP)
2. ✅ Works in terminal, automation contexts
3. ✅ Model-agnostic routing via cloud backend
4. ✅ Cross-tool orchestration
5. ✅ Broader distribution: `pip install popkit`

### User Impact

**High Impact: v2.0 Strategic**
- VS Code/Cursor users (60-70% of market) can now use PopKit
- DevOps workflows via CLI automation
- Research/academic with local LLM support

**Lower Priority: v1.0 Marketplace**
- Claude Code users already have plugin (sufficient for MVP)

---

## 6. Risks

### Technical Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Cross-platform testing | High | CI matrix testing |
| Session sync conflicts | High | Timestamps + version control |
| Model API costs | Medium | Design cost controls |
| Terminal compatibility | Medium | Target modern terminals |

### Business Risks

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Fragmented UX | High | Design system first |
| Feature parity | Medium | Version management |
| Support burden | Medium | Staged rollout |
| Over-scoping v2.0 | High | Phased implementation |

---

## 7. Recommendation

### Decision: DEFER TO v2.0

```
Status: DEFER TO v2.0
Rationale: Complex infrastructure, not critical for v1.0
Timeline: Post-v1.0 marketplace launch
```

### Why Not v1.0?

**✅ Reasons to Defer**:
1. **v1.0 Focus**: Core Claude Code plugin quality
2. **Infrastructure Gaps**: Auth, session sync, model abstraction missing
3. **Architectural Clarity**: Needs more design work
4. **Market Priority**: Plugin users are primary market
5. **Risk/Reward**: 4-6 months effort, deferred benefit

### Why v2.0 Makes Sense

**✅ Reasons for v2.0**:
1. **Platform Vision**: Foundational for stated future
2. **Market Opportunity**: VS Code, Cursor, Windsurf all support MCP
3. **Infrastructure Readiness**: By v2.0, prerequisites ready
4. **Phased Approach**: Can break into manageable chunks

### v2.0 Roadmap (If Approved)

```
Q1 2026 - CLI Alpha (Phase 1)
├── CLI command parity
├── Textual TUI interface
└── Internal testing

Q2 2026 - IDE Bridge Beta (Phase 2)
├── MCP server for CLI
├── VS Code integration
└── Beta testing

Q3 2026 - Expansion RC (Phase 3)
├── Cursor integration
├── Windsurf integration
├── JetBrains integration
└── Packaging (pip/npm/bun)

Q4 2026 - Release
├── Multi-IDE stable
├── Cloud orchestration
└── General availability
```

---

## 8. Key Design Decisions

### Decision 1: Textual vs Alternatives
**Choice**: Textual
**Why**: Python native, production-ready, cross-platform, MIT licensed

### Decision 2: MCP vs Direct IDE Integration
**Choice**: MCP as primary bridge
**Why**: Standard protocol, decouples from IDE details

### Decision 3: Cloud-Backed vs Standalone
**Choice**: Cloud-backed for v2.0
**Why**: Enables cross-tool sync, pattern learning, premium features

### Decision 4: When to Implement
**Choice**: v2.0 (not v1.0)
**Why**: v1.0 must establish plugin quality first, prerequisites not ready

---

## 9. Open Questions

### UX Questions
1. Should `popkit` show interactive TUI by default or shell-like interface?
2. How does context flow when switching between CLI and VS Code?
3. Offline mode UX when cloud features needed?

### Architecture Questions
1. What's the model abstraction interface?
2. How to handle team accounts and multiple licenses?
3. Should all plugin features be available in CLI?

### Infrastructure Questions
1. Cost per user for cross-IDE session sync?
2. Can v2.0 CLI coexist with v1.0 plugin during transition?

---

## Conclusion

Cross-platform CLI is **strategically important** for PopKit's multi-IDE vision but **not critical for v1.0 marketplace launch**.

**Recommended approach**:
1. **v1.0** (now): Focus on Claude Code plugin excellence
2. **v2.0 alpha** (Q1 2026): Prototype CLI + Textual TUI
3. **v2.0 beta** (Q2 2026): Add MCP bridge + VS Code
4. **v2.0 release** (Q4 2026): Full multi-IDE support

This phased approach validates plugin quality first, builds required infrastructure, and delivers higher-quality cross-platform experience.

---

**Document Status**: Investigation Complete
**Recommendation**: DEFER TO v2.0
**Ready for**: Epic synthesis, v2.0 roadmap planning
