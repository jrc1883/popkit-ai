---
name: pop-plugin-test
description: Run comprehensive tests on plugin components - validates hooks, agents, skills, routing, and plugin structure. Executes test definitions and reports results in structured format.
---

# Plugin Test Runner

Execute test definitions to validate plugin integrity, hook protocols, agent routing, skill format compliance, and overall plugin structure.

## When to Use

- User runs `/popkit:plugin test`
- Post-implementation validation
- Pre-release verification
- Debugging plugin issues
- CI/CD integration

## Arguments

| Flag | Description |
|------|-------------|
| (category) | Test category: `hooks`, `agents`, `skills`, `routing`, `structure`, `sandbox` (default: all) |
| `--verbose` | Show detailed test output including passing tests |
| `--fail-fast` | Stop on first test failure |
| `--json` | Output results as JSON for CI integration |
| `--full` | Include sandbox tests (requires E2B, future) |
| `--test <id>` | Run specific test by ID |

## Process

### Step 1: Parse Arguments and Load Tests

```python
import json
import sys
from pathlib import Path

# Get plugin root from environment
plugin_root = Path(os.environ.get('CLAUDE_PLUGIN_ROOT', '.'))
tests_dir = plugin_root / "tests"

# Parse arguments
args = parse_args(sys.argv[1:])  # category, verbose, fail_fast, json, test_id

# Load test definitions
test_files = []
if args.test_id:
    # Find specific test
    test_files = list(tests_dir.glob(f"**/*{args.test_id}*.json"))
elif args.category:
    # Load category tests
    category_dir = tests_dir / args.category
    if category_dir.exists():
        test_files = list(category_dir.glob("*.json"))
    else:
        print(f"Error: Category '{args.category}' not found", file=sys.stderr)
        sys.exit(1)
else:
    # Load all tests
    test_files = list(tests_dir.glob("**/*.json"))

# Parse test definitions
test_defs = []
for test_file in test_files:
    try:
        test_def = json.loads(test_file.read_text())
        test_def['_file'] = str(test_file)
        test_defs.append(test_def)
    except json.JSONDecodeError as e:
        print(f"Warning: Invalid JSON in {test_file}: {e}", file=sys.stderr)

print(f"Loaded {len(test_defs)} test definitions from {len(test_files)} files")
```

### Step 2: Execute Tests

```python
from popkit_shared.utils.test_runner import TestRunner
from popkit_shared.utils.hook_validator import HookValidator
from popkit_shared.utils.agent_router_test import AgentRouterTest
from popkit_shared.utils.skill_validator import SkillValidator
from popkit_shared.utils.plugin_validator import PluginValidator

# Initialize test runner
runner = TestRunner(
    plugin_root=plugin_root,
    verbose=args.verbose,
    fail_fast=args.fail_fast
)

# Execute tests by category
results = {
    'total': 0,
    'passed': 0,
    'failed': 0,
    'skipped': 0,
    'duration_ms': 0,
    'categories': {},
    'failures': []
}

for test_def in test_defs:
    category = test_def['category']

    # Initialize category results
    if category not in results['categories']:
        results['categories'][category] = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'tests': []
        }

    # Execute test definition
    try:
        test_result = runner.execute_test_definition(test_def)

        # Update counters
        results['total'] += test_result['total_cases']
        results['passed'] += test_result['passed']
        results['failed'] += test_result['failed']
        results['duration_ms'] += test_result['duration_ms']

        # Update category
        cat_results = results['categories'][category]
        cat_results['total'] += test_result['total_cases']
        cat_results['passed'] += test_result['passed']
        cat_results['failed'] += test_result['failed']
        cat_results['tests'].append({
            'name': test_def['name'],
            'passed': test_result['passed'],
            'failed': test_result['failed'],
            'duration_ms': test_result['duration_ms']
        })

        # Collect failures
        if test_result['failed'] > 0:
            results['failures'].extend(test_result['failures'])

            # Fail fast if requested
            if args.fail_fast:
                break

    except Exception as e:
        print(f"Error executing {test_def['name']}: {e}", file=sys.stderr)
        results['failed'] += 1
        results['failures'].append({
            'test_id': test_def.get('test_id', 'unknown'),
            'name': test_def.get('name', 'unknown'),
            'error': str(e)
        })
```

