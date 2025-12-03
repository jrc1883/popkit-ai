---
description: GitHub issue management - create, list, view, work, close, comment with AI-executable format and PopKit Guidance
---

# /popkit:issue - GitHub Issue Management

Manage GitHub issues with AI-optimized formatting and PopKit workflow guidance.

## Usage

```
/popkit:issue <subcommand> [options]
```

## Subcommands

| Subcommand | Description |
|------------|-------------|
| `list` | List repository issues (default) |
| `view` | View issue details |
| `create` | Create new issue with template |
| `work` | Start working on an issue with optional Power Mode |
| `close` | Close an issue |
| `comment` | Add comment to issue |
| `edit` | Update issue metadata |
| `link` | Link issue to PR |

---

## Subcommand: list (default)

List repository issues with Power Mode recommendations.

```
/popkit:issue                         # List open issues
/popkit:issue list                    # Same as above
/popkit:issue list --power            # Only issues recommending Power Mode
/popkit:issue list --label bug        # Filter by label
/popkit:issue list --state all        # All issues (open + closed)
/popkit:issue list --assignee @me     # Assigned to me
/popkit:issue list --milestone v1.0   # By milestone
/popkit:issue list -n 10              # Limit results
```

### Flags

| Flag | Short | Description |
|------|-------|-------------|
| `--power` | `-p` | Show only issues recommending Power Mode |
| `--label` | `-l` | Filter by label |
| `--state` | | `open` (default), `closed`, `all` |
| `--assignee` | | Filter by assignee |
| `--milestone` | | Filter by milestone |
| `--limit` | `-n` | Limit results (default: 20) |

### Output Format

```
Open Issues with Power Mode Recommendations:

| #   | Title                          | Complexity | Power Mode  | Phases |
|-----|--------------------------------|------------|-------------|--------|
| 3   | Add user authentication        | medium     | optional    | 4      |
| 11  | Unified orchestration system   | epic       | RECOMMENDED | 6      |
| 15  | Fix login regression           | small      | not_needed  | 2      |

Legend:
  RECOMMENDED = Power Mode beneficial for this issue
  optional    = Power Mode available but not required
  not_needed  = Sequential execution preferred

Hint: Use /popkit:issue work #11 to start working
      Use /popkit:issue work #11 -p to force Power Mode
```

### Process

1. Fetch issues via `gh issue list --json number,title,body,labels,createdAt,author`
2. Parse PopKit Guidance from each issue body
3. Extract complexity, phases, Power Mode recommendation
4. Generate formatted table

---

## Subcommand: view

View issue details with parsed PopKit Guidance.

```
/popkit:issue view 45
/popkit:issue view 45 --comments
/popkit:issue view #45              # # prefix optional
```

### Output

```
#45: Login fails on mobile
State: open
Labels: bug, priority:high
Assignee: @username

PopKit Workflow:
  Type: Bug fix
  Agents: bug-whisperer, test-writer-fixer
  Power Mode: Not needed
  Phases: Investigation -> Fix -> Test -> Review

Description:
[Full issue body]
```

---

## Subcommand: create

Create new issue with template selection.

```
/popkit:issue create <title>
/popkit:issue create "Add user authentication"
/popkit:issue create --template bug
/popkit:issue create --template feature
/popkit:issue create --template architecture
/popkit:issue create --template research
```

### Available Templates

| Template | Use For | Labels |
|----------|---------|--------|
| `feature` | New features, enhancements | enhancement |
| `bug` | Bug reports, fixes | bug |
| `architecture` | Major changes, epics, multi-PR work | architecture, epic |
| `research` | Spikes, investigations, learning | research |

### Template Selection Flow

When creating without `--template`, prompt user:

```
What type of issue is this?
1. Feature - New capability or enhancement
2. Bug - Something isn't working correctly
3. Architecture - Major changes or epic initiative
4. Research - Investigation or spike
```

### PopKit Guidance Section

All templates include a **PopKit Guidance** section that directs workflow:

