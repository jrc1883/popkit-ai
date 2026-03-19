#!/usr/bin/env python3
"""
Elicitation Hook (Claude Code 2.1.76+)
Fires when the model requests structured input from the user.

Enhances elicitation events with PopKit context so the model asks
better, more informed questions during interactive dialogs.

Responsibilities:
1. Read the elicitation request from stdin JSON
2. Detect if it relates to a PopKit workflow (deploy, brainstorm, project-init)
3. Inject relevant context as additionalContext:
   - deploy: current deploy.json config, available targets
   - project setup: detected project type, tech stack
   - brainstorming: current issue context, recent decisions
4. Lightweight (< 2 seconds), stdlib only
"""

import json
import sys
from datetime import datetime
from pathlib import Path


def detect_workflow(elicitation_data):
    """Detect which PopKit workflow the elicitation relates to.

    Examines the elicitation message/title and the tool_name that triggered it
    to determine the active workflow context.

    Returns:
        str or None: One of 'deploy', 'project-init', 'brainstorm', or None
    """
    message = elicitation_data.get("message", "").lower()
    title = elicitation_data.get("title", "").lower()
    tool_name = elicitation_data.get("tool_name", "").lower()
    combined = f"{message} {title} {tool_name}"

    deploy_signals = [
        "deploy",
        "target",
        "environment",
        "staging",
        "production",
        "release",
        "rollout",
        "infrastructure",
        "pop-deploy",
    ]
    project_signals = [
        "project",
        "init",
        "setup",
        "scaffold",
        "template",
        "create",
        "new project",
        "pop-project",
        "tech stack",
    ]
    brainstorm_signals = [
        "brainstorm",
        "design",
        "architect",
        "approach",
        "trade-off",
        "alternative",
        "option",
        "decision",
        "pop-brainstorm",
    ]

    for signal in deploy_signals:
        if signal in combined:
            return "deploy"

    for signal in project_signals:
        if signal in combined:
            return "project-init"

    for signal in brainstorm_signals:
        if signal in combined:
            return "brainstorm"

    return None


def get_deploy_context():
    """Gather deployment context from the current project.

    Reads deploy.json and scans for common deployment configuration files
    to provide context about available deploy targets.

    Returns:
        str: Human-readable summary of deployment configuration
    """
    context_parts = []

    # Check for deploy.json
    deploy_file = Path.cwd() / "deploy.json"
    if deploy_file.exists():
        try:
            with open(deploy_file, "r", encoding="utf-8") as f:
                deploy_config = json.load(f)
            targets = deploy_config.get(
                "targets", deploy_config.get("environments", {})
            )
            if isinstance(targets, dict):
                target_names = list(targets.keys())
            elif isinstance(targets, list):
                target_names = [t.get("name", str(i)) for i, t in enumerate(targets)]
            else:
                target_names = []
            context_parts.append(
                f"Deploy targets: {', '.join(target_names) if target_names else 'none configured'}"
            )

            # Include current default target if set
            default_target = deploy_config.get(
                "default", deploy_config.get("defaultTarget")
            )
            if default_target:
                context_parts.append(f"Default target: {default_target}")
        except (json.JSONDecodeError, OSError):
            context_parts.append("deploy.json exists but could not be parsed")
    else:
        context_parts.append("No deploy.json found in project root")

    # Check for common deployment config files
    deploy_indicators = {
        "Dockerfile": "Docker",
        "docker-compose.yml": "Docker Compose",
        "docker-compose.yaml": "Docker Compose",
        "fly.toml": "Fly.io",
        "vercel.json": "Vercel",
        "netlify.toml": "Netlify",
        "railway.json": "Railway",
        "render.yaml": "Render",
        "Procfile": "Heroku",
        "app.yaml": "Google App Engine",
        "serverless.yml": "Serverless Framework",
        ".github/workflows/deploy.yml": "GitHub Actions deploy",
    }

    detected_platforms = []
    for filename, platform in deploy_indicators.items():
        if (Path.cwd() / filename).exists():
            detected_platforms.append(platform)

    if detected_platforms:
        context_parts.append(f"Detected platforms: {', '.join(detected_platforms)}")

    return " | ".join(context_parts) if context_parts else ""


