# Changelog

All notable changes to the PopKit Core plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0-beta.9] - 2025-02-10

### Added

- **Native Swarm Orchestration** - Multi-agent teams with E2B sandbox isolation
  - `TeamCreate`/`TeamClose` workflow for parallel agent coordination
  - E2B sandbox integration for safe remote code execution
  - Auto-drive hook for self-organizing teammates (reduces "manager latency")
  - Role-based task claiming: Engineer, Researcher, Architect, Tester, Security Auditor, Documentation
  - Cross-platform sandbox state management (Windows + Unix)

- **`pop-sandbox` Skill** - Full E2B sandbox management
  - `sandbox_create` - Provision ephemeral environments
  - `sandbox_run_command` - Execute commands (with background mode)
  - `sandbox_write_file` / `sandbox_read_file` - File operations
  - `sandbox_list` - List active sandboxes
  - `sandbox_kill` - Terminate sandboxes

### Changed

- **`power-coordinator` Agent** - Upgraded to v2.0.0
  - Now uses native `agentTeams` capability instead of manual loop
  - Integrated sandbox provisioning for conflict-free parallel execution
  - Enhanced progress reporting format

- **`teammate-idle` Hook** - Enhanced with auto-claiming logic
  - Role detection from context
  - Role-to-task keyword matching
  - Swarm event logging for observability

### Dependencies

- Added `e2b-code-interpreter>=1.0.0` for sandbox functionality
- Added `python-dotenv>=1.0.0` for environment management

## [Unreleased]

### Added

- **`/popkit:account`** - Unified account management command (Phase 1)
  - 6 subcommands: status, signup, login, keys, usage, logout
  - Consolidates fragmented account/upgrade/cloud functionality
  - 672 lines of comprehensive account management

### Changed

- **Power Mode Simplification** - Phase 1-2 complete (97.2% reduction planned)
  - Extracted generic Redis interfaces to `popkit-shared`
  - Moved `BaseRedisClient` and `BasePubSub` to `packages/shared-py/popkit_shared/storage/`
  - Reduced `upstash_adapter.py` from 627 to 490 LOC (-137 LOC)
  - Archived 6 test/benchmark files (2,514 LOC) to `packages/benchmarks/power-mode/`
  - Deleted experimental consensus protocol (8 files, 5,055 LOC)
  - Total cleanup: 7,569 LOC removed from active codebase
  - Related: Power Mode Upstash audit (docs/assessments/2025-12-29-power-mode-upstash-audit.md)

### Removed

- **`/popkit:workflow-viz`** - Workflow visualizations now documented in README instead of command
  - Replaced with `/popkit:record` - Session forensics recording
- **`/popkit:upgrade`** - Replaced by `/popkit:account signup` (Phase 3)
- **`/popkit:cloud`** - Replaced by `/popkit:account` subcommands (Phase 3)
- **Command Count**: Reduced from 25 → 23 commands (early removal, no deprecation period needed)

### Analysis

- **Power Mode Audit** - Comprehensive analysis of 19,249 LOC
  - Only 400 LOC (2.1%) is Upstash-specific
  - Core value: Redis Streams pub/sub simulation (200 LOC)
  - Generic code: 800 LOC identified for extraction
  - Target: Simplify from 15k to ~600 LOC
- **Command Overlap** - Identified 40-50% duplication in account commands
  - `/popkit:account` + `/popkit:upgrade` + `/popkit:cloud` → `/popkit:account`
  - 3 commands → 1 unified command with 6 subcommands

## [0.1.0] - 2025-12-20

### Added

- **Initial Release** - Extracted from monolithic PopKit plugin (Issue #576, Epic #580)
- **Commands** (10):
  - `/popkit:plugin` - Plugin testing and management
  - `/popkit:stats` - Efficiency metrics
  - `/popkit:privacy` - Privacy controls
  - `/popkit:account` - Account management
  - `/popkit:upgrade` - Upgrade to premium
  - `/popkit:dashboard` - Multi-project dashboard
  - `/popkit:bug` - Bug reporting
  - `/popkit:power` - Power Mode orchestration
  - `/popkit:project` - Project analysis and tooling
  - `/popkit:record` - Session forensics recording
- **Skills** (10):
  - Project: analyze-project, project-init, project-templates, embed-content, embed-project
  - Meta: bug-reporter, dashboard, power-mode, mcp-generator, skill-generator
- **Agents** (9):
  - Tier 1 (4): api-designer, accessibility-guardian, documentation-maintainer, migration-specialist
  - Tier 2 (5): meta-agent, power-coordinator, bundle-analyzer, dead-code-eliminator, feature-prioritizer
- **Power Mode**: Multi-agent orchestration with Redis/file-based modes
- **Privacy Management**: Strict/moderate/minimal privacy levels
- **Multi-Project Dashboard**: Centralized project management
- **Dependencies**: popkit-shared>=0.1.0

[Unreleased]: https://github.com/jrc1883/popkit-claude/compare/v1.0.0-beta.9...HEAD
[1.0.0-beta.9]: https://github.com/jrc1883/popkit-claude/compare/v1.0.0-beta.8...v1.0.0-beta.9
[0.1.0]: https://github.com/jrc1883/popkit-claude/releases/tag/v0.1.0
