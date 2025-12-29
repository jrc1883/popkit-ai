# Plugin Sync, Detect, and Version Examples

Examples of using `/popkit:plugin sync`, `/popkit:plugin detect`, and `/popkit:plugin version` for plugin maintenance.

## Plugin Sync (Validation)

### Basic Validation

Check plugin integrity without making changes:

```
/popkit:plugin sync
```

Output:
```
PopKit Plugin Validation Report
============================================================

Total Issues: 5
Auto-fixable: 2

Plugin Health Score: 92/100 (Grade: A)

Deductions:
  - 5 warnings (-5)
  - Missing optional metadata (-3)

⚠ MEDIUM: 2 issues
  - orphaned_agent: analytics-dashboard [AUTO-FIXABLE]
    Fix: Add 'analytics-dashboard' to agents/config.json
  - skill_format_error: Missing description field [AUTO-FIXABLE]

⚠ LOW: 3 issues
  - naming_inconsistency: Directory 'old-skill-name' doesn't match frontmatter
  - missing_optional_field: No 'author' in plugin.json
  - missing_optional_field: No 'repository' in plugin.json

2 issues can be automatically fixed.
Run: /popkit:plugin sync apply
```

### Apply Auto-Fixes

Automatically fix safe issues:

```
/popkit:plugin sync apply
```

Output:
```
PopKit Plugin Validation Report
============================================================

[... validation report ...]

Applying auto-fixes...
  ✓ Registered agent: analytics-dashboard
  ✓ Added frontmatter description: skills/new-feature/SKILL.md

Applied 2 auto-fixes

Re-run validation to verify fixes.
```

### Validate Specific Component

```
/popkit:plugin sync --component=skills
```

Output:
```
Validating component: skills

✓ Skills Validation
  Total skills: 68
  Valid: 67
  Invalid: 1

Issues:
  ⚠ skills/example/SKILL.md: Missing description field [AUTO-FIXABLE]

1 issue can be automatically fixed.
Run: /popkit:plugin sync apply --component=skills
```

### JSON Output for CI

```
/popkit:plugin sync --json
```

Output:
```json
{
  "summary": {
    "total_issues": 5,
    "auto_fixable": 2,
    "health_score": 92,
    "grade": "A"
  },
  "issues": {
    "critical": [],
    "high": [],
    "medium": [
      {
        "type": "orphaned_agent",
        "agent": "analytics-dashboard",
        "auto_fixable": true,
        "fix_action": "Add 'analytics-dashboard' to agents/config.json"
      }
    ],
    "low": [
      {
        "type": "naming_inconsistency",
        "directory": "old-skill-name",
        "issue": "Directory name doesn't match skill name"
      }
    ]
  }
}
```

## Plugin Conflict Detection

### Basic Detection

Check for conflicts with other installed plugins:

```
/popkit:plugin detect
```

Output:
```
PopKit Plugin Conflict Detection
============================================================

Scanning installed plugins...
Found 3 plugins: popkit, example-plugin, dev-tools

Checking for conflicts...

✗ HIGH: Command Collision
  - /popkit:test conflicts with dev-tools:/test
  - /popkit:deploy conflicts with dev-tools:/deploy

⚠ MEDIUM: Skill Collision
  - pop-code-reviewer conflicts with example-plugin:code-reviewer
  - Both provide similar functionality

⚠ MEDIUM: Hook Collision
  - Both popkit and dev-tools register PreToolUse hooks
  - May cause unexpected behavior

Summary:
------------------------------------------------------------
Command Collisions: 2 (HIGH)
Skill Collisions: 1 (MEDIUM)
Hook Collisions: 1 (MEDIUM)
Routing Overlap: 0 (LOW)

Recommendations:
  - Rename conflicting commands or disable one plugin
  - Review hook execution order in Claude Code settings
```

### Quick Check

One-line summary:

```
/popkit:plugin detect --quick
```

Output:
```
Conflicts: 2 command collisions, 1 skill collision, 1 hook collision
```

### JSON Output

