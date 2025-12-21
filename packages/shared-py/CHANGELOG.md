# Changelog

All notable changes to the PopKit Shared package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-12-20

### Added

- Initial release of popkit-shared package
- Extracted 69 utility modules from monolithic PopKit plugin
- Organized modules into 8 categories:
  - Core Infrastructure (23 modules)
  - Routing & Discovery (9 modules)
  - State Management (8 modules)
  - Cloud Integration (6 modules)
  - Tool Intelligence (6 modules)
  - Testing & Validation (5 modules)
  - Monitoring & Metrics (5 modules)
  - Specialized Utilities (7 modules)
- Package configuration with Poetry
- PyYAML dependency (only third-party dependency)
- Python 3.8+ compatibility
- Development mode installation support

### Changed

- Import path from `hooks.utils.*` to `popkit_shared.utils.*`
- Simplified dependency management (single package vs. 69 individual modules)

### Migration

See [MIGRATION.md](MIGRATION.md) for complete migration guide.

### Issues

- Resolves Issue #570: Extract shared foundation package
- Part of Epic #580: PopKit Plugin Modularization (Phase 1)

[0.1.0]: https://github.com/jrc1883/popkit/releases/tag/shared-py-v0.1.0
