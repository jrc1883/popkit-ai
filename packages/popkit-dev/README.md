# PopKit Dev - Development Workflow Plugin

**Version:** 1.0.0-beta.1
**Status:** Ready for marketplace publication (Epic #580 Complete)

## Overview

PopKit Dev is a complete development workflow plugin that provides comprehensive tools for feature development, git operations, GitHub integration, and daily routines.

**v0.2.0 Update:** Merged popkit-github plugin for unified development workflow. GitHub operations (issues, PRs, milestones) are now integrated alongside feature development and git operations.

## Features

### Commands (7)

| Command | Description |
|---------|-------------|
| `/popkit:dev` | 7-phase feature development workflow |
| `/popkit:git` | Git operations (commit, push, pr, review, release, publish) |
| `/popkit:issue` | GitHub issue management (create, list, view, close, comment, edit, link) |
| `/popkit:milestone` | Milestone tracking (list, create, close, report, health analysis) |
| `/popkit:worktree` | Git worktree management |
| `/popkit:routine` | Morning health checks and nightly cleanup |
| `/popkit:next` | Context-aware next action recommendations |

### Skills (9)

- `pop-brainstorming` - Interactive idea refinement
- `pop-writing-plans` - Implementation plan generation
- `pop-executing-plans` - Plan execution with review
- `pop-next-action` - Smart action recommendations
- `pop-session-capture/resume/restore` - Session continuity
- `pop-routine-optimized` - Morning/nightly routines
- `pop-routine-measure` - Routine metrics tracking

### Agents (5)

- **code-explorer** - Deep codebase analysis (feature-workflow)
- **code-architect** - Implementation design (feature-workflow)
- **code-reviewer** - Code review (tier-1)
- **refactoring-expert** - Code restructuring (tier-1)
- **rapid-prototyper** - Fast MVP development (tier-2)

## Installation

```bash
# Local installation during development
/plugin install popkit-dev@file:./packages/popkit-dev

# Future: Marketplace installation
/plugin install popkit-dev@popkit-marketplace
```

## Dependencies

- **popkit-shared** (>= 1.0.0) - Shared utility modules
- **Python** (>= 3.8)
- **requests** library

**Minimum Requirements**:
- Claude Code 2.0.67+ (for extended thinking and plan mode)

## Architecture

Part of PopKit's modular plugin architecture (v1.0.0-beta.1):

```
packages/
├── shared-py/          # Shared utilities v1.0.0 (all plugins depend on this)
├── popkit-core/        # Foundation & Power Mode
├── popkit-dev/         # Development workflows (this plugin)
├── popkit-ops/         # Operations, quality, deployment
├── popkit-research/    # Knowledge management
└── popkit-suite/       # Complete bundle (meta-plugin)
```

## Usage Examples

### Feature Development

```bash
# Full 7-phase workflow
/popkit:dev "user authentication"

# Quick mode
/popkit:dev "fix login bug" --mode quick

# Issue-driven
/popkit:dev work #123
```

### Git Operations

```bash
# Smart commit
/popkit:git commit

# Create PR
/popkit:git pr

# Code review
/popkit:git review
```

### Daily Routines

```bash
# Morning health check
/popkit:routine morning

# Nightly cleanup
/popkit:routine nightly
```

## Testing Strategy

1. ✅ Package structure created
2. ✅ All components extracted (5 commands, 9 skills, 5 agents)
3. ⏳ Local installation test
4. ⏳ Command functionality validation
5. ⏳ Integration with monolithic plugin

## Success Metrics

- [ ] All commands work identically to monolithic version
- [ ] Installation < 30 seconds
- [ ] No context window increase
- [ ] Clean uninstall without breaking other plugins

## Issues

- **Phase 2**: Issue #571 (this plugin)
- **Parent Epic**: Issue #580 (Plugin Modularization)
- **Dependency**: Issue #570 (Shared package - completed)

## License

MIT
