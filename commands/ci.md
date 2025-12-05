---
description: "DEPRECATED → Use /popkit:git ci"
deprecated: true
deprecated_in_favor_of: /popkit:git
---

> **DEPRECATED:** This command is deprecated. Use `/popkit:git` instead:
> - `/popkit:ci run list` → `/popkit:git ci list`
> - `/popkit:ci run view` → `/popkit:git ci view`
> - `/popkit:ci run rerun` → `/popkit:git ci rerun`
> - `/popkit:ci run watch` → `/popkit:git ci watch`
> - `/popkit:ci run cancel` → `/popkit:git ci cancel`
> - `/popkit:ci run download` → `/popkit:git ci download`
> - `/popkit:ci run logs` → `/popkit:git ci logs`
> - `/popkit:ci release create` → `/popkit:git release create`
> - `/popkit:ci release list` → `/popkit:git release list`
> - `/popkit:ci release view` → `/popkit:git release view`
> - `/popkit:ci release edit` → `/popkit:git release edit`
> - `/popkit:ci release delete` → `/popkit:git release delete`
> - `/popkit:ci release changelog` → `/popkit:git release changelog`

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

## Executable Commands

### run list
```bash
gh run list [--workflow <file>] [--branch <name>] [--status <state>] [-L <limit>]
```

### run view
```bash
gh run view <run-id>
gh run view <run-id> --log
gh run view <run-id> --job <job-name>
```

### run rerun
```bash
gh run rerun <run-id>
gh run rerun <run-id> --failed
gh run rerun <run-id> --job <job-name>
```

### run watch
```bash
gh run watch <run-id>
```

### run cancel
```bash
gh run cancel <run-id>
```

### run download
```bash
gh run download <run-id>
gh run download <run-id> --name <artifact-name>
gh run download <run-id> --dir <directory>
```

### run logs
```bash
gh run view <run-id> --log
gh run view <run-id> --log --job <job-name>
gh run view <run-id> --log-failed
```

### release create
```bash
# Get last tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "")

# Generate changelog from commits
if [ -n "$LAST_TAG" ]; then
    git log ${LAST_TAG}..HEAD --pretty=format:"- %s (%h)" --no-merges
fi

# Create tag and release
git tag <version>
git push origin <version>
gh release create <version> --title "<version>" --notes "<changelog>" [--draft] [--prerelease]
```

### release list
```bash
gh release list [-L <limit>] [--exclude-drafts | --include-drafts]
```

### release view
```bash
gh release view <tag>
```

### release edit
```bash
gh release edit <tag> [--notes "<notes>"] [--draft=<bool>] [--prerelease=<bool>]
```

### release delete
```bash
gh release delete <tag> [--yes]
# Optionally delete tag:
git tag -d <tag>
git push origin :refs/tags/<tag>
```

### release changelog
```bash
# Get last tag
LAST_TAG=$(git describe --tags --abbrev=0 2>/dev/null)

# Generate changelog grouped by type
git log ${LAST_TAG}..HEAD --pretty=format:"%s" | grep -E "^(feat|fix|docs|perf|refactor|test|chore):"
```

---

## Architecture Integration

| Component | Integration |
|-----------|-------------|
| Workflow Runs | `gh run list/view/rerun/watch/cancel` commands |
| Workflow Artifacts | `gh run download` for build outputs |
| Workflow Logs | `gh run view --log` for debugging |
| Release Creation | `gh release create` with auto-notes |
| Release Management | `gh release list/view/edit/delete` |
| Changelog Generation | Parses conventional commits (feat, fix, docs, etc.) |
| Version Detection | package.json, Cargo.toml, pyproject.toml, git tags |
| Tag Management | Creates and pushes git tags with releases |
| Morning Health Check | `/popkit:morning` includes CI status |
| Quality Gates | Release blocked if CI failing |
| Commit Convention | Groups changelog by commit type prefix |
| PR Integration | Includes PR numbers in changelog entries |

## Related Commands

| Command | Purpose |
|---------|---------|
| `/popkit:git` | Git workflow management |
| `/popkit:morning` | Includes CI status check |
