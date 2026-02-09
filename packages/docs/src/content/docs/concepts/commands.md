---
title: Commands
description: Slash commands for common workflows
---

# Commands

PopKit provides 25 slash commands for common development workflows. Commands are the primary interface for interacting with PopKit.

## Core Commands

### Project Management

- `/popkit-dev:next` - Get context-aware next actions
- `/popkit-core:project analyze` - Comprehensive project analysis
- `/popkit-dev:milestone` - Milestone management and tracking

### Git Workflows

- `/popkit-dev:git commit` - Create commit with auto-generated message
- `/popkit-dev:git push` - Push changes with pre-push checks
- `/popkit-dev:git pr` - Create pull request with comprehensive summary

### Development

- `/popkit-dev:dev` - 7-phase feature development workflow
- `/popkit-dev:work` - Work on specific GitHub issue
- `/popkit-ops:debug` - Debug code or routing issues

### Routines

- `/popkit-dev:routine morning` - Morning health check
- `/popkit-dev:routine nightly` - End-of-day cleanup
- `/popkit-dev:routine generate` - Create custom routine

## Command Structure

Commands follow a consistent pattern:

```
/plugin-name:command [subcommand] [arguments] [--flags]
```

Examples:

```bash
/popkit-dev:git commit
/popkit-dev:git pr --draft
/popkit-dev:routine morning quick
/popkit-ops:security scan --fix
```

## Command vs Skills

| Commands              | Skills                   |
| --------------------- | ------------------------ |
| User-facing interface | Internal automation      |
| Slash command syntax  | Invoked programmatically |
| High-level workflows  | Low-level operations     |
| Documentation focused | Implementation focused   |

Commands often use multiple skills internally to accomplish their goals.

## Next Steps

- Learn about [Hooks](/concepts/hooks/)
- Explore [Power Mode](/features/power-mode/)
- Review command reference (coming in Phase 3)
