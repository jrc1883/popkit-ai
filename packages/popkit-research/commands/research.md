---
description: "list | search | add | tag | show | delete | merge [--type, --project]"
argument-hint: "<subcommand> [query|id|branch] [options]"
---

# /popkit:research - Research Management

Capture, index, and surface research insights during development. Maintains a searchable knowledge base of findings, decisions, and learnings.

## Subcommands

| Subcommand | Description |
|------------|-------------|
| list (default) | List captured research |
| search | Semantic search across research entries |
| add | Add new research entry |
| tag | Add/remove tags from entries |
| show | View full research entry |
| delete | Remove research entry |
| merge | Process research branches from Claude Code Web sessions |

---

## list (default)

List all captured research entries with optional filtering.

**Storage:** `.claude/research/index.json`

**Output:** Table with ID, type, title, tags, date.

**Options:** --type <type>, --project <name>, --tag <tag>, --limit <N>

---

## search

Semantic search across all research entries using embeddings.

**Process:** Embed query → Search Upstash Vector → Rank by relevance → Return top matches.

**Requires:** VOYAGE_API_KEY environment variable.

**Options:** --limit <N> (default: 5), --threshold <0.0-1.0> (default: 0.7)

---

## add

Add new research entry interactively or inline.

**Types:** decision, finding, learning, spike.

**Process:** Prompt for type → title → content → tags → project → Save to index → Embed entry.

**Options:** --type <type>, --title "text", --content "text", --tags "tag1,tag2", --project <name>

---

## tag

Add/remove tags from existing entries.

**Options:** --add "tag1,tag2", --remove "tag1,tag2"

---

## show

View full research entry with metadata.

**Output:** Formatted entry with ID, type, title, tags, project, date, full content.

---

## delete

Remove research entry after confirmation.

**Options:** --yes (skip confirmation)

---

## merge

Process research branches from Claude Code Web sessions.

**Process:** Load research branches → Parse entries → Deduplicate → Merge into index → Embed new entries.

**Branch format:** `.claude/research/branches/<session-id>.json`

**Options:** --branch <session-id>, --all (merge all branches)

---

## Architecture

| Component | Integration |
|-----------|-------------|
| Index Storage | .claude/research/index.json |
| Embeddings | Voyage AI, Upstash Vector |
| Branch Sync | Claude Code Web → CLI session handoff |
| Search | Semantic similarity with relevance threshold |

**Related:** `/popkit:knowledge`, `/popkit:dev brainstorm`, `/popkit:project embed`
