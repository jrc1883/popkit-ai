# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PopKit** is an AI-powered development workflow system. This repository is the **private monorepo** containing all PopKit components.

### Terminology (Avoid Confusion)

| Term | Meaning |
|------|---------|
| **PopKit (this repo)** | Private monorepo where we develop everything |
| **PopKit Plugin** | The Claude Code plugin users install (public: `jrc1883/popkit-claude`) |
| **PopKit Cloud** | Shared backend API (Cloudflare Workers) |
| **PopKit Platform** | Future vision: model-agnostic orchestrator for multiple IDEs |

### Current Architecture

```
jrc1883/popkit (PRIVATE - this repo)
├── packages/plugin/     → Published to jrc1883/popkit-claude (PUBLIC, declarative only)
├── packages/cloud/      → Deployed to Cloudflare Workers
└── packages/cloud-*/    → Billing, docs, team features
```

Users install the plugin via: `/plugin install popkit@popkit-claude`

### Cloud Infrastructure

**Live endpoints:**
- `api.thehouseofdeals.com` → PopKit Cloud API (Cloudflare Worker)

**Stack:**
| Service | Purpose | Status |
|---------|---------|--------|
| Cloudflare Workers | API hosting, edge computing | Active |
| Upstash Redis | Pattern storage, Power Mode coordination | Active |
| Upstash Vector | Semantic search, embeddings | Active |
| Upstash QStash | Scheduled jobs (future) | Available |

**Cloudflare Skills:**
- `pop-cloudflare-worker-deploy` - Deploy Workers with custom domains
- `pop-cloudflare-pages-deploy` - Deploy static sites to Pages
- `pop-cloudflare-dns-manage` - DNS record management

**Environment Variables (Wrangler Secrets):**
```bash
wrangler secret put UPSTASH_REDIS_REST_URL
wrangler secret put UPSTASH_REDIS_REST_TOKEN
wrangler secret put UPSTASH_VECTOR_REST_URL
wrangler secret put UPSTASH_VECTOR_REST_TOKEN
```

### Public vs Private Split

The public repo (`jrc1883/popkit-claude`) contains **only declarative content**:
- Commands (markdown specs)
- Skills (marketing stubs for premium, full prompts for free)
- Agents (definitions and routing)
- Output styles (templates)

Implementation code stays **private** in this repo:
- `packages/plugin/power-mode/` - Orchestration logic
- `packages/plugin/templates/` - MCP server implementation
- `packages/plugin/hooks/utils/` - Premium logic, pattern detection
- `packages/cloud/` - All cloud API code

### Future Vision

PopKit will evolve from a Claude Code plugin to a platform supporting:
- Multiple AI models (Claude, GPT, Gemini, local LLMs)
- Multiple IDEs (VS Code, Cursor, Windsurf, JetBrains)
- Standalone CLI (installable via pip/npm/bun)
- Shared cloud backend for cross-project learning

The Claude Code plugin is the **first integration** of this platform.

### Plugin Architecture

The plugin implements a two-tier agent system:

- **Tier 1 (always-active)**: Universal, project-agnostic tools that work anywhere
- **Tier 2 (on-demand)**: Specialized agents activated by triggers
- **Tier 3 (generated)**: Project-specific MCP servers, skills, and agents created via `/popkit:project generate`

## Core Philosophy

PopKit exists to **orchestrate Claude Code's full power** for real-world development workflows. Claude Code provides raw tools; PopKit chains them together programmatically.

### Key Principles

1. **Full Claude Code Orchestration**
   - Leverages ALL capabilities: hooks, agents, skills, commands, status line, output styles, MCP servers
   - Not just using tools, but composing them into coherent workflows

2. **Non-Linear Development Support**
   - Development isn't linear; there are branches and different paths
   - Can help new projects (generate PRDs, setup GitHub)
   - Can analyze existing projects (identify gaps, recommend fixes)
   - Adapts to any project type (full stack, web, mobile)

