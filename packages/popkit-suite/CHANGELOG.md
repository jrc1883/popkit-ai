# Changelog

All notable changes to PopKit Suite will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0-beta.1] - 2025-12-21

### Added

- Initial release as meta-plugin for complete PopKit ecosystem
- Comprehensive installation guide for all 4 PopKit plugins
- Migration guide from monolithic popkit (v0.2.x)
- Documentation of selective vs complete installation options
- FAQ section covering common questions
- Troubleshooting guide for installation issues

### Architecture

- **Plugin type:** Meta (documentation and recommendations only)
- **Commands:** 0 (no executable commands)
- **Skills:** 0 (documentation only)
- **Agents:** 0 (documentation only)
- **Size:** Minimal (~5k tokens, just README documentation)

### Documentation Provided

- Quick install guide for all 4 plugins
- Detailed breakdown of what each plugin provides
- Selective installation scenarios (minimal, developer, devops)
- Migration instructions from monolithic version
- Architecture overview of modular plugin system
- FAQ covering plugin dependencies, updates, and mixing plugins
- Troubleshooting section for common issues

### Recommended Plugins

This meta-plugin recommends installing:

1. **popkit** (foundation) - 7 commands
   - Account, stats, privacy, bug, plugin, cache, upgrade

2. **popkit-dev** (development) - 7 commands
   - dev, git, issue, milestone, worktree, routine, next
   - 10 skills, 5 agents

3. **popkit-ops** (operations) - 5 commands
   - assess, audit, debug, security, deploy
   - 6 skills, 6 agents

4. **popkit-research** (knowledge) - 2 commands
   - research, knowledge
   - 3 skills, 1 agent

**Total when all installed:** 21 commands, 19 skills, 13 agents

### Why This Exists

Claude Code does NOT support plugin dependencies, so this meta-plugin serves as:
- Installation guide for the complete suite
- Migration documentation for existing users
- Reference for understanding the modular architecture
- Quick-start documentation for new users

### Integration

- Does not install other plugins automatically (not supported by Claude Code)
- Provides clear instructions for manual installation
- Documents how skills are globally available across plugins
- Explains how plugins work together despite being independent

### Issues

- Implements Issue #587: Create popkit-suite meta-plugin
- Supersedes Issue #577: Create meta-plugin for backwards compatibility (old architecture)
- Completes Epic #580: PopKit Plugin Modularization

### Future

As the PopKit ecosystem grows, this README will be updated to include:
- New plugins as they're released
- Updated migration guides
- Expanded FAQ based on user feedback
- Installation automation (if Claude Code adds dependency support)

[1.0.0-beta.1]: https://github.com/jrc1883/popkit/releases/tag/popkit-suite-v1.0.0-beta.1
