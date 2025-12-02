---
description: Work on a GitHub issue with optional Power Mode - unified command for issue-driven development
---

# /popkit:work - Work on GitHub Issue

Start working on a GitHub issue with intelligent Power Mode detection based on PopKit Guidance.

## Usage

```
/popkit:work #N [flags]
/popkit:work <issue-number> [flags]
```

## Arguments

Parse from `$ARGUMENTS`:

| Argument | Format | Description |
|----------|--------|-------------|
| Issue number | `#4`, `gh-4`, or `4` | GitHub issue to work on |

## Flags

| Flag | Short | Description |
|------|-------|-------------|
| `--power` | `-p` | Force Power Mode activation |
| `--solo` | `-s` | Force sequential mode (no Power Mode) |
| `--phases` | | Override phases: `--phases explore,implement,test` |
| `--agents` | | Override agents: `--agents reviewer,tester` |

## Examples

```bash
# Auto-detect Power Mode from issue's PopKit Guidance
/popkit:work #4

# Force Power Mode regardless of guidance
/popkit:work #4 -p
/popkit:work #4 --power

# Force sequential execution (no Power Mode)
/popkit:work #4 --solo

# Override phases
/popkit:work #4 --phases implement,test,review

# Combine flags
/popkit:work #4 -p --phases design,implement
```

## Process

### Step 1: Parse Arguments

Extract from `$ARGUMENTS`:
- Issue number (required): `#4`, `gh-4`, or just `4`
- Flags: `-p`/`--power`, `-s`/`--solo`, `--phases`, `--agents`

### Step 2: Fetch Issue

```bash
gh issue view <number> --json number,title,body,labels,state,author
```

### Step 3: Parse PopKit Guidance

If issue body contains `## PopKit Guidance` section:
- Extract workflow type (brainstorm_first, plan_required, direct)
- Extract phases (discovery, architecture, implementation, etc.)
- Extract suggested agents (primary, supporting)
- Extract quality gates
- Extract Power Mode recommendation
- Extract complexity

### Step 4: Determine Power Mode

**Decision priority:**
1. Command flags override everything:
   - `-p` or `--power` → Force Power Mode ON
   - `-s` or `--solo` → Force Power Mode OFF
2. If no flags, use PopKit Guidance:
   - `power_mode: recommended` → Power Mode ON
   - `complexity: epic` → Power Mode ON
   - 3+ agents → Power Mode ON
3. If no guidance, auto-generate plan:
   - Infer issue type from labels/title
   - Recommend Power Mode for large/epic complexity
4. Default to sequential mode

### Step 5: Configure Workflow

**If Power Mode activated:**
```
[+] POWER MODE ACTIVATED
Issue: #4 - Add user authentication
Source: PopKit Guidance (recommended) | Flag (-p) | Auto-generated

Phases: discovery -> architecture -> implementation -> testing -> review
Agents: code-architect (primary), test-writer-fixer (supporting)
Quality Gates: typescript, build, lint, test

Redis: localhost:16379 [OK]
Status line: [POP] #4 Phase: discovery (1/5) [----------] 0%
```

**If sequential mode:**
```
[+] WORKING ON ISSUE #4
Title: Add user authentication
Mode: Sequential (no Power Mode)

Phases: discovery -> architecture -> implementation -> testing -> review
Agent: code-architect (primary)

Ready to begin Phase 1: Discovery
```

### Step 6: Create Todo List

Generate todos from phases:
```
- [ ] Discovery: Explore codebase and gather requirements
- [ ] Architecture: Design implementation approach
- [ ] Implementation: Build the feature
- [ ] Testing: Write and run tests
- [ ] Review: Final code review
```

### Step 7: Begin Work

If brainstorming required:
```
PopKit Guidance requires brainstorming first.
Invoking pop-brainstorming skill...
```

Otherwise, start first phase.

## Output

### Power Mode Start
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

### Sequential Mode Start
```
[+] WORKING ON ISSUE #4
Title: Add user authentication
Mode: Sequential

Phases: 5 (discovery -> review)
Agent: code-architect

Starting Phase 1: Discovery...
```

## Relationship to Other Commands

| Command | Relationship |
|---------|--------------|
| `/popkit:issue work #N` | Alias - same behavior |
| `/popkit:power status` | Check Power Mode status |
| `/popkit:power stop` | Stop Power Mode |
| `/popkit:issues` | List issues to find issue numbers |

## Architecture Integration

| Component | Integration |
|-----------|-------------|
| Flag Parsing | `hooks/utils/flag_parser.py` |
| Issue Fetching | `gh issue view` via GitHub CLI |
| Guidance Parsing | `hooks/utils/github_issues.py` |
| Power Mode | `power-mode/coordinator.py` |
| Status Line | `power-mode/statusline.py` |
| State | `.claude/power-mode-state.json` |
