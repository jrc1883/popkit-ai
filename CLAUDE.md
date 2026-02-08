# CLAUDE.md

This file provides guidance to Claude Code when working with the PopKit plugin repository.

---

## Overview

**PopKit** is an AI-powered development workflow system for Claude Code. This repository contains the public release of PopKit's modular plugin suite.

### Repository Structure

This repository is organized as a monorepo with multiple plugin packages:

```
popkit-claude/
├── packages/
│   ├── popkit-core/        # Foundation plugin (Power Mode, config, project tools)
│   ├── popkit-dev/         # Development workflows (git, GitHub, routines)
│   ├── popkit-ops/         # Operations & quality (test, debug, deploy)
│   ├── popkit-research/    # Knowledge management (research, notes)
│   ├── shared-py/          # Shared Python utilities (70 modules)
│   └── docs/               # Documentation site (Astro + Starlight)
├── docs/                   # Technical guides and documentation
├── CLAUDE.md               # This file
├── README.md               # User-facing documentation
└── CHANGELOG.md            # Version history
```

---

## Installation

### From GitHub Marketplace (Recommended)

PopKit is published as a GitHub-based marketplace. Install it in two steps:

**Step 1: Add the marketplace (one-time setup)**

```bash
/plugin marketplace add jrc1883/popkit-claude
```

**Step 2: Install plugins**

```bash
# Install all plugins for full functionality
/plugin install popkit-core@popkit-claude
/plugin install popkit-dev@popkit-claude
/plugin install popkit-ops@popkit-claude
/plugin install popkit-research@popkit-claude
```

After installation, restart Claude Code and run `/popkit-dev:next` to get started.

### For Local Development (Git Clone)

If you've cloned this repository for development and want to test local changes:

```bash
# Navigate to the repository root
cd /path/to/popkit-claude

# Install plugins from local directories
/plugin install ./packages/popkit-core
/plugin install ./packages/popkit-dev
/plugin install ./packages/popkit-ops
/plugin install ./packages/popkit-research
```

Restart Claude Code after installing local plugins.

**Note:** Local installations take precedence over marketplace installations.

---

## Plugin Architecture

PopKit uses a modular plugin architecture with 4 focused plugins:

| Plugin              | Purpose                    | Key Features                                       |
| ------------------- | -------------------------- | -------------------------------------------------- |
| **popkit-core**     | Foundation & orchestration | Power Mode, project analysis, plugin management    |
| **popkit-dev**      | Development workflows      | Git operations, GitHub integration, daily routines |
| **popkit-ops**      | Operations & quality       | Testing, debugging, security, deployment           |
| **popkit-research** | Knowledge management       | Research capture, knowledge base                   |

### Plugin Components

Each plugin package contains:

- `.claude-plugin/plugin.json` - Plugin manifest and configuration
- `commands/*.md` - Slash commands (e.g., `/popkit-dev:git`)
- `skills/*/SKILL.md` - Reusable automation skills
- `agents/*/AGENT.md` - Specialized AI agents
- `hooks/hooks.json` - Hook configuration
- `hooks/*.py` - Python hook scripts (JSON stdin/stdout protocol)
- `power-mode/` - Multi-agent orchestration (core only)
- `tests/` - Plugin integrity tests

### Hook Standards

All hooks follow Claude Code portability standards:

- Use `${CLAUDE_PLUGIN_ROOT}` for plugin-relative paths
- Double-quoted paths for Windows compatibility
- Forward slashes for cross-platform support
- Python shebang: `#!/usr/bin/env python3`
- JSON stdin/stdout protocol for communication

Example hook command:

```json
{
  "type": "command",
  "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/session-start.py\"",
  "timeout": 10000
}
```

### Pre-Commit Hook (Issue #156)

PopKit Core includes an automatic **Ruff pre-commit hook** that validates Python code quality:

**Features:**

- Runs `ruff check --fix` and `ruff format` on staged Python files
- Auto-fixes formatting and linting issues transparently
- Re-stages files automatically after fixes
- Blocks commit only on unfixable errors
- Fails open if Ruff is not installed (with warning)
- Performance: <5s for typical commits

**Behavior:**

1. Detects staged Python files: `git diff --cached --name-only --diff-filter=ACM`
2. Runs Ruff validation with auto-fix enabled
3. Re-stages files if auto-fixes were applied
4. Exits 0 (allow commit) or 1 (block commit)

**Edge Cases:**

- No Python files staged → Skip hook immediately
- Ruff not installed → Fail open with warning message
- Auto-fixes applied → Re-stage files and allow commit
- Unfixable errors → Block commit with error details
- Hook errors → Fail open (never block on hook failures)

**Configuration:** See `packages/popkit-core/hooks/hooks.json` - timeout is 30s to handle large commits.

### New in Claude Code 2.1.0

**Skill Hot-Reload:**

- Skills automatically reload when modified
- No session restart required
- Test changes instantly with `/skill invoke <name>`
- Ideal for rapid skill development and iteration

**Forked Skill Contexts:**

- Skills can declare `context: fork` in frontmatter
- Runs in isolated context (reduces token overhead)
- Ideal for expensive operations: embeddings, web research, one-time scans
- Example skills: `pop-research-capture`, `pop-embed-content`, `pop-assessment-*`

