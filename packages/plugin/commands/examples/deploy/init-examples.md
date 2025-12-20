# Deploy Init Examples

## Basic Usage

```bash
/popkit:deploy                          # Auto-runs init if unconfigured
/popkit:deploy init                     # Explicit init
/popkit:deploy init --force             # Re-analyze even if configured
```

## Initialization Process

1. **Check PopKit Initialization**
   - Verify `.claude/popkit/` exists
   - Verify CLAUDE.md has PopKit markers
   - Offer to fix gaps if found

2. **Front-load User Intent** (using AskUserQuestion with multiple questions)

   ```
   Questions:
   [1] "What type of project are you deploying?" [header: "Project"]
       Options:
       - Web application (frontend/fullstack/SSR)
       - Backend API/service
       - CLI tool or library

   [2] "Where do you want to deploy?" [header: "Targets", multiSelect: true]
       Options:
       - Docker (universal - any server/cloud)
       - Vercel/Netlify (frontend hosting)
       - npm/PyPI registry (package publishing)
       - GitHub Releases (binary artifacts)

   [3] "What's your current deployment setup?" [header: "State"]
       Options:
       - Starting fresh (no GitHub, no CI/CD)
       - Have GitHub, need CI/CD
       - Have CI/CD, need target config
       - Everything exists (just orchestrate)
   ```

3. **Store Configuration**
   ```json
   // .claude/popkit/deploy.json
   {
     "version": "1.0",
     "project_type": "web-app",
     "targets": ["docker", "vercel"],
     "state": "needs-cicd",
     "initialized_at": "2025-12-10T...",
     "initialized_by": "popkit-1.2.0",
     "github": {
       "repo": "owner/repo",
       "default_branch": "main",
       "has_actions": true
     },
     "history": []
   }
   ```

## Sample Output

```
PopKit Deployment Initialization
═════════════════════════════════

[1/3] Checking PopKit prerequisites...
      ✓ .claude/popkit/ exists
      ✓ CLAUDE.md has PopKit markers
      ✓ settings.json has PopKit fields

[2/3] Detecting current state...
      ✓ GitHub repository: owner/repo
      ✓ GitHub Actions: detected
      ⚠️ Docker: not configured
      ⚠️ Vercel: not configured

[3/3] Saving configuration...
      ✓ .claude/popkit/deploy.json created

Configuration:
  Project Type: web-app
  Targets: docker, vercel
  State: has-github-needs-cicd

Next Steps:
  Run /popkit:deploy setup docker    → Generate Dockerfile & CI
  Run /popkit:deploy setup vercel    → Configure Vercel deployment
```
