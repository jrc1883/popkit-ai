---
name: cloud
description: "signup | login | status | logout - Manage PopKit Cloud connection"
argument-hint: "<subcommand>"
---

# /popkit:cloud

Manage your connection to PopKit Cloud for semantic agent routing, pattern learning, and cloud knowledge base.

## Subcommands

| Subcommand | Description |
|------------|-------------|
| `signup` | Create new PopKit Cloud account and get API key |
| `login` | Login to existing account |
| `status` (default) | Show cloud connection status and usage |
| `logout` | Disconnect from cloud and clear local API key |

## Architecture

PopKit Cloud enhances local workflows with semantic intelligence:
- **Always works locally**: All workflows execute without API key
- **Enhanced with cloud**: API key adds semantic routing, pattern learning, cross-project insights
- **Free tier**: 100 requests/day, unlimited local execution
- **No subscription**: Pay only for what you use (embeddings, advanced features)

**Cloud API:** `api.thehouseofdeals.com`
**Config file:** `.claude/popkit/cloud-config.json` (chmod 600)
**Environment:** `POPKIT_API_KEY` (optional, enhances local workflows)

## Examples

```bash
# Create account and get API key
/popkit:cloud signup

# Check connection status
/popkit:cloud
/popkit:cloud status

# Login to existing account
/popkit:cloud login

# Disconnect from cloud
/popkit:cloud logout
```

## Execution

### Subcommand: signup

Create a new PopKit Cloud account and obtain an API key.

**Process:**
1. Check for existing cloud config
2. Prompt for email and password using AskUserQuestion
3. POST to `https://api.thehouseofdeals.com/v1/auth/signup`
4. Save API key to `.claude/popkit/cloud-config.json` (chmod 600)
5. Show environment variable setup instructions
6. Test connection using saved API key
7. Display success summary with tier info

**Implementation:**

Invoke the `pop-cloud-signup` skill via Skill tool:

```
Use Skill tool with skill="popkit:pop-cloud-signup"
```

The skill handles the full signup workflow including:
- Email/password collection via AskUserQuestion
- API request to cloud signup endpoint
- Secure storage of API key
- Connection validation
- User instructions

**Success Output:**

```markdown
✅ PopKit Cloud Account Created

**Email:** user@example.com
**API Key:** pk_live_abc123... (saved securely)
**Tier:** Free (100 requests/day)

### Quick Start

1. **Set environment variable** (optional but recommended):
   ```bash
   export POPKIT_API_KEY="pk_live_abc123..."
   ```

2. **Verify connection**:
   ```bash
   /popkit:cloud status
   ```

3. **Enhanced features now active:**
   - Semantic agent routing
   - Community pattern learning
   - Cloud knowledge base
   - Cross-project insights

**Note:** All workflows still work without setting POPKIT_API_KEY. The key adds semantic intelligence.

### Documentation

- Cloud Status: `docs/cloud/cloud-status.md`
- Cloud Validation: `docs/cloud/cloud-validation.md`
```

**Error Handling:**

```markdown
❌ Signup Failed

**Error:** Email already registered

Try logging in instead:
```bash
/popkit:cloud login
```

Or use a different email address.
```

---

### Subcommand: status (default)

Show cloud connection status, usage metrics, and available features.

**Implementation:**

#### Step 1: Check API Key

```python
import os
import json
from pathlib import Path

# Check environment variable first
api_key = os.environ.get("POPKIT_API_KEY")

# Fall back to config file
if not api_key:
    config_path = Path.home() / ".claude/popkit/cloud-config.json"
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
            api_key = config.get("api_key")

if not api_key:
    print("❌ No PopKit Cloud connection")
    print("\nRun /popkit:cloud signup to get started.")
    return
```

#### Step 2: Query Cloud API

```bash
curl -s -H "Authorization: Bearer $POPKIT_API_KEY" \
  https://api.thehouseofdeals.com/v1/status
```

**Expected Response:**

```json
{
  "status": "connected",
  "latency_ms": 82,
  "tier": "free",
  "usage": {
    "requests_today": 45,
    "limit": 100,
    "embeddings_used": 12,
    "patterns_stored": 156
  },
  "features": {
    "semantic_routing": true,
    "pattern_learning": true,
    "cloud_knowledge": true
  }
}
```

#### Step 3: Display Status

**With API key configured:**

```markdown
✅ PopKit Cloud Connected

**Status:** Connected (82ms)
**Tier:** Free (100 requests/day)
**Usage Today:** 45 / 100 requests

### Available Features
- All core workflows: ✅ (always available locally)
- Semantic agent routing: ✅ (enhanced with cloud)
- Community pattern learning: ✅ (enhanced with cloud)
- Cloud knowledge base: ✅ (enhanced with cloud)
- Cross-project insights: ✅ (enhanced with cloud)

### Usage This Month
- API calls: 1,234
- Embeddings: 456
- Pattern queries: 89
- Patterns stored: 156

**API Key Source:** Environment variable (`POPKIT_API_KEY`)

Run `/popkit:account` for detailed account info.
```

