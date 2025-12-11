# PopKit Commands Reference

Complete reference for all `/popkit:` slash commands.

## Quick Reference

| Command | Description |
|---------|-------------|
| `/popkit:next` | Context-aware recommendations |
| `/popkit:dev` | Development workflows (7-phase, issue-driven) |
| `/popkit:git` | Git operations, PRs, reviews, releases |
| `/popkit:power` | Multi-agent orchestration |
| `/popkit:issue` | GitHub issue management |
| `/popkit:routine` | Morning/nightly health checks |
| `/popkit:project` | Project analysis and setup |
| `/popkit:assess` | Multi-perspective self-assessment |
| `/popkit:worktree` | Git worktree management |
| `/popkit:milestone` | Milestone management |
| `/popkit:plugin` | Plugin testing and validation |
| `/popkit:upgrade` | Upgrade to premium features |

---

## /popkit:next

Analyzes current project state and recommends specific PopKit commands based on what needs attention.

```bash
/popkit:next                # Full analysis with recommendations
/popkit:next quick          # Condensed output
/popkit:next verbose        # Include all context sources
```

**Checks:** Git status, TypeScript errors, lint issues, open GitHub issues, technical debt.

**Priority Scoring:**
1. TypeScript errors (blocks development)
2. Uncommitted changes (risk of lost work)
3. Ahead of remote (share work)
4. High priority issues
5. Technical debt

---

## /popkit:dev

Unified entry point for all development workflows.

### Modes

| Mode | Description |
|------|-------------|
| `full` | 7-phase guided workflow (default) |
| `work #N` | Issue-driven development |
| `brainstorm` | Idea refinement through dialogue |
| `plan` | Create implementation plan |
| `execute` | Execute existing plan |
| `quick` | Minimal ceremony implementation |
| `prd` | Generate PRD document |
| `suite` | Generate full documentation suite |

### Examples

```bash
/popkit:dev "user authentication"         # Full 7-phase workflow
/popkit:dev work #57                       # Work on issue
/popkit:dev work #57 -p                    # With Power Mode
/popkit:dev brainstorm "notifications"     # Refine ideas
/popkit:dev plan                           # Create plan
/popkit:dev execute --batch-size 5         # Execute plan
/popkit:dev quick "fix timezone bug"       # Quick fix
```

### The 7 Phases

1. **Discovery** - Understand what to build
2. **Exploration** - Analyze codebase (code-explorer agent)
3. **Questions** - Clarify requirements
4. **Architecture** - Design implementation (code-architect agent)
5. **Implementation** - Build the feature
6. **Review** - Verify quality (code-reviewer agent)
7. **Summary** - Complete and document

### Flags

| Flag | Description |
|------|-------------|
| `-T`, `--thinking` | Enable extended thinking |
| `-p`, `--power` | Force Power Mode |
| `-s`, `--solo` | Force sequential mode |
| `--from FILE` | Generate from existing document |

---

## /popkit:git

Comprehensive git operations with smart commits, PR management, code review, CI/CD runs, and releases.

### Subcommands

| Subcommand | Description |
|------------|-------------|
| `commit` | Smart commit with auto-generated message (default) |
| `push` | Push current branch to remote |
| `pr` | Pull request management |
| `review` | Code review with confidence filtering |
| `ci` | GitHub Actions workflow runs |
| `release` | GitHub releases with auto-changelog |
| `publish` | Publish plugin to public repo |
| `prune` | Remove stale local branches |
| `finish` | Complete development with options |

### Examples

```bash
/popkit:git                               # Smart commit
/popkit:git commit "fixed the auth bug"   # Commit with hint
/popkit:git pr                            # Create PR
/popkit:git pr create --draft             # Draft PR
/popkit:git pr merge 67 --squash          # Squash merge
/popkit:git review --pr 67                # Review PR changes
/popkit:git ci list --status failure      # Failed CI runs
/popkit:git release create v1.2.0         # Create release
/popkit:git prune --dry-run               # Preview branch cleanup
```

### Code Review

Reviews use confidence-based filtering (80+ threshold):
- 90-100: Critical (must fix)
- 80-89: Important (should fix)
- 50-79: Noted but not reported
- 0-49: Ignored (likely false positive)

---

## /popkit:power

Manage multi-agent orchestration for complex tasks.

### Architecture

Uses Claude Code's native background agents (2.0.64+) for true parallel collaboration.

### Tier Comparison

| Feature | Free | Premium ($9/mo) | Pro ($29/mo) |
|---------|------|-----------------|--------------|
| Mode | File-based | Native Async | Native Async |
| Max Agents | 2 | 5 | 10 |
| Parallel Execution | Sequential | True parallel | True parallel |

### Subcommands

| Subcommand | Description |
|------------|-------------|
| `status` | Check current Power Mode status (default) |
| `start` | Start Power Mode with objective |
| `stop` | Stop Power Mode gracefully |
| `init` | Initialize infrastructure |
| `metrics` | View quantifiable value metrics |
| `widgets` | Manage status line widgets |
| `consensus` | Multi-agent decision-making |

