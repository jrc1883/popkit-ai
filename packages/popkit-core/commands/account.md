---
name: account
description: "status | signup | login | keys | usage | logout - Manage your PopKit account"
argument-hint: "<subcommand>"
---

# /popkit:account

Manage your PopKit account and cloud connection for enhanced semantic intelligence.

## Subcommands

| Subcommand | Description |
|------------|-------------|
| `status` (default) | Show account status, API key, cloud connection, and usage |
| `signup` | Create new PopKit account and get API key |
| `login` | Login to existing account |
| `keys` | List and manage your API keys |
| `usage` | Detailed feature usage and rate limits |
| `logout` | Disconnect from cloud and clear local session |

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
# Show account status
/popkit:account
/popkit:account status

# Create new account
/popkit:account signup

# Login to existing account
/popkit:account login

# Manage API keys
/popkit:account keys

# View usage statistics
/popkit:account usage

# Disconnect from cloud
/popkit:account logout
```

## Execution

### Subcommand: status (default)

Show comprehensive account information including API key status, cloud connection, and usage.

#### Step 1: Check API Key

```python
import os
import json
from pathlib import Path

# Check environment variable first
api_key = os.environ.get("POPKIT_API_KEY")
api_key_source = "Environment variable (POPKIT_API_KEY)"

# Fall back to config file
if not api_key:
    config_path = Path.home() / ".claude/popkit/cloud-config.json"
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
            api_key = config.get("api_key")
            api_key_source = f"Config file ({config_path})"

if not api_key:
    # No API key - show local mode status
    api_key_source = "Not configured"
```

#### Step 2: Query Cloud Status (if API key exists)

```bash
curl -s -H "Authorization: Bearer $POPKIT_API_KEY" \
  https://api.thehouseofdeals.com/v1/status