3. **Programmatic Chaining**
   - Simple tasks chained together → orchestrated workflows
   - Example: GitHub push + feature update as unified `/popkit:git pr`
   - Follows Claude Code engineering blog best practices
   - Context preservation for long-running processes

4. **Tiered Loading**
   - Don't load all tools at once
   <!-- AUTO-GEN:TIER-COUNTS START -->
   - Tier 1: Always-active core agents (11)
   - Tier 2: On-demand specialists activated by triggers (17)
   - Feature Workflow: 7-phase development agents (3)
   - Skills: 68 reusable skills
   - Commands: 24 slash commands
   <!-- AUTO-GEN:TIER-COUNTS END -->

5. **Project-Specific Customization ("Chain Combos")**
   - Base commands work everywhere (Tier 1)
   - Generate custom versions for specific projects (Tier 2)
   - Skills/commands that learn and grow with the project
   - Example: `/popkit:generate-mcp` creates project-specific MCP server

6. **Inter-Agent Communication** (Power Mode)
   - Pub-sub pattern for parallel agent orchestration
   - Redis-based message passing for multi-agent coordination
   - Structured output styles for inter-agent communication
   - Periodic check-ins and sync barriers between phases

### Design Goals

| Goal | Implementation |
|------|----------------|
| Check GitHub first | Always improve existing code before implementing from scratch |
| Context preservation | STATUS.json pattern, session capture/restore skills |
| Confidence-based filtering | 80+ threshold prevents false positives |
| Progressive disclosure | Load documentation only when needed |
| Engineering blog alignment | Follow Anthropic's recommended patterns |
| Interactive prompts | Always use AskUserQuestion for user decisions |

### User Interaction Standard

**All PopKit skills and commands MUST use `AskUserQuestion`** for user decisions:

```
Use AskUserQuestion tool with:
- question: Clear question ending with "?"
- header: Short label (max 12 chars)
- options: 2-4 choices with labels and descriptions
- multiSelect: false (unless multiple selections make sense)
```

**NEVER present options as plain text** like "1. Option A, 2. Option B - type 1 or 2".

Benefits:
- Arrow key navigation for selection
- Prevents typos in user responses
- Consistent UX across all PopKit features
- "Other" option always available for custom input

### AskUserQuestion Enforcement (Issue #159)

Following Anthropic's recommendation from the Hooks Guide:
> "By encoding these rules as hooks rather than prompting instructions, you turn suggestions into app-level code that executes every time."

Skills can define **required decision points** in `agents/config.json` under `skill_decisions`:

```json
"skill_decisions": {
  "skills": {
    "pop-project-init": {
      "completion_decisions": [
        {
          "id": "next_action",
          "question": "Project initialized. What would you like to do next?",
          "header": "Next Step",
          "options": [
            {"label": "Analyze codebase", "description": "Run /popkit:project analyze"},
            {"label": "Done for now", "description": "I'll explore on my own"}
          ]
        }
      ]
    }
  }
}
```

**How it works:**
1. `pre-tool-use.py` tracks when a skill is invoked
2. `post-tool-use.py` checks for pending completion decisions
3. Reminders are output to stderr when decisions are pending
4. Decisions are recorded when AskUserQuestion is used

**Implementation files:**
- `agents/config.json` → `skill_decisions` section (decision definitions)
- `hooks/utils/skill_state.py` → State tracking and enforcement logic
- `hooks/pre-tool-use.py` → Skill invocation tracking
- `hooks/post-tool-use.py` → Pending decision reminders

## Repository Structure

This is a **monorepo** with npm workspaces:

