---
title: Installation
description: How to install PopKit plugins for Claude Code
---

# Installation

PopKit is published as a GitHub-based marketplace. Install it in two steps:

## Step 1: Add the Marketplace (One-time Setup)

```bash
/plugin marketplace add jrc1883/popkit-claude
```

## Step 2: Install Plugins

Install all plugins for full functionality:

```bash
# Install all plugins
/plugin install popkit-core@popkit-claude
/plugin install popkit-dev@popkit-claude
/plugin install popkit-ops@popkit-claude
/plugin install popkit-research@popkit-claude
```

After installation, restart Claude Code and run `/popkit-dev:next` to get started.

## For Local Development (Git Clone)

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

## Version Requirements

PopKit requires Claude Code 2.1.6+ for full feature support and latest security fixes.

| Feature                         | Minimum Version |
| ------------------------------- | --------------- |
| **Skill Hot-Reload**            | 2.1.0           |
| **Forked Skill Contexts**       | 2.1.0           |
| **SessionStart agent_type**     | 2.1.2           |
| **Plugin Auto-Update Control**  | 2.1.2           |
| **Unified Commands/Skills UX**  | 2.1.3           |
| **Shell Continuation Security** | 2.1.6           |

## Next Steps

- [Quick Start Guide](/getting-started/quick-start/)
- [Core Concepts](/concepts/agents/)
