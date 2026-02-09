#!/usr/bin/env python3
"""
Git Worktree Operations Script

Multi-operation routing script for managing git worktrees:
- list: Display all worktrees with status
- create: Create new worktree with branch
- remove: Remove worktree with safety checks
- switch: Navigate to worktree directory
- update-all: Pull latest in all worktrees
- prune: Remove stale references
- init: Auto-create worktrees from branches
- analyze: Health analysis and cleanup recommendations

Usage:
    python worktree_operations.py --operation <op> [options]

Returns JSON output for programmatic integration.
"""

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Tuple, Optional


# ============================================================================
# Configuration
# ============================================================================

DEFAULT_CONFIG = {
    "worktree": {
        "enabled": True,
        "worktreeDir": "../[project]-worktrees",
        "namingPattern": "dev-[branch]",
        "autoUpdate": False,
        "autoInstall": False,
        "protectedBranches": ["main", "master", "develop", "production"],
    }
}


# ============================================================================
# Utility Functions
# ============================================================================


def run_git_command(cmd: str, timeout: int = 30) -> Tuple[str, bool]:
    """
    Execute git command safely.

    Args:
        cmd: Git command to run (will be split properly handling quotes)
        timeout: Command timeout in seconds

    Returns:
        Tuple of (output, success) - output includes stderr on failure
    """
    try:
        # Use shlex.split to properly handle quoted strings
        result = subprocess.run(
            ["git"] + shlex.split(cmd),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        # Return stdout on success, stderr (or both) on failure for better error messages
        if result.returncode == 0:
            return result.stdout.strip(), True
        else:
            error_output = result.stderr.strip() or result.stdout.strip()
            return error_output, False
    except subprocess.TimeoutExpired:
        return "Command timed out", False
    except Exception as e:
        return str(e), False


def load_config() -> Dict[str, Any]:
    """Load configuration from .popkit/config.json with defaults."""
    config_path = Path.cwd() / ".popkit" / "config.json"

    if config_path.exists():
        try:
            with open(config_path, "r") as f:
                config = json.load(f)
                # Merge with defaults
                worktree_config = DEFAULT_CONFIG["worktree"].copy()
                worktree_config.update(config.get("worktree", {}))
                return {"worktree": worktree_config}
        except Exception:
            pass

    return DEFAULT_CONFIG


def load_status_json() -> Dict[str, Any]:
    """Load STATUS.json if it exists."""
    status_path = Path.cwd() / ".popkit" / "STATUS.json"

    if status_path.exists():
        try:
            with open(status_path, "r") as f:
                return json.load(f)
        except Exception:
            pass

    return {}


def save_status_json(status: Dict[str, Any]) -> bool:
    """Save STATUS.json."""
    status_path = Path.cwd() / ".popkit" / "STATUS.json"
    status_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(status_path, "w") as f:
            json.dump(status, f, indent=2)
        return True
    except Exception:
        return False


def get_project_name() -> str:
    """Get project name from git root directory."""
    output, ok = run_git_command("rev-parse --show-toplevel")
    if ok:
        return Path(output).name
    return "project"


def resolve_worktree_path(
    branch: str, config: Dict[str, Any], name: Optional[str] = None
) -> Path:
    """
    Resolve worktree path from config template.

    Args:
        branch: Branch name
        config: Configuration dict
        name: Optional custom directory name

    Returns:
        Absolute path to worktree directory
    """
    project = get_project_name()

    if name:
        dirname = name
    else:
        # Apply naming pattern
        pattern = config["worktree"]["namingPattern"]
        dirname = pattern.replace("[branch]", branch.replace("/", "-"))

    # Resolve template
    template = config["worktree"]["worktreeDir"]
    template = template.replace("[project]", project)

    # Resolve relative to git root
    git_root_output, ok = run_git_command("rev-parse --show-toplevel")
    if not ok:
        return Path.cwd() / dirname

    git_root = Path(git_root_output)

    if template.startswith("../"):
        base_dir = git_root.parent / template[3:]
    elif template.startswith("./"):
        base_dir = git_root / template[2:]
    else:
        base_dir = Path(template)

    return base_dir / dirname


def enable_windows_longpaths() -> bool:
    """Enable Windows long paths if on Windows."""
    if sys.platform == "win32":
        output, ok = run_git_command("config core.longpaths true")
        return ok
    return True


# ============================================================================
# Operation Functions
# ============================================================================


def operation_list(json_output: bool = False) -> Dict[str, Any]:
    """List all worktrees with status."""
    output, ok = run_git_command("worktree list --porcelain")

    if not ok:
        return {
            "success": False,
            "error": "Failed to list worktrees",
            "details": output,
        }

    # Parse porcelain output
    worktrees = []
    current = {}

    for line in output.split("\n"):
        if line.startswith("worktree "):
            if current:
                worktrees.append(current)
            current = {"path": line[9:]}
        elif line.startswith("HEAD "):
            current["head"] = line[5:]
        elif line.startswith("branch "):
            current["branch"] = line[7:].replace("refs/heads/", "")
        elif line == "bare":
            current["bare"] = True
        elif line == "detached":
            current["detached"] = True

    if current:
        worktrees.append(current)

    # Enrich with status information
    for wt in worktrees:
        wt["isDefault"] = wt["path"] == Path.cwd().as_posix()

        # Check for uncommitted changes
        if Path(wt["path"]).exists():
            status_output, status_ok = run_git_command(
                f'-C "{wt["path"]}" status --porcelain'
            )
            wt["uncommittedChanges"] = bool(status_output) if status_ok else False

    if json_output:
        return {"success": True, "worktrees": worktrees}

    # Print table format
    print("\nWorktrees:")
    for wt in worktrees:
        branch = wt.get("branch", "detached")
        path = wt["path"]
        flags = []

        if wt.get("isDefault"):
            flags.append("default")
        if wt.get("uncommittedChanges"):
            flags.append("uncommitted changes")

        flag_str = f"  [{', '.join(flags)}]" if flags else ""
        print(f"  {branch:30s}  {path}{flag_str}")

    return {"success": True, "worktrees": worktrees}


def operation_create(
    branch: str, base: Optional[str] = None, name: Optional[str] = None
) -> Dict[str, Any]:
    """Create new worktree with branch."""
    config = load_config()

    # Check protected branches
    if branch in config["worktree"]["protectedBranches"]:
        return {
            "success": False,
            "error": f"Cannot create worktree on protected branch '{branch}'",
        }

    # Resolve worktree path
    worktree_path = resolve_worktree_path(branch, config, name)

    # Check if path already exists
    if worktree_path.exists():
        return {
            "success": False,
            "error": f"Worktree path already exists: {worktree_path}",
        }

    # Create parent directory
    worktree_path.parent.mkdir(parents=True, exist_ok=True)

    # Enable Windows long paths
    enable_windows_longpaths()

    # Create worktree (use .as_posix() for cross-platform compatibility)
    base_arg = f" {base}" if base else ""
    cmd = f'worktree add "{worktree_path.as_posix()}" -b {branch}{base_arg}'
    output, ok = run_git_command(cmd)

    if not ok:
        return {
            "success": False,
            "error": "Failed to create worktree",
            "details": output,
        }

    # Update STATUS.json
    status = load_status_json()
    if "git" not in status:
        status["git"] = {}

    status["git"]["worktree"] = {
        "isWorktree": True,
        "name": worktree_path.name,
        "baseRef": base or "HEAD",
        "linkedPath": str(Path.cwd()),
    }

    save_status_json(status)

    return {
        "success": True,
        "path": str(worktree_path),
        "branch": branch,
        "message": f"Worktree created at {worktree_path}",
    }


def operation_remove(name: str, force: bool = False) -> Dict[str, Any]:
    """Remove worktree with safety checks."""
    # Find worktree by name
    list_result = operation_list(json_output=True)
    if not list_result["success"]:
        return list_result

    worktree = None
    for wt in list_result["worktrees"]:
        wt_path = Path(wt["path"])
        # Match by: directory name, full path, or branch name
        if wt_path.name == name or wt["path"] == name or wt.get("branch") == name:
            worktree = wt
            break

    if not worktree:
        return {"success": False, "error": f"Worktree not found: {name}"}

    # Safety checks
    if worktree.get("uncommittedChanges") and not force:
        return {
            "success": False,
            "error": "Worktree has uncommitted changes. Use --force to remove anyway.",
        }

    # Remove worktree
    cmd = f'worktree remove "{worktree["path"]}"'
    if force:
        cmd += " --force"

    output, ok = run_git_command(cmd)

    if not ok:
        return {
            "success": False,
            "error": "Failed to remove worktree",
            "details": output,
        }

    return {"success": True, "message": f"Worktree removed: {worktree['path']}"}


def operation_switch(name: str) -> Dict[str, Any]:
    """Navigate to worktree directory (outputs path for shell integration)."""
    list_result = operation_list(json_output=True)
    if not list_result["success"]:
        return list_result

    for wt in list_result["worktrees"]:
        wt_path = Path(wt["path"])
        # Match by: directory name, full path, or branch name
        if wt_path.name == name or wt["path"] == name or wt.get("branch") == name:
            return {"success": True, "path": wt["path"]}

    return {"success": False, "error": f"Worktree not found: {name}"}


def operation_update_all(install: bool = False) -> Dict[str, Any]:
    """Pull latest in all worktrees."""
    list_result = operation_list(json_output=True)
    if not list_result["success"]:
        return list_result

    results = []

    for wt in list_result["worktrees"]:
        wt_path = wt["path"]
        branch = wt.get("branch", "detached")

        # Pull
        pull_output, pull_ok = run_git_command(f'-C "{wt_path}" pull')

        result = {
            "path": wt_path,
            "branch": branch,
            "pullSuccess": pull_ok,
            "pullOutput": pull_output,
        }

        # Install dependencies if requested
        if install and Path(wt_path, "package.json").exists():
            install_result = subprocess.run(
                "npm install", cwd=wt_path, capture_output=True, text=True, shell=True
            )
            result["installSuccess"] = install_result.returncode == 0
            result["installOutput"] = install_result.stdout.strip()

        results.append(result)

    success_count = sum(1 for r in results if r["pullSuccess"])

    return {
        "success": True,
        "totalWorktrees": len(results),
        "successCount": success_count,
        "results": results,
    }


def operation_prune(dry_run: bool = False) -> Dict[str, Any]:
    """Remove stale worktree references."""
    if dry_run:
        # List what would be pruned
        output, ok = run_git_command("worktree list --porcelain")

        if not ok:
            return {
                "success": False,
                "error": "Failed to list worktrees",
                "details": output,
            }

        stale = []
        current_path = None

        for line in output.split("\n"):
            if line.startswith("worktree "):
                current_path = line[9:]
            elif line.startswith("branch ") and current_path:
                if not Path(current_path).exists():
                    stale.append(current_path)
                current_path = None

        return {"success": True, "dryRun": True, "staleWorktrees": stale}

    # Actually prune
    output, ok = run_git_command("worktree prune")

    return {"success": ok, "output": output}


def operation_init(pattern: str = "dev-*") -> Dict[str, Any]:
    """Auto-create worktrees for branches matching pattern."""
    # List branches matching pattern
    output, ok = run_git_command(f"branch --list {pattern}")

    if not ok:
        return {"success": False, "error": "Failed to list branches", "details": output}

    # Parse branch names, removing '* ' prefix for current branch
    branches = []
    for line in output.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Remove '* ' prefix if present (current branch)
        if line.startswith("* "):
            branches.append(line[2:])
        else:
            branches.append(line)

    if not branches:
        return {"success": True, "message": f"No branches match pattern '{pattern}'"}

    # Get existing worktrees
    list_result = operation_list(json_output=True)
    existing_branches = {wt.get("branch") for wt in list_result.get("worktrees", [])}

    # Create worktrees for branches that don't have one
    created = []
    skipped = []

    for branch in branches:
        if branch in existing_branches:
            skipped.append(branch)
            continue

        create_result = operation_create(branch)
        if create_result["success"]:
            created.append(branch)

    return {"success": True, "pattern": pattern, "created": created, "skipped": skipped}


def operation_analyze() -> Dict[str, Any]:
    """Health analysis and cleanup recommendations."""
    list_result = operation_list(json_output=True)
    if not list_result["success"]:
        return list_result

    recommendations = []

    for wt in list_result["worktrees"]:
        wt_path = wt["path"]
        branch = wt.get("branch", "detached")

        # Check if behind base branch (assume main)
        behind_output, behind_ok = run_git_command(
            f'-C "{wt_path}" rev-list HEAD..main --count'
        )

        if behind_ok and behind_output and int(behind_output) > 0:
            recommendations.append(
                {
                    "id": "sync_worktree",
                    "name": f"Sync {branch} with main",
                    "command": "/popkit-dev:git merge main",
                    "score": 70,
                    "why": f"Worktree is {behind_output} commits behind main",
                }
            )

        # Check for uncommitted changes
        if wt.get("uncommittedChanges"):
            recommendations.append(
                {
                    "id": "commit_changes",
                    "name": f"Commit changes in {branch}",
                    "command": "/popkit-dev:git commit",
                    "score": 60,
                    "why": "Worktree has uncommitted changes",
                }
            )

    return {"success": True, "recommendations": recommendations}


# ============================================================================
# Main
# ============================================================================


def main():
    """Main entry point with operation routing."""
    parser = argparse.ArgumentParser(
        description="Git Worktree Operations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--operation",
        required=True,
        choices=[
            "list",
            "create",
            "remove",
            "switch",
            "update-all",
            "prune",
            "init",
            "analyze",
        ],
        help="Operation to perform",
    )

    # list options
    parser.add_argument("--json", action="store_true", help="Output in JSON format")

    # create options
    parser.add_argument("branch", nargs="?", help="Branch name for create operation")
    parser.add_argument("--base", help="Base branch for create operation")
    parser.add_argument("--name", help="Custom directory name for worktree")

    # remove options
    parser.add_argument("--force", action="store_true", help="Force removal")

    # update-all options
    parser.add_argument(
        "--install", action="store_true", help="Run npm install after update"
    )

    # prune options
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview without executing"
    )

    # init options
    parser.add_argument("--pattern", default="dev-*", help="Branch pattern for init")

    args = parser.parse_args()

    # Route to operation function
    result = None

    if args.operation == "list":
        result = operation_list(json_output=args.json)

    elif args.operation == "create":
        if not args.branch:
            result = {
                "success": False,
                "error": "Branch name required for create operation",
            }
        else:
            result = operation_create(args.branch, base=args.base, name=args.name)

    elif args.operation == "remove":
        if not args.branch:
            result = {
                "success": False,
                "error": "Worktree name required for remove operation",
            }
        else:
            result = operation_remove(args.branch, force=args.force)

    elif args.operation == "switch":
        if not args.branch:
            result = {
                "success": False,
                "error": "Worktree name required for switch operation",
            }
        else:
            result = operation_switch(args.branch)

    elif args.operation == "update-all":
        result = operation_update_all(install=args.install)

    elif args.operation == "prune":
        result = operation_prune(dry_run=args.dry_run)

    elif args.operation == "init":
        result = operation_init(pattern=args.pattern)

    elif args.operation == "analyze":
        result = operation_analyze()

    # Output result
    if result:
        if args.operation != "list" or args.json:
            print(json.dumps(result, indent=2))

        sys.exit(0 if result.get("success", False) else 1)
    else:
        print(json.dumps({"success": False, "error": "Unknown operation"}))
        sys.exit(1)


if __name__ == "__main__":
    main()
