# Changelog

All notable changes to PopKit are documented in this file.

**Versioning:** PopKit uses `0.x.y` versioning until stable. Version `1.0.0` will mark API stability.

## [0.9.12] - Current

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
