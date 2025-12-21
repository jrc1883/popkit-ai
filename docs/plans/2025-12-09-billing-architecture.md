# User Signup & Billing Architecture

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

**Date:** 2025-12-09
**Epic:** #125
**Status:** ~~Design~~ **DEPRECATED**

---

## Executive Summary

Design a billing system that allows PopKit plugin users to upgrade from free to premium via a seamless flow: plugin command → browser signup → Stripe checkout → API key → premium features.

## Current State

### Already Built
- ✅ Cloud API (Hono on Cloudflare Workers)
- ✅ Auth middleware with API key validation (`pk_live_xxx`)
- ✅ API key creation with tier support (`free`, `pro`, `team`)
- ✅ Redis storage for keys and user data
- ✅ Rate limiting middleware

### Missing
- ❌ User signup flow (email, password)
- ❌ Stripe integration (checkout, webhooks)
- ❌ `/popkit:upgrade` command
- ❌ `/popkit:account` command
- ❌ Landing page (popkit.dev)
- ❌ Email notifications

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  Plugin (Claude Code)                                               │
│  ├── /popkit:upgrade → Opens browser to signup page                 │
│  ├── /popkit:account → Shows tier, usage, billing portal link       │
│  └── POPKIT_API_KEY env var → Validates against cloud API           │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│  Landing Page (Cloudflare Pages - popkit.dev)                       │
│  ├── / → Marketing page                                             │
│  ├── /signup → Email + password form                                │
│  ├── /login → Existing user login                                   │
│  ├── /checkout?plan=pro → Stripe Checkout redirect                  │
│  ├── /success → Show API key after payment                          │
│  └── /portal → Stripe Customer Portal redirect                      │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│  Cloud API (Cloudflare Workers)                                     │
│  ├── POST /v1/auth/signup → Create user account                     │
│  ├── POST /v1/auth/login → Authenticate, return session             │
│  ├── POST /v1/billing/checkout → Create Stripe Checkout Session     │
│  ├── POST /v1/billing/webhook → Handle Stripe webhooks              │
│  ├── GET /v1/billing/portal → Generate billing portal URL           │
│  ├── GET /v1/account → Get user account info + API keys             │
│  └── POST /v1/account/keys → Generate new API key                   │
└─────────────────────────────────────────────────────────────────────┘
                                    ↓
