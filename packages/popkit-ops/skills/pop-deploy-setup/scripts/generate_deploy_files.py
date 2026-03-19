#!/usr/bin/env python3
"""
Deployment File Generator.

Generate deployment infrastructure files from deploy.json configuration.

Usage:
    python generate_deploy_files.py --dir DIR --action ACTION [--targets TARGETS] [--template LEVEL]

Actions:
    load-config  - Load and validate deploy.json, report status
    generate     - Generate deployment files for specified targets

Output:
    JSON object with operation results
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Configuration loading
# ---------------------------------------------------------------------------


def load_deploy_config(project_dir: Path) -> dict[str, Any]:
    """Load and validate .claude/popkit/deploy.json."""
    config_file = project_dir / ".claude" / "popkit" / "deploy.json"

    if not config_file.exists():
        return {
            "success": False,
            "error": "deploy.json not found. Run /popkit-ops:deploy init first.",
            "config_path": str(config_file),
        }

    try:
        config = json.loads(config_file.read_text())
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "error": f"Invalid JSON in deploy.json: {e}",
            "config_path": str(config_file),
        }

    # Validate required fields
    required_fields = ["version", "project_name", "targets"]
    missing = [f for f in required_fields if f not in config]
    if missing:
        return {
            "success": False,
            "error": f"Missing required fields in deploy.json: {', '.join(missing)}",
            "config_path": str(config_file),
        }

    # Find enabled targets
    enabled_targets = [
        name
        for name, target in config.get("targets", {}).items()
        if target.get("enabled", False)
    ]

    primary_target = None
    for name, target in config.get("targets", {}).items():
        if target.get("primary", False):
            primary_target = name
            break

    return {
        "success": True,
        "config_path": str(config_file),
        "project_name": config["project_name"],
        "enabled_targets": enabled_targets,
        "primary_target": primary_target,
        "ci_provider": config.get("ci", {}).get("provider"),
        "config": config,
    }


def detect_existing_files(project_dir: Path, targets: list[str]) -> dict[str, Any]:
    """Detect existing deployment files that might conflict."""
    existing = {}
    conflicts = []

    file_checks = {
        "docker": [
            "Dockerfile",
            "docker-compose.yml",
            "docker-compose.yaml",
            ".dockerignore",
        ],
        "npm": [".npmrc", ".npmignore"],
        "pypi": ["MANIFEST.in", "setup.cfg"],
        "vercel": ["vercel.json"],
        "netlify": ["netlify.toml"],
        "github_releases": [],
        "k8s": ["k8s/deployment.yml", "k8s/service.yml", "k8s/ingress.yml"],
    }

    ci_files = [
        ".github/workflows/deploy.yml",
        ".github/workflows/release.yml",
        ".github/workflows/test.yml",
    ]

    for target in targets:
        target_files = file_checks.get(target, [])
        for file_path in target_files:
            full_path = project_dir / file_path
            if full_path.exists():
                existing[file_path] = {
                    "exists": True,
                    "size": full_path.stat().st_size,
                }
                conflicts.append(file_path)

    # Always check CI files
    for file_path in ci_files:
        full_path = project_dir / file_path
        if full_path.exists():
            existing[file_path] = {
                "exists": True,
                "size": full_path.stat().st_size,
            }
            conflicts.append(file_path)

    return {
        "existing_files": existing,
        "conflicts": conflicts,
        "conflict_count": len(conflicts),
    }


# ---------------------------------------------------------------------------
# File generators
# ---------------------------------------------------------------------------


def generate_dockerfile(
    project_name: str, config: dict[str, Any], template: str
) -> str:
    """Generate Dockerfile content based on project config."""
    docker_config = config.get("config", {})

    if template == "minimal":
        return """FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
CMD ["node", "src/index.js"]
"""

    if template == "advanced":
        return """# Stage 1: Dependencies
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

# Stage 2: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Stage 3: Production
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

RUN addgroup --system --gid 1001 appgroup \\
    && adduser --system --uid 1001 appuser

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

USER appuser
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

CMD ["node", "dist/index.js"]
"""

    # standard (default)
    return """# Build stage
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM node:20-alpine
WORKDIR /app
ENV NODE_ENV=production

COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \\
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000/health || exit 1

CMD ["node", "dist/index.js"]
"""


def generate_dockerignore() -> str:
    """Generate .dockerignore content."""
    return """node_modules
npm-debug.log*
.git
.gitignore
.env
.env.*
*.md
!README.md
Dockerfile
docker-compose*.yml
.dockerignore
.github
.vscode
.idea
coverage
.nyc_output
dist
__pycache__
*.pyc
.pytest_cache
.mypy_cache
"""


def generate_docker_compose(
    project_name: str, config: dict[str, Any], template: str
) -> str:
    """Generate docker-compose.yml content."""
    docker_config = config.get("config", {})
    image_name = docker_config.get("image_name", project_name)

    if template == "minimal":
        return """services:
  app:
    build: .
    ports:
      - "3000:3000"
