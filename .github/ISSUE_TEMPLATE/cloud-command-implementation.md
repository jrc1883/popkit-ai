---
name: Implement /popkit:cloud command
about: User-facing command to manage PopKit Cloud connection
title: "Implement /popkit:cloud command for cloud connection management"
labels: enhancement, P1-high, size:M
---

## Summary

User-facing command to manage PopKit Cloud connection: signup, login, logout, status.

## Context

PopKit Cloud is deployed and fully operational at `api.thehouseofdeals.com`. The backend API works end-to-end:
- ✅ Signup endpoint creates accounts and generates API keys
- ✅ Authentication validates API keys
- ✅ Usage tracking works (100 requests/day free tier)
- ✅ Pattern storage works (collective learning)
- ✅ Redis connected (82ms latency)

**Current State:** Cloud works but users can't connect (no plugin implementation).

**Files Created:**
- `packages/plugin/commands/cloud.md` - Command specification
- `packages/plugin/skills/pop-cloud-signup/SKILL.md` - Signup skill specification
- `CLOUD-STATUS.md` - Architecture documentation
- `CLOUD-VALIDATION.md` - End-to-end validation proof

**Bug Fixed:**
- `packages/plugin/power-mode/cloud_client.py` - URL now points to correct domain

## What Needs Implementation

### 1. /popkit:cloud signup Skill

Implement Python script for `pop-cloud-signup`:

1. Check for existing cloud config
2. Use AskUserQuestion for email/password
3. POST to https://api.thehouseofdeals.com/v1/auth/signup
4. Save API key to .claude/popkit/cloud-config.json (chmod 600)
5. Show environment variable setup instructions
6. Test connection using cloud_client.py
7. Display success summary with tier info

### 2. /popkit:cloud status Implementation

Show cloud connection status with usage metrics

### 3. /popkit:cloud login Implementation

Login to existing account

### 4. /popkit:cloud logout Implementation

Disconnect from cloud

### 5. Status Line Cloud Widget

Add cloud connectivity indicator to status line

## Acceptance Criteria

- [ ] User can run `/popkit:cloud signup` from plugin
- [ ] Signup creates account and returns API key
- [ ] API key saved to `.claude/popkit/cloud-config.json`
- [ ] Instructions shown for setting `POPKIT_API_KEY`
- [ ] `/popkit:cloud status` shows connection status
- [ ] Status line displays cloud connection indicator
- [ ] Power Mode automatically uses cloud when API key set
- [ ] Error handling for network issues, invalid credentials
- [ ] Security: chmod 600 on cloud-config.json, never log passwords

## Estimated Effort

**Implementation:** 2-4 hours
- Signup skill: 1 hour
- Status/login/logout: 1 hour
- Status line widget: 30 min
- Testing: 30 min

**Current Blocker:** None. Cloud is deployed and working.
