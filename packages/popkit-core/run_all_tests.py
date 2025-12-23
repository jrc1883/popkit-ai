#!/usr/bin/env python3
"""
Modular test runner for all PopKit plugin packages.
Tests each plugin independently and runs cross-plugin validation.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any

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
            'plugins': {},
            'cross_plugin': {},
            'summary': {
                'total_plugins': 0,
                'plugins_passed': 0,
                'plugins_failed': 0,
                'total_tests': 0,
                'tests_passed': 0,
                'tests_failed': 0,
                'duration_ms': 0
            }
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

        print(f"\n{'='*60}")
        print(f"Testing Plugin: {plugin_name}")
        print(f"{'='*60}")

        if not tests_dir.exists():
            print(f"No tests directory found for {plugin_name}")
            return {
                'plugin': plugin_name,
                'total': 0,
                'passed': 0,
                'failed': 0,
                'skipped': True,
                'message': 'No tests directory'
            }

        # Load test files (excluding cross-plugin tests)
        test_files = []
        for category_dir in tests_dir.iterdir():
            if category_dir.is_dir() and category_dir.name != 'cross-plugin':
                test_files.extend(category_dir.glob("*.json"))

        if not test_files:
            print(f"No test files found for {plugin_name}")
            return {
                'plugin': plugin_name,
                'total': 0,
                'passed': 0,
                'failed': 0,
                'skipped': True,
                'message': 'No test files'
            }

        print(f"Found {len(test_files)} test file(s)")

        # Load test definitions
        test_defs = []
        for test_file in test_files:
            try:
                test_def = json.loads(test_file.read_text())
                test_def['_file'] = str(test_file)
                test_defs.append(test_def)
            except json.JSONDecodeError as e:
                print(f"Warning: Invalid JSON in {test_file}: {e}", file=sys.stderr)

        # Run tests
        runner = TestRunner(
            plugin_root=plugin_dir,
            verbose=self.verbose,
            fail_fast=self.fail_fast
        )

        results = {
            'plugin': plugin_name,
            'total': 0,
            'passed': 0,
            'failed': 0,
            'duration_ms': 0,
            'categories': {},
            'failures': []
        }

        for test_def in test_defs:
            cat = test_def.get('category', 'unknown')

            if cat not in results['categories']:
                results['categories'][cat] = {
                    'total': 0,
                    'passed': 0,
                    'failed': 0
                }

            try:
                test_result = runner.execute_test_definition(test_def)

                # Update totals
                results['total'] += test_result['total_cases']
                results['passed'] += test_result['passed']
                results['failed'] += test_result['failed']
                results['duration_ms'] += test_result['duration_ms']

                # Update category
                cat_results = results['categories'][cat]
                cat_results['total'] += test_result['total_cases']
                cat_results['passed'] += test_result['passed']
                cat_results['failed'] += test_result['failed']

                # Collect failures
                if test_result['failed'] > 0:
                    for failure in test_result['failures']:
                        failure['plugin'] = plugin_name
                    results['failures'].extend(test_result['failures'])

                    if self.fail_fast:
                        break

            except Exception as e:
                print(f"Error executing {test_def.get('name', 'unknown')}: {e}", file=sys.stderr)
                results['failed'] += 1

        return results

    def run_cross_plugin_tests(self, plugins: List[Path]) -> Dict[str, Any]:
        """
        Run cross-plugin validation tests.

        Args:
            plugins: List of all plugin directories

        Returns:
            Cross-plugin test results
        """
        print(f"\n{'='*60}")
        print("Running Cross-Plugin Validation Tests")
        print(f"{'='*60}")

        # Find cross-plugin test directory (usually in popkit-core)
        cross_plugin_tests_dir = self.root_dir / "packages" / "popkit-core" / "tests" / "cross-plugin"

        if not cross_plugin_tests_dir.exists():
            print("No cross-plugin tests found")
            return {
                'total': 0,
                'passed': 0,
                'failed': 0,
                'skipped': True
            }

        test_files = list(cross_plugin_tests_dir.glob("*.json"))
        print(f"Found {len(test_files)} cross-plugin test(s)")

        # For cross-plugin tests, we need to pass context about all plugins
        # This is a simplified implementation - would need custom validators
        results = {
            'total': len(test_files),
            'passed': 0,
            'failed': 0,
            'duration_ms': 0,
            'failures': []
        }

        # TODO: Implement cross-plugin test execution
        # For now, just note that they exist
        print("Cross-plugin tests discovered (execution requires custom validators)")
        results['skipped'] = True

        return results

    def print_summary(self):
        """Print comprehensive test summary."""
        print(f"\n{'='*60}")
        print("MODULAR PLUGIN TEST SUMMARY")
        print(f"{'='*60}\n")

        # Per-plugin results
        print("Per-Plugin Results:")
        print("-" * 60)

        for plugin_name, results in sorted(self.all_results['plugins'].items()):
            if results.get('skipped'):
                status = "[SKIP]"
                message = results.get('message', 'No tests')
            elif results['failed'] == 0:
                status = "[PASS]"
                message = f"{results['passed']}/{results['total']} tests passed"
            else:
                status = "[FAIL]"
                message = f"{results['failed']}/{results['total']} tests failed"

            print(f"{status} {plugin_name}: {message}")

            # Show category breakdown if verbose or failures
            if (self.verbose or results['failed'] > 0) and not results.get('skipped'):
                for cat, cat_results in sorted(results.get('categories', {}).items()):
                    cat_status = "[ok]" if cat_results['failed'] == 0 else "[x]"
                    print(f"  {cat_status} {cat}: {cat_results['passed']}/{cat_results['total']}")

        # Cross-plugin results
        cross = self.all_results.get('cross_plugin', {})
        if not cross.get('skipped'):
            status = "[PASS]" if cross['failed'] == 0 else "[FAIL]"
            print(f"\n{status} Cross-Plugin Validation: {cross['passed']}/{cross['total']}")

        # Overall summary
        summary = self.all_results['summary']
        print(f"\n{'='*60}")
        print("Overall Summary:")
        print("-" * 60)
        print(f"Total Plugins Tested: {summary['total_plugins']}")
        print(f"Plugins Passed: {summary['plugins_passed']}")
        print(f"Plugins Failed: {summary['plugins_failed']}")
        print(f"\nTotal Test Cases: {summary['total_tests']}")
        print(f"Tests Passed: {summary['tests_passed']} ({summary['tests_passed']/summary['total_tests']*100:.1f}%)" if summary['total_tests'] > 0 else "Tests Passed: 0 (0%)")
        print(f"Tests Failed: {summary['tests_failed']} ({summary['tests_failed']/summary['total_tests']*100:.1f}%)" if summary['total_tests'] > 0 else "Tests Failed: 0 (0%)")
        print(f"Duration: {summary['duration_ms']/1000:.2f}s")

        # Show failures if any
        all_failures = []
        for plugin_name, results in self.all_results['plugins'].items():
            all_failures.extend(results.get('failures', []))

        if all_failures:
            print(f"\nFailures ({len(all_failures)}):")
            print("-" * 60)
            for failure in all_failures[:10]:  # Show first 10
                plugin = failure.get('plugin', 'unknown')
                name = failure.get('name', 'unknown')
                reason = failure.get('reason', 'unknown')
                print(f"[x] {plugin} - {name}")
                print(f"    {reason}")
            if len(all_failures) > 10:
                print(f"\n... and {len(all_failures) - 10} more failures")

    def run(self):
        """Run all tests for all plugins."""
        print("PopKit Modular Plugin Test Runner")
        print("="*60)

        # Discover plugins
        plugins = self.discover_plugins()
        print(f"Discovered {len(plugins)} plugin package(s):")
        for plugin in plugins:
            print(f"  - {plugin.name}")

        # Test each plugin
        for plugin_dir in plugins:
            plugin_name = plugin_dir.name
            plugin_results = self.run_plugin_tests(plugin_dir)
            self.all_results['plugins'][plugin_name] = plugin_results

            # Update summary
            self.all_results['summary']['total_plugins'] += 1
            if plugin_results.get('skipped'):
                continue
            elif plugin_results['failed'] == 0:
                self.all_results['summary']['plugins_passed'] += 1
            else:
                self.all_results['summary']['plugins_failed'] += 1

            self.all_results['summary']['total_tests'] += plugin_results['total']
            self.all_results['summary']['tests_passed'] += plugin_results['passed']
            self.all_results['summary']['tests_failed'] += plugin_results['failed']
            self.all_results['summary']['duration_ms'] += plugin_results['duration_ms']

            if self.fail_fast and plugin_results['failed'] > 0:
                break

        # Run cross-plugin tests
        if not self.fail_fast or self.all_results['summary']['tests_failed'] == 0:
            cross_results = self.run_cross_plugin_tests(plugins)
            self.all_results['cross_plugin'] = cross_results

        # Print summary
        self.print_summary()

        # Exit code
        sys.exit(0 if self.all_results['summary']['tests_failed'] == 0 else 1)


def main():
    """Main entry point."""
    # Parse arguments
    verbose = "--verbose" in sys.argv
    fail_fast = "--fail-fast" in sys.argv

    # Root is 3 levels up from this script (packages/popkit-core/run_all_tests.py -> apps/popkit)
    root_dir = Path(__file__).parent.parent.parent

    # Run tests
    runner = ModularPluginTestRunner(
        root_dir=root_dir,
        verbose=verbose,
        fail_fast=fail_fast
    )
    runner.run()


if __name__ == "__main__":
    main()
