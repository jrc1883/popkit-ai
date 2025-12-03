# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**popkit** is a Claude Code plugin providing AI-powered development workflows through skills, agents, commands, and hooks. All commands use the `popkit:` prefix (e.g., `/popkit:commit`, `/popkit:review`). It implements a two-tier architecture:

- **Tier 1 (this repo)**: Universal, project-agnostic tools that work anywhere
- **Tier 2 (generated)**: Project-specific MCP servers, skills, and agents created via `/generate-mcp` and `/generate-skills`

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
   - Tier 1: Always-active core agents (11)
   - Tier 2: On-demand specialists activated by triggers (16)
   - Feature Workflow: 7-phase development agents (3)

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

## Repository Structure

```
.claude-plugin/          Plugin manifest (plugin.json, marketplace.json)
.mcp.json                MCP server configuration
agents/                  30 agent definitions with tiered activation
  config.json            Agent routing, workflows, confidence thresholds
  tier-1-always-active/  11 core agents (code-reviewer, bug-whisperer, etc.)
  tier-2-on-demand/      17 specialized agents (including power-coordinator)
  feature-workflow/      2 agents for 7-phase feature development
skills/                  30 reusable skills (SKILL.md format in subdirectories)
commands/                15 slash commands for workflows (consolidated with subcommands)
hooks/                   17 Python hooks (JSON stdin/stdout protocol)
  hooks.json             Hook configuration and event mapping
  utils/                 Stateless utilities (message_builder.py, context_carrier.py, stateless_hook.py, mcp_detector.py)
  pre_tool_use_stateless.py  Stateless safety checks
  post_tool_use_stateless.py Stateless result processing
output-styles/           15+ output format templates (includes schemas/)
power-mode/              Multi-agent orchestration (Redis or file-based)
  protocol.py            Message types, serialization, guardrails
  coordinator.py         Mesh brain with objective tracking
  coordinator_auto.py    Auto-detects Redis vs file-based mode
  file_fallback.py       File-based fallback (no Redis required)
  checkin-hook.py        PostToolUse hook for agent check-ins
  config.json            Channels, intervals, constraints
  docker-compose.yml     Redis + Commander Docker setup
  setup-redis.py         Cross-platform Redis management script
templates/mcp-server/    Template for generating project-specific MCP servers
tests/                   Plugin self-test definitions
  hooks/                 Hook input/output tests
  routing/               Agent routing tests
  structure/             File structure validation tests
```

## Development Notes

This is a **configuration-only plugin** - no build or lint commands exist. All content is:
- Markdown files with YAML frontmatter (skills, commands, agents)
- JSON configuration (plugin.json, config.json, hooks.json, .mcp.json)
- Python scripts (hooks with JSON stdin/stdout protocol)
- TypeScript templates (mcp-server)
- JSON test definitions (tests/)

**Self-testing available:** Run `/popkit:plugin-test` to validate plugin integrity.

## Claude Platform Integration

PopKit leverages Claude API platform features for optimal performance. Configuration is in `agents/config.json`.

### Effort Parameter

Controls compute allocation per agent based on what 80% of scenarios require:

| Level | When to Use | Agents |
|-------|-------------|--------|
| `high` | Deep analysis, critical decisions | bug-whisperer, security-auditor, code-architect, power-coordinator |
| `medium` | Balanced scenarios (default) | code-reviewer, test-writer-fixer, api-designer |
| `low` | Straightforward tasks | documentation-maintainer, rapid-prototyper, user-story-writer |

### Extended Thinking

Model-specific thinking configuration with flag overrides:

| Model | Default | Budget | Override |
|-------|---------|--------|----------|
| Sonnet | Enabled | 10k tokens | `--no-thinking` to disable |
| Opus | Disabled | - | `-T` or `--thinking` to enable |
| Haiku 4.5 | Enabled | 5k tokens | `--no-thinking` to disable |

**Flags:** `-T`, `--thinking`, `--no-thinking`, `--think-budget N`

**Example:** `/popkit:design brainstorm -T` enables thinking on Opus

### Tool Choice

Workflow step tool enforcement in `agents/config.json`:

```json
"git-commit": {
  "steps": [
    { "action": "stage_files", "tool_choice": { "type": "tool", "name": "Bash" } }
  ]
}
```

### Model Assignment per Agent

Different agents use different Claude models based on task complexity:

