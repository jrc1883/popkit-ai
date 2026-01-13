# Plugin Testing Examples

Examples of using `/popkit:plugin test` for comprehensive plugin validation.

## Basic Testing

### Run All Tests

```
/popkit:plugin test
```

Output:

```
Loaded 35 test definitions from 5 files

PopKit Plugin Test Results
============================================================

✓ Category: hooks
  ✓ Pre-Tool-Use Hook JSON Protocol (5/5 cases, 234ms)
  ✓ Post-Tool-Use Hook JSON Protocol (5/5 cases, 189ms)
  ✓ Session-Start Hook Protocol (4/4 cases, 1234ms)

✓ Category: agents
  ✓ Agent Routing - Keyword Matching (6/6 cases, 45ms)
  ✓ Agent Routing - Confidence Threshold (4/4 cases, 32ms)

✓ Category: skills
  ✓ Skill Format Validation (5/5 cases, 123ms)

✓ Category: structure
  ✓ Plugin Structure Integrity (7/7 cases, 89ms)

Summary:
------------------------------------------------------------
Total Tests: 31
Passed: 31 (100.0%)
Failed: 0 (0.0%)
Duration: 1.86s
```

## Category-Specific Testing

### Test Only Hooks

```
/popkit:plugin test hooks
```

Output:

```
Loaded 3 test definitions from 1 file

PopKit Plugin Test Results
============================================================

✓ Category: hooks
  ✓ Pre-Tool-Use Hook JSON Protocol (5/5 cases, 234ms)
  ✓ Post-Tool-Use Hook JSON Protocol (5/5 cases, 189ms)
  ✓ Session-Start Hook Protocol (4/4 cases, 1234ms)

Summary:
------------------------------------------------------------
Total Tests: 14
Passed: 14 (100.0%)
Failed: 0 (0.0%)
Duration: 1.66s
```

### Test Only Agent Routing

```
/popkit:plugin test agents
```

Output:

```
Loaded 2 test definitions from 1 file

PopKit Plugin Test Results
============================================================

✓ Category: agents
  ✓ Agent Routing - Keyword Matching (6/6 cases, 45ms)
  ✓ Agent Routing - Confidence Threshold (4/4 cases, 32ms)

Summary:
------------------------------------------------------------
Total Tests: 10
Passed: 10 (100.0%)
Failed: 0 (0.0%)
Duration: 0.08s
```

### Test Only Skills

```
/popkit:plugin test skills
```

### Test Only Plugin Structure

```
/popkit:plugin test structure
```

## Verbose Mode

Show detailed output including passing tests:

```
/popkit:plugin test hooks --verbose
```

Output:

```
Executing: Pre-Tool-Use Hook JSON Protocol
Category: hooks
Test cases: 5

  ✓ Valid Bash tool produces valid JSON output
    - Exit code: 0 ✓
    - JSON valid: true ✓
    - Duration: 234ms ✓

  ✓ Read tool input validation
    - Exit code: 0 ✓
    - JSON valid: true ✓

  ✓ Task tool triggers agent orchestration
    - Exit code: 0 ✓
    - JSON valid: true ✓

  ✓ Write tool safety checks
    - Exit code: 0 ✓
    - JSON valid: true ✓

  ✓ Hook handles invalid JSON input gracefully
    - Exit code: 1 ✓ (expected error)

Summary:
------------------------------------------------------------
Total Tests: 5
Passed: 5 (100.0%)
Failed: 0 (0.0%)
Duration: 0.23s
```

## Handling Failures

### Example: Test Failure

```
/popkit:plugin test skills
```

Output:

```
PopKit Plugin Test Results
============================================================

✗ Category: skills
  ✓ Skill Format Validation (4/5 cases, 123ms)
  ✗ Case: no-hardcoded-paths
    Found hardcoded path in: skills/example/SKILL.md

Failed Tests:
------------------------------------------------------------

✗ skill-format-validation
  Test: Skill Format Validation
  Case: no-hardcoded-paths
  Reason: Found hardcoded path
  File: skills/example/SKILL.md
  Path: /Users/john/project

Summary:
------------------------------------------------------------
Total Tests: 5
Passed: 4 (80.0%)
Failed: 1 (20.0%)
Duration: 0.12s
```

### Fail-Fast Mode

Stop on first failure:

```
/popkit:plugin test --fail-fast
```

Output:

```
PopKit Plugin Test Results
============================================================

✓ Category: hooks
  ✓ Pre-Tool-Use Hook JSON Protocol (5/5 cases)

✗ Category: agents
  ✗ Agent Routing - Keyword Matching (5/6 cases)
    Failed: bug-keyword-routing
    Reason: Agent not activated: bug-whisperer

Stopped due to --fail-fast

Summary:
------------------------------------------------------------
Total Tests: 11
Passed: 10 (90.9%)
Failed: 1 (9.1%)
Duration: 0.54s
```

## JSON Output for CI

```
/popkit:plugin test --json
```

Output:

