# Feature Gating: Pre-Launch Mode

> **⚠️ ARCHITECTURE CHANGE (December 20, 2025)**
>
> This document was created under PopKit's original subscription model (free/pro/team tiers).
> PopKit's architecture has been redesigned to use an **API key enhancement model**:
>
> - All features work FREE locally
> - API key adds semantic intelligence enhancements
> - No subscription tiers or feature gating
>
> **New design:** See Epic #580 and `docs/plans/2025-12-20-plugin-modularization-design.md`
>
> The content below is preserved for reference but may not reflect current architecture.

---

**Date:** 2025-12-12
**Status:** ~~Implemented~~ **DEPRECATED**
**Epic:** #126 (Premium Feature Gating)

## Overview

Pre-launch mode allows PopKit to show "coming soon" messages for premium features instead of directing users to purchase subscriptions. This is useful when premium tiers aren't ready for public launch yet, but you want to collect interested users via email.

## How It Works

### Environment Flag

Set `POPKIT_BILLING_LIVE` to control the mode:

```bash
# Pre-launch mode (default)
export POPKIT_BILLING_LIVE=false

# Live billing mode
export POPKIT_BILLING_LIVE=true
```

### User Flow

#### Pre-Launch Mode (`POPKIT_BILLING_LIVE=false`)

1. User tries to use a premium feature (e.g., `/popkit:project generate`)
2. Hook intercepts and shows:
   ```
   🎉 Coming Soon: Custom MCP Server Generation
      This premium feature is launching soon!
      Required tier: Pro

      Want to be notified at launch? You'll be prompted to enter your email.
   ```
3. Claude shows AskUserQuestion with options:
   - **Continue with free tier** (if fallback available)
   - **Get notified at launch** → Email signup
   - **Cancel**

4. If user selects "Get notified at launch":
   - Prompts for email address in console
   - Validates email format
   - Sends to `/v1/waitlist/signup` API
   - Shows confirmation message

#### Live Billing Mode (`POPKIT_BILLING_LIVE=true`)

1. User tries to use a premium feature
2. Hook shows standard upgrade prompt:
   ```
   ⭐ Premium Feature Required: Custom MCP Server Generation
      Your tier: Free
      Required: Pro

      Run /popkit:upgrade to unlock premium features
   ```
3. User runs `/popkit:upgrade` to purchase subscription

## Implementation Details

### Modified Files

| File | Changes |
|------|---------|
| `packages/plugin/hooks/utils/premium_checker.py` | Added `BILLING_LIVE` flag, `capture_waitlist_email()`, `get_coming_soon_message()` |
| `packages/plugin/hooks/pre-tool-use.py` | Updated premium message output to check billing status |
| `packages/plugin/skills/pop-waitlist-signup/SKILL.md` | New skill for email capture flow |
| `packages/cloud/src/routes/waitlist.ts` | New API endpoint for waitlist signups |
| `packages/cloud/src/index.ts` | Added waitlist routes (public, no auth) |
| `packages/cloud/src/types.ts` | Added `WAITLIST_KV` and `DB` bindings |
| `packages/cloud/wrangler.toml` | Added KV namespace configuration |

### Cloud API Endpoints

#### POST /v1/waitlist/signup (public)

Capture email signup for premium features.

**Request:**
```json
{
  "email": "user@example.com",
  "feature": "pop-mcp-generator",
  "timestamp": "2025-12-12T10:30:00Z",
  "tier": "free"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully added to waitlist",
  "id": "uuid-here"
}
```

#### GET /v1/waitlist/list (auth required)

List all waitlist signups (admin only).

**Response:**
```json
{
  "total": 42,
  "entries": [
    {
      "id": "uuid",
      "email": "user@example.com",
      "feature": "pop-mcp-generator",
      "tier": "free",
      "created_at": "2025-12-12T10:30:00Z",
      "ip_address": "1.2.3.4",
      "user_agent": "curl/8.0.0"
    }
  ]
}
```

#### GET /v1/waitlist/stats (public)

Get waitlist statistics.

