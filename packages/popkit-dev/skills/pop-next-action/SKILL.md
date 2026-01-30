---
name: pop-next-action
description: "Context-aware recommendation engine that analyzes git status, TypeScript errors, GitHub issues, and technical debt to suggest prioritized next actions. Returns specific popkit commands with explanations of why each is relevant. Use when unsure what to work on next, starting a session, or feeling stuck. Do NOT use when you already know what to do - just proceed with that task directly."
---

# Next Action Recommendation

## Overview

Analyzes current project state and provides prioritized, context-aware recommendations for what to work on next. Returns actionable popkit commands with explanations.

**Core principle:** Don't just list commands - recommend the RIGHT command based on actual project state.

**Trigger:** When user expresses uncertainty ("what should I do", "where to go", "stuck") or runs `/popkit:next`.

## When to Use

Invoke this skill when:

- User asks "what should I do next?"
- User seems stuck or unsure of direction
- User mentions "popkit" and needs guidance
- Starting a new session and need orientation
- Returning to a project after time away

**Do NOT use when** user already knows what to do - just proceed with that task directly.

## Analysis Process

**Three-step workflow:**

1. **Gather Project State** - Collect git status, branch info, TypeScript errors, GitHub issues, technical debt, research branches
2. **Detect Project Context** - Identify protected branches, uncommitted work, build errors, research to merge, issue votes
3. **Score & Recommend** - Calculate relevance scores and return top 3-5 recommendations with explanations

## Context Detection

| Indicator | What It Means | Weight |
|-----------|---------------|--------|
| **On protected branch** | **Requires feature branch** | **CRITICAL** |
| Uncommitted changes | Active work in progress | HIGH |
| TypeScript errors | Build broken | HIGH |
| **Research branches** | Web session findings to process | HIGH |
| Ahead of remote | Ready to push/PR | MEDIUM |
| Open issues | Known work items | MEDIUM |
| **Issue votes** | Community priority (👍=1pt, ❤️=2pt, 🚀=3pt) | MEDIUM |
| TECHNICAL_DEBT.md | Documented debt | MEDIUM |

## Scoring Algorithm

```
Score = Base Priority + Context Multipliers

Base Priorities:
- Create feature branch (if on protected): 100  # HIGHEST
- Fix build errors: 90
- Process research branches: 85
- Commit uncommitted work: 80
- Push ahead commits (if on feature branch): 60
- Address open issues: 50
- Tackle tech debt: 40
- Start new feature: 30

Context Multipliers:
- On protected branch with commits: +50 to branch creation
- Has uncommitted changes: +20 to commit
- Build failing: +30 to fix
- Research branches detected: +20 to process
- High-voted issues: +10 to +30 based on votes
- Stale issues: +5 to +15 based on age
```

## Research Branch Detection (Issue #181)

Detects research branches from Claude Code Web sessions:

**Patterns:**
- `origin/claude/research-*` - Explicit research branches
- `origin/claude/*-research-*` - Topic-specific research
- Branches with `docs/research/*.md` or `RESEARCH*.md` files

**Integration:**
```python
from popkit_shared.utils.research_branch_detector import (
    get_research_branches,
    format_branch_table
)

branches = get_research_branches()
if branches:
    print(format_branch_table(branches))
    print("Use `pop-research-merge` skill to process them.")
```

## Issue Prioritization (NEW)

Fetches community votes to prioritize issues:

```python
from popkit_shared.utils.priority_scorer import get_priority_scorer, fetch_open_issues

scorer = get_priority_scorer()
issues = fetch_open_issues(limit=10)
ranked = scorer.rank_issues(issues)  # Combines votes + staleness + labels
```

**Vote Weights:** 👍=1pt, ❤️=2pt, 🚀=3pt, 👎=-1pt

## Output Format

Returns top 3-5 recommendations with:

- **Command** - Exact popkit command to run
- **Why** - Explanation based on detected context
- **Priority** - Critical/High/Medium/Low
- **Score** - Calculated relevance score

Example:
```
1. [CRITICAL] Create feature branch (Score: 150)
   Command: /popkit:git branch create feature/fix-build-errors
   Why: Currently on protected branch 'main' with 5 uncommitted files

2. [HIGH] Fix TypeScript errors (Score: 120)
   Command: /popkit:dev fix-errors
   Why: 12 TypeScript errors detected, build is broken

3. [HIGH] Process research branch (Score: 105)
   Command: /popkit:research merge claude/research-api-design
   Why: Research branch contains findings from web session
```

## Session Recording Integration (Issue #180)

Records all analysis steps for observability:

- Git status analysis (uncommitted files, branch protection)
- Context file reads (STATUS.json, TECHNICAL_DEBT.md)
- Research branch detection
- Issue prioritization decisions
- Final recommendation scores

Uses `popkit_shared.utils.session_recorder` for structured logging.

## Related Skills

- **pop-research-merge**: Process detected research branches
- **pop-morning**: Start-of-day orientation (includes next action)
- **pop-git-branch**: Create feature branches when on protected branch

## Related Commands

- **/popkit:next**: Main entry point
- **/popkit:routine morning**: Includes next action recommendations
- **/popkit:research merge**: Process research branches

## Success Criteria

✅ Analyzes current project state accurately
✅ Detects protected branches and recommends feature branch creation
✅ Identifies research branches from web sessions
✅ Prioritizes issues by community votes
✅ Returns 3-5 actionable recommendations
✅ Provides clear explanations for each recommendation
✅ Records all analysis steps for observability

---

**Skill Type**: Decision Support
**Category**: Workflow Automation
**Tier**: Core (Always Available)
**Version**: 2.1.0
