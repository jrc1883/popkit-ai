---
name: pop-knowledge-lookup
description: "Query cached external knowledge sources for up-to-date context on Claude Code, best practices, and documentation"
---

# Knowledge Lookup

## Overview

Query cached external documentation and blog content to get fresh context for development tasks. Knowledge sources are synced on session start and cached for 24 hours.

**Core principle:** Get authoritative, up-to-date information from official sources.

**Trigger:** When you need current information about Claude Code, best practices, or configured documentation sources.

## When to Use

Invoke this skill when:
- User asks about Claude Code features or best practices
- You need to reference official documentation
- Answering questions about hooks, commands, or Claude Code architecture
- Looking for examples from the engineering blog

## Available Knowledge Sources

Default sources (synced automatically):
1. **anthropic-engineering** - Claude Code Engineering Blog
2. **claude-code-docs-overview** - Claude Code Documentation Overview
3. **claude-code-docs-hooks** - Claude Code Hooks Reference

## Lookup Process

### Step 1: List Available Knowledge

```bash
# Check what knowledge is available
cat ~/.claude/config/knowledge/sources.json
```

### Step 2: Check Cache Freshness

```bash
# Query the cache database
sqlite3 ~/.claude/config/knowledge/cache.db \
  "SELECT source_id, fetched_at, expires_at, status FROM knowledge_cache"
```

### Step 3: Read Specific Content

```bash
# Read cached content for a specific source
cat ~/.claude/config/knowledge/content/anthropic-engineering.md

# Or for documentation
cat ~/.claude/config/knowledge/content/claude-code-docs-overview.md
```

### Step 4: Search Across Sources

```bash
# Search for specific topic across all cached content
grep -ri "hooks" ~/.claude/config/knowledge/content/

# Search for a pattern
grep -ri "MCP" ~/.claude/config/knowledge/content/
```

## Response Format

When providing information from knowledge sources:

```markdown
## Knowledge Reference

**Source:** [Source Name]
**Fetched:** [Timestamp]
**Relevance:** [Why this is relevant to the query]

### Key Information

[Relevant excerpt or summary from cached knowledge]

---
*From cached knowledge source: [source_id]*
*Last updated: [fetched_at]*
```

## Example Queries

### Query: "How do hooks work in Claude Code?"

1. Read the hooks documentation:
```bash
cat ~/.claude/config/knowledge/content/claude-code-docs-hooks.md
```

2. Extract relevant sections
3. Provide answer with source attribution

### Query: "What are best practices for Claude Code?"

1. Read the engineering blog:
```bash
cat ~/.claude/config/knowledge/content/anthropic-engineering.md
```

2. Look for best practices content
3. Summarize with examples

### Query: "Is there something about X in the docs?"

1. Search all sources:
```bash
grep -ri "X" ~/.claude/config/knowledge/content/
```

2. If found, read the full context
3. If not found, inform user and suggest they check directly

## Handling Stale or Missing Data

If knowledge is stale or missing:

```markdown
**Note:** The cached knowledge for [source] is [stale/missing].

Last fetched: [date] (expired [time] ago)

Would you like me to:
1. Refresh the knowledge sources? (`/popkit:knowledge refresh`)
2. Provide what I have from my training data?
3. Search the web for current information?
```

## Related

- `/popkit:knowledge` command - Manage knowledge sources
- `knowledge-sync.py` hook - Automatic session start sync
- Session start hook - Triggers knowledge sync with TTL check
