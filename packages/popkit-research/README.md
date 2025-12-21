# PopKit Research

Research and knowledge management plugin for PopKit - capture, organize, and search research with semantic embeddings.

## Overview

PopKit Research provides comprehensive tools for managing research and building a knowledge base:

- **Research Capture**: Save code snippets, documentation, and insights
- **Knowledge Organization**: Tag, categorize, and merge related research
- **Semantic Search**: Find relevant research using natural language queries
- **Cloud Sync**: Optional cloud-backed knowledge base for cross-project learning
- **Meta-Research**: Discover what agents and tools would help your project

## Commands

| Command | Description |
|---------|-------------|
| `/popkit:research` | Research management (list, search, add, tag, show, delete, merge) |
| `/popkit:knowledge` | Knowledge base management (list, add, remove, sync, search) |

## Skills

### Knowledge Management (3)
- `pop-knowledge-lookup` - Semantic search for knowledge items
- `pop-research-capture` - Capture and organize research
- `pop-research-merge` - Merge and consolidate research items

## Agents

### Tier 2 - On-Demand (1)
- `researcher` - Meta-research specialist for discovering beneficial agents and development opportunities

## API Key Enhancement

| Feature | Free (Local) | With API Key (Cloud) |
|---------|--------------|----------------------|
| Research capture | ✅ Local files | ✅ Cloud storage |
| Research search | ✅ Text search | ✅ Semantic search |
| Knowledge base | ✅ Local notes | ✅ Cross-project knowledge |
| Pattern learning | ❌ | ✅ Community patterns |
| Research sync | ❌ | ✅ Cloud backup |

**All core features work FREE locally.** API key adds cloud intelligence and cross-project insights.

## Installation

This plugin is part of the PopKit ecosystem and depends on `popkit-shared`.

```bash
# Install via Claude Code plugin manager
/plugin install popkit-research@popkit-marketplace
```

## Usage Examples

### Research Management

```bash
# List all research items
/popkit:research list

# Search research
/popkit:research search "authentication patterns"

# Add research
/popkit:research add "JWT validation best practices"

# Tag research
/popkit:research tag 123 security,auth

# Show research item
/popkit:research show 123

# Delete research
/popkit:research delete 123

# Merge related research
/popkit:research merge 123 124 125
```

### Knowledge Base

```bash
# List knowledge items
/popkit:knowledge list

# Add to knowledge base
/popkit:knowledge add

# Remove from knowledge base
/popkit:knowledge remove <id>

# Sync with cloud (requires API key)
/popkit:knowledge sync

# Semantic search (requires API key)
/popkit:knowledge search "how to optimize database queries"
```

### Meta-Research (Researcher Agent)

The `researcher` agent analyzes your codebase to identify:
- Which agents would be most helpful
- What development opportunities exist
- Beneficial patterns from the community

## Local vs Cloud Storage

### Local Mode (Default)
- Research stored in `.claude/popkit/research/`
- Text-based search
- No API key required
- Full privacy

### Cloud Mode (With API Key)
- Research backed up to PopKit Cloud
- Semantic search with embeddings
- Cross-project pattern learning
- Community insights

## Research Structure

Research items are stored as JSON:

```json
{
  "id": "123",
  "title": "JWT Validation Best Practices",
  "content": "...",
  "tags": ["security", "auth"],
  "project": "my-app",
  "created": "2025-12-20T10:00:00Z",
  "updated": "2025-12-20T12:00:00Z"
}
```

## Dependencies

- `popkit-shared>=0.1.0` - Shared utilities package
- Optional: Voyage AI API key for semantic search

## Development Status

**Version**: 0.1.0 (Beta)
**Phase**: 6 of 8 (Plugin Modularization - Epic #580)

## License

MIT

## Author

Joseph Cannon <joseph@thehouseofdeals.com>
