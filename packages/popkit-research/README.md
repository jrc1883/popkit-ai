# PopKit - Research Plugin

**Version:** 1.0.0-beta.4
**Status:** Research Plugin (Ready for marketplace)

## Overview

PopKit-Research is the knowledge management plugin for the PopKit ecosystem. It provides research capture, knowledge base management, and semantic search capabilities for organizing development insights.

**Install this plugin** when you need to capture and search research, documentation, and lessons learned.

## Features

### Commands (2)

| Command                      | Description                                                               |
| ---------------------------- | ------------------------------------------------------------------------- |
| `/popkit-research:research`  | Research capture and search (list, search, add, tag, show, delete, merge) |
| `/popkit-research:knowledge` | Knowledge base management (list, add, remove, sync, search)               |

### Skills (3)

This plugin provides 3 specialized skills:

- `pop-research-capture` - Capture and organize development research
- `pop-research-merge` - Merge and consolidate research findings
- `pop-knowledge-lookup` - Search and retrieve knowledge base entries

**Note:** Skills are globally available once installed - other PopKit plugins can use these skills!

### Agents (1)

| Agent        | Tier               | Trigger                                                   |
| ------------ | ------------------ | --------------------------------------------------------- |
| `researcher` | Tier 2 (on-demand) | Project analysis, codebase exploration, pattern discovery |

## Installation

```bash
# Recommended: Install popkit-core foundation first
/plugin install popkit-core@popkit-claude

# Then install research plugin
/plugin install popkit-research@popkit-claude

# Or install during development (local)
/plugin install popkit-research@file:./packages/popkit-research
```

## Dependencies

- **popkit-core** (foundation plugin recommended) - For account management and stats
- **Python** (>= 3.8) - For hook execution
- **PopKit Cloud API** (optional) - For semantic search and community patterns

## Architecture

PopKit-Research is part of PopKit's modular plugin architecture:

```
popkit-core (foundation)
├── Account management
├── Usage statistics
├── Privacy controls
├── Power Mode orchestration
└── Project analysis

popkit-dev (development)
├── Feature development
├── Git operations
└── Daily routines

popkit-ops (operations)
├── Quality assessment
├── Debugging workflows
└── Deployment automation

popkit-research (knowledge)    ← You are here
├── Research capture
├── Knowledge management
└── Semantic search

└── Installs all 4 plugins above
```

## Usage Examples

### Research Management

```bash
# List all research items
/popkit-research:research list

# Search research by keyword
/popkit-research:research search "authentication"

# Add new research item
/popkit-research:research add "OAuth implementation patterns"

# Tag research item
/popkit-research:research tag <id> security,authentication

# Show research details
/popkit-research:research show <id>

# Delete research item
/popkit-research:research delete <id>

# Merge research items
/popkit-research:research merge <id1> <id2>

# Filter by project
/popkit-research:research list --project myapp

# Filter by type
/popkit-research:research list --type pattern
```

### Knowledge Base Management

```bash
# List knowledge base entries
/popkit-research:knowledge list

# Add knowledge entry
/popkit-research:knowledge add

# Remove knowledge entry
/popkit-research:knowledge remove <id>

# Sync with cloud (requires API key)
/popkit-research:knowledge sync

# Search knowledge base
/popkit-research:knowledge search <query>
```

### Researcher Agent

The researcher agent activates for:

- Project analysis and pattern discovery
- Codebase exploration requests
- Meta-research about plugin opportunities
- Cross-project insight generation

Use via Task tool or invoke directly for project analysis.

## Free vs API Key Enhanced

### Local Mode (No API Key)

- File-based research storage
- Local search (keyword matching)
- Full research and knowledge commands
- Single-project knowledge base

### With API Key

- Cloud-backed knowledge base
- Semantic search with embeddings
- Cross-project pattern learning
- Community knowledge sharing
- Automatic tagging suggestions

Configure API key via `/popkit-core:account keys` (requires popkit foundation).

## File Structure

```
packages/popkit-research/
├── .claude-plugin/
│   └── plugin.json             # Plugin manifest
├── commands/
│   ├── research.md             # Research management
│   └── knowledge.md            # Knowledge base
├── skills/
│   ├── pop-research-capture/
│   ├── pop-research-merge/
│   └── pop-knowledge-lookup/
├── agents/
│   └── tier-2-on-demand/
│       └── researcher/
├── hooks/
│   └── utils/                  # 70 bundled Python utilities
├── README.md                   # This file
└── CHANGELOG.md                # Version history
```

## Testing Strategy

1. ✅ Package structure created
2. ✅ Commands extracted from monolithic plugin
3. ✅ Skills extracted
4. ✅ Agent extracted
5. ✅ plugin.json created
6. ⏳ Local installation test
7. ⏳ Command functionality validation
8. ⏳ Agent routing verification
9. ⏳ Skill execution testing

## Success Metrics

- [ ] Both commands work identically to monolithic version
- [ ] Researcher agent routes correctly
- [ ] All 3 skills execute successfully
- [ ] Installation < 30 seconds
- [ ] No context window increase
- [ ] Clean uninstall
- [ ] No functionality regression

## Issues

- **This plugin**: Issue #586 (Extract popkit-research)
- **Parent Epic**: Issue #580 (Plugin Modularization)
- **Dependencies**: popkit foundation (#584 - COMPLETED)

## Related Plugins

When you need more capabilities, install additional PopKit plugins:

```bash
# For account management and stats
/plugin install popkit-core@popkit-claude

# For development workflows
/plugin install popkit-dev@popkit-claude

# For quality assurance and deployment
/plugin install popkit-ops@popkit-claude

# Or install everything
```

## License

MIT

## Support

- **Documentation:** See command files in `commands/`
- **Bug Reports:** `/popkit-core:bug report` (requires popkit foundation)
- **Feature Requests:** GitHub Issues
- **Community:** PopKit Cloud (coming soon)
