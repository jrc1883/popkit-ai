# popkit

Pop Toolkit - AI-powered development workflows for Claude Code with skills, agents, and automation. All commands use the `popkit:` prefix (e.g., `/popkit:commit`, `/popkit:review`).

## Features

- **30 Specialized Agents** - 11 Tier-1 always-active + 17 Tier-2 on-demand + 2 feature-workflow
- **30 Skills** - From brainstorming to power mode to knowledge management
- **28 Commands** - Full GitHub lifecycle, git operations, power mode orchestration
- **16 Hooks** - Safety checks, agent orchestration, quality gates, power mode check-ins
- **14 Output Styles** - Consistent templates for commits, PRs, reviews, power mode check-ins
- **Quality Gates** - Auto-validation (tsc, build, lint) with rollback on failure
- **Issue-Driven Workflow** - Parse GitHub issues for automatic orchestration
- **Power Mode** - Multi-agent orchestration (Redis or file-based fallback)
- **MCP Server Template** - Generate project-specific dev servers with semantic search

## Installation

```bash
claude plugins add popkit
```

Or install from GitHub:

```bash
claude plugins add https://github.com/jrc1883/popkit
```

## Quick Start

### New Project Setup

```bash
/popkit:init-project           # Create .claude/ structure
/popkit:prd                    # Create requirements document
/popkit:analyze-project        # Discover patterns and opportunities
/popkit:setup-precommit        # Configure quality gates
/popkit:generate-mcp           # Create project-specific MCP server
```

### Feature Development

```bash
/popkit:brainstorm             # Refine idea with Socratic questioning
/popkit:worktree create feat-x # Create isolated workspace
/popkit:write-plan             # Generate implementation plan
/popkit:execute-plan           # Build with TDD
/popkit:review                 # Code review with confidence filtering
/popkit:finish-branch          # Merge, PR, keep, or discard
```

### Issue-Driven Development

```bash
/popkit:issue create           # Create AI-executable GitHub issue
/popkit:issue work 11          # Start working on issue (activates workflow)
/popkit:worktree create fix-123
/popkit:debug                  # Systematic debugging
/popkit:pr create              # Submit fix with template
/popkit:issue close            # Mark complete
```

The `/popkit:issue work <number>` command:
- Parses the PopKit Guidance section from the issue
- Triggers brainstorming if specified in the issue
- Activates Power Mode for epic/complex issues
- Creates todos from the issue phases
- Suggests appropriate agents

## Commands Reference

### Core Workflow
| Command | Description |
|---------|-------------|
| `/popkit:brainstorm` | Interactive design refinement using Socratic method |
| `/popkit:write-plan` | Create detailed implementation plan |
| `/popkit:execute-plan` | Execute plan in batches with review checkpoints |
| `/popkit:debug` | Systematic debugging with root cause analysis |
| `/popkit:review` | Code review with confidence-based filtering |
| `/popkit:feature-dev` | 7-phase feature development workflow |

### Git Operations
| Command | Description |
|---------|-------------|
| `/popkit:commit` | Auto-generate commit message matching repo style |
| `/popkit:commit-push-pr` | Full workflow: branch -> commit -> push -> PR |
| `/popkit:clean-gone` | Remove stale branches after PR merges |
| `/popkit:worktree create <name>` | Create isolated workspace with branch |
| `/popkit:worktree analyze` | Identify worktree opportunities |
| `/popkit:finish-branch` | Complete work with 4-option flow |

### GitHub Lifecycle
| Command | Description |
|---------|-------------|
| `/popkit:issue create` | Create AI-executable GitHub issue |
| `/popkit:issue list/view/close` | Issue management |
| `/popkit:pr create` | Create PR with template |
| `/popkit:pr list/view/merge` | PR management |
| `/popkit:run list/view/rerun` | GitHub Actions management |
| `/popkit:release create` | Create GitHub release |

