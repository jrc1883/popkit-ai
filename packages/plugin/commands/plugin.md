---
description: "test | docs | sync | detect | version [--verbose, --json]"
argument-hint: "<subcommand> [options]"
---

# /popkit:plugin - Plugin Management

Manage the popkit plugin itself - tests, docs, validation, conflicts, and versions.

## Subcommands

| Subcommand | Description |
|------------|-------------|
| test (default) | Run plugin self-tests |
| docs | Generate and update documentation |
| sync | Validate plugin integrity |
| detect | Detect conflicts with other plugins |
| version | Bump version with full release workflow |

---

## test (default)

Run comprehensive tests on plugin components.

**Categories:** hooks, agents, skills, routing, structure, sandbox.

**Test Files:** tests/hooks/, tests/agents/, tests/skills/, tests/routing/, tests/sandbox/

**Options:** --verbose, --fail-fast, --json, --full (sandbox), --skill <name>, --command <name>, --mode local|e2b

---

## docs

Generate and synchronize plugin documentation by analyzing the codebase.

**Process:** Run doc-sync check → Invoke skill (check or sync mode) → Report results.

**Auto-generated sections:** AUTO-GEN:TIER-COUNTS, AUTO-GEN:REPO-STRUCTURE, AUTO-GEN:KEY-FILES in CLAUDE.md.

**Options:** --check (default), --sync, --json, --verbose

---

## sync

Validate plugin integrity and offer to fix issues.

**Validation checks:** Agents (YAML, fields, references), Routing (keywords, patterns), Output Styles (schemas), Hooks (JSON protocol, syntax), Skills (SKILL.md, frontmatter), Commands (frontmatter), Tests (JSON, coverage).

**Safe auto-fixes:** Add missing frontmatter, register orphaned agents, create missing schemas, add missing test cases.

**Never auto-fix:** Code changes, agent prompts, skill instructions, configuration values.

**Options:** apply (auto-fix), --component=<name>

---

## detect

Detect conflicts between popkit and other installed Claude Code plugins.

**When it runs:** On-demand via `/popkit:plugin detect`, quick check in `/popkit:morning`, NOT at session start.

**Conflict categories:** Command Collision (HIGH), Skill Collision (MEDIUM), Hook Collision (MEDIUM), Routing Overlap (LOW).

**Process:** Scan plugins → Load manifests → Extract components → Compare → Report.

**Options:** --quick (one-line summary), --json, --plugins <dir>

---

## version

Bump plugin version with full release workflow.

**Process:** Determine bump type → Update version files (plugin.json, marketplace.json) → Update CHANGELOG.md → Commit → Push → Publish to public repo.

**Version numbering:** MAJOR (breaking), MINOR (features), PATCH (fixes).

**Options:** patch/minor/major, --dry-run, --no-publish, --no-push, --message "text"

---

## Architecture

| Component | Integration |
|-----------|-------------|
| Test Definitions | tests/ directory |
| Test Skills | skills/pop-plugin-test/, pop-sandbox-test/ |
| Doc Skills | skills/pop-auto-docs/, pop-doc-sync/ |
| Doc-Sync Utility | hooks/utils/doc_sync.py |
| Validation | skills/pop-validation-engine/ |
| Conflict Detector | hooks/utils/plugin_detector.py |
| Sandbox Analytics | tests/sandbox/analytics.py |

**Related:** /popkit:debug routing, /popkit:morning, /popkit:nightly

## Examples

See examples/plugin/ for: test-examples.md, sync-detect-version.md.
