---
name: cloud-signup
description: Create PopKit Cloud account, generate API key, and configure local connection
---

# PopKit Cloud Signup

Create a new PopKit Cloud account and obtain an API key for enhanced semantic intelligence features.

## When to Use

- User runs `/popkit:cloud signup`
- User wants to enable cloud enhancements (semantic routing, pattern learning)
- User needs to create an account to access cloud features

## Input

User provides (via AskUserQuestion):

- Email address
- Password (minimum 8 characters)

Optional flags:

- `--skip-test`: Skip connection testing after signup

## Process

### 1. Check for Existing Configuration

```python
from pathlib import Path
import json
import os

config_path = Path.home() / ".claude/popkit/cloud-config.json"

# Check config file
if config_path.exists():
    with open(config_path) as f:
        config = json.load(f)
        email = config.get("email")

    print(f"⚠️  Existing cloud config found for {email}")

    # Use AskUserQuestion to confirm
    # Options:
    #   1. "Continue with new signup" (will overwrite existing)
    #   2. "Login to existing account" (invoke pop-cloud-login skill)
    #   3. "Cancel"

# Check environment variable
if os.environ.get("POPKIT_API_KEY"):
    print("⚠️  POPKIT_API_KEY environment variable is already set")
```

### 2. Collect User Credentials

**Email Collection:**

Use AskUserQuestion tool with custom input for email address.

**Password Collection:**

Use AskUserQuestion tool with custom input for password (minimum 8 characters).

**Validation:**

- Email: Must contain @ and valid domain
- Password: Minimum 8 characters, no maximum

### 3. Create Account via Cloud API

```python
import requests

url = "https://api.thehouseofdeals.com/v1/auth/signup"
payload = {
    "email": email,
    "password": password
}

try:
    response = requests.post(url, json=payload, timeout=10)

    if response.status_code == 201:
        # Success
        data = response.json()
        api_key = data["api_key"]
        user_id = data["user_id"]
        tier = data.get("tier", "free")

        print(f"✅ Account created successfully")
        print(f"User ID: {user_id}")
        print(f"Tier: {tier}")

    elif response.status_code == 409:
        # Email already registered
        print("❌ Signup failed: Email already registered")
        print("\nTry logging in instead: /popkit:cloud login")
        return

    # Other error handling...

except requests.exceptions.Timeout:
    print("❌ Signup failed: Request timed out")
    print("Check your internet connection and try again")
    return
```

### 4. Save API Key Locally

```python
from pathlib import Path
import json
import os

config_dir = Path.home() / ".claude/popkit"
config_dir.mkdir(parents=True, exist_ok=True)

config_path = config_dir / "cloud-config.json"

config = {
    "api_key": api_key,
    "email": email,
    "user_id": user_id,
    "tier": tier,
    "created_at": "2025-12-26T00:00:00Z"  # Use current timestamp
}

with open(config_path, "w") as f:
    json.dump(config, f, indent=2)

# Set restrictive permissions (Unix/Mac only)
try:
    os.chmod(config_path, 0o600)
    print(f"🔒 API key saved securely: {config_path}")
except Exception:
    # Windows doesn't support chmod the same way
    print(f"✅ API key saved: {config_path}")
```

### 5. Test Connection

```python
import requests

try:
    headers = {"Authorization": f"Bearer {api_key}"}
    response = requests.get(
        "https://api.thehouseofdeals.com/v1/health",
        headers=headers,
        timeout=5
    )

    if response.status_code == 200:
        latency_ms = response.elapsed.total_seconds() * 1000
        print(f"✅ Cloud connection verified ({latency_ms:.0f}ms)")
    else:
        print(f"⚠️  Warning: Could not verify connection (HTTP {response.status_code})")

except Exception as e:
    print(f"⚠️  Warning: Could not test connection: {e}")
    print("Your account was created successfully")
```

### 6. Display Setup Instructions

````markdown
✅ PopKit Cloud Account Created

**Email:** user@example.com
**API Key:** **\*\***def456 (saved securely)
**Tier:** Free (100 requests/day)

## Quick Start

### Option 1: Use config file (recommended)

Your API key is already saved in `~/.claude/popkit/cloud-config.json`.
PopKit will automatically use it for cloud enhancements.

**Verify connection:**

```bash
/popkit:cloud status
```
````

### Option 2: Set environment variable

For maximum portability, export the API key:

```bash
# Add to ~/.bashrc or ~/.zshrc
export POPKIT_API_KEY="pk_live_abc123def456..."
```

## What's Enhanced?

### Core Workflows (Always Available)

✅ All development commands and skills work without API key

### Cloud Enhancements (Now Active)

✅ **Semantic agent routing** - Better agent selection via embeddings
✅ **Community pattern learning** - Learn from other developers' solutions
✅ **Cloud knowledge base** - Access shared documentation and patterns
✅ **Cross-project insights** - Recommendations based on similar projects

## Usage Limits

**Free Tier:**

- 100 API requests/day
- Unlimited local execution
- All workflows available

Need more? Upgrade at: `/popkit:upgrade`

## Next Steps

1. **Verify connection:**

   ```bash
   /popkit:cloud status
   ```

2. **Test semantic routing:**

   ```bash
   /popkit:next  # Uses embeddings to recommend next action
   ```

3. **View account info:**
   ```bash
   /popkit:account
   ```

## Security Notes

- API key stored with chmod 600 (user read/write only)
- Password never stored locally
- All requests use HTTPS
- Config file: `~/.claude/popkit/cloud-config.json`

**To disconnect:**

```bash
/popkit:cloud logout
```

````

## Error Handling

### Email Already Registered (409)

```markdown
❌ Signup Failed

**Error:** Email already registered

Try logging in instead:
```bash
/popkit:cloud login
````

````

### Invalid Email/Password (400)

```markdown
❌ Signup Failed

**Error:** Invalid email or password

Requirements:
- Email: Must be valid format (contains @ and domain)
- Password: Minimum 8 characters

Please try again with valid credentials.
````

### Connection Timeout

```markdown
❌ Signup Failed

**Error:** Request timed out

Please check:

1. Your internet connection
2. Firewall/proxy settings
3. Cloud status: https://status.thehouseofdeals.com

Try again in a moment.
```

## Related Skills

- `pop-cloud-login` - Login to existing account
- `pop-cloud-status` - Check connection status
- `pop-cloud-logout` - Disconnect from cloud

## Security

**API Key Storage:**

- File: `~/.claude/popkit/cloud-config.json`
- Permissions: chmod 600 (user read/write only)
- Never logged in full (only last 6 chars shown)

**Password Handling:**

- Never stored locally
- Only transmitted to cloud API over HTTPS
- Never logged or printed

**Best Practices:**

- Use strong passwords (16+ characters recommended)
- Don't share API keys
- Use `/popkit:cloud logout` when switching accounts
