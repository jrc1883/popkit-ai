#!/usr/bin/env python3
"""
Test the output-validator.py hook with sample agent outputs.
"""

import json
import subprocess
import sys
from pathlib import Path

# Test cases with different output styles
test_cases = [
    {
        "name": "debugging-report: Valid output with all required fields",
        "input": {
            "agent": "bug-whisperer",
            "output_style": "debugging-report",
            "output": """## Debugging Report: Memory Leak in UserDashboard

**Severity**: critical
**Status**: Root Cause Found

### Symptom
The application shows increasing memory usage over time, eventually leading to crashes after 2-3 hours of operation.

### Summary
Identified an event listener leak in the UserDashboard component. The component was not cleaning up listeners on unmount, causing memory to accumulate with each render cycle.
"""
        }
    },
    {
        "name": "security-audit-report: Valid output",
        "input": {
            "agent": "security-auditor",
            "output_style": "security-audit-report",
            "output": """## Security Audit Report: E-Commerce Platform

**Security Score**: 85
**Audit Date**: 2026-01-11
**Severity**: high
**Recommendation**: Implement rate limiting on API endpoints

### Summary
Overall security posture is good with a few areas needing attention. Found 3 high-severity vulnerabilities related to API authentication.
"""
        }
    },
    {
        "name": "agent-handoff: Valid output",
        "input": {
            "agent": "code-architect",
            "output_style": "agent-handoff",
            "output": """## Architecture Design Complete

**From**: code-architect
**To**: rapid-prototyper
**Task**: Implement user authentication feature
**Status**: Design approved
**Confidence**: 95

### Summary
Completed architecture analysis. Recommended approach uses JWT tokens with refresh mechanism. Ready for implementation by rapid-prototyper.
"""
        }
    },
    {
        "name": "debugging-report: Missing required field (severity)",
        "input": {
            "agent": "bug-whisperer",
            "output_style": "debugging-report",
            "output": """## Debugging Report: Performance Issue

**Status**: Under Investigation

### Symptom
Slow page load times observed.

### Summary
Still investigating the root cause.
"""
        }
    },
    {
        "name": "performance-report: Valid minimal output",
        "input": {
            "agent": "performance-optimizer",
            "output_style": "performance-report",
            "output": """## Performance Report

**Date**: 2026-01-11

### Summary
Optimized bundle size from 800KB to 400KB through code splitting and tree shaking.
"""
        }
    }
]

# Path to the output-validator hook
validator_path = Path("packages/popkit-core/hooks/output-validator.py")

print("Testing output-validator.py hook integration...\n")
print(f"Validator: {validator_path.absolute()}\n")
print("="*70)

for i, test_case in enumerate(test_cases, 1):
    print(f"\nTest {i}: {test_case['name']}")
    print("-"*70)

    try:
        # Run the validator with the test input
        result = subprocess.run(
            [sys.executable, str(validator_path)],
            input=json.dumps(test_case["input"]),
            capture_output=True,
            text=True,
            timeout=5
        )

        # Parse the output
        if result.stdout.strip():
            response = json.loads(result.stdout)
            print(f"Status: {response.get('status', 'unknown')}")

            if response.get('status') == 'valid':
                print(f"Confidence: {response.get('confidence')}%")
                print(f"Fields extracted: {', '.join(response.get('extracted_fields', []))}")
            elif response.get('status') == 'invalid':
                print(f"Confidence: {response.get('confidence')}%")
                print(f"Missing fields: {', '.join(response.get('missing_fields', []))}")
                print(f"Suggestion: {response.get('suggestion', 'N/A')}")
            elif response.get('status') == 'warning':
                print(f"Reason: {response.get('reason', 'N/A')}")

            print("Result: PASS")
        else:
            print("Result: FAIL (no output)")
            if result.stderr:
                print(f"Error: {result.stderr}")

    except subprocess.TimeoutExpired:
        print("Result: FAIL (timeout)")
    except json.JSONDecodeError as e:
        print(f"Result: FAIL (invalid JSON output)")
        print(f"Output: {result.stdout}")
    except Exception as e:
        print(f"Result: FAIL ({e})")

print("\n" + "="*70)
print("\nValidation testing complete!")