**Response:**
```json
{
  "total": 42,
  "by_feature": {
    "pop-mcp-generator": 20,
    "pop-embed-project": 12,
    "pop-power-mode:redis": 10
  },
  "by_tier": {
    "free": 40,
    "pro": 2
  }
}
```

### Data Storage

Waitlist signups are stored in Cloudflare KV:

**Keys:**
- `waitlist:{email}:{feature}` - Individual signup
- `waitlist:all:{timestamp}:{id}` - List index

**Metadata:**
```json
{
  "email": "user@example.com",
  "feature": "pop-mcp-generator",
  "tier": "free",
  "created_at": "2025-12-12T10:30:00Z"
}
```

Optional D1 database for analytics:

```sql
CREATE TABLE waitlist_signups (
  id TEXT PRIMARY KEY,
  email TEXT NOT NULL,
  feature TEXT NOT NULL,
  tier TEXT DEFAULT 'free',
  created_at TEXT NOT NULL,
  ip_address TEXT,
  user_agent TEXT
);

CREATE INDEX idx_email ON waitlist_signups(email);
CREATE INDEX idx_feature ON waitlist_signups(feature);
CREATE INDEX idx_created_at ON waitlist_signups(created_at);
```

## Testing

### Test Pre-Launch Mode

```bash
# Set pre-launch mode
export POPKIT_BILLING_LIVE=false

# Try a premium feature
# In Claude Code:
/popkit:project generate

# Should see "Coming Soon" message
# Select "Get notified at launch"
# Enter email: test@example.com
```

### Test Email Capture

```bash
# Direct API call
curl -X POST https://popkit-cloud-api.joseph-cannon.workers.dev/v1/waitlist/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "feature": "pop-mcp-generator",
    "timestamp": "2025-12-12T10:30:00Z",
    "tier": "free"
  }'

# Check stats
curl https://popkit-cloud-api.joseph-cannon.workers.dev/v1/waitlist/stats
```

### Test Premium Checker Utility

```bash
# Check billing status
python3 packages/plugin/hooks/utils/premium_checker.py billing-status

# Test waitlist capture
python3 packages/plugin/hooks/utils/premium_checker.py waitlist test@example.com pop-mcp-generator
```

## Deployment

### 1. Create KV Namespace

```bash
cd packages/cloud
wrangler kv:namespace create "WAITLIST_KV"

# Update wrangler.toml with the returned ID
```

### 2. (Optional) Create D1 Database

```bash
wrangler d1 create popkit-db
wrangler d1 execute popkit-db --command "CREATE TABLE waitlist_signups (...)"

# Update wrangler.toml with database ID
```

### 3. Deploy Cloud API

```bash
cd packages/cloud
npm run deploy
```

### 4. Test Endpoints

```bash
# Health check
curl https://popkit-cloud-api.joseph-cannon.workers.dev/v1/health

# Waitlist stats
curl https://popkit-cloud-api.joseph-cannon.workers.dev/v1/waitlist/stats
```

## Switching to Live Billing

When ready to launch premium tiers:

1. **Set environment variable:**
   ```bash
   export POPKIT_BILLING_LIVE=true
   ```

2. **Restart Claude Code** to pick up new env var

3. **Verify upgrade flow:**
   - Try premium feature
   - Should see "Upgrade to Premium" message
   - `/popkit:upgrade` should work

4. **Export waitlist:**
   ```bash
   curl -H "Authorization: Bearer your-admin-key" \
     https://popkit-cloud-api.joseph-cannon.workers.dev/v1/waitlist/list > waitlist.json
   ```

5. **Send launch emails** to all waitlist subscribers

## Privacy & Compliance

- Emails are stored in Cloudflare KV (encrypted at rest)
- No third-party sharing
- Used only for launch notifications
- Users can request deletion via email
- GDPR/CCPA compliant

## Future Enhancements

- [ ] Email verification (send confirmation link)
- [ ] Unsubscribe mechanism
- [ ] Automated launch email via Resend API
- [ ] A/B test different messaging
- [ ] Track conversion rate (waitlist → paid)

## Related

- Epic #126 - Premium Feature Gating
- Epic #125 - User Signup & Billing
- Issue #130 - Stripe Integration
- Issue #133 - Email Service (Resend)
