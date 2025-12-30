# Changelog

All notable changes to the PopKit Core plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **Power Mode Simplification** - Extracted generic Redis interfaces to `popkit-shared`
  - Moved `BaseRedisClient` and `BasePubSub` to `packages/shared-py/popkit_shared/storage/`
  - Reduced `upstash_adapter.py` from 627 to 490 LOC (-137 LOC)
  - Enables reuse across local Redis, Upstash, ElastiCache, etc.
  - Related: Power Mode Upstash audit (docs/assessments/2025-12-29-power-mode-upstash-audit.md)

### Removed
- **`/popkit:workflow-viz`** - Workflow visualizations now documented in README instead of command
  - Replaced with `/popkit:record` - Session forensics recording

### Deprecated
- **Account Command Consolidation Plan** - Preparing to merge 3 commands into 1
  - `/popkit:upgrade` → `/popkit:account signup` (future)
  - `/popkit:cloud` → `/popkit:account` subcommands (future)
  - Plan: docs/plans/2025-12-29-account-consolidation-plan.md
  - Migration: 3-phase approach with 2+ release deprecation period

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

[Unreleased]: https://github.com/jrc1883/popkit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jrc1883/popkit/releases/tag/v0.1.0