```
/popkit:plugin detect --json
```

Output:
```json
{
  "plugins_scanned": 3,
  "conflicts": {
    "command_collisions": [
      {
        "severity": "HIGH",
        "command": "/popkit:test",
        "conflicts_with": "dev-tools:/test"
      },
      {
        "severity": "HIGH",
        "command": "/popkit:deploy",
        "conflicts_with": "dev-tools:/deploy"
      }
    ],
    "skill_collisions": [
      {
        "severity": "MEDIUM",
        "skill": "pop-code-reviewer",
        "conflicts_with": "example-plugin:code-reviewer"
      }
    ],
    "hook_collisions": [
      {
        "severity": "MEDIUM",
        "hook_type": "PreToolUse",
        "plugins": ["popkit", "dev-tools"]
      }
    ],
    "routing_overlaps": []
  },
  "summary": {
    "total_conflicts": 4,
    "high_severity": 2,
    "medium_severity": 2,
    "low_severity": 0
  }
}
```

### Custom Plugin Directory

```
/popkit:plugin detect --plugins ~/.claude/custom-plugins
```

## Version Management

### Patch Version Bump

For bug fixes:

```
/popkit:plugin version patch
```

Output:
```
Current version: 0.2.4
New version: 0.2.5

Updating version files...
  ✓ Updated .claude-plugin/plugin.json
  ✓ Updated .claude-plugin/marketplace.json

Updating CHANGELOG.md...
  ✓ Added section for v0.2.5

Creating commit...
  ✓ Committed: "chore: bump version to 0.2.5 for bug fixes"

Pushing to remote...
  ✓ Pushed to origin/main

Publishing to public repo...
  ✓ Published to jrc1883/popkit-claude

Version 0.2.5 released successfully!
```

### Minor Version Bump

For new features:

```
/popkit:plugin version minor
```

Output:
```
Current version: 0.2.5
New version: 0.3.0

[... same process as patch ...]

Version 0.3.0 released successfully!
```

### Major Version Bump

For breaking changes:

```
/popkit:plugin version major
```

Output:
```
Current version: 0.3.0
New version: 1.0.0

⚠ This is a MAJOR version bump (breaking changes)

Updating version files...
  ✓ Updated .claude-plugin/plugin.json
  ✓ Updated .claude-plugin/marketplace.json

Updating CHANGELOG.md...
  ✓ Added section for v1.0.0
  ⚠ Add breaking changes documentation

Creating commit...
  ✓ Committed: "chore: bump version to 1.0.0 with breaking changes"

Version 1.0.0 released successfully!

Next steps:
  - Document breaking changes in CHANGELOG.md
  - Create migration guide for users
  - Announce on release channels
```

### Dry Run

Preview changes without applying:

```
/popkit:plugin version patch --dry-run
```

Output:
```
[DRY RUN] Would update:
  - .claude-plugin/plugin.json: 0.2.4 → 0.2.5
  - .claude-plugin/marketplace.json: 0.2.4 → 0.2.5
  - CHANGELOG.md: Add v0.2.5 section

[DRY RUN] Would commit:
  "chore: bump version to 0.2.5 for bug fixes"

[DRY RUN] Would push to:
  - origin/main
  - jrc1883/popkit-claude

No changes made (dry run mode)
```

### Skip Publishing

Update version without publishing:

```
/popkit:plugin version minor --no-publish
```

### Skip Push

Update version without pushing:

```
/popkit:plugin version patch --no-push
```

### Custom Message

```
/popkit:plugin version patch --message "fix: resolve authentication timeout issue"
```

Output:
```
Current version: 0.2.5
New version: 0.2.6

[... version updates ...]

Creating commit...
  ✓ Committed: "fix: resolve authentication timeout issue"

Version 0.2.6 released successfully!
```

## Documentation Sync

### Check Documentation Status

```
/popkit:plugin docs
```

