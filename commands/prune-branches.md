---
description: Remove local branches whose remote tracking branches are gone (after PR merge)
---

# /popkit:prune-branches - Clean Merged Branches

Remove stale local branches after PRs are merged.

## Usage

```
/popkit:prune-branches [--dry-run]
```

## Process

### Step 1: Fetch and Prune

```bash
git fetch --prune
```

### Step 2: Find Gone Branches

```bash
git branch -vv | grep ': gone]' | awk '{print $1}'
```

### Step 3: Preview (always)

```
Found 3 branches to remove:
- feature/auth (merged 2 days ago)
- fix/login-bug (merged 1 week ago)
- chore/update-deps (merged 3 days ago)

Proceed with deletion? [y/N]
```

### Step 4: Delete (if confirmed)

```bash
for branch in $gone_branches; do
  git branch -d "$branch"
done
```

### Step 5: Report

```
Cleaned up 3 branches:
✓ feature/auth
✓ fix/login-bug
✓ chore/update-deps

Current branches: main, develop
```

## Safety

- Uses `-d` (safe delete) not `-D`
- Won't delete unmerged branches
- Always previews before deletion
- Never deletes main/master/develop

## Options

```
/popkit:prune-branches              # Interactive cleanup
/popkit:prune-branches --dry-run    # Preview only, no deletion
/popkit:prune-branches --force      # Delete unmerged branches too (asks confirmation)
```