**YAML List Format:**

- Agent `tools` field now supports clean YAML list syntax
- Old format still supported (backwards compatible)
- Example:
  ```yaml
  tools:
    - Read
    - Grep
    - Glob
  ```

**Wildcard Tool Permissions:**

- Fine-grained Bash command control using `*` wildcards
- Security model: explicit allow, block by omission
- Example:
  ```yaml
  tools:
    - Read
    - Write
    # Testing frameworks - safe, test-specific commands
    - Bash(npm test)
    - Bash(npm run test*)
    - Bash(pytest *)
    # Security scanning - read-only audit commands
    - Bash(npm audit*)
    - Bash(snyk test*)
    # Git operations - safe, read-only inspection
    - Bash(git status)
    - Bash(git diff*)
    - Bash(git log*)
  ```
- **Wildcard Syntax:**
  - `Bash(command)` - Exact match only
  - `Bash(command *)` - Command with any arguments
  - `Bash(command subcommand*)` - Subcommand with any arguments
- **Security Principle:** Be conservative. Only list allowed patterns; everything else is blocked.
- **Blocked by Omission:** Commands not listed are automatically blocked (e.g., `git push --force`, `rm -rf`, `sudo`)
- See [Wildcard Permission Design](docs/research/2026-01-08-wildcard-permission-design.md) for detailed patterns and examples

### New in Claude Code 2.1.2

**SessionStart Hook agent_type:**

- When users run `claude --agent <agent-name>`, the `agent_type` field is now included in SessionStart hook input
- PopKit detects this and optimizes session initialization:
  - Skips embedding-based agent filtering (user already selected the agent)
  - Applies category-specific optimizations (Tier 1, Tier 2, Feature Workflow)
  - Improves logging and analytics for agent-specific sessions
- Example: `claude --agent code-reviewer` triggers optimized code review session

**Plugin Auto-Update Control:**

- New `FORCE_AUTOUPDATE_PLUGINS` environment variable
- When set to `true`, plugins auto-update even if main Claude Code auto-updater is disabled
- Useful for teams wanting stable Claude Code versions but latest plugin features:
  ```bash
  export FORCE_AUTOUPDATE_PLUGINS=true
  ```

**Large Output Persistence:**

- Large tool outputs are now saved to disk instead of truncated
- Enables PopKit hooks and agents to process complete outputs
- No code changes required - automatic improvement for all workflows

**Permission Explainer Improvements:**

- Routine dev workflows (git fetch, rebase, npm install, tests) no longer flagged as medium risk
- Validates PopKit's wildcard permission approach (`Bash(npm test*)`, `Bash(git log*)`)
- Smoother UX for developers using PopKit's security-conscious agent permissions

### New in Claude Code 2.1.3

**Commands and Skills Merge:**

- Unified slash commands and skills into a single mental model
- No behavior changes - purely UX improvement
- Skills and commands remain separate in plugin structure
- More intuitive for users when invoking workflows

**Release Channel Control:**

- Added `/config` toggle for `stable` vs `latest` release channels
- Users can control update frequency independently

**Permission Rule Validation:**

- Detection and warnings for unreachable permission rules
- `/doctor` command shows rule conflicts with actionable fixes
- Improved security configuration UX

**Bug Fixes:**

- Plan files no longer persist across `/clear` commands
- Fixed skill duplicate detection on ExFAT filesystems
- Corrected sub-agent model selection during conversation compaction

### New in Claude Code 2.1.4

**Background Task Control:**

- New `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` environment variable
- Allows disabling all background task functionality when needed
- Useful for debugging or resource-constrained environments

### New in Claude Code 2.1.5

**Temp Directory Override:**

- New `CLAUDE_CODE_TMPDIR` environment variable
- Overrides default temp directory for internal files
- Useful for custom storage configurations or permissions issues

### New in Claude Code 2.1.6

**Settings Search:**

- `/config` command gained search functionality
- Quickly filter settings by keyword
- Improved navigation for large configuration files

**Updates Visibility:**

- `/doctor` now shows auto-update channel and available npm versions
- Better transparency about version management

**Stats Date Filtering:**

- `/stats` command added date range filtering
- Options: Last 7 days, Last 30 days, All time
- More granular usage analytics

**Nested Skills Discovery:**

- Automatic discovery of skills from nested `.claude/skills` directories
- Supports more flexible project organization

**Context Window Display:**

- Added percentage-based fields for context window usage
- Easier to understand token consumption at a glance

**Security Fixes:**

- Resolved permission bypass via shell line continuation
- Improved command validation and sanitization

**Bug Fixes:**

- Fixed text styling (bold, colors) getting progressively misaligned
- Removed ability to @-mention MCP servers (use `/mcp enable <name>` instead)

### New in Claude Code 2.1.7

**Wildcard Permission Security:**

- Fixed security vulnerability where wildcard permission rules could match compound commands containing shell operators
- `Bash(git log*)` no longer matches `git log && rm -rf /` - this is the correct, intended behavior
- Validates PopKit's wildcard permission design in AGENT.md files

**MCP Tool Search Auto Mode:**