```markdown
## PopKit Guidance

### Workflow
- [ ] **Brainstorm First** - Use `pop-brainstorming` skill
- [ ] **Plan Required** - Use `/popkit:plan write`
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

---

## Subcommand: work

Start working on an issue with intelligent Power Mode detection.

```
/popkit:issue work #N [flags]
/popkit:issue work 4                  # Auto-detect Power Mode from guidance
/popkit:issue work #4 -p              # Force Power Mode ON
/popkit:issue work #4 --power         # Same as -p
/popkit:issue work #4 --solo          # Force sequential mode (no Power Mode)
/popkit:issue work #4 --phases explore,implement,test
/popkit:issue work #4 --agents reviewer,tester
/popkit:issue work #4 -p --phases design,implement
```

### Flags

| Flag | Short | Description |
|------|-------|-------------|
| `--power` | `-p` | Force Power Mode activation |
| `--solo` | `-s` | Force sequential mode (no Power Mode) |
| `--phases` | | Override phases: `--phases explore,implement,test` |
| `--agents` | | Override agents: `--agents reviewer,tester` |

### Power Mode Decision Priority

1. **Command flags override everything:**
   - `-p` or `--power` -> Force Power Mode ON
   - `-s` or `--solo` -> Force Power Mode OFF
2. **If no flags, use PopKit Guidance:**
   - `power_mode: recommended` -> Power Mode ON
   - `complexity: epic` -> Power Mode ON
   - 3+ agents -> Power Mode ON
3. **If no guidance, auto-generate plan:**
   - Infer issue type from labels/title
   - Recommend Power Mode for large/epic complexity
4. Default to sequential mode

### Process

1. **Parse Arguments**: Extract issue number and flags
2. **Fetch Issue**: `gh issue view <number> --json number,title,body,labels,state,author`
3. **Parse PopKit Guidance**: Extract workflow, phases, agents, quality gates
4. **Determine Power Mode**: Apply decision priority above
5. **Configure Workflow**: Set phases, agents, boundaries
6. **Create Todo List**: Generate todos from phases
7. **Begin Work**: If brainstorming required, invoke skill first

### Output (Power Mode)

```
[+] POWER MODE - ISSUE #4
Title: Add user authentication
Labels: feature, priority:high

Configuration:
  Source: PopKit Guidance
  Phases: 5 (discovery -> review)
  Agents: code-architect, test-writer-fixer
  Quality Gates: typescript, build, lint, test

Status Line: [POP] #4 Phase: discovery (1/5) [----------] 0%

Starting Phase 1: Discovery...
```

### Output (Sequential Mode)

```
[+] WORKING ON ISSUE #4
Title: Add user authentication
Mode: Sequential

Phases: 5 (discovery -> review)
Agent: code-architect

Starting Phase 1: Discovery...
```

---

## Subcommand: close

Close an issue.

```
/popkit:issue close 45
/popkit:issue close 45 --comment "Fixed in #PR"
/popkit:issue close 45 --reason completed
/popkit:issue close 45 --reason not_planned
/popkit:issue close 45 --superseded-by 67
```

---

## Subcommand: comment

Add comment to issue.

```
/popkit:issue comment 45 "Working on this"
/popkit:issue comment 45 --file notes.md
/popkit:issue comment 45 --phase-update "Completed implementation, moving to testing"
```

---

## Subcommand: edit

Update issue metadata.

```
/popkit:issue edit 45 --title "New title"
/popkit:issue edit 45 --label add:priority:high
/popkit:issue edit 45 --assignee @username
/popkit:issue edit 45 --milestone v1.0
```

---

## Subcommand: link

Link issue to PR.

```
/popkit:issue link 45 --pr 67
```

---

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

---

## Inference for Issues Without Guidance

When an issue lacks PopKit Guidance, infer from:

| Indicator | Inferred Complexity | Power Mode |
|-----------|---------------------|------------|
| Label: `epic` | epic | RECOMMENDED |
| Label: `architecture` | large | RECOMMENDED |
| Label: `bug` | small-medium | optional |
| Label: `feature` | medium | optional |
| Label: `docs` | small | not_needed |
| No labels | unknown | (unknown) |

---

## Examples

```bash
# List open issues with Power Mode recommendations
/popkit:issue
/popkit:issue list

# List only issues recommending Power Mode
/popkit:issue list --power

# View issue details
/popkit:issue view 45

# Create with template selection prompt
/popkit:issue create "Add user authentication"

# Create with specific template
/popkit:issue create "Refactor auth system" --template architecture

# Start working (auto-detect Power Mode)
/popkit:issue work 11

# Start working with forced Power Mode
/popkit:issue work 11 -p

# Start working in sequential mode
/popkit:issue work 11 --solo

# Close as superseded
/popkit:issue close 8 --superseded-by 11

# Add phase update comment
/popkit:issue comment 11 --phase-update "Completed Phase 1: Discovery"
```

---

## GitHub CLI Integration

All commands use `gh` CLI:

```bash
gh issue list --state open --json number,title,body,labels
gh issue view 45
gh issue create --title "..." --body "..." --template feature_request.md
gh issue close 45
gh issue comment 45 --body "..."
```

---

## Architecture Integration

| Component | Integration |
|-----------|-------------|
| Issue Fetching | `gh issue view/list` via GitHub CLI |
| PopKit Guidance Parser | `hooks/utils/github_issues.py` |
| Flag Parsing | `hooks/utils/flag_parser.py` |
| Issue Templates | `.github/ISSUE_TEMPLATE/*.md` |
| Phase Tracking | `STATUS.json` integration |
| Power Mode | `power-mode/coordinator.py` |
| Status Line | `power-mode/statusline.py` |
| State | `.claude/power-mode-state.json` |

## Related Commands

| Command | Purpose |
|---------|---------|
| `/popkit:power status` | Check Power Mode status |
| `/popkit:power stop` | Stop Power Mode |
| `/popkit:pr create` | Create pull request |
