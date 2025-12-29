# Changelog

All notable changes to PopKit Operations will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0-beta.1] - 2025-12-21

### Added

- Initial release as standalone operations plugin
- Extracted from monolithic PopKit plugin (Issue #585)
- Merged quality assurance (Issue #573) and deployment (Issue #574) concepts
- 5 commands: assess, audit, debug, security, deploy
- Quality assessment with 5 assessors (anthropic, security, performance, ux, architecture)
- Code auditing tools (quarterly, yearly, stale, duplicates, health, ip-leak)
- Systematic debugging workflows (code, routing)
- Security scanning and auto-fix capabilities
- Deployment orchestration (init, setup, validate, execute, rollback)

### Architecture

- **Plugin type:** Operations (quality assurance + deployment)
- **Commands:** 5
- **Skills:** 6 (assessment and debugging)
- **Agents:** 6 (4 tier-1 always-active, 2 tier-2 on-demand)
- **Size:** Medium (~70 bundled utilities)
- **Dependencies:** None (self-contained with bundled utilities)

### Skills Provided

- pop-assessment-anthropic - Anthropic engineering patterns compliance
- pop-assessment-security - Security vulnerability assessment
- pop-assessment-performance - Performance analysis and optimization
- pop-assessment-ux - User experience evaluation
- pop-assessment-architecture - Code quality and design patterns
- pop-systematic-debugging - Structured debugging workflows

### Agents Provided

**Tier 1 (Always Active):**
- bug-whisperer - Expert debugging for complex issues
- performance-optimizer - Performance engineering and bottleneck analysis
- security-auditor - Security vulnerability detection
- test-writer-fixer - Test creation and debugging

**Tier 2 (On-Demand):**
- deployment-validator - Pre-deployment validation and checks
- rollback-specialist - Emergency deployment recovery

### Integration

- Works standalone or with other PopKit plugins
- Skills globally available to all installed plugins
- Bundled utilities for self-contained operation
- Optional integration with popkit foundation for account features

### Issues

- Implements Issue #585: Extract popkit-ops plugin
- Merges Issue #573: Extract popkit-quality (closed)
- Merges Issue #574: Extract popkit-deploy (closed)
- Part of Epic #580: PopKit Plugin Modularization

[1.0.0-beta.1]: https://github.com/jrc1883/popkit/releases/tag/popkit-ops-v1.0.0-beta.1