- MCP tool search auto mode enabled by default for all users
- When MCP tool descriptions exceed 10% of context window, they are deferred and discovered via MCPSearch
- Users can disable by adding `MCPSearch` to `disallowedTools`
- Agents with MCP wildcard permissions (`mcp__server__*`) may find tools deferred; use MCPSearch to discover first

**Windows Fixes:**

- Fixed false "file modified" errors from cloud sync tools, antivirus, or Git touching timestamps
- Fixed bash commands failing when temp directory paths contained characters misinterpreted as escape sequences

### New in Claude Code 2.1.9

**PreToolUse `additionalContext` (Critical):**

- PreToolUse hooks can now return `additionalContext` to inject context directly into model reasoning
- PopKit's `pre-tool-use.py` can return safety warnings, agent suggestions, and coordination recommendations visible to the model
- Example: `{"decision": "approve", "additionalContext": "POPKIT: This file is in production path. Create backup first."}`
- This is the single most impactful hook protocol change for PopKit

**Skill Session ID:**

- Skills can access `${CLAUDE_SESSION_ID}` via string substitution
- Enables session-specific output paths and tracking in skill definitions

**Plans Directory:**

- `plansDirectory` setting customizes where plan files are stored
- PopKit should not hardcode plan file paths

**AskUserQuestion Editor:**

- External editor support (Ctrl+G) in AskUserQuestion "Other" input field
- Useful for detailed responses in The PopKit Way interaction pattern

### New in Claude Code 2.1.10

**Setup Hook Event (Critical):**

- New `Setup` hook event triggered via `--init`, `--init-only`, or `--maintenance` CLI flags
- `claude --init` can trigger PopKit's `pop-project-init` workflow
- `claude --maintenance` can trigger PopKit health checks and cleanup routines
- `--init-only` is perfect for CI/CD pipelines needing setup without an interactive session
- PopKit should add a `Setup` hook entry in `hooks.json`

### New in Claude Code 2.1.14

**Plugin SHA Pinning:**

- Plugins can be pinned to specific git commit SHAs
- Marketplace entries can install exact versions: `/plugin install popkit-core@popkit-claude#<sha>`
- Teams can pin to known-good PopKit versions while testing updates
- CI/CD pipelines benefit from deterministic plugin installations

**Stability Fixes:**

- Fixed context window blocking at ~65% instead of intended ~98% (regression fix)
- Fixed memory crashes when running parallel subagents (Power Mode reliability)
- Fixed memory leak in long-running sessions from uncleaned stream resources

### New in Claude Code 2.1.16

**Native Task Management:**

- New task management system with dependency tracking
- PopKit's Power Mode could leverage native dependency tracking for subagent coordination
- Skills generating TODOs should consider native tasks
- `CLAUDE_CODE_ENABLE_TASKS=false` temporarily reverts to old system (2.1.19)

### New in Claude Code 2.1.19

**Command Argument Syntax:**

- Shorthand `$0`, `$1` for accessing individual arguments in custom commands
- Bracket syntax `$ARGUMENTS[0]` replaces dot syntax `$ARGUMENTS.0`
- Audit PopKit commands for old dot syntax

**Skill Auto-Approval:**

- Skills without additional permissions or hooks are allowed without user approval
- Many PopKit informational/orchestration skills now execute without prompts

**Background Hook Fix:**

- Backgrounded hook commands with `"blocking": false` now correctly return early
- Enables more PopKit hooks to run non-blocking without session delays

### New in Claude Code 2.1.20

**PR Status Footer:**

- Native PR review status indicator in the prompt footer
- PopKit can reduce redundant PR status queries in workflows
- `--add-dir` flag and `CLAUDE_ADD_DIR` env var load CLAUDE.md from additional directories

**Background Agent Permissions:**

- Background agents now prompt for permissions before launch (not after)
- `Bash(*)` is equivalent to `Bash` (validates PopKit's wildcard permission approach)
- `TaskUpdate` gains `delete` capability for cleaner task cleanup

### New in Claude Code 2.1.21

**File Tool Preference:**

- Model now prefers Read/Edit/Write tools over bash equivalents (cat/sed/awk)
- Validates PopKit's agent permission model (agents don't need `Bash(cat *)`)
- VSCode auto-activates Python venv for hook execution

### New in Claude Code 2.1.27

**PR Workflow Improvements:**

- `--from-pr` flag links sessions to specific pull requests
- Auto PR linking via `gh pr create` for better traceability
- Tool denials now appear in debug logs (helps debug agent permissions)

**Windows Compatibility:**

- Fixed .bashrc compatibility for Windows environments
- Important for Windows PopKit hook execution reliability

### New in Claude Code 2.1.30

**PDF and Research:**

- `pages` parameter on Read tool for large PDFs (e.g., `pages: "1-5"`)
- PDFs >10 pages return `@` reference instead of inline content
- PopKit research workflows should use `pages` parameter for large documents

**Task Tool Metrics:**

- Task results now include token count, tool uses, and duration
- PopKit's `chain-metrics.py` can consume native metrics instead of computing manually
- New `/debug` command for session troubleshooting

### New in Claude Code 2.1.32

**Claude Opus 4.6:**