### Project Setup
| Command | Description |
|---------|-------------|
| `/popkit:init-project` | Initialize new project with .claude/ structure |
| `/popkit:prd` | Create Product Requirements Document |
| `/popkit:generate-mcp` | Generate project-specific MCP server |
| `/popkit:generate-skills` | Generate project-specific skills |
| `/popkit:analyze-project` | Full codebase analysis |
| `/popkit:setup-precommit` | Configure pre-commit hooks |

### Knowledge & Observability
| Command | Description |
|---------|-------------|
| `/popkit:knowledge` | Manage external knowledge sources with caching |
| `/popkit:knowledge add <url>` | Add new knowledge source |
| `/popkit:knowledge refresh` | Force refresh cached knowledge |
| `/popkit:chain-viz` | Visualize workflow chains with metrics |
| `/popkit:sync` | Validate and synchronize plugin state |
| `/popkit:next` | Context-aware action recommendations |
| `/popkit:morning` | Morning health check with "Ready to Code" score |
| `/popkit:generate-morning` | Create project-specific morning command |

### Power Mode
| Command | Description |
|---------|-------------|
| `/popkit:power-init` | Set up Redis for multi-agent orchestration |
| `/popkit:power-init start/stop` | Start or stop Redis container |
| `/popkit:power-mode "objective"` | Activate Power Mode with parallel agents |
| `/popkit:power-mode status` | Check orchestration status |

### Meta
| Command | Description |
|---------|-------------|
| `/popkit:popkit-release` | Release new version of popkit itself |
| `/popkit:plugin-test` | Run plugin self-tests |
| `/popkit:routing-debug` | Debug agent selection logic |
| `/popkit:auto-docs` | Generate and sync documentation |

## Agents

### Tier-1 (Always Active)
- `code-reviewer` - Code quality and best practices
- `bug-whisperer` - Complex debugging specialist
- `security-auditor` - Vulnerability assessment
- `test-writer-fixer` - Test implementation and fixes
- `api-designer` - API design patterns
- `performance-optimizer` - Performance analysis
- `refactoring-expert` - Code restructuring
- `documentation-maintainer` - Doc synchronization
- `query-optimizer` - Database query optimization
- `migration-specialist` - System migrations
- `accessibility-guardian` - A11y compliance

### Tier-2 (On-Demand)
- `ai-engineer` - ML/AI integration
- `deployment-validator` - Deployment verification
- `feature-prioritizer` - Backlog management
- `rapid-prototyper` - Quick MVP creation
- `backup-coordinator` - Backup strategies
- `meta-agent` - Agent configuration
- `researcher-agent` - Codebase research
- `user-story-writer` - Requirements documentation
- `devops-automator` - CI/CD automation
- `bundle-analyzer` - Bundle optimization
- `log-analyzer` - Log analysis
- And more...

### Feature Workflow (from Anthropic)
- `code-explorer` - Trace execution paths and data flow
- `code-architect` - Design blueprints and implementation maps
- `code-reviewer` - Confidence-based issue filtering (80+ threshold)

## Skills

### Core Development
- `popkit:brainstorming` - Design refinement through Socratic questioning
- `popkit:systematic-debugging` - 4-phase debugging framework
- `popkit:writing-plans` - Detailed implementation planning
- `popkit:executing-plans` - Plan execution with review checkpoints
- `popkit:test-driven-development` - Test-driven development workflow
- `popkit:verification-before-completion` - Pre-completion verification
- `popkit:root-cause-tracing` - Bug backward tracing
- `popkit:code-review` - Quality review with confidence scoring
- `popkit:simplification-cascades` - Complexity reduction

### Session Management
- `popkit:session-capture` - Save session state to STATUS.json
- `popkit:session-resume` - Restore context on startup
- `popkit:context-restore` - Load previous session context

### Power Mode
- `popkit:power-mode` - Multi-agent orchestration activation
- `popkit:power-init` - Redis setup and management (in command)

### Knowledge & Chains
- `popkit:knowledge-lookup` - Query cached external knowledge sources
- `popkit:chain-management` - Workflow chain validation and metrics
- `popkit:next-action` - Context-aware recommendation engine
- `popkit:validation-engine` - Reusable validation patterns

