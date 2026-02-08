---
title: Git Workflows
description: Unified git operations with context gathering
---

# Git Workflows

PopKit provides unified git commands that automatically gather context and follow best practices.

## Commands

### Commit

**Command**: `/popkit-dev:git commit`

**What it does**:

1. Runs `git status` to see staged changes
2. Runs `git diff` to see modifications
3. Reviews recent commits for style
4. Generates meaningful commit message
5. Creates commit with co-author tag

**Usage**:

```bash
# Stage files first
git add src/auth.js src/routes.js

# Let PopKit create commit
/popkit-dev:git commit
```

**Output**:

```
feat: Implement OAuth2 authentication with Google provider

Add OAuth2 flow with Google Sign-In integration:
- Create /auth/google/callback route
- Add token validation middleware
- Store refresh tokens in Redis

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

### Push

**Command**: `/popkit-dev:git push`

**What it does**:

1. Checks branch protection rules
2. Runs pre-push hooks
3. Validates tests pass
4. Pushes to remote

**Usage**:

```bash
/popkit-dev:git push
```

### Pull Request

**Command**: `/popkit-dev:git pr`

**What it does**:

1. Analyzes all commits in branch
2. Examines full diff from base branch
3. Generates comprehensive PR summary
4. Creates PR with test plan
5. Links related issues

**Usage**:

```bash
# Create PR
/popkit-dev:git pr

# Create draft PR
/popkit-dev:git pr --draft
```

**Output**:

```markdown
## Summary

- Implement OAuth2 authentication with Google provider
- Add token refresh mechanism
- Create middleware for protected routes

## Test Plan

- [ ] Test Google Sign-In flow
- [ ] Verify token refresh works
- [ ] Check protected routes block unauthenticated users
- [ ] Test logout functionality

🤖 Generated with Claude Code
```

### Publish

**Command**: `/popkit-dev:git publish`

**What it does**:

1. Checks for sensitive data
2. Reviews commit history
3. Creates public repository
4. Pushes code
5. Sets up README and LICENSE

**Usage**:

```bash
/popkit-dev:git publish
```

## Branch Protection

PopKit enforces standard Git workflows with branch protection awareness.

### Protected Branches

The following branches are protected and require feature branch workflow:

- `main` - Primary integration branch
- `master` - Legacy primary branch
- `develop` - Development integration branch
- `production` - Production release branch

### Feature Branch Workflow

When on a protected branch with uncommitted changes, PopKit will:

1. **Detect**: Check `git branch --show-current`
2. **Warn**: Show critical priority recommendation
3. **Guide**: Provide feature branch creation commands

**Recommended Workflow**:

```bash
# Create feature branch
git checkout -b feat/your-feature-name
git push -u origin feat/your-feature-name

# Create pull request
/popkit-dev:git pr

# Clean up local protected branch
git checkout main
git reset --hard origin/main
```

## Best Practices

1. **Stage Intentionally**: Only stage files you want to commit
2. **Review Diffs**: Check what's being committed
3. **Descriptive Messages**: PopKit generates them, but review
4. **Use Feature Branches**: Never commit directly to main/master
5. **Create PRs**: Use PR workflow for all changes
6. **Link Issues**: Reference issue numbers in PRs

## Troubleshooting

### Commit Message Not Generated

**Symptom**: Generic commit message

**Solution**:

- Ensure files are staged (`git add`)
- Check that there are actual changes (`git diff --staged`)

### PR Creation Fails

**Symptom**: `gh pr create` fails

**Solution**:

- Install GitHub CLI: `brew install gh` or `choco install gh`
- Authenticate: `gh auth login`
- Ensure branch is pushed: `git push -u origin branch-name`

### Protected Branch Warning

**Symptom**: PopKit warns about committing to main

**Solution**:

- Create feature branch: `git checkout -b feat/my-feature`
- Push feature branch: `git push -u origin feat/my-feature`
- Create PR: `/popkit-dev:git pr`

## Next Steps

- Learn about [Routines](/features/routines/)
- Explore [Power Mode](/features/power-mode/)
- Review [Feature Development](/features/feature-dev/)