- New frontier model available for all agents
- Agents with `model: inherit` automatically use Opus 4.6 when user selects it
- May have different response patterns affecting structured output expectations

**Agent Teams (Research Preview):**

- Native multi-agent collaboration built into Claude Code
- Uses tmux-based inter-agent messaging (vs PopKit Power Mode's Redis pub/sub)
- Strategic consideration: PopKit Power Mode differentiates with phase management, drift detection, sync barriers, pattern learning
- Research preview - API may change before GA

**Agent Memory:**

- Automatic memory recording and recall during operations
- Overlaps with PopKit's `knowledge-sync.py` hook and `pop-knowledge-lookup` skill
- PopKit should focus on structured, domain-specific knowledge management

**Other Notable Changes:**

- `--resume` reuses previous `--agent` value (better agent session continuity)
- Skill character budget now scales at 2% of context window size
- "Summarize from here" for partial conversation summarization

### New in Claude Code 2.1.33

**New Hook Events:**

- `TeammateIdle`: Fires when a teammate agent becomes idle in multi-agent teams
  - PopKit can reassign idle agents, track utilization, trigger phase transitions
- `TaskCompleted`: Fires when a task completes
  - PopKit can track metrics, trigger dependent tasks, route completion insights

**`Task(agent_type)` Restriction Syntax:**

- Agents can restrict which sub-agent types they spawn: `Task(code-reviewer)`
- PopKit's `power-coordinator` can be restricted to known agent types only
- Enhances security and predictability of multi-agent workflows

**Agent `memory` Frontmatter Field:**

- Agents declare memory persistence scope in frontmatter:
  ```yaml
  memory: user      # Persists across all projects
  memory: project   # Persists within this project
  memory: local     # Persists within this directory
  ```
- All 22 PopKit agents should declare appropriate memory scopes
- Example: `researcher` → `memory: project`, `accessibility-guardian` → `memory: user`

**Skill Discoverability:**

- Plugin names now shown in skill descriptions and `/skills` menu
- PopKit skills appear with their plugin prefix (popkit-core, popkit-dev, etc.)

---

## Integration with Official Claude Plugins

PopKit is designed to complement and extend official Claude Code plugins through workflow orchestration. Rather than replacing official tools, PopKit integrates them into complete development workflows.

### Architecture Philosophy

**PopKit = Workflow Orchestration Layer**

- **Official Plugins**: Building blocks (agents, tools, capabilities)
- **PopKit**: Orchestration (workflows, coordination, automation)

PopKit uses official Claude agents (code-explorer, code-architect, code-reviewer) as foundational components within larger, context-aware workflows that span the entire development lifecycle.

### Code Review Integration

PopKit provides a two-tier code review strategy:

#### Local Pre-PR Review: `/popkit-dev:git review`

**Purpose**: Internal quality check before creating PR
**Usage**: During implementation phase
**Features**:

- Confidence-based filtering (80+ threshold)
- Reviews staged changes, branches, or specific files
- Focus areas: simplicity, correctness, conventions
- Output: Local terminal report for immediate fixes

**When to use**: Before creating PR to catch issues early

```bash
# Review current changes
/popkit-dev:git review --staged

# Review specific branch
/popkit-dev:git review --branch feat/user-auth

# Review with specific focus
/popkit-dev:git review --focus security
```

#### Automated PR Review: Official `code-review` Plugin

**Purpose**: Post-PR automated review with GitHub integration
**Usage**: After PR creation
**Features**:

- 4 parallel agents (2× CLAUDE.md compliance, bugs, git history)
- Native GitHub comment posting with code links
- Confidence threshold filtering (80+)
- Full SHA references for permanent links

**Integration Point**: Automatically invoked after PR creation in workflows

**Installation**:

```bash
claude plugin install code-review@claude-plugins-official
```

**Workflow Integration**:

The official code-review plugin is integrated into:

1. **`pop-finish-branch` skill**: After PR creation step

   ```
   create_pr → automated_pr_review → issue_close_decision
   ```

2. **`/popkit-dev:dev` workflow**: In Phase 7 (Summary)
   ```
   Phase 6: Quality Review (local)
   Phase 7: Summary → Create PR → Auto code-review
   ```

**Usage**: Automatically triggered, or manually via:

```bash
# Review current PR
/code-review

# Review specific PR with GitHub comments
/code-review --comment
```

### GitHub Integration Strategy

PopKit uses `gh` CLI with intelligent caching instead of MCP for GitHub operations.

**Technical Approach**:

| Aspect          | PopKit Implementation                            |
| --------------- | ------------------------------------------------ |
| **Method**      | `gh` CLI via subprocess + smart caching          |
| **Cache Layer** | Two-tier: Local JSON + optional Redis            |
| **TTL**         | 60min (labels/milestones), 24hr (team members)   |
| **Features**    | Fuzzy label matching, typo detection, validation |
| **Offline**     | ✅ Yes (cached data remains available)           |
| **Token Cost**  | 0 upfront (no tool descriptions in context)      |

**Why CLI over MCP**:

1. **Zero Setup**: `gh` CLI already installed for GitHub users
2. **Smart Caching**: Reduces API calls more effectively than MCP
3. **Offline Support**: Works with cached data when disconnected
4. **Token Efficiency**: No upfront context overhead
5. **Simplicity**: Direct command execution, no server required

**Cache Implementation** (Issue #96):

```python
from popkit_shared.utils.github_cache import GitHubCache

cache = GitHubCache()
labels = cache.get_labels()  # Fast, cached
valid, invalid, suggestions = validate_labels(requested_labels, cache)
```

**JSON Output**: PopKit uses `--json` flag by default for structured, type-safe responses:

```bash
gh pr list --json number,title,state,labels
gh issue view 123 --json body,assignees,milestone
gh run list --json status,conclusion,name
```

**Alternative**: GitHub MCP server available for teams preferring Model Context Protocol architecture. Install separately if needed for real-time API integration.

### When to Use Official Plugins vs PopKit

| Use Case                                | Recommendation                                                           |
| --------------------------------------- | ------------------------------------------------------------------------ |
| **Complete workflows**                  | PopKit (e.g., `/popkit-dev:dev`, `/popkit-dev:routine`)                  |
| **PR code review with GitHub comments** | Official code-review plugin                                              |
| **Feature development**                 | PopKit `/dev` (includes code-explorer/code-architect)                    |
| **GitHub operations**                   | PopKit CLI + cache (simpler, cached)                                     |
| **Frontend design**                     | Official `frontend-design` plugin, orchestrated via PopKit brainstorming |
| **Multi-agent coordination**            | PopKit Power Mode (complex) or Agent Teams (simple, 2.1.32+)             |
| **Morning/nightly routines**            | PopKit (unique capability)                                               |

### Complementary Official Plugins

These official plugins work well alongside PopKit:

- **frontend-design**: Production-grade UI design (orchestrated via PopKit brainstorming workflow)
- **code-review**: Automated PR reviews with GitHub integration
- **github** (MCP): Alternative to CLI approach (optional)
- **pubmed**: Life sciences research integration
- **playwright**: Browser automation and testing

PopKit includes code-simplifier (refactoring-expert) and workflow orchestration capabilities. For frontend design, use the official `frontend-design` plugin which PopKit can orchestrate through brainstorming and UX assessment workflows.

### Frontend Design Integration Strategy

PopKit does not include its own UI/design agents. Instead, it orchestrates official and community tools:

**Recommended Workflow for Frontend Tasks:**

1. **Ideation**: `pop-brainstorming` skill for design specification and decision exploration
2. **Implementation**: Official `frontend-design` plugin for production-grade UI code
3. **Validation**: `pop-assessment-ux` skill for UX heuristic evaluation
4. **Accessibility**: `accessibility-guardian` agent for WCAG compliance audits

**Official Plugin**: Install `frontend-design` from `claude-plugins-official` for:

- Distinctive typography, color palettes, and animations
- Context-aware design that avoids generic AI aesthetics
- Component architecture and design system creation

**Community Options**:

- `frontend-dev` plugin: AI vision-based visual testing (closed-loop test/fix/validate)
- Figma MCP connector: Design-to-code pipeline from Figma files

---

## Testing

### Plugin Validation

Run comprehensive plugin tests:

```bash
# Test all plugins
cd packages/popkit-core
python run_all_tests.py              # All plugins
python run_all_tests.py --verbose    # Detailed output

# Test individual plugin
cd packages/popkit-core
python run_tests.py                  # popkit-core only
python run_tests.py hooks            # Specific category
```

### Test Categories

- **agents**: Agent markdown validation and frontmatter
- **hooks**: Hook JSON protocol and execution
- **skills**: Skill format and structure
- **structure**: Plugin integrity and required files
- **cross-plugin**: Cross-plugin compatibility

### Via PopKit Commands

```bash
/popkit-core:plugin test              # Run all tests
/popkit-core:plugin test agents       # Test specific category
/popkit-core:plugin test --verbose    # Detailed output
```

---

## Contributing

### Development Workflow

1. **Clone the repository**

   ```bash
   git clone https://github.com/jrc1883/popkit-claude.git
   cd popkit-claude
   ```

2. **Make changes**
   - Edit plugin files in `packages/*/`
   - Follow existing patterns for commands, skills, agents
   - Update tests if adding new features

3. **Test your changes**

   ```bash
   cd packages/popkit-core
   python run_all_tests.py
   ```

4. **Install locally to test**

   ```bash
   /plugin install ./packages/popkit-core
   # Restart Claude Code
   ```

5. **Submit a pull request**
   - Create a feature branch
   - Commit with conventional commit format
   - Submit PR with clear description

### Conventional Commits

All commits use conventional commit format:

```
feat: Add new feature
fix: Bug fix
docs: Documentation updates
test: Test additions/updates
chore: Maintenance tasks
```

### Code Standards

- **Commands**: Markdown files with YAML frontmatter
- **Skills**: SKILL.md format with description, usage, examples
- **Agents**: AGENT.md with purpose, triggers, capabilities
- **Hooks**: Python scripts with JSON stdin/stdout, proper error handling
- **No build required**: Configuration-only plugin (no TypeScript/compilation)
- **Code Comments**: Follow [COMMENTING-STANDARD.md](docs/standards/COMMENTING-STANDARD.md) - comments explain _why_ not _what_. Target Level 2 (Moderate) for most Python modules. Always document magic numbers and design decisions.

---

## Version Requirements

PopKit requires specific Claude Code versions for full functionality:

| Feature                          | Minimum Version | Description                                     |
| -------------------------------- | --------------- | ----------------------------------------------- |
| **Extended Thinking**            | 2.0.67          | Default enabled (10k tokens)                    |
| **Native Async Mode**            | 2.0.64          | Background Task tool (5+ agents)                |
| **MCP Wildcard Permissions**     | 2.0.70          | `mcp__server__*` syntax for tool permissions    |
| **Plan Mode**                    | 2.0.70          | Agent approval workflow                         |
| **Configuration Management**     | 2.0.71          | `/config` toggle                                |
| **MCP Permissions**              | 2.0.71          | Fixed permissions for MCP servers               |
| **Skill Hot-Reload**             | 2.1.0           | Skills reload without restart                   |
| **Forked Skill Contexts**        | 2.1.0           | Isolated execution contexts                     |
| **YAML List Format**             | 2.1.0           | Clean agent tools syntax                        |
| **SessionStart agent_type**      | 2.1.2           | `--agent` flag detection in hooks               |
| **Plugin Auto-Update Control**   | 2.1.2           | `FORCE_AUTOUPDATE_PLUGINS` env var              |
| **Large Output Persistence**     | 2.1.2           | Tool outputs saved to disk (not truncated)      |
| **Unified Commands/Skills UX**   | 2.1.3           | Mental model simplification (no code changes)   |
| **Release Channel Toggle**       | 2.1.3           | `stable` vs `latest` in `/config`               |
| **Permission Rule Validation**   | 2.1.3           | Unreachable rule detection in `/doctor`         |
| **Background Task Disable**      | 2.1.4           | `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` env var  |
| **Temp Directory Override**      | 2.1.5           | `CLAUDE_CODE_TMPDIR` env var                    |
| **Settings Search**              | 2.1.6           | Keyword filtering in `/config`                  |
| **Nested Skills Discovery**      | 2.1.6           | Auto-detect `.claude/skills` subdirectories     |
| **Shell Continuation Security**  | 2.1.6           | Permission bypass fix                           |
| **Wildcard Permission Security** | 2.1.7           | Shell operator matching fix for compound cmds   |
| **MCP Auto Search Default**      | 2.1.7           | MCP tools deferred when >10% context window     |
| **PreToolUse additionalContext** | 2.1.9           | Hooks can inject context into model reasoning   |
| **Skill Session ID Access**      | 2.1.9           | `${CLAUDE_SESSION_ID}` substitution in skills   |
| **Plans Directory Config**       | 2.1.9           | `plansDirectory` setting for plan file location |
| **Setup Hook Event**             | 2.1.10          | `--init`, `--init-only`, `--maintenance` flags  |
| **Plugin SHA Pinning**           | 2.1.14          | Pin plugins to specific git commit SHAs         |
| **Native Task Management**       | 2.1.16          | Task system with dependency tracking            |
| **Customizable Keybindings**     | 2.1.18          | `/keybindings` for personalized shortcuts       |
| **Argument Bracket Syntax**      | 2.1.19          | `$ARGUMENTS[0]` replaces `$ARGUMENTS.0`         |
| **Auto-Approved Simple Skills**  | 2.1.19          | Skills without hooks/permissions skip approval  |
| **Background Hook Fix**          | 2.1.19          | Non-blocking hooks return early correctly       |
| **PR Status Footer**             | 2.1.20          | Native PR review status in prompt footer        |
| **Additional Dir CLAUDE.md**     | 2.1.20          | `--add-dir` loads CLAUDE.md from extra dirs     |
| **Bash(\*) = Bash Equivalence**  | 2.1.20          | Validates wildcard permission design            |
| **File Tool Preference**         | 2.1.21          | Model prefers Read/Edit/Write over bash equiv   |
| **Async Hook Cancellation**      | 2.1.23          | Pending hooks cancelled on session end          |
| **PR Session Linking**           | 2.1.27          | `--from-pr` flag and auto-linking via `gh pr`   |
| **Windows Bash Fix**             | 2.1.27          | .bashrc compatibility for Windows hooks         |
| **PDF Page Ranges**              | 2.1.30          | `pages` parameter on Read tool for PDFs         |
| **Task Tool Metrics**            | 2.1.30          | Token count, tool uses, duration in results     |
| **Debug Command**                | 2.1.30          | `/debug` for session troubleshooting            |
| **Claude Opus 4.6**              | 2.1.32          | New frontier model available                    |
| **Agent Teams (Preview)**        | 2.1.32          | Native multi-agent collaboration                |
| **Agent Memory**                 | 2.1.32          | Automatic memory recording and recall           |
| **Session Resume Agent Reuse**   | 2.1.32          | `--resume` reuses previous `--agent` value      |
| **Skill Budget Scaling**         | 2.1.32          | Skill character budget = 2% of context window   |
| **TeammateIdle Hook**            | 2.1.33          | New hook event for idle teammate agents         |
| **TaskCompleted Hook**           | 2.1.33          | New hook event for completed tasks              |
| **Task(agent_type) Syntax**      | 2.1.33          | Restrict sub-agent spawning in frontmatter      |
| **Agent Memory Frontmatter**     | 2.1.33          | `memory: user\|project\|local` in AGENT.md      |

**Recommended**: Claude Code 2.1.33+ for full feature support including Agent Teams, Agent Memory, and latest hook events.

---

## Current Status

**Version**: 1.0.0-beta.8
**Status**: Beta release
**Plugins**: 4 modular plugins
**Commands**: 25 workflow commands
**Skills**: 38 reusable skills
**Agents**: 23 specialized agents

### Recent Updates

- **2026-02-06**: TeammateIdle + TaskCompleted hooks, CC 2.1.7-2.1.33 full changelog audit, version table expanded (42 entries)
- **2026-02-06**: CC 2.1.33 integration, agent memory, interactive init, routing accuracy (v1.0.0-beta.8)
- **2026-02-05**: Issue triage and cleanup (17 issues closed), commenting standards, design integration strategy
- **2026-01-31**: GitHub cache, priority scheduling, agent expertise system (v1.0.0-beta.7)
- **2026-01-13**: CI/CD pipeline complete, all tests passing (v1.0.0-beta.5)
- **2026-01-12**: Claude Code 2.1.6 compatibility verified, hook import paths fixed (v1.0.0-rc.1)
- **2026-01-09**: Claude Code 2.1.2 integration complete (v1.0.0-beta.4)

See [CHANGELOG.md](CHANGELOG.md) for full version history.

---

## The PopKit Way

PopKit maintains workflow control through a consistent interaction pattern:

### Core Principle

**Never end a workflow without user interaction.** Every command, skill, and routine MUST end with `AskUserQuestion` to:

- Keep PopKit in control of the workflow loop
- Force intentional user decisions
- Enable context-aware next actions
- Prevent "report dump and done" anti-pattern
- Maintain continuous workflow engagement

### Implementation Pattern

All skills/commands must follow this pattern:

```python
# After completing the main task (report, analysis, etc.)
# Generate context-aware next action options
options = [
    {
        "label": "Primary action (Recommended)",
        "description": "What this action does"
    },
    {
        "label": "Alternative action",
        "description": "What this action does"
    },
    {
        "label": "Other",
        "description": "I have something else in mind"
    }
]

# Output AskUserQuestion instructions for Claude
output_ask_user_question_instructions(options)
```

### Examples

#### ✅ Correct (The PopKit Way)

```markdown
# ☀️ Morning Routine Report

[... report content ...]

## 🎯 Next Steps

Use AskUserQuestion with options:

- "Fix environment issues (Recommended)"
- "Continue: previous task"
- "Review open PRs"
- "Other"
```

#### ❌ Incorrect (Anti-Pattern)

```markdown
# ☀️ Morning Routine Report

[... report content ...]

Morning session initialized. Ready to code!
[session ends without user interaction]
```

### Required Components

1. **Context Analysis**: Examine workflow results to determine appropriate next actions
2. **Option Generation**: Create 2-4 context-aware options (always include "Other")
3. **Recommendation**: Mark the most appropriate option as "(Recommended)"
4. **Clear Instructions**: Tell Claude explicitly to use AskUserQuestion (not just suggest it)

### Skills Using This Pattern

✅ **Correctly Implemented:**

- `pop-brainstorming` - Ends with design decision options
- `issue` command - Ends with "Work on next issue" / "Review PRs" / etc.
- `milestone` command - Ends with next milestone actions
- `pop-morning` - Ends with context-aware next actions (v1.0.0-beta.4+)
- `pop-nightly` - Ends with shutdown options based on Sleep Score (v1.0.0-beta.4+)

🚧 **Needs Implementation:**

- Other skills TBD (audit needed)

### Quality Check

Before committing any skill/command:

- [ ] Does it end with AskUserQuestion?
- [ ] Are options context-aware (not generic)?
- [ ] Is there a "(Recommended)" option?
- [ ] Does it maintain workflow control?

**If any answer is "no", the implementation violates The PopKit Way.**

---

## Git Workflow Principles

PopKit enforces standard Git workflows with branch protection awareness.

### Core Principle: Feature Branch Workflow

**Never commit directly to protected branches.** All work must go through feature branches and pull requests.

### Protected Branches

The following branches are **protected** and require feature branch workflow:

- `main` - Primary integration branch
- `master` - Legacy primary branch
- `develop` - Development integration branch
- `production` - Production release branch

### Branch Protection Detection

As of issue #141, PopKit skills detect when working on protected branches and recommend proper workflow:

**Detection**: Skills check `git branch --show-current` during project state analysis

**Recommendation**: When on protected branch with unpushed commits:

1. **Priority**: CRITICAL (score 100, highest)
2. **Command**: `git checkout -b feat/descriptive-name`
3. **Workflow**:

   ```bash
   # Create and push feature branch
   git checkout -b feat/your-feature-name
   git push -u origin feat/your-feature-name

   # Create pull request
   gh pr create --title "..." --body "..."

   # Clean up local main
   git checkout main
   git reset --hard origin/main
   ```

### Affected Components

The following components enforce branch protection:

✅ **Implemented (v1.0.0-beta.6+)**:

- `pop-next-action` skill - Detects protected branches, suppresses direct push recommendations
- Adds "Current Branch" indicator to recommendation output
- Shows ⚠️ CRITICAL urgency when on protected branch

🚧 **To Be Audited**:

- `popkit-dev:git` command - May need branch protection checks
- `pop-morning` routine - May recommend unsafe git operations
- Other git-related skills/commands

### Testing

Branch protection logic is verified through:

- **Unit tests** (8): `test_next_action_branch_protection.py`
- **Integration tests** (4): `test_next_action_integration.py`

### Quality Check

Before committing git-related code:

- [ ] Does it check `git branch --show-current`?
- [ ] Does it detect protected branches (main/master/develop/production)?
- [ ] Does it suppress direct push recommendations when on protected branch?
- [ ] Does it recommend feature branch creation as highest priority?
- [ ] Does it include full workflow commands (checkout, push, PR, cleanup)?

**If any answer is "no", the implementation violates Git Workflow Principles.**

---

## GitHub Actions Standards

PopKit enforces specific standards for GitHub Actions workflows to prevent configuration errors.

### Core Principle: Underscored Parameters for actions/first-interaction

**The `actions/first-interaction@v3` action MUST use underscored parameter names** (snake_case), not hyphens.

**IMPORTANT**: This is action-specific. While many GitHub Actions use hyphenated parameters (kebab-case), `actions/first-interaction` explicitly requires underscores.

### Parameter Naming Convention

When using `actions/first-interaction` in workflows, the `with:` section requires underscores:

```yaml
# ✅ CORRECT - Underscores (snake_case)
- uses: actions/first-interaction@v3
  with:
    repo_token: ${{ secrets.GITHUB_TOKEN }}
    issue_message: |
      Welcome message here
    pr_message: |
      PR welcome message here

# ❌ WRONG - Hyphens (kebab-case)
- uses: actions/first-interaction@v3
  with:
    repo-token: ${{ secrets.GITHUB_TOKEN }}
    issue-message: |
      This will fail!
    pr-message: |
      This will fail!
```

### Common Actions and Their Parameters

| Action                         | Parameter     | Correct Format  |
| ------------------------------ | ------------- | --------------- |
| `actions/first-interaction@v3` | Token         | `repo_token`    |
| `actions/first-interaction@v3` | Issue message | `issue_message` |
| `actions/first-interaction@v3` | PR message    | `pr_message`    |

### Historical Context (Lesson Learned)

- **PR #154**: Changed underscores → hyphens (broke workflow) ❌
- **PR #159**: Reverted hyphens → underscores (fixed workflow) ✅
- **PR #161**: Changed underscores → hyphens again (broke workflow) ❌
  _This PR was created due to confusion about the correct format_
- **Current PR**: Changed hyphens → underscores (correct fix) ✅

**Root Cause**: The error message from `actions/first-interaction@v3` explicitly states:

```
Unexpected input(s) 'repo-token', 'pr-message'
valid inputs are ['issue_message', 'pr_message', 'repo_token']
```

This action uses underscores, unlike most GitHub Actions which use hyphens.

### Validation

Workflows in `.github/workflows/` are validated by:

1. **CI Validation** (`.github/workflows/workflow-lint.yml`): Checks for hyphenated parameters as errors
2. **This Documentation**: Context for AI models to prevent errors
3. **Manual Review**: PRs touching workflows require extra scrutiny

### Quality Check

Before modifying GitHub Actions workflows:

- [ ] Does it use underscored parameter names (snake_case) for `actions/first-interaction`?
- [ ] Have you tested the workflow in a feature branch?
- [ ] Does it reference the correct action version?
- [ ] Are all required parameters provided?

**If any answer is "no", the workflow will fail in CI.**

---

## Documentation

### User Documentation

- [README.md](README.md) - Quick start and overview
- [CHANGELOG.md](CHANGELOG.md) - Version history
- Package-specific READMEs in `packages/*/`

### Architecture Documentation

- [Plugin Modularization Design](docs/plans/2025-12-20-plugin-modularization-design.md)
- [Testing & Validation Plan](docs/plans/2025-12-21-phase5-testing-validation-plan.md)
- [Hook Portability Audit](docs/HOOK_PORTABILITY_AUDIT.md)
- [MCP Wildcard Permissions Guide](docs/MCP_WILDCARD_PERMISSIONS.md) - Claude Code 2.0.70+ wildcard syntax

### For Claude Code

When working with this repository:

- This is a **configuration-only plugin** - no build/compile steps needed
- All plugin content is declarative (Markdown + JSON + Python hooks)
- Test changes with `run_all_tests.py` before committing
- Use `/plugin install ./packages/<plugin-name>` to test local changes
- Follow existing patterns for new commands/skills/agents
- Hooks must use `${CLAUDE_PLUGIN_ROOT}` for portability

---

## License

MIT

---

## Author

**Joseph Cannon**
<joseph@thehouseofdeals.com>

---

**Repository**: https://github.com/jrc1883/popkit-claude
**Issues**: https://github.com/jrc1883/popkit-claude/issues
