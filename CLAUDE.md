# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**popkit** is a Claude Code plugin providing AI-powered development workflows through skills, agents, commands, and hooks. All commands use the `popkit:` prefix (e.g., `/popkit:commit`, `/popkit:review`). It implements a two-tier architecture:

- **Tier 1 (this repo)**: Universal, project-agnostic tools that work anywhere
- **Tier 2 (generated)**: Project-specific MCP servers, skills, and agents created via `/generate-mcp` and `/generate-skills`

## Repository Structure

```
.claude-plugin/          Plugin manifest (plugin.json, marketplace.json)
.mcp.json                MCP server configuration
agents/                  29 agent definitions with tiered activation
  config.json            Agent routing, workflows, confidence thresholds
  tier-1-always-active/  11 core agents (code-reviewer, bug-whisperer, etc.)
  tier-2-on-demand/      16 specialized agents (including rapid-prototyper)
  feature-workflow/      3 agents for 7-phase feature development
skills/                  26 reusable skills (SKILL.md format in subdirectories)
commands/                23 slash commands for workflows
hooks/                   10 Python hooks (JSON stdin/stdout protocol)
  hooks.json             Hook configuration and event mapping
output-styles/           9 output format templates
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
- `/popkit:generate-morning`: Creates project-specific `[prefix]:morning` with:
  - Service health checks (detected ports, databases)
  - Framework-specific validations
  - Domain checks (API keys, external services)

"Ready to Code" score (0-100) helps prioritize morning fixes.

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

## Version History

**Note:** Popkit uses `0.x.y` versioning until stable. Version `1.0.0` will mark API stability.

### v0.6.1 (Current)

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
- **Command Restoration**: Fixed 3 corrupted command files (`knowledge.md`, `chain-viz.md`, `sync.md`)
- **Enhanced Command Structure**: All commands now include architecture integration tables
- **New Knowledge Subcommand**: Added `/popkit:knowledge search <query>`

### Previous (1.x Legacy)

The 1.x versions were pre-stable releases that have been reset:
- 1.5.0 → Became 0.6.0
- 1.4.x → Knowledge sync, chain visualization, update notifier
- 1.3.x → Output validation, sync command, error tracking
- 1.2.x → Morning health check, tier 1+2 pattern
- 1.1.x → Auto-docs, plugin self-testing, routing debugger

## Features (from 1.4.0)

- **Knowledge Sync** (`/popkit:knowledge`): Configurable external documentation syncing with TTL-based caching
  - Default sources: Claude Code Engineering Blog, Claude Code Documentation
  - Add/remove sources via terminal command
  - Automatic sync on session start with 24-hour cache
  - `pop-knowledge-lookup` skill for agent knowledge queries
- **Chain Visualization** (`/popkit:chain-viz`): Workflow visualization with validation and metrics
  - ASCII diagrams showing agent chains
  - Validation of workflow definitions
  - Performance metrics tracking (timing, success rates, bottlenecks)
  - `pop-chain-management` skill for programmatic access
- **Update Notifier**: Automatic plugin update checks on session start
  - 24-hour TTL cache to avoid repeated API calls
  - Non-blocking with silent failure
  - Clear notification with update command

### v1.4.1

- **Command Prefix Fix**: Removed explicit `name:` field from command frontmatter in `knowledge.md`, `chain-viz.md`, and `sync.md` to ensure proper `/popkit:` prefix registration

### v1.3.0

- **Output Validation Layer**: JSON schemas for agent outputs with `output-validator.py` hook
- **Sync Command** (`/popkit:sync`): Validate plugin integrity (Scan → Compare → Report → Apply)
- **Error Tracking**: Lessons learned system with GitHub issue integration
- **E2E Testing Framework**: 10 end-to-end test scenarios in `tests/e2e/`
- **Validation Engine Skill** (`pop-validation-engine`): Reusable validation pattern
- **Enhanced Routing**: Added lint/eslint/prettier/cleanup keywords and config file patterns

### v1.2.0

- **Morning Health Check** (`/popkit:morning`): Universal morning routine with "Ready to Code" score
- **Morning Generator** (`/popkit:generate-morning`): Create project-specific morning commands
- **Tier 1 + Tier 2 Pattern**: Generic commands that generate project-specific versions

### v1.1.0

- **Auto-Documentation** (`/popkit:auto-docs`): Generate and sync documentation
- **Plugin Self-Testing** (`/popkit:plugin-test`): Validate all plugin components
- **Routing Debugger** (`/popkit:routing-debug`): Debug agent selection logic
- **SKILL.md Format**: Skills now use directory structure (`skills/name/SKILL.md`)
- **JSON Hook Protocol**: All hooks use stdin/stdout JSON instead of argv
- **MCP Configuration**: `.mcp.json` for Model Context Protocol integration

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
