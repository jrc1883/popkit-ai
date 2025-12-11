# PopKit - AI-Powered Development Workflows

Welcome to the PopKit Wiki! PopKit is a Claude Code plugin that orchestrates AI-powered development workflows.

## Quick Start

### Installation

```bash
# Add the PopKit marketplace
/plugin marketplace add jrc1883/popkit-claude

# Install the plugin
/plugin install popkit@popkit-claude

# Restart Claude Code to activate
```

### Basic Usage

After installation, use `/popkit:` commands to access PopKit features:

```bash
/popkit:next              # Get context-aware recommendations
/popkit:dev work #123     # Work on a GitHub issue
/popkit:git commit        # Smart commit with auto-generated message
/popkit:routine morning   # Run morning health check
```

## Core Features

| Feature | Description | Command |
|---------|-------------|---------|
| **Next Action** | Context-aware recommendations | `/popkit:next` |
| **Dev Workflow** | 7-phase feature development | `/popkit:dev` |
| **Git Integration** | Smart commits, PRs, reviews | `/popkit:git` |
| **Power Mode** | Multi-agent orchestration | `/popkit:power` |
| **Issue Management** | GitHub issue workflows | `/popkit:issue` |
| **Routines** | Morning/nightly health checks | `/popkit:routine` |

## Navigation

- [[Commands]] - Full command reference
- [[Agents]] - Available agents and their capabilities
- [[Skills]] - Reusable skill library
- [[Contributing]] - How to contribute

## Architecture

PopKit uses a tiered agent system:

- **Tier 1**: Always-active core agents (11 agents)
- **Tier 2**: On-demand specialists (17 agents)
- **Feature Workflow**: 7-phase development agents (2 agents)

## Resources

- [GitHub Repository](https://github.com/jrc1883/popkit-claude)
- [Issue Tracker](https://github.com/jrc1883/popkit-claude/issues)
- [Changelog](https://github.com/jrc1883/popkit-claude/blob/main/CHANGELOG.md)

## Version

Current: 0.1.0 (Preview)

---
*PopKit is developed by [jrc1883](https://github.com/jrc1883)*
