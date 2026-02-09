# PopKit

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0--beta.8-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Build Status](https://img.shields.io/github/actions/workflow/status/jrc1883/popkit-claude/ci.yml?branch=main)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![TypeScript](https://img.shields.io/badge/typescript-5.0+-blue.svg)
![Claude Code](https://img.shields.io/badge/Claude%20Code-2.1.33+-purple.svg)

**AI-powered development workflows for Claude Code**

Transform Claude Code into a complete development workflow system with intelligent agents, parallel execution, and GitHub-first automation.

[Quick Start](#-quick-start) ·
[Features](#-features) ·
[Documentation](https://popkit.dev) ·
[Contributing](#-contributing)

</div>

---

## Why PopKit?

| Challenge | PopKit Solution |
|-----------|-----------------|
| **Multiple AI subscriptions** | One Claude subscription runs coordinated multi-agent workflows |
| **Tool fatigue** | Zero new tools—PopKit lives inside Claude Code |
| **Context bloat** | Embedding-based routing reduced baseline by 40% (25.7k → 15.3k tokens) |
| **Manual coordination** | Power Mode runs specialized agents in parallel automatically |
| **Broken workflows** | GitHub issues → tasks → PRs → reviews, all automated |
| **Quality gaps** | 6 specialized assessors ensure production-ready code |

---

## Quick Start

**30 seconds to get started:**

```bash
# Step 1: Add the PopKit marketplace (one-time)
/plugin marketplace add jrc1883/popkit-claude

# Step 2: Install plugins
/plugin install popkit-core@popkit-claude
/plugin install popkit-dev@popkit-claude
/plugin install popkit-ops@popkit-claude
/plugin install popkit-research@popkit-claude

# Step 3: Restart Claude Code, then run:
/popkit-dev:next
```

**Install what you need:**

| Plugins | Commands | Best For |
|---------|----------|----------|
| `popkit-core` only | 11 | Power Mode, project setup |
| + `popkit-dev` | 18 | Daily development workflows |
| + `popkit-ops` | 23 | Testing, security, deployment |
| + `popkit-research` | 25 | Full feature set |

---

## Features

### Development Workflows

```bash
/popkit-dev:dev "Add user authentication"
```

7-phase guided workflow: **Discovery → Exploration → Questions → Architecture → Implementation → Review → Summary**

### Daily Routines

```bash
/popkit-dev:routine morning    # "Ready to Code" score (0-100)
/popkit-dev:routine nightly    # "Sleep Score" + cleanup
```

Automated health checks, dependency updates, and context restoration.

### Git Operations

```bash
/popkit-dev:git commit        # Smart conventional commits
/popkit-dev:git pr            # PR with summary + checklist
/popkit-dev:git review        # In-depth code review
```

### Quality Assurance

```bash
/popkit-ops:assess all        # 6 specialized assessors
/popkit-ops:debug "issue"     # Systematic debugging
/popkit-ops:security scan     # Vulnerability detection
```

### Power Mode

Multi-agent orchestration for complex tasks:

- **Native Async**: 5+ agents via background tasks (zero setup)
- **Redis Mode**: 10+ agents with persistent coordination
- **File-Based**: 2 agents sequential (zero setup)

```bash
/popkit-core:power start --agents 5
```

---

## Architecture

```
popkit-claude/
├── packages/
│   ├── popkit-core/        # Foundation (Power Mode, config, project tools)
│   ├── popkit-dev/         # Development (git, GitHub, routines)
│   ├── popkit-ops/         # Operations (test, debug, security, deploy)
│   ├── popkit-research/    # Knowledge (research capture, notes)
│   ├── shared-py/          # 70 shared Python utility modules
│   └── docs/               # Documentation site (Astro + Starlight)
```

### By The Numbers

| Component | Count | Description |
|-----------|-------|-------------|
| **Plugins** | 4 | Modular, install what you need |
| **Commands** | 25 | Slash commands for workflows |
| **Skills** | 43 | Reusable automation patterns |
| **Agents** | 23 | Specialized AI assistants |
| **Python Modules** | 70 | Shared utilities |

### Plugin Details

| Plugin | Purpose | Key Commands |
|--------|---------|--------------|
| **popkit-core** | Foundation & orchestration | `/power`, `/project`, `/stats` |
| **popkit-dev** | Development workflows | `/dev`, `/git`, `/routine`, `/next` |
| **popkit-ops** | Operations & quality | `/assess`, `/debug`, `/security`, `/deploy` |
| **popkit-research** | Knowledge management | `/research`, `/knowledge` |

---

## Requirements

- **Claude Code 2.1.33+** (recommended for full feature support)
- **Python 3.11+** (for hooks and utilities)
- **Git** (for version control workflows)
- **GitHub CLI (`gh`)** (for GitHub integration)

---

## Documentation

- **[Full Documentation](https://popkit.dev)** - Comprehensive guides
- **[CLAUDE.md](CLAUDE.md)** - Development instructions
- **[CHANGELOG.md](CHANGELOG.md)** - Version history
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines

### Plugin READMEs

- [popkit-core](packages/popkit-core/README.md) - Foundation & Power Mode
- [popkit-dev](packages/popkit-dev/README.md) - Development workflows
- [popkit-ops](packages/popkit-ops/README.md) - Operations & quality
- [popkit-research](packages/popkit-research/README.md) - Knowledge management

---

## Contributing

We welcome contributions! See our [Contributing Guidelines](CONTRIBUTING.md).

```bash
# Clone and install locally
git clone https://github.com/jrc1883/popkit-claude.git
cd popkit-claude

# Install plugins for local development
/plugin install ./packages/popkit-core
/plugin install ./packages/popkit-dev
/plugin install ./packages/popkit-ops
/plugin install ./packages/popkit-research

# Run tests
cd packages/popkit-core && python run_all_tests.py
```

---

## Current Status

**Version:** 1.0.0-beta.8
**Status:** Public beta

All core features are stable and tested. We're actively improving documentation and gathering user feedback.

**Recent Updates:**
- Claude Code 2.1.33 compatibility (Agent Teams, Agent Memory, new hook events)
- Embedding-based agent routing (40% context reduction)
- GitHub cache integration for faster operations
- 6 open issues, 4 pending dependency PRs

See [CHANGELOG.md](CHANGELOG.md) for full version history.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Author

**Joseph Cannon**

- Email: joseph@thehouseofdeals.com
- GitHub: [@jrc1883](https://github.com/jrc1883)

---

<div align="center">

**Ready to supercharge your Claude Code workflow?**

```bash
/plugin marketplace add jrc1883/popkit-claude
/plugin install popkit-core@popkit-claude
```

**[Back to Top](#popkit)**

</div>
