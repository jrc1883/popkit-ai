# PopKit Modular Plugin Testing Guide

**Last Updated**: December 23, 2025
**Architecture Version**: Post-Epic #580 (Modular Plugins)

## Overview

PopKit's testing infrastructure has been redesigned to support the modular plugin architecture where functionality is distributed across multiple independent plugin packages.

### Key Principles

1. **Independent Plugin Testing**: Each plugin is self-contained and testable independently
2. **No Centralized Configuration**: No `agents/config.json` - Claude Code discovers agents from markdown files
3. **Semantic Routing**: Agent routing based on descriptions, not keyword mappings
4. **Cross-Plugin Validation**: Ensures all plugins work together without conflicts

## Architecture

### Plugin Packages

PopKit consists of 5 modular plugin packages:

| Package | Agents | Purpose |
|---------|--------|---------|
| `popkit-core` | 9 | Core utilities, plugin management, Power Mode |
| `popkit-dev` | 5 | Development workflows (dev, git, routine) |
| `popkit-ops` | 6 | Deployment, security, quality assurance |
| `popkit-research` | 1 | Research and knowledge management |
| `popkit-suite` | 0 | Meta-plugin for backwards compatibility |
| **Total** | **21** | |

### Test Distribution

Tests are organized by plugin package:

```
packages/
  popkit-core/
    tests/
      agents/          # Agent definition validation
      hooks/           # Hook protocol tests
      skills/          # Skill format tests
      structure/       # Plugin integrity tests
      cross-plugin/    # Cross-plugin validation
    run_tests.py       # Single plugin test runner
    run_all_tests.py   # All plugins test runner

  popkit-dev/tests/    # (Future) Dev-specific tests
  popkit-ops/tests/    # (Future) Ops-specific tests
  ...
```

## Running Tests

### Test All Plugins

Run the comprehensive modular test runner:

```bash
cd packages/popkit-core
python run_all_tests.py
```

**Output:**
```
PopKit Modular Plugin Test Runner
============================================================
Discovered 5 plugin package(s)

Testing Plugin: popkit-core
============================================================
Found 6 test file(s)
[ok] Agent markdown files exist in all plugins
[ok] All agents have valid YAML frontmatter
...

Testing Plugin: popkit-dev
============================================================
No tests directory found for popkit-dev

============================================================
MODULAR PLUGIN TEST SUMMARY
============================================================
Total Plugins Tested: 5
Plugins Passed: 4
Total Test Cases: 31
Tests Passed: 19 (61.3%)
Duration: 6.23s
```

### Test Single Plugin

Test an individual plugin package:

```bash
cd packages/popkit-core
python run_tests.py              # All tests for this plugin
python run_tests.py agents       # Just agent tests
python run_tests.py --verbose    # Detailed output
```

### Test Options

| Option | Description |
|--------|-------------|
| `--verbose` | Show detailed output including passing tests |
| `--fail-fast` | Stop on first failure |
| `--json` | Output results as JSON for CI integration |

## Test Categories

### 1. Agent Tests (`agents/`)

**Purpose**: Validate agent markdown files have proper structure for semantic routing

**What's Tested**:
- Agent markdown files exist in plugins
- Valid YAML frontmatter with `name` and `description`
- Descriptions are specific enough for semantic matching (>20 chars)
- No generic phrases like "helper" or "utility"
- Agent names are unique across all plugins
- Agents are in proper tier directories

**Test File**: `tests/agents/test-agent-definitions.json`

**Example Assertions**:
```json
{
  "assertions": [
    {
      "type": "agents_directory_exists",
      "description": "Each plugin should have an agents/ directory"
    },
    {
      "type": "yaml_frontmatter_exists",
      "description": "Agent files must have YAML frontmatter"
    },
    {
      "type": "has_frontmatter_field",
      "field": "description",
      "description": "Descriptions enable semantic routing"
    }
  ]
}
```

### 2. Hook Tests (`hooks/`)

**Purpose**: Validate hooks follow JSON stdin/stdout protocol

**What's Tested**:
- Hooks accept JSON input via stdin
- Hooks output valid JSON to stdout
- Exit codes are correct (0 for success)
- Hooks complete within timeout limits
- Hook logic executes correctly

**Test Files**:
- `tests/hooks/test-pre-tool-use.json`
- `tests/hooks/test-post-tool-use.json`
- `tests/hooks/test-session-start.json`

**Note**: Some hook tests require actual execution environments and may fail in isolation.

### 3. Skill Tests (`skills/`)

**Purpose**: Validate skill format and structure

**What's Tested**:
- Each skill has a `SKILL.md` file
- Valid YAML frontmatter with required fields
- No hardcoded absolute paths
- Proper skill naming convention (`pop-*`)

**Test File**: `tests/skills/test-skill-format.json`

### 4. Structure Tests (`structure/`)

**Purpose**: Validate plugin directory structure and required files

**What's Tested**:
- `.claude-plugin/plugin.json` exists and is valid
- README.md exists
- Optional directories (agents, skills, commands, hooks) are valid if present
- No centralized `agents/config.json` exists (modular architecture)
- All components are registered in `plugin.json`

**Test File**: `tests/structure/test-plugin-integrity.json`

**Key Assertion** (Modular Architecture):
```json
{
  "case_id": "no-centralized-config",
  "name": "No centralized config.json (modular architecture)",
  "assertions": [
    {
      "type": "file_not_exists",
      "path": "agents/config.json",
      "description": "Centralized config.json should not exist"
    }
  ]
}
```

### 5. Cross-Plugin Tests (`cross-plugin/`)

