# Cloudflare Pages Deployment Setup

Complete guide for deploying PopKit documentation to Cloudflare Pages with custom domain (`popkit.unjoe.me`).

**Related**: Issue #97 - Documentation Website Implementation
**Workflow**: `.github/workflows/deploy-docs.yml`

---

## Overview

This setup uses:
- **GitHub Actions** for CI/CD automation
- **Cloudflare Pages** for hosting
- **Custom domain**: `popkit.unjoe.me`
- **Automatic deployments** on push to `main`
- **Preview deployments** for pull requests

---

## Prerequisites

- [x] Cloudflare account with unjoe.me domain
- [x] GitHub repository: jrc1883/popkit-claude
- [x] Admin access to both platforms

---

## Step 1: Create Cloudflare Pages Project

### 1.1 Create the Project

1. Go to **Cloudflare Dashboard**: https://dash.cloudflare.com/
2. Navigate to **Workers & Pages** in the left sidebar
3. Click **Create application** → **Pages** tab
4. Click **Create project** → **Direct Upload** (we'll use GitHub Actions, not Git integration)
5. Project name: **`popkit-docs`** (must match workflow file)
6. Click **Create project**

**Important**: Use "Direct Upload" method, NOT "Connect to Git". The GitHub Actions workflow will handle uploads.

### 1.2 Note Your Project Details

After creation, you'll see:
- Project name: `popkit-docs`
- Project URL: `https://popkit-docs.pages.dev`

Keep this tab open for the next step.

---

## Step 2: Get Cloudflare Credentials

### 2.1 Get Account ID

1. In Cloudflare Dashboard, go to **Workers & Pages**
2. Click on your **popkit-docs** project
3. Go to **Settings** tab
4. Scroll to **API** section
5. Copy your **Account ID** (looks like: `abc123def456ghi789jkl012mno345pq`)

**Save this**: You'll need it for GitHub secrets.

### 2.2 Create API Token

1. Go to **My Profile** (top right) → **API Tokens**
2. Click **Create Token**
3. Use template: **Edit Cloudflare Workers** (or create custom token)
4. Configure permissions:
   ```
   Account Resources:
   - Cloudflare Pages: Edit
   ```
5. Set **Account Resources**: Choose your account
6. Set **Zone Resources**: (Optional, can leave as default)
7. **Client IP Address Filtering**: (Optional, leave blank for GitHub Actions IPs)
8. Click **Continue to summary**
9. Click **Create Token**
10. **IMPORTANT**: Copy the token immediately (shown only once!)

**Token looks like**: `abc123-XyZ789-def456-GhI012-jkl345`

**Save this securely**: You'll need it for GitHub secrets.

---

## Step 3: Configure GitHub Secrets

### 3.1 Add Secrets to Repository

1. Go to GitHub repository: https://github.com/jrc1883/popkit-claude
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**

**Add these two secrets**:

#### Secret 1: CLOUDFLARE_API_TOKEN
- **Name**: `CLOUDFLARE_API_TOKEN`
- **Value**: Paste the API token from Step 2.2
- Click **Add secret**

#### Secret 2: CLOUDFLARE_ACCOUNT_ID
- **Name**: `CLOUDFLARE_ACCOUNT_ID`
- **Value**: Paste the Account ID from Step 2.1
- Click **Add secret**

### 3.2 Verify Secrets

After adding, you should see:
- ✅ `CLOUDFLARE_API_TOKEN`
- ✅ `CLOUDFLARE_ACCOUNT_ID`
- ✅ `GITHUB_TOKEN` (automatically available, no setup needed)

---

## Step 4: Configure Custom Domain

### 4.1 Add Custom Domain to Cloudflare Pages

1. In Cloudflare Dashboard → **Workers & Pages** → **popkit-docs**
2. Go to **Custom domains** tab
3. Click **Set up a custom domain**
4. Enter: `popkit.unjoe.me`
5. Click **Continue**

### 4.2 Verify DNS Configuration

Since `unjoe.me` is already in your Cloudflare account, the DNS record will be created automatically:

**Type**: CNAME
**Name**: `popkit`
**Target**: `popkit-docs.pages.dev`
**Proxy status**: Proxied (orange cloud)

Cloudflare will automatically:
- Create the DNS record
- Provision SSL certificate (takes ~1-2 minutes)
- Enable HTTPS

### 4.3 Verify Domain Works

After SSL provisioning completes (~1-2 minutes):
1. Visit: https://popkit.unjoe.me
2. You should see: "Waiting for content" or a 404 page (normal - no content deployed yet)
3. Verify SSL works: 🔒 in browser address bar

---

## Step 5: Test Deployment

### 5.1 Trigger First Deployment

The workflow is already in your repository (`.github/workflows/deploy-docs.yml`).

**Option A: Push to Main** (triggers production deployment)
```bash
cd C:/Users/Josep/popkit-claude
git checkout main
git pull

# Make a small change to trigger deployment
echo "# Setup complete" >> docs/CLOUDFLARE_PAGES_SETUP.md
git add docs/CLOUDFLARE_PAGES_SETUP.md
git commit -m "docs: trigger initial Cloudflare Pages deployment"
git push
```

**Option B: Create a Pull Request** (triggers preview deployment)
```bash
git checkout -b test/docs-deployment
echo "# Test" >> packages/docs/README.md
git add packages/docs/README.md
git commit -m "test: trigger preview deployment"
git push -u origin test/docs-deployment
gh pr create --title "test: trigger preview deployment" --body "Testing Cloudflare Pages preview"
```

### 5.2 Monitor Workflow

1. Go to **Actions** tab in GitHub: https://github.com/jrc1883/popkit-claude/actions
2. Click on the **Deploy Docs** workflow run
3. Watch the build and deployment progress

**Expected output**:
```
✓ Build Documentation (2-3 minutes)
  - Install dependencies
  - Build docs site
  - Verify build output
  - Upload artifact

✓ Deploy to Cloudflare Pages (1-2 minutes)
  - Download artifact
  - Deploy to Cloudflare
  - Summary
```

### 5.3 Verify Deployment

After workflow completes:

1. **Production URL**: https://popkit.unjoe.me
2. **Cloudflare Pages URL**: https://popkit-docs.pages.dev

Both should show the PopKit documentation site with:
- ✅ Homepage loads
- ✅ Navigation sidebar
- ✅ Search functionality
- ✅ All 18 pages accessible
- ✅ XML Prompts Guide
- ✅ Commands Reference

---

## Step 6: Verify Automatic Deployments

### 6.1 Test Production Deployment

1. Make a change to documentation:
   ```bash
   # Edit any doc file
   echo "# Test update" >> packages/docs/src/content/docs/index.mdx
   git add packages/docs/src/content/docs/index.mdx
   git commit -m "docs: test automatic deployment"
   git push
   ```

2. Workflow triggers automatically (check Actions tab)
3. Changes appear on https://popkit.unjoe.me within 3-5 minutes

### 6.2 Test Preview Deployment

1. Create a PR with documentation changes
2. Workflow triggers automatically
3. Bot comments on PR with preview URL
4. Preview URL looks like: `https://<commit-hash>.popkit-docs.pages.dev`
5. Verify preview shows your changes

---

## Workflow Details

### Triggers

**Production Deployment** (to popkit.unjoe.me):
- Push to `main` branch
- Only when these paths change:
  - `packages/docs/**`
  - `package.json`
  - `package-lock.json`
  - `.github/workflows/deploy-docs.yml`

**Preview Deployment** (temporary URL):
- Pull requests to `main`
- Same path filters as production

### Build Process

1. **Install dependencies**: `npm ci` (from root, respects workspaces)
2. **Build docs**: `npm run docs:build` (workspace script)
3. **Verify output**: Check `packages/docs/dist` exists
4. **Upload artifact**: Save for deployment job

### Deployment Process

1. **Download artifact**: Get build output from build job
2. **Deploy to Cloudflare Pages**: Use `cloudflare/wrangler-action@v3` with `pages deploy` command
3. **Comment on PR**: (Preview only) Add preview URL to PR
4. **Summary**: Add deployment details to workflow summary

**Note**: The official `cloudflare/pages-action` is now deprecated. We use `wrangler-action@v3` which is the recommended approach from Cloudflare.

---

## Troubleshooting

### Error: "Missing CLOUDFLARE_API_TOKEN secret"

**Solution**: Complete Step 3.1 to add the secret.

### Error: "Project not found: popkit-docs"

**Solution**: Complete Step 1.1 to create the Cloudflare Pages project with exact name `popkit-docs`.

### Error: "Invalid API token"

**Solution**: Verify token permissions in Step 2.2. Must have **Cloudflare Pages: Edit** permission.

### Error: "Domain already exists"

**Solution**:
1. Check if `popkit.unjoe.me` is configured for another project
2. In Cloudflare Dashboard → DNS, remove existing `popkit` CNAME record
3. Re-add in Step 4

### Build fails with "Module not found"

**Solution**:
1. Verify `package.json` workspaces configuration
2. Try local build: `npm ci && npm run docs:build`
3. Check for missing dependencies

### Deployment succeeds but site shows 404

**Solution**:
1. Verify build output: Check workflow logs for `packages/docs/dist` contents
2. Ensure `index.html` exists in build artifact
3. Check Cloudflare Pages project → Deployments → View deployment

### Custom domain not working

**Solution**:
1. Verify DNS: Check Cloudflare → DNS → Records for `popkit` CNAME
2. Wait for SSL: Certificate provisioning takes 1-2 minutes
3. Clear browser cache: Hard refresh (Ctrl+Shift+R)
4. Check Cloudflare Pages → Custom domains → Status

---

## Commands Reference

### Local Development
```bash
# Run development server
npm run docs:dev

# Build for production
npm run docs:build

# Preview production build
npm run docs:preview
```

### Manual Deployment (if workflow fails)
```bash
# Install Wrangler CLI (Cloudflare's deployment tool)
npm install -g wrangler

# Login to Cloudflare
wrangler login

# Build docs
npm run docs:build

# Deploy manually
cd packages/docs
wrangler pages publish dist --project-name=popkit-docs
```

### Workflow Management
```bash
# View workflow runs
gh run list --workflow=deploy-docs.yml

# View specific run
gh run view <run-id>

# Re-run failed workflow
gh run rerun <run-id>

# Cancel running workflow
gh run cancel <run-id>
```

---

## Monitoring & Analytics

### Cloudflare Pages Dashboard

View deployment history and analytics:
1. Cloudflare Dashboard → Workers & Pages → popkit-docs
2. **Deployments** tab: View all deployments
3. **Analytics** tab: Traffic, requests, bandwidth
4. **Functions** tab: (Not used - static site only)
5. **Settings** tab: Configuration

### GitHub Actions

View workflow runs:
1. GitHub → Actions → Deploy Docs workflow
2. Click on specific run for detailed logs
3. View deployment summary in workflow output

---

## Security Best Practices

### API Token Security

- ✅ **DO**: Store API token in GitHub Secrets
- ✅ **DO**: Use minimal required permissions (Pages: Edit only)
- ✅ **DO**: Rotate token periodically (every 90 days)
- ❌ **DON'T**: Commit API token to repository
- ❌ **DON'T**: Share API token in logs or public channels
- ❌ **DON'T**: Use tokens with excessive permissions

### Deployment Security

- ✅ **DO**: Use branch protection on `main`
- ✅ **DO**: Require PR reviews before merging
- ✅ **DO**: Enable concurrency cancellation (prevents conflicts)
- ✅ **DO**: Verify build output before deployment
- ❌ **DON'T**: Deploy untrusted code
- ❌ **DON'T**: Disable SSL/HTTPS

---

## Maintenance

### Update Workflow

To modify the deployment workflow:
1. Edit `.github/workflows/deploy-docs.yml`
2. Test changes in a PR (triggers preview deployment)
3. Merge to `main` after verification

### Update Dependencies

Periodically update Astro and Starlight:
```bash
cd packages/docs
npm update @astrojs/starlight astro
npm audit fix
npm run docs:build  # Test build
```

### Rotate API Token

Every 90 days:
1. Create new API token (Step 2.2)
2. Update GitHub secret `CLOUDFLARE_API_TOKEN`
3. Revoke old token in Cloudflare Dashboard

---

## Additional Resources

- **Cloudflare Pages Docs**: https://developers.cloudflare.com/pages/
- **GitHub Actions Docs**: https://docs.github.com/en/actions
- **Astro Docs**: https://docs.astro.build/
- **Starlight Docs**: https://starlight.astro.build/

---

## Support

**Issues**: https://github.com/jrc1883/popkit-claude/issues
**Workflow**: `.github/workflows/deploy-docs.yml`
**Related Issue**: #97 - Documentation Website Implementation

---

**Setup complete! 🎉**

Your documentation site will now automatically deploy on every push to `main`.
