---
name: install
namespace: popkit-suite
description: Interactive guide to install PopKit plugins based on your needs
aliases: [setup, get-started]
---

# PopKit Suite Installation Guide

Welcome to PopKit! This guide will help you install the right plugins for your workflow.

## Quick Install Options

### Option 1: Complete Suite (Recommended for New Users)

Install all 4 PopKit plugins for full functionality:

```
/plugin install popkit-core@popkit-marketplace
/plugin install popkit-dev@popkit-marketplace
/plugin install popkit-ops@popkit-marketplace
/plugin install popkit-research@popkit-marketplace
```

**What you get:** All 23 commands, 38 skills, 22 agents

**Then:** Restart Claude Code to load the plugins

---

### Option 2: Selective Installation

**Choose based on your role:**

#### For Developers (Foundation + Development)
```
/plugin install popkit-core@popkit-marketplace
/plugin install popkit-dev@popkit-marketplace
```
**Commands:** 18 total (project setup, git, GitHub, routines, feature dev)

#### For DevOps Engineers (Foundation + Dev + Ops)
```
/plugin install popkit-core@popkit-marketplace
/plugin install popkit-dev@popkit-marketplace
/plugin install popkit-ops@popkit-marketplace
```
**Commands:** 23 total (adds testing, debugging, security, deployment)

#### For Researchers (Foundation + Research)
```
/plugin install popkit-core@popkit-marketplace
/plugin install popkit-research@popkit-marketplace
```
**Commands:** 13 total (project setup + knowledge management)

#### Minimal Setup (Foundation Only)
```
/plugin install popkit-core@popkit-marketplace
```
**Commands:** 11 total (project analysis, plugin management, Power Mode)

---

## What Each Plugin Provides

### 🎯 popkit-core (Foundation)
**11 commands** - Required for full functionality

Core features: Project analysis, plugin management, Power Mode orchestration, stats, privacy, account management, dashboard

**Install this first** - Recommended for all users

### 🛠️ popkit-dev (Development)
**7 commands** - Development workflows

Features: 7-phase feature development, smart git operations, GitHub integration, daily routines, context-aware recommendations

**Best for:** Daily development work, git/GitHub workflows

### 🔧 popkit-ops (Operations)
**5 commands** - Quality assurance and deployment

Features: Multi-perspective code assessments, systematic debugging, security scanning, deployment orchestration

**Best for:** Testing, quality assurance, DevOps, deployment

### 📚 popkit-research (Knowledge)
**2 commands** - Research and knowledge management

Features: Research capture, semantic search, knowledge base

**Best for:** Documentation, learning, knowledge management

---

## After Installation

1. **Restart Claude Code** to load the plugins
2. Run `/popkit:next` to get started (if you installed popkit-dev)
3. Run `/popkit:project analyze` to analyze your current project
4. Explore available commands with `/help`

## Getting Help

- List all commands: `/help` and look for `/popkit:*` commands
- Plugin management: `/popkit:plugin test` (test your installation)
- Documentation: See individual plugin READMEs in the repository

## Troubleshooting

### Commands not found after installation?
**Solution:** Restart Claude Code

### Which plugins do I need?
- **Minimum:** popkit-core (11 commands)
- **Recommended:** popkit-core + popkit-dev (18 commands)
- **Complete:** All 4 plugins (23 commands)

### Can I uninstall plugins later?
Yes! Use `/plugin uninstall <plugin-name>@popkit-marketplace`

---

**Ready to install?** Choose an option above and copy the installation commands!
