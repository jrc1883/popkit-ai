---
title: Commands Reference
description: Complete reference for all PopKit commands
---

# Commands Reference

PopKit provides 25 slash commands across 4 plugins for managing development workflows.

These `/popkit-*` commands are the recommended entry points. For direct primitive invocation, see [Skills Reference](/reference/skills/) (`/pop-*` layer).

## popkit-core

Core foundation commands for project management and orchestration.

### /popkit-core:power

**Description:** Multi-agent orchestration control

**Subcommands:**

- `start` - Start Power Mode (Redis or Native Async)
- `stop` - Stop Power Mode and cleanup
- `status` - Check Power Mode state
- `init` - Initialize Redis configuration
- `metrics` - View orchestration metrics
- `widgets` - Generate dashboard widgets
- `consensus` - Run consensus voting

**Options:** `--consensus`, `--agents N`

**Example:**

```bash
/popkit-core:power start
/popkit-core:power status
```

---

### /popkit-core:project

**Description:** Project initialization and analysis

**Subcommands:**

- `init` - Initialize PopKit in project
- `analyze` - Analyze project structure
- `board` - View project kanban board
- `embed` - Generate project embeddings
- `generate` - Generate project documentation
- `mcp` - MCP server management
- `setup` - Configure project settings
- `skills` - List/manage project skills
- `observe` - Monitor project changes
- `reference` - Generate reference docs

**Options:** `--power`, `--json`

**Example:**

```bash
/popkit-core:project init
/popkit-core:project analyze --json
```

---

### /popkit-core:plugin

**Description:** Plugin development and testing

**Subcommands:**

- `test` - Run plugin validation tests
- `docs` - Generate plugin documentation
- `sync` - Sync plugin metadata
- `detect` - Detect plugin issues
- `version` - Update plugin versions

**Options:** `--verbose`, `--json`

**Example:**

```bash
/popkit-core:plugin test agents
/popkit-core:plugin docs --verbose
```

---

### /popkit-core:account

**Description:** PopKit Cloud account management

**Subcommands:**

- `status` - Check account status
- `signup` - Create new account
- `login` - Authenticate
- `keys` - Manage API keys
- `usage` - View usage stats
- `logout` - Sign out

**Example:**

```bash
/popkit-core:account status
/popkit-core:account usage
```

---

### /popkit-core:stats

**Description:** Development efficiency metrics

**Subcommands:**

- `session` - Current session stats
- `today` - Today's metrics
- `week` - Weekly summary
- `cloud` - Cloud sync status
- `reset` - Reset statistics

**Example:**

```bash
/popkit-core:stats today
/popkit-core:stats week
```

---

### /popkit-core:dashboard

**Description:** Multi-project management

**Subcommands:**

- `add` - Register project
- `remove` - Unregister project
- `refresh` - Update project data
- `discover` - Find projects

**Example:**

```bash
/popkit-core:dashboard add
/popkit-core:dashboard refresh
```

---

### /popkit-core:bug

**Description:** Bug reporting and tracking

**Subcommands:**

- `report` - Report bug to GitHub
- `search` - Search existing bugs
- `share` - Share bug pattern

**Options:** `--issue`, `--share`

**Example:**

```bash
/popkit-core:bug report
/popkit-core:bug search "login error"
```

---

### /popkit-core:privacy

**Description:** Privacy settings management

**Subcommands:**

- `status` - View privacy settings
- `consent` - Manage consent
- `settings` - Update privacy and telemetry settings
- `export` - Export data
- `delete` - Delete data

**Settings options:** `level <strict|moderate|minimal>`, `telemetry <off|anonymous|community>`

**Example:**

```bash
/popkit-core:privacy status
/popkit-core:privacy settings level strict
/popkit-core:privacy settings telemetry anonymous
```

---

### /popkit-core:record

**Description:** Session recording control

**Subcommands:**

- `start` - Begin recording
- `stop` - End recording
- `status` - Check recording state

**Example:**

```bash
/popkit-core:record start
/popkit-core:record status
```

---

## popkit-dev

Development workflow commands for git, issues, and routines.

### /popkit-dev:git

**Description:** Git workflow management with smart commits, PRs, and releases

**Subcommands:**

