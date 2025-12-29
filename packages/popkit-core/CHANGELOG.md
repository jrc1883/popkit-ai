# Changelog

All notable changes to the PopKit Core plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
  - `/popkit:workflow-viz` - Workflow visualization
  - `/popkit:bug` - Bug reporting
  - `/popkit:power` - Power Mode orchestration
  - `/popkit:project` - Project analysis and tooling
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
