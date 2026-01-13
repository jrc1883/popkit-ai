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

| Plugin | Purpose | Key Features |
|--------|---------|--------------|
| **popkit-core** | Foundation & orchestration | Power Mode, project analysis, plugin management |
| **popkit-dev** | Development workflows | Git operations, GitHub integration, daily routines |
| **popkit-ops** | Operations & quality | Testing, debugging, security, deployment |
| **popkit-research** | Knowledge management | Research capture, knowledge base |

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

---

## Version Requirements

PopKit requires specific Claude Code versions for full functionality:

| Feature | Minimum Version | Description |
|---------|-----------------|-------------|
| **Extended Thinking** | 2.0.67 | Default enabled (10k tokens) |
| **Native Async Mode** | 2.0.64 | Background Task tool (5+ agents) |
| **MCP Wildcard Permissions** | 2.0.70 | `mcp__server__*` syntax for tool permissions |
| **Plan Mode** | 2.0.70 | Agent approval workflow |
| **Configuration Management** | 2.0.71 | `/config` toggle |
| **MCP Permissions** | 2.0.71 | Fixed permissions for MCP servers |
| **Skill Hot-Reload** | 2.1.0 | Skills reload without restart |
| **Forked Skill Contexts** | 2.1.0 | Isolated execution contexts |
| **YAML List Format** | 2.1.0 | Clean agent tools syntax |
| **SessionStart agent_type** | 2.1.2 | `--agent` flag detection in hooks |
| **Plugin Auto-Update Control** | 2.1.2 | `FORCE_AUTOUPDATE_PLUGINS` env var |
| **Large Output Persistence** | 2.1.2 | Tool outputs saved to disk (not truncated) |
| **Unified Commands/Skills UX** | 2.1.3 | Mental model simplification (no code changes) |
| **Release Channel Toggle** | 2.1.3 | `stable` vs `latest` in `/config` |
| **Permission Rule Validation** | 2.1.3 | Unreachable rule detection in `/doctor` |
| **Background Task Disable** | 2.1.4 | `CLAUDE_CODE_DISABLE_BACKGROUND_TASKS` env var |
| **Temp Directory Override** | 2.1.5 | `CLAUDE_CODE_TMPDIR` env var |
| **Settings Search** | 2.1.6 | Keyword filtering in `/config` |
| **Nested Skills Discovery** | 2.1.6 | Auto-detect `.claude/skills` subdirectories |
| **Shell Continuation Security** | 2.1.6 | Permission bypass fix |

**Recommended**: Claude Code 2.1.6+ for full feature support and latest security fixes.

---

## Current Status

**Version**: 1.0.0-beta.4
**Status**: Beta release
**Plugins**: 4 modular plugins
**Commands**: 23 workflow commands
**Skills**: 38 reusable skills
**Agents**: 22 specialized agents

### Recent Updates

- **2026-01-12**: Claude Code 2.1.6 compatibility verified, hook import paths fixed (v1.0.0-rc.1)
- **2026-01-09**: Claude Code 2.1.2 integration complete (v1.0.0-beta.4)
- **2026-01-06**: Repository field format fix (all plugin.json files)
- **2025-12-29**: Core cleanup and account consolidation (v1.0.0-beta.3)
- **2025-12-28**: Version alignment at v1.0.0-beta.1
- **2025-12-21**: Testing & validation complete (96.3% pass rate)
- **2025-12-20**: Plugin modularization complete

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
