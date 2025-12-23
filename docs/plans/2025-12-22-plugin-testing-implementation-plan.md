# Plugin Testing Infrastructure - Implementation Plan

**Date**: 2025-12-22
**Epic**: #580 Phase 6 - Documentation & Release
**Priority**: Quality over speed - comprehensive implementation

## Overview

Build complete testing infrastructure for PopKit plugin validation, documentation synchronization, and sandbox testing.

## Architecture

```
packages/popkit-core/
├── skills/
│   ├── pop-plugin-test/          # Test runner (P0)
│   ├── pop-validation-engine/    # Integrity validation (P1)
│   ├── pop-doc-sync/             # Doc synchronization (P1)
│   └── pop-auto-docs/            # Doc generation (P2)
├── tests/
│   ├── hooks/                    # Hook protocol tests
│   ├── agents/                   # Agent routing tests
│   ├── skills/                   # Skill format tests
│   ├── routing/                  # Routing logic tests
│   ├── structure/                # Plugin integrity tests
│   └── sandbox/                  # Sandbox tests (P3)
└── examples/
    └── plugin/                   # Usage examples
```

## Dependencies

### Available
- ✅ `popkit_shared.utils.doc_sync` - Documentation utilities
- ✅ `popkit_shared.utils.plugin_detector` - Conflict detection
- ✅ All 69 shared utilities in `popkit_shared`
- ✅ Hook infrastructure (25 hooks firing programmatically)

### To Create
- Test runner engine
- Validation engine
- Test definition format
- Example documentation

## Implementation Phases

### Phase 1: Test Infrastructure (P0) ⭐

**Goal**: Make `/popkit:plugin test` functional

#### 1.1 Test Definition Format

Create standardized JSON format for all tests:

```json
{
  "test_id": "hook-pre-tool-use-protocol",
  "category": "hooks",
  "name": "Pre-Tool-Use Hook JSON Protocol",
  "description": "Verify pre-tool-use.py follows JSON stdin/stdout protocol",
  "severity": "critical",
  "test_cases": [
    {
      "case_id": "valid-bash-input",
      "name": "Valid Bash tool produces valid output",
      "input": {
        "tool": "Bash",
        "args": {"command": "echo test"}
      },
      "assertions": [
        {
          "type": "exit_code",
          "expected": 0
        },
        {
          "type": "json_valid",
          "field": "stdout"
        },
        {
          "type": "has_field",
          "field": "status"
        }
      ]
    }
  ],
  "dependencies": ["pre-tool-use.py", "popkit_shared.utils"]
}
```

**Test categories**:
- `hooks` - Hook protocol validation
- `agents` - Agent routing logic
- `skills` - Skill format compliance
- `routing` - Routing confidence and keywords
- `structure` - Plugin integrity
- `sandbox` - Isolated execution tests

#### 1.2 Test Definitions Structure

```
tests/
├── hooks/
│   ├── test-pre-tool-use.json
│   ├── test-post-tool-use.json
│   ├── test-session-start.json
│   ├── test-user-prompt-submit.json
│   └── test-agent-orchestrator.json
├── agents/
│   ├── test-routing-keywords.json
│   ├── test-routing-confidence.json
│   └── test-agent-activation.json
├── skills/
│   ├── test-skill-format.json
│   ├── test-skill-frontmatter.json
│   └── test-skill-execution.json
├── routing/
│   ├── test-keyword-matching.json
│   ├── test-file-pattern-matching.json
│   └── test-error-pattern-matching.json
├── structure/
│   ├── test-plugin-json.json
│   ├── test-hooks-json.json
│   ├── test-agent-config.json
│   └── test-skill-discovery.json
└── sandbox/
    ├── test-isolation.json
    └── analytics.py
```

#### 1.3 pop-plugin-test Skill

**Skill structure**:

```markdown
---
name: pop-plugin-test
description: Run comprehensive tests on plugin components - validates hooks, agents, skills, routing, and plugin structure
---

# Plugin Test Runner

Executes test definitions to validate plugin integrity and functionality.

## When to Use

- User runs `/popkit:plugin test`
- Post-implementation validation
- Pre-release verification
- Debugging plugin issues

## Process

### 1. Parse Arguments

Options:
- Category filter: `hooks`, `agents`, `skills`, `routing`, `structure`, `sandbox`
- `--verbose` - Show detailed test output
- `--fail-fast` - Stop on first failure
- `--json` - Output results as JSON
- `--full` - Include sandbox tests (requires E2B)

### 2. Load Test Definitions

Scan `tests/` directory and load JSON definitions:

```python
from pathlib import Path
import json

