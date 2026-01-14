#!/usr/bin/env python3
"""
Pre-Commit Hook
Runs Ruff validation on staged Python files before commit.

Responsibilities:
1. Detect staged Python files
2. Run Ruff check --fix on staged files
3. Run Ruff format on staged files
4. Re-stage files if auto-fixes applied
5. Block commit on unfixable errors
6. Fail-open if Ruff not installed (with warning)

Issue #156: Automatic Ruff Pre-Commit Hook Integration
"""

import sys
import json
import subprocess


def get_staged_python_files():
    """Get list of staged Python files.

    Returns:
        list: List of staged Python file paths, or None on error
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode != 0:
            return None

        # Filter for Python files only
        files = result.stdout.strip().split("\n")
        python_files = [f for f in files if f.endswith(".py") and f]

        return python_files if python_files else []

    except Exception:
        # Git command failed or timeout - fail-open gracefully
        return None


def check_ruff_installed():
    """Check if Ruff is installed.

    Returns:
        bool: True if Ruff is installed, False otherwise
    """
    try:
        result = subprocess.run(["ruff", "--version"], capture_output=True, timeout=2)
        return result.returncode == 0
    except Exception:
        return False


def run_ruff_check(files):
    """Run Ruff check with auto-fix on files.

    Args:
        files: List of file paths to check

    Returns:
        dict: Result with 'success', 'fixed_files', 'errors'
    """
    try:
        result = subprocess.run(
            ["ruff", "check", "--fix"] + files,
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Ruff exit codes:
        # 0 = no issues
        # 1 = issues found (may be auto-fixed)
        # 2 = fatal error

        if result.returncode == 2:
            return {
                "success": False,
                "fixed_files": [],
                "errors": result.stdout + result.stderr,
            }

        # Parse output to detect fixed files
        fixed_files = []
        if result.returncode == 1 or "Fixed" in result.stdout:
            # Check which files were modified
            for file in files:
                try:
                    # Check if file was modified (unstaged changes)
                    check_result = subprocess.run(
                        ["git", "diff", "--name-only", file],
                        capture_output=True,
                        text=True,
                        timeout=2,
                    )
                    if file in check_result.stdout:
                        fixed_files.append(file)
                except Exception:
                    # git diff failed for this file - skip detection
                    pass

        return {
            "success": result.returncode in [0, 1],
            "fixed_files": fixed_files,
            "errors": result.stdout + result.stderr if result.returncode != 0 else "",
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "fixed_files": [],
            "errors": "Ruff check timed out after 30 seconds",
        }
    except Exception as e:
        return {"success": False, "fixed_files": [], "errors": str(e)}


def run_ruff_format(files):
    """Run Ruff format on files.

    Args:
        files: List of file paths to format

    Returns:
        dict: Result with 'success', 'formatted_files', 'errors'
    """
    try:
        result = subprocess.run(
            ["ruff", "format"] + files, capture_output=True, text=True, timeout=30
        )

        if result.returncode != 0:
            return {
                "success": False,
                "formatted_files": [],
                "errors": result.stdout + result.stderr,
            }

        # Check which files were formatted
        formatted_files = []
        for file in files:
            try:
                # Check if file was modified (unstaged changes)
                check_result = subprocess.run(
                    ["git", "diff", "--name-only", file],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                if file in check_result.stdout:
                    formatted_files.append(file)
            except Exception:
                # git diff failed for this file - skip detection
                pass

        return {"success": True, "formatted_files": formatted_files, "errors": ""}

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "formatted_files": [],
            "errors": "Ruff format timed out after 30 seconds",
        }
    except Exception as e:
        return {"success": False, "formatted_files": [], "errors": str(e)}


def restage_files(files):
    """Re-stage files after auto-fixes.

    Args:
        files: List of file paths to re-stage

    Returns:
        bool: True if successful, False otherwise
    """
    if not files:
        return True

    try:
        result = subprocess.run(["git", "add"] + files, capture_output=True, timeout=5)
        return result.returncode == 0
    except Exception:
        return False


def main():
    """Main entry point for the hook - JSON stdin/stdout protocol"""
    try:
        # Read input data from stdin (hook protocol expects JSON, but we don't need it for pre-commit)
        input_data = sys.stdin.read()
        _ = json.loads(input_data) if input_data.strip() else {}

        # Get staged Python files
        python_files = get_staged_python_files()

        if python_files is None:
            # Git command failed - fail-open
            response = {
                "status": "success",
                "message": "Pre-commit hook: git command failed, allowing commit",
                "warning": "Could not detect staged files",
            }
            print(json.dumps(response))
            sys.exit(0)

        if not python_files:
            # No Python files staged - skip hook
            response = {
                "status": "success",
                "message": "Pre-commit hook: no Python files staged, skipping Ruff validation",
            }
            print(json.dumps(response))
            sys.exit(0)

        # Check if Ruff is installed
        if not check_ruff_installed():
            # Ruff not installed - fail-open with warning
            warning_msg = (
                "⚠️  Ruff is not installed. Install with: pip install ruff\n"
                "   Pre-commit validation will be skipped until Ruff is available."
            )
            print(warning_msg, file=sys.stderr)

            response = {
                "status": "success",
                "message": "Pre-commit hook: Ruff not installed, allowing commit",
                "warning": "Ruff not found - install with 'pip install ruff'",
                "files_skipped": python_files,
            }
            print(json.dumps(response))
            sys.exit(0)

        # Run Ruff check with auto-fix
        print(f"Running Ruff check on {len(python_files)} file(s)...", file=sys.stderr)
        check_result = run_ruff_check(python_files)

        if not check_result["success"]:
            # Ruff found unfixable errors - block commit
            error_msg = (
                "❌ Ruff found issues that could not be auto-fixed:\n\n"
                f"{check_result['errors']}\n\n"
                "Please fix these issues and try again."
            )
            print(error_msg, file=sys.stderr)

            response = {
                "status": "error",
                "message": "Pre-commit hook: Ruff validation failed",
                "errors": check_result["errors"],
                "files_checked": python_files,
            }
            print(json.dumps(response))
            sys.exit(1)  # Block commit

        # Run Ruff format
        print("Running Ruff format...", file=sys.stderr)
        format_result = run_ruff_format(python_files)

        if not format_result["success"]:
            # Format failed - block commit
            error_msg = (
                "❌ Ruff format failed:\n\n"
                f"{format_result['errors']}\n\n"
                "Please fix these issues and try again."
            )
            print(error_msg, file=sys.stderr)

            response = {
                "status": "error",
                "message": "Pre-commit hook: Ruff format failed",
                "errors": format_result["errors"],
                "files_checked": python_files,
            }
            print(json.dumps(response))
            sys.exit(1)  # Block commit

        # Re-stage files if auto-fixes were applied
        all_modified = list(
            set(check_result["fixed_files"] + format_result["formatted_files"])
        )

        if all_modified:
            print(
                f"Auto-fixed {len(all_modified)} file(s), re-staging...",
                file=sys.stderr,
            )

            if not restage_files(all_modified):
                # Re-stage failed - warn but allow commit
                warning_msg = "⚠️  Could not re-stage auto-fixed files. Please review and stage manually."
                print(warning_msg, file=sys.stderr)

                response = {
                    "status": "success",
                    "message": "Pre-commit hook: Ruff validation passed with fixes",
                    "warning": "Could not re-stage auto-fixed files",
                    "files_checked": python_files,
                    "files_fixed": all_modified,
                }
                print(json.dumps(response))
                sys.exit(0)

            success_msg = "✓ Ruff validation passed. Auto-fixes applied and staged."
            print(success_msg, file=sys.stderr)
        else:
            success_msg = "✓ Ruff validation passed. No issues found."
            print(success_msg, file=sys.stderr)

        # Success
        response = {
            "status": "success",
            "message": "Pre-commit hook: Ruff validation passed",
            "files_checked": python_files,
            "files_fixed": all_modified,
        }
        print(json.dumps(response))
        sys.exit(0)

    except json.JSONDecodeError as e:
        # Invalid JSON input - fail-open
        response = {"status": "error", "error": f"Invalid JSON input: {e}"}
        print(json.dumps(response))
        sys.exit(0)  # Don't block on hook errors

    except Exception as e:
        # Generic exception - fail-open
        response = {"status": "error", "error": str(e)}
        print(json.dumps(response))
        print(f"⚠️  Error in pre-commit hook: {e}", file=sys.stderr)
        sys.exit(0)  # Don't block on hook errors


if __name__ == "__main__":
    main()