┌─────────────────────────────────────────────────────────────────────┐
│  External Services                                                  │
│  ├── Upstash Redis → User data, API keys, sessions                  │
│  ├── Stripe → Checkout, subscriptions, webhooks                     │
│  └── Resend/SendGrid → Transactional emails                         │
└─────────────────────────────────────────────────────────────────────┘
```

## Data Models

### User Account (Redis Hash: `popkit:user:{userId}`)
```json
{
  "id": "usr_abc123",
  "email": "user@example.com",
  "passwordHash": "argon2id$...",
  "name": "John Doe",
  "tier": "pro",
  "stripeCustomerId": "cus_xxx",
  "stripeSubscriptionId": "sub_xxx",
  "createdAt": "2025-12-09T00:00:00Z",
  "updatedAt": "2025-12-09T00:00:00Z"
}
```

### API Key (Redis Hash: `popkit:keys`)
```json
{
  "pk_live_xxx": {
    "id": "key_abc123",
    "userId": "usr_abc123",
    "tier": "pro",
    "name": "Default Key",
    "createdAt": "2025-12-09T00:00:00Z",
    "lastUsedAt": "2025-12-09T00:00:00Z"
  }
}
```

### Session (Redis String: `popkit:session:{sessionId}`)
```json
{
  "userId": "usr_abc123",
  "createdAt": "2025-12-09T00:00:00Z",
  "expiresAt": "2025-12-16T00:00:00Z"
}
```

## User Flows

### Flow 1: New User Signup

```
1. User runs premium command without API key
2. Plugin shows upgrade prompt (AskUserQuestion)
3. User selects "Upgrade to Premium"
4. Plugin runs: open https://popkit.dev/signup
5. User enters email + password
6. Landing page creates account via POST /v1/auth/signup
7. User is redirected to Stripe Checkout
8. After payment, Stripe webhook updates user tier
9. Landing page shows API key
10. User sets POPKIT_API_KEY in environment
11. Premium features unlocked
```

### Flow 2: Existing User Login

```
1. User visits popkit.dev/login
2. Enters email + password
3. Landing page authenticates via POST /v1/auth/login
4. User sees dashboard with API keys
5. Can generate new keys, view usage, manage billing
```

### Flow 3: Billing Management

```
1. User runs /popkit:account
2. Plugin shows current tier, usage stats
3. User selects "Manage Billing"
4. Plugin runs: open {billing_portal_url}
5. User manages subscription in Stripe Portal
```

## Pricing Tiers

| Tier | Price | Features |
|------|-------|----------|
| **Free** | $0/mo | Core workflows, file-based Power Mode, basic commands |
| **Pro** | $9/mo | + Custom MCP/skills, hosted Redis, pattern sharing, dashboard |
| **Team** | $29/mo | + Team coordination, analytics, priority support |

## API Endpoints to Build

### Auth Routes (`/v1/auth/*`)

| Method | Path | Description |
|--------|------|-------------|
| POST | /signup | Create user account |
| POST | /login | Authenticate user |
| POST | /logout | Invalidate session |
| POST | /forgot-password | Send reset email |
| POST | /reset-password | Reset password with token |

### Billing Routes (`/v1/billing/*`)

| Method | Path | Description |
|--------|------|-------------|
| POST | /checkout | Create Stripe Checkout Session |
| POST | /webhook | Handle Stripe webhooks |
| GET | /portal | Get billing portal URL |
| GET | /subscription | Get subscription status |

### Account Routes (`/v1/account/*`)

| Method | Path | Description |
|--------|------|-------------|
| GET | / | Get account info |
| PUT | / | Update account |
| GET | /keys | List API keys |
| POST | /keys | Create new API key |
| DELETE | /keys/:id | Revoke API key |
| GET | /usage | Get usage stats |

## Plugin Commands to Build

### `/popkit:upgrade`

```markdown
Opens browser to PopKit signup/upgrade page.

**Usage:**
- `/popkit:upgrade` - Open signup page
- `/popkit:upgrade pro` - Direct to Pro checkout
- `/popkit:upgrade team` - Direct to Team checkout
```

### `/popkit:account`

```markdown
View and manage PopKit account.

**Subcommands:**
- `status` - Show current tier, usage
- `keys` - List and manage API keys
- `billing` - Open billing portal
- `logout` - Clear local session
```

## Implementation Order

1. **Phase 1: Core Auth (Week 1)**
   - [ ] Auth routes (signup, login)
   - [ ] Session management
   - [ ] Password hashing (Argon2id)

2. **Phase 2: Stripe Integration (Week 2)**
   - [ ] Stripe Checkout integration
   - [ ] Webhook handler (subscription events)
   - [ ] Billing portal integration

3. **Phase 3: Landing Page (Week 3)**
   - [ ] Simple signup/login forms
   - [ ] Dashboard showing API keys
   - [ ] Checkout flow

4. **Phase 4: Plugin Commands (Week 4)**
   - [ ] `/popkit:upgrade` command
   - [ ] `/popkit:account` command
   - [ ] Premium feature gating hooks

## Security Considerations

- **Password Storage**: Argon2id with secure parameters
- **API Keys**: 48 random hex characters, hashed for storage
- **Sessions**: JWT or opaque tokens with 7-day expiry
- **HTTPS**: All endpoints require TLS
- **Rate Limiting**: Already implemented
- **CORS**: Restrict to known origins in production

## Open Questions

1. **Domain**: popkit.dev or popkit.io? (Need to purchase)
2. **Email Provider**: Resend ($20/mo) vs SendGrid (free tier)?
3. **Landing Page**: Simple HTML or use a framework (Astro)?
4. **Trial Period**: 7-day trial or straight to checkout?

---

*This plan supports Epic #125 and will be broken into child issues.*
