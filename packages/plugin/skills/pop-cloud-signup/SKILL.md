---
description: "Sign up for PopKit Cloud and get your API key"
tags: ["cloud", "setup", "api-key"]
---

# PopKit Cloud Signup

Generate a PopKit Cloud account and API key to enable cloud features.

## What This Does

1. **Creates a cloud account** with email/password
2. **Generates API key** (format: `pk_live_xxxxx`)
3. **Shows setup instructions** for environment variable
4. **Tests connection** to verify it works

## Usage

```
Use this skill when the user wants to:
- "Sign up for PopKit Cloud"
- "Get a PopKit API key"
- "Enable cloud features"
- "Connect to PopKit Cloud"
```

## Prerequisites

- Internet connection
- PopKit Cloud deployed at api.thehouseofdeals.com

## Process

### Step 1: Collect User Information

```
Use AskUserQuestion tool with:
- questions:
  [1] "What email should we use for your PopKit Cloud account?" [header: "Email"]
      - This is a text input question (no predefined options)
      - User will type their email address

  [2] "Choose a password (min 8 characters)" [header: "Password"]
      - This is a text input question
      - User will type their password
      - Note: Not shown in UI for security
```

### Step 2: Call Signup Endpoint

Make HTTP POST request to cloud:

```bash
curl -X POST https://api.thehouseofdeals.com/v1/auth/signup \
  -H "Content-Type: application/json" \
  -d '{
    "email": "<user_email>",
    "password": "<user_password>",
    "name": "PopKit User"
  }'
```

Expected response:
```json
{
  "user": {
    "id": "usr_abc123",
    "email": "user@example.com",
    "tier": "free",
    "createdAt": "2025-12-20T..."
  },
  "sessionToken": "abc123...",
  "apiKey": "pk_live_abc123def456..."
}
```

### Step 3: Save API Key Locally

Store the API key in project config:

```
Create/update: .claude/popkit/cloud-config.json
{
  "apiKey": "pk_live_...",
  "userId": "usr_...",
  "tier": "free",
  "configuredAt": "2025-12-20T..."
}
```

### Step 4: Set Environment Variable

Show instructions based on OS:

**Linux/macOS:**
```bash
# Add to ~/.bashrc or ~/.zshrc
export POPKIT_API_KEY=pk_live_abc123def456...

# Or for current session only
export POPKIT_API_KEY=pk_live_abc123def456...
```

**Windows PowerShell:**
```powershell
# Add to $PROFILE
$env:POPKIT_API_KEY = "pk_live_abc123def456..."

# Or for current session only
$env:POPKIT_API_KEY = "pk_live_abc123def456..."
```

**Windows CMD:**
```cmd
set POPKIT_API_KEY=pk_live_abc123def456...
```

### Step 5: Test Connection

Verify the API key works:

```bash
# Python test
cd packages/plugin/power-mode
POPKIT_API_KEY=pk_live_... python cloud_client.py
```

Expected output:
```
✓ Connected!
  User ID: usr_abc123
  Tier: free
```

### Step 6: Show Success Summary

Display formatted summary:

```
╔══════════════════════════════════════╗
║   PopKit Cloud Account Created!     ║
╚══════════════════════════════════════╝

Email: user@example.com
Tier: Free (100 requests/day)
User ID: usr_abc123

Your API Key (save this securely):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pk_live_abc123def456...
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Setup Instructions:
─────────────────────────────────────

1. Set environment variable:
   export POPKIT_API_KEY=pk_live_abc123def456...

2. Restart Claude Code to load the new variable

3. Test connection:
   /popkit:cloud status

Cloud Features Now Available:
✓ Pattern sharing (collective learning)
✓ Research knowledge base
✓ Inter-agent messaging
✓ Workflow persistence
✓ Analytics

Upgrade to Pro ($9/mo) for:
• 1,000 requests/day (10x more)
• 24-hour session persistence
• Full collective learning access

Run /popkit:upgrade to see pricing
```

## Error Handling

### Email Already Registered

```
Error: Email already registered

This email is already associated with a PopKit Cloud account.

Options:
1. Login instead: /popkit:cloud login
2. Use a different email
3. Reset password: /popkit:cloud reset-password
```

