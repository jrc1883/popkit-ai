---
description: Validate and synchronize plugin state across all components
---

# /popkit:sync

Validates plugin integrity and offers to fix issues. Uses the Scan -> Compare -> Report -> Recommend/Apply pattern.

## Usage

```bash
/popkit:sync                         # Analyze and report only
/popkit:sync apply                   # Automatically apply safe fixes
/popkit:sync --component=agents      # Check specific component
/popkit:sync --component=hooks       # Check hooks only
```

## Architecture Integration

| Component | Role |
|-----------|------|
| **Skill** | `pop-validation-engine` - Reusable validation pattern |
| **Pattern** | Scan -> Compare -> Report -> Recommend/Apply |
| **Test Dir** | `tests/` - Validation test definitions |

## Instructions

You are the sync validation engine. Parse ARGUMENTS to determine mode.

### Step 0: Parse Arguments

- No args → full scan, report only
- `apply` → scan and apply safe fixes
- `--component=X` → scan only that component

---

## Phase 1: Scan

Scan these components (or specific one if `--component` provided):

### 1. Agents (`agents/`)
- [ ] All agent files have valid YAML frontmatter
- [ ] Required fields present: description, tools (in frontmatter or Task tool description)
- [ ] output_style references exist in `output-styles/`
- [ ] Agent is listed in appropriate tier in `config.json`

### 2. Routing (`agents/config.json`)
- [ ] All keywords map to valid agent references
- [ ] File patterns are syntactically valid globs
- [ ] Error patterns have valid agent mappings
- [ ] No orphaned agents (defined but not in any tier)
- [ ] No missing agents (referenced but not defined)

### 3. Output Styles (`output-styles/`)
- [ ] All styles have YAML frontmatter
- [ ] Schemas exist for styles with `output_style` references
- [ ] Example sections are present

### 4. Hooks (`hooks/`)
- [ ] All hooks in `hooks.json` exist as files
- [ ] Python files have valid syntax
- [ ] Hooks follow JSON stdin/stdout protocol
- [ ] Shebang is `#!/usr/bin/env python3`

### 5. Skills (`skills/`)
- [ ] Each skill directory has `SKILL.md`
- [ ] Frontmatter has required fields: name, description
- [ ] No duplicate skill names

### 6. Commands (`commands/`)
- [ ] All command files have valid frontmatter
- [ ] No `name:` field (uses filename prefix)
- [ ] Description field is present

### 7. Tests (`tests/`)
- [ ] Test files are valid JSON
- [ ] Routing rules have test coverage
- [ ] Agent types have routing tests

---

## Phase 2: Compare

Build validation results:

```
ValidationResult {
  component: string
  status: 'pass' | 'warning' | 'error'
  issues: Issue[]
}

Issue {
  severity: 'error' | 'warning' | 'info'
  file: string
  line?: number
  message: string
  autoFixable: boolean
  suggestedFix?: string
}
```

---

## Phase 3: Report

**Output Format:**
```
## Popkit Sync Report

**Scan Date:** [timestamp]
**Components Checked:** [count]
**Issues Found:** [errors] errors, [warnings] warnings, [info] info

### Summary

| Component | Status | Issues |
|-----------|--------|--------|
| Agents | pass/warning/error | [count] |
| Routing | pass/warning/error | [count] |
| Output Styles | pass/warning/error | [count] |
| Hooks | pass/warning/error | [count] |
| Skills | pass/warning/error | [count] |
| Commands | pass/warning/error | [count] |
| Tests | pass/warning/error | [count] |

### Errors (Must Fix)
- `[file]`: [message]

### Warnings (Should Fix)
- `[file]`: [message]

### Info (Nice to Have)
- `[file]`: [message]

### Auto-Fixable Issues
The following can be automatically fixed:
1. [issue] - [fix description]

Run `/popkit:sync apply` to apply these fixes.
```

---

## Phase 4: Apply (if requested)

**Only apply when** `apply` argument is provided.

**Safe Auto-Fixes:**
- Add missing frontmatter fields with defaults
- Register orphaned agents in config.json tiers
- Create missing schema files from templates
- Add missing routing test cases
- Remove explicit `name:` fields from command frontmatter

**Never Auto-Fix:**
- Code changes in hooks
- Agent prompt content
- Skill instructions
- Configuration values requiring decisions

**Apply Process:**
1. Create backup of files to modify
2. Apply fixes one at a time
3. Report each fix applied
4. Re-run validation to confirm

**Output Format:**
```
## Applying Fixes

### Backup Created
Location: `~/.claude/sync-backups/[timestamp]/`

### Fixes Applied
1. [file]: [fix applied]
2. [file]: [fix applied]

### Re-validation
[Run Phase 3 Report again]
```

---

## Example Output

```
## Popkit Sync Report

**Scan Date:** 2025-01-28T10:00:00Z
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
- `output-styles/agent-handoff.md`: Missing schema at `schemas/agent-handoff.schema.json`

### Warnings (Should Fix)
- `agents/tier-2-on-demand/new-agent.md`: Missing output_style field
- `agents/tier-2-on-demand/another-agent.md`: Not in config.json tiers
- `skills/pop-new-skill/SKILL.md`: Missing description in frontmatter

### Info (Nice to Have)
- `tests/routing/`: No test for 'format' keyword
- `tests/routing/`: No test for 'style' keyword

### Auto-Fixable Issues
1. Missing schema - Will create from template
2. Missing output_style - Will add default
3. Orphaned agent - Will add to tier-2-on-demand

Run `/popkit:sync apply` to apply these fixes.
```

---

## Related Components

- **Skill:** `pop-validation-engine` - Pattern for validation
- **Command:** `/popkit:plugin-test` - Run automated tests
- **Command:** `/popkit:routing-debug` - Debug agent routing
- **Command:** `/popkit:auto-docs` - Update documentation
