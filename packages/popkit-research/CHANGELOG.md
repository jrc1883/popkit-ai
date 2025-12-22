# Changelog

All notable changes to PopKit Research will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0-beta.1] - 2025-12-21

### Added

- Initial release as standalone research plugin
- Extracted from monolithic PopKit plugin (Issue #586)
- 2 commands: research, knowledge
- Research capture and organization workflows
- Knowledge base management with local storage
- Semantic search capabilities (with API key)
- Meta-research agent for project analysis

### Architecture

- **Plugin type:** Knowledge (research and knowledge management)
- **Commands:** 2
- **Skills:** 3 (research capture, merge, lookup)
- **Agents:** 1 (researcher, tier-2 on-demand)
- **Size:** Small (~70 bundled utilities)
- **Dependencies:** None (self-contained with bundled utilities)

### Skills Provided

- pop-research-capture - Capture and organize development research
- pop-research-merge - Merge and consolidate research findings
- pop-knowledge-lookup - Search and retrieve knowledge base entries

### Agents Provided

**Tier 2 (On-Demand):**
- researcher - Meta-research specialist for project analysis and pattern discovery

### Features

**Local Mode (Works Without API Key):**
- File-based research storage
- Local keyword search
- Research tagging and organization
- Knowledge base management

**Enhanced with API Key:**
- Cloud-backed knowledge base
- Semantic search with embeddings
- Cross-project pattern learning
- Community knowledge sharing
- Automatic tagging suggestions

### Integration

- Works standalone or with other PopKit plugins
- Skills globally available to all installed plugins
- Bundled utilities for self-contained operation
- Optional integration with popkit foundation for account features
- Optional cloud enhancement with PopKit Cloud API

### Issues

- Implements Issue #586: Extract popkit-research plugin
- Supersedes Issue #575: Extract popkit-research (old architecture)
- Part of Epic #580: PopKit Plugin Modularization

[1.0.0-beta.1]: https://github.com/jrc1883/popkit/releases/tag/popkit-research-v1.0.0-beta.1
