---
description: 7-phase feature development workflow - Discovery through Summary
---

# /popkit:feature-dev - Complete Feature Development

End-to-end feature development using the 7-phase workflow.

## Usage

```
/popkit:feature-dev [feature-name]
/popkit:feature-dev "user authentication"
/popkit:feature-dev "payment integration" -T  # With extended thinking
```

## Flags

| Flag | Description |
|------|-------------|
| `-T`, `--thinking` | Enable extended thinking for architecture decisions and design phases |
| `--no-thinking` | Disable extended thinking (use default) |
| `--think-budget N` | Set thinking token budget (default: 10000) |

## The 7 Phases

### Phase 1: Discovery

**Goal:** Understand what to build

```
What feature would you like to build?
> User authentication with OAuth

Let me gather context about the project...
- Project: Next.js 14 with Supabase
- Existing auth: None
- Related: User model exists
```

### Phase 2: Exploration

**Goal:** Understand the codebase

Uses **code-explorer** agent:

```
Exploring codebase for similar features...

Entry Points:
- `src/app/api/auth/route.ts` (new)
- `src/components/auth/` (to create)

Patterns Found:
- API routes use standard Response format
- Components use server actions
- Database uses Supabase client

Files to Read:
- `src/lib/supabase.ts` - Client setup
- `src/types/user.ts` - User model
```

### Phase 3: Questions

**Goal:** Clarify requirements

```
A few questions to clarify the implementation:

1. Which OAuth providers should we support?
   a) Google only
   b) Google + GitHub
   c) All major providers

2. Should we support email/password as well?
   a) Yes
   b) No, OAuth only

3. Where should users be redirected after login?
   a) Dashboard
   b) Previous page
   c) Custom URL

> 1b, 2a, 3a
```

### Phase 4: Architecture

**Goal:** Design the implementation

Uses **code-architect** agent:

```
Designing architecture...

## Architecture Design: User Authentication

### Approach: Pragmatic Balance

### Component Design

| Component | Purpose | Location |
|-----------|---------|----------|
| AuthProvider | Context for auth state | `src/providers/` |
| LoginForm | Email/password form | `src/components/auth/` |
| OAuthButtons | Google/GitHub buttons | `src/components/auth/` |

### Implementation Map

Phase 1: Setup Supabase Auth
Phase 2: Create components
Phase 3: Add API routes
Phase 4: Wire up providers

Do you approve this architecture? [y/N]
```

### Phase 5: Implementation

**Goal:** Build the feature

```
Creating worktree for isolated development...
✓ .worktrees/feature-user-auth created
✓ npm install complete
✓ Tests passing (baseline)

Generating implementation plan...
✓ Plan saved to docs/plans/2025-01-15-user-auth.md

Executing plan...
[Task-by-task implementation with TDD]
```

### Phase 6: Review

**Goal:** Verify quality

Uses **code-reviewer** agent:

```
Reviewing implementation...

## Code Review: User Authentication

### Summary
Clean implementation with 95% test coverage.

### Critical Issues: 0
### Important Issues: 1
- Token refresh could be more robust

### Assessment
Ready to merge with minor improvements.

Quality Score: 8/10
```

### Phase 7: Summary

**Goal:** Complete and document

```
Feature development complete!

## Summary

### What Was Built
- OAuth login (Google, GitHub)
- Email/password authentication
- Session management
- Protected routes

### Files Created
- 8 new files
- 3 files modified
- 47 tests added

### Next Steps
Options:
1. Merge to main
2. Create PR for review
3. Keep branch for more work
4. Discard

Which option?
```

## Architecture Integration

| Component | Integration |
|-----------|-------------|
| Agent: code-explorer | Phase 2 - Codebase exploration |
| Agent: code-architect | Phase 4 - Architecture design |
| Agent: code-reviewer | Phase 6 - Code review |
| Skill: pop-brainstorming | Phase 1 - Discovery and ideation |
| Skill: pop-writing-plans | Phase 5 - Implementation plan generation |
| Skill: pop-executing-plans | Phase 5 - Plan execution |
| Skill: pop-finish-branch | Phase 7 - Completion workflow |
| Command: /popkit:worktree | Creates isolated workspace |
| Command: /popkit:plan | Generates implementation plans |
| Command: /popkit:review | Final quality check |
| Hooks: issue-workflow.py | Phase tracking and status updates |
| State: power-mode-state.json | Phase progress for status line |

## Executable Commands

### Phase 1: Discovery
```bash
# Gather project context
cat package.json | head -20
cat README.md | head -50
git log --oneline -10
```

### Phase 2: Exploration
**Invoke agent:**
```
Use Task tool with subagent_type="Explore"
Prompt: "Explore the codebase to understand patterns for [feature]"
```

### Phase 4: Architecture
**Invoke agent:**
```
Use Task tool with subagent_type="Plan"
Prompt: "Design architecture for [feature] based on exploration findings"
```

### Phase 5: Implementation
```bash
# Create isolated worktree
git worktree add .worktrees/feature-<name> -b feature/<name>
cd .worktrees/feature-<name>

# Install dependencies
npm install  # or pip install, cargo build

# Verify baseline tests
npm test

# Generate implementation plan
# Invoke pop-writing-plans skill

# Execute plan in batches
# Invoke pop-executing-plans skill
```

### Phase 6: Review
**Invoke agent:**
```
Use Task tool with subagent_type="code-reviewer"
Prompt: "Review implementation of [feature] against architecture design"
```

### Phase 7: Summary
```bash
# Check final status
git status
npm test
npm run build

# Options:
# 1. Merge: git checkout main && git merge feature/<name>
# 2. PR: gh pr create --title "[Feature] <name>" --body "..."
# 3. Keep: Leave worktree for more work
# 4. Discard: git worktree remove .worktrees/feature-<name>
```

## Related Commands

| Command | Relationship |
|---------|--------------|
| `/popkit:design brainstorm` | Use before Phase 1 for complex features |
| `/popkit:plan write` | Detailed implementation plan (Phase 5) |
| `/popkit:review` | Code review after implementation |
| `/popkit:git finish` | Complete and merge branch |
| `/popkit:issue work` | Start from GitHub issue with phase tracking |
