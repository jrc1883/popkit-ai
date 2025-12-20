# Pull Request Examples

## Creating PRs

```bash
/popkit:git pr                        # Create PR from current branch
/popkit:git pr create                 # Same as above
/popkit:git pr create --title "Add auth"
/popkit:git pr create --draft         # As draft
/popkit:git pr create --base develop  # Target branch
```

## PR Creation Process

1. Verify clean state
2. Create/switch branch (if needed)
3. Stage changes
4. Generate commit
5. Push branch
6. Create PR with template

## PR Template

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

## Listing PRs

```bash
/popkit:git pr list                   # Open PRs
/popkit:git pr list --state all       # All PRs
/popkit:git pr list --author @me      # My PRs
/popkit:git pr list --review-requested
/popkit:git pr list --draft           # Draft PRs only
```

Output example:
```
Open PRs (5):
#67 [ready] Add authentication - @user - 2 reviews
#66 [draft] Refactor API - @user - 0 reviews
#65 [changes] Fix login bug - @user - 1 review
```

## Viewing PRs

```bash
/popkit:git pr view 67
/popkit:git pr view 67 --comments
/popkit:git pr view 67 --files
/popkit:git pr view 67 --checks
```

## Merging PRs

```bash
/popkit:git pr merge 67               # Default merge
/popkit:git pr merge 67 --squash      # Squash and merge
/popkit:git pr merge 67 --rebase      # Rebase and merge
/popkit:git pr merge 67 --delete-branch
```

Pre-merge checks:
1. All required reviews approved
2. All status checks passing
3. No merge conflicts
4. Branch is up to date

## Other PR Commands

```bash
/popkit:git pr checkout 67            # Check out PR locally
/popkit:git pr diff 67                # View PR diff
/popkit:git pr ready 67               # Mark draft as ready
/popkit:git pr update 67              # Update PR branch with base
```