### Generators
- `popkit:project-init` - Scaffold new projects
- `popkit:mcp-generator` - Generate project-specific MCP servers
- `popkit:skill-generator` - Generate project-specific skills

### Analysis
- `popkit:analyze-project` - Full codebase analysis
- `popkit:setup-precommit` - Configure pre-commit hooks

### Design & Quality
- `frontend-design` - UI/UX with bold typography, color, motion
- `hookify` - Pattern-based hook creation
- `confidence-filtering` - Code review scoring (80+ threshold)

## Output Styles

Templates for consistent formatting:

### Git/GitHub
- `commit-message` - Conventional commits with attribution
- `pull-request` - PR template with summary, changes, test plan
- `github-issue` - AI-executable issue format
- `release-notes` - Changelog with highlights and breaking changes

### Development
- `code-review` - Structured review with confidence levels
- `implementation-plan` - Task-based planning format
- `design-document` - Architecture documentation
- `changelog` - Version history format

### Session
- `morning-report` - Daily status summary
- `nightly-summary` - End-of-day review
- `handoff-notes` - Context transfer format

## Architecture

This plugin implements a **two-tier architecture**:

### Tier 1: Universal Plugin (this repo)
- General-purpose skills, agents, hooks
- Works on ANY project
- Publishable to GitHub + Claude Marketplace

### Tier 2: Project-Specific (generated)
- Custom MCP server with semantic search
- Project-specific skills based on codebase
- Custom agents with auto-trigger rules

Generate Tier 2 tooling with:
```bash
/popkit:generate-mcp       # Creates .claude/mcp-servers/[project]-dev/
/popkit:generate-skills    # Creates .claude/skills/[project]-*
```

## Quality Gates

Automatic code integrity validation after file modifications.

### Triggers

Quality gates run when:
- **High-risk actions**: Config file changes, deletions, import/export changes
- **Batch threshold**: After 5 file edits
- **Rapid changes**: 3+ different files modified quickly

### Validation

Auto-detected based on project files:
| Project Type | Gate | Command |
|--------------|------|---------|
| TypeScript | `tsc --noEmit` | Detects `tsconfig.json` |
| Build | `npm run build` | Detects `package.json` with build script |
| Lint | `npm run lint` | Detects `package.json` with lint script |

### Failure Handling

When validation fails, you get options:
1. **Fix now** (default) - Errors injected into context
2. **Rollback** - Restore clean state, save patch for recovery
3. **Continue** - Proceed despite errors (not recommended)
4. **Pause** - Stop for manual review

### Configuration

Override auto-detection with `.claude/quality-gates.json`:

```json
{
  "gates": [
    {"name": "typescript", "enabled": true},
    {"name": "lint", "enabled": false},
    {"name": "custom", "command": "./scripts/validate.sh", "enabled": true}
  ],
  "triggers": {"batch_threshold": 10}
}
```

## Power Mode

Multi-agent orchestration for complex tasks requiring parallel collaboration.

### Two Backend Options

| Mode | Requirements | Agents | Use Case |
|------|--------------|--------|----------|
| **Redis** | Docker | 6+ | Production, full orchestration |
| **File-Based** | None | 2-3 | Development, learning, CI/CD |

### Quick Start

```bash
# Option 1: File-based (no setup, auto-activates)
/popkit:power-mode "Build user authentication"

# Option 2: Redis (full power)
/popkit:power-init start
/popkit:power-mode "Build user authentication"
```

### Features

- Periodic check-ins (push state, pull insights)
- Sync barriers between phases
- Guardrails prevent unconventional approaches
- Coordinator manages agent mesh network
- Human escalation for sensitive operations

See `power-mode/` directory for full documentation.

## Alignment with Anthropic Best Practices

| Best Practice | Implementation |
|--------------|----------------|
| Tool Search Tool | MCP template with semantic embeddings |
| defer_loading | Non-critical tools marked for deferred load |
| Progress Documentation | STATUS.json pattern |
| Feature Tracking | TodoWrite integration |
| Session Startup Protocol | session-resume skill |

## License

MIT

## Author

Joseph Cannon (joseph.cannon@outlook.com)
