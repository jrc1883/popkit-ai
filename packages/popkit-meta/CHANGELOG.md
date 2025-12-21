# Changelog

All notable changes to the PopKit meta-plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-12-20

### Added
- **Initial Release** - Meta-plugin for backwards compatibility (Issue #577, Epic #580)
- **Complete Suite**: Installs all 6 PopKit workflow plugins in one command
- **Dependencies**:
  - popkit-shared>=0.1.0 - Shared utilities foundation
  - popkit-dev>=0.1.0 - Development workflows (5 commands, 9 skills, 5 agents)
  - popkit-github>=0.1.0 - GitHub integration (2 commands)
  - popkit-quality>=0.1.0 - Quality assurance (4 commands, 11 skills, 11 agents)
  - popkit-deploy>=0.1.0 - Deployment automation (1 command, 13 skills, 3 agents)
  - popkit-research>=0.1.0 - Research management (2 commands, 3 skills, 1 agent)
  - popkit-core>=0.1.0 - Core utilities (10 commands, 10 skills, 9 agents)
- **Total**: 24 commands, 46 skills, 29 agents
- **Backwards Compatibility**: Drop-in replacement for monolithic plugin
- **Migration Guide**: Comprehensive migration documentation
- **Unified Namespace**: All commands under `/popkit:` prefix

### Documentation
- README.md - Complete installation and usage guide
- MIGRATION.md - Step-by-step migration from monolithic plugin
- Individual plugin documentation linked

### Architecture
- Zero implementation code (pure dependency aggregator)
- All functionality provided by sub-plugins
- Semantic versioning synchronized across plugins

[Unreleased]: https://github.com/jrc1883/popkit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jrc1883/popkit/releases/tag/v0.1.0