### Invalid Email Format

```
Error: Invalid email format

Please provide a valid email address.
Example: user@example.com
```

### Password Too Short

```
Error: Password must be at least 8 characters

Please choose a longer password for security.
```

### Network Error

```
Error: Could not connect to PopKit Cloud

Possible causes:
- No internet connection
- PopKit Cloud is down
- Firewall blocking access

Check cloud status: https://status.popkit.dev
```

### API Key Already Exists Locally

```
Warning: PopKit Cloud already configured

Found existing API key in .claude/popkit/cloud-config.json
User ID: usr_existing123
Tier: free

Options:
1. Keep existing account (do nothing)
2. Create new account (will replace existing)
3. View current account: /popkit:cloud status
```

Before creating new account, ask:

```
Use AskUserQuestion tool with:
- question: "You already have a PopKit Cloud account. Create a new one?"
- header: "Existing Account"
- options:
  - label: "Keep existing account"
    description: "Don't change anything"
  - label: "Create new account"
    description: "Replace current API key with new one"
- multiSelect: false
```

## Implementation Notes

### HTTP Request Method

Use Python's `urllib.request` (no external dependencies):

```python
import urllib.request
import json

url = "https://api.thehouseofdeals.com/v1/auth/signup"
data = json.dumps({
    "email": email,
    "password": password,
    "name": "PopKit User"
}).encode('utf-8')

headers = {
    'Content-Type': 'application/json'
}

request = urllib.request.Request(url, data=data, headers=headers, method='POST')

try:
    with urllib.request.urlopen(request, timeout=30) as response:
        result = json.loads(response.read().decode('utf-8'))
        api_key = result['apiKey']
        user_id = result['user']['id']
        tier = result['user']['tier']
except urllib.error.HTTPError as e:
    # Handle 409 (email exists), 400 (invalid input), etc.
    error_body = e.read().decode('utf-8')
    error_data = json.loads(error_body)
    # Show user-friendly error message
except urllib.error.URLError as e:
    # Network error
    print(f"Network error: {e.reason}")
```

### Security Considerations

1. **Never log passwords** - Don't print or store password
2. **Secure API key storage** - Use file permissions (chmod 600)
3. **Don't commit to git** - Add `.claude/popkit/cloud-config.json` to `.gitignore`
4. **Test vs live keys** - Support both `pk_test_` and `pk_live_`

### OS Detection

```python
import platform

os_type = platform.system()
if os_type == "Windows":
    # Show PowerShell/CMD instructions
elif os_type == "Darwin":
    # Show macOS/zsh instructions
else:
    # Show Linux/bash instructions
```

### File Permissions

After creating cloud-config.json:

```python
import os
import stat

config_file = Path(".claude/popkit/cloud-config.json")

# Set to read/write for owner only (chmod 600)
os.chmod(config_file, stat.S_IRUSR | stat.S_IWUSR)
```

## Related Commands

- `/popkit:cloud status` - Check cloud connection and usage
- `/popkit:cloud login` - Login to existing account
- `/popkit:upgrade` - Upgrade to Pro/Team tier
- `/popkit:power start` - Use Power Mode with cloud coordination

## Premium Features

This skill is available in all tiers:
- ✅ Free - Sign up and basic cloud access
- ✅ Pro - Same signup process
- ✅ Team - Same signup process + team features

## Testing

To test this skill:

```bash
# 1. Test signup flow
/popkit:cloud signup

# 2. Verify API key was created
cat .claude/popkit/cloud-config.json

# 3. Test connection
export POPKIT_API_KEY=<key_from_file>
python packages/plugin/power-mode/cloud_client.py

# 4. Test cloud features
/popkit:power start
```

## Future Enhancements

1. **OAuth support** - Google, GitHub login
2. **Email verification** - Confirm email before activating
3. **Password reset** - Self-service password recovery
4. **API key rotation** - Generate new keys, revoke old ones
5. **Team invites** - Add team members to account

---

**Status:** Ready to implement
**Dependencies:** PopKit Cloud deployed at api.thehouseofdeals.com
**Estimated Time:** 15 minutes to code, 5 minutes to test
