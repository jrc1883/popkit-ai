---
description: Implementation planning - write detailed plans and execute them in batches with review checkpoints
---

# /popkit:plan - Implementation Planning

Create and execute comprehensive implementation plans with exact file paths, code examples, and verification steps.

## Usage

```
/popkit:plan <subcommand> [options]
```

## Subcommands

| Subcommand | Description |
|------------|-------------|
| `write` | Create detailed implementation plan (default) |
| `execute` | Execute plan in batches with review checkpoints |
| `list` | List existing plans |
| `view` | View a specific plan |

---

## Subcommand: write (default)

Generate comprehensive implementation plans for engineers with zero codebase context.

```
/popkit:plan                          # Interactive planning
/popkit:plan write                    # Same as above
/popkit:plan write user-auth          # From topic
/popkit:plan write --from design.md   # From design doc
/popkit:plan write --issue 45         # From GitHub issue
```

### Process

Invokes the **pop-writing-plans** skill:

1. Load design document or gather requirements
2. Break into bite-sized tasks (2-5 minutes each)
3. Include exact file paths
4. Provide complete code examples
5. Add verification commands
6. Save to `docs/plans/YYYY-MM-DD-<feature>.md`

### Plan Structure

```markdown
# [Feature] Implementation Plan

> **For Claude:** Use /popkit:plan execute to implement.

**Goal:** [One sentence]
**Architecture:** [2-3 sentences]
**Tech Stack:** [Technologies]

---

### Task 1: [Component Name]

**Files:**
- Create: `exact/path/to/file.ts`
- Modify: `existing/file.ts:50-75`
- Test: `tests/file.test.ts`

**Step 1: Write the failing test**
```typescript
// Complete test code
```

**Step 2: Run test to verify it fails**
Run: `npm test -- file.test.ts`
Expected: FAIL

**Step 3: Write minimal implementation**
```typescript
// Complete implementation
```

**Step 4: Run test to verify it passes**
Run: `npm test -- file.test.ts`
Expected: PASS

**Step 5: Commit**
```bash
git commit -m "feat: add component"
```

---

### Task 2: ...
```

### Principles

- **DRY** - Don't repeat yourself
- **YAGNI** - You ain't gonna need it
- **TDD** - Test-driven development
- **Frequent commits** - After each task

### Output

Creates plan at `docs/plans/YYYY-MM-DD-<feature>.md`

Then offers execution options:
1. **Execute Now** - Run `/popkit:plan execute`
2. **Subagent-Driven** - Same session, fresh subagent per task
3. **Later** - Save plan for future execution

---

## Subcommand: execute

Execute implementation plans in controlled batches with review checkpoints.

```
/popkit:plan execute                              # Select from recent plans
/popkit:plan execute docs/plans/2025-01-15-auth.md
/popkit:plan execute --batch-size 5               # Larger batches
/popkit:plan execute --start-at 4                 # Resume from task 4
/popkit:plan execute --dry-run                    # Preview without executing
```

### Options

| Option | Description |
|--------|-------------|
| `--batch-size N` | Tasks per batch (default: 3) |
| `--start-at N` | Resume from task N |
| `--dry-run` | Preview without executing |

### Process

Invokes the **pop-executing-plans** skill:

#### Step 1: Load and Review

```
Loading plan: docs/plans/2025-01-15-auth.md

Plan Summary:
- Goal: Add user authentication
- Tasks: 8
- Estimated: 2-3 hours

Review Questions:
- [Any concerns about the plan]

Proceed with execution? [y/N]
```

#### Step 2: Execute Batch

Default: 3 tasks per batch

```
Executing Batch 1 (Tasks 1-3):

Task 1: Create auth context [in_progress]
- Writing test...
- Test fails as expected
- Implementing...
- Test passes
- Committed: abc123

Task 1: Complete

Task 2: Add login form [in_progress]
...
```

#### Step 3: Report and Review

```
Batch 1 Complete:
[ok] Task 1: Create auth context
[ok] Task 2: Add login form
[ok] Task 3: Add validation

Commits: 3
Tests: 12 passing

Ready for feedback.
```

User provides feedback -> apply changes -> continue.

#### Step 4: Repeat

Continue with next batch until all tasks complete.

#### Step 5: Finish

After all tasks:
- Run final verification
- Present completion options (merge, PR, keep, discard)
- Invoke `/popkit:git finish` flow

### Handling Blockers

If blocked mid-batch:
1. Stop immediately
2. Report the blocker
3. Ask for clarification
4. Don't guess or work around

---

## Subcommand: list

List existing plans.

```
/popkit:plan list                     # All plans
/popkit:plan list --recent            # Last 5 plans
/popkit:plan list --status pending    # Unexecuted plans
```

### Output

```
Implementation Plans:

| Date       | Feature              | Tasks | Status      |
|------------|----------------------|-------|-------------|
| 2025-01-15 | user-auth            | 8     | in_progress |
| 2025-01-10 | dark-mode            | 5     | completed   |
| 2025-01-05 | api-refactor         | 12    | pending     |

Use /popkit:plan view <name> to see details
Use /popkit:plan execute <path> to execute
```

---

## Subcommand: view

View a specific plan.

```
/popkit:plan view user-auth
/popkit:plan view docs/plans/2025-01-15-user-auth.md
```

### Output

```
Plan: user-auth
Created: 2025-01-15
Status: in_progress (4/8 tasks complete)

Goal: Add user authentication with JWT tokens

Tasks:
1. [ok] Create auth context
2. [ok] Add login form
3. [ok] Add validation
4. [ok] Implement JWT generation
5. [ ] Add protected routes
6. [ ] Create logout flow
7. [ ] Add password reset
8. [ ] Write integration tests

Next: Task 5 - Add protected routes

Commands:
  /popkit:plan execute --start-at 5   Resume execution
  cat docs/plans/2025-01-15-user-auth.md   View full plan
```

---

## Integration with Skills

| Skill | Purpose |
|-------|---------|
| `pop-writing-plans` | Core planning skill |
| `pop-executing-plans` | Core execution skill |
| `pop-test-driven-development` | For each task |
| `pop-verify-completion` | After each batch |
| `pop-finish-branch` | At completion |
| `pop-brainstorming` | Pre-planning design refinement |

---

## Examples

```bash
# Create plan interactively
/popkit:plan
/popkit:plan write

# Create plan from topic
/popkit:plan write user-authentication

# Create plan from design doc
/popkit:plan write --from docs/design/auth-system.md

# Execute most recent plan
/popkit:plan execute

# Execute specific plan with larger batches
/popkit:plan execute docs/plans/2025-01-15-auth.md --batch-size 5

# Resume from task 4
/popkit:plan execute --start-at 4

# Preview execution without changes
/popkit:plan execute --dry-run

# List all plans
/popkit:plan list

# View specific plan
/popkit:plan view user-auth
```

---

## Architecture Integration

| Component | Integration |
|-----------|-------------|
| Plan Storage | `docs/plans/YYYY-MM-DD-<feature>.md` |
| Writing Skill | `skills/pop-writing-plans/SKILL.md` |
| Executing Skill | `skills/pop-executing-plans/SKILL.md` |
| TDD Skill | `skills/pop-test-driven-development/SKILL.md` |
| Verification Skill | `skills/pop-verify-completion/SKILL.md` |
| Progress Tracking | Todo list integration |

## Related Commands

| Command | Purpose |
|---------|---------|
| `/popkit:git finish` | Complete branch after execution |
| `/popkit:issue work` | Start from GitHub issue |
| `/popkit:brainstorm` | Design refinement before planning |