**Without API key:**

```markdown
⚪ PopKit Cloud Not Connected

**Status:** Working locally (no cloud enhancements)

### Available Features
- All core workflows: ✅ (full functionality)
- Semantic agent routing: ⚪ (keyword-based only)
- Community pattern learning: ⚪ (local only)
- Cloud knowledge base: ⚪ (not available)
- Cross-project insights: ⚪ (not available)

### Get Cloud Enhancements

Run `/popkit:cloud signup` to create a free account and enable:
- Semantic agent routing via embeddings
- Community pattern learning across projects
- Cloud-backed knowledge base
- Cross-project insights

**Note:** All workflows work without cloud. The API key adds semantic intelligence.
```

---

### Subcommand: login

Login to an existing PopKit Cloud account.

**Process:**
1. Check for existing cloud config (warn if found)
2. Prompt for email and password using AskUserQuestion
3. POST to `https://api.thehouseofdeals.com/v1/auth/login`
4. Save API key to `.claude/popkit/cloud-config.json` (chmod 600)
5. Test connection using saved API key
6. Display success summary

**Implementation:**

```python
import os
import json
import requests
from pathlib import Path

# Check for existing config
config_path = Path.home() / ".claude/popkit/cloud-config.json"
if config_path.exists():
    print("⚠️  Existing cloud config found. Login will overwrite it.")
    # Use AskUserQuestion to confirm
    # question: "Overwrite existing cloud config?"
    # options: ["Yes, login", "No, cancel"]

# Prompt for credentials
# Use AskUserQuestion with custom input for email
# Use AskUserQuestion with custom input for password (masked)

# Login request
response = requests.post(
    "https://api.thehouseofdeals.com/v1/auth/login",
    json={"email": email, "password": password}
)

if response.status_code == 200:
    data = response.json()
    api_key = data["api_key"]

    # Save to config
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump({"api_key": api_key, "email": email}, f)

    # Set restrictive permissions
    os.chmod(config_path, 0o600)

    print(f"✅ Logged in as {email}")
    print(f"API key saved to {config_path}")
    print("\nRun /popkit:cloud status to verify connection")
else:
    print(f"❌ Login failed: {response.json().get('error', 'Unknown error')}")
```

**Success Output:**

```markdown
✅ Logged in to PopKit Cloud

**Email:** user@example.com
**API Key:** pk_live_xyz789... (saved securely)

Run `/popkit:cloud status` to verify connection.
```

---

### Subcommand: logout

Disconnect from PopKit Cloud and clear local API key.

**Process:**
1. Check for existing cloud config
2. Confirm logout using AskUserQuestion
3. Delete `.claude/popkit/cloud-config.json`
4. Unset `POPKIT_API_KEY` (show instructions, can't unset from session)
5. Display success message

**Implementation:**

```python
import os
from pathlib import Path

# Check for config
config_path = Path.home() / ".claude/popkit/cloud-config.json"
if not config_path.exists() and not os.environ.get("POPKIT_API_KEY"):
    print("⚪ Not connected to PopKit Cloud")
    return

# Confirm logout
# Use AskUserQuestion with:
# question: "Disconnect from PopKit Cloud?"
# options: ["Yes, logout", "No, cancel"]

# Delete config file
if config_path.exists():
    config_path.unlink()
    print(f"✅ Deleted cloud config: {config_path}")

# Remind about environment variable
if os.environ.get("POPKIT_API_KEY"):
    print("\n⚠️  POPKIT_API_KEY environment variable is still set")
    print("Unset it in your shell:")
    print("  unset POPKIT_API_KEY")

print("\n✅ Disconnected from PopKit Cloud")
print("\nAll workflows will continue to work locally.")
print("Run /popkit:cloud signup to reconnect.")
```

**Success Output:**

```markdown
✅ Disconnected from PopKit Cloud

**Config file:** Deleted
**API key:** Cleared

### What's next?

All workflows continue to work locally without cloud enhancements.

To reconnect:
```bash
/popkit:cloud signup   # Create new account
/popkit:cloud login    # Login to existing account
```
```

---

## Security

**API Key Storage:**
- Stored in `.claude/popkit/cloud-config.json`
- File permissions: `chmod 600` (user read/write only)
- Never logged or printed in full (only last 6 chars shown)

**Password Handling:**
- Never stored locally
- Only sent to cloud API over HTTPS
- Never logged or printed

**Environment Variable:**
- `POPKIT_API_KEY` is optional
- Config file used as fallback
- Environment variable takes precedence

---

## Related Commands

| Command | Purpose |
|---------|---------|
| `/popkit:account` | View account info and usage |
| `/popkit:stats` | Session metrics |
| `/popkit:privacy` | Privacy settings |

## Related Documentation

- `docs/cloud/cloud-status.md` - Cloud architecture and deployment
- `docs/cloud/cloud-validation.md` - End-to-end validation
- `CLOUD.md` - Cloud service documentation
