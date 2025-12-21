# PopKit GitHub - GitHub Workflow Plugin

**Version:** 0.1.0
**Status:** Phase 3 of Plugin Modularization

## Overview

PopKit GitHub is a focused GitHub integration plugin extracted from the monolithic PopKit plugin. It provides comprehensive tools for issue management, milestone tracking, and GitHub workflow automation.

## Features

### Commands (2)

| Command | Description |
|---------|-------------|
| `/popkit:issue` | Complete issue management (create, list, view, close, comment, edit, link) |
| `/popkit:milestone` | Milestone tracking (list, create, close, report, health analysis) |

### Issue Management

**CRUD Operations:**
```bash
# Create new issue
/popkit:issue create "Bug: login fails"
/popkit:issue create --title "Feature" --body "Description" --label bug

# List issues
/popkit:issue list
/popkit:issue list --state open --label P0-critical
/popkit:issue list --milestone v1.0.0

# View issue details
/popkit:issue view 123

# Update issue
/popkit:issue edit 123 --title "New Title"
/popkit:issue comment 123 "Adding context..."

# Close issue
/popkit:issue close 123
```

**Advanced Features:**
- Smart issue creation from context
- Label management
- Milestone assignment
- Issue linking and references
- State transitions

### Milestone Management

**Tracking & Health:**
```bash
# List milestones
/popkit:milestone list
/popkit:milestone list --state open

# Create milestone
/popkit:milestone create "v1.0.0" --due 2025-12-31

# Health report
/popkit:milestone health v1.0.0
/popkit:milestone report v1.0.0 --json

# Close milestone
/popkit:milestone close v1.0.0
```

**Health Metrics:**
- Progress tracking (% complete)
- Burndown analysis
- Risk assessment
- Timeline health
- Blocker identification

## Installation

```bash
# Local installation (development)
/plugin install popkit-github@file:./packages/popkit-github

# Future: Marketplace installation
/plugin install popkit-github@popkit-marketplace
```

## Prerequisites

- **GitHub CLI (`gh`)** - Required for all GitHub operations
- **popkit-shared** (>= 0.1.0) - Shared utilities
- **Authenticated GitHub session** - Run `gh auth login` first

## Dependencies

- **popkit-shared** (>= 0.1.0) - Shared utility modules
- **GitHub CLI** - For GitHub API operations
- **Python** (>= 3.8)

## Architecture

Part of PopKit's modular plugin architecture:

```
packages/
├── shared-py/          # Shared utilities (Phase 1) ✅
├── popkit-dev/         # Development workflows (Phase 2) ✅
├── popkit-github/      # GitHub integration (Phase 3) ← You are here
├── popkit-data/        # Future: Data & AI workflows
├── popkit-cloud/       # Future: Cloud operations
└── popkit-security/    # Future: Security scanning
```

## Usage Examples

### Issue Workflow

```bash
# Create issue from current work
/popkit:issue create "Add OAuth support"

# List P0 issues for current milestone
/popkit:issue list --label P0-critical --milestone v1.0.0

# View and comment
/popkit:issue view 45
/popkit:issue comment 45 "Started implementation in branch feature/oauth"

# Close when done
/popkit:issue close 45
```

### Milestone Tracking

```bash
# Create release milestone
/popkit:milestone create "v1.0.0" --due 2025-12-31 --description "First stable release"

# Check health during sprint
/popkit:milestone health v1.0.0

# Generate report
/popkit:milestone report v1.0.0 --verbose

# Close when complete
/popkit:milestone close v1.0.0
```

## Integration with Other Plugins

Works seamlessly with:
- **popkit-dev** - Create issues from feature development
- **popkit-deploy** - Link deployments to milestones
- **popkit-cloud** - Track cloud resource issues

## Testing Strategy

1. ✅ Package structure created
2. ✅ Commands extracted
3. ⏳ Local installation test
4. ⏳ Command functionality validation
5. ⏳ GitHub CLI integration test

## Success Metrics

- [ ] All commands work identically to monolithic version
- [ ] Installation < 30 seconds
- [ ] No context window increase
- [ ] Clean uninstall

## Issues

- **Phase 3**: Issue #572 (this plugin)
- **Parent Epic**: Issue #580 (Plugin Modularization)
- **Dependencies**: Issues #570 (shared-py), #571 (popkit-dev)

## License

MIT