### Step 3: Generate Report

#### Text Output (default)

```python
if not args.json:
    print("\\nPopKit Plugin Test Results")
    print("=" * 60)
    print()

    # Category breakdown
    for category, cat_results in sorted(results['categories'].items()):
        pass_rate = (cat_results['passed'] / cat_results['total'] * 100) if cat_results['total'] > 0 else 0
        status = "✓" if cat_results['failed'] == 0 else "✗"

        print(f"{status} Category: {category}")

        for test in cat_results['tests']:
            test_status = "✓" if test['failed'] == 0 else "✗"
            if args.verbose or test['failed'] > 0:
                print(f"  {test_status} {test['name']} ({test['passed']}/{test['passed'] + test['failed']} cases, {test['duration_ms']}ms)")

        if cat_results['failed'] > 0:
            print(f"  {cat_results['failed']} failures in {category}")
        print()

    # Failures detail
    if results['failures']:
        print("Failed Tests:")
        print("-" * 60)
        for failure in results['failures']:
            print(f"\\n✗ {failure.get('test_id', 'unknown')}")
            print(f"  Test: {failure.get('name', 'unknown')}")
            print(f"  Case: {failure.get('case_id', 'unknown')}")
            print(f"  Reason: {failure.get('reason', 'unknown')}")
            if 'expected' in failure:
                print(f"  Expected: {failure['expected']}")
            if 'actual' in failure:
                print(f"  Actual: {failure['actual']}")

    # Summary
    print("\\nSummary:")
    print("-" * 60)
    print(f"Total Tests: {results['total']}")
    print(f"Passed: {results['passed']} ({results['passed']/results['total']*100:.1f}%)")
    print(f"Failed: {results['failed']} ({results['failed']/results['total']*100:.1f}%)")
    print(f"Duration: {results['duration_ms']/1000:.2f}s")

    # Exit code
    sys.exit(0 if results['failed'] == 0 else 1)
```

#### JSON Output (--json)

```python
if args.json:
    output = {
        'summary': {
            'total': results['total'],
            'passed': results['passed'],
            'failed': results['failed'],
            'pass_rate': (results['passed'] / results['total'] * 100) if results['total'] > 0 else 0,
            'duration_ms': results['duration_ms']
        },
        'categories': results['categories'],
        'failures': results['failures'],
        'timestamp': datetime.now().isoformat()
    }

    print(json.dumps(output, indent=2))
    sys.exit(0 if results['failed'] == 0 else 1)
```

## Test Execution

### Hook Tests

```python
# For hook protocol tests
from popkit_shared.utils.hook_validator import validate_hook_protocol

hook_result = validate_hook_protocol(
    hook_path=plugin_root / test_def['hook_file'],
    input_data=test_case['input']
)

# Validate assertions
for assertion in test_case['assertions']:
    if assertion['type'] == 'exit_code':
        assert hook_result['exit_code'] == assertion['expected']
    elif assertion['type'] == 'json_valid':
        assert hook_result['json_valid']
    elif assertion['type'] == 'duration':
        assert hook_result['duration_ms'] < assertion['max_ms']
```

### Agent Routing Tests

```python
# For agent routing tests
from popkit_shared.utils.agent_router_test import test_keyword_routing

router_result = test_keyword_routing(
    config_path=plugin_root / "agents/config.json",
    user_query=test_case['input']['user_query'],
    expected_agents=test_case['expected_agents']
)

# Validate agent activation
for assertion in test_case['assertions']:
    if assertion['type'] == 'agent_activated':
        assert assertion['agent'] in router_result['activated_agents']
```

### Skill Format Tests

