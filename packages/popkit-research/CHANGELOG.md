# Changelog

All notable changes to the PopKit Research plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-12-20

### Added
- **Initial Release** - Extracted from monolithic PopKit plugin (Issue #575, Epic #580)
- **Commands** (2):
  - `/popkit:research` - Research management (list, search, add, tag, show, delete, merge)
  - `/popkit:knowledge` - Knowledge base management (list, add, remove, sync, search)
- **Skills** (3):
  - `pop-knowledge-lookup` - Semantic search for knowledge items
  - `pop-research-capture` - Capture and organize research
  - `pop-research-merge` - Merge and consolidate research items
- **Agents** (1):
  - `researcher` - Meta-research specialist
- **Features**:
  - Local file-based research storage (FREE)
  - Cloud-backed knowledge base (with API key)
  - Semantic search with embeddings (with API key)
  - Cross-project pattern learning (with API key)
- **Dependencies**: popkit-shared>=0.1.0

[Unreleased]: https://github.com/jrc1883/popkit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/jrc1883/popkit/releases/tag/v0.1.0
