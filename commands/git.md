---
description: Git workflow management - commit, push, PR management, code review, branch cleanup, and development completion
---

# /popkit:git - Git Workflow Management

Comprehensive git operations with smart commits, PR management, code review, branch cleanup, and development completion.

## Usage

```
/popkit:git <subcommand> [options]
```

## Subcommands

| Subcommand | Description |
|------------|-------------|
| `commit` | Smart commit with auto-generated message (default) |
| `push` | Push current branch to remote |
| `pr` | Pull request management (create, list, view, merge) |
| `review` | Code review with confidence-based filtering |
| `prune` | Remove stale local branches after PR merge |
| `finish` | Complete development with 4-option flow |

---

## Subcommand: commit (default)

Generate commit message from staged changes, following repository conventions.

```
/popkit:git                           # Auto-generate commit message
/popkit:git commit                    # Same as above
/popkit:git commit "fixed the login"  # Use hint for message
/popkit:git commit --amend            # Amend previous commit
```

### Process

1. **Check Status**
   ```bash
   git status --porcelain
   git diff --cached --stat
   ```

2. **Analyze Changes**
   - Count files changed
   - Identify change types (new, modified, deleted)
   - Detect patterns (feat, fix, refactor, etc.)

3. **Generate Message**
   Following conventional commits:
   ```
   <type>(<scope>): <subject>

   <body>

   <footer>
   ```
   Types: feat, fix, docs, style, refactor, perf, test, chore, ci, revert

4. **Commit**
   ```bash
   git commit -m "$(cat <<'EOF'
   <generated message>

   Generated with Claude Code

   Co-Authored-By: Claude <noreply@anthropic.com>
   EOF
   )"
   ```

### Attribution

All commits include:
- Claude Code attribution link
- Co-Authored-By header

---

## Subcommand: push

Push current branch to remote.

```
/popkit:git push                      # Push current branch
/popkit:git push --force-with-lease   # Force push safely
/popkit:git push -u                   # Set upstream
```

### Safety

- Warns before pushing to main/master
- Uses `--force-with-lease` instead of `--force`
- Confirms if branch has no upstream

---

## Subcommand: pr

Full pull request management - create, list, view, merge, and more.

### pr create (default for pr)

Create new pull request:

```
/popkit:git pr                        # Create PR from current branch
/popkit:git pr create                 # Same as above
/popkit:git pr create --title "Add auth"
/popkit:git pr create --draft         # As draft
/popkit:git pr create --base develop  # Target branch
```

**Process:**
1. Verify clean state
2. Create/switch branch (if needed)
3. Stage changes
4. Generate commit
5. Push branch
6. Create PR with template

**PR Template:**
```markdown
## Summary
<2-3 bullet points describing changes>

## Changes
- `file.ts`: <what changed>

## Test Plan
- [ ] Unit tests pass
- [ ] Manual testing completed

## Related Issues
Closes #<issue-number>

---
Generated with Claude Code
```

### pr list

List pull requests:

```
/popkit:git pr list                   # Open PRs
/popkit:git pr list --state all       # All PRs
/popkit:git pr list --author @me      # My PRs
/popkit:git pr list --review-requested
/popkit:git pr list --draft           # Draft PRs only
```

Output:
```
Open PRs (5):
#67 [ready] Add authentication - @user - 2 reviews
#66 [draft] Refactor API - @user - 0 reviews
#65 [changes] Fix login bug - @user - 1 review
```

### pr view

View PR details:

```
/popkit:git pr view 67
/popkit:git pr view 67 --comments
/popkit:git pr view 67 --files
/popkit:git pr view 67 --checks
```

Output:
```
#67: Add authentication
State: open (ready for review)
Author: @username
Base: main <- feature/auth
Created: 2 days ago

Checks:
[ok] CI / build
[ok] CI / test
[ok] CI / lint

Reviews:
[ok] @reviewer1: approved
[...] @reviewer2: pending

Files changed (5):
+120 -45 src/auth/login.ts
```

### pr merge

Merge pull request:

```
/popkit:git pr merge 67               # Default merge
/popkit:git pr merge 67 --squash      # Squash and merge
/popkit:git pr merge 67 --rebase      # Rebase and merge
/popkit:git pr merge 67 --delete-branch
```

**Pre-merge checks:**
1. All required reviews approved
2. All status checks passing
3. No merge conflicts
4. Branch is up to date

### pr checkout

Check out PR locally:

```
/popkit:git pr checkout 67
```

### pr diff

View PR diff:

```
/popkit:git pr diff 67
/popkit:git pr diff 67 --file src/auth.ts
```

### pr ready

Mark PR as ready for review (from draft):

```
/popkit:git pr ready 67
```

### pr update

Update PR branch with base:

```
/popkit:git pr update 67
```

---

## Subcommand: review

Code review with confidence-based issue filtering.

```
/popkit:git review                    # Review uncommitted changes
/popkit:git review --staged           # Review staged changes only
/popkit:git review --branch feature/auth
/popkit:git review --pr 67            # Review PR changes
/popkit:git review --file src/auth.ts # Review specific file
```

### Process

Invokes the **code-review** skill:

1. **Gather Changes**
   ```bash
   git diff HEAD~1...HEAD         # For branch review
   git diff --cached              # For staged
   git diff                       # For uncommitted
   ```

2. **Analyze Categories**
   - **Simplicity/DRY/Elegance** - Duplication, complexity, abstractions
   - **Bugs/Correctness** - Logic errors, edge cases, type safety
   - **Conventions** - Project patterns, naming, organization

