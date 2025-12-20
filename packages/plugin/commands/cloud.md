---
description: "signup | status | login | logout - Manage PopKit Cloud connection"
argument-hint: "<subcommand>"
---

# /popkit:cloud - Cloud Connection Management

Manage your PopKit Cloud account and connection.

## Usage

```
/popkit:cloud <subcommand>
```

## Subcommands

| Subcommand | Description |
|------------|-------------|
| `signup` | Create new PopKit Cloud account and get API key |
| `status` | Check cloud connection, tier, and usage |
| `login` | Login to existing PopKit Cloud account |
| `logout` | Disconnect from PopKit Cloud (remove API key) |

---

## Subcommand: signup

Create a new PopKit Cloud account and generate your API key.

```
/popkit:cloud signup
```

### Process

Invokes the `pop-cloud-signup` skill which:

1. **Collects account info** - email, password
2. **Creates cloud account** - calls `/v1/auth/signup`
3. **Generates API key** - format `pk_live_xxxxx`
4. **Saves configuration** - stores in `.claude/popkit/cloud-config.json`
5. **Shows setup instructions** - how to set environment variable
6. **Tests connection** - verifies API key works

### Output

```
╔══════════════════════════════════════╗
║   PopKit Cloud Account Created!     ║
╚══════════════════════════════════════╝

Email: user@example.com
Tier: Free (100 requests/day)

Your API Key (save this securely):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pk_live_abc123def456...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Setup:
1. export POPKIT_API_KEY=pk_live_abc123def456...
2. Restart Claude Code
3. Run /popkit:cloud status to verify
```

---

## Subcommand: status

Check PopKit Cloud connection status, tier, and usage statistics.

```
/popkit:cloud status
/popkit:cloud status --json    # JSON output
```

### Implementation

```
If POPKIT_API_KEY not set:
  Show: Not connected message with signup instructions

If POPKIT_API_KEY set:
  1. Load cloud client
  2. Connect to api.thehouseofdeals.com/v1/health
  3. If connected:
     - Show user ID, tier, email
     - Show usage stats (requests today/limit)
     - Show cloud features available
     - Show latency
  4. If failed:
     - Show connection error
     - Show troubleshooting steps
```

### Output (Connected)

```
PopKit Cloud Status
═══════════════════

Connection: ✓ Connected
URL: https://api.thehouseofdeals.com
Latency: 82ms

Account:
  Email: user@example.com
  Tier: Free
  User ID: usr_abc123

Usage Today:
  Requests: 47 / 100
  Remaining: 53
  Resets: in 17 hours

Available Features:
  ✓ Pattern sharing (collective learning)
  ✓ Research knowledge base
  ✓ Inter-agent messaging
  ✓ Workflow persistence
  ✓ Analytics

Upgrade to Pro for:
  • 1,000 requests/day (10x more)
  • 24-hour session persistence
  • Priority support

Run /popkit:upgrade to see plans
```

### Output (Not Connected)

```
PopKit Cloud Status
═══════════════════

Connection: ✗ Not configured

PopKit Cloud is not set up.

To enable cloud features:
  1. Sign up: /popkit:cloud signup
  2. Or login: /popkit:cloud login

Cloud Features (when connected):
  • Pattern sharing (learn from community)
  • Research knowledge base
  • Power Mode coordination
  • Workflow persistence
```

---

## Subcommand: login

Login to an existing PopKit Cloud account.

```
/popkit:cloud login
```

### Process

1. **Check for existing config** - warn if already logged in
2. **Collect credentials** - email, password via AskUserQuestion
3. **Call login endpoint** - POST `/v1/auth/login`
4. **Save API key** - store in cloud-config.json
5. **Show success** - display tier and setup instructions

### Implementation

```bash
POST https://api.thehouseofdeals.com/v1/auth/login
{
  "email": "user@example.com",
  "password": "userpassword"
}

Response:
{
  "user": { "id": "usr_...", "tier": "free" },
  "sessionToken": "...",
  "apiKey": "pk_live_..."
}
```

### Output

```
╔══════════════════════════════════════╗
║      Logged in to PopKit Cloud      ║
╚══════════════════════════════════════╝

Welcome back, user@example.com!
Tier: Free

Your API Key:
pk_live_abc123def456...

Setup (if not already done):
  export POPKIT_API_KEY=pk_live_abc123def456...

Cloud features are now available.
Run /popkit:cloud status for details.
```

---

## Subcommand: logout

