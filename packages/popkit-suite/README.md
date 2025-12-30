# PopKit Suite - Complete Installation

**Version:** 1.0.0-beta.1
**Status:** Meta-Plugin (Phase 4 of Plugin Modularization)

## Overview

PopKit Suite is a meta-plugin that guides you through installing the complete PopKit ecosystem. This plugin provides **recommendations and documentation only** - it does not contain any commands, skills, or agents itself.

**Think of this as:** An installation guide that lives in your Claude Code plugin list.

## What You Get

When you follow the installation guide below, you'll have access to **all 23 commands** across 4 focused plugins:

- **9 commands** - Foundation (popkit-core)
- **7 commands** - Development (popkit-dev)
- **5 commands** - Operations (popkit-ops)
- **2 commands** - Research (popkit-research)

**Total: 23 commands, 38 skills, 21 agents**

## Quick Install (Complete Suite)

Install all 4 PopKit plugins to get the full functionality:

```bash
# 1. Foundation (required for others)
/plugin install popkit-core@popkit-marketplace

# 2. Development workflows
/plugin install popkit-dev@popkit-marketplace

# 3. Operations and quality assurance
/plugin install popkit-ops@popkit-marketplace

# 4. Research and knowledge management
/plugin install popkit-research@popkit-marketplace
```

**Restart Claude Code** after installation to load all plugins.

## What Each Plugin Provides

### popkit-core (Foundation)

**9 commands:** Account management and system features

- `/popkit:plugin` - Plugin testing and validation
- `/popkit:stats` - Usage metrics and efficiency tracking
- `/popkit:privacy` - Privacy settings and data controls
- `/popkit:account` - Manage API key, subscription, billing
- `/popkit:dashboard` - Multi-project management
- `/popkit:bug` - Bug reporting and diagnostics
- `/popkit:power` - Multi-agent orchestration
- `/popkit:project` - Project analysis and initialization
- `/popkit:record` - Session recording and playback

**14 skills, 9 agents** including power-coordinator, api-designer, accessibility-guardian.

**Install first** - other plugins recommend this for account features.

### popkit-dev (Development)

**7 commands:** Complete development workflows

- `/popkit:dev` - 7-phase feature development
- `/popkit:git` - Git operations (commit, push, pr, review, ci, release, publish)
- `/popkit:issue` - GitHub issue management
- `/popkit:milestone` - Milestone tracking
- `/popkit:worktree` - Git worktree management
- `/popkit:routine` - Morning health checks, nightly cleanup
- `/popkit:next` - Context-aware next action recommendations

**12 skills, 5 agents** including code-reviewer, code-architect, refactoring-expert.

### popkit-ops (Operations)

**5 commands:** Quality assurance and deployment

- `/popkit:assess` - Code quality assessments
- `/popkit:audit` - Quarterly/yearly health audits
- `/popkit:debug` - Systematic debugging workflows
- `/popkit:security` - Security scanning and fixes
- `/popkit:deploy` - Deployment orchestration

**7 skills, 6 agents** including security-auditor, performance-optimizer, bug-whisperer, test-writer-fixer.

### popkit-research (Knowledge)

**2 commands:** Research and knowledge management

- `/popkit:research` - Research capture and search
- `/popkit:knowledge` - Knowledge base management

**3 skills, 1 agent** (researcher for meta-analysis).

## Selective Installation

Don't need everything? Install only what you need:

### Minimal Setup (Foundation Only)
```bash
/plugin install popkit-core@popkit-marketplace
```
Gets: Account, stats, privacy, bug reporting, power mode, project tools (9 commands)

### Developer Setup
```bash
/plugin install popkit-core@popkit-marketplace
/plugin install popkit-dev@popkit-marketplace
```
Gets: Foundation + Development (16 commands)

### DevOps Engineer Setup
```bash
/plugin install popkit-core@popkit-marketplace
/plugin install popkit-dev@popkit-marketplace
/plugin install popkit-ops@popkit-marketplace
```
Gets: Foundation + Dev + Ops (21 commands)

## Migration from Monolithic PopKit

If you're upgrading from the old monolithic popkit plugin (v0.2.x):

### Option 1: Keep Everything (Recommended)

```bash
# 1. Uninstall old monolithic version
/plugin uninstall popkit@popkit-marketplace

# 2. Install new modular plugins
/plugin install popkit-core@popkit-marketplace
/plugin install popkit-dev@popkit-marketplace
/plugin install popkit-ops@popkit-marketplace
/plugin install popkit-research@popkit-marketplace

# 3. Restart Claude Code
```

You'll have the same 23 commands, just organized across 4 plugins instead of 1.

### Option 2: Selective Migration

Install only the plugins you actually use:

