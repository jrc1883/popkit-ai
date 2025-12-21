# PopKit

**AI-powered development workflows for Claude Code** - Modular plugin suite for professional software development.

**Version:** 0.1.0 (Beta) | **Plugins:** 8 | **Commands:** 24 | **Skills:** 46 | **Agents:** 29

---

## 🎯 What is PopKit?

PopKit transforms Claude Code into a complete development workflow system. Instead of using raw tools, you get:

- **7 Focused Plugins**: Install only what you need
- **24 Workflow Commands**: From feature dev to deployment
- **46 Reusable Skills**: Composable automation patterns
- **29 Specialized Agents**: Context-aware AI assistance
- **FREE Local Execution**: All features work without cloud
- **API Key Enhancements**: Optional semantic intelligence

---

## 📦 Modular Architecture

PopKit is now split into focused workflow plugins:

| Plugin | Purpose | Commands | When to Use |
|--------|---------|----------|-------------|
| **[popkit-dev](packages/popkit-dev/)** | Development workflows | 5 | Daily dev, git, routines |
| **[popkit-github](packages/popkit-github/)** | GitHub integration | 2 | Issues, milestones |
| **[popkit-quality](packages/popkit-quality/)** | Testing & debugging | 4 | QA, security, assessments |
| **[popkit-deploy](packages/popkit-deploy/)** | Deployment automation | 1 | Ship to any platform |
| **[popkit-research](packages/popkit-research/)** | Knowledge management | 2 | Research, notes |
| **[popkit-core](packages/popkit-core/)** | Meta features | 10 | Project setup, Power Mode |
| **[popkit (meta)](packages/popkit-meta/)** | Complete suite | All | One-click install |

**Plus**: `popkit-shared` - Shared Python utilities foundation

---

## ⚡ Quick Start

### Option 1: Complete Suite (Recommended)

Install everything with one command:

```bash
/plugin install popkit@popkit-marketplace
# Restart Claude Code
```

All 24 commands available under `/popkit:` namespace.

### Option 2: Selective Installation

Install only what you need:

```bash
# Core development workflows
/plugin install popkit-dev@popkit-marketplace

# Add GitHub integration
/plugin install popkit-github@popkit-marketplace

# Add quality tools
/plugin install popkit-quality@popkit-marketplace

# Restart Claude Code
```

See [Migration Guide](packages/popkit-meta/MIGRATION.md) for details.

---

## 🚀 Core Workflows

### Feature Development

```bash
# Start development workflow
/popkit:dev "Add user authentication"
  → Brainstorm → Plan → Implement → Review → PR

# Daily routines
/popkit:routine morning    # Health check + "Ready to Code" score
/popkit:routine nightly    # Cleanup + "Sleep Score"

# Context-aware help
/popkit:next              # What should I do next?
```

### Git Operations

```bash
# Smart commits
/popkit:git commit        # Auto-generates conventional commit message

# Pull requests
/popkit:git pr            # Creates PR with summary + checklist

# Code review
/popkit:git review        # In-depth code review with suggestions
```

### Quality Assurance

```bash
# Multi-perspective assessment
/popkit:assess all        # Run 6 specialized assessors

# Systematic debugging
/popkit:debug "login fails on mobile"

# Security scanning
/popkit:security scan     # Find vulnerabilities + create issues
```

### Deployment

```bash
# Universal deployment
/popkit:deploy init       # Configure deployment targets
/popkit:deploy execute    # Ship to Docker/npm/Vercel/etc.
```

---

## 🏗️ Repository Structure

```
popkit/
├── packages/
│   ├── popkit-shared/      # Shared Python utilities (69 modules)
│   ├── popkit-dev/         # Development workflows plugin
│   ├── popkit-github/      # GitHub integration plugin
│   ├── popkit-quality/     # Quality assurance plugin
│   ├── popkit-deploy/      # Deployment automation plugin
│   ├── popkit-research/    # Research management plugin
│   ├── popkit-core/        # Core utilities plugin
│   ├── popkit-meta/        # Meta-plugin (backwards compatibility)
│   └── cloud/              # PopKit Cloud API (Cloudflare Workers)
├── docs/
│   ├── plans/              # Design documents
│   ├── research/           # Research notes
│   ├── phases/             # Phase completion reports
│   └── cloud/              # Cloud documentation
├── CLAUDE.md               # Claude Code instructions
├── CHANGELOG.md            # Version history
└── README.md               # This file
```

---

## 🔑 API Key Enhancement Model

**Everything works FREE locally.** An API key adds:

- ✨ **Semantic Search**: Find skills/agents using natural language
- 🌐 **Cloud Knowledge**: Cross-project learning and patterns
- 🤝 **Community Intelligence**: Benefit from collective insights
- 🎯 **Enhanced Routing**: Better agent selection with embeddings

**No feature gating** - only intelligence amplification.

---

## 📚 Documentation

### Plugin Documentation
- [popkit-dev README](packages/popkit-dev/README.md)
- [popkit-github README](packages/popkit-github/README.md)
- [popkit-quality README](packages/popkit-quality/README.md)
- [popkit-deploy README](packages/popkit-deploy/README.md)
- [popkit-research README](packages/popkit-research/README.md)
- [popkit-core README](packages/popkit-core/README.md)
- [popkit-meta Migration Guide](packages/popkit-meta/MIGRATION.md)

### Architecture
- [Plugin Modularization Design](docs/plans/2025-12-20-plugin-modularization-design.md)
- [Testing & Validation Plan](docs/plans/2025-12-21-phase5-testing-validation-plan.md)
- [CLAUDE.md](CLAUDE.md) - Full development guide

---

## 🎯 Current Status

**Epic #580**: Plugin Modularization
**Phase**: 5 of 6 (Testing & Validation)
**Progress**: 75% Complete

**Recent Milestones**:
- ✅ All 6 plugins extracted and tested (Phases 1-4)
- ✅ 96.3% test pass rate (155/161 tests)
- ✅ Zero functionality regression
- 🔄 Manual command testing (in progress)
- 📋 Documentation & marketplace release (next)

See [CLAUDE.md](CLAUDE.md) for detailed roadmap.

---

## 🤝 Contributing

PopKit is in active development. See:
- [GitHub Issues](https://github.com/jrc1883/elshaddai/issues?q=is%3Aissue+is%3Aopen+label%3Aapp%3Apopkit)
- [CLAUDE.md](CLAUDE.md) - Development guide

---

## 📜 License

MIT

---

## 👤 Author

**Joseph Cannon**
<joseph@thehouseofdeals.com>

---

**Ready to supercharge your development workflow?**

```bash
/plugin install popkit@popkit-marketplace
```

Then restart Claude Code and run `/popkit:next` to get started!
