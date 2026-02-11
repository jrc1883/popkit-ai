---
description: "create | list | view | close | comment | edit | link [--state, --label]"
argument-hint: "<subcommand> [#number] [options]"
---

# /popkit-dev:issue - GitHub Issue Management

Manage GitHub issues with AI-optimized formatting and PopKit workflow guidance.

## Usage

```
/popkit-dev:issue <subcommand> [options]
```

## Subcommands

| Subcommand | Description                      |
| ---------- | -------------------------------- |
| `list`     | List repository issues (default) |
| `view`     | View issue details               |
| `create`   | Create new issue with template   |
| `close`    | Close an issue                   |
| `comment`  | Add comment to issue             |
| `edit`     | Update issue metadata            |
| `link`     | Link issue to PR                 |

> **Note:** To start working on an issue, use `/popkit-dev:dev work #N` instead.

---

## Subcommand: list (default)

List repository issues with Power Mode recommendations.

```
/popkit-dev:issue                         # List open issues
/popkit-dev:issue list                    # Same as above
/popkit-dev:issue list --power            # Only issues recommending Power Mode
/popkit-dev:issue list --votes            # Sort by vote score
/popkit-dev:issue list --label bug        # Filter by label
/popkit-dev:issue list --state all        # All issues (open + closed)
/popkit-dev:issue list --assignee @me     # Assigned to me
/popkit-dev:issue list --milestone v1.0   # By milestone
/popkit-dev:issue list -n 10              # Limit results
```

### Flags

| Flag          | Short | Description                              |
| ------------- | ----- | ---------------------------------------- |
| `--power`     | `-p`  | Show only issues recommending Power Mode |
| `--votes`     | `-v`  | Sort by community vote score             |
| `--label`     | `-l`  | Filter by label                          |
| `--state`     |       | `open` (default), `closed`, `all`        |
| `--assignee`  |       | Filter by assignee                       |
| `--milestone` |       | Filter by milestone                      |
| `--limit`     | `-n`  | Limit results (default: 20)              |

### Output Format

**Standard Format:**

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

Hint: Use /popkit-dev:dev work #11 to start working
      Use /popkit-dev:dev work #11 -p to force Power Mode
```

**With --votes flag:**

```
Open Issues (sorted by community votes):

| #   | Title                          | Votes                  | Score |
|-----|--------------------------------|------------------------|-------|
| 88  | [Epic] Self-Improvement System | 👍12 ❤️3 🚀2           | 24    |
| 75  | Team Coordination Features     | 👍8  ❤️5 🚀1           | 21    |
| 66  | Power Mode v2                  | 👍6  ❤️2               | 10    |
| 92  | Vote-Based Prioritization      | 👍3                    | 3     |

Vote Weights: 👍 +1 | ❤️ +2 | 🚀 +3 | 👎 -1
```

### Process with Votes

When `--votes` flag is provided:

```python
from priority_scorer import get_priority_scorer, fetch_open_issues

# Fetch and rank by priority score
scorer = get_priority_scorer()
issues = fetch_open_issues(limit=20)
ranked = scorer.rank_issues(issues)

# Display sorted by score
print(scorer.format_ranked_list(ranked, max_items=10))
```

### Process

Use the `issue_list.py` utility:

```python
from issue_list import list_issues_with_power_mode_status, format_issues_table

# Fetch and format issues
data = list_issues_with_power_mode_status(
    filter_power=False,  # Set True for --power flag
    label=None,          # Filter by label
    state="open",        # open/closed/all
    limit=20
)
print(format_issues_table(data))
```

**Steps performed:**

1. Fetch issues via `gh issue list --json number,title,body,labels,createdAt,author`
2. Parse PopKit Guidance from each issue body
3. Extract complexity, phases, Power Mode recommendation
4. Generate formatted table

---

## Subcommand: view

View issue details with parsed PopKit Guidance.

```
/popkit-dev:issue view 45
/popkit-dev:issue view 45 --comments
/popkit-dev:issue view #45              # # prefix optional
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
/popkit-dev:issue create <title>
/popkit-dev:issue create "Add user authentication"
/popkit-dev:issue create --template bug
/popkit-dev:issue create --template feature
/popkit-dev:issue create --template architecture
/popkit-dev:issue create --template research
```

### Available Templates

| Template       | Use For                             | Labels             |
| -------------- | ----------------------------------- | ------------------ |
| `feature`      | New features, enhancements          | enhancement        |
| `bug`          | Bug reports, fixes                  | bug                |
| `architecture` | Major changes, epics, multi-PR work | architecture, epic |
| `research`     | Spikes, investigations, learning    | research           |

### Template Selection Flow

When creating without `--template`, prompt user:

```
What type of issue is this?
1. Feature - New capability or enhancement
2. Bug - Something isn't working correctly
3. Architecture - Major changes or epic initiative
4. Research - Investigation or spike
```

### Label Validation (Issue #96)

**CRITICAL:** Always validate labels BEFORE calling `gh issue create` to prevent errors.

**Implementation:**

```python
from popkit_shared.utils.github_validator import validate_labels
from popkit_shared.utils.github_cache import GitHubCache

