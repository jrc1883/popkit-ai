# PopKit Cross-Platform Architecture Vision
**Research Document | v1.0 | 2025-12-14**

---

## Executive Summary

This document explores PopKit's evolution from a Claude Code plugin to a **multi-platform, CLI-first orchestration engine** that can launch and coordinate development workflows across Claude Code, other IDEs, web interfaces, and standalone terminals—all backed by a unified cloud state management layer using Upstash Redis and long-term storage.

**Core Insight**: Instead of reimplementing PopKit for each platform, build a **platform-agnostic orchestration layer** (PopKit CLI) that communicates via cloud APIs and local state, with platform-specific frontends (Claude Code plugin, VS Code extension, Cursor, web UI, etc.) that delegate to this central orchestrator.

---

## Design Inspiration Analysis

### 1. **Textual Framework Pattern**
**What it does**: Provides sophisticated terminal UIs using web-like patterns (CSS, components, events)

**Key insight for PopKit**:
- Textual enables running the **same app** in terminal AND web browser with minimal code changes
- This directly enables PopKit's cross-platform vision: build once, deploy to 10+ surfaces
- Architecture: `TextualApp` → web browser (auto), terminal (auto), Claude Code plugin (custom wrapper)

**Application**:
```
PopKit CLI (Textual-based)
├── Terminal mode (native)
├── Web mode (Textual SSR)
├── Claude Code plugin (MCP bridge)
├── VS Code webview (Textual SSR)
└── Cursor sidepanel (Textual SSR)
```

### 2. **Posting API Client Pattern**
**What it does**: Terminal HTTP client with excellent UX/DX

**Key insight for PopKit**:
- Progressive disclosure: vim keybindings + command palette for power users
- Local YAML storage (git-friendly, version controllable)
- Python extensibility (pre/post-request scripts)
- Seamless $EDITOR integration

**Application to PopKit**:
- Command palette for skill/agent discovery (`⌘ K` or Ctrl-P)
- Vim keybindings as opt-in power mode
- Local `.popkit/` config that's git-friendly and version-controllable
- Python/shell script hooks for custom workflows (extend existing hook system)
- Editor integration: launch native editor for complex tasks

### 3. **Harlequin SQL IDE Pattern**
**What it does**: Domain-focused terminal IDE with plugin architecture

**Key insight for PopKit**:
- **Plugin adapters** for domain-specific extensions (SQL adapters for different databases)
- Unified interface with theme consistency
- Domain knowledge embedded in UI (SQL-specific context menu, autocompletion)

**Application to PopKit**:
- Project-specific "adapters" (framework adapters: Next.js, Rails, Django, etc.)
- Custom skills loaded per-project via MCP servers
- Theme consistency across platforms (light/dark with brand colors)
- Specialized UI for different workflows (feature dev, bug fixing, refactoring, etc.)

### 4. **Multi-Model Orchestration Pattern (Claude + Gemini)**
**What it does**: Route tasks to best-fit AI model based on task characteristics

**Key insight for PopKit**:
- Claude excels at orchestration, structured reasoning, context awareness
- Gemini excels at large file analysis (1M+ tokens), document processing
- **Unified interface**: User doesn't care which model runs the task

**Application to PopKit v2.0**:
```
User Task
  ├─ [Claude Orchestrator] Analyze requirements
  ├─ Route to best agent:
  │  ├─ [Claude] Code review, architecture decisions, testing strategy
  │  ├─ [Gemini] Large codebase analysis, PDF processing, bulk data review
  │  └─ [OpenAI] Code generation (v2.0 future)
  └─ [Claude] Synthesize results + present to user
```

---

## Proposed Architecture: PopKit Platform v2.0

### Layer 1: Cloud Backbone (Existing + Enhanced)

