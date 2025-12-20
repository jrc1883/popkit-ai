# Plugin Sync, Detect & Version Examples

## docs - Documentation Sync

### Basic Usage

```bash
/popkit:plugin docs                   # Full documentation check and generation
/popkit:plugin docs --check           # Check for documentation drift only
/popkit:plugin docs --sync            # Auto-fix drift in auto-generated sections
/popkit:plugin docs --json            # Output drift report as JSON
```

### Auto-Generated Sections

The `--sync` mode updates content between these markers in CLAUDE.md:

| Marker | Content Updated |
|--------|-----------------|
| `AUTO-GEN:TIER-COUNTS` | Agent tier counts |
| `AUTO-GEN:REPO-STRUCTURE` | Directory tree with counts |
| `AUTO-GEN:KEY-FILES` | Key files table |

---

## sync - Validate Plugin Integrity

### Basic Usage

```bash
/popkit:plugin sync                   # Analyze and report only
/popkit:plugin sync apply             # Automatically apply safe fixes
/popkit:plugin sync --component=agents
/popkit:plugin sync --component=hooks
```

### Validation Checks

#### Agents (`agents/`)
- All agent files have valid YAML frontmatter
- Required fields present: description, tools
- output_style references exist in `output-styles/`
- Agent is listed in appropriate tier in `config.json`

#### Routing (`agents/config.json`)
- All keywords map to valid agent references
- File patterns are syntactically valid globs
- No orphaned agents (defined but not in any tier)
- No missing agents (referenced but not defined)

#### Hooks, Skills, Commands
- Validate frontmatter, schemas, dependencies
- Ensure JSON stdin/stdout protocol for hooks
- Check for duplicate names

### Safe Auto-Fixes

- Add missing frontmatter fields with defaults
- Register orphaned agents in config.json tiers
- Create missing schema files from templates
- Add missing routing test cases

**Never Auto-Fix:**
- Code changes in hooks
- Agent prompt content
- Skill instructions
- Configuration values requiring decisions

---

## detect - Plugin Conflicts

### Basic Usage

```bash
/popkit:plugin detect                 # Full conflict report
/popkit:plugin detect --quick         # One-line summary
/popkit:plugin detect --json          # JSON output
```

### Conflict Categories

| Type | Severity | Description |
|------|----------|-------------|
| Command Collision | HIGH | Same command name in multiple plugins |
| Skill Collision | MEDIUM | Same skill name in multiple plugins |
| Hook Collision | MEDIUM | Same event, overlapping tools |
| Routing Overlap | LOW | Same keywords to different agents |

### Quick Mode

```
/popkit:plugin detect --quick

Plugin Conflicts: 2 (1 HIGH, 1 medium)
```

Or if no conflicts:

```
Plugin Conflicts: None (3 plugins, all compatible)
```

---

## version - Version Management

### Basic Usage

```bash
/popkit:plugin version                # Interactive bump (asks for type)
/popkit:plugin version patch          # 1.0.0 → 1.0.1
/popkit:plugin version minor          # 1.0.0 → 1.1.0
/popkit:plugin version major          # 1.0.0 → 2.0.0
/popkit:plugin version --dry-run      # Preview without changes
```

### Process

1. **Determine Version Bump** (patch/minor/major)
2. **Update Version Files** (plugin.json, marketplace.json)
3. **Update CHANGELOG.md** (add new version entry)
4. **Commit Changes** (`git commit -m "chore: bump version to X.Y.Z"`)
5. **Push to Origin** (`git push`)
6. **Publish to Public Repo** (git subtree split + push to popkit-claude)

### Version Numbering

Following semantic versioning:
- **MAJOR** (X.0.0): Breaking changes to commands, agents, or hooks
- **MINOR** (0.X.0): New features, commands, or agents (backward compatible)
- **PATCH** (0.0.X): Bug fixes, documentation updates

### Sample Output

```
/popkit:plugin version minor

PopKit Version Bump
===================

Current version: 1.0.0
New version:     1.1.0

Files to update:
  - packages/plugin/.claude-plugin/plugin.json
  - packages/plugin/.claude-plugin/marketplace.json
  - CHANGELOG.md

[1/5] Updating version files...     ✓
[2/5] Adding changelog entry...     ✓
[3/5] Committing changes...         ✓
[4/5] Pushing to origin...          ✓
[5/5] Publishing to popkit-claude...✓

Release complete!
  Tag: v1.1.0
  Public repo: https://github.com/jrc1883/popkit-claude

Users can update with:
  /plugin update popkit@popkit-marketplace
```
