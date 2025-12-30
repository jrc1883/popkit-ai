# PopKit - Operations Plugin

**Version:** 1.0.0-beta.1
**Status:** Operations Plugin (Phase 3b of Plugin Modularization)

## Overview

PopKit-Ops is the operations plugin for the PopKit ecosystem. It provides quality assurance, deployment automation, debugging workflows, and security scanning capabilities.

**Install this plugin** when you need DevOps and quality engineering workflows.

## Features

### Commands (5)

| Command | Description |
|---------|-------------|
| `/popkit:assess` | Code quality assessments (anthropic, security, performance, ux, architect, docs) |
| `/popkit:audit` | Quarterly/yearly health audits (quarterly, yearly, stale, duplicates, health, ip-leak) |
| `/popkit:debug` | Systematic debugging workflows (code, routing) |
| `/popkit:security` | Security scanning and fixes (scan, list, fix, report) |
| `/popkit:deploy` | Deployment orchestration (init, setup, validate, execute, rollback) |

### Skills (6)

This plugin provides 6 specialized skills:

- `pop-assessment-anthropic` - Compliance with Anthropic engineering patterns
- `pop-assessment-security` - Security vulnerability assessment
- `pop-assessment-performance` - Performance analysis and optimization
- `pop-assessment-ux` - User experience evaluation
- `pop-assessment-architecture` - Code quality and design patterns
- `pop-systematic-debugging` - Structured debugging workflows

**Note:** Skills are globally available once installed - other PopKit plugins can use these skills!

### Agents (6)

| Agent | Tier | Trigger |
|-------|------|---------|
| `bug-whisperer` | Tier 1 (always-active) | Complex debugging, hard-to-reproduce bugs |
| `performance-optimizer` | Tier 1 (always-active) | Performance issues, bottleneck analysis |
| `security-auditor` | Tier 1 (always-active) | Security scanning, vulnerability detection |
| `test-writer-fixer` | Tier 1 (always-active) | Test creation, test failures, coverage |
| `deployment-validator` | Tier 2 (on-demand) | Pre-deployment checks, validation |
| `rollback-specialist` | Tier 2 (on-demand) | Deployment failures, emergency recovery |

## Installation

```bash
# Recommended: Install popkit-core foundation first
/plugin install popkit-core@popkit-marketplace

# Then install operations plugin
/plugin install popkit-ops@popkit-marketplace

# Or install during development (local)
/plugin install popkit-ops@file:./packages/popkit-ops
```

## Dependencies

- **popkit-core** (foundation plugin recommended) - For account management and stats
- **Python** (>= 3.8) - For hook execution
- **PopKit Cloud API** (optional) - For enhanced features

## Architecture

PopKit-Ops is part of PopKit's modular plugin architecture:

```
popkit-core (foundation)
├── Account management
├── Usage statistics
├── Privacy controls
├── Power Mode orchestration
└── Project analysis

popkit-dev (development)
├── Feature development
├── Git operations
└── Daily routines

popkit-ops (operations)       ← You are here
├── Quality assessment
├── Debugging workflows
├── Security scanning
└── Deployment automation

popkit-research (knowledge)
├── Research capture
└── Knowledge management

popkit-suite (meta-plugin)
└── Installs all 4 plugins above
```

## Usage Examples

### Quality Assessment

```bash
# Run all assessors
/popkit:assess all

# Run specific assessor
/popkit:assess anthropic      # Anthropic patterns compliance
/popkit:assess security       # Security vulnerabilities
/popkit:assess performance    # Performance issues
/popkit:assess ux             # User experience
/popkit:assess architect      # Code quality

# With auto-fix
/popkit:assess security --fix

# With JSON output
/popkit:assess all --json
```

### Code Auditing

```bash
# Quarterly health check
/popkit:audit quarterly

# Yearly comprehensive audit
/popkit:audit yearly

# Find stale code
/popkit:audit stale

# Find duplicated code
/popkit:audit duplicates

# Overall project health
/popkit:audit health

# IP leak detection (for split-repo projects)
/popkit:audit ip-leak
/popkit:audit ip-leak --fix
```

### Systematic Debugging

