---
description: Plugin management - testing, documentation generation, and integrity validation
---

# /popkit:plugin - Plugin Management

Manage the popkit plugin itself - run tests, generate docs, and validate integrity.

## Usage

```
/popkit:plugin <subcommand> [options]
```

## Subcommands

| Subcommand | Description |
|------------|-------------|
| `test` | Run plugin self-tests (default) |
| `docs` | Generate and update documentation |
| `sync` | Validate plugin integrity |

---

## Subcommand: test (default)

Run comprehensive tests on plugin components to ensure everything works correctly.

```
/popkit:plugin                        # Run all tests (default)
/popkit:plugin test                   # Same as above
/popkit:plugin test hooks             # Test hooks only
/popkit:plugin test agents            # Test agents only
/popkit:plugin test skills            # Test skills only
/popkit:plugin test routing           # Test agent routing
/popkit:plugin test structure         # Test file structure
```

### Test Categories

| Category | What It Tests |
|----------|---------------|
| `hooks` | JSON stdin/stdout, error handling, timeouts |
| `agents` | Definitions, tools, routing keywords |
| `skills` | SKILL.md format, descriptions, dependencies |
| `routing` | Agent selection based on prompts |
| `structure` | File existence, YAML validity, references |

### Process

1. Load test definitions from `tests/` directory
2. Execute tests by category
3. Report results with pass/fail summary

### Output

```
Running plugin self-tests...

[Structure Tests]
[ok] agents/config.json valid
[ok] hooks/hooks.json valid
[ok] All 29 agents have definitions
[ok] All 22 skills have SKILL.md

[Hook Tests]
[ok] pre-tool-use: JSON protocol
[ok] post-tool-use: JSON protocol
[ok] session-start: JSON protocol
...

[Agent Tests]
[ok] bug-whisperer: definition valid
[ok] code-reviewer: routing keywords work
...

[Routing Tests]
[ok] "fix bug" -> bug-whisperer (0.8 confidence)
[ok] "review code" -> code-reviewer (0.9 confidence)
...

---
Results: 54 passed, 0 failed, 2 skipped
Time: 12.3s
---
```

### Options

| Flag | Description |
|------|-------------|
| `--verbose` | Show detailed test output |
| `--fail-fast` | Stop on first failure |
| `--json` | Output results as JSON |

### Test Files

Test definitions are stored in:
- `tests/hooks/` - Hook input/output tests
- `tests/agents/` - Agent definition tests
- `tests/skills/` - Skill structure tests
- `tests/routing/` - Agent routing tests

---

## Subcommand: docs

Generate and synchronize plugin documentation by analyzing the codebase.

```
/popkit:plugin docs                   # Full documentation generation
/popkit:plugin docs check             # Check for documentation drift
/popkit:plugin docs claude            # Update CLAUDE.md only
/popkit:plugin docs readme            # Update README.md only
/popkit:plugin docs components        # Generate component reference
```

### Process

1. Scan the plugin structure:
   - Count agents in `agents/` directories
   - Extract skill descriptions from `skills/*/SKILL.md`
   - List commands from `commands/`
   - Document hooks from `hooks/`
2. Generate or update documentation files:
   - CLAUDE.md - Project instructions
   - README.md - User documentation
   - docs/components.md - Component reference
3. Report any drift between code and documentation

### Options

| Flag | Description |
|------|-------------|
| `check` | Only check for drift, don't update files |
| `claude` | Update CLAUDE.md only |
| `readme` | Update README.md only |
| `components` | Generate component reference only |

### Output

```
/popkit:plugin docs

Scanning plugin structure...
- Agents: 29 (11 tier-1, 15 tier-2, 3 feature-workflow)
- Skills: 22 (21 + auto-docs)
- Commands: 16 (consolidated with subcommands)
- Hooks: 10

Updating CLAUDE.md...
[ok] Repository structure updated
[ok] Component counts updated

Updating README.md...
[ok] Feature counts updated
[ok] Installation section current

No documentation drift detected.
```

---

## Subcommand: sync

Validate plugin integrity and offer to fix issues.

```
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

#### Output Styles (`output-styles/`)
- All styles have YAML frontmatter
- Schemas exist for styles with `output_style` references

#### Hooks (`hooks/`)
- All hooks in `hooks.json` exist as files
- Python files have valid syntax
- Hooks follow JSON stdin/stdout protocol
- Shebang is `#!/usr/bin/env python3`

#### Skills (`skills/`)
- Each skill directory has `SKILL.md`
- Frontmatter has required fields: name, description
- No duplicate skill names

#### Commands (`commands/`)
- All command files have valid frontmatter
- Description field is present

#### Tests (`tests/`)
- Test files are valid JSON
- Routing rules have test coverage

### Output

```
## Popkit Sync Report

**Scan Date:** [timestamp]
**Components Checked:** 7
**Issues Found:** 1 error, 3 warnings, 2 info

### Summary

| Component | Status | Issues |
|-----------|--------|--------|
| Agents | warning | 2 |
| Routing | pass | 0 |
| Output Styles | error | 1 |
| Hooks | pass | 0 |
| Skills | warning | 1 |
| Commands | pass | 0 |
| Tests | info | 2 |

### Errors (Must Fix)
- `output-styles/agent-handoff.md`: Missing schema

### Warnings (Should Fix)
- `agents/tier-2-on-demand/new-agent.md`: Missing output_style field

### Auto-Fixable Issues
1. Missing schema - Will create from template

Run `/popkit:plugin sync apply` to apply these fixes.
```

### Apply Mode

**Safe Auto-Fixes:**
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

## Examples

```bash
# Run all plugin tests
/popkit:plugin
/popkit:plugin test

# Test specific category
/popkit:plugin test routing
/popkit:plugin test hooks

# Update documentation
/popkit:plugin docs
/popkit:plugin docs check

# Validate plugin integrity
/popkit:plugin sync
/popkit:plugin sync apply
```

---

## Architecture Integration

| Component | Integration |
|-----------|-------------|
| Test Definitions | `tests/` directory |
| Plugin Test Skill | `skills/pop-plugin-test/SKILL.md` |
| Auto-Docs Skill | `skills/pop-auto-docs/SKILL.md` |
| Validation Engine | `skills/pop-validation-engine/SKILL.md` |
| Documentation | CLAUDE.md, README.md |

## Related Commands

| Command | Purpose |
|---------|---------|
| `/popkit:debug routing` | Debug agent routing issues |
| `/popkit:morning` | Includes plugin health check |
