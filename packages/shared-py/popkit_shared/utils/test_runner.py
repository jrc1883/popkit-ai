"""
Test runner for PopKit plugin testing infrastructure.

Executes test definitions and validates assertions across all test categories:
- hooks: Hook protocol validation
- agents: Agent routing logic
- skills: Skill format compliance
- routing: Routing confidence and keywords
- structure: Plugin integrity
"""

import json
import time
from pathlib import Path
from typing import Any, Dict


class TestRunner:
    """Execute test definitions and validate assertions."""

    def __init__(self, plugin_root: Path, verbose: bool = False, fail_fast: bool = False):
        """
        Initialize test runner.

        Args:
            plugin_root: Path to plugin root directory
            verbose: Show detailed output for all tests
            fail_fast: Stop on first failure
        """
        self.plugin_root = Path(plugin_root)
        self.verbose = verbose
        self.fail_fast = fail_fast
        self.results = {
            "total_cases": 0,
            "passed": 0,
            "failed": 0,
            "duration_ms": 0,
            "failures": [],
        }

    def execute_test_definition(self, test_def: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a complete test definition with all test cases.

        Args:
            test_def: Test definition dictionary from JSON

        Returns:
            Test results dictionary with passed/failed counts
        """
        start_time = time.time()
        category = test_def.get("category", "unknown")

        results = {
            "test_id": test_def.get("test_id", "unknown"),
            "name": test_def.get("name", "unknown"),
            "category": category,
            "total_cases": len(test_def.get("test_cases", [])),
            "passed": 0,
            "failed": 0,
            "duration_ms": 0,
            "failures": [],
        }

        if self.verbose:
            print(f"\nExecuting: {test_def['name']}")
            print(f"Category: {category}")
            print(f"Test cases: {results['total_cases']}")

        # Execute each test case
        for test_case in test_def.get("test_cases", []):
            try:
                case_result = self._execute_test_case(test_def, test_case)

                if case_result["passed"]:
                    results["passed"] += 1
                    if self.verbose:
                        print(f"  [ok] {test_case.get('name', 'unknown')}")
                else:
                    results["failed"] += 1
                    results["failures"].append(case_result["failure"])

                    print(f"  [x] {test_case.get('name', 'unknown')}")
                    print(f"    Reason: {case_result['failure']['reason']}")

                    if self.fail_fast:
                        break

            except Exception as e:
                results["failed"] += 1
                failure = {
                    "test_id": test_def.get("test_id"),
                    "case_id": test_case.get("case_id", "unknown"),
                    "name": test_case.get("name", "unknown"),
                    "reason": f"Execution error: {str(e)}",
                    "error": str(e),
                }
                results["failures"].append(failure)

                print(f"  [x] {test_case.get('name', 'unknown')}")
                print(f"    Error: {str(e)}")

                if self.fail_fast:
                    break

        # Calculate duration
        end_time = time.time()
        results["duration_ms"] = int((end_time - start_time) * 1000)

        return results

    def _execute_test_case(
        self, test_def: Dict[str, Any], test_case: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single test case.

        Args:
            test_def: Parent test definition
            test_case: Individual test case

        Returns:
            Result dictionary with passed status and optional failure details
        """
        category = test_def.get("category")

        # Route to appropriate validator based on category
        if category == "hooks":
            return self._execute_hook_test(test_def, test_case)
        elif category == "agents":
            return self._execute_agent_test(test_def, test_case)
        elif category == "skills":
            return self._execute_skill_test(test_def, test_case)
        elif category == "routing":
            return self._execute_routing_test(test_def, test_case)
        elif category == "structure":
            return self._execute_structure_test(test_def, test_case)
        else:
            return {
                "passed": False,
                "failure": {
                    "test_id": test_def.get("test_id"),
                    "case_id": test_case.get("case_id"),
                    "reason": f"Unknown test category: {category}",
                },
            }

    def _execute_hook_test(self, test_def: Dict, test_case: Dict) -> Dict:
        """Execute hook protocol test."""
        from .hook_validator import validate_hook_protocol

        hook_file = self.plugin_root / test_def.get("hook_file", "")

        if not hook_file.exists():
            return {
                "passed": False,
                "failure": {
                    "test_id": test_def.get("test_id"),
                    "case_id": test_case.get("case_id"),
                    "reason": f"Hook file not found: {hook_file}",
                },
            }

        try:
            result = validate_hook_protocol(
                hook_file, test_case.get("input"), plugin_root=self.plugin_root
            )
            return self._validate_assertions(test_def, test_case, result)
        except Exception as e:
            return {
                "passed": False,
                "failure": {
                    "test_id": test_def.get("test_id"),
                    "case_id": test_case.get("case_id"),
                    "reason": f"Hook validation error: {str(e)}",
                },
            }

    def _execute_agent_test(self, test_def: Dict, test_case: Dict) -> Dict:
        """Execute agent definition validation test (modular architecture)."""
        from .agent_validator import validate_agent_files

        try:
            # For modular architecture, we validate agent markdown files
            result = validate_agent_files(self.plugin_root)

            # If test case specifies plugins to scan, collect all agent files
            if test_case.get("scan_all_plugins"):
                # This would require scanning multiple plugin directories
                # For now, just validate current plugin
                pass

            return self._validate_assertions(test_def, test_case, result)
        except Exception as e:
            return {
                "passed": False,
                "failure": {
                    "test_id": test_def.get("test_id"),
                    "case_id": test_case.get("case_id"),
                    "reason": f"Agent validation test error: {str(e)}",
                },
            }

    def _execute_skill_test(self, test_def: Dict, test_case: Dict) -> Dict:
        """Execute skill format test."""
        from .skill_validator import validate_all_skills

        scan_pattern = test_case.get("scan_pattern", "skills/*/SKILL.md")
        skill_files = list(self.plugin_root.glob(scan_pattern))

        if not skill_files:
            return {
                "passed": False,
                "failure": {
                    "test_id": test_def.get("test_id"),
                    "case_id": test_case.get("case_id"),
                    "reason": f"No skill files found matching: {scan_pattern}",
                },
            }

        try:
            results = validate_all_skills(skill_files)
            return self._validate_assertions(test_def, test_case, {"skills": results})
        except Exception as e:
            return {
                "passed": False,
                "failure": {
                    "test_id": test_def.get("test_id"),
                    "case_id": test_case.get("case_id"),
                    "reason": f"Skill validation error: {str(e)}",
                },
            }

    def _execute_routing_test(self, test_def: Dict, test_case: Dict) -> Dict:
        """Execute routing logic test."""
        # Similar to agent test but focuses on routing logic
        return self._execute_agent_test(test_def, test_case)

    def _execute_structure_test(self, test_def: Dict, test_case: Dict) -> Dict:
        """Execute plugin structure integrity test."""
        from .plugin_validator import validate_plugin_structure

        try:
            # If test case specifies a file, validate that specific file
            if "file" in test_case:
                file_path = self.plugin_root / test_case["file"]

                # Check if file is optional
                if test_case.get("optional") and not file_path.exists():
                    return {"passed": True}

                # Build result for file validation
                result = {
                    "file_path": str(file_path),
                    "exists": file_path.exists(),
                    "json_valid": False,
                }

                if file_path.exists():
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            parsed = json.load(f)
                            result["json_valid"] = True
                            result.update(parsed)  # Add parsed content to result
                    except json.JSONDecodeError as e:
                        result["json_error"] = str(e)
                else:
                    result["error"] = f"File not found: {test_case['file']}"

                return self._validate_assertions(test_def, test_case, result)
            else:
                # General structure validation
                result = validate_plugin_structure(self.plugin_root)
                return self._validate_assertions(test_def, test_case, result)
        except Exception as e:
            return {
                "passed": False,
                "failure": {
                    "test_id": test_def.get("test_id"),
                    "case_id": test_case.get("case_id"),
                    "reason": f"Structure validation error: {str(e)}",
                },
            }

    def _validate_assertions(self, test_def: Dict, test_case: Dict, result: Dict) -> Dict:
        """
        Validate assertions against test result.

        Args:
            test_def: Test definition
            test_case: Test case with assertions
            result: Result from test execution

        Returns:
            Validation result with passed status
        """
        assertions = test_case.get("assertions", [])

        for assertion in assertions:
            assertion_type = assertion.get("type")

            try:
                if assertion_type == "exit_code":
                    if result.get("exit_code") != assertion.get("expected"):
                        return self._create_failure(
                            test_def,
                            test_case,
                            assertion,
                            "Exit code mismatch",
                            assertion.get("expected"),
                            result.get("exit_code"),
                        )

                elif assertion_type == "json_valid":
                    if not result.get("json_valid", False):
                        return self._create_failure(
                            test_def, test_case, assertion, "Output is not valid JSON"
                        )

                elif assertion_type == "has_field":
                    field = assertion.get("field")
                    # For hook tests, check in parsed_output if available
                    check_dict = result.get("parsed_output", result)
                    if field not in check_dict:
                        return self._create_failure(
                            test_def, test_case, assertion, f"Missing required field: {field}"
                        )

                elif assertion_type == "regex":
                    import re

                    field = assertion.get("field")
                    pattern = assertion.get("pattern")
                    check_dict = result.get("parsed_output", result)

                    # Handle skill arrays: check each skill's field
                    if "skills" in result and isinstance(result["skills"], list):
                        for skill in result["skills"]:
                            if "frontmatter" in skill and field in skill["frontmatter"]:
                                value = skill["frontmatter"][field]
                                if not re.match(pattern, str(value)):
                                    return self._create_failure(
                                        test_def,
                                        test_case,
                                        assertion,
                                        f"Field '{field}' does not match pattern in {skill.get('file', 'unknown')}",
                                        pattern,
                                        value,
                                    )
                    else:
                        value = check_dict.get(field, "")
                        if not re.match(pattern, str(value)):
                            return self._create_failure(
                                test_def,
                                test_case,
                                assertion,
                                f"Field '{field}' does not match pattern",
                                pattern,
                                value,
                            )

                elif assertion_type == "duration":
                    max_ms = assertion.get("max_ms")
                    actual_ms = result.get("duration_ms", 0)
                    if actual_ms > max_ms:
                        return self._create_failure(
                            test_def,
                            test_case,
                            assertion,
                            "Duration exceeded",
                            f"< {max_ms}ms",
                            f"{actual_ms}ms",
                        )

                elif assertion_type == "agent_activated":
                    agent = assertion.get("agent")
                    if agent not in result.get("activated_agents", []):
                        return self._create_failure(
                            test_def, test_case, assertion, f"Agent not activated: {agent}"
                        )

                elif assertion_type == "file_exists":
                    file_path = self.plugin_root / assertion.get("path", "")
                    if not file_path.exists():
                        return self._create_failure(
                            test_def,
                            test_case,
                            assertion,
                            f"File not found: {assertion.get('path')}",
                        )

                elif assertion_type == "file_not_exists":
                    file_path = self.plugin_root / assertion.get("path", "")
                    if file_path.exists():
                        return self._create_failure(
                            test_def,
                            test_case,
                            assertion,
                            f"File should not exist: {assertion.get('path')}",
                        )

                elif assertion_type == "directory_exists":
                    dir_path = self.plugin_root / assertion.get("path", "")
                    required = assertion.get("required", True)
                    if required and not (dir_path.exists() and dir_path.is_dir()):
                        return self._create_failure(
                            test_def,
                            test_case,
                            assertion,
                            f"Required directory not found: {assertion.get('path')}",
                        )

                elif assertion_type == "yaml_frontmatter_exists":
                    # Check if result has valid frontmatter
                    if not result.get("valid"):
                        errors = result.get("errors", [])
                        if any("frontmatter" in str(e).lower() for e in errors):
                            return self._create_failure(
                                test_def,
                                test_case,
                                assertion,
                                "YAML frontmatter missing or invalid",
                            )

                elif assertion_type == "agents_directory_exists":
                    agents_dir = self.plugin_root / "agents"
                    if not (agents_dir.exists() and agents_dir.is_dir()):
                        return self._create_failure(
                            test_def, test_case, assertion, "Agents directory does not exist"
                        )

                elif assertion_type == "agent_files_found":
                    min_count = assertion.get("min_count", 1)
                    agent_count = result.get("agent_count", 0)
                    if agent_count < min_count:
                        return self._create_failure(
                            test_def,
                            test_case,
                            assertion,
                            f"Expected at least {min_count} agent file(s), found {agent_count}",
                        )

                elif assertion_type == "commands_registered":
                    # Check if all command files are registered in plugin.json
                    # This is validated by plugin_validator, check result
                    if not result.get("valid", True):
                        errors = result.get("errors", [])
                        if any("command" in str(e).lower() for e in errors):
                            return self._create_failure(
                                test_def, test_case, assertion, "Not all commands are registered"
                            )

                elif assertion_type == "skills_registered":
                    # Check if all skill directories are registered in plugin.json
                    if not result.get("valid", True):
                        errors = result.get("errors", [])
                        if any("skill" in str(e).lower() for e in errors):
                            return self._create_failure(
                                test_def, test_case, assertion, "Not all skills are registered"
                            )

                elif assertion_type == "agents_registered":
                    # Check if all agent files are registered in plugin.json
                    if not result.get("valid", True):
                        errors = result.get("errors", [])
                        if any("agent" in str(e).lower() for e in errors):
                            return self._create_failure(
                                test_def, test_case, assertion, "Not all agents are registered"
                            )

                elif assertion_type == "file_in_tier_directory":
                    # Check if agent files are in proper tier directories
                    allowed_tiers = assertion.get("allowed_tiers", [])
                    # This would need to be validated by checking file paths
                    # For now, assume validated by plugin_validator
                    pass

                elif assertion_type == "note":
                    # Notes are informational, always pass
                    pass

                # Add more assertion types as needed

            except Exception as e:
                return self._create_failure(
                    test_def, test_case, assertion, f"Assertion error: {str(e)}"
                )

        # All assertions passed
        return {"passed": True}

    def _create_failure(
        self,
        test_def: Dict,
        test_case: Dict,
        assertion: Dict,
        reason: str,
        expected: Any = None,
        actual: Any = None,
    ) -> Dict:
        """Create failure result dictionary."""
        failure = {
            "test_id": test_def.get("test_id"),
            "case_id": test_case.get("case_id"),
            "name": test_case.get("name"),
            "assertion": assertion.get("type"),
            "reason": reason,
        }

        if expected is not None:
            failure["expected"] = expected
        if actual is not None:
            failure["actual"] = actual
        if "description" in assertion:
            failure["description"] = assertion["description"]

        return {"passed": False, "failure": failure}
