---
title: Quick Start
description: Get started with PopKit in minutes
---

# Quick Start

This guide will help you get up and running with PopKit in minutes.

## Prerequisites

- Claude Code 2.1.6 or higher
- Git installed
- Node.js 18+ (for local development)

## First Steps

After installing PopKit plugins, restart Claude Code and try these commands:

### 1. Check Your Project Status

```bash
/popkit-dev:next
```

This command analyzes your project state and recommends context-aware next actions.

### 2. Run Morning Routine

```bash
/popkit-dev:routine morning
```

Get a comprehensive project health check with "Ready to Code" score.

### 3. Try a Feature Workflow

```bash
/popkit-dev:dev "Add user authentication"
```

Guided 7-phase feature development workflow from discovery to implementation.

## Key Commands

| Command                       | Description                                    |
| ----------------------------- | ---------------------------------------------- |
| `/popkit-dev:next`            | Get context-aware next actions                 |
| `/popkit-dev:git commit`      | Smart git commit with auto-generated messages  |
| `/popkit-dev:git pr`          | Create pull request with comprehensive summary |
| `/popkit-dev:routine morning` | Morning health check and setup                 |
| `/popkit-dev:routine nightly` | End-of-day cleanup and summary                 |

## Power Mode

For complex tasks requiring multiple agents:

1. Check if Power Mode is available:

   ```bash
   /popkit-core:power status
   ```

2. Start Power Mode:

   ```bash
   /popkit-core:power start
   ```

3. Run a complex workflow:
   ```bash
   /popkit-dev:dev "Implement OAuth2 authentication" --power
   ```

## Next Steps

- Learn about [Agent System](/concepts/agents/)
- Explore [Skills](/concepts/skills/)
- Understand [Power Mode](/features/power-mode/)
