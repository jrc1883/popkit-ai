# Changelog

All notable changes to PopKit Foundation will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0-beta.1] - 2025-12-21

### Added

- Initial release as standalone foundation plugin
- Extracted from monolithic PopKit plugin (Issue #584)
- 7 commands: account, stats, privacy, bug, plugin, cache, upgrade
- Account management with PopKit Cloud API integration
- Usage statistics tracking (local and cloud-synced)
- Privacy controls and data management
- Bug reporting and diagnostics
- Plugin testing and validation tools
- Cache management utilities
- Premium feature information and upgrade flows

### Architecture

- **Plugin type:** Foundation (system features)
- **Commands:** 7 (no skills, no agents)
- **Size:** Minimal (~100 lines of command markdown)
- **Dependencies:** popkit-shared >= 0.1.0

### Integration

- Connects to PopKit Cloud API (`api.thehouseofdeals.com`)
- Stores API key in `~/.popkit/config.json`
- All other PopKit plugins read this config for premium validation

### Issues

- Implements Issue #584: Extract popkit foundation plugin
- Supersedes Issue #576: Extract popkit-core (old architecture)
- Part of Epic #580: PopKit Plugin Modularization

[1.0.0-beta.1]: https://github.com/jrc1883/popkit/releases/tag/popkit-v1.0.0-beta.1