### Examples

```bash
/popkit:power                             # Check status
/popkit:power start "Build auth system"   # Start with objective
/popkit:power stop                        # Stop gracefully
/popkit:power metrics --compare           # View metrics
```

---

## /popkit:issue

Manage GitHub issues with AI-optimized formatting.

### Subcommands

| Subcommand | Description |
|------------|-------------|
| `list` | List repository issues (default) |
| `view` | View issue details |
| `create` | Create new issue with template |
| `close` | Close an issue |
| `comment` | Add comment to issue |
| `edit` | Update issue metadata |
| `link` | Link issue to PR |

### Examples

```bash
/popkit:issue                             # List open issues
/popkit:issue list --power                # Issues recommending Power Mode
/popkit:issue view 45                     # View details
/popkit:issue create "Add feature"        # Create with template
/popkit:issue close 45 --reason completed # Close issue
```

### Templates

- `feature` - New features, enhancements
- `bug` - Bug reports, fixes
- `architecture` - Major changes, epics
- `research` - Spikes, investigations

---

## /popkit:routine

Day-bracketing workflow with morning health checks and nightly maintenance.

### Morning Routine

```bash
/popkit:routine morning           # Full health check
/popkit:routine morning quick     # One-line summary
/popkit:routine morning --full    # Include tests + security
```

**Ready to Code Score (0-100):**
- Clean working directory: 25 points
- Up to date with remote: 15 points
- TypeScript clean: 20 points
- Lint clean: 15 points
- Tests passing: 25 points

### Nightly Routine

```bash
/popkit:routine nightly           # Full cleanup report
/popkit:routine nightly cleanup   # Clean caches and artifacts
/popkit:routine nightly backup    # Save session state
```

**Sleep Score (0-100):**
- No uncommitted changes: 30 points (critical)
- Session state saved: 20 points
- Git maintenance done: 15 points
- Security audit clean: 15 points
- Caches under limit: 10 points
- Logs rotated: 10 points

---

## /popkit:project

Complete project lifecycle tools.

### Subcommands

| Subcommand | Description |
|------------|-------------|
| `init` | Initialize .claude/ structure |
| `analyze` | Deep codebase analysis (default) |
| `board` | GitHub Projects board view |
| `embed` | Embed items for semantic search |
| `generate` | Full pipeline (analyze + skills + mcp + embed) |
| `mcp` | Generate project-specific MCP server |
| `setup` | Configure pre-commit hooks |
| `skills` | Generate custom skills |
| `observe` | Cross-project dashboard |

### Examples

```bash
/popkit:project                   # Analyze project
/popkit:project init              # Initialize structure
/popkit:project init --power      # With Power Mode setup
/popkit:project mcp               # Generate MCP server
/popkit:project setup --level strict --ci
/popkit:project generate          # Full pipeline
```

---

## /popkit:assess

Run specialized assessor agents to review PopKit from different expert perspectives.

### Assessors

| Assessor | Focus |
|----------|-------|
| `anthropic` | Claude Code compliance, hook protocols |
| `security` | Vulnerabilities, secrets, injection |
| `performance` | Token efficiency, context usage |
| `ux` | Command naming, discoverability |
| `architect` | Code quality, DRY, patterns |
| `docs` | CLAUDE.md, SKILL.md, AGENT.md |
| `all` | Complete assessment |

### Examples

```bash
/popkit:assess all                # Run all assessments
/popkit:assess security           # Security audit only
/popkit:assess docs --fix         # Auto-fix documentation issues
```

---

## /popkit:worktree

Git worktree management for isolated development.

```bash
/popkit:worktree create feature-x   # Create worktree
/popkit:worktree list               # List worktrees
/popkit:worktree remove feature-x   # Remove worktree
```

---

## /popkit:milestone

Milestone management for release planning.

```bash
/popkit:milestone list              # List milestones
/popkit:milestone create 0.3.0      # Create milestone
/popkit:milestone close 0.2.0       # Close milestone
/popkit:milestone report            # Generate report
```

---

## /popkit:plugin

Plugin testing and validation.

```bash
/popkit:plugin test                 # Run all plugin tests
/popkit:plugin test hooks           # Test hook JSON protocol
/popkit:plugin test routing         # Verify agent selection
```

---

## Extended Thinking Support

Many commands support extended thinking for deeper analysis:

| Flag | Description |
|------|-------------|
| `-T`, `--thinking` | Enable extended thinking |
| `--no-thinking` | Disable extended thinking |
| `--think-budget N` | Set token budget (default: 10000) |

**Default behavior by model:**
- Sonnet: Enabled by default (10k tokens)
- Opus: Disabled by default, use `-T` to enable
- Haiku: Enabled by default (5k tokens)

---

## See Also

- [[Home]] - Getting started
- [[Agents]] - Available agents
- [[Contributing]] - How to contribute