"""

    if template == "advanced":
        return f"""services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
      args:
        NODE_ENV: production
    image: {image_name}:latest
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000/health"]
      interval: 30s
      timeout: 3s
      start_period: 5s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: "1.0"
          memory: 512M
        reservations:
          cpus: "0.25"
          memory: 128M
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
"""

    # standard
    return f"""services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    image: {image_name}:latest
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:3000/health"]
      interval: 30s
      timeout: 3s
      start_period: 5s
      retries: 3
"""


def generate_k8s_deployment(project_name: str, config: dict[str, Any]) -> str:
    """Generate Kubernetes deployment manifest."""
    docker_config = config.get("targets", {}).get("docker", {}).get("config", {})
    image_name = docker_config.get("image_name", project_name)
    registry = docker_config.get("registry", "ghcr.io")

    return f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {project_name}
  labels:
    app: {project_name}
spec:
  replicas: 2
  selector:
    matchLabels:
      app: {project_name}
  template:
    metadata:
      labels:
        app: {project_name}
    spec:
      containers:
        - name: {project_name}
          image: {registry}/{image_name}:latest
          ports:
            - containerPort: 3000
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
          livenessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 10
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: 3000
            initialDelaySeconds: 5
            periodSeconds: 10
"""


def generate_k8s_service(project_name: str) -> str:
    """Generate Kubernetes service manifest."""
    return f"""apiVersion: v1
kind: Service
metadata:
  name: {project_name}
  labels:
    app: {project_name}
spec:
  type: ClusterIP
  ports:
    - port: 80
      targetPort: 3000
      protocol: TCP
      name: http
  selector:
    app: {project_name}
"""


def generate_k8s_ingress(project_name: str) -> str:
    """Generate Kubernetes ingress manifest."""
    return f"""apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {project_name}
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
    - host: {project_name}.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {project_name}
                port:
                  number: 80
"""


def generate_github_actions_deploy(
    project_name: str, config: dict[str, Any], template: str
) -> str:
    """Generate GitHub Actions deploy workflow."""
    ci_config = config.get("ci", {})
    triggers = ci_config.get("triggers", {})
    push_branches = triggers.get("push", ["main"])
    tag_patterns = triggers.get("tag", ["v*"])
    workflow_dispatch = ci_config.get("workflow_dispatch", False)

    # Build trigger section
    trigger_lines = ["on:"]
    if push_branches:
        trigger_lines.append("  push:")
        trigger_lines.append("    branches:")
        for branch in push_branches:
            trigger_lines.append(f'      - "{branch}"')
    if tag_patterns:
        if not push_branches:
            trigger_lines.append("  push:")
        trigger_lines.append("    tags:")
        for pattern in tag_patterns:
            trigger_lines.append(f'      - "{pattern}"')
    if workflow_dispatch:
        trigger_lines.append("  workflow_dispatch:")
        trigger_lines.append("    inputs:")
        trigger_lines.append("      environment:")
        trigger_lines.append('        description: "Deployment environment"')
        trigger_lines.append("        required: true")
        trigger_lines.append('        default: "staging"')
        trigger_lines.append("        type: choice")
        trigger_lines.append("        options:")
        trigger_lines.append("          - staging")
        trigger_lines.append("          - production")

    trigger_section = "\n".join(trigger_lines)

    if template == "minimal":
        return f"""name: Deploy
{trigger_section}
jobs:
  deploy:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4

      - name: Build
        run: npm ci && npm run build

      - name: Deploy
        run: echo "Add deployment steps here"
"""

    if template == "advanced":
        return f"""name: Deploy
{trigger_section}
permissions:
  contents: read
  packages: write
  id-token: write

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{{{ github.repository }}}}

jobs:
  test:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - run: npm run lint
      - run: npm test

  build:
    needs: test
    runs-on: self-hosted
    outputs:
      version: ${{{{ steps.version.outputs.version }}}}
    steps:
      - uses: actions/checkout@v4

      - name: Get version
        id: version
        run: echo "version=${{{{ github.ref_name }}}}" >> "$GITHUB_OUTPUT"

      - uses: docker/setup-buildx-action@v3

      - uses: docker/login-action@v3
        with:
          registry: ${{{{ env.REGISTRY }}}}
          username: ${{{{ github.actor }}}}
          password: ${{{{ secrets.GITHUB_TOKEN }}}}

      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: |
            ${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}:latest
            ${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}:${{{{ steps.version.outputs.version }}}}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-staging:
    needs: build
    runs-on: self-hosted
    environment: staging
    steps:
      - name: Deploy to staging
        run: echo "Deploy ${{{{ needs.build.outputs.version }}}} to staging"

  deploy-production:
    needs: [build, deploy-staging]
    runs-on: self-hosted
    environment: production
    if: startsWith(github.ref, 'refs/tags/v')
    steps:
      - name: Deploy to production
        run: echo "Deploy ${{{{ needs.build.outputs.version }}}} to production"
"""

    # standard
    return f"""name: Deploy
{trigger_section}
permissions:
  contents: read
  packages: write

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{{{ github.repository }}}}

jobs:
  build-and-deploy:
    runs-on: self-hosted
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"

      - name: Install dependencies
        run: npm ci

      - name: Run tests
        run: npm test

      - name: Build
        run: npm run build

      - uses: docker/login-action@v3
        if: github.event_name != 'pull_request'
        with:
          registry: ${{{{ env.REGISTRY }}}}
          username: ${{{{ github.actor }}}}
          password: ${{{{ secrets.GITHUB_TOKEN }}}}

      - uses: docker/build-push-action@v5
        if: github.event_name != 'pull_request'
        with:
          context: .
          push: true
          tags: ${{{{ env.REGISTRY }}}}/${{{{ env.IMAGE_NAME }}}}:latest

      - name: Deploy
        if: github.ref == 'refs/heads/main'
        run: echo "Add deployment steps here"
"""


