# GitHub Cache Integration Guide

**Issue #96: GitHub Metadata Caching**

This guide explains how to integrate the GitHub cache into commands and skills to prevent errors from invalid labels, milestones, and other metadata.

## Overview

The GitHub cache provides two-tier caching (Local JSON / Redis) for repository metadata:

- **Labels** - Cached for 60 minutes
- **Milestones** - Cached for 60 minutes
- **Team Members** - Cached for 24 hours

## The "Check First" Pattern

Always validate metadata BEFORE making GitHub API calls to prevent errors.

```python
from popkit_shared.utils.github_validator import validate_labels
from popkit_shared.utils.github_cache import GitHubCache

# Before gh issue create or gh pr create:
cache = GitHubCache()
valid, invalid, suggestions = validate_labels(requested_labels, cache)

if invalid:
    # Show suggestions to user
    # Either auto-correct or ask user to confirm
    pass
else:
    # All labels valid, proceed with gh command
    pass
```

## Integration Points

### 1. Issue Creation (`issue.md` command)

**When:** User creates issue with `--label` flag or template selection

**Before:**

```bash
gh issue create --title "..." --body "..." --label bug,priority:high
```

**After (with validation):**

```python
# Parse labels from user input
requested_labels = ["bug", "priority:high"]

# Validate
cache = GitHubCache()
valid, invalid, suggestions = validate_labels(requested_labels, cache)

if invalid:
    # Show error with suggestions
    print(f"Invalid labels: {', '.join(invalid)}")
    for s in suggestions:
        print(f"  {s['invalid']} -> Did you mean: {', '.join(s['suggestions'][:3])}?")

    # Ask user to correct or auto-fix
    # Option 1: Auto-fix with best suggestion
    # Option 2: Ask user to select from suggestions
    # Option 3: Remove invalid labels
else:
    # Proceed with gh issue create
    gh_command = f"gh issue create --title '...' --label {','.join(valid)}"
```

### 2. Pull Request Creation (`git.md` command)

**When:** User creates PR with `--label` flag

**Before:**

```bash
gh pr create --title "..." --body "..." --label enhancement,needs-review
```

**After (with validation):**

```python
# Same pattern as issue creation
requested_labels = ["enhancement", "needs-review"]
cache = GitHubCache()
valid, invalid, suggestions = validate_labels(requested_labels, cache)

if invalid:
    # Show suggestions and handle correction
    pass
else:
    # Proceed with gh pr create
    pass
```

### 3. Bug Reporting (`bug.md` command, `pop-bug-reporter` skill)

**When:** User reports bug with `--issue` flag

**Before:**

```bash
gh issue create --title "Bug: ..." --body "..." --label bug,needs-triage
```

**After (with validation):**

```python
# Bug reports always use "bug" label
default_labels = ["bug", "needs-triage"]
cache = GitHubCache()
valid, invalid, suggestions = validate_labels(default_labels, cache)

# Auto-fix: Use "bug" if exists, otherwise first fuzzy match
# Don't block bug reports on invalid labels - just warn
```

### 4. Branch Finishing (`pop-finish-branch` skill)

**When:** User chooses "Create PR" option

**Before:**

```bash
gh pr create --title "..." --body "..." --label feature,ready-for-review
```

**After (with validation):**

```python
# Determine labels based on branch prefix
branch_name = get_current_branch()
inferred_labels = infer_labels_from_branch(branch_name)  # e.g., feat/ -> enhancement

cache = GitHubCache()
valid, invalid, suggestions = validate_labels(inferred_labels, cache)

# Auto-fix or proceed with valid labels only
```

## Error Handling Strategies

### Strategy 1: Auto-Fix with Best Match (Recommended)

```python
valid, invalid, suggestions = validate_labels(requested_labels, cache)

fixed_labels = valid.copy()
for s in suggestions:
    if s['suggestions']:
        # Use best match (first suggestion)
        best_match = s['suggestions'][0]
        fixed_labels.append(best_match)
        print(f"Auto-corrected: {s['invalid']} -> {best_match}")

# Proceed with fixed_labels
```

