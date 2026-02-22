---
title: Commands
description: Slash commands for common workflows
---

# Commands

PopKit provides 25 slash commands for common development workflows. Commands are the primary interface for interacting with PopKit.

## Two-Tier Model

PopKit intentionally exposes both orchestration commands and direct skills:

| Tier              | Prefix     | Purpose                                                      | Recommended |
| ----------------- | ---------- | ------------------------------------------------------------ | ----------- |
| Workflow commands | `/popkit-` | High-level flows that orchestrate skills, hooks, and scripts | Yes         |
| Direct skills     | `/pop-`    | Low-level primitives for targeted/advanced usage             | Advanced    |

Most users should start with `/popkit-*` commands and drop to `/pop-*` when they want precise, direct control.

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
- `/popkit-dev:issue` - GitHub issue management and execution flows
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

| Commands                                | Skills                                        |
| --------------------------------------- | --------------------------------------------- |
| User-facing workflows                   | Reusable primitives                           |
| Usually `/popkit-*`                     | Usually `/pop-*` (or `/skill invoke <name>`)  |
| Can orchestrate multiple skills + hooks | Focused on one domain capability              |
| Stable entry points for daily usage     | Advanced/direct execution and building blocks |

Commands often use multiple skills internally to accomplish their goals.

## What Commands Add

When a `/popkit-*` command wraps a `/pop-*` skill, it typically adds:

### Mode Handling

Commands detect your current context and adjust behavior:

- **Plan mode**: Commands may gather more information before acting
- **Quick mode**: Commands skip exploratory steps for faster execution
- **Power mode**: Commands can delegate to multiple agents in parallel

Example: `/popkit-dev:next` in quick mode skips detailed analysis; in verbose mode it provides full recommendations with reasoning.

### Reporting

Commands produce structured output that includes:

- **Scores**: Numerical health indicators (Ready to Code Score, Sleep Score)
- **Summaries**: What was analyzed or accomplished
- **Next steps**: Recommended follow-up actions with `AskUserQuestion`

### Command-Level Guidance

Commands provide context-aware suggestions:

- What to do next based on results
- Which related commands might help
- When to escalate to Power Mode for complex tasks

This guidance follows "The PopKit Way" — every command ends with actionable options, not just a report dump.

## Next Steps

- Learn about [Hooks](/concepts/hooks/)
- Explore [Power Mode](/features/power-mode/)
- Review [Commands Reference](/reference/commands/)