<!-- AUTO-GEN:REPO-STRUCTURE START -->
```
packages/
  plugin/                  Claude Code plugin (main package)
    .claude-plugin/        Plugin manifest (plugin.json, marketplace.json)
    .mcp.json              MCP server configuration
    agents/                31 agent definitions with tiered activation
      config.json          Agent routing, workflows, confidence thresholds
      tier-1-always-active/  11 core agents
      tier-2-on-demand/    17 specialized agents
      feature-workflow/    3 agents for 7-phase feature development
    skills/                68 reusable skills (SKILL.md format)
    commands/              24 slash commands
    hooks/                 23 Python hooks (JSON stdin/stdout)
      hooks.json           Hook configuration
      utils/               60+ utility modules
    output-styles/         15+ output format templates
    power-mode/            Multi-agent orchestration
    templates/mcp-server/  MCP server generator template
    tests/                 Plugin self-test definitions
    assets/                Visual assets and VHS tapes
    scripts/               Utility scripts (sync-readme.py)
  cloud/                   PopKit Cloud API (Cloudflare Workers)
    src/                   API routes and middleware
    wrangler.toml          Cloudflare configuration
  cloud-billing/           Billing and entitlements
  cloud-docs/              Cloud documentation
  cloud-scripts/           Deployment scripts
  cloud-team/              Team coordination features
package.json               Root package.json with workspaces
CHANGELOG.md               Version history
```
<!-- AUTO-GEN:REPO-STRUCTURE END -->

## Development Notes

This is a **configuration-only plugin** - no build or lint commands exist. All content is:
- Markdown files with YAML frontmatter (skills, commands, agents)
- JSON configuration (plugin.json, config.json, hooks.json, .mcp.json)
- Python scripts (hooks with JSON stdin/stdout protocol)
- TypeScript templates (mcp-server)
- JSON test definitions (tests/)

**Self-testing available:** Run `/popkit:plugin-test` to validate plugin integrity.

## Claude Platform Integration

PopKit leverages Claude API platform features for optimal performance. Configuration is in `packages/plugin/agents/config.json`.

### Effort Parameter

Agent compute allocation: `high` (deep analysis), `medium` (default), `low` (quick tasks).
Configured per-agent in `packages/plugin/agents/config.json`.

### Extended Thinking

**Flags:** `-T`, `--thinking`, `--no-thinking`, `--think-budget N`

- Sonnet: Enabled by default (10k tokens)
- Opus: Enabled by default (10k tokens) - as of Claude Code 2.0.67
- Haiku: Enabled by default (5k tokens)

### PDF Support

Skills accept PDF file paths for design docs, PRDs, and specifications.
Use `document-skills:pdf` to generate PDF output.

### Semantic Embeddings

Voyage AI embeddings for tool discovery. Set `VOYAGE_API_KEY` env var.
Use `/popkit:project embed` to embed project items.

### Claude Code Version Requirements

PopKit features require specific Claude Code versions for full functionality:

| Feature | Minimum Version | Description |
|---------|-----------------|-------------|
| **Extended Thinking** | 2.0.67 | Default enabled on Sonnet/Opus/Haiku (10k tokens) |
| **Native Async Mode** | 2.0.64 | Zero-setup background Task tool (5+ agents) |
| **Plan Mode** | 2.0.70 | Agent approval workflow before execution |
| **Configuration Management** | 2.0.71 | `/config` toggle for prompt suggestions |
| **Settings Alias** | 2.0.71 | `/settings` command alias for `/config` |
| **MCP Permissions** | 2.0.71 | Fixed `dangerously-skip-permissions` for MCP servers |
| **Bash Glob Safety** | 2.0.71 | Fixed permission rules for shell glob patterns |
| **Bedrock Support** | 2.0.71 | `ANTHROPIC_BEDROCK_BASE_URL` environment variable |

**Current Recommendation:** Claude Code 2.0.71+ for full PopKit feature support.

## Key Architectural Patterns

### Agent Routing (packages/plugin/agents/config.json)

Agents are routed via three mechanisms:
1. **Keywords**: "bug" → bug-whisperer, "security" → security-auditor
2. **File patterns**: `*.test.ts` → test-writer-fixer, `*.sql` → query-optimizer
3. **Error patterns**: TypeError → bug-whisperer, SecurityError → security-auditor