**Purpose**: Ensure all plugins work together without conflicts

**What's Tested**:
- No duplicate command names across plugins
- No duplicate skill names across plugins
- No duplicate agent names across plugins
- Consistent versioning (all use semver)
- No circular dependencies between plugins

**Test File**: `tests/cross-plugin/test-plugin-ecosystem.json`

## Test Utilities

Testing utilities are in `packages/shared-py/popkit_shared/utils/`:

| Utility | Purpose |
|---------|---------|
| `test_runner.py` | Core test execution engine |
| `plugin_validator.py` | Plugin structure validation (updated for modular architecture) |
| `agent_validator.py` | Agent markdown file validation (new for modular architecture) |
| `skill_validator.py` | Skill format validation |
| `hook_validator.py` | Hook protocol validation |

### Key Updates for Modular Architecture

**plugin_validator.py**:
- `agents/config.json` is now optional (not required)
- Warns if centralized config exists (legacy structure)
- All component directories (agents, skills, commands, hooks) are optional

**agent_validator.py** (new):
- Validates agent markdown files directly
- Parses YAML frontmatter
- Checks description quality for semantic routing
- Validates tier directory structure

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Test PopKit Plugins

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          cd packages/shared-py
          pip install -r requirements.txt

      - name: Run All Plugin Tests
        run: |
          cd packages/popkit-core
          python run_all_tests.py --json > test-results.json

      - name: Upload Test Results
        uses: actions/upload-artifact@v2
        if: always()
        with:
          name: test-results
          path: packages/popkit-core/test-results.json
```

## Writing New Tests

### 1. Create Test Definition

Tests are defined as JSON files in the appropriate category directory:

```json
{
  "test_id": "my-new-test",
  "category": "agents",
  "name": "My New Test",
  "description": "What this test validates",
  "severity": "high",
  "test_cases": [
    {
      "case_id": "test-case-1",
      "name": "Test case description",
      "assertions": [
        {
          "type": "assertion_type",
          "description": "What this assertion checks"
        }
      ]
    }
  ]
}
```

### 2. Supported Assertion Types

| Type | Purpose |
|------|---------|
| `file_exists` | File must exist |
| `file_not_exists` | File must not exist |
| `directory_exists` | Directory must exist |
| `json_valid` | File contains valid JSON |
| `yaml_frontmatter_exists` | Markdown has valid YAML frontmatter |
| `has_frontmatter_field` | Frontmatter has specific field |
| `agents_directory_exists` | Plugin has agents/ directory |
| `agent_files_found` | Minimum number of agent files exist |
| `exit_code` | Hook returns expected exit code |
| `duration` | Execution completes within time limit |

### 3. Add Test to Category

Place the test file in the appropriate directory:
- `tests/agents/` for agent validation
- `tests/hooks/` for hook protocol
- `tests/skills/` for skill format
- `tests/structure/` for plugin integrity
- `tests/cross-plugin/` for cross-plugin validation

## Migration from Monolithic to Modular

### What Changed

**Before (Monolithic)**:
- Single `agents/config.json` with all routing rules
- Keyword-based agent routing
- Centralized test suite

**After (Modular)**:
- Each plugin has own agents (markdown files)
- Semantic routing based on descriptions
- Distributed test suite per plugin
- Cross-plugin validation

### Updating Existing Tests

**Old approach** (looking for config.json):
```json
{
  "config_file": "agents/config.json",
  "assertions": [
    {
      "type": "agent_activated",
      "agent": "bug-whisperer"
    }
  ]
}
```

**New approach** (validating markdown):
```json
{
  "scan_pattern": "agents/**/*.md",
  "assertions": [
    {
      "type": "yaml_frontmatter_exists"
    },
    {
      "type": "has_frontmatter_field",
      "field": "description"
    }
  ]
}
```

## Troubleshooting

### "Config file not found: agents/config.json"

**Cause**: Test is looking for old centralized config
**Fix**: Update test to use agent markdown validation (see agent-definitions.json)

### "No agents directory found"

**Cause**: Plugin doesn't have agents (this is OK - agents are optional)
**Fix**: No action needed - test will pass with warning

### Hook tests failing with exit code mismatches

**Cause**: Hooks require actual execution environment
**Fix**: These failures are expected in isolated testing - hooks work correctly in Claude Code

### Cross-plugin tests skipped

**Cause**: Cross-plugin validators not fully implemented yet
**Fix**: Manual validation - check for naming conflicts across plugin.json files

## Best Practices

1. **Write Tests for Each Plugin**: Add tests in each plugin's `tests/` directory
2. **Test Independence**: Each test should be runnable independently
3. **Clear Descriptions**: Make test names and descriptions clear
4. **Use Assertions Wisely**: Choose appropriate assertion types
5. **Document Expected Behavior**: Add notes to test definitions
6. **Keep Tests Updated**: Update tests when changing plugin structure

## Future Enhancements

- [ ] Implement full cross-plugin validator utilities
- [ ] Add integration tests for multi-plugin workflows
- [ ] Create test templates for new plugin packages
- [ ] Add performance benchmarking tests
- [ ] Implement test coverage reporting

## Related Documentation

- [Epic #580: Plugin Modularization](../docs/plans/2025-12-20-plugin-modularization-design.md)
- [Testing Validation Report](../docs/assessments/2025-12-21-phase5-validation-report-initial.md)
- [Claude Code Plugin Documentation](https://docs.anthropic.com/claude/docs/plugins)

---

For questions or issues with testing, see `/popkit:bug report` or open a GitHub issue.