```bash
# Uninstall old version
/plugin uninstall popkit@popkit-marketplace

# Install selectively
/plugin install popkit-core@popkit-marketplace       # Always install foundation
/plugin install popkit-dev@popkit-marketplace        # If you use dev workflows
/plugin install popkit-ops@popkit-marketplace        # If you use quality/deployment
/plugin install popkit-research@popkit-marketplace   # If you use research capture
```

### What Changed?

**Good news:** All commands work identically! The only change is organization:

| Old (Monolithic) | New (Modular) |
|------------------|---------------|
| 1 plugin | 4 focused plugins |
| 24 commands | 23 commands (rationalized) |
| ~100k tokens | ~85k tokens (optimized) |
| Install all or nothing | Install what you need |

**No breaking changes** - all command behavior is preserved.

## Why Modular?

### Benefits of the New Architecture

1. **Faster Installation** - Install only what you need
2. **Reduced Context Usage** - Only load plugins you're using
3. **Clearer Organization** - Plugins grouped by workflow
4. **Independent Updates** - Update plugins separately
5. **Skills Sharing** - Skills from any plugin available to all agents

### How Skills Work

**Important:** Skills are **globally available** once installed by any plugin!

Example:
```bash
# Install just two plugins
/plugin install popkit-dev       # Provides code-reviewer agent
/plugin install popkit-ops       # Provides security-scan skill

# Now code-reviewer can use security-scan!
# No duplication needed - skills are shared automatically
```

This is a core Claude Code feature that enables true modularity.

## Architecture Overview

```
PopKit Ecosystem (Modular Architecture)

popkit-core (foundation)
├── 9 commands: plugin, stats, privacy, account, dashboard, bug, power, project, record
├── 14 skills: project analysis, documentation, meta-features
├── 9 agents: api-designer, accessibility-guardian, power-coordinator, etc.
└── Size: ~30k tokens

popkit-dev (development)
├── 7 commands: dev, git, issue, milestone, worktree, routine, next
├── 12 skills: brainstorming, planning, execution, session management, templates, worktrees
├── 5 agents: code-explorer, code-architect, code-reviewer, refactoring-expert, rapid-prototyper
└── Size: ~25k tokens

popkit-ops (operations)
├── 5 commands: assess, audit, debug, security, deploy
├── 7 skills: 5 assessment types + systematic debugging + code review
├── 6 agents: security-auditor, performance-optimizer, bug-whisperer, test-writer-fixer, deployment-validator, rollback-specialist
└── Size: ~20k tokens

popkit-research (knowledge)
├── 2 commands: research, knowledge
├── 3 skills: capture, merge, lookup
├── 1 agent: researcher
└── Size: ~10k tokens

popkit-suite (meta) ← You are here
├── 0 commands (documentation only)
├── 0 skills (documentation only)
├── 0 agents (documentation only)
└── Size: ~5k tokens (this README)
```

## Frequently Asked Questions

### Do I need all 4 plugins?

No! Install only what you need. The foundation plugin (popkit) is recommended for account management, but the others are optional.

### Can I mix and match?

Yes! All plugins work independently. Install any combination that fits your workflow.

### What about dependencies?

Claude Code doesn't support plugin dependencies, so each plugin is self-contained. However, some plugins *recommend* others for enhanced functionality (e.g., popkit-dev recommends popkit for account features).

### How do updates work?

Each plugin has its own version number. Update them independently:
```bash
/plugin update popkit-core@popkit-marketplace
/plugin update popkit-dev@popkit-marketplace
```

### Can I uninstall individual plugins?

Yes! Uninstall any plugin you're not using:
```bash
/plugin uninstall popkit-research@popkit-marketplace
```

The other plugins will continue to work normally.

### What happened to the old monolithic plugin?

The old monolithic popkit (v0.2.x) is deprecated in favor of this modular architecture. Existing users should migrate to the new plugins using the guide above.

## Troubleshooting

### Command not found after installation

**Solution:** Restart Claude Code to load the newly installed plugins.

### Still seeing old commands

**Solution:** Uninstall the old monolithic popkit first, then install the new modular plugins.

### Plugins seem to duplicate functionality

**Clarification:** While plugins bundle Python utilities separately, **skills are shared globally**. There's no functional duplication - each plugin provides unique commands and capabilities.

## Support

- **Documentation:** See individual plugin READMEs
- **Bug Reports:** `/popkit:bug report` (requires popkit foundation)
- **Feature Requests:** GitHub Issues
- **Community:** PopKit Cloud (coming soon)

## License

MIT

## Credits

PopKit is developed by Joseph Cannon and the PopKit community.

---

**Ready to get started?** Scroll up to the Quick Install section and install all 4 plugins!