### Confidence-Based Filtering

Code review uses 80+ confidence threshold to filter issues:
- 0-25: Likely false positive, skip
- 50-75: Worth mentioning
- 80-100: Must address

### 7-Phase Feature Development

The `/popkit:feature-dev` command and feature-workflow agents follow: Discovery → Exploration (code-explorer) → Questions → Architecture (code-architect) → Implementation → Review (code-reviewer) → Summary

### Session Continuity

Three skills manage state between sessions (invoke via Skill tool):
- `pop-session-capture`: Saves state to STATUS.json
- `pop-session-resume`: Restores context on startup
- `pop-context-restore`: Loads previous session

### Unified Routine Management (Morning + Nightly)

Day-bracketing workflow via `/popkit:routine`:
- `morning`: Health check → "Ready to Code" score (0-100)
- `nightly`: Cleanup → "Sleep Score" (0-100)
- `--measure`: Track context usage, duration, and tool breakdown

Subcommands: `run`, `quick`, `generate`, `list`, `set`, `edit`, `delete`

**Routine Measurement** (`--measure` flag):
Tracks execution metrics for routine optimization:
- Duration, tool calls, token usage (input/output)
- Cost estimates (Claude Sonnet 4.5 pricing)
- Per-tool breakdown (Bash, Read, Grep, etc.)
- JSON persistence to `.claude/popkit/measurements/`

Implementation:
- `hooks/utils/routine_measurement.py` - Tracker
- `hooks/post-tool-use.py` - Auto-capture tool calls
- `skills/pop-routine-measure/` - Skill + tests

See `packages/plugin/commands/routine.md` for full documentation.

### Power Mode (Multi-Agent Orchestration)

Parallel agent collaboration via `/popkit:power`:
- **Native Async Mode** (Claude Code 2.0.64+): Zero setup, 5+ agents via background Task tool
- **Redis Mode** (Pro tier): Full power, 10+ agents, requires Docker
- **File-Based Mode** (Free tier): Zero setup, 2 agents sequential

**Plan Mode** (Claude Code 2.0.70+): Agents present implementation plans for user approval before executing changes.
- Use `--require-plans` to force all agents to present plans
- Use `--trust-agents` to allow all agents to execute directly
- Default: Configuration-based per agent (Tier 1=execute, Tier 2=plan)

Configuration: `packages/plugin/agents/config.json` → `plan_mode` section defines which agents require plan approval.

Use `/popkit:power init` to set up. See `packages/plugin/commands/power.md` for details.

### Stateless Message Composition

Hooks use pure functions for reliability and testability:
- `packages/plugin/hooks/utils/message_builder.py` - Message composition
- `packages/plugin/hooks/utils/context_carrier.py` - Immutable context passing
- `packages/plugin/hooks/utils/stateless_hook.py` - Base class for hooks

See `packages/plugin/tests/hooks/` for 58 tests covering this pattern.

### Context Optimization (Issues #275, #276)

Two-phase optimization reducing PopKit's context baseline by **40.5%** (25.7k → 15.3k tokens):

