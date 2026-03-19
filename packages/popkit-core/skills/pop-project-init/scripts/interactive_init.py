#!/usr/bin/env python3
"""
Interactive Project Init Detection Script.

Detects monorepo workspace, project type, and generates
AskUserQuestion configurations for the init workflow.

Usage:
    python interactive_init.py [--dir DIR]

Output:
    JSON object with detection results and question configs

Part of PopKit Issue #65.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# =============================================================================
# Monorepo Detection
# =============================================================================


def detect_monorepo(project_dir: Path) -> Dict[str, Any]:
    """Detect if the project is in a monorepo workspace.

    Args:
        project_dir: Path to the project directory

    Returns:
        Dict with is_monorepo, workspace_type, workspace_root, projects
    """
    result = {
        "is_monorepo": False,
        "workspace_type": None,
        "workspace_root": None,
        "projects": [],
    }

    # Check for workspace markers walking up from project_dir
    current = project_dir.resolve()
    for _ in range(10):
        if _has_workspace_marker(current):
            result["is_monorepo"] = True
            result["workspace_root"] = str(current)
            result["workspace_type"] = _detect_workspace_type(current)
            result["projects"] = _list_workspace_projects(
                current, result["workspace_type"]
            )
            break

        parent = current.parent
        if parent == current:
            break
        current = parent

    return result


def _has_workspace_marker(directory: Path) -> bool:
    """Check if a directory has workspace markers."""
    markers = [
        directory / "pnpm-workspace.yaml",
        directory / "lerna.json",
        directory / ".claude" / "workspace.json",
    ]

    for marker in markers:
        if marker.exists():
            return True

    # Check package.json for workspaces field
    package_json = directory / "package.json"
    if package_json.exists():
        try:
            data = json.loads(package_json.read_text(encoding="utf-8"))
            if "workspaces" in data:
                return True
        except (json.JSONDecodeError, IOError):
            pass  # Intentionally ignored: fallback to return False below

    return False


def _detect_workspace_type(workspace_root: Path) -> str:
    """Detect workspace type from markers."""
    if (workspace_root / "pnpm-workspace.yaml").exists():
        return "pnpm"
    if (workspace_root / "lerna.json").exists():
        return "lerna"
    if (workspace_root / ".claude" / "workspace.json").exists():
        return "popkit"

    if (workspace_root / "yarn.lock").exists():
        return "yarn"
    if (workspace_root / "pnpm-lock.yaml").exists():
        return "pnpm"

    return "npm"


def _list_workspace_projects(workspace_root: Path, workspace_type: str) -> List[str]:
    """List projects in the workspace."""
    projects = []

    # Check common package directories
    for packages_dir in ["packages", "apps", "libs", "services"]:
        pkg_path = workspace_root / packages_dir
        if pkg_path.is_dir():
            for child in sorted(pkg_path.iterdir()):
                if child.is_dir() and not child.name.startswith("."):
                    projects.append(f"{packages_dir}/{child.name}")

    return projects[:20]  # Limit to 20


# =============================================================================
# Stack Detection
# =============================================================================


def detect_stack(project_dir: Path) -> Dict[str, Any]:
    """Detect project stack/framework from existing files.

    Args:
        project_dir: Path to the project directory

    Returns:
        Dict with detected stack info and suggestions
    """
    result = {
        "detected": None,
        "confidence": "none",
        "indicators": {},
        "suggestions": [],
    }

    indicators = {
        "package_json": (project_dir / "package.json").exists(),
        "pyproject_toml": (project_dir / "pyproject.toml").exists(),
        "setup_py": (project_dir / "setup.py").exists(),
        "cargo_toml": (project_dir / "Cargo.toml").exists(),
        "go_mod": (project_dir / "go.mod").exists(),
        "wrangler_toml": (project_dir / "wrangler.toml").exists(),
        "tsconfig_json": (project_dir / "tsconfig.json").exists(),
    }
    result["indicators"] = indicators

    # Detect from package.json
    if indicators["package_json"]:
        try:
            pkg = json.loads((project_dir / "package.json").read_text(encoding="utf-8"))
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

            if "next" in deps:
                result["detected"] = "nextjs"
                result["confidence"] = "high"
            elif "react" in deps and "next" not in deps:
                result["detected"] = "react-spa"
                result["confidence"] = "high"
            elif "vue" in deps:
                result["detected"] = "vue"
                result["confidence"] = "high"
            elif "express" in deps or "fastify" in deps:
                result["detected"] = "node-api"
                result["confidence"] = "high"
            elif "typescript" in deps:
                result["detected"] = "typescript"
                result["confidence"] = "medium"
        except (json.JSONDecodeError, IOError):
            pass  # Intentionally ignored: stack detection continues with other indicators

    # Detect from pyproject.toml
    if indicators["pyproject_toml"]:
        try:
            content = (
                (project_dir / "pyproject.toml").read_text(encoding="utf-8").lower()
            )
            if "fastapi" in content:
                result["detected"] = "python-fastapi"
                result["confidence"] = "high"
            elif "django" in content:
                result["detected"] = "python-django"
                result["confidence"] = "high"
            elif "flask" in content:
                result["detected"] = "python-flask"
                result["confidence"] = "high"
            elif "click" in content:
                result["detected"] = "python-cli"
                result["confidence"] = "medium"
            else:
                result["detected"] = "python"
                result["confidence"] = "medium"
        except IOError:
            pass  # Intentionally ignored: stack detection continues with other indicators

    # Detect Cloudflare Workers
    if indicators["wrangler_toml"]:
        result["detected"] = "cloudflare-workers"
        result["confidence"] = "high"

    # Build suggestions list
    result["suggestions"] = _build_stack_suggestions(result["detected"])

    return result


def _build_stack_suggestions(detected: Optional[str]) -> List[Dict[str, str]]:
    """Build stack suggestion options."""
    all_stacks = [
        {
            "value": "nextjs",
            "label": "Next.js Application",
            "description": "Full-stack React with App Router, TypeScript, Tailwind",
        },
        {
            "value": "python-fastapi",
            "label": "Python FastAPI",
            "description": "Async Python API with OpenAPI docs, Pydantic",
        },
        {
            "value": "cloudflare-workers",
            "label": "Cloudflare Workers",
            "description": "Edge computing with Wrangler, TypeScript",
        },
        {
            "value": "react-spa",
            "label": "React SPA",
            "description": "Single-page React app with Vite, TypeScript",
        },
        {
            "value": "python-cli",
            "label": "Python CLI",
            "description": "Command-line tool with Click, Rich output",
        },
        {
            "value": "node-api",
            "label": "Node.js API",
            "description": "Express/Fastify API with TypeScript",
        },
        {
            "value": "library",
            "label": "Library/Package",
            "description": "Reusable npm or PyPI package",
        },
        {
            "value": "plugin",
            "label": "Claude Code Plugin",
            "description": "Plugin with skills, commands, and agents",
        },
    ]

    # Put detected stack first with (Detected) tag
    if detected:
        suggestions = []
        for stack in all_stacks:
            if stack["value"] == detected:
                stack["label"] = f"{stack['label']} (Detected)"
                suggestions.insert(0, stack)
            else:
                suggestions.append(stack)
        return suggestions

    return all_stacks


# =============================================================================
# Quality Gate Detection
# =============================================================================


def detect_quality_gates(project_dir: Path) -> Dict[str, Any]:
    """Detect existing quality gate configuration.

    Args:
        project_dir: Path to the project directory

    Returns:
        Dict with existing quality tools and recommended level
    """
    existing_tools = []

    # Check for existing quality tools
    if (project_dir / ".eslintrc.json").exists() or (
        project_dir / ".eslintrc.js"
    ).exists():
        existing_tools.append("eslint")
    if (project_dir / ".prettierrc").exists() or (
        project_dir / ".prettierrc.json"
    ).exists():
        existing_tools.append("prettier")
    if (project_dir / "tsconfig.json").exists():
        existing_tools.append("typescript")
    if (project_dir / "pyproject.toml").exists():
        try:
            content = (project_dir / "pyproject.toml").read_text(encoding="utf-8")
            if "[tool.ruff]" in content or "[tool.ruff" in content:
                existing_tools.append("ruff")
            if "[tool.mypy]" in content:
                existing_tools.append("mypy")
            if "[tool.pytest]" in content:
                existing_tools.append("pytest")
        except IOError:
            pass  # Intentionally ignored: quality detection continues without pyproject.toml data
    if (project_dir / ".github" / "workflows").is_dir():
        existing_tools.append("ci-workflows")
    if (project_dir / "SECURITY.md").exists():
        existing_tools.append("security-policy")

    # Recommend level based on existing tools
    if len(existing_tools) >= 5:
        recommended_level = "strict"
    elif len(existing_tools) >= 3:
        recommended_level = "standard"
    else:
        recommended_level = "basic"

    return {
        "existing_tools": existing_tools,
        "recommended_level": recommended_level,
    }


# =============================================================================
# Premium Feature Detection
# =============================================================================


def detect_premium_features(project_dir: Path) -> Dict[str, Any]:
    """Detect authentication status and available premium features.

    Args:
        project_dir: Path to the project directory

    Returns:
        Dict with is_authenticated and available features
    """
    is_authenticated = bool(os.environ.get("POPKIT_API_KEY"))
    has_voyage_key = bool(os.environ.get("VOYAGE_API_KEY"))

    plugin_data = os.environ.get("CLAUDE_PLUGIN_DATA")
    if plugin_data:
        config_path = Path(plugin_data) / "config.json"
    else:
        config_path = project_dir / ".claude" / "popkit" / "config.json"
    current_tier = "free"
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
            current_tier = config.get("tier", "free")
        except (json.JSONDecodeError, IOError):
            pass  # Intentionally ignored: defaults to free tier if config unreadable

    return {
        "is_authenticated": is_authenticated,
        "has_voyage_key": has_voyage_key,
        "current_tier": current_tier,
        "features": {
            "power_mode": "available",
            "semantic_search": "requires_voyage_key"
            if not has_voyage_key
            else "available",
            "cloud_sync": "requires_auth" if not is_authenticated else "available",
        },
    }


# =============================================================================
# Question Generation
# =============================================================================


def generate_questions(
    monorepo: Dict[str, Any],
    stack: Dict[str, Any],
    quality: Dict[str, Any],
    premium: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Generate AskUserQuestion configurations based on detection results.

    Args:
        monorepo: Monorepo detection results
        stack: Stack detection results
        quality: Quality gate detection results
        premium: Premium feature detection results

    Returns:
        List of question configurations for AskUserQuestion
    """
    questions = []

    # Question 1: Monorepo (only if detected)
    if monorepo["is_monorepo"]:
        project_count = len(monorepo["projects"])
        questions.append(
            {
                "id": "monorepo_config",
                "question": f"Monorepo detected ({monorepo['workspace_type']}, {project_count} packages). How should PopKit be configured?",
                "header": "Workspace",
                "options": [
                    {
                        "label": "App-specific config (Recommended)",
                        "description": "Configure PopKit for this app only with its own .claude/popkit/",
                    },
                    {
                        "label": "Shared workspace config",
                        "description": "Single PopKit config at workspace root shared by all apps",
                    },
                    {
                        "label": "Both (hybrid)",
                        "description": "Workspace config with app-specific overrides",
                    },
                ],
            }
        )

    # Question 2: Stack Selection
    stack_options = []
    suggestions = stack["suggestions"][:4]  # AskUserQuestion supports max 4 options
    for s in suggestions:
        stack_options.append(
            {
                "label": s["label"],
                "description": s["description"],
            }
        )

    if stack["confidence"] == "high":
        question_text = f"Detected {stack['detected']}. Confirm or change project type?"
    elif stack["confidence"] == "medium":
        question_text = f"Looks like {stack['detected']}. What type of project is this?"
    else:
        question_text = "What type of project would you like to initialize?"

    questions.append(
        {
            "id": "stack_selection",
            "question": question_text,
            "header": "Stack",
            "options": stack_options,
        }
    )

    # Question 3: Quality Gates
    rec = quality["recommended_level"]
    existing = quality["existing_tools"]
    existing_str = f" ({', '.join(existing[:3])})" if existing else ""

    questions.append(
        {
            "id": "quality_gates",
            "question": f"What quality gate level?{existing_str}",
            "header": "Quality",
            "options": [
                {
                    "label": "Basic" + (" (Recommended)" if rec == "basic" else ""),
                    "description": "Formatting only (Prettier/Ruff). Fast, minimal overhead.",
                },
                {
                    "label": "Standard"
                    + (" (Recommended)" if rec == "standard" else ""),
                    "description": "Formatting + linting + type checking. Good balance.",
                },
                {
                    "label": "Strict" + (" (Recommended)" if rec == "strict" else ""),
                    "description": "All of Standard + pre-commit hooks + test requirements.",
                },
                {
                    "label": "Enterprise",
                    "description": "All of Strict + security scanning + audit logging.",
                },
            ],
        }
    )

    # Question 4: Premium Features (only if authenticated)
    if premium["is_authenticated"] or premium["has_voyage_key"]:
        questions.append(
            {
                "id": "premium_features",
                "question": "Which premium features would you like to enable?",
                "header": "Features",
                "multiSelect": True,
                "options": [
                    {
                        "label": "Power Mode (Recommended)",
                        "description": "Multi-agent orchestration for parallel task execution",
                    },
                    {
                        "label": "Semantic Search",
                        "description": "Natural language search for skills, agents, and commands",
                    },
                    {
                        "label": "Cloud Sync",
                        "description": "Cross-session state and analytics via PopKit Cloud",
                    },
                ],
            }
        )

    return questions


# =============================================================================
# Main
# =============================================================================


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Interactive project init detection")
    parser.add_argument("--dir", default=".", help="Project directory")
    args = parser.parse_args()

    project_dir = Path(args.dir).resolve()

    # Run all detections
    monorepo = detect_monorepo(project_dir)
    stack = detect_stack(project_dir)
    quality = detect_quality_gates(project_dir)
    premium = detect_premium_features(project_dir)

    # Generate questions
    questions = generate_questions(monorepo, stack, quality, premium)

    result = {
        "operation": "interactive_init",
        "directory": str(project_dir),
        "detection": {
            "monorepo": monorepo,
            "stack": stack,
            "quality_gates": quality,
            "premium": premium,
        },
        "questions": questions,
        "question_count": len(questions),
    }

    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
