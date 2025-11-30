---
description: Release a new version of popkit itself (meta-command for plugin maintenance)
---

# /popkit:popkit-release

Release a new version of the popkit plugin. This is a meta-command specifically for maintaining popkit itself.

## Usage

```bash
/popkit:popkit-release patch "Fixed X"      # 1.5.0 → 1.5.1
/popkit:popkit-release minor "Added Y"      # 1.5.0 → 1.6.0
/popkit:popkit-release major "Breaking Z"   # 1.5.0 → 2.0.0
/popkit:popkit-release status               # Show current version info
```

## Architecture Integration

| Component | Role |
|-----------|------|
| **Config** | `.claude-plugin/plugin.json` - Main version |
| **Config** | `.claude-plugin/marketplace.json` - Marketplace version |
| **Docs** | `CLAUDE.md` - Changelog section |
| **Tool** | `gh release create` - GitHub release |

## Instructions

You are the popkit release manager. This command automates the entire release process.

### Step 0: Parse Arguments

- `status` → Show current version and recent releases
- `patch "message"` → Bug fix release (x.y.Z)
- `minor "message"` → Feature release (x.Y.0)
- `major "message"` → Breaking change (X.0.0)

---

## Subcommand: Status

**Trigger:** `status` or no arguments

**Steps:**
1. Read current version from `.claude-plugin/plugin.json`
2. Get latest GitHub release: `gh release list --limit 1`
3. Show pending changes: `git log $(git describe --tags --abbrev=0)..HEAD --oneline`

**Output Format:**
```
## Popkit Version Status

**Current:** 1.5.0
**Latest Release:** v1.5.0 (2 hours ago)
**Pending Commits:** 3

### Unreleased Changes
- abc123 fix: restore corrupted commands
- def456 feat: add search to knowledge
- ghi789 chore: update dependencies

Ready to release? Use:
- `/popkit:popkit-release patch "description"` for bug fixes
- `/popkit:popkit-release minor "description"` for features
```

---

## Subcommand: Release (patch/minor/major)

**Trigger:** `patch`, `minor`, or `major` with description

**Steps:**

### Step 1: Calculate New Version
```python
# Read current from plugin.json
current = "1.5.0"
parts = current.split(".")

if bump_type == "patch":
    new = f"{parts[0]}.{parts[1]}.{int(parts[2])+1}"
elif bump_type == "minor":
    new = f"{parts[0]}.{int(parts[1])+1}.0"
elif bump_type == "major":
    new = f"{int(parts[0])+1}.0.0"
```

### Step 2: Update Version Files

Update `.claude-plugin/plugin.json`:
```json
{
  "version": "NEW_VERSION"
}
```

Update `.claude-plugin/marketplace.json`:
```json
{
  "plugins": [{ "version": "NEW_VERSION" }]
}
```

### Step 3: Update CLAUDE.md Changelog

Add new section at top of "New Features" section:
```markdown
## New Features (vNEW_VERSION)

- **[Summary from argument]**: [Details from commits]

### vOLD_VERSION
[Previous content moves down]
```

### Step 4: Generate Changelog from Commits

```bash
# Get commits since last tag
git log $(git describe --tags --abbrev=0)..HEAD --pretty=format:"- %s"
```

Group by conventional commit type:
- `feat:` → Features
- `fix:` → Bug Fixes
- `docs:` → Documentation
- `chore:` → Maintenance

### Step 5: Commit Changes

```bash
git add .claude-plugin/plugin.json .claude-plugin/marketplace.json CLAUDE.md
git commit -m "chore: bump version to NEW_VERSION for [description]

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Step 6: Push

```bash
git push
```

### Step 7: Create GitHub Release

```bash
gh release create vNEW_VERSION \
  --title "vNEW_VERSION - [Description]" \
  --notes "[Generated changelog]"
```

**Output Format:**
```
## Released: v1.6.0

### Changes Made
1. Updated `.claude-plugin/plugin.json`: 1.5.0 → 1.6.0
2. Updated `.claude-plugin/marketplace.json`: 1.5.0 → 1.6.0
3. Updated `CLAUDE.md` changelog
4. Committed: abc1234
5. Pushed to origin/master
6. Created release: https://github.com/jrc1883/popkit/releases/tag/v1.6.0

### Next Steps
- Restart Claude Code to trigger update notification
- Or run: `/plugin update popkit@popkit-marketplace`
```

---

## Error Handling

| Error | Response |
|-------|----------|
| Uncommitted changes | Warn and ask to commit first |
| Not on master branch | Warn and suggest switching |
| GitHub auth failed | Show `gh auth login` instructions |
| Version already exists | Error with current release info |

---

## Version Strategy Notes

For pre-1.0 (beta) software, consider:
- Use `0.x.y` format where minor = breaking, patch = features
- Or use `1.0.0-beta.N` format

Currently popkit uses `1.x.y` format. To switch to beta format:
```bash
/popkit:popkit-release set-version 0.1.0
```

---

## Related Components

- **Command:** `/popkit:release` - Generic release management
- **Command:** `/popkit:commit` - Commit with conventional format
- **Hook:** Update notifier checks GitHub releases on session start