# 1. Collect labels from template and user flags
requested_labels = get_labels_from_template(template)  # e.g., ["bug"]
if user_labels:
    requested_labels.extend(user_labels)  # e.g., ["priority:high"]

# 2. Validate using cache
cache = GitHubCache()
valid, invalid, suggestions = validate_labels(requested_labels, cache)

# 3. Handle invalid labels
if invalid:
    print(f"⚠️  Invalid labels: {', '.join(invalid)}")

    # Auto-fix with suggestions
    fixed_labels = valid.copy()
    for s in suggestions:
        if s['suggestions']:
            best_match = s['suggestions'][0]
            fixed_labels.append(best_match)
            print(f"   Auto-corrected: {s['invalid']} → {best_match}")

    # Ask user to confirm
    # Use AskUserQuestion: "Use corrected labels or cancel?"

    labels_to_use = fixed_labels
else:
    labels_to_use = valid

# 4. Create issue with validated labels
gh issue create --title "..." --body "..." --label {','.join(labels_to_use)}
```

**Example Output:**

```
Creating issue with labels: bug, priority:high

⚠️  Invalid labels: priority:high
   Auto-corrected: priority:high → P1-high

✓ Using labels: bug, P1-high
✓ Issue #123 created successfully
```

**Benefits:**

- ✅ Prevents "label does not exist" errors
- ✅ Catches typos with fuzzy matching
- ✅ Suggests correct alternatives
- ✅ Improves first-time success rate

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

## Subcommand: close

Close an issue with optional comment or reason.

```
/popkit-dev:issue close 45
/popkit-dev:issue close 45 --comment "Fixed in #PR"
/popkit-dev:issue close 45 --reason completed
/popkit-dev:issue close 45 --reason not_planned
/popkit-dev:issue close 45 --superseded-by 67
```

### Flags

| Flag              | Description                            |
| ----------------- | -------------------------------------- |
| `--comment`       | Add closing comment                    |
| `--reason`        | `completed` (default) or `not_planned` |
| `--superseded-by` | Reference replacement issue            |

### Process

1. **Parse Arguments**: Extract issue number, comment, reason
2. **Build Command**: Construct `gh issue close` with options
3. **Execute**: Run the close command
4. **Confirm**: Report success to user
5. **Prompt Next Action**: Use AskUserQuestion for workflow continuation

**Execute this command:**

```bash
gh issue close <number> [--comment "..."] [--reason completed|not_planned]
```

If `--superseded-by N` is provided, include in comment: "Superseded by #N"

### Post-Close Prompt (Required)

After successfully closing an issue, **always use AskUserQuestion** to guide the user's next action:

```
Use AskUserQuestion tool with:
- question: "Issue #N closed. What would you like to do next?"
- header: "Next Action"
- options:
  1. label: "Work on next issue"
     description: "Start working on another open issue"
  2. label: "View remaining issues"
     description: "List all open issues (/popkit-dev:issue list)"
  3. label: "End session"
     description: "Capture session state and finish"
- multiSelect: false
```

**Based on selection:**

- "Work on next issue" → Fetch open issues, present top 3-5 as options via another AskUserQuestion
- "View remaining issues" → Execute `/popkit-dev:issue list`
- "End session" → Invoke `pop-session-capture` skill

---

## Subcommand: comment

Add comment to issue.

```
/popkit-dev:issue comment 45 "Working on this"
/popkit-dev:issue comment 45 --file notes.md
/popkit-dev:issue comment 45 --phase-update "Completed implementation, moving to testing"
```

### Flags

| Flag             | Description                       |
| ---------------- | --------------------------------- |
| `--file`         | Read comment body from file       |
| `--phase-update` | Format as phase transition update |

### Process

1. **Parse Arguments**: Extract issue number, comment text or file
2. **Format Comment**: If `--phase-update`, prefix with "## Phase Update\n\n"
3. **Execute**: Run `gh issue comment`
4. **Confirm**: Report success

**Execute this command:**

```bash
gh issue comment <number> --body "<comment>"
# OR with file:
gh issue comment <number> --body-file <file>
```

---

## Subcommand: edit

Update issue metadata.

```
/popkit-dev:issue edit 45 --title "New title"
/popkit-dev:issue edit 45 --label add:priority:high
/popkit-dev:issue edit 45 --label remove:wontfix
/popkit-dev:issue edit 45 --assignee @username
/popkit-dev:issue edit 45 --milestone v1.0
```

### Flags

| Flag          | Description                                    |
| ------------- | ---------------------------------------------- |
| `--title`     | Update issue title                             |
| `--label`     | Add/remove label (`add:name` or `remove:name`) |
| `--assignee`  | Set assignee                                   |
| `--milestone` | Set milestone                                  |
| `--body`      | Update issue body                              |

### Process

1. **Parse Arguments**: Extract issue number and edit flags
2. **Validate Labels** (Issue #96): If adding labels, validate them first
3. **Build Command**: Construct `gh issue edit` with appropriate flags
4. **Execute**: Run the edit command
5. **Confirm**: Report changes made

**Label Validation (when using `--label add:name`):**

```python
from popkit_shared.utils.github_validator import validate_labels
from popkit_shared.utils.github_cache import GitHubCache