# ---------------------------------------------------------------------------
# File generation orchestrator
# ---------------------------------------------------------------------------


def generate_files(
    project_dir: Path,
    config: dict[str, Any],
    targets: list[str],
    template: str,
) -> dict[str, Any]:
    """Generate all deployment files for specified targets."""
    project_name = config.get("project_name", project_dir.name)
    generated = []
    skipped = []
    errors = []

    def write_file(rel_path: str, content: str) -> None:
        """Write a file, creating parent directories as needed."""
        full_path = project_dir / rel_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        generated.append(rel_path)

    for target in targets:
        try:
            if target == "docker":
                docker_target = config.get("targets", {}).get("docker", {})
                write_file(
                    "Dockerfile",
                    generate_dockerfile(project_name, docker_target, template),
                )
                if template in ("standard", "advanced"):
                    write_file(".dockerignore", generate_dockerignore())
                    write_file(
                        "docker-compose.yml",
                        generate_docker_compose(project_name, docker_target, template),
                    )

            elif target == "k8s":
                k8s_dir = "k8s"
                write_file(
                    f"{k8s_dir}/deployment.yml",
                    generate_k8s_deployment(project_name, config),
                )
                write_file(
                    f"{k8s_dir}/service.yml",
                    generate_k8s_service(project_name),
                )
                if template in ("standard", "advanced"):
                    write_file(
                        f"{k8s_dir}/ingress.yml",
                        generate_k8s_ingress(project_name),
                    )

            elif target == "ci":
                write_file(
                    ".github/workflows/deploy.yml",
                    generate_github_actions_deploy(project_name, config, template),
                )

        except Exception as e:
            errors.append({"target": target, "error": str(e)})

    return {
        "generated": generated,
        "generated_count": len(generated),
        "skipped": skipped,
        "skipped_count": len(skipped),
        "errors": errors,
        "error_count": len(errors),
        "template": template,
    }


# ---------------------------------------------------------------------------
# CLI entrypoint
# ---------------------------------------------------------------------------


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate deployment infrastructure files"
    )
    parser.add_argument("--dir", default=".", help="Project directory")
    parser.add_argument(
        "--action",
        required=True,
        choices=["load-config", "generate"],
        help="Action to perform",
    )
    parser.add_argument(
        "--targets",
        help="Comma-separated list of targets (docker,ci,k8s,npm,pypi,vercel,netlify)",
    )
    parser.add_argument(
        "--template",
        default="standard",
        choices=["minimal", "standard", "advanced"],
        help="Template complexity level",
    )
    args = parser.parse_args()

    project_dir = Path(args.dir).resolve()

    if not project_dir.exists():
        print(
            json.dumps({"error": f"Directory not found: {project_dir}"}, indent=2),
            file=sys.stderr,
        )
        return 1

    if args.action == "load-config":
        result = load_deploy_config(project_dir)
        if result["success"]:
            existing = detect_existing_files(project_dir, result["enabled_targets"])
            result["existing_files"] = existing

        report = {
            "operation": "load_deploy_config",
            "directory": str(project_dir),
            "timestamp": datetime.now().isoformat(),
            **result,
        }
        print(json.dumps(report, indent=2))
        return 0 if result["success"] else 1

    elif args.action == "generate":
        # Load config first
        config_result = load_deploy_config(project_dir)
        if not config_result["success"]:
            print(
                json.dumps(
                    {
                        "operation": "generate_deploy_files",
                        "success": False,
                        "error": config_result["error"],
                    },
                    indent=2,
                ),
                file=sys.stderr,
            )
            return 1

        config = config_result["config"]

        # Determine targets
        if args.targets:
            targets = [t.strip() for t in args.targets.split(",") if t.strip()]
        else:
            targets = config_result["enabled_targets"]
            # Always include CI if configured
            if config.get("ci", {}).get("provider"):
                targets.append("ci")

        result = generate_files(project_dir, config, targets, args.template)

        report = {
            "operation": "generate_deploy_files",
            "success": result["error_count"] == 0,
            "directory": str(project_dir),
            "project_name": config.get("project_name"),
            "timestamp": datetime.now().isoformat(),
            **result,
        }
        print(json.dumps(report, indent=2))
        return 0 if result["error_count"] == 0 else 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
