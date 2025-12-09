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
   <!-- AUTO-GEN:TIER-COUNTS START -->
   - Tier 1: Always-active core agents (11)
   - Tier 2: On-demand specialists activated by triggers (17)
   - Feature Workflow: 7-phase development agents (3)
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

## Repository Structure

This is a **monorepo** with npm workspaces:

<!-- AUTO-GEN:REPO-STRUCTURE START -->
```
packages/
  plugin/                  Claude Code plugin (main package)
    .claude-plugin/        Plugin manifest (plugin.json, marketplace.json)
    .mcp.json              MCP server configuration
    agents/                30 agent definitions with tiered activation
      config.json          Agent routing, workflows, confidence thresholds
      tier-1-always-active/  11 core agents
      tier-2-on-demand/    17 specialized agents
      feature-workflow/    3 agents for 7-phase feature development
    skills/                36 reusable skills (SKILL.md format)
    commands/              15 slash commands
    hooks/                 18 Python hooks (JSON stdin/stdout)
      hooks.json           Hook configuration
      utils/               24 utility modules
    output-styles/         15+ output format templates
    power-mode/            Multi-agent orchestration
    templates/mcp-server/  MCP server generator template
    tests/                 Plugin self-test definitions
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
- Opus: Disabled by default, use `-T` to enable
- Haiku: Enabled by default (5k tokens)

### PDF Support

Skills accept PDF file paths for design docs, PRDs, and specifications.
Use `document-skills:pdf` to generate PDF output.

### Semantic Embeddings

Voyage AI embeddings for tool discovery. Set `VOYAGE_API_KEY` env var.
Use `/popkit:project embed` to embed project items.

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

Subcommands: `run`, `quick`, `generate`, `list`, `set`, `edit`, `delete`

See `packages/plugin/commands/routine.md` for full documentation.

### Power Mode (Multi-Agent Orchestration)

Parallel agent collaboration via `/popkit:power`:
- **Redis Mode**: Full power, 6+ agents, requires Docker
- **File-Based Mode**: Zero setup, 2-3 agents, auto-fallback

Use `/popkit:power init` to set up. See `packages/plugin/commands/power.md` for details.

### Stateless Message Composition

Hooks use pure functions for reliability and testability:
- `packages/plugin/hooks/utils/message_builder.py` - Message composition
- `packages/plugin/hooks/utils/context_carrier.py` - Immutable context passing
- `packages/plugin/hooks/utils/stateless_hook.py` - Base class for hooks

See `packages/plugin/tests/hooks/` for 58 tests covering this pattern.

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
| `packages/plugin/power-mode/coordinator.py` | Multi-agent mesh network coordinator |
| `packages/plugin/power-mode/statusline.py` | Visual Power Mode status line display |
| `packages/plugin/hooks/utils/` | 24 utility modules (embeddings, routing, etc.) |
| `packages/cloud/src/index.ts` | Cloud API entry point |
| `packages/cloud/wrangler.toml` | Cloudflare Workers configuration |
<!-- AUTO-GEN:KEY-FILES END -->

## Version History

**Current Version:** 0.9.9 (Self-Improvement & Learning System)

See [CHANGELOG.md](CHANGELOG.md) for full version history.

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
