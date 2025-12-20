# Deploy Setup Examples

## Basic Usage

```bash
/popkit:deploy setup                    # Interactive setup for all targets
/popkit:deploy setup docker             # Setup Docker specifically
/popkit:deploy setup vercel             # Setup Vercel specifically
/popkit:deploy setup netlify            # Setup Netlify specifically
/popkit:deploy setup npm                # Setup npm publishing
/popkit:deploy setup pypi               # Setup PyPI publishing
/popkit:deploy setup github-releases    # Setup GitHub Releases
/popkit:deploy setup --all              # Setup all configured targets
```

## Files Generated Per Target

| Target | Files Generated |
|--------|-----------------|
| Docker | `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.github/workflows/docker-publish.yml` |
| Vercel | `vercel.json`, `.github/workflows/preview-deploy.yml` |
| Netlify | `netlify.toml`, `.github/workflows/netlify-deploy.yml` |
| npm | Validates `package.json`, `.github/workflows/npm-publish.yml`, `.npmrc` template |
| PyPI | Validates `pyproject.toml`, `.github/workflows/pypi-publish.yml` |
| GitHub Releases | `.github/workflows/release.yml`, asset configuration |

## Setup Process

1. **Load Configuration**
   - Read `deploy.json` for targets and project type
   - Verify GitHub connection

2. **Generate Files**
   - Create Dockerfile (multi-stage, optimized for project type)
   - Create CI/CD workflow for target
   - Configure environment variables

3. **Optionally Commit**
   - Offer to commit generated files
   - Or let user review first

## Sample Output

```
/popkit:deploy setup docker

Setting up Docker deployment...

[1/4] Analyzing project for Dockerfile generation...
      ✓ Detected: Node.js 20 with Next.js 14
      ✓ Build command: npm run build
      ✓ Start command: npm start
      ✓ Port: 3000

[2/4] Generating Dockerfile...
      ✓ Multi-stage build (builder + runner)
      ✓ Optimized layer caching
      ✓ Non-root user for security
      → Dockerfile created

[3/4] Generating docker-compose.yml...
      ✓ Dev environment config
      ✓ Volume mounts for hot reload
      → docker-compose.yml created

[4/4] Generating CI/CD workflow...
      ✓ Build on push to main
      ✓ Push to ghcr.io
      → .github/workflows/docker-publish.yml created

Files created:
  - Dockerfile (multi-stage, 3 stages)
  - docker-compose.yml (dev environment)
  - .dockerignore
  - .github/workflows/docker-publish.yml

Would you like to commit these files?
```

## Template Levels

| Template | Included |
|----------|----------|
| `minimal` | Basic Dockerfile, no CI |
| `standard` | Dockerfile + CI/CD workflow |
| `production` | Standard + caching, security scanning, multi-registry |