### Strategy 2: Ask User to Confirm

```python
valid, invalid, suggestions = validate_labels(requested_labels, cache)

if invalid:
    print(f"Invalid labels: {', '.join(invalid)}")
    for s in suggestions:
        print(f"  {s['invalid']} -> Suggestions: {', '.join(s['suggestions'][:3])}")

    # Use AskUserQuestion to let user choose
    # Option 1: Use suggestions
    # Option 2: Remove invalid labels
    # Option 3: Cancel operation
```

### Strategy 3: Remove Invalid Labels

```python
valid, invalid, suggestions = validate_labels(requested_labels, cache)

if invalid:
    print(f"Removing invalid labels: {', '.join(invalid)}")

# Proceed with only valid labels
```

## Milestone Validation

```python
from popkit_shared.utils.github_validator import validate_milestone

# Before gh issue edit --milestone "v1.0"
milestone_title = "v1.0"
cache = GitHubCache()

exists, milestone_number, suggestions = validate_milestone(milestone_title, cache)

if not exists:
    print(f"Milestone '{milestone_title}' not found")
    if suggestions:
        print(f"Did you mean: {', '.join(suggestions[:3])}?")
    # Handle correction
else:
    # Use milestone_number in gh command
    gh_command = f"gh issue edit {issue_number} --milestone '{milestone_title}'"
```

## Cache Refresh

```python
# Force refresh (e.g., after creating new labels)
cache = GitHubCache()
labels = cache.get_labels(force_refresh=True)
```

## Testing Integration

```bash
# Run integration tests
python test_github_cache_integration.py

# Test with real repository
cd /path/to/your/repo
python -c "
from popkit_shared.utils.github_cache import GitHubCache
cache = GitHubCache()
print('Labels:', len(cache.get_labels()))
print('Milestones:', len(cache.get_milestones()))
"
```

## Implementation Checklist

For each command/skill that uses GitHub operations:

- [ ] Import `validate_labels` and `GitHubCache`
- [ ] Add validation before `gh issue create`
- [ ] Add validation before `gh pr create`
- [ ] Add validation before `gh issue edit --label`
- [ ] Add validation before `gh pr edit --label`
- [ ] Handle invalid labels (auto-fix, ask user, or remove)
- [ ] Show suggestions for typos
- [ ] Test with valid labels (should work)
- [ ] Test with invalid labels (should show suggestions)
- [ ] Test with typos (should auto-correct)

## Files to Update

1. **Commands:**
   - `packages/popkit-dev/commands/issue.md` - Issue creation flow
   - `packages/popkit-dev/commands/git.md` - PR creation flow
   - `packages/popkit-core/commands/bug.md` - Bug reporting flow

2. **Skills:**
   - `packages/popkit-core/skills/pop-bug-reporter/SKILL.md`
   - `packages/popkit-dev/skills/pop-finish-branch/SKILL.md`
   - `packages/popkit-research/skills/pop-research-merge/SKILL.md`
   - `packages/popkit-dev/skills/pop-brainstorming/SKILL.md`

3. **Agents:**
   - `packages/popkit-dev/agents/tier-2-on-demand/prd-parser/AGENT.md`

## Benefits

✅ **Prevents errors** - No more "label does not exist" failures
✅ **Improves UX** - Fuzzy matching catches typos
✅ **Reduces API calls** - Caching saves rate limits
✅ **Faster execution** - Local cache is instant
✅ **Better suggestions** - Levenshtein distance finds close matches

## Performance Impact

- **First call:** ~500ms (fetch from GitHub)
- **Cached calls:** <5ms (local JSON read)
- **TTL:** 60 minutes (labels/milestones), 24 hours (team)
- **Storage:** <100KB per repository

## Related Issues

- Issue #96: GitHub Metadata Caching (this implementation)
- Issue #142: Branch Protection (uses cache for branch validation)

## See Also

- [`github_cache.py`](github_cache.py) - Cache implementation
- [`github_validator.py`](github_validator.py) - Validation functions
- [`test_github_cache_integration.py`](../../test_github_cache_integration.py) - Integration tests