| Model | Use Case | Agents |
|-------|----------|--------|
| `haiku` | Writing, quick tasks | documentation-maintainer, user-story-writer, rapid-prototyper |
| `sonnet` | Balanced (default) | code-reviewer, test-writer-fixer, api-designer |
| `opus` | Deep reasoning | bug-whisperer, security-auditor, code-architect, power-coordinator |

**Heuristics:**
- **Haiku**: Docs, comments, prototypes (fast, cheap)
- **Sonnet**: Review, testing, most development (balanced)
- **Opus**: Architecture, security, debugging (thorough)

**Override:** Use `--model opus` to force a specific model for any agent

### JSON Schema Strict Mode

Output style schemas use `strict: true` for guaranteed valid JSON output.

### Stop Reason Handling

Hooks detect truncation (`max_tokens`) and warn users with recovery suggestions.

### PDF Support

Claude can read PDF files directly. PopKit leverages this for:

**Input Support** - Skills that accept PDF file paths:
- `pop-brainstorming`: Read design docs, PRDs, specifications
- `pop-executing-plans`: Read implementation plans, PRDs
- `code-architect`: Analyze architecture diagrams, ADRs

**Output Styles** - PDF-formatted output templates:
- `pdf-report`: Formal analysis report for stakeholders
- `pdf-prd`: Product requirements document
- `pdf-architecture`: Architecture decision record (ADR)

**Usage:** Provide PDF path in user message:
```
User: Analyze this design: /path/to/design.pdf
User: Execute plan from: /path/to/implementation.pdf
```

Use `document-skills:pdf` to generate actual PDF files from output.

## Key Architectural Patterns

### Agent Routing (agents/config.json)

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

### Morning Routine (Generic + Generator)

Two-tier approach for daily health checks:
- `/popkit:morning`: Generic check (git, tests, lint) - works on any project
- `/popkit:morning generate`: Creates project-specific `[prefix]:morning` with:
  - Service health checks (detected ports, databases)
  - Framework-specific validations
  - Domain checks (API keys, external services)

"Ready to Code" score (0-100) helps prioritize morning fixes.

**MCP Detection** (`hooks/utils/mcp_detector.py`):

The generator auto-detects existing MCP infrastructure before generating commands:

| Detection | Result | Command Size |
|-----------|--------|--------------|
| MCP + health tools | `mcp_wrapper` recommendation | 10-20 lines |
| MCP, no health tools | `hybrid` recommendation | Mixed |
| No MCP | `bash` recommendation | 100+ lines |

MCP health tools detected: `morning_routine`, `check_*`, `*_health`, `*_status`, `ping_*`, `verify_*`

**Generator Flags:**
- `--detect`: Preview MCP detection without generating
- `--bash`: Force bash-based generation (skip MCP)
- `--mcp-wrapper`: Force MCP wrapper generation

### Power Mode (Multi-Agent Orchestration)

Parallel agent collaboration with two backend options:

**Redis Mode** (Full Power):
- Real-time pub/sub messaging between agents
- Sync barriers between workflow phases
- Supports 6+ parallel agents
- Requires Docker: `/popkit:power init start`

**File-Based Mode** (No Dependencies):
- Uses shared JSON file for coordination
- Good for 2-3 agents, development, learning
- Auto-activates when Redis unavailable
- Zero setup required

Both modes provide:
- Periodic check-ins every N tool calls (push state, pull insights)
- Coordinator agent manages mesh network
- Guardrails prevent "cheating" (unconventional approaches require human approval)
- Inspired by ZigBee mesh networks and DeepMind's objective-driven agents

### Stateless Message Composition

Hooks follow a stateless pattern for reliability, testability, and error recovery:

**Message Builder** (`hooks/utils/message_builder.py`):
- Pure functions for composing Claude API messages
- `build_user_message()`, `build_assistant_message()`: Basic messages
- `build_tool_use_message()`, `build_tool_result_message()`: Tool interactions
- `merge_tool_uses()`, `merge_tool_results()`: Parallel tool handling
- `rebuild_from_history()`: Reconstruct messages for retry/debugging

**Context Carrier** (`hooks/utils/context_carrier.py`):
- Immutable `HookContext` dataclass
- Explicit state passing between hooks (no SQLite or env vars)
- JSON serialization for persistence between turns
- `create_context()`, `update_context()`, `serialize_context()`

**Stateless Hook Base** (`hooks/utils/stateless_hook.py`):
- `StatelessHook` ABC for building hooks
- No hidden state or external dependencies
- Full context in, full context out

