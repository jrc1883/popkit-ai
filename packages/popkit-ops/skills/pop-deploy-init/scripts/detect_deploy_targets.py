#!/usr/bin/env python3
"""
Deployment Target Detection Script.

Analyze project structure to detect available deployment targets.

Usage:
    python detect_deploy_targets.py [--dir DIR] [--json]

Output:
    JSON object with detection results and recommended targets
"""

import json
import sys
from pathlib import Path
from typing import Any


def detect_docker_target(project_dir: Path) -> dict[str, Any]:
    """Detect Docker deployment capability."""
    result = {
        "detected": False,
        "confidence": "none",
        "reason": None,
        "config": {},
    }

    dockerfile = project_dir / "Dockerfile"
    compose_file = project_dir / "docker-compose.yml"
    compose_yaml = project_dir / "docker-compose.yaml"

    if dockerfile.exists():
        result["detected"] = True
        result["confidence"] = "high"
        result["reason"] = "Dockerfile exists"
        result["config"]["dockerfile"] = "Dockerfile"
        result["config"]["build_context"] = "."

        # Check for multi-stage build
        content = dockerfile.read_text()
        if "FROM" in content and content.count("FROM") > 1:
            result["config"]["multi_stage"] = True

    elif compose_file.exists() or compose_yaml.exists():
        result["detected"] = True
        result["confidence"] = "high"
        result["reason"] = "docker-compose.yml exists"
        result["config"]["compose_file"] = (
            "docker-compose.yml" if compose_file.exists() else "docker-compose.yaml"
        )

    # Check package.json for docker scripts
    pkg_json = project_dir / "package.json"
    if pkg_json.exists() and not result["detected"]:
        try:
            pkg = json.loads(pkg_json.read_text())
            scripts = pkg.get("scripts", {})
            if any("docker" in k.lower() for k in scripts):
                result["detected"] = True
                result["confidence"] = "medium"
                result["reason"] = "Docker scripts in package.json"
        except Exception:
            pass

    # Suggest image name from project
    if result["detected"]:
        result["config"]["image_name"] = _get_project_name(project_dir)
        result["config"]["registry"] = _detect_registry(project_dir)

    return result


def detect_npm_target(project_dir: Path) -> dict[str, Any]:
    """Detect npm publishing capability."""
    result = {
        "detected": False,
        "confidence": "none",
        "reason": None,
        "config": {},
    }

    pkg_json = project_dir / "package.json"
    if not pkg_json.exists():
        return result

    try:
        pkg = json.loads(pkg_json.read_text())

        # Check if it's a publishable package
        if pkg.get("private", False):
            result["reason"] = "Package marked as private"
            return result

        if "name" not in pkg:
            result["reason"] = "No package name defined"
            return result

        result["detected"] = True
        result["config"]["name"] = pkg["name"]
        result["config"]["registry"] = "https://registry.npmjs.org"
        result["config"]["access"] = (
            "restricted" if pkg["name"].startswith("@") else "public"
        )

        # Check for build/dist setup
        if "main" in pkg or "exports" in pkg:
            result["confidence"] = "high"
            result["reason"] = "Package has main/exports entry point"
        elif "bin" in pkg:
            result["confidence"] = "high"
            result["reason"] = "Package has bin entry point"
        else:
            result["confidence"] = "medium"
            result["reason"] = "Package.json exists without private flag"

        # Check for TypeScript
        if "typescript" in pkg.get("devDependencies", {}):
            result["config"]["typescript"] = True
            result["config"]["build_command"] = pkg.get("scripts", {}).get(
                "build", "tsc"
            )

    except Exception as e:
        result["reason"] = f"Error reading package.json: {e}"

    return result


def detect_pypi_target(project_dir: Path) -> dict[str, Any]:
    """Detect PyPI publishing capability."""
    result = {
        "detected": False,
        "confidence": "none",
        "reason": None,
        "config": {},
    }

    pyproject = project_dir / "pyproject.toml"
    setup_py = project_dir / "setup.py"

    if pyproject.exists():
        try:
            content = pyproject.read_text()

            # Check for project metadata
            if "[project]" in content:
                result["detected"] = True
                result["confidence"] = "high"
                result["reason"] = "pyproject.toml with [project] section"

                # Detect build backend
                if "hatchling" in content or "[tool.hatch" in content:
                    result["config"]["build_backend"] = "hatch"
                elif "poetry" in content or "[tool.poetry" in content:
                    result["config"]["build_backend"] = "poetry"
                elif "setuptools" in content:
                    result["config"]["build_backend"] = "setuptools"
                else:
                    result["config"]["build_backend"] = "setuptools"

                result["config"]["registry"] = "https://upload.pypi.org/legacy/"

        except Exception as e:
            result["reason"] = f"Error reading pyproject.toml: {e}"

    elif setup_py.exists():
        result["detected"] = True
        result["confidence"] = "medium"
        result["reason"] = "setup.py exists (legacy)"
        result["config"]["build_backend"] = "setuptools"
        result["config"]["registry"] = "https://upload.pypi.org/legacy/"

    return result