```
┌─────────────────────────────────────────────────────┐
│ PopKit Cloud API (Cloudflare Workers)               │
│ api.thehouseofdeals.com                             │
├─────────────────────────────────────────────────────┤
│ ┌──────────────────┐  ┌──────────────────────────┐ │
│ │ Auth/Identity    │  │ Rate Limiting & Routing  │ │
│ └──────────────────┘  └──────────────────────────┘ │
└─────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────┐
│ Data Layer (Upstash)                                │
├─────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────┐  │
│ │ Redis (Hot Tier - Real-time coordination)     │  │
│ │  • Agent coordination (pub/sub)                │  │
│ │  • Session state (in-flight workflows)         │  │
│ │  • Pattern cache (recently learned patterns)   │  │
│ │  • TTL: 24 hours                              │  │
│ └────────────────────────────────────────────────┘  │
│ ┌────────────────────────────────────────────────┐  │
│ │ Vector DB (Semantic Layer)                     │  │
│ │  • Project embeddings                          │  │
│ │  • Skill/agent semantic search                 │  │
│ │  • Code pattern embeddings                     │  │
│ │  • Multi-model compatible                      │  │
│ └────────────────────────────────────────────────┘  │
│ ┌────────────────────────────────────────────────┐  │
│ │ Postgres (Cold Tier - Long-term storage)      │  │
│ │  • Project metadata & configuration             │  │
│ │  • Workflow history (30-90 day retention)      │  │
│ │  • Learned patterns (anonymized)               │  │
│ │  • User preferences & settings                 │  │
│ │  • Billing & entitlements                      │  │
│ └────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

**New responsibilities**:
- `POST /projects/{id}/state` - Store/restore cross-platform session state
- `GET /workflows/{id}/status` - Real-time workflow coordination
- `POST /analytics/session` - Aggregate metrics from all platforms
- `GET /patterns/suggest` - Query learned patterns from all users

### Layer 2: PopKit CLI (Command-Line Orchestrator) - NEW

```
┌─────────────────────────────────────────────────────┐
│ PopKit CLI / TUI (Python + Textual)                 │
│ `pip install popkit` or `npm install -g popkit-cli` │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ Textual Application Layer                   │   │
│  │  • Unified TUI interface (terminal)         │   │
│  │  • Web server (SSR for other frontends)     │   │
│  │  • MCP server (for IDE integrations)        │   │
│  └─────────────────────────────────────────────┘   │
│           ↓                                        │
│  ┌─────────────────────────────────────────────┐   │
│  │ Orchestration Engine                        │   │
│  │  • Workflow routing (which agent runs task) │   │
│  │  • Multi-model delegation (Claude/Gemini)   │   │
│  │  • Hook execution (pre/post workflow)       │   │
│  │  • Local state management                   │   │
│  └─────────────────────────────────────────────┘   │
│           ↓                                        │
│  ┌─────────────────────────────────────────────┐   │
│  │ Local Storage Layer (~/.popkit)             │   │
│  │  • config.yml (git-friendly settings)       │   │
│  │  • profiles/ (per-project configs)          │   │
│  │  • cache/ (embeddings, patterns)            │   │
│  │  • sessions/ (workflow history)             │   │
│  │  • state.json (current session state)       │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Responsibilities**:
- Main entry point for PopKit workflows (`popkit feature-dev`, `popkit bug-fix`)
- Local command execution (git, npm, etc.) with sandboxing
- Workflow state persistence (can pause/resume across sessions)
- Multi-session support (multiple projects running in parallel via background threads)
- Integration with Claude Code, VS Code, Cursor, web UI via standardized APIs

### Layer 3: Platform Integrations (Cloud ↔ PopKit CLI)

#### 3a. Claude Code Plugin (Existing)
```
User in Claude Code
    ↓
/popkit:feature-dev command
    ↓
[Plugin] → POST /projects/{id}/launch → [PopKit CLI]
           (send requirements, workspace context)
    ↓
[PopKit CLI] Runs workflow locally
    ↓
[CLI] → POST /projects/{id}/sync → [Plugin]
        (stream updates, request approvals)
    ↓
[Plugin] Display results in Claude Code editor
```

**Benefits**:
- Claude Code keeps its AI orchestration capabilities
- PopKit CLI handles execution details
- Both can run independently or together

#### 3b. VS Code Extension (NEW)
```
User in VS Code
    ↓
PopKit Sidebar Panel (Textual SSR webview)
    ↓
[Extension] ↔ PopKit Cloud API
             ↔ Local PopKit CLI (if installed)
    ↓
Execute workflows or delegate to CLI for complex tasks
```

#### 3c. Web Dashboard (NEW)
```
https://app.popkit.dev/workspace
    ↓
[Web UI] (Textual SSR + React for complex sections)
    ↓
Real-time workflow monitoring
Session management
Cross-platform project sync
```

#### 3d. Cursor/Windsurf (v2.0 Future)
```
Same as VS Code pattern, via native sidepanel APIs
```

---

## State Management Strategy

### Short-Term State (In-Flight Workflows)
**Storage**: Upstash Redis with 24-hour TTL
**Use cases**:
- Multi-agent coordination (Power Mode via pub/sub)
- Session checkpoints (pause/resume within session)
- Real-time sync between platforms

**Schema**:
```json
{
  "workflow_id": "feat-auth-123",
  "status": "in_progress",
  "current_agent": "code-architect",
  "checkpoint": {
    "phase": 2,
    "decisions": [...],
    "generated_code": "..."
  },
  "platform_sync": {
    "claude_code": { "last_sync": "2025-12-14T10:30:00Z", "approved": true },
    "vscode": { "last_sync": "2025-12-14T10:31:00Z", "viewing": true }
  }
}
```

