"""
Hook protocol validator for PopKit plugin testing.

Validates that hooks follow the JSON stdin/stdout protocol required by Claude Code.
"""

import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


def validate_hook_protocol(
    hook_path: Path, input_data: Any, timeout: int = 10000, plugin_root: Path | None = None
) -> dict[str, Any]:
    """
    Validate that a hook follows JSON stdin/stdout protocol.

    Args:
        hook_path: Path to hook Python file
        input_data: Input data to send via stdin (will be JSON-encoded)
        timeout: Maximum execution time in milliseconds (default: 10000)
        plugin_root: Optional plugin root directory (defaults to hook_path.parent.parent)

    Returns:
        Validation result dictionary:
        {
            'valid': bool,
            'exit_code': int,
            'stdout': str,
            'stderr': str,
            'duration_ms': int,
            'json_valid': bool,
            'parsed_output': dict (if JSON valid),
            'errors': List[str]
        }
    """
    result = {
        "valid": False,
        "exit_code": -1,
        "stdout": "",
        "stderr": "",
        "duration_ms": 0,
        "json_valid": False,
        "errors": [],
    }

    if not hook_path.exists():
        result["errors"].append(f"Hook file not found: {hook_path}")
        return result

    # Prepare input JSON
    try:
        if isinstance(input_data, str):
            # If string, use as-is (for testing invalid JSON)
            input_json = input_data
        else:
            input_json = json.dumps(input_data)
    except (TypeError, ValueError) as e:
        result["errors"].append(f"Failed to encode input as JSON: {e}")
        return result

    # Execute hook
    try:
        start_time = time.time()

        # Run from plugin root to ensure proper module imports
        # If not provided, assume hook is at <root>/hooks/<hook>.py
        if plugin_root is None:
            plugin_root = hook_path.parent.parent

        # Set environment variables for clean test execution
        import os

        test_env = os.environ.copy()
        test_env["POPKIT_TEST_MODE"] = "true"
        test_env["PYTHONDONTWRITEBYTECODE"] = "1"  # Prevent .pyc file creation

        # Add shared-py to PYTHONPATH so hooks can import popkit_shared
        shared_py_path = (plugin_root.parent / "shared-py").resolve()  # Use absolute path
        if shared_py_path.exists():
            existing_path = test_env.get("PYTHONPATH", "")
            test_env["PYTHONPATH"] = (
                f"{shared_py_path}:{existing_path}" if existing_path else str(shared_py_path)
            )

        process = subprocess.run(
            [sys.executable, str(hook_path)],
            input=input_json,
            capture_output=True,
            text=True,
            timeout=timeout / 1000,  # Convert to seconds
            cwd=str(plugin_root),
            env=test_env,
        )

        end_time = time.time()
        result["duration_ms"] = int((end_time - start_time) * 1000)
        result["exit_code"] = process.returncode
        result["stdout"] = process.stdout
        result["stderr"] = process.stderr

    except subprocess.TimeoutExpired:
        result["errors"].append(f"Hook exceeded timeout of {timeout}ms")
        return result
    except Exception as e:
        result["errors"].append(f"Failed to execute hook: {e}")
        return result

    # Validate JSON output
    if result["stdout"]:
        try:
            parsed = json.loads(result["stdout"])
            result["json_valid"] = True
            result["parsed_output"] = parsed

            # Check for required fields (if not error case)
            if result["exit_code"] == 0:
                # Hooks can return 'status', 'result', or 'decision' as top-level fields
                if "status" not in parsed and "result" not in parsed and "decision" not in parsed:
                    result["errors"].append(
                        "Output missing 'status', 'result', or 'decision' field"
                    )
                else:
                    result["valid"] = True
            else:
                # For error cases, just having valid JSON is enough
                result["valid"] = True

        except json.JSONDecodeError as e:
            result["errors"].append(f"Invalid JSON in stdout: {e}")
            result["json_valid"] = False

    elif result["exit_code"] == 0:
        # Hook succeeded but produced no output
        result["errors"].append("Hook produced no output on stdout")

    return result


def validate_all_hooks(
    hooks_dir: Path, sample_inputs: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Validate all hooks in a hooks directory.

    Args:
        hooks_dir: Path to hooks directory
        sample_inputs: Optional dict mapping hook names to sample inputs

    Returns:
        Validation results for all hooks
    """
    results = {"total": 0, "valid": 0, "invalid": 0, "hooks": {}}

    if not hooks_dir.exists():
        return results

    # Default sample inputs for common hooks
    default_inputs = {
        "pre-tool-use": {"tool": "Bash", "params": {"command": "echo test"}},
        "post-tool-use": {
            "tool": "Bash",
            "params": {"command": "echo test"},
            "result": {"success": True},
        },
        "session-start": {"event": "SessionStart", "session_id": "test-123"},
        "user-prompt-submit": {"event": "UserPromptSubmit", "prompt": "test prompt"},
    }

    # Use provided inputs or defaults
    inputs = sample_inputs if sample_inputs else default_inputs

    # Find all hook Python files
    hook_files = list(hooks_dir.glob("*.py"))
    hook_files = [h for h in hook_files if not h.name.startswith("test_")]

    for hook_file in hook_files:
        hook_name = hook_file.stem
        sample_input = inputs.get(hook_name, {})

        try:
            hook_result = validate_hook_protocol(hook_file, sample_input)

            results["total"] += 1
            if hook_result["valid"]:
                results["valid"] += 1
            else:
                results["invalid"] += 1

            results["hooks"][hook_name] = {
                "valid": hook_result["valid"],
                "exit_code": hook_result["exit_code"],
                "json_valid": hook_result["json_valid"],
                "duration_ms": hook_result["duration_ms"],
                "errors": hook_result["errors"],
            }

        except Exception as e:
            results["total"] += 1
            results["invalid"] += 1
            results["hooks"][hook_name] = {"valid": False, "error": str(e)}

    return results


def check_hook_performance(
    hook_path: Path, input_data: Any, iterations: int = 10
) -> dict[str, Any]:
    """
    Check hook performance over multiple iterations.

    Args:
        hook_path: Path to hook file
        input_data: Input data for hook
        iterations: Number of iterations to run

    Returns:
        Performance statistics
    """
    durations = []

    for _ in range(iterations):
        result = validate_hook_protocol(hook_path, input_data)
        if result["valid"]:
            durations.append(result["duration_ms"])

    if not durations:
        return {"valid": False, "error": "No successful runs"}

    return {
        "valid": True,
        "iterations": len(durations),
        "min_ms": min(durations),
        "max_ms": max(durations),
        "avg_ms": sum(durations) / len(durations),
        "total_ms": sum(durations),
    }