# Parse labels to add
labels_to_add = parse_label_flags(args)  # e.g., ["priority:high", "needs-review"]

if labels_to_add:
    cache = GitHubCache()
    valid, invalid, suggestions = validate_labels(labels_to_add, cache)

    if invalid:
        # Show suggestions and auto-correct
        for s in suggestions:
            if s['suggestions']:
                print(f"⚠️  {s['invalid']} → {s['suggestions'][0]}")

# Proceed with validated labels
```

**Execute this command:**

```bash
gh issue edit <number> [--title "..."] [--add-label <name>] [--remove-label <name>] [--assignee <user>] [--milestone <name>]
```

---

## Subcommand: link

Link issue to PR by adding a comment with the reference.

```
/popkit-dev:issue link 45 --pr 67
/popkit-dev:issue link 45 --closes-pr 67
```

### Flags

| Flag          | Description                                |
| ------------- | ------------------------------------------ |
| `--pr`        | PR number to link (adds reference comment) |
| `--closes-pr` | PR that closes this issue                  |

### Process

1. **Parse Arguments**: Extract issue number and PR number
2. **Format Link**: Create reference comment
3. **Execute**: Add comment to issue with PR reference
4. **Confirm**: Report link created

**Execute this command:**

```bash
gh issue comment <issue> --body "Related: #<pr>"
# OR for closing reference:
gh issue comment <issue> --body "Closes: #<pr>"
```

Note: GitHub automatically links issues and PRs when referenced in commits/PR descriptions.

---

## Agent Routing

Based on issue content and labels:

| Indicator                       | Primary Agent         | Supporting                               |
| ------------------------------- | --------------------- | ---------------------------------------- |
| `[Bug]` label or "bug" in title | bug-whisperer         | test-writer-fixer                        |
| `[Feature]` label               | code-architect        | test-writer-fixer                        |
| `[Architecture]` label          | code-architect        | migration-specialist, refactoring-expert |
| `[Research]` label              | researcher            | code-explorer                            |
| Security keywords               | security-auditor      | code-reviewer                            |
| Performance keywords            | performance-optimizer | bundle-analyzer                          |
| API keywords                    | api-designer          | documentation-maintainer                 |
| Database keywords               | query-optimizer       | migration-specialist                     |

---

## Inference for Issues Without Guidance

When an issue lacks PopKit Guidance, infer from:

| Indicator             | Inferred Complexity | Power Mode  |
| --------------------- | ------------------- | ----------- |
| Label: `epic`         | epic                | RECOMMENDED |
| Label: `architecture` | large               | RECOMMENDED |
| Label: `bug`          | small-medium        | optional    |
| Label: `feature`      | medium              | optional    |
| Label: `docs`         | small               | not_needed  |
| No labels             | unknown             | (unknown)   |

---

## Examples

```bash
# List open issues with Power Mode recommendations
/popkit-dev:issue
/popkit-dev:issue list

# List only issues recommending Power Mode
/popkit-dev:issue list --power

# View issue details
/popkit-dev:issue view 45

# Create with template selection prompt
/popkit-dev:issue create "Add user authentication"

# Create with specific template
/popkit-dev:issue create "Refactor auth system" --template architecture

# Close as superseded
/popkit-dev:issue close 8 --superseded-by 11

# Add phase update comment
/popkit-dev:issue comment 11 --phase-update "Completed Phase 1: Discovery"
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

| Component              | Integration                                            |
| ---------------------- | ------------------------------------------------------ |
| Issue Listing          | `hooks/utils/issue_list.py`                            |
| Issue Fetching         | `gh issue view/list` via GitHub CLI                    |
| PopKit Guidance Parser | `hooks/utils/github_issues.py`                         |
| Vote Fetching          | `hooks/utils/vote_fetcher.py`                          |
| Priority Scoring       | `hooks/utils/priority_scorer.py`                       |
| Flag Parsing           | `hooks/utils/flag_parser.py`                           |
| Issue Templates        | `.github/ISSUE_TEMPLATE/*.md`                          |
| Phase Tracking         | `STATUS.json` integration                              |
| Power Mode             | `power-mode/coordinator.py`                            |
| Status Line            | `power-mode/statusline.py`                             |
| State                  | `.claude/popkit/power-mode-state.json`                 |
| **GitHub Cache**       | `popkit_shared.utils.github_cache` **(Issue #96)**     |
| **Label Validation**   | `popkit_shared.utils.github_validator` **(Issue #96)** |
| Cache Storage          | `.claude/popkit/github-cache.json` (60 min TTL)        |

## Related Commands

| Command                     | Purpose                   |
| --------------------------- | ------------------------- |
| `/popkit-dev:dev work #N`   | Start working on an issue |
| `/popkit-core:power status` | Check Power Mode status   |
| `/popkit-dev:git pr`        | Create pull request       |
