# GitHub Release Examples

## Creating Releases

```bash
/popkit:git release create <version>
/popkit:git release create v1.2.0
/popkit:git release create v1.2.0 --draft
/popkit:git release create v1.2.0 --prerelease
/popkit:git release create v1.2.0 --title "Feature Name"
/popkit:git release create v1.2.0 --update-docs     # Also update CLAUDE.md
/popkit:git release create v1.2.0 --changelog-only  # Preview changelog
```

## Release Creation Process

1. Parse commits since last release tag
2. Generate changelog from conventional commits
3. If `--update-docs`: Update CLAUDE.md Version History
4. Create git tag
5. Create GitHub release with notes

## Changelog Generation

Uses `hooks/utils/changelog_generator.py` to:
1. Parse conventional commits (feat, fix, docs, etc.)
2. Extract issue numbers from commit messages
3. Generate formatted CLAUDE.md entry
4. Insert at correct position in Version History

```bash
# Preview what would be added to CLAUDE.md
python hooks/utils/changelog_generator.py --preview

# Generate and update CLAUDE.md
python hooks/utils/changelog_generator.py --update --version 1.2.0 --title "Feature Name"
```

## Release Notes Template

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

## Managing Releases

```bash
/popkit:git release list                  # All releases
/popkit:git release list --limit 5        # Recent 5
/popkit:git release view v1.2.0           # View release
/popkit:git release edit v1.2.0 --notes "Updated notes"
/popkit:git release delete v1.2.0         # Delete release
/popkit:git release changelog             # Preview changelog
```

## Version Detection

Automatically detects version from:
1. Command argument
2. package.json version
3. Cargo.toml version
4. Latest tag + increment