def detect_vercel_target(project_dir: Path) -> dict[str, Any]:
    """Detect Vercel deployment capability."""
    result = {
        "detected": False,
        "confidence": "none",
        "reason": None,
        "config": {},
    }

    vercel_json = project_dir / "vercel.json"
    vercel_dir = project_dir / ".vercel"
    pkg_json = project_dir / "package.json"

    if vercel_json.exists():
        result["detected"] = True
        result["confidence"] = "high"
        result["reason"] = "vercel.json exists"

        try:
            config = json.loads(vercel_json.read_text())
            if "projectId" in config:
                result["config"]["project_id"] = config["projectId"]
            if "orgId" in config:
                result["config"]["team_id"] = config["orgId"]
        except Exception:
            pass

    elif vercel_dir.exists():
        result["detected"] = True
        result["confidence"] = "medium"
        result["reason"] = ".vercel directory exists"

    # Check for Next.js (commonly deployed to Vercel)
    if pkg_json.exists() and not result["detected"]:
        try:
            pkg = json.loads(pkg_json.read_text())
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

            if "next" in deps:
                result["detected"] = True
                result["confidence"] = "high"
                result["reason"] = "Next.js project detected"
                result["config"]["framework"] = "nextjs"

        except Exception:
            pass

    if result["detected"]:
        result["config"]["production_branch"] = "main"

    return result


def detect_netlify_target(project_dir: Path) -> dict[str, Any]:
    """Detect Netlify deployment capability."""
    result = {
        "detected": False,
        "confidence": "none",
        "reason": None,
        "config": {},
    }

    netlify_toml = project_dir / "netlify.toml"
    netlify_dir = project_dir / ".netlify"

    if netlify_toml.exists():
        result["detected"] = True
        result["confidence"] = "high"
        result["reason"] = "netlify.toml exists"

        try:
            content = netlify_toml.read_text()
            # Basic TOML parsing for common fields
            if "publish" in content:
                result["config"]["has_publish_dir"] = True
            if "command" in content:
                result["config"]["has_build_command"] = True
        except Exception:
            pass

    elif netlify_dir.exists():
        result["detected"] = True
        result["confidence"] = "medium"
        result["reason"] = ".netlify directory exists"

    # Check for static site generators
    if not result["detected"]:
        pkg_json = project_dir / "package.json"
        if pkg_json.exists():
            try:
                pkg = json.loads(pkg_json.read_text())
                deps = {
                    **pkg.get("dependencies", {}),
                    **pkg.get("devDependencies", {}),
                }

                static_generators = ["gatsby", "hugo", "jekyll", "eleventy", "astro"]
                for gen in static_generators:
                    if gen in deps or f"@{gen}" in str(deps):
                        result["detected"] = True
                        result["confidence"] = "medium"
                        result["reason"] = f"{gen} static site detected"
                        result["config"]["framework"] = gen
                        break
            except Exception:
                pass

    return result


def detect_github_releases_target(project_dir: Path) -> dict[str, Any]:
    """Detect GitHub Releases capability."""
    result = {
        "detected": False,
        "confidence": "none",
        "reason": None,
        "config": {},
    }

    git_dir = project_dir / ".git"
    changelog = project_dir / "CHANGELOG.md"

    if not git_dir.exists():
        result["reason"] = "Not a git repository"
        return result

    result["detected"] = True

    # Check for existing release workflow
    workflows_dir = project_dir / ".github" / "workflows"
    if workflows_dir.exists():
        for workflow in workflows_dir.glob("*.yml"):
            try:
                content = workflow.read_text()
                if "release" in content.lower():
                    result["config"]["existing_workflow"] = workflow.name
                    result["confidence"] = "high"
                    result["reason"] = "Release workflow already exists"
                    break
            except Exception:
                pass

    if "confidence" not in result or result["confidence"] == "none":
        if changelog.exists():
            result["confidence"] = "high"
            result["reason"] = "CHANGELOG.md exists"
            result["config"]["changelog"] = True
        else:
            result["confidence"] = "medium"
            result["reason"] = "Git repository detected"

    result["config"]["release_notes_source"] = (
        "changelog" if changelog.exists() else "commits"
    )

    return result


