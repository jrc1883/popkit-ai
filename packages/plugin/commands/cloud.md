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
| `status` | Check cloud connection and enhancement status |
| `login` | Login to existing PopKit Cloud account |
| `logout` | Disconnect from PopKit Cloud (remove API key) |

---

## Subcommand: signup

Create a new PopKit Cloud account and generate your API key.

```
/popkit:cloud signup
```

### Process

**SECURITY NOTE:** Credentials should NEVER be typed into Claude's chat context.

Invokes the `pop-cloud-signup` skill which:

1. **Opens browser** - redirects to https://popkit.dev/signup
2. **User creates account** - fills form in secure web page
3. **Generates API key** - format `pk_live_xxxxx`
4. **User copies key** - from dashboard after signup
5. **Saves configuration** - stores in `.claude/popkit/cloud-config.json`
6. **Tests connection** - verifies API key works

**Alternative (if web signup not preferred):**
- Use Python's `getpass` module for secure terminal input
- NEVER ask for email/password in Claude's chat

### Output

```
╔══════════════════════════════════════╗
║      Opening PopKit Signup...       ║
╚══════════════════════════════════════╝

Opening https://popkit.dev/signup in your browser...

Next steps:
1. Complete signup in browser
2. Copy your API key from the dashboard
3. Run /popkit:cloud login with your API key

Or set directly:
  export POPKIT_API_KEY=pk_live_...

Then run /popkit:cloud status to verify connection.
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
  User ID: usr_abc123

Enhancements Active:
  ✓ Semantic agent routing (via embeddings)
  ✓ Community pattern learning
  ✓ Cloud knowledge base
  ✓ Cross-project insights
  ✓ Inter-agent messaging
  ✓ Workflow persistence

Usage This Month:
  API Calls: 1,234
  Embeddings: 456
  Pattern Queries: 89

All core workflows also work offline with local fallbacks.
```

### Output (Not Connected)

```
PopKit Cloud Status
═══════════════════

Connection: ✗ Not configured
Mode: Local (fully functional)

To enable enhancements:
  1. Sign up: /popkit:cloud signup
  2. Or login: /popkit:cloud login

Enhanced Intelligence (with API key):
  • Semantic agent routing (via embeddings)
  • Community pattern learning
  • Cloud knowledge base
  • Cross-project insights
  • Workflow persistence

All core workflows work perfectly without API key.
The key adds semantic intelligence, not new features.
```

---

## Subcommand: login

Login to an existing PopKit Cloud account.

```
/popkit:cloud login
```

### Process

**SECURITY NOTE:** For web-based login, open browser instead of collecting credentials in chat.

1. **Check for existing config** - warn if already logged in
2. **Open login page** - https://popkit.dev/login
3. **User logs in** - secure web form
4. **User copies API key** - from dashboard
5. **Save API key** - store in cloud-config.json
6. **Show success** - display setup instructions

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

Your API Key:
pk_live_abc123def456...

Setup (if not already done):
  export POPKIT_API_KEY=pk_live_abc123def456...

Cloud enhancements are now active.
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

### Rate Limit (if implemented)

**Note:** Currently no rate limits. Future usage-based pricing may apply.

```
Note: Cloud enhancements paused

Usage-based limit reached (future feature)

Options:
  1. Continue in local mode (fully functional)
  2. All workflows work with local fallbacks
  3. Set POPKIT_CLOUD_ENABLED=false to disable cloud checks
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

## API Key Benefits

API key adds semantic intelligence to all workflows:
- ✅ Semantic agent routing (via embeddings)
- ✅ Community pattern learning
- ✅ Cloud knowledge base
- ✅ Cross-project insights
- ✅ Workflow persistence

**Cost:** Free for now, usage-based pricing coming soon

All core workflows work perfectly without API key.

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

- `/popkit:upgrade` - Get API key for enhanced intelligence
- `/popkit:account` - View API key status and enhancements
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