**Example:**
```python
from stateless_hook import StatelessHook
from context_carrier import HookContext

class MySafetyHook(StatelessHook):
    def process(self, ctx: HookContext) -> HookContext:
        # Pure function - no external state
        if self._is_dangerous(ctx.tool_input):
            return self.update_context(ctx, hook_output=("safety", {"action": "block"}))
        return self.update_context(ctx, hook_output=("safety", {"action": "continue"}))
```

**Tests:** 58 tests in `tests/hooks/` covering message building, context passing, and integration.

## Installing popkit for Development

To use popkit while developing popkit (chicken-and-egg), install it from GitHub:

```
/plugin marketplace add jrc1883/popkit
/plugin install popkit@popkit-marketplace
```

Then **restart Claude Code** to load the plugin. After restart, `/popkit:` commands will be available.

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

Located in `templates/mcp-server/`, this TypeScript template generates project-specific MCP servers with:
- Health checks (dev server, database)
- Git tools (status, diff, recent commits)
- Quality tools (typecheck, lint, tests)
- Semantic tool discovery via embeddings

To build the template locally:
```bash
cd templates/mcp-server
npm install
npm run build
```

## Key Files for Plugin Behavior

| File | Purpose |
|------|---------|
| `.claude-plugin/plugin.json` | Plugin manifest and activation triggers |
| `.mcp.json` | MCP server and tool configuration |
| `agents/config.json` | All routing rules, workflows, confidence levels |
| `hooks/hooks.json` | Hook event configuration |
| `hooks/pre-tool-use.py` | Safety checks before tool execution |
| `hooks/post-tool-use.py` | Cleanup and validation after tools |
| `hooks/agent-orchestrator.py` | Agent sequencing and routing logic |
| `power-mode/coordinator.py` | Multi-agent mesh network coordinator |
| `power-mode/coordinator_auto.py` | Auto-detects Redis vs file-based mode |
| `power-mode/file_fallback.py` | File-based fallback (no Redis needed) |
| `power-mode/checkin-hook.py` | Periodic agent check-ins |
| `power-mode/setup-redis.py` | Cross-platform Redis management |
| `power-mode/statusline.py` | Visual Power Mode status line display |
| `hooks/utils/flag_parser.py` | Centralized command flag parsing |
| `hooks/utils/github_issues.py` | GitHub issue guidance parsing |
| `hooks/utils/mcp_detector.py` | MCP infrastructure detection for morning generator |

## Version History

**Note:** Popkit uses `0.x.y` versioning until stable. Version `1.0.0` will mark API stability.

### v0.9.4 (Current) - Platform Integration Completion

- **Closed Platform Issues** - Completed 7 of 14 Claude Platform integration issues:
  - #14: Effort Parameter (config + documentation)
  - #15: Extended Thinking Configuration (flags, model defaults)
  - #16: Context Token Monitoring (hook with thresholds)
  - #17: Tool Description Enhancement (19 skills updated)
  - #18: Stop Reason Handling (truncation detection)
  - #21: tool_choice Parameter (workflow enforcement)
  - #24: JSON Schema strict Mode (5 schemas updated)
- **Documentation** - Added "Claude Platform Integration" section to CLAUDE.md
- **Testing** - Added skill description validation tests
- **Bug Fix** - `--think-budget N` now correctly implies thinking enabled

### v0.9.3 - Claude Platform Feature Integration

- **Effort Parameter Configuration** - Added `effort` section to `agents/config.json`
  - Per-agent effort levels (low/medium/high) based on 80% scenario analysis
  - High effort: bug-whisperer, security-auditor, performance-optimizer, query-optimizer, migration-specialist, ai-engineer, power-coordinator, rollback-specialist, code-architect
  - Low effort: documentation-maintainer, feature-prioritizer, rapid-prototyper, user-story-writer, feedback-synthesizer
  - All others default to medium
- **Extended Thinking Configuration** - Added `thinking` section to `agents/config.json`
  - Sonnet: Thinking enabled by default (10k tokens)
  - Opus: Thinking off by default, enable with `-T` flag
  - Haiku 4.5: Thinking enabled (5k tokens)
  - Flags: `-T`/`--thinking`, `--no-thinking`, `--think-budget N`