def _get_project_name(project_dir: Path) -> str:
    """Get project name from package.json or directory name."""
    pkg_json = project_dir / "package.json"
    if pkg_json.exists():
        try:
            pkg = json.loads(pkg_json.read_text())
            name = pkg.get("name", "")
            if name:
                # Remove scope if present
                return name.split("/")[-1]
        except Exception:
            pass

    pyproject = project_dir / "pyproject.toml"
    if pyproject.exists():
        try:
            content = pyproject.read_text()
            # Simple extraction - look for name = "..."
            for line in content.split("\n"):
                if line.strip().startswith("name") and "=" in line:
                    name = line.split("=")[1].strip().strip('"').strip("'")
                    return name
        except Exception:
            pass

    return project_dir.name


def _detect_registry(project_dir: Path) -> str:
    """Detect container registry from git remote."""
    git_config = project_dir / ".git" / "config"
    if git_config.exists():
        try:
            content = git_config.read_text()
            if "github.com" in content:
                return "ghcr.io"
            if "gitlab.com" in content:
                return "registry.gitlab.com"
        except Exception:
            pass

    return "docker.io"


def detect_all_targets(project_dir: Path) -> dict[str, Any]:
    """Detect all deployment targets."""
    targets = {
        "docker": detect_docker_target(project_dir),
        "npm": detect_npm_target(project_dir),
        "pypi": detect_pypi_target(project_dir),
        "vercel": detect_vercel_target(project_dir),
        "netlify": detect_netlify_target(project_dir),
        "github_releases": detect_github_releases_target(project_dir),
    }

    # Calculate summary
    detected = [name for name, info in targets.items() if info["detected"]]
    high_confidence = [
        name
        for name, info in targets.items()
        if info["detected"] and info["confidence"] == "high"
    ]

    return {
        "targets": targets,
        "detected_count": len(detected),
        "detected_names": detected,
        "high_confidence": high_confidence,
        "recommended_primary": high_confidence[0] if high_confidence else None,
    }


def generate_question_config(detection: dict[str, Any]) -> dict[str, Any]:
    """Generate AskUserQuestion configuration for target selection."""
    options = []

    for name, info in detection["targets"].items():
        if info["detected"]:
            label_map = {
                "docker": "Docker",
                "npm": "npm Registry",
                "pypi": "PyPI Registry",
                "vercel": "Vercel",
                "netlify": "Netlify",
                "github_releases": "GitHub Releases",
            }

            label = label_map.get(name, name.title())
            if info["confidence"] == "high":
                label += " (Detected)"

            options.append(
                {
                    "id": name,
                    "label": label,
                    "description": info["reason"],
                    "detected": True,
                    "confidence": info["confidence"],
                }
            )

    # Add non-detected options with lower priority
    for name, info in detection["targets"].items():
        if not info["detected"]:
            label_map = {
                "docker": "Docker",
                "npm": "npm Registry",
                "pypi": "PyPI Registry",
                "vercel": "Vercel",
                "netlify": "Netlify",
                "github_releases": "GitHub Releases",
            }

            options.append(
                {
                    "id": name,
                    "label": label_map.get(name, name.title()),
                    "description": "Not detected - configure manually",
                    "detected": False,
                    "confidence": "none",
                }
            )

    return {
        "question": f"Detected {detection['detected_count']} deployment targets. Which do you want to configure?",
        "header": "Targets",
        "multiSelect": True,
        "options": options[:4],  # Limit to 4 per AskUserQuestion spec
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Detect deployment targets")
    parser.add_argument("--dir", default=".", help="Project directory")
    parser.add_argument(
        "--json", action="store_true", help="Output JSON only (no formatting)"
    )
    args = parser.parse_args()

    project_dir = Path(args.dir).resolve()

    if not project_dir.exists():
        print(
            json.dumps({"error": f"Directory not found: {project_dir}"}, indent=2),
            file=sys.stderr,
        )
        return 1

    detection = detect_all_targets(project_dir)
    question_config = generate_question_config(detection)

    report = {
        "operation": "detect_deploy_targets",
        "directory": str(project_dir),
        "project_name": _get_project_name(project_dir),
        "detection": detection,
        "question_config": question_config,
    }

    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
