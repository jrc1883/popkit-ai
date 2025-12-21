# Changelog

All notable changes to the PopKit Quality plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-12-20

### Added
- **Initial Release** - Extracted from monolithic PopKit plugin (Issue #573, Epic #580)
- **Commands** (4):
  - `/popkit:assess` - Multi-perspective self-assessment
  - `/popkit:audit` - Project audits and health checks
  - `/popkit:debug` - Systematic debugging workflow
  - `/popkit:security` - Security vulnerability management
- **Skills** (11):
  - Assessment: anthropic, architecture, documentation, performance, security, ux
  - Quality: systematic-debugging, security-scan, plugin-test, routing-debug, test-driven-development
- **Agents** (11):
  - Tier 1: bug-whisperer, test-writer-fixer, security-auditor, performance-optimizer, query-optimizer
  - Assessors: anthropic-engineer, documentation-auditor, performance-tester, security-auditor, technical-architect, ux-reviewer
- **Dependencies**: popkit-shared>=0.1.0

[Unreleased]: https://github.com/jrc1883/popkit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jrc1883/popkit/releases/tag/v0.1.0
