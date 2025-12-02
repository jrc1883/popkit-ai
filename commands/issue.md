---
description: GitHub issue management - create, list, view, close, comment with AI-executable format and PopKit Guidance
---

# /popkit:issue - GitHub Issue Management

Manage GitHub issues with AI-optimized formatting and PopKit workflow guidance.

## Usage

```
/popkit:issue <subcommand> [options]
```

## Subcommands

### create

Create new issue with template selection:

```
/popkit:issue create <title>
/popkit:issue create "Add user authentication"
/popkit:issue create --template bug
/popkit:issue create --template feature
/popkit:issue create --template architecture
/popkit:issue create --template research
```

**Available Templates:**

| Template | Use For | Labels |
|----------|---------|--------|
| `feature` | New features, enhancements | enhancement |
| `bug` | Bug reports, fixes | bug |
| `architecture` | Major changes, epics, multi-PR work | architecture, epic |
| `research` | Spikes, investigations, learning | research |

**Template Selection Flow:**

When creating without `--template`, prompt user:

```
What type of issue is this?
1. Feature - New capability or enhancement
2. Bug - Something isn't working correctly
3. Architecture - Major changes or epic initiative
4. Research - Investigation or spike
```

### Template Structure

All templates include a **PopKit Guidance** section that directs workflow:

```markdown
## PopKit Guidance

### Workflow
- [ ] **Brainstorm First** - Use `pop-brainstorming` skill
- [ ] **Plan Required** - Use `/popkit:write-plan`
- [ ] **Direct Implementation** - Proceed directly

### Development Phases
- [ ] Discovery
- [ ] Architecture
- [ ] Implementation
- [ ] Testing
- [ ] Documentation
- [ ] Review

### Suggested Agents
- Primary: `[agent-name]`
- Supporting: `[agent-name]`

### Quality Gates
- [ ] TypeScript check
- [ ] Build verification
- [ ] Lint pass
- [ ] Test pass

### Power Mode
- [ ] Recommended - Parallel agents beneficial
- [ ] Optional - Can benefit from coordination
- [ ] Not Needed - Sequential work is fine

### Estimated Complexity
- [ ] Small (1-2 files)
- [ ] Medium (3-5 files)
- [ ] Large (6+ files)
- [ ] Epic (multiple PRs)
```

**Why PopKit Guidance Matters:**

This section is parsed by PopKit to:
1. Determine if brainstorming should be triggered first
2. Auto-activate Power Mode for complex issues
3. Schedule quality gates between phases
4. Route to appropriate agents
5. Track phase progress

### list

List repository issues:

```
/popkit:issue list                    # Open issues
/popkit:issue list --state all        # All issues
/popkit:issue list --label bug        # Filtered by label
/popkit:issue list --label architecture  # Architecture issues
/popkit:issue list --assignee @me     # Assigned to me
/popkit:issue list --milestone v1.0   # By milestone
```

Output:
```
Open Issues (12):
#45 [bug] Login fails on mobile - @user - 2 days ago
#44 [feature] Add dark mode - @user - 3 days ago
#43 [architecture] Unified orchestration - @user - 1 week ago
...
```

### view

View issue details:

```
/popkit:issue view 45
/popkit:issue view 45 --comments
```

Output includes PopKit Guidance parsing:
```
#45: Login fails on mobile
State: open
Labels: bug, priority:high
Assignee: @username

PopKit Workflow:
  Type: Bug fix
  Agents: bug-whisperer, test-writer-fixer
  Power Mode: Not needed
  Phases: Investigation → Fix → Test → Review

Description:
[Full issue body]
```

### close

Close issue:

```
/popkit:issue close 45
/popkit:issue close 45 --comment "Fixed in #PR"
/popkit:issue close 45 --reason completed
/popkit:issue close 45 --reason not_planned
/popkit:issue close 45 --superseded-by 67
```

### comment

Add comment to issue:

```
/popkit:issue comment 45 "Working on this"
/popkit:issue comment 45 --file notes.md
/popkit:issue comment 45 --phase-update "Completed implementation, moving to testing"
```

### edit

Update issue:

```
/popkit:issue edit 45 --title "New title"
/popkit:issue edit 45 --label add:priority:high
/popkit:issue edit 45 --assignee @username
/popkit:issue edit 45 --milestone v1.0
```

### link

Link issue to PR:

```
/popkit:issue link 45 --pr 67
```

### work

Start working on an issue (NEW):

```
/popkit:issue work 45
```

This command:
1. Reads the issue and parses PopKit Guidance
2. Checks if brainstorming is required → triggers `pop-brainstorming`
3. Checks complexity → activates Power Mode if needed
4. Creates initial todo list from phases
5. Routes to suggested agents

## Agent Routing

Based on issue content and labels:

| Indicator | Primary Agent | Supporting |
|-----------|---------------|------------|
| `[Bug]` label or "bug" in title | bug-whisperer | test-writer-fixer |
| `[Feature]` label | code-architect | test-writer-fixer |
| `[Architecture]` label | code-architect | migration-specialist, refactoring-expert |
| `[Research]` label | researcher | code-explorer |
| Security keywords | security-auditor | code-reviewer |
| Performance keywords | performance-optimizer | bundle-analyzer |
| API keywords | api-designer | documentation-maintainer |
| Database keywords | query-optimizer | migration-specialist |

## GitHub CLI Integration

All commands use `gh` CLI:
```bash
gh issue create --title "..." --body "..." --template feature_request.md
gh issue list --state open
gh issue view 45
gh issue close 45
gh issue comment 45 --body "..."
```

## Examples

```
# Create with template selection prompt
/popkit:issue create "Add user authentication"

# Create with specific template
/popkit:issue create "Refactor auth system" --template architecture

# Start working on an issue (triggers workflow)
/popkit:issue work 11

# List architecture issues
/popkit:issue list --label architecture

# Close as superseded
/popkit:issue close 8 --superseded-by 11

# Add phase update
/popkit:issue comment 11 --phase-update "Completed Phase 1: Discovery"
```

## Architecture Integration

| Component | Integration |
|-----------|-------------|
| Issue Templates | `.github/ISSUE_TEMPLATE/*.md` |
| PopKit Guidance Parser | `hooks/issue-parser.py` (planned) |
| Phase Tracking | `STATUS.json` integration |
| Power Mode Triggers | Parsed from Guidance section |
| Quality Gates | Scheduled per phase from Guidance |
