# PopKit (Complete Suite)

The complete PopKit plugin suite - all development workflow tools in one unified package.

## Overview

PopKit is a comprehensive AI-powered development workflow system for Claude Code. This meta-plugin installs all 6 PopKit workflow plugins, providing backwards compatibility with the original monolithic plugin while offering the benefits of modular architecture.

## What's Included

Installing this meta-plugin gives you access to **24 commands**, **46 skills**, and **29 agents** across 6 focused plugins:

### 1. Development Workflows (popkit-dev)
**5 commands** for feature development and daily routines
- `/popkit:dev` - 7-phase feature development workflow
- `/popkit:git` - Git operations (commit, push, pr, review)
- `/popkit:worktree` - Git worktree management
- `/popkit:routine` - Morning health checks and nightly cleanup
- `/popkit:next` - Context-aware next action recommendations

### 2. GitHub Integration (popkit-github)
**2 commands** for issue and milestone management
- `/popkit:issue` - Create, list, view, close, comment on issues
- `/popkit:milestone` - Milestone tracking and health analysis

### 3. Quality Assurance (popkit-quality)
**4 commands** for testing, debugging, and security
- `/popkit:assess` - Multi-perspective code assessment
- `/popkit:audit` - Project audits (quarterly, yearly, stale, duplicates)
- `/popkit:debug` - Systematic debugging with root cause analysis
- `/popkit:security` - Security vulnerability management

### 4. Deployment Automation (popkit-deploy)
**1 command** for universal deployment orchestration
- `/popkit:deploy` - Deploy to Docker, npm, PyPI, Vercel, Netlify, Cloudflare, GitHub Releases

### 5. Research & Knowledge (popkit-research)
**2 commands** for research and knowledge management
- `/popkit:research` - Capture, organize, and search research
- `/popkit:knowledge` - Knowledge base with semantic search

### 6. Core Utilities (popkit-core)
**10 commands** for meta features and project management
- `/popkit:plugin` - Plugin testing and management
- `/popkit:stats` - Efficiency metrics and analytics
- `/popkit:privacy` - Privacy controls and data management
- `/popkit:account` - Account management
- `/popkit:upgrade` - Upgrade to premium
- `/popkit:dashboard` - Multi-project management
- `/popkit:workflow-viz` - Workflow visualization
- `/popkit:bug` - Bug reporting
- `/popkit:power` - Power Mode multi-agent orchestration
- `/popkit:project` - Project analysis and initialization

## Installation

### Option 1: Complete Suite (This Plugin)

Install everything with one command:

```bash
/plugin install popkit@popkit-marketplace
```

Then restart Claude Code. All 24 commands will be available under `/popkit:` namespace.

### Option 2: Selective Installation

Install only the plugins you need:

```bash
# Development workflows only
/plugin install popkit-dev@popkit-marketplace

# Add GitHub integration
/plugin install popkit-github@popkit-marketplace

# Add quality tools
/plugin install popkit-quality@popkit-marketplace

# Add deployment
/plugin install popkit-deploy@popkit-marketplace

# Add research tools
/plugin install popkit-research@popkit-marketplace

# Add core utilities
/plugin install popkit-core@popkit-marketplace
```

## Quick Start

After installation:

1. **Initialize a project**:
   ```bash
   /popkit:project init
   ```

2. **Start development workflow**:
   ```bash
   /popkit:dev "Add user authentication"
   ```

3. **Run morning health check**:
   ```bash
   /popkit:routine morning
   ```

4. **Commit changes**:
   ```bash
   /popkit:git commit
   ```

5. **Create pull request**:
   ```bash
   /popkit:git pr
   ```

## Why Use the Meta-Plugin?

### Advantages

✅ **Backwards Compatible**: Works exactly like the original monolithic plugin
✅ **One-Click Install**: Get all features with a single command
✅ **Unified Namespace**: All commands under `/popkit:`
✅ **Automatic Updates**: Update all plugins together
✅ **Zero Configuration**: Works out of the box

### When to Use Individual Plugins Instead

Consider installing plugins individually if you:

- Only need specific features (e.g., just git workflows)
- Want to minimize context window usage
- Prefer granular control over updates
- Are building a minimal development environment

See [MIGRATION.md](MIGRATION.md) for detailed migration guidance.

## Architecture

This meta-plugin has **no implementation code** - it's purely a dependency aggregator:

```json
{
  "dependencies": {
    "popkit-shared": ">=0.1.0",
    "popkit-dev": ">=0.1.0",
    "popkit-github": ">=0.1.0",
    "popkit-quality": ">=0.1.0",
    "popkit-deploy": ">=0.1.0",
    "popkit-research": ">=0.1.0",
    "popkit-core": ">=0.1.0"
  }
}
```

All commands, skills, and agents come from the individual plugins.

## Plugin Breakdown

| Plugin | Commands | Skills | Agents | Size | Install Size |
|--------|----------|--------|--------|------|--------------|
| popkit-dev | 5 | 9 | 5 | Medium | ~15 MB |
| popkit-github | 2 | 0 | 0 | Small | ~2 MB |
| popkit-quality | 4 | 11 | 11 | Large | ~20 MB |
| popkit-deploy | 1 | 13 | 3 | Large | ~12 MB |
| popkit-research | 2 | 3 | 1 | Small | ~4 MB |
| popkit-core | 10 | 10 | 9 | Largest | ~35 MB |
| **Total** | **24** | **46** | **29** | **~88 MB** | **~88 MB** |

## Features

### API Key Enhancement Model

All features work **FREE** locally. An API key adds:

- **Semantic Search**: Find skills and agents using natural language
- **Cloud Knowledge Base**: Cross-project learning and pattern sharing
- **Community Patterns**: Benefit from collective intelligence
- **Enhanced Routing**: Better agent selection with embeddings

No feature gating - only intelligence amplification.

### Privacy First

- **Local-first**: All core features work without cloud
- **Opt-in Telemetry**: Usage stats are completely optional
- **Data Export**: Full data export available anytime
- **Right to Deletion**: Complete data deletion on request

## Documentation

Each plugin has its own documentation:

- [popkit-dev README](../popkit-dev/README.md)
- [popkit-github README](../popkit-github/README.md)
- [popkit-quality README](../popkit-quality/README.md)
- [popkit-deploy README](../popkit-deploy/README.md)
- [popkit-research README](../popkit-research/README.md)
- [popkit-core README](../popkit-core/README.md)

## Migration from Monolithic Plugin

See [MIGRATION.md](MIGRATION.md) for complete migration guide.

**TL;DR**:
```bash
# Uninstall old
/plugin uninstall popkit-monolithic

# Install new (this plugin)
/plugin install popkit@popkit-marketplace

# Restart Claude Code
```

All your workflows continue to work unchanged!

## Troubleshooting

### Commands not found after installation

1. Check plugins are installed: `/plugin list`
2. Restart Claude Code
3. Verify all sub-plugins are present

### Version mismatch warnings

Update all plugins to latest:
```bash
/plugin update popkit
```

Or reinstall:
```bash
/plugin uninstall popkit
/plugin install popkit@popkit-marketplace
```

### Need help?

- Report issues: `/popkit:bug report "description"`
- GitHub: https://github.com/jrc1883/popkit/issues
- Migration guide: [MIGRATION.md](MIGRATION.md)

## Development Status

**Version**: 0.1.0 (Beta)
**Phase**: 8 of 8 (Plugin Modularization - Epic #580)
**Status**: Complete modularization, ready for testing

## Versioning

All sub-plugins follow semantic versioning:

- **MAJOR** (X.0.0): Breaking changes
- **MINOR** (0.X.0): New features (backwards compatible)
- **PATCH** (0.0.X): Bug fixes

The meta-plugin version matches the highest sub-plugin version.

## License

MIT

## Author

Joseph Cannon <joseph@thehouseofdeals.com>

## Contributing

See the main repository for contribution guidelines:
https://github.com/jrc1883/popkit

---

**Ready to supercharge your development workflow?**

```bash
/plugin install popkit@popkit-marketplace
```

Then restart Claude Code and run `/popkit:next` to get started!
