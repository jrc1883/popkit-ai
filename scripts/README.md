# PopKit Migration Scripts

This directory contains automation scripts for migrating issues from the private `elshaddai` repository to the public `popkit-claude` repository.

## Scripts

### `migrate-issues.sh` (Bash)
For macOS, Linux, and WSL users.

```bash
# Make executable
chmod +x scripts/migrate-issues.sh

# Preview migration (dry run)
./scripts/migrate-issues.sh --dry-run --phase 1

# Migrate critical issues (Phase 1)
./scripts/migrate-issues.sh --phase 1

# Migrate specific issue
./scripts/migrate-issues.sh --issue 691

# Migrate all recommended issues
./scripts/migrate-issues.sh --all

# Show help
./scripts/migrate-issues.sh --help
```

### `migrate-issues.ps1` (PowerShell)
For Windows users.

```powershell
# Preview migration (dry run)
.\scripts\migrate-issues.ps1 -DryRun -Phase 1

# Migrate critical issues (Phase 1)
.\scripts\migrate-issues.ps1 -Phase 1

# Migrate specific issue
.\scripts\migrate-issues.ps1 -Issue 691

# Migrate all recommended issues
.\scripts\migrate-issues.ps1 -All

# Show help
.\scripts\migrate-issues.ps1 -Help
```

## Prerequisites

1. **GitHub CLI (`gh`)** - Install from https://cli.github.com/
2. **Authentication** - Run `gh auth login` if not already authenticated
3. **Repository Access** - Must have write access to both repositories

## Migration Phases

### Phase 1: Critical Issues (25 issues)
- P0-critical and P1-high release blockers
- Testing & validation issues
- Plugin modularization
- Security fixes
- Performance optimizations

**Recommended:** Run this phase first to address urgent issues.

### Phase 2: Features & Enhancements (25 issues)
- XML system architecture
- Power Mode improvements
- Routine templates
- Agent expertise system
- Cache management

**Recommended:** Run after Phase 1 is complete and validated.

### Phase 3: Documentation & Low Priority (50 issues)
- Documentation improvements
- UX enhancements
- XML integration epic
- Miscellaneous features

**Recommended:** Run after Phases 1 and 2 are complete.

## What the Script Does

1. **Fetches issue** from source repository (`elshaddai`)
2. **Sanitizes content** - Removes private information
3. **Transforms labels** - Removes private labels, adds `migration` label
4. **Adds footer** - Links back to original issue
5. **Creates issue** in target repository (`popkit-claude`)
6. **Closes if needed** - Preserves original state (open/closed)
7. **Cross-links** - Adds comment to original issue with new URL

## Safety Features

- **Dry run mode** - Preview migrations without creating issues
- **Rate limiting** - 2-second delay between issues to avoid API throttling
- **Error handling** - Continues on failure, reports statistics at end
- **Sanitization** - Removes repository-specific references
- **Warning system** - Alerts if billing/payment keywords detected

## Post-Migration Checklist

After running the migration script:

- [ ] Review migrated issues for accuracy
- [ ] Check for accidentally exposed private information
- [ ] Close duplicate issues
- [ ] Add issues to GitHub Projects board
- [ ] Create milestones (v1.0.0, v1.1.0)
- [ ] Triage labels (priority, phase, size)
- [ ] Update CLAUDE.md with migration notes
- [ ] Close original issues in elshaddai with "Migrated" comment

## Troubleshooting

### "gh: command not found"
Install GitHub CLI: https://cli.github.com/

### "Not authenticated with GitHub"
Run: `gh auth login`

### "Failed to fetch issue"
- Check issue number exists in source repo
- Verify you have read access to `jrc1883/elshaddai`

### "Failed to create issue"
- Verify you have write access to `jrc1883/popkit-claude`
- Check for API rate limiting (wait a few minutes)

### "Permission denied" (Bash script)
Run: `chmod +x scripts/migrate-issues.sh`

### "Execution policy" error (PowerShell)
Run PowerShell as Administrator and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## Examples

### Preview Phase 1 Migration
```bash
# Bash
./scripts/migrate-issues.sh --dry-run --phase 1

# PowerShell
.\scripts\migrate-issues.ps1 -DryRun -Phase 1
```

### Migrate One Issue for Testing
```bash
# Bash
./scripts/migrate-issues.sh --issue 691

# PowerShell
.\scripts\migrate-issues.ps1 -Issue 691
```

### Migrate All Critical Issues
```bash
# Bash
./scripts/migrate-issues.sh --phase 1

# PowerShell
.\scripts\migrate-issues.ps1 -Phase 1
```

### Migrate Everything
```bash
# Bash
./scripts/migrate-issues.sh --all

# PowerShell
.\scripts\migrate-issues.ps1 -All
```

## Issue List by Phase

See [ISSUE_MIGRATION_ANALYSIS.md](../docs/ISSUE_MIGRATION_ANALYSIS.md) for detailed breakdown of:
- Which issues are in each phase
- Why each issue should (or shouldn't) be migrated
- Risk assessment
- Timeline and effort estimates

## Support

For questions or issues with the migration script:
1. Review [ISSUE_MIGRATION_ANALYSIS.md](../docs/ISSUE_MIGRATION_ANALYSIS.md)
2. Check the Troubleshooting section above
3. Open an issue in `popkit-claude` repository

## License

MIT - Same as PopKit project