Disconnect from PopKit Cloud by removing your API key.

```
/popkit:cloud logout
```

### Process

1. **Check if logged in** - read cloud-config.json
2. **Confirm logout** - ask user to confirm
3. **Remove API key** - delete cloud-config.json
4. **Clear environment** - show how to unset POPKIT_API_KEY
5. **Show fallback info** - explain local Redis or file-based fallback

### Confirmation

```
Use AskUserQuestion tool with:
- question: "Disconnect from PopKit Cloud?"
- header: "Logout"
- options:
  - label: "Yes, logout"
    description: "Remove API key and disconnect"
  - label: "No, stay connected"
    description: "Keep using cloud features"
- multiSelect: false
```

### Output

```
Logged out from PopKit Cloud

Removed: .claude/popkit/cloud-config.json

To complete logout, unset your environment variable:

Linux/macOS:
  unset POPKIT_API_KEY

Windows PowerShell:
  Remove-Item Env:POPKIT_API_KEY

Windows CMD:
  set POPKIT_API_KEY=

Power Mode will now use:
  1. Local Redis (if Docker running)
  2. File-based fallback (if not)

To login again: /popkit:cloud login
```

---

## Error Handling

### Network Errors

```
Error: Cannot connect to PopKit Cloud

Possible causes:
  • No internet connection
  • PopKit Cloud is down
  • Firewall blocking access

Troubleshooting:
  1. Check internet: ping api.thehouseofdeals.com
  2. Check cloud status: /popkit:cloud status
  3. Try local mode: POPKIT_CLOUD_ENABLED=false
```

### Invalid API Key

```
Error: Invalid API key

Your API key may be:
  • Expired
  • Revoked
  • Malformed

Solutions:
  1. Logout and login again: /popkit:cloud logout
  2. Generate new key: /popkit:cloud signup
  3. Contact support if issue persists
```

### Rate Limit Exceeded

```
Error: Rate limit exceeded

Free tier: 100 requests/day
Used today: 100 / 100

Resets in: 5 hours

Options:
  1. Wait for reset
  2. Upgrade to Pro (1,000/day): /popkit:upgrade
  3. Use local mode temporarily: POPKIT_CLOUD_ENABLED=false
```

---

## Integration with Other Commands

PopKit Cloud automatically enhances other commands:

| Command | Cloud Enhancement |
|---------|-------------------|
| `/popkit:power start` | Uses cloud for agent coordination |
| `/popkit:research add` | Stores research in cloud for cross-project access |
| `/popkit:stats` | Includes cloud usage metrics |
| `/popkit:routine morning` | Shows cloud health check |

---

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `POPKIT_API_KEY` | Your cloud API key | None |
| `POPKIT_CLOUD_ENABLED` | Enable/disable cloud | `true` |
| `POPKIT_CLOUD_URL` | Custom cloud URL | `https://api.thehouseofdeals.com/v1` |
| `POPKIT_DEV_MODE` | Use local dev server | `false` |

---

## Premium Features

All cloud management features available in all tiers:
- ✅ Free - Basic signup, login, status
- ✅ Pro - Same features + higher limits
- ✅ Team - Same features + team management

---

## Examples

```bash
# Sign up for new account
/popkit:cloud signup

# Check connection status
/popkit:cloud status

# Login to existing account
/popkit:cloud login

# Get status as JSON
/popkit:cloud status --json

# Logout
/popkit:cloud logout
```

---

## Related Commands

- `/popkit:upgrade` - Upgrade to Pro/Team tier
- `/popkit:power start` - Start Power Mode with cloud coordination
- `/popkit:stats` - View usage statistics
- `/popkit:routine morning` - Daily health check including cloud

---

## Implementation Details

### Cloud Config File

Located at `.claude/popkit/cloud-config.json`:

```json
{
  "apiKey": "pk_live_abc123def456...",
  "userId": "usr_abc123",
  "email": "user@example.com",
  "tier": "free",
  "configuredAt": "2025-12-20T10:00:00Z",
  "lastVerified": "2025-12-20T10:05:00Z"
}
```

### Security

- File permissions: `chmod 600` (owner read/write only)
- Added to `.gitignore` automatically
- API key never logged or printed except during setup
- Supports both `pk_test_` (development) and `pk_live_` (production)

---

**Status:** Ready to implement
**Dependencies:**
- PopKit Cloud deployed at api.thehouseofdeals.com
- `pop-cloud-signup` skill (created)
**Estimated Time:** 30 minutes to implement all subcommands