def load_tests(category=None):
    tests_dir = Path(__file__).parent.parent.parent / "tests"
    test_files = []

    if category:
        test_files = list((tests_dir / category).glob("*.json"))
    else:
        test_files = list(tests_dir.glob("**/*.json"))

    return [json.loads(f.read_text()) for f in test_files]
```

### 3. Execute Tests

For each test definition:

```python
from popkit_shared.utils.test_runner import TestRunner

runner = TestRunner(verbose=args.verbose, fail_fast=args.fail_fast)

for test_def in tests:
    result = runner.execute(test_def)
    results.append(result)
```

### 4. Generate Report

Format results:

```
PopKit Plugin Test Results
==========================

Category: hooks
  ✓ Pre-Tool-Use Hook Protocol (5/5 cases)
  ✓ Post-Tool-Use Hook Protocol (5/5 cases)
  ✗ Session-Start Hook Protocol (3/5 cases)
    Failed: test-session-start-timeout
    Reason: Hook exceeded 10s timeout

Category: agents
  ✓ Routing Keywords (12/12 cases)
  ✓ Routing Confidence (8/8 cases)

Summary:
  Total: 35 tests
  Passed: 33 (94%)
  Failed: 2 (6%)
  Duration: 12.3s
```

### 5. JSON Output (if --json)

```json
{
  "summary": {
    "total": 35,
    "passed": 33,
    "failed": 2,
    "duration_ms": 12345
  },
  "categories": {
    "hooks": {
      "total": 10,
      "passed": 9,
      "failed": 1
    }
  },
  "failures": [
    {
      "test_id": "hook-session-start-timeout",
      "category": "hooks",
      "reason": "Hook exceeded 10s timeout",
      "expected": "< 10000ms",
      "actual": "11234ms"
    }
  ]
}
```

## Integration

Uses shared utilities:
- `popkit_shared.utils.test_runner` - Test execution engine
- `popkit_shared.utils.hook_validator` - Hook protocol validation
- `popkit_shared.utils.agent_router` - Routing logic validation
```

### Phase 2: Validation & Documentation (P1)

#### 2.1 pop-validation-engine Skill

Validates plugin integrity and offers safe auto-fixes:

**Validation checks**:
- Agent YAML syntax and required fields
- Skill SKILL.md frontmatter completeness
- Command markdown frontmatter
- Hook hooks.json schema compliance
- Routing config.json structure
- Output style schema validation

**Safe auto-fixes**:
- Add missing frontmatter fields (with defaults)
- Register orphaned agents in config.json
- Create missing output style schemas
- Add missing test case placeholders

**Never auto-fix** (report only):
- Code changes
- Agent prompts
- Skill instructions
- Configuration values

#### 2.2 pop-doc-sync Skill

Wrapper around `doc_sync.py` utility for documentation synchronization:

**Features**:
- Analyzes codebase for AUTO-GEN sections
- Updates TIER-COUNTS, REPO-STRUCTURE, KEY-FILES
- Validates cross-references
- Reports stale documentation

**Options**:
- `--check` - Report what would change (default)
- `--sync` - Apply changes
- `--json` - JSON output
- `--verbose` - Show detailed changes

### Phase 3: Documentation Generation (P2)

#### 3.1 pop-auto-docs Skill

Analyzes codebase and generates/updates documentation:

**Generates**:
- README sections from plugin.json
- CHANGELOG entries from git commits
- API documentation from code analysis
- Migration guides from breaking changes

**Process**:
1. Scan codebase for documentation needs
2. Analyze existing docs for gaps
3. Generate missing documentation
4. Validate cross-references
5. Report what was created/updated

### Phase 4: Sandbox Testing (P3)

#### 4.1 Sandbox Infrastructure

**Purpose**: Isolated execution testing for skills and agents

**Components**:
- `tests/sandbox/analytics.py` - Metrics and analysis
- `pop-sandbox-test` skill - Sandbox test runner
- E2B integration for cloud isolation

