---
name: account
description: "status | keys | billing | logout - Manage your PopKit account"
argument-hint: "<subcommand>"
---

# /popkit:account

View and manage your PopKit account.

## Subcommands

| Subcommand | Description |
|------------|-------------|
| `status` (default) | Show API key status and available enhancements |
| `usage` | Detailed feature usage and rate limits (Issue #138) |
| `keys` | List and manage your API keys |
| `logout` | Clear local session/cache |

## Examples

```bash
/popkit:account           # Show API key status
/popkit:account status    # Same as above
/popkit:account usage     # Detailed usage stats
/popkit:account keys      # List your API keys
/popkit:account logout    # Clear cached session
```

## Execution

### Subcommand: status (default)

Check if `POPKIT_API_KEY` is set and query the cloud API for account info.

#### Step 1: Check API Key

```python
import os

api_key = os.environ.get("POPKIT_API_KEY")
if not api_key:
    print("No POPKIT_API_KEY found. Run /popkit:cloud signup to get started.")
    return
```

#### Step 2: Query Cloud Status

```bash
curl -s -H "Authorization: Bearer $POPKIT_API_KEY" \
  https://api.thehouseofdeals.com/v1/health
```

#### Step 3: Display Status

**With API key configured:**

```markdown
## PopKit Status

**API Key:** Configured ✅
**Cloud Connection:** Connected (45ms)
**Enhancements:** Active

### Available Features
- All core workflows: ✅ (always available)
- Semantic agent routing: ✅ (enhanced with API key)
- Community pattern learning: ✅ (enhanced with API key)
- Cloud knowledge base: ✅ (enhanced with API key)
- Cross-project insights: ✅ (enhanced with API key)

### Usage This Month
- API calls: 1,234
- Embeddings: 456
- Pattern queries: 89

**Note:** All workflows work without API key. The key adds semantic intelligence.

Run `/popkit:cloud status` for detailed connection info.
```

**Without API key:**

```markdown
## PopKit Status

**API Key:** Not configured
**Mode:** Local (fully functional)

### Available Features
- All core workflows: ✅ (always available)
- Semantic agent routing: ⚪ Local keyword-based routing
- Community pattern learning: ⚪ Local pattern storage
- Cloud knowledge base: ⚪ File-based knowledge
- Cross-project insights: ⚪ Single-project mode

### Get Enhanced Intelligence

An API key adds semantic enhancements to your workflows:
- Smarter agent routing via embeddings
- Community pattern learning
- Cross-project knowledge base
- Faster skill discovery

**Get started:**
1. Run `/popkit:cloud signup`
2. Copy your API key
3. Set: `POPKIT_API_KEY=pk_live_...`

**Cost:** Free for now, usage-based pricing coming soon

All core workflows work perfectly without API key. The key just makes them smarter.
```

---

### Subcommand: usage (Issue #138)

Show detailed feature usage and rate limits.

#### Step 1: Query Usage Summary

```bash
curl -s -H "Authorization: Bearer $POPKIT_API_KEY" \
  https://popkit-cloud-api.joseph-cannon.workers.dev/v1/usage/summary
```

#### Step 2: Display Usage

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

Run `/popkit:cloud signup` to enhance your workflows.

**Cost:** Free for now, usage-based pricing coming soon
```

---

### Subcommand: keys

List and manage API keys.

#### Step 1: Query Keys

```bash
curl -s -H "Authorization: Bearer $POPKIT_API_KEY" \
  https://popkit-cloud-api.joseph-cannon.workers.dev/v1/account/keys
```

#### Step 2: Display Keys

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
    description: "Return to main menu"
- multiSelect: false
```

---

### Subcommand: logout

Clear any cached authentication.

```markdown
## Logged Out

Cleared local PopKit session cache.

Note: Your `POPKIT_API_KEY` environment variable is still set.
To fully logout, unset it:

**macOS/Linux:**
```bash
unset POPKIT_API_KEY
```

**Windows (PowerShell):**
```powershell
Remove-Item Env:POPKIT_API_KEY
```
```

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

## Error Handling

| Error | Response |
|-------|----------|
| No API key | "Run /popkit:cloud signup to get an API key" |
| Invalid API key | "API key invalid. Get a new one via /popkit:cloud signup" |
| Network error | "Couldn't reach PopKit Cloud. Working in local mode." |

## Related

- `/popkit:cloud` - Cloud connection management (signup, login, status)
- `/popkit:privacy` - Privacy and data settings