**Phase 1: Tool Choice Enforcement** (Issue #275 - Completed 2025-12-17)
- `tool_filter.py` - Workflow-based tool filtering with wildcard support
- `pre-tool-use.py` integration - Passthrough mode with debug logging
- `agents/config.json` - Enforcement active, override via `POPKIT_DISABLE_TOOL_FILTER`
- **Result:** System Tools reduced 32.3% (23.3k → 15k tokens)

**Phase 2: Embedding-Based Agent Loading** (Issue #276 - Completed 2025-12-17)
- `generate-agent-embeddings.py` - Voyage AI embeddings for 28 agents
- `agent_loader.py` - Semantic search with keyword fallback, always includes Tier 1 agents
- `session-start.py` integration - Loads top 10 relevant agents per query
- **Result:** Custom Agents reduced 87.5% (2.4k → 0.3k tokens)

**Combined Impact:**
- Baseline: 25.7k tokens
- After optimization: 15.3k tokens
- **Target exceeded:** Goal 25k, achieved 15.3k ✅

**Measurement:** Run `python packages/plugin/scripts/measure-context-usage.py`

**Future Enhancement:** Issue #281 - Enhanced embeddings with full agent definitions for 3-5k additional savings

## Installing popkit for Development

To use popkit while developing popkit (chicken-and-egg), install it from the public plugin repo:

```
/plugin marketplace add jrc1883/popkit-claude
/plugin install popkit@popkit-claude
```

Then **restart Claude Code** to load the plugin. After restart, `/popkit:` commands will be available.

## Repository Architecture (Public/Private Split)

PopKit uses a **split-repo model** to keep the core plugin open-source while keeping cloud services private:

| Repository | Visibility | Contents | Status |
|------------|------------|----------|--------|
| `jrc1883/popkit` | **Private** | Full monorepo (plugin + cloud + billing) | Active |
| `jrc1883/popkit-claude` | **Public** | Claude Code plugin (declarative only) | Active |
| `jrc1883/popkit-mcp` | **Public** | Universal MCP server | Future |
| `jrc1883/popkit-codex` | **Public** | Codex integration | Future |
| `jrc1883/popkit-gemini` | **Public** | Gemini integration | Future |

Each public repo is populated via `git subtree split` from the corresponding `packages/` directory.

### Milestone Strategy

| Milestone | Purpose | Key Issues |
|-----------|---------|------------|
| `v1.0.0` | Claude Code plugin ready for marketplace | #2 (Marketplace), #224 (Validation) |
| `v2.0.0` | Multi-model platform expansion | #112 (Universal MCP), #113 (Codex), #114 (Gemini), #115 (Orchestration) |

**v2.0.0 Roadmap:**
1. Google Gemini Integration (#114)
2. OpenAI Codex Integration (#113)
3. Universal MCP Server (#112)
4. Intelligent Orchestration Layer (#115)

Labels:
- **Priority**: `P0-critical`, `P1-high`, `P2-medium`, `P3-low`
- **Phase**: `phase:now` (current), `phase:next` (queued), `phase:future` (v2.0+)

### Publishing Plugin to Public Repo

When ready to release plugin changes publicly:

```bash
# Manual publish from CLI
/popkit:git publish                    # Push current state
/popkit:git publish --tag v1.0.0       # With version tag
/popkit:git publish --dry-run          # Preview first

# Or via GitHub Actions
# Go to Actions → "Publish Plugin" → Run workflow
```

### How It Works

1. **Development**: Work in `packages/plugin/` within the private monorepo
2. **Commit**: Changes stay in private repo until you explicitly publish
3. **Publish**: `git subtree split` extracts plugin and pushes to public repo
4. **Users Install**: From public `jrc1883/popkit-claude` via marketplace

### Branch Naming Convention

**IMPORTANT**: The private monorepo uses `master`, but the public repo uses `main`.

When publishing manually:
```bash
# Correct - push to main branch
git push plugin-public $(git subtree split --prefix=packages/plugin):main --force

# Wrong - pushing to master creates a separate branch
git subtree push --prefix=packages/plugin plugin-public master
```

### Remote Setup

The `plugin-public` remote is needed for publishing:

```bash
git remote add plugin-public https://github.com/jrc1883/popkit-claude.git
```

This is automatically configured when running `/popkit:git publish` for the first time.

## The Chicken-and-Egg Problem

When developing this plugin:
1. The skills/agents you're editing are the same ones you're using to edit
2. Changes to hooks affect the current session behavior
3. Use `/popkit:worktree create` to test changes in isolation before merging

## Testing Changes

Verify changes using the built-in test framework:
1. Run `/popkit:plugin-test` to validate all components
2. Run `/popkit:plugin-test hooks` to test hook JSON protocol
3. Run `/popkit:plugin-test routing` to verify agent selection
4. For isolation: Create a worktree with `/popkit:worktree create test-feature`

## MCP Server Template

Located in `packages/plugin/templates/mcp-server/`, this TypeScript template generates project-specific MCP servers with:
- Health checks (dev server, database)
- Git tools (status, diff, recent commits)
- Quality tools (typecheck, lint, tests)
- Semantic tool discovery via embeddings

To build the template locally:
```bash
cd packages/plugin/templates/mcp-server
npm install
npm run build
```

## Key Files for Plugin Behavior

All plugin files are in `packages/plugin/`:

<!-- AUTO-GEN:KEY-FILES START -->
| File | Purpose |
|------|---------|
| `packages/plugin/.claude-plugin/plugin.json` | Plugin manifest and activation triggers |
| `packages/plugin/.mcp.json` | MCP server and tool configuration |
| `packages/plugin/agents/config.json` | All routing rules, workflows, confidence levels |
| `packages/plugin/hooks/hooks.json` | Hook event configuration |
| `packages/plugin/hooks/pre-tool-use.py` | Safety checks before tool execution |
| `packages/plugin/hooks/post-tool-use.py` | Cleanup and validation after tools |
| `packages/plugin/hooks/utils/skill_state.py` | Skill tracking and AskUserQuestion enforcement |
| `packages/plugin/hooks/utils/skill_context.py` | Skill-to-skill context handoff |
| `packages/plugin/hooks/utils/context_storage.py` | File/Upstash storage with Redis Streams |
| `packages/plugin/power-mode/coordinator.py` | Multi-agent mesh network coordinator |
| `packages/plugin/power-mode/statusline.py` | Visual Power Mode status line display |
| `packages/plugin/hooks/utils/` | 51 utility modules (embeddings, routing, etc.) |
| `packages/plugin/scripts/sync-readme.py` | Auto-generate README sections |
| `packages/cloud/src/index.ts` | Cloud API entry point |
| `packages/cloud/wrangler.toml` | Cloudflare Workers configuration |
| `.github/workflows/publish-plugin.yml` | GitHub Actions for public repo sync |
| `.github/workflows/sync-readme.yml` | Auto-sync README on changes |
<!-- AUTO-GEN:KEY-FILES END -->

## Analytics and Observability

### Local Session Tracking

PopKit can track session data locally for analysis:

```
~/.popkit/
├── sessions/           # Session logs
│   └── {date}-{id}.json
├── patterns/           # Learned patterns
│   └── learned-patterns.json
├── metrics/            # Usage statistics
│   └── usage-stats.json
└── config/             # User preferences
    └── settings.json
```

### Cloud Analytics (Premium)

When connected to PopKit Cloud:
- Session duration and commands used
- Agent routing frequency
- Error rates and recovery patterns
- Cross-project pattern learning

### Sandbox Testing

Test PopKit workflows in isolated environments:
1. Use `/popkit:worktree create` for git isolation
2. Test in separate projects to validate behavior
3. Capture logs with `/popkit:bug report` for analysis
4. Compare sessions using local metrics

### Quality Validation

Run comprehensive validation before releases:
```bash
/popkit:assess all          # Run all assessors
/popkit:plugin test         # Test plugin integrity
/popkit:debug routing       # Verify agent routing
```

See `docs/plans/2025-12-13-v1-validation-audit-plan.md` for full audit strategy.

## Version History

**Current Version:** 0.2.5 (Pre-release)
**Target:** 1.0.0 (Marketplace Release)

See [CHANGELOG.md](CHANGELOG.md) for full version history.

## Current Status & Roadmap

### Epic #580: Plugin Modularization (IN PROGRESS)

**Goal**: Transform monolithic plugin into 6 focused workflow-based plugins

**Progress**: Phase 6/6 (Documentation & Release) - 83% Complete

**Phases Completed** ✅:
- Phase 1: Shared Foundation Package (`@popkit/shared-py` - 70 utility modules)
- Phase 2: popkit-dev Plugin (core development workflows)
- Phase 3: Remaining Plugins (github, quality, deploy, research, core)
- Phase 4: Meta-Plugin (backwards compatibility)
- Phase 5: Testing & Validation (Issue #578 CLOSED)
  - ✅ Plugin structure verified (all 6 plugins)
  - ✅ Shared package imports tested (7/7 critical modules)
  - ✅ Test suite compatibility: 155/161 passing (96.3%)
  - ✅ Performance measured: 298,568 tokens (acceptable despite 6.8% increase)
  - ⏸️ Manual testing deferred to post-beta (requires published plugins)

**Current Phase** 🔄:
- **Phase 6: Documentation & Release** (Ready to start)
  - Update documentation for modular architecture
  - Create marketplace listings
  - Prepare v1.0.0-beta.1 release
  - Publish to marketplace
  - Conduct real UAT with beta users

**Key Documents**:
- Design: [`docs/plans/2025-12-20-plugin-modularization-design.md`](docs/plans/2025-12-20-plugin-modularization-design.md)
- Testing Plan: [`docs/plans/2025-12-21-phase5-testing-validation-plan.md`](docs/plans/2025-12-21-phase5-testing-validation-plan.md)
- Validation Report: [`docs/assessments/2025-12-21-phase5-validation-report-initial.md`](docs/assessments/2025-12-21-phase5-validation-report-initial.md)

**Architecture Change**: All features now FREE with local execution. API key adds semantic intelligence enhancements (no subscription tiers).

### Recent Milestones

- **2025-12-21**: Phase 5 COMPLETE - Issue #578 closed, ready for Phase 6
  - Structure validation: 100% (all 6 plugins verified)
  - Test suite: 96.3% passing (155/161 tests)
  - Performance measured: 298,568 tokens (6.8% increase acceptable)
  - Created comprehensive testing documentation
- **2025-12-20**: All 6 modular plugins extracted (#570-577 closed)
- **2025-12-20**: Shared foundation package published
- **2025-12-19**: Comprehensive assessment completed (82/100 score)
- **2025-12-18**: Documentation deprecation notices added (#582 closed)

## Conventions

- All commits use conventional commit format with Claude attribution
- Output styles define templates for PRs, issues, releases, reviews
- Skills can invoke other skills; commands can invoke skills
- Python hooks use `#!/usr/bin/env python3` and are chmod +x

## Releasing New Versions

When releasing a new version of popkit:

### 1. Update Version Numbers

Update version in these files (must match):
- `packages/plugin/.claude-plugin/plugin.json` - Main plugin version
- `packages/plugin/.claude-plugin/marketplace.json` - Marketplace version

### 2. Update Changelog

Add new version section to `CHANGELOG.md`:
```markdown
## [X.Y.Z] - Title

- **Feature Name**: Description
```

### 3. Commit and Push

```bash
git add packages/plugin/.claude-plugin/plugin.json packages/plugin/.claude-plugin/marketplace.json CHANGELOG.md
git commit -m "chore: bump version to X.Y.Z for [feature summary]"
git push
```

### 4. Update Installed Plugin

After pushing, update the installed plugin:
```
/plugin update popkit@popkit-marketplace
```

Then **restart Claude Code** to load the new version.

### 5. Verify Installation

After restart, verify the update worked:
- Check `/popkit:` commands are available
- Run `/popkit:plugin-test` to validate components
- Test any new features added

### Version Numbering

Follow semantic versioning:
- **MAJOR** (X.0.0): Breaking changes to commands, agents, or hooks
- **MINOR** (0.X.0): New features, commands, or agents (backward compatible)
- **PATCH** (0.0.X): Bug fixes, documentation updates
