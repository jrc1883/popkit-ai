# PopKit - Foundation Plugin

**Version:** 1.0.0-beta.1
**Status:** Foundation Plugin (Phase 3a of Plugin Modularization)

## Overview

PopKit is the foundation plugin for the PopKit ecosystem. It provides essential system features that all other PopKit plugins conceptually depend on: account management, usage statistics, privacy controls, bug reporting, and premium feature validation.

**This is the first plugin you should install** when using any PopKit workflows.

## Features

### Commands (7)

| Command | Description |
|---------|-------------|
| `/popkit:account` | Manage API key, subscription status, billing, logout |
| `/popkit:stats` | Usage metrics and efficiency tracking |
| `/popkit:privacy` | Privacy settings and data controls |
| `/popkit:bug` | Bug reporting, diagnostics, and issue search |
| `/popkit:plugin` | Plugin testing, validation, and management |
| `/popkit:cache` | Cache management and cleanup |
| `/popkit:upgrade` | Premium features and pricing information |

### No Skills or Agents

This plugin is intentionally minimal - it provides only command execution without autonomous agents or reusable skills. This keeps it lightweight and fast to install.

## Installation

```bash
# Local installation during development
/plugin install popkit@file:./packages/popkit

# Future: Marketplace installation (when published)
/plugin install popkit@popkit-marketplace
```

## Dependencies

- **popkit-shared** (>= 0.1.0) - Shared utility modules
- **Python** (>= 3.8)
- **PopKit Cloud API** (optional) - For premium features

## Architecture

PopKit is part of PopKit's modular plugin architecture:

```
popkit (foundation)           ← You are here
├── Account management
├── Usage statistics
├── Privacy controls
├── Bug reporting
├── Plugin testing
├── Cache management
└── Premium features

popkit-dev (development)
├── Feature development
├── Git operations
├── GitHub integration
└── Daily routines

popkit-ops (operations)
├── Quality assessment
├── Security auditing
├── Debugging workflows
└── Deployment automation

popkit-research (knowledge)
├── Research capture
└── Knowledge management

popkit-suite (meta-plugin)
└── Installs all 4 plugins above
```

## Usage Examples

### Account Management

```bash
# View account status
/popkit:account status

# Configure API key
/popkit:account keys

# View billing information
/popkit:account billing

# Logout (clear API key)
/popkit:account logout
```

### Usage Statistics

```bash
# View current session stats
/popkit:stats session

# View today's stats
/popkit:stats today

# View weekly stats
/popkit:stats week

# View cloud-synced stats (requires API key)
/popkit:stats cloud

# Reset local statistics
/popkit:stats reset
```

### Privacy Controls

```bash
# View current privacy status
/popkit:privacy status

# Update consent preferences
/popkit:privacy consent

# Export your data
/popkit:privacy export

# Delete your data
/popkit:privacy delete

# Set privacy level (strict/moderate/minimal)
/popkit:privacy level strict
```

### Bug Reporting

```bash
# Report a bug
/popkit:bug report

# Search for existing bugs
/popkit:bug search "authentication"

# Share diagnostic information
/popkit:bug share
```

### Plugin Management

```bash
# Test plugin structure
/popkit:plugin test

# Generate plugin documentation
/popkit:plugin docs

# Sync README with auto-generated sections
/popkit:plugin sync

# Detect project-specific opportunities
/popkit:plugin detect

# Manage plugin versions
/popkit:plugin version
```

### Cache Management

```bash
# View cache status (coming soon)
/popkit:cache status

# Clear cache (coming soon)
/popkit:cache clear
```

### Premium Features

```bash
# View premium features
/popkit:upgrade

# Upgrade to Pro tier
/popkit:upgrade pro

# Upgrade to Team tier
/popkit:upgrade team

# Open pricing page
/popkit:upgrade --open
```

## Integration with PopKit Cloud

PopKit connects to **PopKit Cloud** (Cloudflare Workers at `api.thehouseofdeals.com`) for:

- **Subscription validation** - Check premium tier entitlements
- **Usage analytics** - Sync statistics across devices (optional)
- **Pattern learning** - Community knowledge sharing (optional, anonymized)
- **Cross-project insights** - Learn from your workflow patterns

**All cloud features are optional.** PopKit works fully offline without an API key.

### Configuring API Key

```bash
/popkit:account keys
# Follow prompts to enter your API key
```

API keys are stored in `~/.popkit/config.json` and used by all PopKit plugins.

## Premium Features

PopKit offers two tiers:

### Free Tier (No API Key)
- All 7 commands available
- Local statistics tracking
- Local privacy controls
- Bug reporting (anonymous)
- Plugin testing tools
- Local cache management

### Pro Tier (With API Key)
- Everything in Free
- Cloud-synced statistics
- Cross-device analytics
- Pattern learning from community
- Priority support
- Early access to new features

**Pricing:** See `/popkit:upgrade` for current pricing

## File Structure

```
packages/popkit/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest
├── commands/
│   ├── account.md           # Account management
│   ├── stats.md             # Usage statistics
│   ├── privacy.md           # Privacy controls
│   ├── bug.md               # Bug reporting
│   ├── plugin.md            # Plugin testing
│   ├── cache.md             # Cache management
│   └── upgrade.md           # Premium features
├── README.md                # This file
└── CHANGELOG.md             # Version history
```

## Testing Strategy

1. ✅ Package structure created
2. ✅ Commands extracted from monolithic plugin
3. ✅ plugin.json created with 7 commands
4. ⏳ Local installation test
5. ⏳ Command functionality validation
6. ⏳ API key configuration test
7. ⏳ Cloud API integration test

## Success Metrics

- [ ] All 7 commands work identically to monolithic version
- [ ] Installation < 30 seconds
- [ ] No context window increase
- [ ] Clean uninstall
- [ ] API key management works
- [ ] Premium validation works

## Issues

- **This plugin**: Issue #584 (Extract popkit foundation)
- **Parent Epic**: Issue #580 (Plugin Modularization)
- **Dependencies**: Issues #570 (shared-py - COMPLETED)

## Related Plugins

When you need more capabilities, install additional PopKit plugins:

```bash
# For development workflows
/plugin install popkit-dev@popkit-marketplace

# For quality assurance and deployment
/plugin install popkit-ops@popkit-marketplace

# For knowledge management
/plugin install popkit-research@popkit-marketplace

# Or install everything
/plugin install popkit-suite@popkit-marketplace
```

## License

MIT

## Support

- **Documentation:** See command files in `commands/`
- **Bug Reports:** `/popkit:bug report`
- **Feature Requests:** GitHub Issues
- **Community:** PopKit Cloud (coming soon)
