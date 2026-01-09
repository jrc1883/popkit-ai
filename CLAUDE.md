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

After installation, restart Claude Code and run `/popkit:next` to get started.

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
- `commands/*.md` - Slash commands (e.g., `/popkit:git`)
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
/popkit:plugin test              # Run all tests
/popkit:plugin test agents       # Test specific category
/popkit:plugin test --verbose    # Detailed output
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
| **Plan Mode** | 2.0.70 | Agent approval workflow |
| **Configuration Management** | 2.0.71 | `/config` toggle |
| **MCP Permissions** | 2.0.71 | Fixed permissions for MCP servers |
| **Skill Hot-Reload** | 2.1.0 | Skills reload without restart |
| **Forked Skill Contexts** | 2.1.0 | Isolated execution contexts |
| **YAML List Format** | 2.1.0 | Clean agent tools syntax |
| **SessionStart agent_type** | 2.1.2 | `--agent` flag detection in hooks |
| **Plugin Auto-Update Control** | 2.1.2 | `FORCE_AUTOUPDATE_PLUGINS` env var |
| **Large Output Persistence** | 2.1.2 | Tool outputs saved to disk (not truncated) |

**Recommended**: Claude Code 2.1.2+ for full feature support.

---

## Current Status

**Version**: 1.0.0-beta.3
**Status**: Beta release
**Plugins**: 4 modular plugins
**Commands**: 23 workflow commands
**Skills**: 38 reusable skills
**Agents**: 22 specialized agents

### Recent Updates

- **2025-12-29**: Core cleanup and account consolidation (v1.0.0-beta.3)
- **2025-12-28**: Version alignment at v1.0.0-beta.1
- **2025-12-21**: Testing & validation complete (96.3% pass rate)
- **2025-12-20**: Plugin modularization complete

See [CHANGELOG.md](CHANGELOG.md) for full version history.

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
