---
description: "list | create | remove | switch | update-all | prune | init | analyze"
argument-hint: "<operation> [options]"
---

# /popkit-dev:worktree - Git Worktree Management

Manage git worktrees for parallel development without branch switching overhead.

## Usage

```
/popkit-dev:worktree <operation> [options]
```

## Operations

### list

Display all worktrees with branch, path, status:

```
/popkit-dev:worktree list
```

### create

Create worktree (dev or feature branch):

```
/popkit-dev:worktree create <branch>
/popkit-dev:worktree create feat/new-feature --base main --name my-feature
```

Options:
- `--base <branch>` - Base branch (default: current branch)
- `--name <name>` - Worktree directory name (default: derived from branch)

### remove

Remove worktree with uncommitted change warnings:

```
/popkit-dev:worktree remove <name>
/popkit-dev:worktree remove dev-feat-worktree --force
```

Options:
- `--force` - Remove even with uncommitted changes

### switch

Navigate to worktree directory:

```
/popkit-dev:worktree switch <name>
```

### update-all

Pull latest in all worktrees:

```
/popkit-dev:worktree update-all
/popkit-dev:worktree update-all --install
```

Options:
- `--install` - Run npm install after updates

### prune

Remove stale references:

```
/popkit-dev:worktree prune
/popkit-dev:worktree prune --dry-run
```

Options:
- `--dry-run` - Preview changes without executing

### init

Auto-branch with updates for dev branches:

```
/popkit-dev:worktree init
/popkit-dev:worktree init --pattern "dev-*"
```

Options:
- `--pattern <pattern>` - Filter branches by pattern

### analyze

Health analysis and cleanup recommendations:

```
/popkit-dev:worktree analyze
```

## Skill Integration

This command delegates to the **pop-worktree-manager** skill which handles:

- Cross-platform path handling (Windows long paths, Path objects)
- STATUS.json integration for morning routine reporting
- Protected branch safety checks (main/master/develop/production)
- Multi-operation routing via `--operation` flag
- Shared utilities from `popkit_shared` package

## Integration Points

**Morning Routine**: Displays worktree status (name, base branch, commits behind)

**Next Action**: Recommends sync when worktree is behind base branch

**STATUS.json Schema**:
```json
{
  "git": {
    "worktree": {
      "isWorktree": true,
      "name": "dev-feat-worktree",
      "baseRef": "main",
      "linkedPath": "/abs/path/to/main-repo"
    }
  }
}
```

## Examples

```bash
# List all worktrees with status
/popkit-dev:worktree list

# Create feature worktree from main
/popkit-dev:worktree create feat/new-feature --base main

# Update all worktrees and install dependencies
/popkit-dev:worktree update-all --install

# Analyze worktree health
/popkit-dev:worktree analyze

# Remove worktree with safety checks
/popkit-dev:worktree remove dev-feat-worktree

# Clean up stale references
/popkit-dev:worktree prune --dry-run
```

---

Use this command to work on multiple branches simultaneously without the overhead of constant branch switching.
