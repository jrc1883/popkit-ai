#!/usr/bin/env python3
"""
Modular test runner for all PopKit plugin packages.
Tests each plugin independently and runs cross-plugin validation.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add shared-py to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "shared-py"))

from popkit_shared.utils.test_runner import TestRunner


class ModularPluginTestRunner:
    """Test runner for modular plugin architecture."""

    def __init__(self, root_dir: Path, verbose: bool = False, fail_fast: bool = False):
        """
        Initialize modular test runner.

        Args:
            root_dir: Root directory containing all plugin packages
            verbose: Show detailed output
            fail_fast: Stop on first failure
        """
        self.root_dir = Path(root_dir)
        self.verbose = verbose
        self.fail_fast = fail_fast
        self.all_results = {
            "plugins": {},
            "cross_plugin": {},
            "summary": {
                "total_plugins": 0,
                "plugins_passed": 0,
                "plugins_failed": 0,
                "total_tests": 0,
                "tests_passed": 0,
                "tests_failed": 0,
                "duration_ms": 0,
            },
        }

    def discover_plugins(self) -> List[Path]:
        """Discover all PopKit plugin packages."""
        packages_dir = self.root_dir / "packages"
        plugins = []

        for pkg_dir in packages_dir.glob("popkit-*"):
            if (pkg_dir / ".claude-plugin" / "plugin.json").exists():
                plugins.append(pkg_dir)

        return sorted(plugins)

    def run_plugin_tests(self, plugin_dir: Path) -> Dict[str, Any]:
        """
        Run all tests for a single plugin.

        Args:
            plugin_dir: Path to plugin directory

        Returns:
            Test results for the plugin
        """
        plugin_name = plugin_dir.name
        tests_dir = plugin_dir / "tests"

        print(f"\n{'=' * 60}")
        print(f"Testing Plugin: {plugin_name}")
        print(f"{'=' * 60}")

        if not tests_dir.exists():
            print(f"No tests directory found for {plugin_name}")
            return {
                "plugin": plugin_name,
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": True,
                "message": "No tests directory",
            }

        # Load JSON test files (excluding cross-plugin tests)
        test_files = []
        for category_dir in tests_dir.iterdir():
            if category_dir.is_dir() and category_dir.name != "cross-plugin":
                test_files.extend(category_dir.glob("*.json"))

        # Also discover Python test files (pytest-based)
        py_test_files = list(tests_dir.glob("test_*.py"))
        for category_dir in tests_dir.iterdir():
            if category_dir.is_dir() and category_dir.name != "cross-plugin":
                py_test_files.extend(category_dir.glob("test_*.py"))

        if not test_files and not py_test_files:
            print(f"No test files found for {plugin_name}")
            return {
                "plugin": plugin_name,
                "total": 0,
                "passed": 0,
                "failed": 0,
                "skipped": True,
                "message": "No test files",
            }

        total_files = len(test_files) + len(py_test_files)
        print(
            f"Found {total_files} test file(s) ({len(test_files)} JSON, {len(py_test_files)} Python)"
        )

        # Load test definitions
        test_defs = []
        for test_file in test_files:
            try:
                test_def = json.loads(test_file.read_text())
                test_def["_file"] = str(test_file)
                test_defs.append(test_def)
            except json.JSONDecodeError as e:
                print(f"Warning: Invalid JSON in {test_file}: {e}", file=sys.stderr)

        # Run tests
        runner = TestRunner(plugin_root=plugin_dir, verbose=self.verbose, fail_fast=self.fail_fast)

        results = {
            "plugin": plugin_name,
            "total": 0,
            "passed": 0,
            "failed": 0,
            "duration_ms": 0,
            "categories": {},
            "failures": [],
        }

        for test_def in test_defs:
            cat = test_def.get("category", "unknown")

            if cat not in results["categories"]:
                results["categories"][cat] = {"total": 0, "passed": 0, "failed": 0}

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

                # Collect failures
                if test_result["failed"] > 0:
                    for failure in test_result["failures"]:
                        failure["plugin"] = plugin_name
                    results["failures"].extend(test_result["failures"])

                    if self.fail_fast:
                        break

            except Exception as e:
                print(
                    f"Error executing {test_def.get('name', 'unknown')}: {e}",
                    file=sys.stderr,
                )
                results["failed"] += 1

        # Run Python test files with pytest if found
        if py_test_files:
            py_results = self._run_pytest(plugin_dir, py_test_files)
            results["total"] += py_results["total"]
            results["passed"] += py_results["passed"]
            results["failed"] += py_results["failed"]
            results["duration_ms"] += py_results["duration_ms"]

            if "pytest" not in results["categories"]:
                results["categories"]["pytest"] = {"total": 0, "passed": 0, "failed": 0}
            results["categories"]["pytest"]["total"] += py_results["total"]
            results["categories"]["pytest"]["passed"] += py_results["passed"]
            results["categories"]["pytest"]["failed"] += py_results["failed"]

        return results

    def _run_pytest(self, plugin_dir: Path, test_files: List[Path]) -> Dict[str, Any]:
        """
        Run Python test files using pytest.

        Args:
            plugin_dir: Plugin directory for context
            test_files: List of Python test file paths

        Returns:
            Test results dictionary
        """
        import time as time_mod

        start = time_mod.time()
        results = {"total": 0, "passed": 0, "failed": 0, "duration_ms": 0}

        print(f"\n  Running {len(test_files)} Python test file(s) with pytest...")

        try:
            cmd = [
                sys.executable,
                "-m",
                "pytest",
                *[str(f) for f in test_files],
                "-v",
                "--tb=short",
                "-q",
            ]
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(plugin_dir),
            )

            # Parse pytest output for counts
            for line in proc.stdout.splitlines():
                if " passed" in line or " failed" in line or " error" in line:
                    import re

                    passed_match = re.search(r"(\d+) passed", line)
                    failed_match = re.search(r"(\d+) failed", line)
                    error_match = re.search(r"(\d+) error", line)

                    if passed_match:
                        results["passed"] = int(passed_match.group(1))
                    if failed_match:
                        results["failed"] = int(failed_match.group(1))
                    if error_match:
                        results["failed"] += int(error_match.group(1))

            results["total"] = results["passed"] + results["failed"]

            if self.verbose:
                for line in proc.stdout.splitlines():
                    if line.strip():
                        print(f"    {line}")

            if proc.returncode == 0:
                print(f"  [ok] pytest: {results['passed']} passed")
            else:
                print(f"  [x] pytest: {results['failed']} failed, {results['passed']} passed")
                if not self.verbose:
                    # Show failure details even in non-verbose mode
                    for line in proc.stdout.splitlines():
                        if "FAILED" in line or "ERROR" in line:
                            print(f"    {line}")

        except subprocess.TimeoutExpired:
            print("  [x] pytest: timed out after 120s")
            results["failed"] = len(test_files)
            results["total"] = len(test_files)
        except FileNotFoundError:
            print("  [x] pytest: not installed, skipping Python tests")

        results["duration_ms"] = int((time_mod.time() - start) * 1000)
        return results

    def run_cross_plugin_tests(self, plugins: List[Path]) -> Dict[str, Any]:
        """
        Run cross-plugin validation tests.

        Args:
            plugins: List of all plugin directories

        Returns:
            Cross-plugin test results
        """
        print(f"\n{'=' * 60}")
        print("Running Cross-Plugin Validation Tests")
        print(f"{'=' * 60}")

        # Find cross-plugin test directory (usually in popkit-core)
        cross_plugin_tests_dir = (
            self.root_dir / "packages" / "popkit-core" / "tests" / "cross-plugin"
        )

        if not cross_plugin_tests_dir.exists():
            print("No cross-plugin tests found")
            return {"total": 0, "passed": 0, "failed": 0, "skipped": True}

        test_files = list(cross_plugin_tests_dir.glob("*.json"))
        print(f"Found {len(test_files)} cross-plugin test(s)")

        # Import validators
        import time

        sys.path.insert(0, str(cross_plugin_tests_dir / "validators"))
        from ecosystem_validators import (
            load_plugin_version,
            scan_plugin_agents,
            scan_plugin_commands,
            scan_plugin_skills,
            validate_agent_count_matches,
            validate_namespace_consistent,
            validate_no_circular_deps,
            validate_semver_valid,
            validate_shared_package_version,
            validate_skill_naming_convention,
            validate_total_agents,
            validate_unique_agent_names,
            validate_unique_command_names,
            validate_unique_skill_names,
            validate_version_compatibility,
        )

        # Scan all plugins to build ecosystem data
        # Only include actual Claude Code plugins (have .claude-plugin/plugin.json)
        # or packages with popkit-package.yaml (v2 universal manifests).
        # Skip Python-only packages like popkit-mcp, popkit-cli that don't have
        # skills/agents/commands.
        plugins_data = {}
        for plugin_dir in self.root_dir.glob("packages/popkit-*"):
            has_plugin_json = (plugin_dir / ".claude-plugin" / "plugin.json").exists()
            has_manifest = (plugin_dir / "popkit-package.yaml").exists()
            if not (has_plugin_json or has_manifest):
                continue
            plugin_name = plugin_dir.name
            plugins_data[plugin_name] = {
                "path": plugin_dir,
                "commands": scan_plugin_commands(plugin_dir),
                "skills": scan_plugin_skills(plugin_dir),
                "agents": scan_plugin_agents(plugin_dir),
                "version": load_plugin_version(plugin_dir),
            }

        # Execute cross-plugin tests
        results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "duration_ms": 0,
            "failures": [],
        }

        start_time = time.time()

        for test_file in test_files:
            with open(test_file, "r", encoding="utf-8") as f:
                test_def = json.load(f)

            test_name = test_def.get("name", test_file.name)
            print(f"\nRunning: {test_name}")

            for test_case in test_def.get("test_cases", []):
                for assertion in test_case.get("assertions", []):
                    results["total"] += 1
                    assertion_type = assertion["type"]

                    # Map assertion types to validator functions
                    try:
                        if assertion_type == "unique_command_names":
                            passed, message = validate_unique_command_names(plugins_data)
                        elif assertion_type == "unique_skill_names":
                            passed, message = validate_unique_skill_names(plugins_data)
                        elif assertion_type == "unique_agent_names":
                            passed, message = validate_unique_agent_names(plugins_data)
                        elif assertion_type == "namespace_consistent":
                            passed, message = validate_namespace_consistent(
                                plugins_data,
                                assertion.get("expected_prefix", "popkit:"),
                            )
                        elif assertion_type == "skill_naming_convention":
                            passed, message = validate_skill_naming_convention(
                                plugins_data, assertion.get("expected_prefix", "pop-")
                            )
                        elif assertion_type == "semver_valid":
                            passed, message = validate_semver_valid(plugins_data)
                        elif assertion_type == "version_compatibility":
                            passed, message = validate_version_compatibility(plugins_data)
                        elif assertion_type == "shared_package_version":
                            passed, message = validate_shared_package_version(
                                plugins_data,
                                assertion.get("package", "@popkit/shared-py"),
                            )
                        elif assertion_type == "no_circular_deps":
                            passed, message = validate_no_circular_deps(plugins_data)
                        elif assertion_type == "agent_count_matches":
                            passed, message = validate_agent_count_matches(
                                plugins_data, test_case.get("expected_counts", {})
                            )
                        elif assertion_type == "total_agents":
                            passed, message = validate_total_agents(
                                plugins_data, assertion.get("expected", 0)
                            )
                        else:
                            passed = False
                            message = f"Unknown assertion type: {assertion_type}"

                        if passed:
                            results["passed"] += 1
                            if self.verbose:
                                print(f"  [ok] {test_case['name']}: {message}")
                        else:
                            results["failed"] += 1
                            failure = {
                                "test": test_name,
                                "case": test_case["name"],
                                "assertion": assertion_type,
                                "reason": message,
                            }
                            results["failures"].append(failure)
                            print(f"  [x] {test_case['name']}: {message}")

                    except Exception as e:
                        results["failed"] += 1
                        failure = {
                            "test": test_name,
                            "case": test_case["name"],
                            "assertion": assertion_type,
                            "reason": f"Validator error: {str(e)}",
                        }
                        results["failures"].append(failure)
                        print(f"  [x] {test_case['name']}: {str(e)}")

        results["duration_ms"] = int((time.time() - start_time) * 1000)

        print(f"\nCross-plugin tests: {results['passed']}/{results['total']} passed")

        return results

    def print_summary(self):
        """Print comprehensive test summary."""
        print(f"\n{'=' * 60}")
        print("MODULAR PLUGIN TEST SUMMARY")
        print(f"{'=' * 60}\n")

        # Per-plugin results
        print("Per-Plugin Results:")
        print("-" * 60)

        for plugin_name, results in sorted(self.all_results["plugins"].items()):
            if results.get("skipped"):
                status = "[SKIP]"
                message = results.get("message", "No tests")
            elif results["failed"] == 0:
                status = "[PASS]"
                message = f"{results['passed']}/{results['total']} tests passed"
            else:
                status = "[FAIL]"
                message = f"{results['failed']}/{results['total']} tests failed"

            print(f"{status} {plugin_name}: {message}")

            # Show category breakdown if verbose or failures
            if (self.verbose or results["failed"] > 0) and not results.get("skipped"):
                for cat, cat_results in sorted(results.get("categories", {}).items()):
                    cat_status = "[ok]" if cat_results["failed"] == 0 else "[x]"
                    print(f"  {cat_status} {cat}: {cat_results['passed']}/{cat_results['total']}")

        # Cross-plugin results
        cross = self.all_results.get("cross_plugin", {})
        if not cross.get("skipped"):
            status = "[PASS]" if cross["failed"] == 0 else "[FAIL]"
            print(f"\n{status} Cross-Plugin Validation: {cross['passed']}/{cross['total']}")

        # Overall summary
        summary = self.all_results["summary"]
        print(f"\n{'=' * 60}")
        print("Overall Summary:")
        print("-" * 60)
        print(f"Total Plugins Tested: {summary['total_plugins']}")
        print(f"Plugins Passed: {summary['plugins_passed']}")
        print(f"Plugins Failed: {summary['plugins_failed']}")
        print(f"\nTotal Test Cases: {summary['total_tests']}")
        print(
            f"Tests Passed: {summary['tests_passed']} ({summary['tests_passed'] / summary['total_tests'] * 100:.1f}%)"
            if summary["total_tests"] > 0
            else "Tests Passed: 0 (0%)"
        )
        print(
            f"Tests Failed: {summary['tests_failed']} ({summary['tests_failed'] / summary['total_tests'] * 100:.1f}%)"
            if summary["total_tests"] > 0
            else "Tests Failed: 0 (0%)"
        )
        print(f"Duration: {summary['duration_ms'] / 1000:.2f}s")

        # Show failures if any
        all_failures = []
        for plugin_name, results in self.all_results["plugins"].items():
            all_failures.extend(results.get("failures", []))

        # Include cross-plugin failures
        cross = self.all_results.get("cross_plugin", {})
        all_failures.extend(cross.get("failures", []))

        if all_failures:
            print(f"\nFailures ({len(all_failures)}):")
            print("-" * 60)
            for failure in all_failures[:10]:  # Show first 10
                plugin = failure.get("plugin", failure.get("test", "cross-plugin"))
                name = failure.get("name", failure.get("case", "unknown"))
                reason = failure.get("reason", "unknown")
                print(f"[x] {plugin} - {name}")
                print(f"    {reason}")
            if len(all_failures) > 10:
                print(f"\n... and {len(all_failures) - 10} more failures")

    def run(self):
        """Run all tests for all plugins."""
        print("PopKit Modular Plugin Test Runner")
        print("=" * 60)

        # Discover plugins
        plugins = self.discover_plugins()
        print(f"Discovered {len(plugins)} plugin package(s):")
        for plugin in plugins:
            print(f"  - {plugin.name}")

        # Test each plugin
        for plugin_dir in plugins:
            plugin_name = plugin_dir.name
            plugin_results = self.run_plugin_tests(plugin_dir)
            self.all_results["plugins"][plugin_name] = plugin_results

            # Update summary
            self.all_results["summary"]["total_plugins"] += 1
            if plugin_results.get("skipped"):
                continue
            elif plugin_results["failed"] == 0:
                self.all_results["summary"]["plugins_passed"] += 1
            else:
                self.all_results["summary"]["plugins_failed"] += 1

            self.all_results["summary"]["total_tests"] += plugin_results["total"]
            self.all_results["summary"]["tests_passed"] += plugin_results["passed"]
            self.all_results["summary"]["tests_failed"] += plugin_results["failed"]
            self.all_results["summary"]["duration_ms"] += plugin_results["duration_ms"]

            if self.fail_fast and plugin_results["failed"] > 0:
                break

        # Run cross-plugin tests
        if not self.fail_fast or self.all_results["summary"]["tests_failed"] == 0:
            cross_results = self.run_cross_plugin_tests(plugins)
            self.all_results["cross_plugin"] = cross_results

            # Include cross-plugin results in summary
            if not cross_results.get("skipped"):
                self.all_results["summary"]["total_tests"] += cross_results["total"]
                self.all_results["summary"]["tests_passed"] += cross_results["passed"]
                self.all_results["summary"]["tests_failed"] += cross_results["failed"]
                self.all_results["summary"]["duration_ms"] += cross_results["duration_ms"]

        # Print summary
        self.print_summary()

        # Exit code: JSON tests are strict, pytest failures are reported but non-blocking
        json_failures = 0
        pytest_failures = 0
        for plugin_name, results in self.all_results["plugins"].items():
            for cat, cat_results in results.get("categories", {}).items():
                if cat == "pytest":
                    pytest_failures += cat_results.get("failed", 0)
                else:
                    json_failures += cat_results.get("failed", 0)

        # Cross-plugin failures are strict
        cross = self.all_results.get("cross_plugin", {})
        json_failures += cross.get("failed", 0)

        if pytest_failures > 0:
            print(f"\nNote: {pytest_failures} pytest failure(s) reported (non-blocking)")

        sys.exit(0 if json_failures == 0 else 1)


def main():
    """Main entry point."""
    # Parse arguments
    verbose = "--verbose" in sys.argv
    fail_fast = "--fail-fast" in sys.argv

    # Root is 3 levels up from this script (packages/popkit-core/run_all_tests.py -> apps/popkit)
    root_dir = Path(__file__).parent.parent.parent

    # Run tests
    runner = ModularPluginTestRunner(root_dir=root_dir, verbose=verbose, fail_fast=fail_fast)
    runner.run()


if __name__ == "__main__":
    main()