```

**Expected Response:**

```json
{
  "status": "connected",
  "latency_ms": 82,
  "email": "user@example.com",
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

#### Step 3: Display Unified Status

**With API key configured:**

```markdown
✅ PopKit Account Connected

**Email:** user@example.com
**API Key:** ******def456
**API Key Source:** {api_key_source}
**Cloud Status:** Connected (82ms)
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

Run `/popkit:account usage` for detailed breakdown.
```

**Without API key:**

```markdown
⚪ No PopKit Account

**Status:** Working locally (fully functional)

### Available Features
- All core workflows: ✅ (full functionality)
- Semantic agent routing: ⚪ (keyword-based only)
- Community pattern learning: ⚪ (local only)
- Cloud knowledge base: ⚪ (not available)
- Cross-project insights: ⚪ (not available)

### Get Cloud Enhancements

Run `/popkit:account signup` to create a free account and enable:
- Semantic agent routing via embeddings
- Community pattern learning across projects
- Cloud-backed knowledge base
- Cross-project insights

**Note:** All workflows work without cloud. The API key adds semantic intelligence.
```

---

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

1. **Verify connection:**
   ```bash
   /popkit:account status
   ```

2. **Cloud enhancements now active:**
   - Semantic agent routing ✅
   - Community pattern learning ✅
   - Cloud knowledge base ✅
   - Cross-project insights ✅

**Config file:** ~/.claude/popkit/cloud-config.json

Run `/popkit:account` to see your account status.
```

**Error Handling:**

```markdown
❌ Signup Failed

**Error:** Email already registered

This email is already associated with a PopKit Cloud account.

Try logging in instead:
```bash
/popkit:account login
```

Or use a different email address.
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
    # header: "Confirm"
    # options:
    #   - label: "Yes, login", description: "Overwrite and login"
    #   - label: "No, cancel", description: "Keep existing config"
    # multiSelect: false

# Prompt for credentials using AskUserQuestion
# Email collection:
# question: "What email did you use for your PopKit Cloud account?"
# header: "Email"
# options:
#   - label: "Enter email", description: "Type your email address"
# multiSelect: false

# Password collection:
# question: "Enter your password"
# header: "Password"
# options:
#   - label: "Enter password", description: "Type your password (will be hidden)"
# multiSelect: false

# Login request
response = requests.post(
    "https://api.thehouseofdeals.com/v1/auth/login",
    json={"email": email, "password": password},
    timeout=10
)

if response.status_code == 200:
    data = response.json()
    api_key = data["api_key"]
    user_id = data.get("user_id")
    tier = data.get("tier", "free")

    # Save to config
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump({
            "api_key": api_key,
            "email": email,
            "user_id": user_id,
            "tier": tier,
            "created_at": "2025-12-29T00:00:00Z"  # Current timestamp
        }, f, indent=2)

    # Set restrictive permissions (Unix/Mac only)
    try:
        os.chmod(config_path, 0o600)
    except Exception:
        pass  # Windows doesn't support chmod the same way

    print(f"✅ Logged in as {email}")
    print(f"API key saved to {config_path}")
    print("\nRun /popkit:account status to verify connection")
else:
    error_msg = response.json().get("error", "Unknown error")
    print(f"❌ Login failed: {error_msg}")
```

**Success Output:**

```markdown
✅ Logged in to PopKit Cloud

**Email:** user@example.com
**API Key:** pk_live_xyz789... (saved securely)

Run `/popkit:account status` to verify connection.
```

**Error Handling:**

```markdown
❌ Login Failed

**Error:** Invalid email or password

Please check your credentials and try again.

**Need help?**
- Forgot password? Contact joseph@thehouseofdeals.com
- Don't have an account? Run `/popkit:account signup`
```

---

### Subcommand: keys

List and manage API keys.

**Requires:** Active API key configured

**Implementation:**

#### Step 1: Check API Key

```python
import os

api_key = os.environ.get("POPKIT_API_KEY")
if not api_key:
    config_path = Path.home() / ".claude/popkit/cloud-config.json"
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
            api_key = config.get("api_key")

if not api_key:
    print("❌ No API key configured")
    print("\nRun /popkit:account signup to create an account")
    return
```

#### Step 2: Query Keys

```bash
curl -s -H "Authorization: Bearer $POPKIT_API_KEY" \
  https://api.thehouseofdeals.com/v1/account/keys
```

#### Step 3: Display Keys

```markdown
## Your API Keys

| Name | Key | Last Used |
|------|-----|-----------|
| Default Key | pk_live_...abc123 | 2 hours ago |
| CI Pipeline | pk_live_...def456 | 1 day ago |

### Actions
```

Then use AskUserQuestion:

```
Use AskUserQuestion tool with:
- question: "What would you like to do with your API keys?"
- header: "Keys"
- options:
  - label: "Create new key"
    description: "Generate a new API key"
  - label: "Revoke a key"
    description: "Deactivate an existing key"
  - label: "Done"
    description: "Return to account menu"
- multiSelect: false
```

---

### Subcommand: usage

Show detailed feature usage and rate limits.

**Requires:** Active API key configured

**Implementation:**

#### Step 1: Check API Key

```python
import os

api_key = os.environ.get("POPKIT_API_KEY")
if not api_key:
    config_path = Path.home() / ".claude/popkit/cloud-config.json"
    if config_path.exists():
        with open(config_path) as f:
            config = json.load(f)
            api_key = config.get("api_key")

if not api_key:
    print("❌ No API key configured")
    print("\nRun /popkit:account signup to create an account")
    return
```

#### Step 2: Query Usage Summary

```bash
curl -s -H "Authorization: Bearer $POPKIT_API_KEY" \
  https://api.thehouseofdeals.com/v1/usage/summary
```

#### Step 3: Display Usage

**With API key configured:**

```markdown
## Feature Usage

**API Key:** Active
**Period:** December 2025

### This Month's Usage

| Feature | Used | Notes |
|---------|------|-------|
| API Calls | 1,234 | Cloud enhancements active |
| Embeddings | 456 | Semantic agent routing |
| Pattern Queries | 89 | Community knowledge base |
| Knowledge Base Access | 125 | Cross-project insights |

### Enhancement Status

All enhancements active. ✅

**Note:** All features also work offline with local fallbacks.
```

**Without API key:**

```markdown
## Feature Usage

**Mode:** Local (no API key)
**Period:** December 2025

### This Month's Usage

| Feature | Used | Mode |
|---------|------|------|
| Core Workflows | 523 | Local (fully functional) |
| Agent Routing | 89 | Keyword-based |
| Pattern Storage | 34 | File-based |
| Knowledge Base | 12 | Local files |

### Get Enhanced Intelligence

An API key would add:
- Semantic agent routing (via embeddings)
- Community pattern learning
- Cloud knowledge base
- Cross-project insights

Run `/popkit:account signup` to enhance your workflows.
```

---

### Subcommand: logout

Disconnect from PopKit Cloud and clear local session.

**Process:**
1. Check for existing cloud config or environment variable
2. Confirm logout using AskUserQuestion
3. Delete `.claude/popkit/cloud-config.json`
4. Remind about `POPKIT_API_KEY` environment variable
5. Display success message

**Implementation:**

```python
import os
from pathlib import Path

# Check for config or env var
config_path = Path.home() / ".claude/popkit/cloud-config.json"
has_config = config_path.exists()
has_env = os.environ.get("POPKIT_API_KEY")

if not has_config and not has_env:
    print("⚪ Not connected to PopKit Cloud")
    print("\nRun /popkit:account signup to create an account")
    return

# Confirm logout using AskUserQuestion
# Use AskUserQuestion tool with:
# question: "Disconnect from PopKit Cloud?"
# header: "Logout"
# options:
#   - label: "Yes, logout"
#     description: "Clear local session and disconnect"
#   - label: "No, cancel"
#     description: "Keep current connection"
# multiSelect: false

# Delete config file
if config_path.exists():
    config_path.unlink()
    print(f"✅ Deleted cloud config: {config_path}")

# Remind about environment variable
if has_env:
    print("\n⚠️  POPKIT_API_KEY environment variable is still set")
    print("Unset it in your shell:")
    print("\n**macOS/Linux:**")
    print("  unset POPKIT_API_KEY")
    print("\n**Windows (PowerShell):**")
    print("  Remove-Item Env:POPKIT_API_KEY")

print("\n✅ Disconnected from PopKit Cloud")
print("\nAll workflows will continue to work locally.")
```

**Success Output:**

```markdown
✅ Logged out from PopKit Cloud

**Config file:** Deleted
**API key:** Cleared

### What's next?

All workflows continue to work locally without cloud enhancements.

To reconnect:
- `/popkit:account signup` - Create new account
- `/popkit:account login` - Login to existing account
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

**Best Practices:**
- Use strong passwords (16+ characters recommended)
- Don't share API keys
- Use `/popkit:account logout` when switching accounts

---

## Claude Code 2.0.71+ Settings Integration

PopKit works seamlessly with Claude Code's new settings management (available in v2.0.71+):

### Managing Prompt Suggestions

Control prompt suggestions visibility:

```bash
/config                    # Open configuration UI
/settings                  # Alias for /config (new in 2.0.71)
```

**PopKit Configuration Options:**
- Disable prompt suggestions when you prefer to work without recommendations
- Enable suggestions to get PopKit skill recommendations during development
- Fine-tune suggestion types by feature category

### Account Settings

Access account-related settings:

```bash
/settings                  # Opens Claude Code settings panel
# Then navigate to "PopKit Account" section for:
# - API key management
# - Privacy preferences
# - Data retention policies
```

**Note:** Requires Claude Code 2.0.71+. For earlier versions, use `/popkit:account` directly.

---

## Error Handling

| Error | Response |
|-------|----------|
| No API key | "Run /popkit:account signup to create an account" |
| Invalid API key | "API key invalid. Run /popkit:account login or signup" |
| Network error | "Couldn't reach PopKit Cloud. Working in local mode." |
| API rate limit | "Rate limit reached. Working in local mode until reset." |

---

## Related Commands

| Command | Purpose |
|---------|---------|
| `/popkit:privacy` | Privacy and data settings |
| `/popkit:stats` | Session metrics |

---

## Related Documentation

- `docs/cloud/cloud-status.md` - Cloud architecture and deployment
- `docs/cloud/cloud-validation.md` - End-to-end validation
- `CLOUD.md` - Cloud service documentation
