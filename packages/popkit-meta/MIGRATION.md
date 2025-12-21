# PopKit Migration Guide

This guide explains how to migrate from the monolithic PopKit plugin to the new modular architecture.

## Overview

PopKit has been split into 7 focused plugins:

| Plugin | Purpose | Commands | When to Use |
|--------|---------|----------|-------------|
| **popkit-dev** | Development workflows | 5 | Feature dev, git, routines |
| **popkit-github** | GitHub integration | 2 | Issues, milestones |
| **popkit-quality** | Testing & debugging | 4 | QA, security, assessments |
| **popkit-deploy** | Deployment automation | 1 | Deploy to any platform |
| **popkit-research** | Knowledge management | 2 | Research, notes |
| **popkit-core** | Meta features | 10 | Project setup, Power Mode |
| **popkit (meta)** | All plugins | 24 | One-click install |

## Migration Options

### Option 1: Meta-Plugin (Recommended for Most Users)

**Best for**: Users who want everything with minimal changes.

```bash
# Uninstall old monolithic plugin
/plugin uninstall popkit

# Install meta-plugin (installs all 6 plugins)
/plugin install popkit@popkit-marketplace

# Restart Claude Code
```

**Result**: All commands work exactly as before under `/popkit:` namespace.

### Option 2: Selective Installation

**Best for**: Users who only need specific features.

```bash
# Uninstall old monolithic plugin
/plugin uninstall popkit

# Install only what you need
/plugin install popkit-dev@popkit-marketplace        # Development workflows
/plugin install popkit-github@popkit-marketplace     # GitHub integration
/plugin install popkit-quality@popkit-marketplace    # Testing & debugging
/plugin install popkit-deploy@popkit-marketplace     # Deployment
/plugin install popkit-research@popkit-marketplace   # Research
/plugin install popkit-core@popkit-marketplace       # Core utilities

# Restart Claude Code
```

**Result**: Only selected commands available, smaller context window usage.

### Option 3: Hybrid Approach

Install the meta-plugin, then uninstall plugins you don't need:

```bash
# Install everything
/plugin install popkit@popkit-marketplace

# Remove plugins you don't use
/plugin uninstall popkit-deploy     # If you don't deploy
/plugin uninstall popkit-research   # If you don't use research features

# Restart Claude Code
```

## Command Mapping

All commands remain under the `/popkit:` namespace. No changes to your workflows!

### Development Workflows (popkit-dev)
- `/popkit:dev` - Feature development
- `/popkit:git` - Git operations
- `/popkit:worktree` - Git worktree management
- `/popkit:routine` - Morning/nightly routines
- `/popkit:next` - Context-aware recommendations

### GitHub Integration (popkit-github)
- `/popkit:issue` - Issue management
- `/popkit:milestone` - Milestone tracking

### Quality Assurance (popkit-quality)
- `/popkit:assess` - Multi-perspective assessment
- `/popkit:audit` - Project audits
- `/popkit:debug` - Systematic debugging
- `/popkit:security` - Security scanning

### Deployment (popkit-deploy)
- `/popkit:deploy` - Universal deployment

### Research (popkit-research)
- `/popkit:research` - Research management
- `/popkit:knowledge` - Knowledge base

### Core Utilities (popkit-core)
- `/popkit:plugin` - Plugin management
- `/popkit:stats` - Statistics
- `/popkit:privacy` - Privacy controls
- `/popkit:account` - Account management
- `/popkit:upgrade` - Upgrade to premium
- `/popkit:dashboard` - Multi-project dashboard
- `/popkit:workflow-viz` - Workflow visualization
- `/popkit:bug` - Bug reporting
- `/popkit:power` - Power Mode
- `/popkit:project` - Project analysis

## What Changed?

### Structure
- **Before**: One monolithic `popkit` plugin (235 Python files)
- **After**: 6 focused plugins + 1 shared foundation + 1 meta-plugin

### Installation
- **Before**: Install `popkit` → get everything
- **After**:
  - Install `popkit` (meta) → get everything (backwards compatible)
  - OR install individual plugins → get only what you need

### Context Window
- **Before**: All 27 commands, 73 skills, 31 agents loaded always
- **After**:
  - Meta-plugin: Same as before
  - Selective: Only chosen plugins loaded (smaller context)

### Functionality
- **No breaking changes**: All commands work identically
- **No namespace changes**: Still `/popkit:command`
- **No API changes**: Hooks, skills, agents unchanged

## Troubleshooting

### "Command not found" after migration

**Cause**: Plugin not installed or Claude Code not restarted.

**Fix**:
1. Check installed plugins: `/plugin list`
2. Install missing plugin: `/plugin install popkit-<name>@popkit-marketplace`
3. Restart Claude Code

### Version mismatch warnings

**Cause**: Sub-plugins have different versions.

**Fix**:
```bash
# Update all to latest
/plugin update popkit-dev
/plugin update popkit-github
/plugin update popkit-quality
/plugin update popkit-deploy
/plugin update popkit-research
/plugin update popkit-core

# Or reinstall meta-plugin
/plugin uninstall popkit
/plugin install popkit@popkit-marketplace
```

### Some features missing

**Cause**: Not all plugins installed.

**Fix**:
- Check which plugins you have: `/plugin list`
- Install meta-plugin for complete suite: `/plugin install popkit@popkit-marketplace`
- Or install specific missing plugin

## Recommended Migration Path

For most users, we recommend:

1. **Week 1-2**: Install meta-plugin
   - No changes to workflow
   - Backwards compatible
   - Test that everything works

2. **Week 3+**: Evaluate selective installation
   - Review which plugins you actually use
   - Uninstall unused plugins to reduce context
   - Or switch to individual plugin installation

## FAQ

### Q: Will the monolithic plugin continue to be maintained?

**A**: No. The monolithic plugin is deprecated. All future updates will be to the modular plugins.

### Q: Do I have to migrate?

**A**: Yes, eventually. The monolithic plugin won't receive updates. But migration is seamless via the meta-plugin.

### Q: Can I use both old and new plugins?

**A**: No. Uninstall the old monolithic plugin before installing the new ones to avoid conflicts.

### Q: What if I only use 2-3 commands?

**A**: Install only the plugins you need! For example, if you only use git and deploy:
```bash
/plugin install popkit-dev@popkit-marketplace      # Has /popkit:git
/plugin install popkit-deploy@popkit-marketplace   # Has /popkit:deploy
```

### Q: Does this affect my API key or cloud features?

**A**: No. API keys work across all plugins. Cloud features are unchanged.

### Q: What about custom configurations in `.claude/`?

**A**: All configurations remain compatible. No changes needed.

## Support

- **Issues**: https://github.com/jrc1883/popkit/issues
- **Migration help**: `/popkit:bug report "Migration issue: ..."`
- **Documentation**: See individual plugin READMEs in `packages/popkit-*/`

## Version Timeline

- **v0.1.0** (December 2025): Beta release of modular plugins
- **v1.0.0** (Q1 2026): Stable release, monolithic plugin deprecated
- **v1.x.x** (2026+): Only modular plugins maintained

---

**Last Updated**: 2025-12-20
