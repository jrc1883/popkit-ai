---
name: knowledge
description: Manage external knowledge sources for agent context enrichment
---

# /popkit:knowledge

Manage configurable knowledge sources that are synced on session start. External documentation and blogs are fetched, cached, and made available to agents for context enrichment.

## Usage

```bash
/popkit:knowledge                    # List all sources with status
/popkit:knowledge add <url>          # Add new knowledge source
/popkit:knowledge remove <id>        # Remove a knowledge source
/popkit:knowledge refresh            # Force refresh all sources
/popkit:knowledge refresh <id>       # Force refresh specific source
/popkit:knowledge status             # Show detailed cache statistics
```

## Instructions

You are the knowledge source manager. Your job is to help users configure and manage external knowledge sources.

### Default Sources

The following sources are configured by default:
1. **Claude Code Engineering Blog**: `https://www.anthropic.com/engineering`
2. **Claude Code Docs - Overview**: `https://docs.anthropic.com/en/docs/claude-code/overview`
3. **Claude Code Docs - Hooks**: `https://docs.anthropic.com/en/docs/claude-code/hooks`

### Subcommand: List (default)

When called without arguments, list all configured sources:

```bash
# Read the sources configuration
cat ~/.claude/config/knowledge/sources.json
```

Display in a table format:
```
+-------------------------------------------------------------------------+
| Knowledge Sources                                                        |
+-------------------------+--------+--------+---------------+--------------+
| ID                      | Status | TTL    | Last Fetch    | Priority     |
+-------------------------+--------+--------+---------------+--------------+
| anthropic-engineering   | Fresh  | 24h    | 2h ago        | high         |
| claude-code-docs        | Fresh  | 24h    | 2h ago        | high         |
+-------------------------+--------+--------+---------------+--------------+
| Total: 2 sources | 2 fresh | 0 stale                                    |
+-------------------------+--------+--------+---------------+--------------+
```

### Subcommand: Add

When user provides a URL to add:

1. **Validate the URL** - Check it's a valid HTTP(S) URL
2. **Generate an ID** - Create kebab-case ID from domain/path
3. **Ask for details**:
   - Name (human-readable)
   - Tags (comma-separated)
   - Priority (high/medium/low)
   - TTL (default: 24 hours)
4. **Test fetch** - Attempt to fetch the URL to verify it works
5. **Add to sources.json** - Update the configuration file

Example interaction:
```
/popkit:knowledge add https://example.com/docs

Adding new knowledge source...
URL: https://example.com/docs
Generated ID: example-docs
Name: [ask user or infer from page title]
Tags: [ask user]
Priority: high/medium/low? [ask user]

Testing fetch... OK (45KB content)
Source added successfully!
```

### Subcommand: Remove

When user wants to remove a source:

1. **Confirm the source exists**
2. **Remove from sources.json**
3. **Optionally delete cached content**

```bash
/popkit:knowledge remove example-docs

Removing 'example-docs'...
- Removed from sources.json
- Deleted cached content (45KB)
Done.
```

### Subcommand: Refresh

Force refresh sources (bypasses TTL cache):

```bash
# Refresh all
/popkit:knowledge refresh

Refreshing all knowledge sources...
- anthropic-engineering: OK (updated 125KB)
- claude-code-docs: OK (updated 89KB)
All sources refreshed.

# Refresh specific
/popkit:knowledge refresh anthropic-engineering

Refreshing anthropic-engineering...
OK (updated 125KB)
```

### Subcommand: Status

Show detailed cache statistics:

```bash
/popkit:knowledge status

+-------------------------------------------------------------------------+
| Knowledge Cache Status                                                   |
+-------------------------------------------------------------------------+
| Cache Location: ~/.claude/config/knowledge/                             |
| Total Sources: 3                                                         |
| Enabled: 3 | Disabled: 0                                                |
| Fresh: 2 | Stale: 1 | Not Cached: 0                                     |
+-------------------------------------------------------------------------+
| Source Details                                                           |
+-------------------------+----------+----------+------------+-------------+
| ID                      | Status   | Size     | Fetched    | Expires     |
+-------------------------+----------+----------+------------+-------------+
| anthropic-engineering   | fresh    | 125KB    | 2h ago     | in 22h      |
| claude-code-docs        | fresh    | 89KB     | 2h ago     | in 22h      |
| custom-api-docs         | stale    | 45KB     | 26h ago    | expired     |
+-------------------------+----------+----------+------------+-------------+
```

## Configuration File

Sources are stored in `~/.claude/config/knowledge/sources.json`:

```json
{
  "version": "1.0.0",
  "settings": {
    "defaultTTL": 86400,
    "maxContentSize": 50000,
    "fetchTimeout": 30000
  },
  "sources": [
    {
      "id": "anthropic-engineering",
      "name": "Claude Code Engineering Blog",
      "url": "https://www.anthropic.com/engineering",
      "enabled": true,
      "ttl": 86400,
      "tags": ["claude", "best-practices"],
      "priority": "high"
    }
  ]
}
```

## Cache Structure

```
~/.claude/config/knowledge/
  sources.json          # Configuration
  cache.db              # SQLite: metadata, TTL, fetch history
  content/
    anthropic-engineering.md
    claude-code-docs.md
```

## Related

- `pop-knowledge-lookup` skill - Query cached knowledge from agents
- Session start hook automatically syncs sources with TTL check
