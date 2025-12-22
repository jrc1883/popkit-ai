# Changelog

All notable changes to PopKit Dev will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-12-21

### Added

- Merged popkit-github plugin for unified development workflow
- `/popkit:issue` command - GitHub issue management (create, list, view, close, comment, edit, link)
- `/popkit:milestone` command - Milestone tracking (list, create, close, report, health analysis)

### Changed

- Renamed from "Development workflows" to "Complete development workflow"
- Updated description to include GitHub management
- Command count: 5 → 7

### Rationale

GitHub operations (issues, PRs, milestones, releases) are integral to modern development workflows, not separate project management concerns. The artificial split between popkit-dev and popkit-github created confusion and broke natural workflow continuity.

**Unified workflow:** Issues → Dev → PR → Merge → Close (all in one plugin)

### Issues

- Implements Issue #583: Merge popkit-github into popkit-dev (Phase 3.5)
- Supersedes Issue #572: Extract popkit-github (Phase 3)
- Part of Epic #580: PopKit Plugin Modularization

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