- `commit` - Smart commit with auto-generated message (default)
- `push` - Push with branch protection checks
- `pr` - Pull request management
- `review` - Code review with confidence filtering or outside-voice advisory review
- `ci` - GitHub Actions workflow monitoring
- `release` - Release management with changelogs
- `publish` - Publish to public repo
- `prune` - Remove stale branches
- `finish` - Complete development flow
- `analyze-strategy` - Analyze branching strategy

**Options:** `--draft`, `--squash`, `--force-with-lease`, `--amend`, `--outside-voice`, `--target-provider`, `--publish`

**Example:**

```bash
/popkit-dev:git commit
/popkit-dev:git pr create --draft
/popkit-dev:git pr ready
/popkit-dev:git review --staged
/popkit-dev:git review --outside-voice --pr 123 --publish comment
/popkit-dev:git analyze-strategy
```

When using `pr ready`, PopKit now treats outside-voice review as the recommended advisory checkpoint:

- check current-head status first
- run the opposite-model review if missing
- or record an explicit skip before continuing

Executable helper:

```bash
python packages/popkit-ops/skills/pop-cross-model-review/scripts/pr_ready.py --pr 123
python packages/popkit-ops/skills/pop-cross-model-review/scripts/pr_ready.py --pr 123 --run-review-if-missing --publish comment
python packages/popkit-ops/skills/pop-cross-model-review/scripts/pr_ready.py --pr 123 --skip-outside-voice
```

---

### /popkit-dev:dev

**Description:** 7-phase feature development workflow

**Usage:** `/popkit-dev:dev "feature description"`

**Phases:**

1. Discovery - Understand requirements
2. Exploration - Explore codebase
3. Questions - Clarify ambiguities
4. Architecture - Design solution
5. Implementation - Build feature
6. Review - Code review
7. Summary - Document completion

**Options:** `--mode quick|full`, `-T`, `--power`

**Example:**

```bash
/popkit-dev:dev "Add dark mode toggle"
/popkit-dev:dev "OAuth2 authentication" --power
```

---

### /popkit-dev:next

**Description:** Context-aware next action recommendations

**Features:**

- Analyzes project state (git, tests, deps, docs)
- Scores recommendations by priority
- Detects branch protection issues
- Provides actionable commands

**Options:** `quick|verbose`

**Example:**

```bash
/popkit-dev:next
/popkit-dev:next verbose
```

---

### /popkit-dev:routine

**Description:** Morning and nightly development routines

**Subcommands:**

- `morning` - Day start health check
- `nightly` - End-of-day cleanup

**Options:** `run|quick|generate|list|set|edit|delete`

**Morning Routine:**

- Git status check
- Dependency updates
- Test verification
- Environment validation
- "Ready to Code" score

**Nightly Routine:**

- Uncommitted changes check
- Test status
- Branch cleanup
- Tomorrow's preparation
- "Sleep Score"

**Example:**

```bash
/popkit-dev:routine morning
/popkit-dev:routine nightly quick
```

---

### /popkit-dev:issue

**Description:** GitHub issue management

**Subcommands:**

- `create` - Create issue
- `list` - List issues
- `view` - View issue details
- `close` - Close issue
- `comment` - Add comment
- `edit` - Edit issue
- `link` - Link to PR/commit

**Options:** `--state`, `--label`

**Example:**

```bash
/popkit-dev:issue list --label bug
/popkit-dev:issue create
/popkit-dev:issue view 123
```

---

### /popkit-dev:milestone

**Description:** Milestone tracking and health reports

**Subcommands:**

- `list` - List milestones
- `create` - Create milestone
- `close` - Close milestone
- `report` - Generate status report
- `health` - Check milestone health

**Options:** `--json`, `--verbose`

**Example:**

```bash
/popkit-dev:milestone list
/popkit-dev:milestone health v1.0.0
```

---

### /popkit-dev:worktree

**Description:** Worktree batch operations and health analysis

PopKit enhances git worktree workflows with batch operations and intelligent recommendations.

**Subcommands:**

- `list` - List all worktrees with status (uncommitted changes, commits behind)
- `update-all` - Pull latest changes in all worktrees simultaneously
- `analyze` - Health analysis with cleanup recommendations
- `init` - Auto-create worktrees from branch patterns
- `prune` - Remove stale worktree references

**Options:** `--install` (run npm install after update), `--dry-run`, `--force`

**Example:**

```bash
# See all worktrees and their status
/popkit-dev:worktree list

# Update all worktrees at once
/popkit-dev:worktree update-all --install

# Get health recommendations
/popkit-dev:worktree analyze

# Auto-create worktrees for dev branches
/popkit-dev:worktree init --pattern "dev-*"
```

