# PopKit Quality

Quality assurance plugin for PopKit - testing, debugging, security scanning, and multi-perspective code assessment.

## Overview

PopKit Quality provides comprehensive quality assurance tools including:

- **Multi-Perspective Assessment**: Run specialized assessors (Anthropic Engineer, Security Auditor, Performance Tester, UX Reviewer, Technical Architect, Documentation Auditor)
- **Project Audits**: Quarterly/yearly reviews, stale issue detection, duplicate finding, health checks, IP leak scanning
- **Systematic Debugging**: Root cause analysis with 4-phase debugging workflow
- **Security Scanning**: Vulnerability management with npm audit integration and GitHub issue tracking

## Commands

| Command | Description |
|---------|-------------|
| `/popkit:assess` | Run assessor agents from different expert perspectives |
| `/popkit:audit` | Perform project audits (quarterly, yearly, stale, duplicates, health, ip-leak) |
| `/popkit:debug` | Systematic debugging with root cause analysis and routing diagnostics |
| `/popkit:security` | Security vulnerability management (scan, list, fix, report) |

## Skills

### Assessment Skills (6)
- `pop-assessment-anthropic` - Validate Claude Code compliance
- `pop-assessment-architecture` - Code quality and architectural patterns
- `pop-assessment-documentation` - Documentation accuracy and completeness
- `pop-assessment-performance` - Token efficiency and context usage
- `pop-assessment-security` - Security vulnerabilities and best practices
- `pop-assessment-ux` - Command naming and discoverability

### Quality Skills (5)
- `pop-systematic-debugging` - 4-phase debugging workflow
- `pop-security-scan` - Security scanning with npm audit
- `pop-plugin-test` - Plugin integrity validation
- `pop-routing-debug` - Agent routing analysis
- `pop-test-driven-development` - TDD workflow guidance

## Agents

### Tier 1 - Always Active (5)
- `bug-whisperer` - Complex debugging and error investigation
- `test-writer-fixer` - Test creation and fixing
- `security-auditor` - Security scanning and fixes
- `performance-optimizer` - Performance analysis and optimization
- `query-optimizer` - Database query optimization

### Assessors (6)
- `anthropic-engineer-assessor` - Claude Code pattern compliance
- `documentation-auditor-assessor` - Documentation quality validation
- `performance-tester-assessor` - Performance and efficiency evaluation
- `security-auditor-assessor` - Security vulnerability identification
- `technical-architect-assessor` - Code quality and architecture review
- `ux-reviewer-assessor` - User experience evaluation

## Installation

This plugin is part of the PopKit ecosystem and depends on `popkit-shared`.

```bash
# Install via Claude Code plugin manager
/plugin install popkit-quality@popkit-marketplace
```

## Usage Examples

```bash
# Run all assessments
/popkit:assess all

# Run specific assessor
/popkit:assess security
/popkit:assess docs

# Project health audit
/popkit:audit health

# Find stale issues
/popkit:audit stale --days 30

# Security scan
/popkit:security
/popkit:security scan --severity high

# Systematic debugging
/popkit:debug "login fails on mobile"
```

## Dependencies

- `popkit-shared>=0.1.0` - Shared utilities package

## Development Status

**Version**: 0.1.0 (Beta)
**Phase**: 4 of 8 (Plugin Modularization - Epic #580)

## License

MIT

## Author

Joseph Cannon <joseph@thehouseofdeals.com>
