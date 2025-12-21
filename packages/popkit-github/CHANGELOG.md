# Changelog

All notable changes to PopKit GitHub will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-12-20

### Added

- Initial release as standalone plugin (Phase 3 of modularization)
- Extracted from monolithic PopKit plugin (Issue #572)
- 2 commands: issue, milestone
- Complete GitHub issue management
  - Create, list, view, close, comment, edit operations
  - Label and milestone assignment
  - Issue linking and references
- Milestone tracking and health analysis
  - Progress tracking and burndown
  - Risk assessment and timeline health
  - Blocker identification
- Integration with GitHub CLI

### Dependencies

- popkit-shared >= 0.1.0 (shared utilities)
- GitHub CLI (gh) - required for GitHub operations

### Prerequisites

- Authenticated GitHub session (`gh auth login`)

### Issues

- Implements Issue #572: Extract popkit-github plugin
- Part of Epic #580: PopKit Plugin Modularization (Phase 3)

[0.1.0]: https://github.com/jrc1883/popkit/releases/tag/popkit-github-v0.1.0
