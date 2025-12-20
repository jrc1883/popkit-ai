# Plugin Publishing Examples

## Basic Publishing

```bash
/popkit:git publish                   # Publish current state to public repo
/popkit:git publish --dry-run         # Preview what would be published
/popkit:git publish --branch release  # Publish to specific branch
/popkit:git publish --tag v1.0.0      # Also create a release tag
```

## Architecture

PopKit uses a **split-repo model**:
- **Private monorepo** (`jrc1883/popkit`): Full development workspace with cloud services, billing, etc.
- **Public plugin repo** (`jrc1883/popkit-plugin`): Open-source plugin only, for Claude Code marketplace

This command uses `git subtree split` to extract `packages/plugin/` and push to the public repo.

## Publishing Process

1. **Verify Clean State**
   ```bash
   git status --porcelain
   # Must have no uncommitted changes in packages/plugin/
   ```

2. **Run IP Leak Scan**
   ```bash
   # Scan for intellectual property that shouldn't be public
   python hooks/utils/ip_protection.py packages/plugin/ --pre-publish
   ```

3. **Run Subtree Split**
   ```bash
   git subtree split --prefix=packages/plugin -b plugin-public-split
   ```

4. **Push to Public Repo**
   ```bash
   # IMPORTANT: Public repo uses 'main' branch (not 'master')
   git push plugin-public $(git subtree split --prefix=packages/plugin):main --force
   ```

5. **Optional: Create Release Tag**
   ```bash
   # If --tag provided
   git tag plugin-v1.0.0 plugin-public-split
   git push plugin-public plugin-v1.0.0
   ```

## IP Leak Scanner

The IP leak scanner (`hooks/utils/ip_protection.py`) prevents publication of sensitive data.

### Scanner Blocked Publish

```bash
# First publish attempt - scanner blocks
/popkit:git publish
# Scanner output:
# ❌ PUBLISH BLOCKED by IP leak scanner
# Found 9 critical/high severity issues.
# - packages/plugin/skills/pop-assessment-security/SKILL.md:45 - AKIAIOSFODNN7EXAMPLE
# ...

# Review findings - they're example patterns from security docs
# Override with skip flag
/popkit:git publish --skip-ip-scan
```

### When to Use --skip-ip-scan

**Use this flag when:**
- Scanner reports false positives (e.g., docs examples showing "bad" patterns)
- Security audit tools reference standard exploit patterns as examples
- Test fixtures contain intentional "bad" patterns for testing

**Don't use this flag if:**
- Scanner found real API keys, tokens, or secrets
- Cloud implementation code leaked into plugin
- Proprietary business logic exposed

## Release Workflow

```bash
# 1. Make changes in monorepo
/popkit:git commit "feat(plugin): add new feature"
/popkit:git push

# 2. When ready to release publicly
/popkit:git publish --tag v1.0.0

# 3. Update marketplace (users run)
/plugin update popkit@popkit-plugin
```

## Remote Configuration

The `plugin-public` remote must be configured:

```bash
git remote add plugin-public https://github.com/jrc1883/popkit-plugin.git
```

This is automatically set up when running `/popkit:git publish` for the first time.

## Troubleshooting

**"Remote not found"**: Run the remote setup command above.

**"Dirty working tree"**: Commit or stash changes in `packages/plugin/` first.

**"PUBLISH BLOCKED by IP leak scanner"**:
1. Review the findings displayed
2. If false positives: Run `/popkit:git publish --skip-ip-scan`
3. If real leaks: Fix them first, commit, then re-run

**"History diverged"**: Use `--force` if public repo has changes not in monorepo (rare).

**"Branch mismatch"**: Always push to `main` branch: `git push plugin-public <sha>:main`
