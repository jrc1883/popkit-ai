# Changelog

All notable changes to PopKit are documented in this file.

**Versioning:** PopKit uses semantic versioning. Currently in preview (0.x) until stable public launch.

## [0.1.0] - December 11, 2025

### Version Rollback to Preview Status

**Breaking Change:** Version rolled back from 1.2.0 to 0.1.0 to correctly signal preview status.

**Rationale:**
- PopKit is not yet stable for production use
- 1.x signals "public API stable" which isn't accurate
- 0.x better communicates "preview" status
- Many features still being refined before stable release

**Version Scheme Going Forward:**
```
0.1.0 - Initial public preview (current)
0.2.0 - Major feature additions (GitHub polish)
0.3.0 - Premium features
0.9.0 - Release candidate
1.0.0 - Stable public launch
```

All features from previous 1.x releases are included in this version.

---

## [1.2.0] - December 10, 2025 (Superseded by 0.1.0)

### Feature: AskUserQuestion Enforcement (Issue #159)

Following Anthropic's recommendation from the Hooks Guide:
> "By encoding these rules as hooks rather than prompting instructions, you turn suggestions into app-level code that executes every time."

**New skill decision enforcement mechanism:**
- Skills can now define required decision points in `agents/config.json` under `skill_decisions`
- Pre-tool-use hook tracks when skills are invoked
- Post-tool-use hook outputs reminders for pending completion decisions
- Ensures consistent UX across all PopKit skills

**Implementation:**
- New `skill_decisions` section in `agents/config.json`
- New `hooks/utils/skill_state.py` for state tracking
- Updated `pre-tool-use.py` with skill invocation tracking
- Updated `post-tool-use.py` with pending decision reminders

**Skills with enforced decisions:**
- `pop-project-init`: "What would you like to do next?"
- `pop-brainstorming`: "Continue to implementation?"
- `pop-writing-plans`: "Ready to execute?"
- `pop-executing-plans`: "What's next?"
- `pop-finish-branch`: "How to integrate?"

---

## [1.1.2] - December 10, 2025

### Bug Fix: Hook Decision Type

- **Fixed**: Hooks now return `"approve"` instead of `"allow"` for decision type
  - Claude Code expects `"approve"` or `"block"` as valid decision types
  - `"allow"` was causing "Unknown hook decision type" error
  - Updated all 3 main hooks: pre-tool-use.py, user-prompt-submit.py, agent-orchestrator.py

---

## [1.1.1] - December 10, 2025

### Bug Fix: Hook Path Resolution

- **Fixed**: Hooks now use `${CLAUDE_PLUGIN_ROOT}` variable for absolute path resolution
  - Resolves "can't open file" errors when plugin is installed from marketplace
  - Hooks previously used relative paths that failed when executed from user's project directory
  - All 18 hook commands updated to use portable absolute paths
- **Fallback**: Python hooks already use `Path(__file__)` for self-resolution as safety net

---

## [1.1.0] - December 10, 2025

### Plugin Version Management

- **Version Command**: New `/popkit:plugin version` subcommand for full release workflow
  - Bump patch/minor/major versions with semantic versioning
  - Auto-updates plugin.json, marketplace.json, and CHANGELOG.md
  - Commits, pushes, and publishes to public repo in one command
  - Supports `--dry-run`, `--no-publish`, `--no-push` options

---

## [1.0.0] - December 9, 2025

### PopKit 1.0 - First Stable Release

This release marks the completion of all planned features for PopKit's initial stable release.

#### Major Features