---

## popkit-ops

Operations and quality commands for testing, debugging, and deployment.

### /popkit-ops:assess

**Description:** AI-powered code quality assessments

**Subcommands:**

- `anthropic` - Anthropic best practices
- `security` - Security vulnerabilities
- `performance` - Performance bottlenecks
- `ux` - UX/accessibility issues
- `architect` - Architecture quality
- `docs` - Documentation completeness
- `all` - Run all assessments

**Options:** `--fix`, `--json`

**Example:**

```bash
/popkit-ops:assess security
/popkit-ops:assess all --fix
```

---

### /popkit-ops:audit

**Description:** Project health audits

**Subcommands:**

- `quarterly` - Quarterly review
- `yearly` - Yearly review
- `stale` - Find stale code
- `duplicates` - Detect duplication
- `health` - Overall health score
- `ip-leak` - Scan for IP leaks

**Options:** `--verbose`, `--fix`

**Example:**

```bash
/popkit-ops:audit health
/popkit-ops:audit ip-leak --verbose
```

---

### /popkit-ops:debug

**Description:** Debugging assistance

**Subcommands:**

- `code` - Debug code issues
- `routing` - Debug agent routing

**Options:** `--trace`, `--verbose`

**Example:**

```bash
/popkit-ops:debug code src/auth.js
/popkit-ops:debug routing --trace
```

---

### /popkit-ops:deploy

**Description:** Deployment management

**Subcommands:**

- `init` - Initialize deployment
- `setup` - Configure deployment
- `validate` - Validate deployment config
- `execute` - Run deployment
- `rollback` - Rollback deployment

**Options:** `--target`, `--all`, `--dry-run`

**Example:**

```bash
/popkit-ops:deploy validate
/popkit-ops:deploy execute --target production
/popkit-ops:deploy rollback
```

---

### /popkit-ops:security

**Description:** Security scanning and fixes

**Subcommands:**

- `scan` - Scan for vulnerabilities
- `list` - List findings
- `fix` - Auto-fix issues
- `report` - Generate security report

**Options:** `--dry-run`, `--severity`, `--fix`

**Example:**

```bash
/popkit-ops:security scan
/popkit-ops:security fix --severity high
```

---

### /popkit-ops:benchmark

**Description:** Performance benchmarking

**Subcommands:**

- `run` - Run benchmarks
- `compare` - Compare results
- `report` - Generate report

**Example:**

```bash
/popkit-ops:benchmark run
/popkit-ops:benchmark compare main feat/optimization
```

---

## popkit-research

Knowledge management commands for research and notes.

### /popkit-research:research

**Description:** Research capture and organization

**Subcommands:**

- `list` - List research items
- `search` - Search research
- `add` - Add research item
- `tag` - Tag research
- `show` - Show research details
- `delete` - Delete research
- `merge` - Merge research items

**Options:** `--type`, `--project`

**Example:**

```bash
/popkit-research:research add "API Design Patterns"
/popkit-research:research search "authentication"
/popkit-research:research tag research-123 --tag security
```

---

### /popkit-research:knowledge

**Description:** Knowledge base management

**Subcommands:**

- `list` - List knowledge items
- `add` - Add knowledge
- `remove` - Remove knowledge
- `sync` - Sync with storage
- `search` - Search knowledge base

**Usage:** `/popkit-research:knowledge search <query>`

**Example:**

```bash
/popkit-research:knowledge add docs/architecture.md
/popkit-research:knowledge search "JWT tokens"
/popkit-research:knowledge sync
```

---

## Command Conventions

### Argument Patterns

- `<required>` - Required argument
- `[optional]` - Optional argument
- `command|alternative` - Multiple options

### Common Options

- `--json` - Output in JSON format
- `--verbose` - Detailed output
- `--dry-run` - Preview without executing
- `--force` - Skip confirmations
- `--fix` - Auto-fix issues

### Output Formats

Commands use consistent output formatting:

- **Success:** Green checkmark with message
- **Warning:** Yellow warning icon with details
- **Error:** Red X with error description
- **Info:** Blue info icon with context

## Next Steps

- Learn about [Skills Reference](/reference/skills/)
- Explore [Agents Reference](/reference/agents/)
- Read [Command Usage Guide](/guides/commands/)
- View [XML Prompts Guide](/guides/xml-prompts/)
