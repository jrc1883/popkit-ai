---
name: deploy-netlify
description: "Use when deploying to Netlify - generates netlify.toml, preview deployment workflows, and environment variable templates. Handles Next.js, Nuxt, Astro, and static sites with automatic framework detection and Netlify Functions support."
---

# Netlify Deployment Setup

## Overview

Configure Netlify deployment for frontend applications. Generates production-ready `netlify.toml`, preview deployment workflows, and environment management.

**Core principle:** Convention over configuration, with escape hatches when needed.

## Critical Rules

| Rule | Details |
|------|---------|
| **ALWAYS detect framework first** | Netlify has framework-specific build plugins |
| **Use deploy previews for PRs** | Automatic with Netlify, add custom workflows |
| **Separate contexts** | Production, deploy-preview, branch-deploy |
| **Use Netlify Functions** | For serverless API routes |
| **Edge Functions for performance** | When latency matters |

## Process

### Step 1: Detect Framework

Run detection script to identify project framework and optimal settings.

**Detects:** Next.js, Nuxt, SvelteKit, Astro, Gatsby, Remix, Vite, Create React App, Angular, Vue CLI, Hugo, Jekyll, MkDocs, Docusaurus, or static site

[See detection script](examples/netlify/detect-framework.py)

### Step 2: Ask About Configuration

```
Use AskUserQuestion tool with:
- question: "Detected [framework]. Configure Netlify settings?"
- header: "Netlify Config"
- options:
  - label: "Default settings (Recommended)"
    description: "Use Netlify's automatic detection with sensible defaults"
  - label: "With Netlify Functions"
    description: "Include serverless function support"
  - label: "With Edge Functions"
    description: "Include edge function support for low latency"
- multiSelect: false
```

### Step 3: Generate Files

| File | Purpose |
|------|---------|
| `netlify.toml` | Build configuration and deployment settings |
| `.github/workflows/netlify-preview.yml` | Preview deployments for PRs |
| `.github/workflows/netlify-production.yml` | Production deployments on main |
| `docs/NETLIFY_SETUP.md` | Environment variable setup guide |

## netlify.toml Templates

[See framework-specific templates](examples/netlify/toml-templates/):
- **Next.js** - With @netlify/plugin-nextjs runtime
- **Vite** - SPA fallback, asset caching
- **Astro** - SSR adapter support
- **Static** - Hugo/Jekyll with pretty URLs
- **Functions** - Serverless function routing
- **Edge** - Edge function middleware

All templates include:
- Build command and publish directory
- Context-specific environments (production, preview)
- Security headers (X-Frame-Options, CSP)
- Asset caching headers
- SPA fallback redirects (where applicable)

## GitHub Actions Workflows

[See workflow templates](examples/netlify/workflows/):
- `netlify-preview.yml` - Deploy previews for PRs with comment
- `netlify-production.yml` - Production deploy on main branch

Both workflows use `nwtgck/actions-netlify@v3` with proper caching and environment separation.

## Netlify Functions

[See function examples](examples/netlify/functions/):
- `hello.ts` - Basic serverless function
- `api-handler.ts` - API endpoint with validation
- `edge-middleware.ts` - Edge function with headers

**Function configuration:**
- Directory: `netlify/functions/`
- Bundler: esbuild (faster than webpack)
- Runtime: Node.js 20.x

## Environment Variables

[See setup guide](examples/netlify/env-setup.md)

### Required GitHub Secrets

| Secret | Description | How to Get |
|--------|-------------|------------|
| `NETLIFY_AUTH_TOKEN` | Personal access token | netlify.com/user/applications |
| `NETLIFY_SITE_ID` | Site ID | Dashboard → Site Settings → General |

### Netlify Dashboard Variables

Configure in Dashboard → Site Settings → Environment Variables:

| Variable | Contexts | Example |
|----------|----------|---------|
| `DATABASE_URL` | Production | Production database |
| `DATABASE_URL` | Deploy previews | Staging database |
| `API_SECRET` | All | Shared API secret |

**Contexts:** production, deploy-preview, branch-deploy, dev

## Output Format

```
Netlify Deployment Setup
════════════════════════

[1/4] Detecting framework...
      ✓ Detected: Vite + React
      ✓ Build: npm run build → dist

[2/4] Generating netlify.toml...
      ✓ SPA fallback redirect
      ✓ Security headers
      ✓ Asset caching
      → netlify.toml

[3/4] Generating workflows...
      → .github/workflows/netlify-preview.yml
      → .github/workflows/netlify-production.yml

[4/4] Env template...
      → docs/NETLIFY_SETUP.md

Required Secrets:
  NETLIFY_AUTH_TOKEN
  NETLIFY_SITE_ID

Quick Commands:
  netlify link         # Connect to site
  netlify dev          # Local development
  netlify deploy       # Preview deploy

Would you like to commit these files?
```

## Verification Checklist

| Check | Command |
|-------|---------|
| TOML valid | `netlify build --dry` |
| CLI linked | `netlify status` |
| Local dev works | `netlify dev` |
| Build succeeds | `netlify build` |
| Deploy works | `netlify deploy` |

## Integration

**Command:** `/popkit:deploy setup netlify`
**Agent:** `devops-automator`
**Followed by:**
- `/popkit:deploy validate` - Pre-deployment checks
- `/popkit:deploy execute netlify` - Trigger deployment

## Related Skills

| Skill | Relationship |
|-------|--------------|
| `pop-deploy-init` | Run first to configure targets |
| `pop-deploy-vercel` | Alternative frontend hosting |
| `pop-deploy-docker` | For containerized deployments |