```bash
# Debug code issues
/popkit:debug code

# Debug agent routing
/popkit:debug routing

# With detailed trace
/popkit:debug code --trace

# With verbose output
/popkit:debug code --verbose
```

### Security Scanning

```bash
# Scan for vulnerabilities
/popkit:security scan

# List all findings
/popkit:security list

# Auto-fix vulnerabilities
/popkit:security fix

# Generate security report
/popkit:security report

# With severity filtering
/popkit:security scan --severity critical
/popkit:security fix --severity high

# Dry run mode
/popkit:security fix --dry-run
```

### Deployment Orchestration

```bash
# Initialize deployment configuration
/popkit:deploy init

# Setup deployment environment
/popkit:deploy setup

# Validate pre-deployment checks
/popkit:deploy validate

# Execute deployment
/popkit:deploy execute

# Rollback to previous version
/popkit:deploy rollback

# Deploy to specific target
/popkit:deploy execute --target production

# Deploy all targets
/popkit:deploy execute --all

# Dry run mode
/popkit:deploy execute --dry-run
```

## Agent Activation

### Tier 1 Agents (Always Active)

These agents are always available and will automatically activate when relevant:

- **bug-whisperer**: Activates for complex bugs, error investigation
- **performance-optimizer**: Activates for performance issues, bottlenecks
- **security-auditor**: Activates for security scanning, vulnerability detection
- **test-writer-fixer**: Activates for test writing, test failures

### Tier 2 Agents (On-Demand)

These agents activate only when explicitly needed:

- **deployment-validator**: Use `/popkit:deploy validate` to activate
- **rollback-specialist**: Use `/popkit:deploy rollback` to activate

## File Structure

```
packages/popkit-ops/
├── .claude-plugin/
│   └── plugin.json             # Plugin manifest
├── commands/
│   ├── assess.md               # Quality assessment
│   ├── audit.md                # Code auditing
│   ├── debug.md                # Systematic debugging
│   ├── security.md             # Security scanning
│   └── deploy.md               # Deployment orchestration
├── skills/
│   ├── pop-assessment-anthropic/
│   ├── pop-assessment-security/
│   ├── pop-assessment-performance/
│   ├── pop-assessment-ux/
│   ├── pop-assessment-architecture/
│   └── pop-systematic-debugging/
├── agents/
│   ├── tier-1-always-active/
│   │   ├── bug-whisperer/
│   │   ├── performance-optimizer/
│   │   ├── security-auditor/
│   │   └── test-writer-fixer/
│   └── tier-2-on-demand/
│       ├── deployment-validator/
│       └── rollback-specialist/
├── hooks/
│   └── utils/                  # 70 bundled Python utilities
├── README.md                   # This file
└── CHANGELOG.md                # Version history
```

## Testing Strategy

1. ✅ Package structure created
2. ✅ Commands extracted from monolithic plugin
3. ✅ Skills extracted
4. ✅ Agents extracted
5. ✅ plugin.json created
6. ⏳ Local installation test
7. ⏳ Command functionality validation
8. ⏳ Agent routing verification
9. ⏳ Skill execution testing

## Success Metrics

- [ ] All 5 commands work identically to monolithic version
- [ ] All 6 agents route correctly
- [ ] All 6 skills execute successfully
- [ ] Installation < 30 seconds
- [ ] No context window increase
- [ ] Clean uninstall
- [ ] No functionality regression

## Issues

- **This plugin**: Issue #585 (Extract popkit-ops)
- **Parent Epic**: Issue #580 (Plugin Modularization)
- **Dependencies**: popkit foundation (#584 - COMPLETED)

## Related Plugins

When you need more capabilities, install additional PopKit plugins:

```bash
# For account management and stats
/plugin install popkit-core@popkit-marketplace

# For development workflows
/plugin install popkit-dev@popkit-marketplace

# For knowledge management
/plugin install popkit-research@popkit-marketplace

# Or install everything
/plugin install popkit-suite@popkit-marketplace
```

## License

MIT

## Support

- **Documentation:** See command files in `commands/`
- **Bug Reports:** `/popkit:bug report` (requires popkit foundation)
- **Feature Requests:** GitHub Issues
- **Community:** PopKit Cloud (coming soon)
