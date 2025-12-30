# PopKit

**AI-powered development workflows for Claude Code** - Modular plugin suite for professional software development.

**Version:** 1.0.0-beta.1 | **Plugins:** 5 | **Commands:** 25 | **Skills:** 38 | **Agents:** 21

---

## 🎯 What is PopKit?

PopKit transforms Claude Code into a complete development workflow system. Instead of using raw tools, you get:

- **5 Focused Plugins**: Install only what you need
- **25 Workflow Commands**: From feature dev to deployment (3 deprecated)
- **38 Reusable Skills**: Composable automation patterns
- **21 Specialized Agents**: Context-aware AI assistance
- **FREE Local Execution**: All features work without cloud
- **API Key Enhancements**: Optional semantic intelligence

---

## 📦 Modular Architecture

PopKit is split into 5 focused workflow plugins:

| Plugin | Purpose | Commands | When to Use |
|--------|---------|----------|-------------|
| **[popkit-core](packages/popkit-core/)** | Foundation & Power Mode | 11 | Project setup, plugin management, orchestration |
| **[popkit-dev](packages/popkit-dev/)** | Development workflows | 7 | Daily dev, git, GitHub, routines |
| **[popkit-ops](packages/popkit-ops/)** | Operations & quality | 5 | Testing, debugging, security, deployment |
| **[popkit-research](packages/popkit-research/)** | Knowledge management | 2 | Research capture, knowledge base |
| **[popkit-suite](packages/popkit-suite/)** | Complete bundle | All | One-click install (all features) |

**Foundation**: `popkit-shared` (v1.0.0) - 70 shared Python utility modules

---

## ⚡ Quick Start

### Option 1: Complete Suite (Recommended)

Install everything with one command:

```bash
/plugin install popkit-suite@popkit-marketplace
# Restart Claude Code
```

All 25 commands available under `/popkit:` namespace.

### Option 2: Selective Installation

Install only what you need:

```bash
# Foundation (required for other plugins)
/plugin install popkit-core@popkit-marketplace

# Development workflows (git, GitHub, feature dev, routines)
/plugin install popkit-dev@popkit-marketplace

# Operations & quality (testing, security, deployment)
/plugin install popkit-ops@popkit-marketplace

# Knowledge management (research, notes)
/plugin install popkit-research@popkit-marketplace

# Restart Claude Code
```

**Minimum**: popkit-core (11 commands)
**Recommended**: popkit-core + popkit-dev (18 commands)
**Complete**: popkit-suite (all 25 commands)

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
│   ├── shared-py/          # Shared Python utilities (70 modules)
│   ├── popkit-core/        # Foundation plugin (Power Mode, config)
│   ├── popkit-dev/         # Development workflows (git, GitHub, routines)
│   ├── popkit-ops/         # Operations & quality (test, debug, deploy)
│   ├── popkit-research/    # Knowledge management (research, notes)
│   ├── popkit-suite/       # Meta-plugin (complete bundle)
│   ├── cloud/              # PopKit Cloud API (Cloudflare Workers)
│   ├── benchmarks/         # Testing framework + archived files
│   ├── docs/               # Documentation site (Astro + Starlight)
│   ├── landing/            # Marketing site
│   └── universal-mcp/      # Multi-IDE MCP server (future)
├── docs/
│   ├── plans/              # Design documents + implementation plans
│   ├── assessments/        # Quality assessment reports
│   └── research/           # Research notes
├── CLAUDE.md               # Claude Code development instructions
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
