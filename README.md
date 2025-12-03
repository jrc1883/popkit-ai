# PopKit

AI-powered development workflows for Claude Code with skills, agents, and automation.

**Version:** 0.9.4 | **Commands:** 15 | **Agents:** 30 | **Skills:** 30

## What is PopKit?

PopKit orchestrates Claude Code's full power for real-world development. Instead of raw tools, you get composable workflows that chain together simple tasks into sophisticated processes.

```
Idea → Brainstorm → Plan → Implement → Review → Ship
```

## Quick Install

```bash
# From Claude Marketplace
/plugin marketplace add jrc1883/popkit
/plugin install popkit@popkit-marketplace
# Restart Claude Code to load
```

## Core Workflows

### Feature Development

```bash
/popkit:design brainstorm       # Refine idea with Socratic questioning
/popkit:worktree create feat-x  # Create isolated workspace
/popkit:plan write              # Generate implementation plan
/popkit:plan execute            # Build with TDD and checkpoints
/popkit:git pr                  # Create pull request
```

### Issue-Driven Development

```bash
/popkit:issue list              # View open issues
/popkit:issue work 42           # Start working (parses PopKit Guidance)
/popkit:issue work 42 -p        # With Power Mode for complex issues
/popkit:debug                   # Systematic debugging
/popkit:git commit              # Auto-commit with repo style
/popkit:issue close 42          # Mark complete
```

### Daily Operations

```bash
/popkit:morning                 # Health check with "Ready to Code" score
/popkit:next                    # Context-aware recommendations
/popkit:git prune               # Clean up merged branches
```

## Commands (15)

All commands use subcommand patterns for discoverability.

| Command | Subcommands | Description |
|---------|-------------|-------------|
| `/popkit:issue` | `list`, `view`, `create`, `work`, `close`, `comment`, `edit`, `link` | GitHub issue management |
| `/popkit:git` | `commit`, `push`, `pr`, `prune`, `finish`, `review` | Git and PR operations |
| `/popkit:plan` | `write`, `execute`, `list`, `view` | Implementation planning |
| `/popkit:design` | `brainstorm`, `prd` | Design refinement |
| `/popkit:power` | `status`, `start`, `stop`, `init` | Multi-agent orchestration |
| `/popkit:ci` | `run`, `release` | GitHub Actions and releases |
| `/popkit:plugin` | `test`, `docs`, `sync` | Plugin management |
| `/popkit:debug` | (default), `routing` | Debugging and diagnostics |
| `/popkit:worktree` | `create`, `list`, `remove`, `analyze` | Git worktree management |
| `/popkit:morning` | (default), `generate` | Health checks |
| `/popkit:next` | `quick`, `verbose` | Action recommendations |
| `/popkit:init-project` | - | Project scaffolding |
| `/popkit:feature-dev` | - | 7-phase development |
| `/popkit:knowledge` | `add`, `refresh`, `search` | External knowledge |
| `/popkit:workflow-viz` | - | Chain visualization |

## Agents (30)

### Tier-1: Always Active (11)

Core agents available for every task:

| Agent | Specialty |
|-------|-----------|
| `code-reviewer` | Code quality, best practices |
| `bug-whisperer` | Complex debugging |
| `security-auditor` | Vulnerability assessment |
| `test-writer-fixer` | Test implementation |
| `api-designer` | API patterns |
| `performance-optimizer` | Performance analysis |
| `refactoring-expert` | Code restructuring |
| `documentation-maintainer` | Doc synchronization |
| `query-optimizer` | Database optimization |
| `migration-specialist` | System migrations |
| `accessibility-guardian` | A11y compliance |

### Tier-2: On-Demand (17)

Specialized agents activated by triggers:

`ai-engineer`, `deployment-validator`, `feature-prioritizer`, `rapid-prototyper`, `backup-coordinator`, `meta-agent`, `researcher`, `user-story-writer`, `devops-automator`, `bundle-analyzer`, `log-analyzer`, `metrics-collector`, `feedback-synthesizer`, `rollback-specialist`, `data-integrity`, `dead-code-eliminator`, `power-coordinator`