3. **Score and Filter**
   Each issue gets confidence score (0-100):
   - 0-49: Ignored (likely false positive)
   - 50-79: Noted but not reported
   - 80-89: Important (should fix)
   - 90-100: Critical (must fix)

   **Threshold: 80+** only reported.

4. **Report**

### Output

```markdown
## Code Review: Feature Auth

### Summary
Clean implementation with good test coverage. Two issues found.

### Critical Issues (Must Fix)

#### Issue 1: Missing null check
- **File**: `src/auth.ts:45`
- **Confidence**: 95/100
- **Category**: Bug/Correctness
- **Description**: `user.email` accessed without null check
- **Fix**: Add optional chaining or null check

### Important Issues (Should Fix)

#### Issue 2: Duplicate validation logic
- **File**: `src/auth.ts:60-75`
- **Confidence**: 82/100
- **Category**: Simplicity/DRY
- **Description**: Email validation duplicated from utils
- **Fix**: Import and use existing validateEmail()

### Assessment

**Ready to merge?** With fixes
**Quality Score: 7/10**
```

### Options

```
/popkit:git review --focus simplicity     # Focus on DRY/elegance
/popkit:git review --focus correctness    # Focus on bugs
/popkit:git review --focus conventions    # Focus on patterns
/popkit:git review --threshold 70         # Lower confidence threshold
/popkit:git review --verbose              # Include lower-confidence issues
```

---

## Subcommand: prune

Remove stale local branches after PRs are merged.

```
/popkit:git prune                     # Interactive cleanup
/popkit:git prune --dry-run           # Preview only
/popkit:git prune --force             # Include unmerged branches
```

### Process

1. **Fetch and Prune**
   ```bash
   git fetch --prune
   ```

2. **Find Gone Branches**
   ```bash
   git branch -vv | grep ': gone]' | awk '{print $1}'
   ```

3. **Preview** (always)
   ```
   Found 3 branches to remove:
   - feature/auth (merged 2 days ago)
   - fix/login-bug (merged 1 week ago)

   Proceed with deletion? [y/N]
   ```

4. **Delete** (if confirmed)

### Safety

- Uses `-d` (safe delete) not `-D`
- Won't delete unmerged branches by default
- Always previews before deletion
- Never deletes main/master/develop

---

## Subcommand: finish

Guide completion of development work with structured options.

```
/popkit:git finish                    # Finish current branch
/popkit:git finish feature/auth       # Finish specific branch
```

### Process

Invokes the **pop-finish-branch** skill:

#### Step 1: Verify Tests

```
Running tests...
[ok] 47 tests passing

Tests verified. Proceeding to options.
```

#### Step 2: Present Options

```
Implementation complete. What would you like to do?

1. Merge back to main locally
2. Push and create a Pull Request
3. Keep the branch as-is (handle later)
4. Discard this work

Which option? [1-4]
```

### Option 1: Merge Locally

```
Merged feature/auth into main.
Branch deleted.
Worktree cleaned up.
```

### Option 2: Create PR

Uses `/popkit:git pr create` flow.

### Option 3: Keep As-Is

```
Keeping branch feature/auth.
Worktree preserved at .worktrees/feature-auth
```

### Option 4: Discard

Requires typed confirmation. Deletes branch, commits, and worktree.

### Safety

- Always verifies tests first
- Never force-pushes without confirmation
- Requires typed confirmation for discard
- Preserves worktree for PR option

---

## Examples

```bash
# Smart commit with auto-generated message
/popkit:git
/popkit:git commit
/popkit:git commit "fixed the auth bug"

# Push to remote
/popkit:git push

# Full PR workflow
/popkit:git pr
/popkit:git pr create --draft
/popkit:git pr list --review-requested
/popkit:git pr view 67 --checks
/popkit:git pr merge 67 --squash --delete-branch

# Code review
/popkit:git review
/popkit:git review --pr 67
/popkit:git review --focus correctness

# Clean up merged branches
/popkit:git prune
/popkit:git prune --dry-run

# Complete development work
/popkit:git finish
```

---

## Git Safety Protocol

All git operations follow these rules:

- **NEVER** update git config
- **NEVER** run destructive/irreversible commands without explicit request
- **NEVER** skip hooks (--no-verify) unless explicitly requested
- **NEVER** force push to main/master
- **AVOID** git commit --amend unless explicitly requested
- **ALWAYS** check authorship before amending
- **ALWAYS** preview before bulk operations

---

## GitHub CLI Integration

All PR commands use `gh` CLI:

```bash
gh pr create --title "..." --body "..."
gh pr list --state open
gh pr view 67
gh pr merge 67 --squash
gh pr review 67 --approve
gh pr checkout 67
```

---

## Architecture Integration

| Component | Integration |
|-----------|-------------|
| Commit Generation | Conventional commits format |
| PR Templates | `output-styles/pr-description.md` |
| Code Review Skill | `skills/pop-code-review/SKILL.md` |
| Branch Cleanup | Git branch tracking |
| Finish Flow | `skills/pop-finish-branch/SKILL.md` |
| GitHub CLI | `gh pr create`, `gh pr list`, etc. |

## Related Commands

| Command | Purpose |
|---------|---------|
| `/popkit:worktree` | Git worktree management |
| `/popkit:plan execute` | Leads to finish flow |
| `/popkit:ci` | CI/CD status and releases |
