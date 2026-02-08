---
name: pop-worktree-manager
description: "Python-based git worktree manager with 8 operations: list, create, remove, switch, update-all, prune, init, analyze. Handles cross-platform paths, STATUS.json integration, protected branch safety. Use this skill when the user invokes /popkit-dev:worktree command or needs programmatic worktree management."
---

# Git Worktree Manager

## Overview

Comprehensive git worktree management through a single Python script with multi-operation routing. Enables parallel development on multiple branches without switching overhead.

**Announce at start:** "I'm using the pop-worktree-manager skill to manage git worktrees."

## Architecture

**Single Python script** (`scripts/worktree_operations.py`) with operation routing:

- Uses `argparse` for CLI argument parsing
- Routes to operation-specific functions via `--operation` flag
- Returns JSON output for programmatic integration
- Handles errors gracefully (never raises exceptions)

**Cross-platform compatibility:**

- Uses `pathlib.Path` objects throughout
- Handles Windows long paths automatically
- Safe command execution (no shell injection)

**Integration points:**

- STATUS.json schema for worktree metadata
- Morning routine displays worktree status
- Next action recommends sync when behind

## Operations

### 1. list

Display all worktrees with status:

```bash
python scripts/worktree_operations.py --operation list [--json]
```

**Output (table format):**

```
Worktrees:
  main (default)          /path/to/project
  feat/new-feature        /path/to/.worktrees/feat-new-feature    [3 commits behind main]
  dev-hotfix              /path/to/.worktrees/dev-hotfix          [uncommitted changes]
```

**Output (JSON format):**

```json
{
  "success": true,
  "worktrees": [
    {
      "branch": "main",
      "path": "/abs/path/to/project",
      "isDefault": true
    },
    {
      "branch": "feat/new-feature",
      "path": "/abs/path/to/.worktrees/feat-new-feature",
      "baseRef": "main",
      "behindBy": 3
    }
  ]
}
```

### 2. create

Create new worktree with branch:

```bash
python scripts/worktree_operations.py --operation create <branch> [--base <base-branch>] [--name <dirname>]
```

**Process:**

1. Validate branch name (exists or can be created)
2. Check protected branches (block on main/master/develop/production)
3. Resolve worktree path from config template
4. Run `git worktree add`
5. Enable Windows long paths if needed
6. Update STATUS.json

**Example:**

```bash
python scripts/worktree_operations.py --operation create feat/auth --base main --name auth-feature
```

### 3. remove

Remove worktree with safety checks:

```bash
python scripts/worktree_operations.py --operation remove <name> [--force]
```

**Safety checks:**

- Warn if uncommitted changes (block unless `--force`)
- Warn if unpushed commits (show count, block unless `--force`)

**Example:**

```bash
python scripts/worktree_operations.py --operation remove dev-feat-worktree
python scripts/worktree_operations.py --operation remove dev-feat-worktree --force
```

### 4. switch

Navigate to worktree directory (outputs path for shell integration):

```bash
python scripts/worktree_operations.py --operation switch <name>
```

**Output:**

```json
{
  "success": true,
  "path": "/abs/path/to/.worktrees/feat-new-feature"
}
```

**Shell integration:**

```bash
cd "$(python scripts/worktree_operations.py --operation switch feat-new-feature | jq -r .path)"
```

### 5. update-all

Pull latest in all worktrees:

```bash
python scripts/worktree_operations.py --operation update-all [--install]
```

**Process:**

1. List all worktrees
2. For each worktree:
   - `cd` to worktree
   - `git pull` (if tracking remote)
   - Run `npm install` if `--install` flag
3. Report success/failure count

**Example:**

```bash
python scripts/worktree_operations.py --operation update-all --install
```

### 6. prune

Remove stale worktree references:

```bash
python scripts/worktree_operations.py --operation prune [--dry-run]
```

**Process:**

1. Run `git worktree list --porcelain`
2. Identify worktrees with deleted directories
3. Run `git worktree prune` (or preview with `--dry-run`)

### 7. init

Auto-create worktrees for dev branches:

```bash
python scripts/worktree_operations.py --operation init [--pattern <pattern>]
```

**Process:**

1. List branches matching pattern (default: `dev-*`)
2. For each matching branch:
   - Create worktree if it doesn't exist
   - Pull latest
   - Run tests

**Example:**

```bash
python scripts/worktree_operations.py --operation init --pattern "dev-*"
```

### 8. analyze

Health analysis and cleanup recommendations:

```bash
python scripts/worktree_operations.py --operation analyze
```

**Checks:**

- Worktrees behind base branch (recommend sync)
- Uncommitted changes (recommend commit or stash)
- Stale worktrees (no activity in 30+ days)
- Protected branch violations

**Output:**

```json
{
  "success": true,
  "recommendations": [
    {
      "id": "sync_worktree",
      "name": "Sync worktree with main",
      "command": "/popkit-dev:git merge main",
      "score": 70,
      "why": "Worktree is 5 commits behind main"
    }
  ]
}
```

## Configuration Schema

**Location:** `.popkit/config.json`

```json
{
  "worktree": {
    "enabled": true,
    "worktreeDir": "../[project]-worktrees",
    "namingPattern": "dev-[branch]",
    "autoUpdate": false,
    "autoInstall": false,
    "protectedBranches": ["main", "master", "develop", "production"]
  }
}
```

