# PopKit Platform Roadmap

**Vision**: Transform PopKit from a Claude Code plugin into a universal AI orchestration platform supporting multiple models, IDEs, and deployment modes.

**Inspiration**: [K-Dense AI's claude-scientific-skills](https://github.com/K-Dense-AI/claude-scientific-skills) demonstrates a successful multi-deployment architecture (plugin + MCP + self-hosted) with 125+ federated skills.

---

## Table of Contents

1. [Current State (v0.9.11)](#current-state-v0911)
2. [Three Levels of PopKit](#three-levels-of-popkit)
3. [Multi-Deployment Architecture](#multi-deployment-architecture)
4. [Roadmap by Phase](#roadmap-by-phase)
5. [Implementation Epics](#implementation-epics)
6. [Technical Architecture](#technical-architecture)
7. [Success Metrics](#success-metrics)

---

## Current State (v0.9.11)

### ✅ What We Have

**Level 1 - Claude Code Plugin:**
- 30 specialized agents (11 Tier-1, 17 Tier-2, 3 feature-workflow)
- 36 reusable skills
- 15 slash commands with subcommands
- 18 Python hooks with 24 utility modules
- Power Mode v3 with Upstash Workflows integration

**Level 2 - Cloud Platform:**
- Cloudflare Workers API (`packages/cloud/`)
- Upstash services: Redis, Workflows, Vector, QStash
- Cross-project observability and pattern learning
- Durable workflow orchestration
- Project registry and activity tracking

**Infrastructure:**
- Monorepo structure with npm workspaces
- Public plugin repo auto-sync (`jrc1883/popkit-plugin`)
- MCP server template generator
- Comprehensive test framework

### 🎯 What's Missing

**Multi-Model Support:**
- No Codex integration (OpenAI)
- No Gemini integration (Google)
- No generic MCP server for other AI tools

**Multi-Deployment:**
- Plugin exists only for Claude Code
- No MCP server deployment option
- No standalone CLI

**Cross-Model Orchestration:**
- No task-to-model routing
- No multi-model workflows
- No unified command interface

---

## Three Levels of PopKit

### Level 1: Plugin Layer (Model-Specific)

**Purpose**: Maximize native capabilities of each AI tool

| AI Tool | Package | Type | Status |
|---------|---------|------|--------|
| Claude Code | `packages/plugin/` | Plugin | ✅ Shipped |
| Codex (OpenAI) | `packages/codex-plugin/` or `packages/codex-mcp/` | Plugin or MCP | 📋 Planned |
| Gemini (Google) | `packages/gemini-plugin/` or `packages/gemini-mcp/` | Plugin or MCP | 📋 Planned |
| Cursor IDE | `packages/cursor-mcp/` | MCP | 📋 Planned |
| VS Code (Continue) | `packages/continue-mcp/` | MCP | 📋 Planned |
| Generic | `packages/universal-mcp/` | MCP | 📋 Planned |

**Characteristics:**
- Full utilization of tool-specific features (hooks, agents, skills, etc.)
- Local-file fallback for offline work
- Optimized for each tool's strengths

### Level 2: Cloud Platform (Model-Agnostic)

**Purpose**: Shared intelligence and coordination across all tools

**Capabilities:**
- Cross-project memory and pattern learning
- Durable workflow orchestration
- Multi-agent coordination (Power Mode)
- Observability and analytics
- Team collaboration features
- Unified instruction system (user preferences)

**Current Implementation:**
- Cloudflare Workers API
- Upstash Redis, Workflows, Vector, QStash
- Model-agnostic JSON API endpoints

### Level 3: Orchestration Layer (Intelligence)

**Purpose**: Route tasks to best model, coordinate multi-model workflows

**Capabilities** (Future):
- Task-to-model routing (e.g., Claude for architecture, Codex for implementation)
- Cost optimization (cheaper models for simple tasks)
- Multi-model workflows (parallel execution across different AIs)
- Unified command interface (`/popkit:dev` works everywhere)
- Model performance analytics

---

## Multi-Deployment Architecture

**Inspired by**: K-Dense AI's claude-scientific-skills three-deployment model

### Deployment Option 1: Native Plugin

**Best for**: Tools with plugin/extension support (Claude Code, VS Code, etc.)

**Benefits:**
- Full IDE integration
- Native UI components (status line, hooks, commands)
- Offline-capable with local fallback
- Best performance (no network overhead)

**Implementation:**
```
packages/
  plugin/          # Claude Code (exists)
  codex-plugin/    # OpenAI Codex (planned)
  gemini-plugin/   # Google Gemini (planned)
  vscode-plugin/   # VS Code extension (future)
```

### Deployment Option 2: MCP Server

**Best for**: Any tool supporting Model Context Protocol (Cursor, Continue, etc.)

**Benefits:**
- Universal compatibility (any MCP-compatible client)
- Single server serves multiple clients
- Easy updates (server-side only)
- Self-hosted option for privacy

**Implementation:**
```
packages/
  universal-mcp/   # Generic MCP server (works with any client)
  cursor-mcp/      # Cursor-optimized (optional)
  codex-mcp/       # Codex fallback if no plugin support
```

**Hosting Options:**
- Cloud-hosted: `https://mcp.popkit.dev` (users connect via URL)
- Self-hosted: `npx popkit-mcp` (runs locally)
- Docker: `docker run popkit/mcp-server`

### Deployment Option 3: Standalone CLI

**Best for**: Users who want PopKit without an AI coding assistant

**Benefits:**
- Direct access to cloud features
- Automation and scripting
- CI/CD integration
- Cross-project management

**Implementation:**
```
packages/
  cli/             # Standalone CLI (npm/pip/bun install)
```

**Usage:**
```bash
# Install
npm install -g @popkit/cli
pip install popkit-cli
bun install -g popkit

# Commands
popkit project observe --active
popkit pattern search "error handling"
popkit workflow run feature-dev --issue 123
```

---

## Roadmap by Phase

### Phase 0: Foundation (Current → v0.10.0)
**Timeline**: 2-4 weeks
**Goal**: Prepare architecture for multi-model expansion

**Tasks:**
1. ✅ Model Capability Research (Codex, Gemini, Cursor)
2. ✅ Unified Cloud API Contract (model-agnostic endpoints)
3. ✅ Tool Detection & Routing (identify calling client)
4. ✅ Cross-Model Pattern Schema (common format)
5. ✅ Documentation-First Skill Enhancement (richer SKILL.md files)

**Deliverables:**
- `docs/MODEL_CAPABILITIES.md` - Feature matrix for each AI tool
- `packages/cloud/src/schemas/` - Model-agnostic schemas
- Updated agent SKILL.md files with use case examples

### Phase 1: Universal MCP Server (v0.10.0 → v0.11.0)
**Timeline**: 3-4 weeks
**Goal**: Build MCP server that works with ANY AI tool

**Tasks:**
1. Create `packages/universal-mcp/` package
2. Implement core PopKit tools via MCP protocol:
   - Pattern retrieval and submission
   - Workflow tracking and resumption
   - Cross-project memory access
   - Agent coordination (Power Mode lite)
3. Build MCP server with stdio and SSE transports
4. Create setup guides for Cursor, Continue, Windsurf
5. Deploy hosted version at `https://mcp.popkit.dev`
6. Test with Claude Code (validate compatibility)

**Deliverables:**
- `packages/universal-mcp/` - Published to npm
- Hosted MCP server (Cloudflare Workers)
- Setup documentation for 3+ clients

**Success Criteria:**
- Works with Cursor out of the box
- Users can access cross-project patterns from any MCP client
- Performance: <100ms latency for tool calls

### Phase 2: Codex Integration (v0.11.0 → v0.12.0)
**Timeline**: 4-6 weeks
**Goal**: Bring OpenAI Codex into PopKit ecosystem

**Tasks:**
1. Codex capability assessment (plugin support? MCP? API?)
2. **Option A**: Build `packages/codex-plugin/` if plugin support exists
3. **Option B**: Create `packages/codex-mcp/` if MCP-only
4. Adapt core agents for Codex (rewrite prompts if needed)
5. Cloud API integration (register Codex sessions)
6. Setup documentation with examples
7. **Meta-development**: Use Codex to build its own integration

**Deliverables:**
- Codex package (plugin or MCP)
- 10+ core agents working with Codex
- Setup guide with screenshots
- Blog post: "Building Codex Integration with Codex"

**Success Criteria:**
- Codex users can access PopKit patterns
- Power Mode works with Codex (if technically possible)
- Cross-project memory persists between Claude and Codex sessions

### Phase 3: Gemini Integration (v0.12.0 → v0.13.0)
**Timeline**: 4-6 weeks
**Goal**: Bring Google Gemini into PopKit ecosystem

**Tasks:**
- Mirror Phase 2 structure for Gemini
- `packages/gemini-plugin/` or `packages/gemini-mcp/`
- Test cross-model pattern sharing (Claude → Codex → Gemini)

**Deliverables:**
- Gemini package
- Three-model compatibility validated

### Phase 4: Cloud Platform Enhancement (v0.13.0 → v0.14.0)
**Timeline**: 6-8 weeks
**Goal**: Make Level 2 truly powerful for multi-model workflows

**Features:**
1. **Cross-Project Pattern Library**
   - Browse/search patterns from any project
   - Semantic search via Upstash Vector
   - Pattern voting and curation

2. **Model Performance Analytics**
   - Track which model is best for which tasks
   - Token usage and cost tracking
   - Effectiveness scoring (bugs introduced, tests passing, etc.)

3. **Unified Instruction System**
   - User preferences apply across all models
   - "Always check GitHub first before implementing"
   - Custom quality gates and review criteria

4. **Workflow Templates**
   - Reusable workflows that work with any model
   - Community-contributed templates
   - Version control for workflows

5. **Team Collaboration**
   - Share patterns/workflows across team
   - Team-wide instruction sets
   - Shared project registry

**Deliverables:**
- Enhanced cloud API with 15+ new endpoints
- Web dashboard for analytics (optional)
- Team collaboration features

### Phase 5: Orchestration Layer (v0.14.0 → v1.0.0)
**Timeline**: 8-12 weeks
**Goal**: Level 3 capabilities - intelligent cross-model orchestration

**Features:**
1. **Task-to-Model Routing**
   - Analyze task, recommend best model
   - Auto-route based on user preferences
   - Confidence scoring for recommendations

2. **Multi-Model Workflows**
   - Use Claude for architecture design
   - Use Codex for implementation
   - Use Gemini for testing
   - Coordinate via Upstash Workflows

3. **Unified Command Interface**
   - `/popkit:dev` works in Claude, Codex, Gemini
   - Commands abstract over model differences
   - Consistent UX across all tools

4. **Cost Optimization**
   - Route simple tasks to cheaper models
   - User-defined budget constraints
   - Cost analytics and recommendations

**Deliverables:**
- Orchestration engine in cloud API
- Multi-model workflow examples
- v1.0.0 release 🎉

### Phase 6: Platform Expansion (v1.0.0+)
**Timeline**: Ongoing
**Goal**: Expand beyond coding assistants

**Features:**
- Multi-IDE support (VS Code, Cursor, Windsurf, JetBrains)
- Standalone CLI (`npm install -g @popkit/cli`)
- Web dashboard (like claude-scientific-skills web UI)
- Enterprise self-hosted option
- Domain-specific skill packs (web dev, data science, DevOps, scientific)

---

## Implementation Epics

### Epic 1: Multi-Model Foundation 🏗️
**Status**: 📋 Planned
**Timeline**: 2-4 weeks
**Goal**: Prepare architecture for multi-model expansion

**Child Issues:**
1. **Model Capability Matrix** - Document what each AI tool can/can't do
2. **Unified Cloud API Contract** - Define model-agnostic endpoints
3. **Tool Detection & Routing** - How cloud identifies calling client
4. **Cross-Model Pattern Schema** - Common format for patterns/learnings
5. **Documentation Enhancement** - Richer SKILL.md files with use cases
6. **Dependency Migration to `uv`** - Adopt Astral's package manager

**Deliverables:**
- `docs/MODEL_CAPABILITIES.md`
- Updated cloud API schemas
- Enhanced agent documentation

---

### Epic 2: Universal MCP Server 🌐
**Status**: 📋 Planned
**Timeline**: 3-4 weeks
**Goal**: Build MCP server for ANY AI tool

**Child Issues:**
1. **MCP Package Setup** - `packages/universal-mcp/` structure
2. **Core Tools Implementation** - Pattern retrieval, workflow tracking, memory access
3. **MCP Protocol Implementation** - stdio and SSE transports
4. **Hosted Deployment** - Cloudflare Workers hosting at `https://mcp.popkit.dev`
5. **Client Setup Guides** - Cursor, Continue, Windsurf documentation
6. **Claude Code Validation** - Test MCP server with Claude Code

**Deliverables:**
- npm package: `@popkit/mcp-server`
- Hosted MCP service
- 3+ client setup guides

**Success Criteria:**
- Works with Cursor out of the box
- <100ms latency for tool calls
- 10+ core tools available

---

### Epic 3: Codex Integration 🤖
**Status**: 📋 Planned
**Timeline**: 4-6 weeks
**Goal**: Bring OpenAI Codex into PopKit

**Child Issues:**
1. **Codex Capability Assessment** - Research plugin/MCP support
2. **Package Architecture Decision** - Plugin vs. MCP server
3. **Core Agents Adaptation** - Rewrite agent prompts for Codex
4. **Cloud API Integration** - Register Codex sessions
5. **Setup Documentation** - Installation guide with examples
6. **Meta-Development** - Use Codex to build its own integration
7. **Cross-Model Testing** - Validate pattern sharing with Claude

**Deliverables:**
- `packages/codex-plugin/` or `packages/codex-mcp/`
- 10+ core agents working with Codex
- Setup guide
- Blog post: "Building Codex Integration with Codex"

**Success Criteria:**
- Codex users access PopKit patterns
- Cross-project memory works across Claude and Codex

---

### Epic 4: Gemini Integration 🔮
**Status**: 📋 Planned
**Timeline**: 4-6 weeks
**Goal**: Bring Google Gemini into PopKit

**Child Issues:**
- Mirror Epic 3 structure for Gemini
- Validate three-model compatibility (Claude + Codex + Gemini)

---

### Epic 5: Cloud Platform Enhancement ☁️
**Status**: 📋 Planned
**Timeline**: 6-8 weeks
**Goal**: Level 2 features for multi-model workflows

**Child Issues:**
1. **Cross-Project Pattern Library** - Browse/search/vote on patterns
2. **Model Performance Analytics** - Track effectiveness per model
3. **Unified Instruction System** - User preferences across all models
4. **Workflow Templates** - Reusable workflows (community-contributed)
5. **Team Collaboration** - Share patterns/workflows across team

**Deliverables:**
- 15+ new cloud API endpoints
- Web dashboard (optional)
- Team features

---

### Epic 6: Orchestration Layer 🎭
**Status**: 📋 Future
**Timeline**: 8-12 weeks
**Goal**: Level 3 - intelligent cross-model orchestration

**Child Issues:**
1. **Task-to-Model Routing** - Recommend best model for task
2. **Multi-Model Workflows** - Coordinate across Claude/Codex/Gemini
3. **Unified Command Interface** - `/popkit:dev` works everywhere
4. **Cost Optimization** - Route to cheaper models when appropriate

**Deliverables:**
- Orchestration engine
- Multi-model workflow examples
- v1.0.0 release 🎉

---

## Technical Architecture

### Model Capability Matrix (Preliminary)

| Capability | Claude Code | Codex | Gemini | Cursor | Continue |
|------------|-------------|-------|--------|--------|----------|
| **Plugin Support** | ✅ Yes | ❓ TBD | ❓ TBD | ❌ No | ❌ No |
| **MCP Support** | ✅ Yes | ❓ TBD | ❓ TBD | ✅ Yes | ✅ Yes |
| **Custom Hooks** | ✅ Yes | ❓ TBD | ❓ TBD | ❌ No | ❓ TBD |
| **Skills/Agents** | ✅ Yes | ❓ TBD | ❓ TBD | ❌ No | ❌ No |
| **Slash Commands** | ✅ Yes | ❓ TBD | ❓ TBD | ❓ TBD | ❓ TBD |
| **Status Line** | ✅ Yes | ❓ TBD | ❓ TBD | ❌ No | ❌ No |
| **Extended Thinking** | ✅ Yes | ❌ No | ❓ TBD | ❓ TBD | ❓ TBD |
| **Output Styles** | ✅ Yes | ❓ TBD | ❓ TBD | ❌ No | ❌ No |
| **API Access** | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |

**Note**: ❓ = Requires research (Epic 1, Issue #1)

### Cloud API Model-Agnostic Design

All cloud endpoints accept a `client` field to identify the calling tool:

```typescript
// POST /v1/patterns/submit
{
  "client": {
    "type": "claude-code" | "codex" | "gemini" | "cursor" | "mcp",
    "version": "0.9.11",
    "session_id": "abc123"
  },
  "pattern": {
    "type": "discovery" | "decision" | "workflow",
    "content": {...},
    "project_id": "hash123",
    "tags": ["error-handling", "typescript"]
  }
}
```

### MCP Server Architecture

```
packages/universal-mcp/
├── src/
│   ├── index.ts              # Main server entry
│   ├── tools/                # MCP tool definitions
│   │   ├── pattern-tools.ts  # Pattern retrieval/submission
│   │   ├── workflow-tools.ts # Workflow tracking
│   │   ├── memory-tools.ts   # Cross-project memory
│   │   └── agent-tools.ts    # Power Mode coordination
│   ├── schemas/              # JSON schemas for tools
│   └── transports/
│       ├── stdio.ts          # Standard IO transport
│       └── sse.ts            # Server-sent events
├── dist/                     # Compiled output
├── package.json
└── README.md
```

**Tool Examples:**

1. `popkit_pattern_search` - Search patterns across projects
2. `popkit_pattern_submit` - Submit new pattern
3. `popkit_workflow_start` - Start tracked workflow
4. `popkit_workflow_checkpoint` - Save workflow state
5. `popkit_memory_recall` - Retrieve cross-project learnings
6. `popkit_agent_coordinate` - Power Mode multi-agent coordination

### Plugin Architecture (Per Model)

Each model-specific plugin follows the same structure:

```
packages/{model}-plugin/
├── .claude-plugin/           # (if plugin system exists)
│   ├── plugin.json
│   └── marketplace.json
├── agents/                   # Model-specific agents
│   ├── tier-1-always-active/
│   ├── tier-2-on-demand/
│   └── config.json
├── skills/                   # Reusable skills
├── commands/                 # Slash commands (if supported)
├── hooks/                    # Event hooks (if supported)
├── output-styles/            # Output formatting
└── cloud-client/             # Shared cloud API client
```

**Shared Code:**
- Cloud API client library (`packages/shared/cloud-client/`)
- Pattern schemas (`packages/shared/schemas/`)
- Utility functions (`packages/shared/utils/`)

---

## Success Metrics

### Phase 0 (Foundation)
- ✅ Model capability matrix complete for 5+ AI tools
- ✅ Cloud API accepts model-agnostic requests
- ✅ All agent SKILL.md files have 3+ use case examples

### Phase 1 (Universal MCP)
- ✅ MCP server works with 3+ clients (Cursor, Claude Code, Continue)
- ✅ <100ms average latency for tool calls
- ✅ 10+ users trying MCP server (beta)

### Phase 2 (Codex)
- ✅ Codex integration published
- ✅ Cross-project patterns accessible from both Claude and Codex
- ✅ 5+ core workflows work with Codex

### Phase 3 (Gemini)
- ✅ Three-model compatibility validated (Claude + Codex + Gemini)
- ✅ 20+ patterns shared across all three models

### Phase 4 (Cloud Enhancement)
- ✅ 100+ patterns in cross-project library
- ✅ Model performance analytics track 3+ effectiveness metrics
- ✅ 10+ team collaboration users

### Phase 5 (Orchestration)
- ✅ Task-to-model routing accuracy >80%
- ✅ Multi-model workflows save 30%+ tokens via optimal routing
- ✅ v1.0.0 release with 100+ active users

### Phase 6 (Platform)
- ✅ 5+ IDEs/tools supported
- ✅ Standalone CLI with 50+ active users
- ✅ Domain-specific skill packs (web dev, data science, etc.)

---

## Competitive Positioning

| Feature | PopKit | Cursor | GitHub Copilot | Windsurf | Replit |
|---------|--------|--------|----------------|----------|--------|
| **Multi-Model Support** | ✅ Planned | ❌ Claude only | ❌ GPT only | ❓ TBD | ✅ Multiple |
| **Cross-Project Memory** | ✅ Yes | ❌ No | ❌ No | ❓ TBD | ❌ No |
| **Workflow Orchestration** | ✅ Power Mode | ❌ No | ❌ No | ❓ TBD | ❌ No |
| **Durable Workflows** | ✅ Upstash | ❌ No | ❌ No | ❓ TBD | ❌ No |
| **Pattern Learning** | ✅ Cloud | ❌ Local only | ❌ No | ❓ TBD | ❌ No |
| **Self-Hosted Option** | ✅ Planned | ❌ No | ❌ No | ❌ No | ❌ No |
| **Open Source** | ✅ Plugin | ❌ No | ❌ No | ❌ No | ❌ No |

**PopKit's Unique Value:**
1. **Orchestration layer is the product** (not just AI access)
2. **Model-agnostic** (works with Claude, Codex, Gemini, etc.)
3. **Cross-project intelligence** (learns across all your work)
4. **Durable workflows** (survives crashes, resumes anywhere)
5. **Open + cloud hybrid** (plugin is open source, cloud is freemium)

---

## Monetization Strategy

### Free Tier
- Local-file fallback (no cloud)
- Universal MCP server (self-hosted)
- Basic agents and skills
- Community support

### Pro Tier ($10/month)
- Cloud-hosted MCP server
- Cross-project pattern library
- Durable workflow orchestration
- Power Mode (multi-agent coordination)
- Model performance analytics
- 10 GB pattern storage

### Team Tier ($25/user/month)
- All Pro features
- Team collaboration (shared patterns)
- Unified instruction sets
- Team analytics
- Priority support
- Unlimited pattern storage

### Enterprise Tier (Custom)
- Self-hosted cloud infrastructure
- SSO/SAML integration
- Custom model integrations
- Dedicated support
- SLA guarantees

---

## Next Steps

### Immediate Actions (This Week)

1. **Create Epic 1 Issues** - Multi-Model Foundation child issues
2. **Research Codex Capabilities** - Plugin support? MCP? API only?
3. **Research Gemini Capabilities** - Same questions
4. **Design Cloud API Extensions** - Model-agnostic endpoints
5. **Start Universal MCP Server** - `packages/universal-mcp/` setup

### This Month

1. **Complete Epic 1** - Foundation work
2. **Build Universal MCP Server** - Epic 2
3. **Test with Cursor** - Validate MCP compatibility
4. **Start Codex Integration** - Epic 3 (if Codex supports plugins/MCP)

### This Quarter

1. **Ship Codex Integration** - Epic 3 complete
2. **Ship Gemini Integration** - Epic 4 complete
3. **Enhance Cloud Platform** - Epic 5 started
4. **Beta Program** - 50+ users testing multi-model setup

### This Year

1. **v1.0.0 Release** - Orchestration layer shipped (Epic 6)
2. **100+ Active Users** - Across all models
3. **Standalone CLI** - npm/pip/bun install
4. **First Revenue** - Pro tier subscriptions

---

## Open Questions

1. **Does Codex support plugins?** If not, MCP only?
2. **Does Gemini have a CLI/plugin system?** Or API only?
3. **Should we build web dashboard?** Or focus on IDE integrations?
4. **Pricing for cloud tier?** $10/month? Usage-based?
5. **Open source cloud backend?** Or proprietary?
6. **Domain-specific skill packs?** (web dev, data science, etc.)
7. **Multi-model workflows?** How to coordinate Claude + Codex in one task?

---

## Conclusion

PopKit is uniquely positioned to become **the orchestration layer for AI coding tools**. By supporting multiple models, multiple deployment modes (plugin + MCP + CLI), and providing cross-project intelligence via cloud backend, PopKit offers value that no other tool provides.

The roadmap is ambitious but achievable:
- **Phase 0-1** (6 weeks): Foundation + Universal MCP
- **Phase 2-3** (12 weeks): Codex + Gemini integrations
- **Phase 4-5** (14 weeks): Cloud enhancement + orchestration
- **Total**: ~32 weeks to v1.0.0

**Next milestone**: Ship Universal MCP Server (4 weeks) and validate multi-client compatibility.

---

**Last Updated**: 2025-12-09
**Version**: 1.0
**Status**: Draft (awaiting review)