**Accessed by**:
- PopKit CLI (primary)
- Plugin via Cloud API
- Multiple platforms for real-time sync

### Medium-Term State (30-Day History)
**Storage**: Postgres + Vector embeddings
**Use cases**:
- Workflow history & replay
- Pattern learning
- User analytics
- Debug logs

**Cleanup**: Automatic archival after 30 days (configurable)

### Long-Term State (Permanent)
**Storage**: Postgres with 90+ day retention
**Use cases**:
- Project-specific learned patterns
- User preferences
- Billing/entitlements
- Compliance & audit logs

---

## Cross-Platform Workflow Coordination

### Example: Feature Development (Start in Claude Code, Continue in VS Code)

```
1. User in Claude Code: /popkit:feature-dev
   ├─ Requirements capture via Claude conversation
   └─ Create workflow, store in Redis

2. Cloud API syncs to all platforms
   ├─ Push notification to VS Code extension
   └─ Update web dashboard in real-time

3. User switches to VS Code
   ├─ Open PopKit sidebar
   ├─ See feature workflow in progress
   └─ Continue from checkpoint

4. During implementation
   ├─ CLI runs tests locally
   ├─ Stream results back to Plugin + VS Code
   ├─ Plugin prompts for approval (if needed)
   └─ VS Code shows inline gutter feedback

5. When complete
   ├─ All platforms show completion status
   ├─ Workflow archived to Postgres
   ├─ Patterns extracted and embedded
   └─ User feedback collected across platforms
```

**Key enabler**: Stateless message protocol
- Each message carries full context (workflow ID, current state, decision history)
- No tight coupling between platforms
- Can add new platforms without changing existing ones

---

## PopKit CLI Design Patterns (Inspired by Posting + Harlequin)

### 1. Command Palette UX
```
$ popkit
┌─────────────────────────────────────────┐
│ PopKit v2.0 Orchestration Engine         │
├─────────────────────────────────────────┤
│ > Feature development                   │
│   Bug fixing                             │
│   Code review                            │
│   Performance optimization               │
│   [Other agents...]                      │
│   ⚙️  Settings                            │
│   📚 Documentation                        │
└─────────────────────────────────────────┘
```

### 2. Vim-Friendly Power Mode
```
$ popkit --vim                    # Enable vim keybindings
$ popkit --no-mouse               # Keyboard only
$ popkit --theme dark             # Theme switching
$ popkit --config ~/.popkit/work  # Project-specific profile
```

### 3. Local Configuration (Git-Friendly)
```
.popkit/
├── config.yml                    # Global settings
├── profiles/
│   ├── work-profile.yml          # Org-specific
│   └── side-project.yml
├── agents/
│   └── custom-agent.md           # Project-specific agents
├── hooks/
│   ├── pre-workflow.sh
│   └── post-workflow.py
├── cache/
│   └── embeddings.pkl
└── sessions/
    └── 2025-12-14-feature.json   # Pauseable workflows
```

### 4. Editor Integration
```
$ popkit edit-with-context
Opens native editor ($EDITOR) with:
  - Current task description
  - Auto-completion suggestions
  - Code snippets
  - Related files

Same as Posting's $EDITOR integration
```

### 5. Interactive Skills
```
$ popkit feature-dev "Auth system"
┌────────────────────────────────────────┐
│ Phase 1: Discovery                      │
│ [?] Use JWT or sessions?                │
│ → Sessions (radio button)               │
│ [?] Need refresh tokens?                │
│ → Yes (checkbox)                        │
├────────────────────────────────────────┤
│ Phase 2: Architecture                   │
│ [Designing based on your answers...]    │
└────────────────────────────────────────┘
```

---

## Multi-Model Orchestration (v2.0)

### Agent → Model Routing

```
Workflow Task
    ↓
[Orchestrator decides model]:
    ├─ Code review → Claude (structured reasoning)
    ├─ Architecture → Claude (long context, multi-step)
    ├─ Large file analysis → Gemini (1M token context)
    ├─ Document generation → Claude (quality output)
    ├─ Code generation → Claude (tested patterns)
    └─ Data processing → Gemini (parallel processing)
```

### Implementation via MCP Servers

```
PopKit Cloud exposes:
  • claude-mcp-server (for existing Claude models)
  • gemini-mcp-server (NEW - bridges to Gemini API)
  • openai-mcp-server (v2.0 future - for Codex, GPT-4)
  • local-llm-mcp-server (v2.0 future - for self-hosted)

Clients (Plugin, CLI, VS Code) call:
  POST /mcp/invoke
  {
    "workflow_id": "...",
    "agent": "code-reviewer",
    "preferred_model": "auto",  // or explicit: claude, gemini
    "context": {...}
  }

Response: Stream of updates until completion
```