**Tests**:
- Skill execution in isolated environment
- Agent coordination without side effects
- Hook firing without state pollution
- Performance benchmarking

### Phase 5: Examples & Documentation

#### 5.1 Test Examples

`examples/plugin/test-examples.md`:
- Running all tests
- Running specific categories
- Interpreting results
- Writing custom tests
- Debugging failures

#### 5.2 Workflow Examples

`examples/plugin/sync-detect-version.md`:
- Validation workflow
- Documentation sync
- Conflict detection
- Version bumping

## Test Definition Specifications

### Assertion Types

| Type | Description | Example |
|------|-------------|---------|
| `exit_code` | Process exit code | `{"type": "exit_code", "expected": 0}` |
| `json_valid` | Valid JSON output | `{"type": "json_valid", "field": "stdout"}` |
| `has_field` | Field exists | `{"type": "has_field", "field": "status"}` |
| `field_value` | Field matches value | `{"type": "field_value", "field": "status", "expected": "success"}` |
| `contains` | String contains substring | `{"type": "contains", "field": "message", "expected": "complete"}` |
| `regex` | Regex match | `{"type": "regex", "field": "output", "pattern": "^✓"}` |
| `duration` | Execution time limit | `{"type": "duration", "max_ms": 5000}` |

### Test Severity Levels

- **critical** - Must pass before release
- **high** - Should pass, failure requires explanation
- **medium** - Nice to have, can fail with known issues
- **low** - Informational, doesn't block release

## Success Criteria

After implementation:

1. ✅ `/popkit:plugin test` executes all tests
2. ✅ All hook protocols validated programmatically
3. ✅ Agent routing logic verified
4. ✅ Skill format compliance checked
5. ✅ Plugin structure integrity confirmed
6. ✅ Documentation auto-sync working
7. ✅ Validation engine catches common issues
8. ✅ Safe auto-fixes applied correctly
9. ✅ Examples demonstrate all features
10. ✅ JSON output for CI integration

## Implementation Order

1. **Test definition format** - Foundation for everything
2. **pop-plugin-test skill** - Test runner
3. **Initial test definitions** - Hooks, agents, skills
4. **Test the tests** - Validate test infrastructure
5. **pop-validation-engine** - Integrity checks
6. **pop-doc-sync** - Documentation sync
7. **pop-auto-docs** - Documentation generation
8. **Examples** - Usage documentation
9. **Sandbox testing** - Advanced isolation (future)

## Utilities to Create

### popkit_shared.utils.test_runner

```python
class TestRunner:
    def __init__(self, verbose=False, fail_fast=False):
        self.verbose = verbose
        self.fail_fast = fail_fast

    def execute(self, test_definition):
        """Execute a test definition and return results"""
        pass

    def run_test_case(self, test_case):
        """Run a single test case"""
        pass

    def validate_assertions(self, result, assertions):
        """Validate assertions against result"""
        pass
```

### popkit_shared.utils.hook_validator

```python
def validate_hook_protocol(hook_path, input_data):
    """
    Validate hook follows JSON stdin/stdout protocol

    Returns:
        {
            "valid": bool,
            "exit_code": int,
            "stdout": str,
            "stderr": str,
            "duration_ms": int,
            "errors": List[str]
        }
    """
    pass
```

### popkit_shared.utils.agent_router_test

```python
def test_routing_keywords(config_path):
    """Test keyword-based routing"""
    pass

def test_routing_confidence(config_path):
    """Test confidence threshold filtering"""
    pass

def test_file_patterns(config_path):
    """Test file pattern matching"""
    pass
```

## Timeline

**Quality-focused approach** (not speed-focused):

1. Research & design: Create test definition format and infrastructure plan
2. Core implementation: Build test runner and initial test definitions
3. Validation: Test the testing infrastructure thoroughly
4. Enhancement: Add validation engine and doc sync
5. Documentation: Create comprehensive examples
6. Polish: Refine error messages, add edge case handling
7. Future: Sandbox testing when needed

## Notes

- All test infrastructure lives in `popkit-core` (foundation plugin)
- Tests validate the foundation architecture works correctly
- Sandbox testing (E2B) is optional and can be added later
- Focus on programmatic validation first, manual testing second
- Test definitions are data-driven (JSON) not code
- Skills execute tests, utilities do the heavy lifting
- All test results should be machine-readable (JSON) and human-readable (formatted text)
