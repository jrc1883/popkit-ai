# Changelog

All notable changes to PopKit Dev will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-12-20

### Added

- Initial release as standalone plugin (proof of concept for modularization)
- Extracted from monolithic PopKit plugin (Issue #571)
- 5 commands: dev, git, worktree, routine, next
- 9 skills: brainstorming, planning, execution, routines, session management
- 5 agents: code-explorer, code-architect, code-reviewer, refactoring-expert, rapid-prototyper
- Complete development workflow support
- Git operations and worktree management
- Daily routine automation (morning health checks, nightly cleanup)
- Context-aware next action recommendations

### Dependencies

- popkit-shared >= 0.1.0 (shared utilities)
- requests >= 2.31.0 (HTTP operations)

### Issues

- Implements Issue #571: Extract popkit-dev plugin (proof of concept)
- Part of Epic #580: PopKit Plugin Modularization (Phase 2)

[0.1.0]: https://github.com/jrc1883/popkit/releases/tag/popkit-dev-v0.1.0