### Feature Workflow (2)

For 7-phase feature development:

- `code-explorer` - Trace execution paths and dependencies
- `code-architect` - Design blueprints and implementation maps

## Skills (30)

Skills are invoked via the Skill tool. Key skills:

| Category | Skills |
|----------|--------|
| **Development** | `pop-brainstorming`, `pop-writing-plans`, `pop-executing-plans`, `pop-systematic-debugging`, `pop-test-driven-development`, `pop-code-review` |
| **Quality** | `pop-verify-completion`, `pop-root-cause-tracing`, `pop-defense-in-depth`, `pop-simplify-cascade` |
| **Session** | `pop-session-capture`, `pop-session-resume`, `pop-context-restore` |
| **Power Mode** | `pop-power-mode`, `pop-worktrees`, `pop-finish-branch` |
| **Generation** | `pop-project-init`, `pop-mcp-generator`, `pop-skill-generator`, `pop-morning-generator` |

## Output Styles (18)

Templates for consistent formatting:

| Category | Styles |
|----------|--------|
| **Git/GitHub** | `commit-message`, `pull-request`, `github-issue`, `release-notes` |
| **Development** | `code-review`, `implementation-plan`, `debugging-report`, `analysis-report` |
| **PDF Export** | `pdf-report`, `pdf-prd`, `pdf-architecture` |
| **Session** | `morning-report`, `nightly-summary`, `agent-handoff` |
| **Power Mode** | `power-mode-checkin`, `next-action-report`, `security-audit-report` |

## Power Mode

Multi-agent orchestration for complex tasks.

### Two Options

| Mode | Setup | Agents | Best For |
|------|-------|--------|----------|
| **File-Based** | None | 2-3 | Development, learning |
| **Redis** | Docker | 6+ | Production, full power |

### Usage

```bash
# File-based (auto-activates, zero setup)
/popkit:power start "Build user authentication"

# Redis (full orchestration)
/popkit:power init start    # Start Redis container
/popkit:power start "Build user authentication"
/popkit:power status        # Check progress
/popkit:power stop          # End session
```

### Features

- Periodic agent check-ins (push state, pull insights)
- Sync barriers between workflow phases
- Coordinator manages agent mesh network
- Guardrails prevent unconventional approaches
- Human escalation for sensitive operations

## Quality Gates

Automatic validation after file modifications.

**Triggers:** Config changes, 5+ file edits, rapid multi-file changes

**Gates:** TypeScript (`tsc`), Build (`npm run build`), Lint (`npm run lint`)

**On Failure:** Fix now, Rollback, Continue, or Pause

## Claude Platform Integration

PopKit leverages Claude API features for optimal performance.

| Feature | Usage |
|---------|-------|
| **Effort Parameter** | `high` for debugging/security, `low` for docs |
| **Extended Thinking** | Sonnet: ON, Opus: OFF (use `-T` flag) |
| **Tool Choice** | Workflow step enforcement |
| **PDF Support** | Read design docs, generate PDF reports |

## Architecture

**Tier 1 (this repo):** Universal, project-agnostic tools

**Tier 2 (generated):** Project-specific MCP servers, skills, agents

```bash
/popkit:init-project        # Create .claude/ structure
/popkit:project mcp         # Generate project MCP server
/popkit:project skills      # Generate project skills
```

## Version History

### v0.9.4 (Current)
- PDF support for input/output
- Redis detection fix
- Flag parser bug fix

### v0.9.3
- Claude Platform Integration (effort, thinking, tool_choice)
- JSON Schema strict mode
- Stop reason handling

### v0.9.2
- Deep command consolidation (31 → 15 commands)
- Subcommand patterns for discoverability

### v0.9.0
- Power Mode with GitHub issue integration
- Status line integration
- File-based fallback orchestration

## License

MIT

## Author

Joseph Cannon (joseph.cannon@outlook.com)

---

*PopKit orchestrates Claude Code's full power for real-world development workflows.*