---

## Implementation Roadmap

### Phase 1: v2.0 Alpha (Q1 2026)
- [ ] Textual-based PopKit CLI MVP
  - [ ] Basic TUI with command palette
  - [ ] Local state storage (.popkit/)
  - [ ] Integration with existing plugin
- [ ] Gemini MCP bridge
  - [ ] Cloud endpoint for Gemini delegation
  - [ ] Model selection logic
  - [ ] Error handling & fallback

### Phase 2: v2.0 Beta (Q2 2026)
- [ ] VS Code extension with PopKit sidebar
- [ ] Web dashboard (Textual SSR + React)
- [ ] Cross-platform state sync
- [ ] Multi-session management

### Phase 3: v2.0 Stable (Q3 2026)
- [ ] Cursor/Windsurf integration
- [ ] Advanced orchestration (Power Mode v2)
- [ ] Plugin ecosystem (project-specific adapters)
- [ ] Premium features (workspace teams, shared workflows)

### Phase 4: v2.0+ Future
- [ ] OpenAI Codex integration
- [ ] Local LLM support
- [ ] Marketplace for skills/agents
- [ ] Desktop app (Tauri/Electron)

---

## Technical Decision Points (For Planning Meeting)

### 1. **Textual vs Custom TUI Framework**
**Options**:
- A) Use Textual (existing, web+terminal, mature)
- B) Build custom lightweight TUI (more control, more work)
- **Recommendation**: A (Textual) - reduces maintenance burden

### 2. **Short-Term State Retention**
**Options**:
- A) 24 hours (current Redis TTL)
- B) 7 days (extended coordination window)
- C) Forever in Postgres (different tier)
- **Consideration**: How long should workflows be pauseable?

### 3. **CLI Distribution**
**Options**:
- A) pip install popkit (Python package)
- B) npm install -g popkit-cli (Node wrapper)
- C) Homebrew/standalone binary
- D) All of the above
- **Recommendation**: A + D (start with pip, expand later)

### 4. **Local State Encryption**
**Options**:
- A) Plain YAML (trust filesystem permissions)
- B) Encrypted at-rest (.popkit is encrypted)
- C) Encrypted with user passphrase
- **Consideration**: Does PopKit handle sensitive data locally?

### 5. **Gemini Integration Timing**
**Options**:
- A) v2.0 alpha (parallel with CLI)
- B) v2.0 beta (after CLI stabilizes)
- C) Separate v2.1 (defer)
- **Recommendation**: A (Gemini MCP is low-coupling, can be independent)

---

## Success Metrics

- **Adoption**: % of users accessing PopKit from multiple platforms
- **Session duration**: Average workflow time across platforms
- **Cross-platform handoffs**: # of workflows that span 2+ platforms
- **Model routing effectiveness**: Latency/cost improvement from multi-model delegation
- **Extensibility**: # of custom project adapters created by community
- **Satisfaction**: NPS from power users (vim keybindings, automation)

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **Complexity explosion** | Hard to maintain, slow to ship | Phase incrementally; v1.0 is plugin-only |
| **State sync failures** | Workflows appear stuck across platforms | Idempotent operations, clear error messages |
| **Latency (cloud round-trips)** | Poor UX on slow networks | Local-first design, offline mode, background sync |
| **Model routing bugs** | Wrong model selected, poor results | Structured logging, user override capability |
| **Fragmentation across IDEs** | Platform-specific bugs, support nightmare | Shared orchestration layer (CLI), same protocol |

---

## Appendix: Design Pattern Comparison

| Aspect | Posting | Harlequin | PopKit v2.0 |
|--------|---------|-----------|------------|
| **Primary Interface** | Terminal TUI | Terminal TUI | Terminal TUI (expandable to web) |
| **Extensibility** | Python scripts | Plugin adapters | MCP servers + Python hooks |
| **Local Storage** | YAML (git-friendly) | SQLite | YAML + JSON (git-friendly) |
| **Multi-platform** | SSH only | Single platform | Cloud sync across 5+ platforms |
| **AI Integration** | None | None | Multi-model orchestration |
| **User Intent** | API requests | SQL queries | Development workflows |

---

## References

- Textual Framework: https://textual.textualize.io/
- Posting: https://github.com/darrenburns/posting
- Harlequin: https://github.com/tconbeer/harlequin
- PopKit CLAUDE.md: Design principles and current architecture
- MCP Specification: Model Context Protocol for inter-tool communication

---

**Document Status**: Ready for planning meeting review
**Next Step**: Schedule architecture review, prioritize phases, assign implementation tasks
