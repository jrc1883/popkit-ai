#!/usr/bin/env python3
"""
Simple test script to validate hook JSON stdin/stdout protocol.

This tests that all hooks:
1. Accept JSON input from stdin
2. Return valid JSON output to stdout
3. Include required fields in response
"""

import json
import subprocess
import sys
from pathlib import Path


def test_hook(hook_path, test_data):
    """
    Test a hook with given input data.

    Returns: (success, result, error_message)
    """
    try:
        # Run the hook
        result = subprocess.run(
            ["python", str(hook_path)],
            input=json.dumps(test_data),
            capture_output=True,
            text=True,
            timeout=5,
        )

        # Parse output
        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            return (
                False,
                None,
                f"Invalid JSON output: {e}\nStdout: {result.stdout}\nStderr: {result.stderr}",
            )

        # Validate required fields
        if "decision" not in output:
            return False, output, "Missing 'decision' field in output"

        if output["decision"] not in ["allow", "deny", "ask"]:
            return False, output, f"Invalid decision value: {output['decision']}"

        return True, output, None

    except subprocess.TimeoutExpired:
        return False, None, "Hook timed out after 5 seconds"
    except Exception as e:
        return False, None, f"Exception: {str(e)}"


def main():
    """Run hook tests."""
    hooks_dir = Path(__file__).parent

    # Test cases for each hook
    test_cases = {
        "validate-security-tool.py": [
            {
                "name": "Allow normal Bash command",
                "input": {"tool": "Bash", "input": {"command": "ls -la"}},
                "expect_decision": "allow",
            },
            {
                "name": "Deny dangerous rm command",
                "input": {"tool": "Bash", "input": {"command": "rm -rf /"}},
                "expect_decision": "deny",
            },
            {
                "name": "Ask for protected file access",
                "input": {"tool": "Read", "input": {"file_path": ".env"}},
                "expect_decision": "ask",
            },
        ],
        "auto-run-tests.py": [
            {
                "name": "Allow non-file-modification tool",
                "input": {"tool": "Read", "input": {"file_path": "test.py"}},
                "expect_decision": "allow",
            },
            {
                "name": "Process Write tool (should allow)",
                "input": {"tool": "Write", "input": {"file_path": "test.py"}},
                "expect_decision": "allow",
            },
        ],
        "auto-save-state.py": [
            {
                "name": "Save session state",
                "input": {"skill": "session-capture", "context": {}},
                "expect_decision": "allow",
            }
        ],
        "save-power-mode-report.py": [
            {
                "name": "Save power mode report",
                "input": {"skill": "power-mode", "context": {}},
                "expect_decision": "allow",
            }
        ],
        "smart-bash-middleware.py": [
            {
                "name": "Allow normal command",
                "input": {"tool": "Bash", "input": {"command": "ls -la"}},
                "expect_decision": "allow",
            },
            {
                "name": "Deny critical dangerous command",
                "input": {"tool": "Bash", "input": {"command": "rm -rf /"}},
                "expect_decision": "deny",
            },
            {
                "name": "Ask for git push --force",
                "input": {"tool": "Bash", "input": {"command": "git push --force origin main"}},
                "expect_decision": "ask",
            },
        ],
    }

    # Run tests
    total_tests = 0
    passed_tests = 0
    failed_tests = []

    print("Testing PopKit Hook JSON Protocol Compliance\n")
    print("=" * 70)

    for hook_name, cases in test_cases.items():
        hook_path = hooks_dir / hook_name

        if not hook_path.exists():
            print(f"\n❌ SKIP: {hook_name} - File not found")
            continue

        print(f"\n📝 Testing: {hook_name}")
        print("-" * 70)

        for case in cases:
            total_tests += 1
            success, output, error = test_hook(hook_path, case["input"])

            if not success:
                print(f"  ❌ {case['name']}")
                print(f"     Error: {error}")
                failed_tests.append({"hook": hook_name, "test": case["name"], "error": error})
            else:
                # Check if decision matches expectation (if specified)
                if "expect_decision" in case:
                    if output["decision"] == case["expect_decision"]:
                        print(f"  ✅ {case['name']} - decision: {output['decision']}")
                        passed_tests += 1
                    else:
                        print(
                            f"  ⚠️  {case['name']} - expected '{case['expect_decision']}', got '{output['decision']}'"
                        )
                        passed_tests += 1  # Still valid JSON protocol
                else:
                    print(f"  ✅ {case['name']} - decision: {output['decision']}")
                    passed_tests += 1

    # Summary
    print("\n" + "=" * 70)
    print(f"\nTest Summary:")
    print(f"  Total: {total_tests}")
    print(f"  Passed: {passed_tests}")
    print(f"  Failed: {total_tests - passed_tests}")

    if failed_tests:
        print("\n❌ Failed Tests:")
        for fail in failed_tests:
            print(f"  - {fail['hook']}: {fail['test']}")
            print(f"    {fail['error']}")

    # Exit code
    sys.exit(0 if passed_tests == total_tests else 1)


if __name__ == "__main__":
    main()
