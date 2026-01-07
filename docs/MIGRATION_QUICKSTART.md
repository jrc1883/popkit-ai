# Issue Migration Quick Start Guide

**Goal:** Move PopKit-related issues from private `elshaddai` repo to public `popkit-claude` repo.

---

## TL;DR

```bash
# 1. Review the analysis
cat docs/ISSUE_MIGRATION_ANALYSIS.md

# 2. Test with dry run (Bash)
./scripts/migrate-issues.sh --dry-run --issue 691

# 2. Test with dry run (PowerShell)
.\scripts\migrate-issues.ps1 -DryRun -Issue 691

# 3. Migrate critical issues (Bash)
./scripts/migrate-issues.sh --phase 1

# 3. Migrate critical issues (PowerShell)
.\scripts\migrate-issues.ps1 -Phase 1
```

---

## What's Being Migrated?

**PUBLIC (Migrate):** ~120 issues
- PopKit plugin features
- Testing & validation
- Documentation
- Bug fixes
- Performance improvements

**PRIVATE (Keep in elshaddai):** ~15 issues
- Cloud API
- Stripe billing
- Premium tiers

**OTHER APPS (Ignore):** ~65 issues
- Genesis, Reseller Central, etc.

---

## Migration Phases

| Phase | Issues | Priority | Description |
|-------|--------|----------|-------------|
| **Phase 1** | 25 | P0-critical, P1-high | Testing, modularization, security |
| **Phase 2** | 25 | P1-high, P2-medium | Features, XML system, Power Mode |
| **Phase 3** | 50 | P2-medium, P3-low | Documentation, UX, misc features |

---

## Quick Commands

### Preview First (Always!)

```bash
# Bash
./scripts/migrate-issues.sh --dry-run --phase 1

# PowerShell
.\scripts\migrate-issues.ps1 -DryRun -Phase 1
```

### Test One Issue

```bash
# Bash
./scripts/migrate-issues.sh --issue 691

# PowerShell
.\scripts\migrate-issues.ps1 -Issue 691
```

### Run Phase 1 (Critical)

```bash
# Bash
./scripts/migrate-issues.sh --phase 1

# PowerShell
.\scripts\migrate-issues.ps1 -Phase 1
```

### Run All Phases

```bash
# Bash
./scripts/migrate-issues.sh --all

# PowerShell
.\scripts\migrate-issues.ps1 -All
```

---

## What Happens?

For each issue:

1. ✅ Fetch from `elshaddai`
2. ✅ Remove private labels (`app:elshaddai`, `scope:monorepo`)
3. ✅ Add `migration` label
4. ✅ Add footer linking to original issue
5. ✅ Create in `popkit-claude`
6. ✅ Preserve state (open/closed)
7. ✅ Comment on original with new URL

---

## Safety Features

- **Dry run mode** - Preview before creating
- **Rate limiting** - 2-second delays
- **Sanitization** - Removes private references
- **Warning system** - Alerts on billing keywords
- **Error handling** - Continues on failure

---

## Prerequisites

```bash
# Install GitHub CLI
# macOS: brew install gh
# Windows: winget install GitHub.cli
# Linux: See https://cli.github.com/

# Authenticate
gh auth login

# Test access
gh issue list --repo jrc1883/elshaddai --limit 1
gh issue list --repo jrc1883/popkit-claude --limit 1
```

---

## Phase 1 Issues (25 Critical)

Testing & Validation:
- #691, #690, #689, #688, #676, #675, #674, #673, #679, #677

Plugin Modularization:
- #580, #589, #588, #587, #586, #585, #584, #583

Critical Fixes:
- #519 (Security: command injection)
- #522 (Performance: context bloat)
- #520 (Documentation: agent directory)
- #518 (Epic: v1.0.0 readiness)
- #650 (Bug: command duplicates)
- #613 (Bug: broken hook)

---

## Post-Migration Checklist

After running the script:

- [ ] Review migrated issues in `popkit-claude`
- [ ] Check for private information leaks
- [ ] Add to GitHub Projects board
- [ ] Create milestones (v1.0.0, v1.1.0)
- [ ] Close duplicates
- [ ] Update CLAUDE.md
- [ ] Comment on originals: "Migrated to popkit-claude"

---

## Troubleshooting

**Problem:** `gh: command not found`
**Solution:** Install GitHub CLI from https://cli.github.com/

**Problem:** `Not authenticated`
**Solution:** Run `gh auth login`

**Problem:** `Permission denied` (Bash)
**Solution:** `chmod +x scripts/migrate-issues.sh`

**Problem:** `Execution policy` (PowerShell)
**Solution:** `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`

**Problem:** `Failed to fetch issue`
**Solution:** Check you have access to private `elshaddai` repo

**Problem:** `Failed to create issue`
**Solution:** Check API rate limits (wait a few minutes)

---

## Full Documentation

- **Analysis:** [ISSUE_MIGRATION_ANALYSIS.md](ISSUE_MIGRATION_ANALYSIS.md)
- **Scripts:** [scripts/README.md](../scripts/README.md)

---

## Timeline

- **Week 1:** Phase 1 (critical issues) - 8 hours
- **Week 2:** Phase 2 (features) - 12 hours
- **Week 3:** Phase 3 (documentation) - 10 hours
- **Week 4:** Review & cleanup - 5 hours

**Total:** ~35 hours

---

## Support

Questions? Check:
1. [ISSUE_MIGRATION_ANALYSIS.md](ISSUE_MIGRATION_ANALYSIS.md) - Detailed analysis
2. [scripts/README.md](../scripts/README.md) - Script documentation
3. Open an issue in `popkit-claude` if stuck

---

**Ready to migrate?** Start with `--dry-run` to preview!
