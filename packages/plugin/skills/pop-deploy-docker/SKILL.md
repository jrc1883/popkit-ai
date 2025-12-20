---
name: deploy-docker
description: "Use when containerizing applications with Docker - generates optimized Dockerfiles for Node.js, Python, Go, and Rust, includes multi-stage builds, and creates docker-compose.yml. Supports GitHub Actions for automated builds and push to registries."
---

# Docker Containerization

## Overview

Generate optimized Docker configurations for applications with multi-stage builds, minimal attack surface, and production-ready setups.

**Core principle:** Secure, minimal, and reproducible container images.

## Critical Rules

| Rule | Details |
|------|---------|
| **ALWAYS use multi-stage builds** | Minimize final image size and attack surface |
| **NEVER include secrets in images** | Use build args or runtime env vars |
| **Use specific base image tags** | Never use `latest` - pin versions |
| **Include .dockerignore** | Exclude dev files and secrets |
| **Run as non-root user** | Security best practice |

## Process

### Step 1: Detect Project Type

Analyze project to determine appropriate base image and build strategy.

**Detects:** Node.js (package.json), Python (requirements.txt/pyproject.toml), Go (go.mod), Rust (Cargo.toml), Next.js (next.config.js)

[See detection script](examples/docker/detect_project.py)

### Step 2: Generate Dockerfile

Create multi-stage Dockerfile optimized for detected project type.

**Stages:** Builder (compile/build) → Production (minimal runtime)

### Step 3: Write Files

| File | Purpose |
|------|---------|
| `Dockerfile` | Multi-stage build configuration |
| `docker-compose.yml` | Local development setup |
| `.dockerignore` | Exclude dev files from build context |
| `.github/workflows/docker-publish.yml` | Automated build and push |

## Dockerfile Templates

[See templates](examples/docker/dockerfiles/):
- **Node.js** - Express/API with alpine base (Node 20)
- **Next.js** - Standalone output optimization
- **Python** - FastAPI/Flask with slim base (Python 3.12)
- **Go** - Multi-stage with scratch final image
- **Rust** - Multi-stage with distroless final image

All templates include:
- Multi-stage builds
- Non-root user execution
- Health checks
- Optimized layer caching

## Docker Compose Template

[See docker-compose.yml example](examples/docker/docker-compose.yml)

Includes:
- Application service
- Database service (PostgreSQL/MongoDB)
- Redis cache (optional)
- Volume mounts for development
- Network configuration

## .dockerignore Template

[See .dockerignore example](examples/docker/dockerignore)

Excludes:
- `node_modules`, `.git`, `.env`
- Test files, documentation
- Build artifacts
- Development-only files

## GitHub Actions Workflow

[See workflow](examples/docker/docker-publish.yml)

Features:
- Build on push to main
- Push to Docker Hub / GHCR
- Multi-platform builds (amd64, arm64)
- Automatic versioning from git tags
- Security scanning with Trivy

## Output Format

```
Docker Containerization Setup
══════════════════════════════

[1/3] Detecting project type...
      ✓ Detected: Node.js (Express)
      ✓ Base image: node:20-alpine

[2/3] Generating Dockerfile...
      ✓ Multi-stage build
      ✓ Production size: ~50MB
      ✓ Non-root user: node

[3/3] Generating support files...
      → Dockerfile
      → docker-compose.yml
      → .dockerignore
      → .github/workflows/docker-publish.yml

Next Steps:
1. Build: docker build -t my-app .
2. Run: docker-compose up
3. Test: docker run --rm my-app

Would you like to commit these files?
```

## Verification Checklist

| Check | Command |
|-------|---------|
| Build succeeds | `docker build -t test .` |
| Image size reasonable | `docker images test` |
| Container runs | `docker run --rm test` |
| Health check works | `docker inspect test` |
| No secrets in image | `docker history test` |

## Integration

**Command:** `/popkit:deploy setup docker`
**Agent:** `devops-automator`
**Followed by:**
- `/popkit:deploy validate` - Test build and run
- `/popkit:deploy execute docker` - Push to registry

## Related Skills

| Skill | Relationship |
|-------|--------------|
| `pop-deploy-init` | Run first to configure targets |
| `pop-deploy-github-releases` | For multi-platform binaries |
