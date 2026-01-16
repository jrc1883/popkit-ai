#!/usr/bin/env python3
"""
Simple test runner for PopKit plugin tests.
Executes all test definitions and reports results.
"""

import json
import sys
from pathlib import Path

# Add shared-py to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared-py"))

from popkit_shared.utils.test_runner import TestRunner


def main():
    """Run all plugin tests."""
    plugin_root = Path(__file__).parent
    tests_dir = plugin_root / "tests"

    # Parse arguments
    verbose = "--verbose" in sys.argv
    fail_fast = "--fail-fast" in sys.argv
    output_json = "--json" in sys.argv
    category = None

    # Check for category argument
    for arg in sys.argv[1:]:
        if not arg.startswith("--"):
            category = arg
            break

    print("PopKit Plugin Test Runner")
    print("=" * 60)
    print()

    # Load test files
    test_files = []
    if category:
        category_dir = tests_dir / category
        if category_dir.exists():
            test_files = list(category_dir.glob("*.json"))
            print(f"Running {category} tests...")
        else:
            print(f"Error: Category '{category}' not found")
            sys.exit(1)
    else:
        test_files = list(tests_dir.glob("**/*.json"))
        print("Running all tests...")

    print(f"Found {len(test_files)} test definition(s)")
    print()

    # Load test definitions
    test_defs = []
    for test_file in test_files:
        try:
            test_def = json.loads(test_file.read_text())
            test_def["_file"] = str(test_file)
            test_defs.append(test_def)
        except json.JSONDecodeError as e:
            print(f"Warning: Invalid JSON in {test_file}: {e}", file=sys.stderr)

    # Initialize test runner
    runner = TestRunner(plugin_root=plugin_root, verbose=verbose, fail_fast=fail_fast)

    # Execute tests
    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "duration_ms": 0,
        "categories": {},
        "failures": [],
    }

    for test_def in test_defs:
        cat = test_def.get("category", "unknown")

        # Initialize category
        if cat not in results["categories"]:
            results["categories"][cat] = {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "tests": [],
            }

        # Execute test
        try:
            test_result = runner.execute_test_definition(test_def)

            # Update totals
            results["total"] += test_result["total_cases"]
            results["passed"] += test_result["passed"]
            results["failed"] += test_result["failed"]
            results["duration_ms"] += test_result["duration_ms"]

            # Update category
            cat_results = results["categories"][cat]
            cat_results["total"] += test_result["total_cases"]
            cat_results["passed"] += test_result["passed"]
            cat_results["failed"] += test_result["failed"]
            cat_results["tests"].append(
                {
                    "name": test_def["name"],
                    "passed": test_result["passed"],
                    "failed": test_result["failed"],
                    "duration_ms": test_result["duration_ms"],
                }
            )

            # Collect failures
            if test_result["failed"] > 0:
                results["failures"].extend(test_result["failures"])

                if fail_fast:
                    break

        except Exception as e:
            print(
                f"Error executing {test_def.get('name', 'unknown')}: {e}",
                file=sys.stderr,
            )
            results["failed"] += 1

    # Output results
    if output_json:
        output = {
            "summary": {
                "total": results["total"],
                "passed": results["passed"],
                "failed": results["failed"],
                "pass_rate": (results["passed"] / results["total"] * 100)
                if results["total"] > 0
                else 0,
                "duration_ms": results["duration_ms"],
            },
            "categories": results["categories"],
            "failures": results["failures"],
        }
        print(json.dumps(output, indent=2))
    else:
        # Text output
        print()
        print("Results by Category:")
        print("-" * 60)

        for cat, cat_results in sorted(results["categories"].items()):
            status = "[PASS]" if cat_results["failed"] == 0 else "[FAIL]"
            print(
                f"{status} {cat}: {cat_results['passed']}/{cat_results['total']} passed"
            )

            if verbose or cat_results["failed"] > 0:
                for test in cat_results["tests"]:
                    test_status = "[ok]" if test["failed"] == 0 else "[x]"
                    print(
                        f"  {test_status} {test['name']} ({test['passed']}/{test['passed'] + test['failed']}, {test['duration_ms']}ms)"
                    )

        # Show failures
        if results["failures"]:
            print()
            print("Failures:")
            print("-" * 60)
            for failure in results["failures"]:
                print(f"[x] {failure.get('name', 'unknown')}")
                print(f"  Reason: {failure.get('reason', 'unknown')}")
                if "expected" in failure:
                    print(f"  Expected: {failure['expected']}")
                if "actual" in failure:
                    print(f"  Actual: {failure['actual']}")
                print()

        # Summary
        print()
        print("Summary:")
        print("=" * 60)
        print(f"Total: {results['total']}")
        print(
            f"Passed: {results['passed']} ({results['passed'] / results['total'] * 100:.1f}%)"
            if results["total"] > 0
            else "Passed: 0 (0%)"
        )
        print(
            f"Failed: {results['failed']} ({results['failed'] / results['total'] * 100:.1f}%)"
            if results["total"] > 0
            else "Failed: 0 (0%)"
        )
        print(f"Duration: {results['duration_ms'] / 1000:.2f}s")

    # Exit code
    sys.exit(0 if results["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