## STATUS.json Integration

**Schema addition to `git` section:**

```json
{
  "git": {
    "branch": "feat/worktree-support",
    "worktree": {
      "isWorktree": true,
      "name": "dev-feat-worktree",
      "baseRef": "main",
      "linkedPath": "/abs/path/to/main-repo"
    }
  }
}
```

**Used by:**

- Morning routine: "🔧 Worktree: {name} (based on: {baseRef})"
- Next action: Recommend sync if commits behind

## Morning Routine Integration

**File:** `packages/popkit-dev/skills/pop-morning/scripts/morning_workflow.py`

**Addition (after loading STATUS.json):**

```python
worktree_info = status.get('git', {}).get('worktree', {})
if worktree_info.get('isWorktree'):
    print(f"■ Worktree: {worktree_info['name']}")
    print(f"  Based on: {worktree_info['baseRef']}")

    # Check if behind base branch
    base_ref = worktree_info['baseRef']
    output, ok = run_git_command(f"rev-list HEAD..{base_ref} --count")
    if ok and int(output) > 0:
        print(f"  ⚠ Behind {base_ref} by {output} commits")
```

## Next Action Integration

**File:** `packages/popkit-dev/skills/pop-next-action/scripts/recommend_action.py`

**Addition (in recommendation calculation):**

```python
worktree = state.get('git', {}).get('worktree', {})
if worktree.get('isWorktree'):
    base_ref = worktree['baseRef']
    output, ok = run_git_command(f'rev-list HEAD..{base_ref} --count')
    if ok and int(output) > 0:
        actions.append({
            'id': 'sync_worktree',
            'name': f'Sync worktree with {base_ref}',
            'command': f'/popkit-dev:git merge {base_ref}',
            'score': 70,
            'why': f'Worktree is {output} commits behind {base_ref}'
        })
```

## Error Handling Strategy

**Never raise exceptions** - all operations return `(success: bool, data: Dict)` tuples:

```python
# Git command failures
output, ok = run_git_command('worktree list')
if not ok:
    return {'success': False, 'error': 'Failed to list worktrees', 'details': output}

# Safety checks
if uncommitted_changes and not force:
    return {'success': False, 'error': 'Worktree has uncommitted changes. Use --force to remove anyway.'}

# Protected branch detection
if branch in config['protectedBranches']:
    return {'success': False, 'error': f'Cannot create worktree on protected branch {branch}'}
```

## Testing Strategy

**Unit Tests (~30 tests):**

- Core operations (list, create, remove) - 10 tests
- Advanced operations (update, prune, init, analyze) - 8 tests
- Safety checks (uncommitted changes, protected branches) - 5 tests
- Cross-platform compatibility (Windows long paths, Path objects) - 4 tests
- Configuration loading and defaults - 3 tests

**Integration Tests (~5 tests):**

- Full workflow: create → switch → update → remove
- Morning routine reports worktree status
- Next action recommends sync when behind
- Multiple worktrees work simultaneously
- Cross-platform path resolution

## Command Invocation Pattern

The `/popkit-dev:worktree` command delegates to this skill:

```
User: /popkit-dev:worktree list

Claude: I'm using the pop-worktree-manager skill to list git worktrees.

[Runs: python scripts/worktree_operations.py --operation list]

Worktrees:
  main (default)          /Users/josep/popkit-claude
  feat/worktree-mgmt      /Users/josep/popkit-worktrees/feat-worktree-mgmt
```

## Quick Reference

| Operation  | Purpose                        | Safety Checks                          |
| ---------- | ------------------------------ | -------------------------------------- |
| list       | Display all worktrees          | None                                   |
| create     | Create new worktree            | Protected branches, path exists        |
| remove     | Delete worktree                | Uncommitted/unpushed changes (--force) |
| switch     | Navigate to worktree           | Worktree exists                        |
| update-all | Pull latest in all             | None (reports failures)                |
| prune      | Clean stale references         | None (--dry-run available)             |
| init       | Auto-create from branches      | Pattern validation                     |
| analyze    | Health check + recommendations | None                                   |

## Common Mistakes

**Creating worktrees on protected branches**

- **Problem:** Violates Git Workflow Principles (see CLAUDE.md)
- **Fix:** Always create feature branch first, then worktree

**Not checking for uncommitted changes before remove**

- **Problem:** Lose work
- **Fix:** Script blocks unless `--force` used

**Hardcoding paths**

- **Problem:** Breaks cross-platform, doesn't handle long paths
- **Fix:** Use `pathlib.Path` throughout, resolve from config

**Skipping STATUS.json updates**

- **Problem:** Morning routine and next action don't work
- **Fix:** Update STATUS.json after create/remove operations

## Red Flags

**Never:**

- Create worktrees on main/master/develop/production
- Remove worktrees with uncommitted changes (without --force)
- Use string concatenation for paths (use Path objects)
- Skip error handling (always return success/failure tuple)

**Always:**

- Validate protected branches before create
- Warn about uncommitted/unpushed changes before remove
- Update STATUS.json after worktree changes
- Use cross-platform path handling