Output:
```
Analyzing 68 skills, 31 agents, 24 commands...

Found 3 AUTO-GEN sections:
  - TIER-COUNTS
  - REPO-STRUCTURE
  - KEY-FILES

2 sections need updating:

============================================================
TIER-COUNTS (changed)
============================================================
Run with --verbose to see diff

============================================================
REPO-STRUCTURE (changed)
============================================================
Run with --verbose to see diff

Run with --sync to apply these changes
```

### Sync Documentation

```
/popkit:plugin docs --sync
```

Output:
```
Analyzing 68 skills, 31 agents, 24 commands...

Found 3 AUTO-GEN sections:
  - TIER-COUNTS
  - REPO-STRUCTURE
  - KEY-FILES

Applying documentation updates...
  ✓ Updated TIER-COUNTS
  ✓ Updated REPO-STRUCTURE
  - KEY-FILES (no change)

✓ Documentation synchronized successfully
```

### Verbose Mode

Show detailed changes:

```
/popkit:plugin docs --verbose
```

Output:
```
[... analysis ...]

============================================================
TIER-COUNTS (changed)
============================================================

Current:
- Tier 1: Always-active core agents (10)
- Tier 2: On-demand specialists (15)
- Skills: 65 reusable skills
- Commands: 22 slash commands

New:
- Tier 1: Always-active core agents (11)
- Tier 2: On-demand specialists (17)
- Skills: 68 reusable skills
- Commands: 24 slash commands

Changes:
  + Tier 1: 10 → 11 (1 new)
  + Tier 2: 15 → 17 (2 new)
  + Skills: 65 → 68 (3 new)
  + Commands: 22 → 24 (2 new)
```

## Combined Workflows

### Pre-Release Checklist

```bash
# 1. Run tests
/popkit:plugin test

# 2. Validate structure
/popkit:plugin sync

# 3. Apply auto-fixes
/popkit:plugin sync apply

# 4. Check for conflicts
/popkit:plugin detect

# 5. Sync documentation
/popkit:plugin docs --sync

# 6. Bump version
/popkit:plugin version minor

# 7. Push and publish
# (automatically done by version command)
```

### CI/CD Validation Pipeline

```.github/workflows/validate.yml
name: Validate PopKit Plugin

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Run Tests
        run: /popkit:plugin test --json > test-results.json

      - name: Validate Structure
        run: /popkit:plugin sync --json > validation-results.json

      - name: Check Documentation
        run: /popkit:plugin docs --check --json > docs-results.json

      - name: Detect Conflicts
        run: /popkit:plugin detect --json > conflicts.json

      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: validation-results
          path: |
            test-results.json
            validation-results.json
            docs-results.json
            conflicts.json
```

### Development Workflow

```bash
# After making changes to agents/skills:

# 1. Run relevant tests
/popkit:plugin test agents

# 2. Check validation
/popkit:plugin sync

# 3. Fix any issues
/popkit:plugin sync apply

# 4. Update docs if needed
/popkit:plugin docs --sync

# 5. Commit changes
git add .
git commit -m "feat: add new analytics dashboard agent"
```

## Best Practices

### 1. Run Sync Before Commits

Always validate before committing:

```bash
/popkit:plugin sync
```

### 2. Use Dry Run for Version Bumps

Preview changes first:

```bash
/popkit:plugin version patch --dry-run
```

### 3. Check Conflicts After Installing Plugins

```bash
/plugin install some-plugin
/popkit:plugin detect
```

### 4. Keep Documentation Current

After structural changes:

```bash
/popkit:plugin docs --sync
```

### 5. Use JSON Output in Automation

```bash
/popkit:plugin sync --json | jq '.summary.health_score'
```

## Troubleshooting

### Sync Reports False Positives

Check specific component:

```
/popkit:plugin sync --component=skills
```

### Documentation Won't Sync

Verify AUTO-GEN markers are correct:

```bash
grep -n "AUTO-GEN" CLAUDE.md
```

### Version Bump Fails

Check git status:

```bash
git status
git remote -v
```

### Conflict Detection Misses Issues

Specify plugin directory:

```
/popkit:plugin detect --plugins ~/.claude/plugins
```
