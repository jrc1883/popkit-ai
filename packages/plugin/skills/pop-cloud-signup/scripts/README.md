# PopKit Cloud Helper Scripts

Python helper scripts for PopKit Cloud authentication and management.

## Scripts

### cloud_auth.py

Handles signup, login, and configuration management for PopKit Cloud.

**Functions:**
- `signup(email, password, name)` - Create new account
- `login(email, password)` - Login to existing account
- `save_config(api_key, user_id, tier, email)` - Save API key locally
- `remove_config()` - Remove local config
- `check_existing_config()` - Check if already configured
- `get_env_instructions(api_key)` - OS-specific env var instructions
- `test_connection(api_key)` - Verify API key works

**CLI Usage:**
```bash
# Create new account
python cloud_auth.py signup user@example.com password123

# Login to existing account
python cloud_auth.py login user@example.com password123

# Test API key
python cloud_auth.py test pk_live_abc123...

# Remove configuration
python cloud_auth.py remove
```

**Security:**
- API keys stored in `~/.claude/popkit/cloud-config.json`
- File permissions set to 600 (owner read/write only)
- Passwords never logged or printed
- Supports both `pk_test_` (dev) and `pk_live_` (prod) keys

### cloud_status.py

Gets cloud connection status, usage stats, and account information.

**Functions:**
- `get_cloud_status()` - Get complete cloud status
- `format_status_output(status, json_output)` - Format status for display

**CLI Usage:**
```bash
# Show status (formatted)
python cloud_status.py

# Show status as JSON
python cloud_status.py --json
```

**Output:**
- Connection status and latency
- Account tier and user ID
- Usage stats (requests today/limit)
- Available features

### cloud_logout.py

Handles logout and cleanup.

**Functions:**
- `logout()` - Remove cloud configuration
- `get_logout_instructions()` - OS-specific unset instructions
- `format_logout_output(result)` - Format logout message

**CLI Usage:**
```bash
python cloud_logout.py
```

## Integration with /popkit:cloud Command

These scripts are invoked by Claude Code when users run `/popkit:cloud` commands:

- `/popkit:cloud signup` → Uses cloud_auth.py signup flow
- `/popkit:cloud login` → Uses cloud_auth.py login flow
- `/popkit:cloud status` → Uses cloud_status.py to show status
- `/popkit:cloud logout` → Uses cloud_logout.py to disconnect

## Cloud API Endpoints

Base URL: `https://api.thehouseofdeals.com/v1`

- `POST /auth/signup` - Create new account
- `POST /auth/login` - Login to existing account
- `GET /health` - Health check (requires Bearer token)

## Configuration File

Location: `~/.claude/popkit/cloud-config.json`

Format:
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

Permissions: `chmod 600` (owner read/write only)

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `POPKIT_API_KEY` | Cloud API key | `pk_live_abc123...` |
| `POPKIT_CLOUD_ENABLED` | Enable/disable cloud | `true` (default) |
| `POPKIT_CLOUD_URL` | Custom cloud URL | `https://api.thehouseofdeals.com/v1` |
| `POPKIT_DEV_MODE` | Use local dev server | `false` (default) |

## Error Handling

All scripts use custom exceptions for specific error types:

- `EmailExistsError` - Email already registered
- `InvalidCredentialsError` - Invalid email or password
- `NetworkError` - Cannot connect to cloud
- `CloudAuthError` - Generic API error

## Testing

Verify cloud API is accessible:
```bash
curl https://api.thehouseofdeals.com/v1/health
```

Expected: `{"status":"ok"}`

## Related Files

- `../SKILL.md` - Skill specification for cloud signup
- `../../commands/cloud.md` - Command specification
- `../../power-mode/cloud_client.py` - Full-featured cloud client
- `../../power-mode/statusline.py` - Status line with cloud widget

## Issue

Part of Issue #566: Implement /popkit:cloud command for cloud connection management