```python
# For skill format tests
from popkit_shared.utils.skill_validator import validate_skill_format

skill_files = list((plugin_root / "skills").glob("*/SKILL.md"))

for skill_file in skill_files:
    validation = validate_skill_format(skill_file)

    # Check assertions
    for assertion in test_case['assertions']:
        if assertion['type'] == 'yaml_frontmatter_exists':
            assert validation['has_frontmatter']
        elif assertion['type'] == 'has_frontmatter_field':
            assert assertion['field'] in validation['frontmatter']
```

### Plugin Structure Tests

```python
# For structure integrity tests
from popkit_shared.utils.plugin_validator import validate_plugin_structure

structure_result = validate_plugin_structure(plugin_root)

# Check required files
for assertion in test_case['assertions']:
    if assertion['type'] == 'file_exists':
        file_path = plugin_root / assertion['path']
        assert file_path.exists(), f"Required file missing: {assertion['path']}"
    elif assertion['type'] == 'json_valid':
        # Validate JSON files
        content = (plugin_root / test_case['file']).read_text()
        json.loads(content)  # Will raise if invalid
```

## Output Examples

### Verbose Mode (--verbose)

```
PopKit Plugin Test Results
============================================================

✓ Category: hooks
  ✓ Pre-Tool-Use Hook JSON Protocol (5/5 cases, 234ms)
  ✓ Post-Tool-Use Hook JSON Protocol (5/5 cases, 189ms)
  ✓ Session-Start Hook Protocol (4/4 cases, 1234ms)

✓ Category: agents
  ✓ Agent Routing - Keyword Matching (6/6 cases, 45ms)
  ✓ Agent Routing - Confidence Threshold (4/4 cases, 32ms)

✗ Category: skills
  ✓ Skill Format Validation (4/5 cases, 123ms)
    ✗ Case: no-hardcoded-paths
      Found hardcoded path in: skills/example/SKILL.md

Summary:
------------------------------------------------------------
Total Tests: 24
Passed: 23 (95.8%)
Failed: 1 (4.2%)
Duration: 1.86s
```

### JSON Mode (--json)

```json
{
  "summary": {
    "total": 24,
    "passed": 23,
    "failed": 1,
    "pass_rate": 95.8,
    "duration_ms": 1857
  },
  "categories": {
    "hooks": {
      "total": 14,
      "passed": 14,
      "failed": 0
    },
    "agents": {
      "total": 10,
      "passed": 10,
      "failed": 0
    }
  },
  "failures": [
    {
      "test_id": "skill-format-validation",
      "case_id": "no-hardcoded-paths",
      "reason": "Found hardcoded path",
      "file": "skills/example/SKILL.md",
      "path": "/Users/john/project"
    }
  ],
  "timestamp": "2025-12-22T15:30:00Z"
}
```

## Integration

### Command Integration

Invoked by `/popkit:plugin test [category] [options]`

```bash
# Run all tests
/popkit:plugin test

# Run specific category
/popkit:plugin test hooks

# Verbose mode
/popkit:plugin test --verbose

# JSON for CI
/popkit:plugin test --json

# Fail fast
/popkit:plugin test --fail-fast

# Specific test
/popkit:plugin test --test hook-pre-tool-use
```

### Dependencies

**Required utilities** (in `popkit_shared.utils`):
- `test_runner.py` - Core test execution engine
- `hook_validator.py` - Hook protocol validation
- `agent_router_test.py` - Agent routing validation
- `skill_validator.py` - Skill format validation
- `plugin_validator.py` - Plugin structure validation

**Test definitions**: `tests/` directory with JSON files

### CI/CD Integration

```yaml
# .github/workflows/test-plugin.yml
- name: Test PopKit Plugin
  run: |
    /popkit:plugin test --json > test-results.json
    exit_code=$?

    # Upload results
    cat test-results.json

    # Fail if tests failed
    exit $exit_code
```

## Notes

- Test definitions are data-driven (JSON format)
- All validators are in `popkit_shared.utils` for reusability
- Supports both human-readable and machine-readable output
- Can be integrated into CI/CD pipelines
- Fail-fast mode useful for development
- JSON mode useful for automation
- Verbose mode helpful for debugging
- Test categories can be run independently
