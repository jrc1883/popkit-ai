# PopKit

<!-- Badge Section -->
<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0--beta.4-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Build Status](https://img.shields.io/github/actions/workflow/status/jrc1883/popkit-claude/ci.yml?branch=main)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)
![GitHub Stars](https://img.shields.io/github/stars/jrc1883/popkit-claude?style=social)
![GitHub Forks](https://img.shields.io/github/forks/jrc1883/popkit-claude?style=social)
![Claude Code](https://img.shields.io/badge/Claude%20Code-2.1.2%2B-purple.svg)

**Get 10x the work done in Claude Code—without the learning curve.**

Transforms Claude Code into a complete development workflow system with intelligent agents that coordinate automatically, handle tasks in parallel, and get smarter over time. One subscription, zero installation friction.

**Version:** 1.0.0-beta.4 | **Plugins:** 4 | **Commands:** 23 | **Skills:** 38 | **Agents:** 22

[Quick Start](#-quick-start) • [Features](#-what-is-popkit) • [Documentation](#-documentation) • [Contributing](#-contributing)

</div>

---

## 📑 Table of Contents

- [What is PopKit?](#-what-is-popkit)
- [See It In Action](#-see-it-in-action)
- [Modular Architecture](#-modular-architecture)
- [Quick Start](#-quick-start)
- [Core Workflows](#-core-workflows)
  - [Feature Development](#feature-development)
  - [Git Operations](#git-operations)
  - [Quality Assurance](#quality-assurance)
  - [Deployment](#deployment)
- [Repository Structure](#️-repository-structure)
- [API Key Enhancement Model](#-api-key-enhancement-model)
- [Documentation](#-documentation)
- [Current Status](#-current-status)
- [Contributing](#-contributing)
- [Contributors](#-contributors)
- [Star History](#-star-history)
- [License](#-license)
- [Author](#-author)

---

## 🎯 What is PopKit?

PopKit transforms Claude Code into a complete development workflow system with intelligent orchestration that makes you more productive without adding complexity.

### Why PopKit?

- **12x Cheaper at Scale** - Run coordinated multi-agent workflows with a single Claude subscription ($20/month), not 12 parallel subscriptions ($240/month). PopKit's intelligent orchestration means you pay once and work on unlimited tasks.

- **Zero Installation Friction** - No new IDE to learn, no Docker containers to manage, no separate tools to install. PopKit lives inside Claude Code as a plugin—install in 30 seconds and start building immediately.

- **Smarter Over Time, Not Just Faster** - Our embedding-based agent routing has already reduced context baseline by 40.5% (25.7k → 15.3k tokens). The more you use PopKit, the cheaper and more precise your AI assistance becomes.

- **Parallel AI Workers Without the Complexity** - Power Mode coordinates multiple specialized agents working on different aspects of your task simultaneously. You get the benefits of parallel execution without managing multiple Claude instances or terminals.

- **GitHub-First Workflows That Actually Work** - Issues automatically become tasks, tasks become PRs, and PRs get reviewed with quality gates. PopKit handles the entire workflow from ideation to deployment without leaving Claude Code.

- **Quality Gates You Can Trust** - Every workflow includes automated testing, security scanning, code review, and deployment validation. Six specialized assessors (Anthropic, Security, Performance, UX, Architecture, Documentation) ensure production-ready code.

### What's Included

- **5 Focused Plugins**: Install only what you need (core, dev, ops, research, or complete suite)
- **23 Workflow Commands**: From morning routines to deployment automation
- **38 Reusable Skills**: Battle-tested workflows from planning to production
- **22 Specialized Agents**: Context-aware AI assistance that routes automatically
- **FREE Local Execution**: All features work without cloud API keys
- **Optional Enhancements**: Semantic intelligence with Voyage AI embeddings

---

## 🎬 See It In Action

### Quick Start Demo

![PopKit Quick Start](packages/popkit-core/assets/images/quick-start.gif)

*Watch how PopKit gets you up and running in seconds with `/plugin install` and intelligent project setup.*

### Morning Routine Workflow

![Morning Routine](packages/popkit-core/assets/images/morning-routine.gif)

*See the `/popkit-dev:routine morning` command in action - automated health checks, dependency updates, and your personalized "Ready to Code" score.*

### Feature Development Workflow

![Feature Workflow](packages/popkit-core/assets/images/feature-workflow.gif)

*Complete feature development cycle: brainstorm → plan → implement → review → PR creation, all orchestrated by `/popkit-dev:dev`.*

### Power Mode Multi-Agent Orchestration

![Power Mode](packages/popkit-core/assets/images/power-mode.gif)

*Experience Power Mode's intelligent agent orchestration handling complex tasks with multiple specialized agents working in parallel.*

---

## 📦 Modular Architecture

PopKit is split into 5 focused workflow plugins:

| Plugin | Purpose | Commands | When to Use |
|--------|---------|----------|-------------|
| **[popkit-core](packages/popkit-core/)** | Foundation & Power Mode | 11 | Project setup, plugin management, orchestration |
| **[popkit-dev](packages/popkit-dev/)** | Development workflows | 7 | Daily dev, git, GitHub, routines |
| **[popkit-ops](packages/popkit-ops/)** | Operations & quality | 5 | Testing, debugging, security, deployment |
| **[popkit-research](packages/popkit-research/)** | Knowledge management | 2 | Research capture, knowledge base |

**Foundation**: `popkit-shared` (v1.0.0) - 70 shared Python utility modules

---

## ⚡ Quick Start

**Step 1: Add the PopKit marketplace (one-time setup)**
```bash
/plugin marketplace add jrc1883/popkit-claude
```

**Step 2: Install PopKit plugins**

```bash
# Install all plugins for full functionality
/plugin install popkit-core@popkit-claude
/plugin install popkit-dev@popkit-claude
/plugin install popkit-ops@popkit-claude
/plugin install popkit-research@popkit-claude

# Restart Claude Code
```

**Or install selectively:**
- `popkit-core` - Foundation (account, stats, Power Mode) - 11 commands
- `popkit-dev` - Development workflows (git, GitHub, routines) - 7 commands
- `popkit-ops` - Operations & quality (testing, security, deploy) - 5 commands
- `popkit-research` - Knowledge management (research, notes) - 2 commands

**Minimum**: popkit-core (9 commands)
**Recommended**: popkit-core + popkit-dev (16 commands)
**Complete**: All 4 plugins (23 commands)

---

## 🚀 Core Workflows

### Feature Development

```bash
# Start development workflow
/popkit-dev:dev "Add user authentication"
  → Brainstorm → Plan → Implement → Review → PR

# Daily routines
/popkit-dev:routine morning    # Health check + "Ready to Code" score
/popkit-dev:routine nightly    # Cleanup + "Sleep Score"

# Context-aware help
/popkit-dev:next              # What should I do next?
```

### Git Operations

```bash
# Smart commits
/popkit-dev:git commit        # Auto-generates conventional commit message

# Pull requests
/popkit-dev:git pr            # Creates PR with summary + checklist

# Code review
/popkit-dev:git review        # In-depth code review with suggestions
```

### Quality Assurance

```bash
# Multi-perspective assessment
/popkit-ops:assess all        # Run 6 specialized assessors

# Systematic debugging
/popkit-ops:debug "login fails on mobile"

# Security scanning
/popkit-ops:security scan     # Find vulnerabilities + create issues
```

### Deployment

```bash
# Universal deployment
/popkit-ops:deploy init       # Configure deployment targets
/popkit-ops:deploy execute    # Ship to Docker/npm/Vercel/etc.
```

---

## 🏗️ Repository Structure

```
popkit/
├── packages/
│   ├── popkit-core/        # Foundation plugin (Power Mode, config)
│   ├── popkit-dev/         # Development workflows (git, GitHub, routines)
│   ├── popkit-ops/         # Operations & quality (test, debug, deploy)
│   ├── popkit-research/    # Knowledge management (research, notes)
│   ├── shared-py/          # Shared Python utilities (70 modules)
│   └── docs/               # Documentation site (Astro + Starlight)
├── docs/                   # Technical guides and documentation
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

PopKit is in active development. We welcome contributions!

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'feat: add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Development Resources
- [GitHub Issues](https://github.com/jrc1883/popkit-claude/issues)
- [CLAUDE.md](CLAUDE.md) - Development guide
- [Contributing Guidelines](CONTRIBUTING.md)

---

## 👥 Contributors

Thanks to all the amazing people who have contributed to PopKit!

<!-- ALL-CONTRIBUTORS-LIST:START -->
<table>
  <tr>
    <td align="center">
      <a href="https://github.com/jrc1883">
        <img src="https://github.com/jrc1883.png" width="100px;" alt="Joseph Cannon"/>
        <br />
        <sub><b>Joseph Cannon</b></sub>
      </a>
      <br />
      <sub>Creator & Maintainer</sub>
    </td>
  </tr>
</table>
<!-- ALL-CONTRIBUTORS-LIST:END -->

*Want to see your name here? Check out our [contributing guidelines](#-contributing)!*

---

## 📈 Star History

<a href="https://star-history.com/#jrc1883/popkit-claude&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=jrc1883/popkit-claude&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=jrc1883/popkit-claude&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=jrc1883/popkit-claude&type=Date" />
  </picture>
</a>

---

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 👤 Author

**Joseph Cannon**
📧 <joseph@thehouseofdeals.com>
🐙 [GitHub](https://github.com/jrc1883)

---

<div align="center">

**Ready to supercharge your development workflow?**

```bash
# Add marketplace (one-time)
/plugin marketplace add jrc1883/popkit-claude

# Install all PopKit plugins
/plugin install popkit-core@popkit-claude
/plugin install popkit-dev@popkit-claude
/plugin install popkit-ops@popkit-claude
/plugin install popkit-research@popkit-claude
```

Then restart Claude Code and run `/popkit-dev:next` to get started!

**[⬆ Back to Top](#popkit)**

</div>
