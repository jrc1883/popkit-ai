#!/usr/bin/env python3
"""
Subprocess Utilities for PopKit.

Consolidated command execution utilities used across all skill scripts.
Replaces 11 duplicate implementations with a single, well-tested module.

Issue #303: Consolidate duplicated run_command function

Usage:
    from popkit_shared.utils.subprocess_utils import run_command, run_command_simple

    # Full result with exit code
    exit_code, stdout, stderr = run_command(["git", "status"], cwd="/path")

    # Simplified result (stdout, success)
    output, success = run_command_simple("git status")
"""

import subprocess
from pathlib import Path
from typing import List, Optional, Tuple, Union


def run_command(
    cmd: Union[str, List[str]],
    cwd: Optional[Union[str, Path]] = None,
    timeout: int = 30,
    shell: bool = False,
    strip_output: bool = True,
) -> Tuple[int, str, str]:
    """
    Run a command and return full result.

    This is the primary command execution function. Use this when you need
    the exit code or stderr output.

    Args:
        cmd: Command as string or list of strings.
             If string and shell=False, will be split on spaces.
        cwd: Working directory (optional)
        timeout: Timeout in seconds (default: 30)
        shell: Run through shell (default: False, for security)
        strip_output: If True (default), strip whitespace from output.
                     If False, only strip trailing newlines (preserves leading ws).

    Returns:
        Tuple of (exit_code, stdout, stderr)
        - exit_code: -1 on timeout or exception
        - stdout: Command output (stripped based on strip_output)
        - stderr: Error output or exception message

    Examples:
        >>> exit_code, stdout, stderr = run_command(["git", "status"])
        >>> exit_code, stdout, stderr = run_command("npm test", cwd="/project")
    """
    try:
        # Normalize command to list if needed
        if isinstance(cmd, str) and not shell:
            cmd_list = cmd.split()
        else:
            cmd_list = cmd

        # Normalize cwd to string if Path
        cwd_str = str(cwd) if cwd else None

        result = subprocess.run(
            cmd_list,
            cwd=cwd_str,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=shell,
        )

        if strip_output:
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
        else:
            # Only strip trailing newlines, preserve leading whitespace
            stdout = result.stdout.rstrip("\r\n")
            stderr = result.stderr.rstrip("\r\n")

        return result.returncode, stdout, stderr

    except subprocess.TimeoutExpired:
        return -1, "", f"Command timed out after {timeout}s"
    except FileNotFoundError as e:
        return -1, "", f"Command not found: {e}"
    except PermissionError as e:
        return -1, "", f"Permission denied: {e}"
    except Exception as e:
        return -1, "", str(e)


def run_command_simple(
    cmd: Union[str, List[str]],
    cwd: Optional[Union[str, Path]] = None,
    timeout: int = 30,
    strip_output: bool = True,
) -> Tuple[str, bool]:
    """
    Run a command and return simplified result.

    Use this when you only need stdout and success/failure status.
    This is the most common pattern in skill scripts.

    Args:
        cmd: Command as string or list of strings
        cwd: Working directory (optional)
        timeout: Timeout in seconds (default: 30)
        strip_output: If True (default), strip whitespace from output.
                     If False, only strip trailing newlines (preserves leading ws).

    Returns:
        Tuple of (output, success)
        - output: stdout on success, error message on failure
        - success: True if exit code was 0

    Examples:
        >>> output, success = run_command_simple("git branch --show-current")
        >>> if success:
        ...     print(f"Current branch: {output}")
        >>> # Preserve leading whitespace (e.g., for git status --porcelain)
        >>> output, success = run_command_simple("git status --porcelain", strip_output=False)
    """
    exit_code, stdout, stderr = run_command(
        cmd, cwd=cwd, timeout=timeout, strip_output=strip_output
    )

    if exit_code == 0:
        return stdout, True
    else:
        # Return stderr if available, otherwise stdout (some commands output errors to stdout)
        error_msg = stderr if stderr else stdout if stdout else f"Exit code: {exit_code}"
        return error_msg, False


def run_command_checked(
    cmd: Union[str, List[str]],
    cwd: Optional[Union[str, Path]] = None,
    timeout: int = 30,
) -> str:
    """
    Run a command and return output, raising on failure.

    Use this when command failure should be an exception.

    Args:
        cmd: Command as string or list of strings
        cwd: Working directory (optional)
        timeout: Timeout in seconds (default: 30)

    Returns:
        Command stdout (stripped)

    Raises:
        RuntimeError: If command fails (non-zero exit code or timeout)

    Examples:
        >>> try:
        ...     branch = run_command_checked("git branch --show-current")
        ... except RuntimeError as e:
        ...     print(f"Git failed: {e}")
    """
    exit_code, stdout, stderr = run_command(cmd, cwd=cwd, timeout=timeout)

    if exit_code != 0:
        error_msg = stderr if stderr else stdout if stdout else f"Exit code: {exit_code}"
        cmd_str = cmd if isinstance(cmd, str) else " ".join(cmd)
        raise RuntimeError(f"Command failed: {cmd_str}\n{error_msg}")

    return stdout


def run_git_command(
    args: Union[str, List[str]],
    cwd: Optional[Union[str, Path]] = None,
    timeout: int = 30,
) -> Tuple[str, bool]:
    """
    Run a git command with 'git' prefix.

    Convenience function for git operations.

    Args:
        args: Git arguments (without 'git' prefix)
        cwd: Working directory (optional)
        timeout: Timeout in seconds (default: 30)

    Returns:
        Tuple of (output, success)

    Examples:
        >>> output, success = run_git_command("branch --show-current")
        >>> output, success = run_git_command(["log", "-1", "--format=%h"])
    """
    if isinstance(args, str):
        cmd = f"git {args}"
    else:
        cmd = ["git"] + args

    return run_command_simple(cmd, cwd=cwd, timeout=timeout)


# Backwards compatibility aliases
# These maintain the exact signatures used in existing code


def run_command_full(cmd: List[str], cwd: str, timeout: int = 30) -> Tuple[int, str, str]:
    """
    Legacy signature matching health_calculator.py.

    Prefer using run_command() directly.
    """
    return run_command(cmd, cwd=cwd, timeout=timeout)


# Module exports
__all__ = [
    "run_command",
    "run_command_simple",
    "run_command_checked",
    "run_git_command",
    "run_command_full",  # Legacy compatibility
]
