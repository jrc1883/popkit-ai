#!/usr/bin/env python3
"""
Test Writer/Fixer Agent - PostToolUse Hook

Purpose: Auto-run tests after code changes to provide immediate feedback.
Scope: Agent-scoped (test-writer-fixer only)
Trigger: PostToolUse
Once: false (runs after every tool use)

This hook automatically runs tests after file modifications to detect
regressions early and provide immediate feedback on test status.
"""

import json
import sys
import os
import subprocess
from pathlib import Path


# File extensions that should trigger test runs
TEST_TRIGGER_EXTENSIONS = [
    ".py", ".js", ".ts", ".jsx", ".tsx",
    ".java", ".go", ".rs", ".rb", ".php"
]

# Test file patterns
TEST_FILE_PATTERNS = [
    "test_", "_test.", ".test.", ".spec.",
    "tests/", "test/", "__tests__/"
]


def is_test_file(file_path):
    """Check if a file is a test file."""
    if not file_path:
        return False

    file_path_lower = file_path.lower()

    for pattern in TEST_FILE_PATTERNS:
        if pattern in file_path_lower:
            return True

    return False


def is_code_file(file_path):
    """Check if a file is a code file that should trigger tests."""
    if not file_path:
        return False

    ext = Path(file_path).suffix.lower()
    return ext in TEST_TRIGGER_EXTENSIONS


def find_test_command(cwd):
    """
    Detect the appropriate test command for the project.

    Returns: (command, description) or (None, None)
    """
    cwd_path = Path(cwd) if cwd else Path.cwd()

    # Python projects
    if (cwd_path / "pytest.ini").exists() or (cwd_path / "setup.py").exists():
        return ["pytest", "--tb=short", "-v"], "pytest"

    # Node.js projects
    if (cwd_path / "package.json").exists():
        # Check for test script in package.json
        try:
            with open(cwd_path / "package.json") as f:
                package = json.load(f)
                if "scripts" in package and "test" in package["scripts"]:
                    return ["npm", "test"], "npm test"
        except:
            pass

    # Go projects
    if (cwd_path / "go.mod").exists():
        return ["go", "test", "./..."], "go test"

    # Rust projects
    if (cwd_path / "Cargo.toml").exists():
        return ["cargo", "test"], "cargo test"

    # Java/Maven projects
    if (cwd_path / "pom.xml").exists():
        return ["mvn", "test"], "mvn test"

    # Java/Gradle projects
    if (cwd_path / "build.gradle").exists():
        return ["./gradlew", "test"], "gradle test"

    return None, None


def run_tests(command, cwd, timeout=60):
    """
    Run tests with the given command.

    Args:
        command: List of command arguments
        cwd: Working directory
        timeout: Timeout in seconds

    Returns:
        {
            "passed": bool,
            "output": str,
            "duration": float
        }
    """
    import time

    start_time = time.time()

    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        duration = time.time() - start_time

        return {
            "passed": result.returncode == 0,
            "output": result.stdout + result.stderr,
            "duration": duration
        }

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        return {
            "passed": False,
            "output": f"Tests timed out after {timeout} seconds",
            "duration": duration
        }

    except Exception as e:
        duration = time.time() - start_time
        return {
            "passed": False,
            "output": f"Test execution error: {str(e)}",
            "duration": duration
        }


def handle_post_tool_use(data):
    """
    Auto-run tests after code changes.

    Args:
        data: {
            "tool": "Write" | "Edit" | "MultiEdit" | etc.,
            "input": {...},
            "output": {...},
            "agent": "test-writer-fixer"
        }

    Returns:
        {
            "decision": "allow",
            "message": "Optional test results"
        }
    """
    tool = data.get("tool", "")
    tool_input = data.get("input", {})

    # Only trigger on file modifications
    if tool not in ["Write", "Edit", "MultiEdit"]:
        return {"decision": "allow"}

    # Get the modified file path
    file_path = tool_input.get("file_path", "")

    # Skip if not a code file
    if not is_code_file(file_path):
        return {"decision": "allow"}

    # Determine working directory
    cwd = os.getcwd()

    # Find test command
    test_command, test_type = find_test_command(cwd)

    if not test_command:
        # No test framework detected - skip
        return {"decision": "allow"}

    # Run tests
    test_result = run_tests(test_command, cwd, timeout=60)

    # Format results message
    if test_result["passed"]:
        message = f"✓ Auto-test passed ({test_type}, {test_result['duration']:.1f}s)"
    else:
        # Extract key failure info (first 500 chars)
        output_preview = test_result["output"][:500]
        message = f"✗ Auto-test failed ({test_type}, {test_result['duration']:.1f}s)\n{output_preview}"

    return {
        "decision": "allow",
        "message": message
    }


if __name__ == "__main__":
    try:
        # Read input from stdin
        data = json.loads(sys.stdin.read())

        # Process the hook
        result = handle_post_tool_use(data)

        # Write output to stdout
        print(json.dumps(result))
        sys.exit(0)

    except Exception as e:
        # On error, allow the operation
        error_result = {
            "decision": "allow",
            "message": f"Hook error (tests not run): {str(e)}"
        }
        print(json.dumps(error_result))
        sys.exit(0)