**Benchmarking Framework (Epic #117)**
- Complete benchmark task schema with Zod validation
- 5 standard benchmarks: bouncing-balls, todo-app, api-client, binary-search-tree, bug-fix
- Metrics collection system with SQLite storage adapter
- E2B.dev integration research and proof-of-concept
- Cross-tool benchmark runner (ClaudeRunner, BenchmarkExecutor)
- Dashboard with Markdown and HTML report generators

**Multi-Project Dashboard (#93)**
- Global project registry with CRUD operations
- Health score calculation (git, build, tests, issues, activity)
- Auto-discovery of projects in common locations
- Project tagging and filtering
- `/popkit:dashboard` command with switch, refresh, discover subcommands

**Cross-Project Pattern Sharing (#95)**
- Privacy-first pattern anonymization
- Cloud API client for community pattern sharing
- Three sharing levels: private, team, community
- Pattern types: command, error, workflow, config
- `pop-pattern-share` skill for interactive sharing

**Quality Assurance (Epic #104)**
- TypeScript migration for cloud packages
- Pytest test suite for hooks
- Linting and code quality tooling
- Value metrics system for Power Mode
- Continuous workflow loop with issue close prompts

#### Component Summary

| Component | Count |
|-----------|-------|
| Tier 1 Agents | 11 |
| Tier 2 Agents | 17 |
| Feature Workflow Agents | 2 |
| Skills | 43 |
| Commands | 18 |
| Hooks | 18 |
| Output Styles | 15+ |

#### Cloud Integration

- Upstash Vector: Semantic agent search (30 agents indexed)
- Upstash Redis: Power Mode, rate limiting, workflow status
- Upstash QStash: Inter-agent communication
- Upstash Workflow: Durable workflow orchestration

---

## [0.9.13]

### Power Mode Value Metrics (#108)

- **MetricsCollector**: New `power-mode/metrics.py` module for quantifiable metrics
  - Time metrics: Phase duration, task times, agent active time
  - Quality metrics: First-pass success rate, code review scores, bugs detected
  - Coordination metrics: Insights shared, context reuses, sync barrier waits
  - Resource metrics: Token usage, agent utilization, peak concurrency
  - Value summary: Overall score (0-100) with rating and highlights
- **Metrics Command**: `/popkit:power metrics` subcommand for viewing reports
  - View current session: `/popkit:power metrics`
  - View specific session: `/popkit:power metrics --session ID`
  - Compare with baseline: `/popkit:power metrics --compare`
- **Coordinator Integration**: Automatic metrics collection throughout Power Mode
  - Agent start/stop tracking
  - Phase timing instrumentation
  - Insight sharing counts
  - Sync barrier wait times
  - Session save to Redis on stop
- **CLI Report**: Formatted metrics output at session end

## [0.9.12]

### Continuous Workflow Loop (#116)

- **Issue Close Prompt**: After `/popkit:dev work #N` completes, prompts to close the issue
- **Epic Parent Check**: Auto-detects when all children of an epic are complete
- **Context-Aware Next Actions**: Presents prioritized open issues as selectable options
- **Keep in the Loop**: Selecting an issue immediately starts work on it
- **Phase 8 added to dev.md**: Close & Continue phase for work mode
- **pop-finish-branch enhanced**: Step 6 for issue close and next actions

### Foundation & Organization

- **Issue Templates Updated**: All templates now include Priority & Phase sections
- **Milestone Strategy**: v1.0.0 for plugin release, v1.1.0 for post-launch
- **Multi-Repo Strategy Documented**: Future public repos for MCP, Codex, Gemini
- **Platform Roadmap Archived**: Moved to `docs/roadmaps/`
- **Epic #88 Closed**: Self-Improvement system fully operational

## [0.9.11]

### Cross-Project Observability

- **Project Registry API** (PopKit Cloud):
  - `POST /v1/projects/register` - Auto-register projects on session start
  - `POST /v1/projects/:id/activity` - Track tool calls and agent usage
  - `GET /v1/projects` - List all registered projects
  - `GET /v1/projects/summary` - Cross-project statistics
- **Plugin Client** (`hooks/utils/project_client.py`):
  - `ProjectClient` class for calling Cloud API
  - Auto-generates project ID from path hash
  - Anonymizes paths for privacy
- **Observe Subcommand** (`/popkit:project observe`):
  - Cross-project dashboard from monorepo
  - View all projects, activity, and health scores
  - `--active` filter for last 24h, `--summary` for quick stats
- **Hook Integration**:
  - `session-start.py` - Auto-registers projects with PopKit Cloud
  - `post-tool-use.py` - Tracks tool usage in PopKit Cloud
- **Smoke Test Skill** (`pop-smoke-test`):
  - Quick runtime health verification
  - Tests plugin loading, hooks, cloud connectivity

## [0.9.10]

### User Feedback & Vote-Based Prioritization

- **User Feedback Collection System** (#91):
  - `hooks/utils/feedback_store.py` - SQLite storage with session tracking and GDPR compliance
  - `hooks/utils/feedback_triggers.py` - Trigger logic with feedback fatigue prevention
  - `hooks/feedback_hook.py` - PostToolUse hook for AskUserQuestion-based collection
  - `skills/pop-feedback-report/` - Analytics skill for viewing statistics
  - 0-3 rating scale: Harmful (0), Unhelpful (1), Helpful (2), Very Helpful (3)
  - Session tracking: min 10 tool calls between prompts, max 3 dismissals before pause
- **Vote-Based Feature Prioritization** (#92):
  - `hooks/utils/vote_fetcher.py` - GitHub reaction fetching with 1-hour SQLite cache
  - `hooks/utils/priority_scorer.py` - Combined priority scoring algorithm
  - Vote weights: 👍 +1, ❤️ +2, 🚀 +3, 👎 -1
  - Priority formula: votes (35%) + staleness (20%) + labels (30%) + epic (15%)
  - `/popkit:issue list --votes` - Sort issues by community priority
  - Updated `pop-next-action` skill with vote integration
- **Monorepo Structure** (#98):
  - Converted to npm workspaces monorepo
  - `packages/plugin/` - Main Claude Code plugin
  - `packages/cloud/` - PopKit Cloud API (Cloudflare Workers)
- **GitHub Issues Closed** - #91, #92, #98 (Self-Improvement Epic child issues)

## [0.9.9]

### Self-Improvement & Learning System

- **Platform-Aware Command Learning** (#89):
  - `hooks/utils/platform_detector.py` - OS/shell detection (Windows/macOS/Linux, CMD/PowerShell/Bash/Git Bash/WSL)
  - `hooks/utils/command_translator.py` - Cross-platform command mapping (cp->xcopy, ls->dir, etc.)
  - `hooks/utils/pattern_learner.py` - SQLite-based correction storage with confidence scoring
  - `hooks/command-learning-hook.py` - PostToolUse hook for failure capture
  - 81 new tests for platform detection and command translation
- **Automatic Bug Reporting** (#90):
  - `hooks/utils/bug_store.py` - SQLite storage with consent levels (strict/moderate/minimal)
  - `hooks/utils/bug_consent.py` - AskUserQuestion-formatted consent prompts
  - `hooks/bug_reporter_hook.py` - PostToolUse hook for automatic error detection
  - GDPR compliance with `export_all()` and `delete_all_data()`
  - Share status tracking: pending, shared, local_only, never_ask
  - 52 new tests for bug store and consent handling
- **Test Cleanup** - Removed orphaned consensus tests (module not merged)
- **GitHub Issues Closed** - #89, #90 (Self-Improvement Epic child issues)

## [0.9.8] - PopKit Cloud & Monetization Foundation

- **Power Mode v2** (#66) - Auto-activation, visibility, and bug fixes
- **Consensus Protocol** (#86) - Multi-agent democratic decision-making
- **Documentation Sync Barrier** (#87) - Power Mode documentation checkpoint
- **PopKit Cloud API** - Cloudflare Workers + Upstash Redis infrastructure
- **Collective Learning System** (#71) - Pattern submission with semantic deduplication
- **Automatic Bug Detection** (#72) - Error pattern matching (20+ patterns)
- **Bug Reporting Command** (#73) - Report, search, and share bug patterns
- **Analytics Dashboard API** (#74) - Efficiency tracking endpoints
- **Privacy Controls & GDPR Compliance** (#77) - Export and deletion endpoints
- **GitHub Issues Closed** - #66-74, #77, #82-87

## [0.9.7] - Command Consolidation

- **Command Consolidation** - Reduced 17 commands to 12 active (7 deprecated):
  - `/popkit:dev` - Unified development command (absorbs design, plan, feature-dev)
  - `/popkit:git` - Enhanced with ci and release subcommands
  - `/popkit:routine` - Unified routine command (absorbs morning, nightly)
  - `/popkit:project` - Enhanced with init subcommand
- **GitHub Issues Closed** - #57-62 (Command Consolidation Epic)

## [0.9.6] - Embeddings Enhancement & Semantic Routing

- **Semantic Embeddings System** - Project-local embedding infrastructure
- **Generator Improvements** - Analysis-driven generation
- **New Skills** - Embedding management (`pop-embed-content`, `pop-embed-project`)
- **MCP Server Template** - Semantic search support
- **GitHub Issues Closed** - #45-55 (Phase 1-3 of Embeddings Enhancement)

## [0.9.5] - Unified Routine Management System

- **Unified Routine Management** - Single command interface for morning/nightly routines
- **Routine Storage Utility** - `hooks/utils/routine_storage.py`
- **Plugin Conflict Detection** - `hooks/utils/plugin_detector.py`
- **GitHub Issues Created** - #28-#34

## [0.9.4] - Platform Integration Completion

- **Closed Platform Issues** - Completed 7 of 14 Claude Platform integration issues
- **Bug Fix** - `--think-budget N` now correctly implies thinking enabled

## [0.9.3] - Claude Platform Feature Integration

- **Effort Parameter Configuration** - Per-agent effort levels in `agents/config.json`
- **Extended Thinking Configuration** - Model-specific defaults with flag overrides
- **Platform Integration Issues** - Created 14 GitHub issues (#14-#27)

## [0.9.2] - Deep Command Consolidation

- **Further Consolidation** - Reduced 22 commands to 15 via subcommand merging
- **Final Count** - 15 top-level commands with comprehensive subcommand structure

## [0.9.1] - Initial Command Consolidation

- **Command Consolidation** - Reduced 31 commands to 22 via subcommand pattern
- **Improved Discoverability** - Related commands grouped under parent command

## [0.9.0]

- **Power Mode Enhancement with GitHub Issue Integration**
- **Flag Parsing Utility** - Centralized flag parsing
- **Status Line Script** - Visual Power Mode indicator
- **Fallback Orchestration** - Auto-generates plan when issue lacks PopKit Guidance

## [0.8.0]

- **Quality Gates Hook** - Auto-validation after file modifications
- **Issue Parser** - Parse PopKit Guidance from GitHub issues
- **Issue-Driven Workflow** - Activation logic for `/popkit:issue work`
- **Enhanced Issue Templates** - 4 templates with PopKit Guidance sections

## [0.7.1]

- **File-Based Power Mode Fallback** - Multi-agent orchestration without Redis
- **Power Init** - Redis setup and management
- **Bug Fix** - Fixed `pre-tool-use.py` attribute mismatch

## [0.7.0]

- **Pop Power Mode** - Multi-agent orchestration via Redis pub/sub
- **Power Coordinator Agent** - Orchestrates multi-agent collaboration
- **Check-In Hook** - PostToolUse hook for agent check-ins

## [0.6.1]

- **Context-Aware Recommendations** - `/popkit:next` command
- **Uncertainty Detection** - Hook suggests `/popkit:next` when user seems unsure

## [0.6.0]

- **Version Reset** - Moved from 1.5.0 to 0.6.0 to reflect pre-stable status
- **Meta-Release Command** - Automated plugin releases
- **Command Restoration** - Fixed 3 corrupted command files

---

## Legacy History (1.x -> 0.6.0 Reset)

> PopKit originally started at v1.0.0 but reset to v0.6.0 to indicate pre-stable status.

**v1.4.0** - Knowledge sync, chain visualization, update notifier
**v1.3.0** - Output validation, sync command, E2E testing
**v1.2.0** - Morning health check, Tier 1 + Tier 2 pattern
**v1.1.0** - Auto-documentation, plugin self-testing, SKILL.md format