def get_project_init_context():
    """Gather project type and tech stack context.

    Detects the project type from configuration files and package manifests
    to provide context for project initialization elicitations.

    Returns:
        str: Human-readable summary of detected project characteristics
    """
    context_parts = []
    cwd = Path.cwd()

    # Detect project type from config files
    project_indicators = {
        "package.json": "Node.js",
        "pyproject.toml": "Python (pyproject)",
        "setup.py": "Python (setup.py)",
        "requirements.txt": "Python (pip)",
        "Cargo.toml": "Rust",
        "go.mod": "Go",
        "pom.xml": "Java (Maven)",
        "build.gradle": "Java (Gradle)",
        "Gemfile": "Ruby",
        "composer.json": "PHP",
        "Package.swift": "Swift",
        "mix.exs": "Elixir",
    }

    detected_types = []
    for filename, project_type in project_indicators.items():
        if (cwd / filename).exists():
            detected_types.append(project_type)

    if detected_types:
        context_parts.append(f"Detected stack: {', '.join(detected_types)}")

    # Check for monorepo indicators
    if (cwd / "lerna.json").exists() or (cwd / "pnpm-workspace.yaml").exists():
        context_parts.append("Monorepo detected")
    elif (cwd / "packages").is_dir():
        pkg_count = sum(1 for p in (cwd / "packages").iterdir() if p.is_dir())
        if pkg_count > 0:
            context_parts.append(f"Possible monorepo: {pkg_count} packages")

    # Check for framework indicators
    framework_indicators = {
        "next.config.js": "Next.js",
        "next.config.mjs": "Next.js",
        "next.config.ts": "Next.js",
        "nuxt.config.ts": "Nuxt",
        "vite.config.ts": "Vite",
        "angular.json": "Angular",
        "svelte.config.js": "SvelteKit",
        "astro.config.mjs": "Astro",
        "remix.config.js": "Remix",
    }

    detected_frameworks = []
    for filename, framework in framework_indicators.items():
        if (cwd / filename).exists():
            detected_frameworks.append(framework)

    if detected_frameworks:
        context_parts.append(f"Framework: {', '.join(detected_frameworks)}")

    # Check for CLAUDE.md (PopKit-managed project)
    if (cwd / "CLAUDE.md").exists():
        context_parts.append("PopKit-managed project (CLAUDE.md present)")

    return " | ".join(context_parts) if context_parts else ""


def get_brainstorm_context():
    """Gather brainstorming context from current project state.

    Reads STATUS.json for recent decisions and context, and checks for
    active issue context to inform brainstorming elicitations.

    Returns:
        str: Human-readable summary of relevant brainstorming context
    """
    context_parts = []

    # Read STATUS.json for current context
    status_file = Path.cwd() / ".claude" / "STATUS.json"
    if status_file.exists():
        try:
            with open(status_file, "r", encoding="utf-8") as f:
                status = json.load(f)

            # Current task context
            task = status.get("currentTask", status.get("task"))
            if task:
                context_parts.append(f"Current task: {task}")

            # Git branch (indicates what we are working on)
            git_info = status.get("git", {})
            branch = git_info.get("branch")
            if branch:
                context_parts.append(f"Branch: {branch}")

            # Recent decisions
            decisions = status.get("context", {}).get("keyDecisions", [])
            if decisions:
                recent = decisions[-3:]  # Last 3 decisions
                decision_text = "; ".join(
                    d.get("summary", d.get("decision", str(d)))
                    if isinstance(d, dict)
                    else str(d)
                    for d in recent
                )
                context_parts.append(f"Recent decisions: {decision_text}")
        except (json.JSONDecodeError, OSError):
            pass

    # Check decisions log for broader context
    decisions_log = Path.cwd() / ".claude" / "popkit" / "decisions-log.json"
    if decisions_log.exists():
        try:
            with open(decisions_log, "r", encoding="utf-8") as f:
                log_entries = json.load(f)
            if log_entries:
                count = len(log_entries)
                context_parts.append(f"{count} previous decisions logged")
        except (json.JSONDecodeError, OSError):
            pass

    return " | ".join(context_parts) if context_parts else ""


def process_elicitation(elicitation_data):
    """Process an elicitation event and return context enhancements.

    Args:
        elicitation_data: Dict from stdin containing elicitation details

    Returns:
        Dict with the hook response (additionalContext if relevant)
    """
    workflow = detect_workflow(elicitation_data)

    if workflow is None:
        # Not a PopKit workflow -- pass through without modification
        return {
            "status": "success",
            "message": "No PopKit workflow context needed",
            "timestamp": datetime.now().isoformat(),
        }

    # Gather workflow-specific context
    context_gatherers = {
        "deploy": get_deploy_context,
        "project-init": get_project_init_context,
        "brainstorm": get_brainstorm_context,
    }

    gatherer = context_gatherers.get(workflow)
    context_text = gatherer() if gatherer else ""

    if not context_text:
        return {
            "status": "success",
            "message": f"Workflow '{workflow}' detected but no context available",
            "timestamp": datetime.now().isoformat(),
        }

    # Build additionalContext for the model
    additional_context = f"POPKIT [{workflow.upper()}]: {context_text}"

    print(
        f"  Elicitation context injected for workflow: {workflow}",
        file=sys.stderr,
    )

    return {
        "additionalContext": additional_context,
        "status": "success",
        "message": f"Context injected for {workflow} workflow",
        "timestamp": datetime.now().isoformat(),
    }


def main():
    """Main entry point - JSON stdin/stdout protocol."""
    try:
        input_data = sys.stdin.read()
        data = json.loads(input_data) if input_data.strip() else {}

        result = process_elicitation(data)

        print(json.dumps(result))

    except json.JSONDecodeError:
        response = {
            "status": "success",
            "message": "Elicitation hook completed (no input)",
            "timestamp": datetime.now().isoformat(),
        }
        print(json.dumps(response))
    except Exception as e:
        response = {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }
        print(json.dumps(response))
        print(f"Error in elicitation hook: {e}", file=sys.stderr)
        sys.exit(0)  # Never block on errors


if __name__ == "__main__":
    main()