```json
{
  "summary": {
    "total": 31,
    "passed": 31,
    "failed": 0,
    "pass_rate": 100.0,
    "duration_ms": 1857
  },
  "categories": {
    "hooks": {
      "total": 14,
      "passed": 14,
      "failed": 0,
      "tests": [
        {
          "name": "Pre-Tool-Use Hook JSON Protocol",
          "passed": 5,
          "failed": 0,
          "duration_ms": 234
        }
      ]
    },
    "agents": {
      "total": 10,
      "passed": 10,
      "failed": 0
    },
    "skills": {
      "total": 5,
      "passed": 5,
      "failed": 0
    },
    "structure": {
      "total": 7,
      "passed": 7,
      "failed": 0
    }
  },
  "failures": [],
  "timestamp": "2025-12-22T15:30:00Z"
}
```

## Specific Test Execution

Run a specific test by ID:

```
/popkit:plugin test --test hook-pre-tool-use
```

Output:

```
Loaded 1 test definition

PopKit Plugin Test Results
============================================================

✓ Pre-Tool-Use Hook JSON Protocol (5/5 cases, 234ms)

Summary:
------------------------------------------------------------
Total Tests: 5
Passed: 5 (100.0%)
Failed: 0 (0.0%)
Duration: 0.23s
```

## CI/CD Integration

### GitHub Actions Example

```.github/workflows/test-plugin.yml
name: Test PopKit Plugin

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Install PopKit
        run: |
          /plugin install popkit@popkit-claude

      - name: Run Plugin Tests
        run: |
          /popkit:plugin test --json > test-results.json
          exit_code=$?

      - name: Upload Test Results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test-results.json

      - name: Fail if Tests Failed
        run: exit $exit_code
```

### Pre-Commit Hook Example

```.git/hooks/pre-commit
#!/bin/bash

echo "Running PopKit plugin tests..."

/popkit:plugin test --fail-fast

if [ $? -ne 0 ]; then
  echo "Tests failed! Commit aborted."
  exit 1
fi

echo "All tests passed!"
```

## Debugging Test Failures

### Step 1: Run Verbose Mode

```
/popkit:plugin test skills --verbose
```

### Step 2: Inspect Test Definition

Check the test definition JSON:

```bash
cat packages/popkit-core/tests/skills/test-skill-format.json
```

### Step 3: Fix Issue

Edit the problematic file based on the error message.

### Step 4: Re-run Test

```
/popkit:plugin test skills
```

## Writing Custom Tests

### Create Test Definition

```json
{
  "test_id": "my-custom-test",
  "category": "skills",
  "name": "My Custom Validation",
  "description": "Custom validation for project-specific requirements",
  "severity": "medium",
  "test_cases": [
    {
      "case_id": "custom-check",
      "name": "Check custom requirement",
      "scan_pattern": "skills/*/SKILL.md",
      "assertions": [
        {
          "type": "contains",
          "field": "content",
          "expected": "Integration",
          "description": "All skills must have Integration section"
        }
      ]
    }
  ]
}
```

Save to: `packages/popkit-core/tests/skills/test-custom.json`

### Run Custom Test

```
/popkit:plugin test skills
```

The custom test will be automatically included.

## Best Practices

### 1. Run Tests Before Committing

Always run tests before committing changes:

```bash
/popkit:plugin test
```

### 2. Use Category-Specific Tests During Development

When working on hooks:

```bash
/popkit:plugin test hooks
```

When working on agents:

```bash
/popkit:plugin test agents
```

### 3. Use Verbose Mode for Debugging

```bash
/popkit:plugin test --verbose
```

### 4. Use JSON Output for Automation

```bash
/popkit:plugin test --json > results.json
```

### 5. Use Fail-Fast for Quick Feedback

```bash
/popkit:plugin test --fail-fast
```

## Interpreting Results

### Exit Codes

- `0`: All tests passed
- `1`: One or more tests failed

### Pass Rate Thresholds

- `100%`: Perfect - ready for release
- `95-99%`: Excellent - minor issues
- `90-94%`: Good - review failures
- `< 90%`: Poor - significant issues

### Common Failure Patterns

**Missing Frontmatter**:

```
✗ skill-format-validation
  Reason: Frontmatter missing required field: description
  File: skills/example/SKILL.md
```

Fix: Add `description` to frontmatter

**Hardcoded Paths**:

```
✗ skill-format-validation
  Reason: Found hardcoded user path
  File: skills/example/SKILL.md
  Path: /Users/john/project
```

Fix: Replace with relative paths or environment variables

**Orphaned Agents**:

```
✗ agent-definitions-exist
  Reason: Agent definition missing for: new-feature-agent
```

Fix: Create `agents/tier-2-on-demand/new-feature-agent.md`

## Performance Considerations

### Test Execution Time

- **Hooks**: ~2s (includes subprocess execution)
- **Agents**: ~100ms (config parsing only)
- **Skills**: ~150ms (file scanning and parsing)
- **Structure**: ~100ms (directory scanning)
- **Total**: ~2.5s for full suite

### Optimization Tips

1. Use category filters for faster iteration
2. Use `--fail-fast` during development
3. Use `--test <id>` for specific test debugging
4. Run full suite only before commits/releases

## Troubleshooting

### "Hook file not found"

Check that hook files exist and hooks.json references are correct.

### "No skill files found"

Verify skills directory exists and contains SKILL.md files.

### "Agent not activated"

Check agents/config.json routing keywords match test expectations.

### "JSON decode error"

Verify test definition files are valid JSON.
