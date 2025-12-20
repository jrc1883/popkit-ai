# Deployment Targets

## Docker (Universal)

Any server/cloud that runs containers. Most flexible option.

**Generated:**
- `Dockerfile` (multi-stage, optimized)
- `docker-compose.yml` (dev environment)
- `.dockerignore`
- `.github/workflows/docker-publish.yml`

**Execution:**
- Build image locally or trigger CI
- Push to registry (Docker Hub, GHCR, ECR)
- Optionally deploy to cloud

---

## Vercel/Netlify (Frontend)

Static sites, SSR apps, serverless functions.

**Generated:**
- `vercel.json` or `netlify.toml`
- Environment variable templates
- `.github/workflows/preview-deploy.yml`

**Execution:**
- Trigger deployment via CLI
- Handle preview deployments for PRs
- Production deploy on main branch

---

## npm/PyPI (Packages)

Library/package publishing.

**Generated:**
- Validates `package.json` / `pyproject.toml`
- `.github/workflows/npm-publish.yml` or `pypi-publish.yml`
- Auth config templates

**Execution:**
- Version bump assistance
- Changelog generation
- Registry publish

---

## GitHub Releases (Binaries)

CLI tools, compiled artifacts.

**Generated:**
- `.github/workflows/release.yml`
- Release asset configuration
- Changelog automation

**Execution:**
- Create GitHub release
- Upload compiled assets
- Generate release notes
