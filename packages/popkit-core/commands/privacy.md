---
description: "status | consent | settings [level|telemetry|exclude|region|auto-delete] | export | delete"
argument-hint: "<subcommand> [level]"
---

# /popkit-core:privacy - Privacy Controls

Manage your privacy settings for collective learning, including consent, data sharing preferences, and GDPR data rights.

## Usage

```
/popkit-core:privacy <subcommand> [options]
```

## Subcommands

| Subcommand | Description                             |
| ---------- | --------------------------------------- |
| `status`   | View current privacy settings (default) |
| `consent`  | Give or revoke consent for data sharing |
| `settings` | Update privacy settings                 |
| `export`   | Export all your data (GDPR)             |
| `delete`   | Delete all your data (GDPR)             |

---

## Subcommand: status (default)

View current privacy settings and consent status.

```
/popkit-core:privacy
/popkit-core:privacy status
```

### Output

```
Privacy Status
==============
Telemetry: off
Consent: Given (2024-12-04)
Project sharing: Enabled
Level: moderate

Settings:
  Anonymization: moderate
  Auto-delete: 90 days
  Region: us
  Excluded projects: 2
  Excluded patterns: 3

Cloud Stats:
  Insights stored: 15
  Patterns contributed: 3
  Usage this month: 2,450 tokens
```

### Status Semantics

- **Telemetry** is machine-level and stored in `~/.claude/config/popkit/onboarding.json`
- **Project sharing** is project-level and stored in `.claude/popkit/privacy.json`
- Changing telemetry does **not** change bug sharing, pattern sharing, or anonymization level

---

## Subcommand: consent

Give or revoke consent for data sharing.

```
/popkit-core:privacy consent give       # Give consent
/popkit-core:privacy consent revoke     # Revoke consent
```

### Giving Consent

When you give consent, you acknowledge:

- Anonymized patterns may be shared with the community
- Your data is processed according to our privacy policy
- You can revoke consent at any time

### Revoking Consent

When you revoke consent:

- Data sharing is immediately disabled
- No new data will be collected
- Existing data remains until you request deletion

---

## Subcommand: settings

Update privacy settings.

```
/popkit-core:privacy settings level <strict|moderate|minimal>
/popkit-core:privacy settings telemetry <off|anonymous|community>
/popkit-core:privacy settings exclude project <name>
/popkit-core:privacy settings exclude pattern <glob>
/popkit-core:privacy settings region <us|eu>
/popkit-core:privacy settings auto-delete <days>
```

### Telemetry Modes

| Mode        | Description                                                                 |
| ----------- | --------------------------------------------------------------------------- |
| `off`       | Local only. No background network observability or project registration.    |
| `anonymous` | Remote observability without project name, path hint, repo slug, or branch. |
| `community` | Remote observability with project identity for full cross-project insights. |

### Anonymization Levels

| Level      | Description                              |
| ---------- | ---------------------------------------- |
| `strict`   | Abstract patterns only, no code snippets |
| `moderate` | Patterns + generic code (default)        |
| `minimal`  | More context preserved (for open source) |

### Examples

```bash
# Set strict anonymization
/popkit-core:privacy settings level strict

# Keep telemetry local-only
/popkit-core:privacy settings telemetry off

# Allow anonymous remote observability
/popkit-core:privacy settings telemetry anonymous

# Exclude a project from sharing
/popkit-core:privacy settings exclude project company-secrets

# Exclude file patterns
/popkit-core:privacy settings exclude pattern "*.env*"

# Set data region to EU
/popkit-core:privacy settings region eu

# Set auto-delete to 30 days
/popkit-core:privacy settings auto-delete 30
```

---

## Subcommand: export

Export all your data from PopKit Cloud (GDPR Right to Data Portability).

```
/popkit-core:privacy export
/popkit-core:privacy export --output ./my-data.json
```

### What's Exported

- All stored insights (summaries, not embeddings)
- Contributed patterns
- Usage statistics
- Privacy settings
- Consent history

### Output Format

```json
{
  "exported_at": "2024-12-04T10:30:00Z",
  "user_id": "user_abc123",
  "data": {
    "insights": { "count": 15, "summaries": {...} },
    "patterns": { "count": 3, "items": {...} },
    "usage": {...}
  }
}
```

---

## Subcommand: delete

Permanently delete all your data from PopKit Cloud (GDPR Right to be Forgotten).

```
/popkit-core:privacy delete
/popkit-core:privacy delete --confirm
```

### What's Deleted

- All stored insights and embeddings
- All contributed patterns
- Usage statistics
- Privacy settings
- Consent records

### Warning

This action is **permanent and cannot be undone**. You will be asked to confirm before deletion.

---

## Anonymization Details

### What Gets Anonymized

| Data Type     | Anonymization     |
| ------------- | ----------------- |
| File paths    | `project/` prefix |
| API keys      | `[API_KEY]`       |
| Emails        | `[EMAIL]`         |
| IPs           | `[IP_ADDRESS]`    |
| UUIDs         | `[UUID]`          |
| Database URLs | `[DATABASE_URL]`  |

### What Never Leaves Your Machine

- Full file contents
- Credentials or secrets
- Personal identifiable info
- Project names (unless open source)
- Exact file paths

---

## Examples

```bash
# Check privacy status
/popkit-core:privacy

# Give consent to start sharing
/popkit-core:privacy consent give

# Keep remote telemetry off
/popkit-core:privacy settings telemetry off

# Allow anonymous observability
/popkit-core:privacy settings telemetry anonymous

# Set strict anonymization for enterprise
/popkit-core:privacy settings level strict

# Exclude sensitive project
/popkit-core:privacy settings exclude project internal-tools

# Export all data
/popkit-core:privacy export --output ~/popkit-data.json

# Delete all data (requires confirmation)
/popkit-core:privacy delete --confirm
```

---

## Claude Code 2.0.71+ Settings Integration

PopKit privacy settings integrate with Claude Code's native settings system (available in v2.0.71+):

### Quick Settings Access

```bash
/settings                  # Opens Claude Code settings (new in 2.0.71)
/config                    # Alias for settings
```

### Privacy Settings in Claude Code

When you access `/settings` in Claude Code 2.0.71+:

1. Navigate to "PopKit Privacy" section
2. Available toggles:
   - **Data Sharing**: Enable/disable collective learning
   - **Anonymization Level**: Choose between strict, moderate, minimal
   - **Auto-Delete**: Set retention period (off, 30, 60, 90 days)
   - **Region**: Select data storage region (us, eu)

### Command-Line Alternative

For CLI-only workflows, continue using `/popkit-core:privacy` directly:

```bash
# These still work in all Claude Code versions
/popkit-core:privacy status                    # View settings
/popkit-core:privacy settings level strict     # Update settings
/popkit-core:privacy consent give              # Manage consent
```

**Note:** `/settings` requires Claude Code 2.0.71+. Earlier versions use `/popkit-core:privacy` exclusively.

---

## Architecture Integration

| Component        | Integration                                         |
| ---------------- | --------------------------------------------------- |
| Privacy Module   | `packages/shared-py/popkit_shared/utils/privacy.py` |
| Onboarding State | `~/.claude/config/popkit/onboarding.json`           |
| Cloud API        | `/v1/privacy/*` endpoints                           |
| Settings Storage | `.claude/popkit/privacy.json`                       |

## Related Commands

| Command                    | Purpose                                   |
| -------------------------- | ----------------------------------------- |
| `/popkit-core:bug --share` | Share bug pattern (uses privacy settings) |
| `/popkit-core:power`       | Power Mode (uses collective patterns)     |