- **Thinking Flag Parser** - Added `parse_thinking_flags()` to `hooks/utils/flag_parser.py`
- **Platform Integration Issues** - Created 14 GitHub issues (#14-#27) tracking:
  - Effort parameter (#14), Extended thinking (#15), Context token monitoring (#16)
  - Tool descriptions (#17), Stop reason handling (#18), Embeddings (#19)
  - PDF support (#20), tool_choice (#21), Stateless messages (#22)
  - Fine-grained streaming (#23), JSON Schema strict (#24)
  - Future: Model per agent (#25), Computer use (#26), Code execution (#27)

### v0.9.2 - Deep Command Consolidation

- **Further Consolidation** - Reduced 22 commands to 15 via additional subcommand merging
  - `/popkit:ci` (new) from `run` + `release` → `run list/view/rerun/watch/cancel/download/logs`, `release create/list/view/edit/delete/changelog`
  - `/popkit:design` (new) from `brainstorm` + `prd` → `brainstorm`, `prd` subcommands
  - `/popkit:debug` enhanced with `code` (default) + `routing` subcommands (merged `routing-debug`)
  - `/popkit:plugin` (new) from `auto-docs` + `sync` + `plugin-test` → `test`, `docs`, `sync` subcommands
  - `/popkit:git` enhanced with `pr` management (`list/view/merge/checkout/diff/ready/update`) + `review` subcommand
- **Removed Redundancy** - Merged `pr` and `review` into `git` command
- **Final Count** - 15 top-level commands with comprehensive subcommand structure

### v0.9.1 - Initial Command Consolidation

- **Command Consolidation** - Reduced 31 commands to 22 via subcommand pattern
  - `/popkit:morning` + `generate-morning` → `/popkit:morning` with `generate` subcommand
  - `/popkit:power` + `power-mode` + `power-init` → `/popkit:power` with `status`, `start`, `stop`, `init` subcommands
  - `/popkit:issue` + `issues` + `work` → `/popkit:issue` with `list`, `view`, `create`, `work`, `close`, `comment`, `edit`, `link` subcommands
  - `/popkit:plan` (new) from `write-plan` + `execute-plan` → `write`, `execute`, `list`, `view` subcommands
  - `/popkit:git` (new) from `commit` + `commit-push-pr` + `prune-branches` + `finish-branch` → `commit`, `push`, `pr`, `prune`, `finish` subcommands
- **Improved Discoverability** - Related commands grouped under parent command
- **Consistent Patterns** - All commands now follow subcommand structure

### v0.9.0

- **Power Mode Enhancement with GitHub Issue Integration**
  - New unified command architecture: `/popkit:issue work #N -p`
  - Power Mode as flag modifier (`-p`/`--power`, `--solo`) on issue commands
  - Status line integration: `[POP] #N Phase: X (N/M) [####--] %` when active
- **Flag Parsing Utility** (`hooks/utils/flag_parser.py`)
  - Centralized parsing for `-p`, `--power`, `--solo`, `--phases`, `--agents` flags
- **Status Line Script** (`power-mode/statusline.py`)
  - Visual Power Mode indicator with phase progress
  - ANSI color output for terminal display
  - Detailed status command (`/popkit:power status`)
- **Fallback Orchestration** (`generate_orchestration_plan` in github_issues.py)
  - Auto-generates plan when issue lacks PopKit Guidance
  - Infers issue type, complexity, phases, and agents from labels/content
  - Confidence scoring with user guidance suggestions
- **Enhanced Checkin Hook** (`power-mode/checkin-hook.py`)
  - Project-local state file preference for status line integration
  - Merges agent tracking with Power Mode state
- **Unified Init Flow** (init-project.md, pop-project-init skill)
  - Power Mode setup option during project initialization
  - Redis Mode vs File Mode selection

### v0.8.0

- **Quality Gates Hook** (`quality-gate.py`): Auto-validation after file modifications
  - Detects project type (TypeScript, build scripts, lint)
  - High-risk action triggers (config changes, deletions, import/export changes)
  - Batch threshold (5 edits) and rapid change detection (3+ files)
  - Interactive failure menu: Fix/Rollback/Continue/Pause
  - Rollback mechanism with git stash + patch file preservation
- **Issue Parser** (`github_issues.py`): Parse PopKit Guidance from GitHub issues
  - Extracts workflow type, phases, agents, quality gates, Power Mode settings
  - Infers issue type from labels and content
  - Maps issue types to recommended agents
- **Issue-Driven Workflow** (`issue-workflow.py`): Activation logic for `/popkit:issue work`
  - Auto-triggers brainstorming based on issue guidance
  - Activates Power Mode for epic/complex issues
  - Generates todos from workflow phases
  - Tracks phase completion across sessions
- **Enhanced Issue Templates**: 4 templates with PopKit Guidance sections
  - Feature Request, Bug Report, Architecture, Research templates
  - Structured metadata for workflow orchestration

### v0.7.1

- **File-Based Power Mode Fallback**: Multi-agent orchestration without Redis
  - `file_fallback.py`: Redis-compatible interface using JSON files
  - `coordinator_auto.py`: Auto-detects Redis vs file-based mode
  - Zero setup required for development/learning
  - Good for 2-3 agents without Docker dependency
- **Power Init** (now `/popkit:power init`): Redis setup and management
  - Docker-based Redis with one command
  - Redis Commander for debugging (`init debug`)
  - Cross-platform setup script
- **Bug Fix**: Fixed `pre-tool-use.py` attribute mismatch (`coordination_rules`)

### v0.7.0

- **Pop Power Mode** (now `/popkit:power start`): Multi-agent orchestration via Redis pub/sub
  - Parallel agent collaboration with shared context
  - Periodic check-ins every N tool calls (push state, pull insights)
  - Sync barriers between workflow phases
  - Coordinator agent manages mesh network
  - Guardrails prevent "cheating" (unconventional approaches require human approval)
  - Inspired by ZigBee mesh networks and DeepMind's objective-driven agents
- **Power Coordinator Agent** (`power-coordinator`): Orchestrates multi-agent collaboration
- **Check-In Hook** (`power-mode-checkin`): PostToolUse hook for agent check-ins
- **Power Mode Output Style**: Standardized format for inter-agent communication
- **Power Mode Skill** (`pop-power-mode`): Activation and configuration skill

### v0.6.1

- **Context-Aware Recommendations** (`/popkit:next`): Analyzes project state and recommends next actions
  - Checks git status, TypeScript errors, GitHub issues, TECHNICAL_DEBT.md
  - Scores and prioritizes recommendations based on context
  - Supports `quick` and `verbose` modes
  - Uses `pop-next-action` skill and `next-action-report` output style
- **Uncertainty Detection**: Hook now suggests `/popkit:next` when user seems unsure
  - Triggers on phrases like "what should I do", "stuck", "where to go"

### v0.6.0

- **Version Reset**: Moved from 1.5.0 to 0.6.0 to reflect pre-stable status
- **Meta-Release Command**: Added `/popkit:popkit-release` for automated plugin releases
- **Command Restoration**: Fixed 3 corrupted command files (`knowledge.md`, `workflow-viz.md`, `sync.md`)
- **Enhanced Command Structure**: All commands now include architecture integration tables
- **New Knowledge Subcommand**: Added `/popkit:knowledge search <query>`

---

## Legacy Version History (1.x → 0.6.0 Reset)

> **Note:** Popkit originally started at v1.0.0 but reset to v0.6.0 to indicate pre-stable status.
> The features below are retained in current versions; this is historical context only.

**v1.5.0** → Reset to **v0.6.0**

**v1.4.0 Features** (now in current):
- Knowledge sync with TTL-based caching
- Chain visualization with metrics
- Update notifier

**v1.3.0 Features** (now in current):
- Output validation layer with JSON schemas
- Sync command for plugin integrity
- E2E testing framework

**v1.2.0 Features** (now in current):
- Morning health check with "Ready to Code" score
- Morning generator for project-specific commands
- Tier 1 + Tier 2 pattern

**v1.1.0 Features** (now in current):
- Auto-documentation generation
- Plugin self-testing
- Routing debugger
- SKILL.md format in directories
- JSON hook protocol

## Conventions

- All commits use conventional commit format with Claude attribution
- Output styles define templates for PRs, issues, releases, reviews
- Skills can invoke other skills; commands can invoke skills
- Python hooks use `#!/usr/bin/env python3` and are chmod +x

## Releasing New Versions

When releasing a new version of popkit:

### 1. Update Version Numbers

Update version in these files (must match):
- `.claude-plugin/plugin.json` - Main plugin version
- `.claude-plugin/marketplace.json` - Marketplace version

### 2. Update Changelog

Add new version section to this file under "New Features":
```markdown
## New Features (vX.Y.Z)

- **Feature Name**: Description
- **Another Feature**: Description

### vX.Y.Z-1
...
```

### 3. Commit and Push

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json CLAUDE.md
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
