---
description: GitHub CI/CD management - workflow runs, releases, changelogs, and deployment status
---

# /popkit:ci - CI/CD Management

Manage GitHub Actions workflows and releases from one command.

## Usage

```
/popkit:ci <subcommand> [options]
```

## Subcommands

| Subcommand | Description |
|------------|-------------|
| `run` | Manage workflow runs (default) |
| `release` | Manage GitHub releases |

---

## Subcommand: run (default)

Monitor and manage GitHub Actions workflows.

### run list

List workflow runs:

```
/popkit:ci                            # Recent runs (default)
/popkit:ci run list                   # Same as above
/popkit:ci run list --workflow ci.yml # Specific workflow
/popkit:ci run list --branch main     # By branch
/popkit:ci run list --status failure  # Failed only
/popkit:ci run list --limit 20        # More results
```

Output:
```
Recent Workflow Runs:
[ok] CI #234 - main - 2m ago - 3m 45s
[x] CI #233 - feature/auth - 1h ago - 2m 12s
[ok] Deploy #89 - main - 2h ago - 5m 30s
[...] CI #235 - fix/bug - running - 1m 20s
```

### run view

View run details:

```
/popkit:ci run view 234
/popkit:ci run view 234 --log
/popkit:ci run view 234 --job build
```

Output:
```
Run #234: CI
Status: success
Workflow: ci.yml
Branch: main
Commit: abc123 - "feat: add auth"
Duration: 3m 45s
Triggered: push

Jobs:
[ok] build (1m 20s)
[ok] test (2m 15s)
[ok] lint (45s)
```

### run rerun

Rerun workflow:

```
/popkit:ci run rerun 233              # Rerun all jobs
/popkit:ci run rerun 233 --failed     # Rerun failed jobs only
/popkit:ci run rerun 233 --job test   # Rerun specific job
```

### run watch

Watch running workflow:

```
/popkit:ci run watch 235
```

Live output with real-time updates.

### run cancel

Cancel running workflow:

```
/popkit:ci run cancel 235
```

### run download

Download artifacts:

```
/popkit:ci run download 234           # All artifacts
/popkit:ci run download 234 --name dist
```

### run logs

View logs:

```
/popkit:ci run logs 234               # All logs
/popkit:ci run logs 234 --job build   # Specific job
/popkit:ci run logs 234 --failed      # Failed steps only
```

---

## Subcommand: release

Create and manage GitHub releases with auto-generated changelogs.

### release create

Create new release:

```
/popkit:ci release create <version>
/popkit:ci release create v1.2.0
/popkit:ci release create v1.2.0 --draft
/popkit:ci release create v1.2.0 --prerelease
```

**Process:**
1. Generate changelog from commits since last release
2. Create git tag
3. Create GitHub release with notes

**Release Notes Template:**
```markdown
## What's Changed

### Features
- feat: Add user authentication (#45)
- feat: Add dark mode support (#43)

### Bug Fixes
- fix: Resolve login validation issue (#44)

### Other Changes
- chore: Update dependencies
- docs: Improve API documentation

## Full Changelog
https://github.com/owner/repo/compare/v1.1.0...v1.2.0

---
Generated with Claude Code
```

### release list

List releases:

```
/popkit:ci release list               # All releases
/popkit:ci release list --limit 5     # Recent 5
/popkit:ci release list --draft       # Include drafts
```

### release view

View release details:

```
/popkit:ci release view v1.2.0
```

### release edit

Edit release:

```
/popkit:ci release edit v1.2.0 --notes "Updated notes"
/popkit:ci release edit v1.2.0 --draft false
/popkit:ci release edit v1.2.0 --prerelease true
```

### release delete

Delete release:

```
/popkit:ci release delete v1.2.0
/popkit:ci release delete v1.2.0 --tag  # Also delete tag
```

### release changelog

Generate changelog without creating release:

```
/popkit:ci release changelog          # Since last release
/popkit:ci release changelog v1.1.0   # Since specific version
/popkit:ci release changelog --format md
```

---

## Workflow Status Icons

- [ok] success
- [x] failure
- [...] in_progress
- [ ] queued
- [~] cancelled
- [!] skipped

---

## Version Detection

Automatically detects version from:
1. Command argument
2. package.json version
3. Cargo.toml version
4. Latest tag + increment

---

## Changelog Generation

Analyzes commits for:
- **feat**: New features
- **fix**: Bug fixes
- **docs**: Documentation
- **perf**: Performance
- **refactor**: Code changes
- **test**: Tests
- **chore**: Maintenance

Groups by type and includes PR/issue links.

---

## GitHub CLI Integration

All commands use `gh` CLI:

```bash
# Run commands
gh run list
gh run view 234
gh run rerun 233 --failed
gh run watch 235
gh run cancel 235
gh run download 234

# Release commands
gh release create v1.2.0 --notes "..."
gh release list
gh release view v1.2.0
gh release edit v1.2.0
gh release delete v1.2.0
```

---

## Examples

```bash
# Check why CI failed
/popkit:ci run list --status failure
/popkit:ci run view 233 --log

# Rerun failed tests
/popkit:ci run rerun 233 --failed

# Watch current run
/popkit:ci run watch

# Create release with auto-generated notes
/popkit:ci release create v1.2.0

# Create draft release for review
/popkit:ci release create v1.3.0 --draft

# View what would be in changelog
/popkit:ci release changelog
```

---

## Architecture Integration

| Component | Integration |
|-----------|-------------|
| Workflow Management | `gh run` commands |
| Release Management | `gh release` commands |
| Changelog Generation | Conventional commits parsing |
| Version Detection | package.json, Cargo.toml, git tags |

## Related Commands

| Command | Purpose |
|---------|---------|
| `/popkit:git` | Git workflow management |
| `/popkit:morning` | Includes CI status check |
