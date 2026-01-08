# PopKit Core

Core utilities plugin for PopKit - plugin management, project analysis, Power Mode orchestration, multi-project dashboard, and meta-features.

## Overview

PopKit Core provides the foundational meta-features and utilities for the PopKit ecosystem:

- **Plugin Management**: Test, validate, and manage plugins
- **Project Analysis**: Initialize projects, analyze structure, generate tooling
- **Power Mode**: Multi-agent orchestration for parallel workflows
- **Multi-Project Dashboard**: Manage multiple projects from one place
- **Statistics**: Efficiency metrics and usage analytics
- **Privacy Controls**: Manage data collection and privacy settings
- **Account Management**: API keys, billing, and subscription
- **Bug Reporting**: Capture and share bugs with context

## Commands

| Command | Description |
|---------|-------------|
| `/popkit:plugin` | Plugin testing and management |
| `/popkit:stats` | Efficiency metrics and usage statistics |
| `/popkit:privacy` | Privacy controls and data management |
| `/popkit:account` | Account management (status, keys, billing, logout) |
| `/popkit:dashboard` | Multi-project management dashboard |
| `/popkit:bug` | Bug reporting (report, search, share) |
| `/popkit:power` | Power Mode multi-agent orchestration |
| `/popkit:project` | Project analysis, initialization, and tooling |
| `/popkit:record` | Session recording and playback |

## Skills

PopKit Core provides 14 specialized skills:

### Project Management (5)
- `pop-analyze-project` - Analyze project structure and patterns
- `pop-project-init` - Initialize PopKit in a project
- `pop-project-templates` - Project template generation
- `pop-embed-content` - Embed project content for semantic search
- `pop-embed-project` - Create project embeddings

### Documentation & Validation (4)
- `pop-auto-docs` - Automatic documentation generation
- `pop-doc-sync` - Documentation synchronization
- `pop-plugin-test` - Plugin integrity testing
- `pop-validation-engine` - Configuration validation

### Meta Features (5)
- `pop-bug-reporter` - Bug capture and reporting
- `pop-dashboard` - Multi-project dashboard
- `pop-power-mode` - Multi-agent orchestration
- `pop-mcp-generator` - MCP server generation
- `pop-skill-generator` - Skill template generation

## Agents

### Tier 1 - Always Active (4)
- `api-designer` - API design patterns and best practices
- `accessibility-guardian` - WCAG compliance and a11y
- `documentation-maintainer` - Documentation synchronization
- `migration-specialist` - System migrations and upgrades

### Tier 2 - On-Demand (5)
- `meta-agent` - Agent generator for custom workflows
- `power-coordinator` - Multi-agent orchestration
- `bundle-analyzer` - Bundle size optimization
- `dead-code-eliminator` - Unused code detection and removal
- `feature-prioritizer` - Backlog management and prioritization

## Agent Routing Strategy

PopKit Core uses a sophisticated **two-tier agent routing system** to intelligently activate specialized agents based on context.

### The Tier System

**Tier 1: Always Active (4 agents in Core)**
- `api-designer` - RESTful and GraphQL API design
- `accessibility-guardian` - WCAG compliance and a11y
- `documentation-maintainer` - Documentation synchronization
- `migration-specialist` - System migrations and upgrades

**Tier 2: On-Demand (5 agents in Core)**
- `meta-agent` - Agent generator for custom workflows
- `power-coordinator` - Multi-agent orchestration
- `bundle-analyzer` - Bundle size optimization
- `dead-code-eliminator` - Unused code detection
- `feature-prioritizer` - Backlog management

### How Agents Are Selected

PopKit routes to agents using **four complementary mechanisms**:

1. **Keyword Matching**: User message contains trigger words
   ```
   "Need to optimize bundle size" → bundle-analyzer
   "API design for user service" → api-designer
   ```

2. **File Pattern Matching**: Working with specific file types
   ```
   "Review webpack.config.js" → bundle-analyzer
   "Update api/users.ts" → api-designer
   ```

3. **Error Pattern Matching**: Specific error signatures
   ```
   "SecurityError in API call" → api-designer + security-auditor
   ```

4. **Semantic Embeddings**: Intent understanding beyond keywords
   ```
   "App loads slowly with large data" → bundle-analyzer
   (Requires VOYAGE_API_KEY)
   ```

### Confidence-Based Filtering

Agents apply **80+ confidence threshold** to prevent false positives:

| Score | Meaning | Action |
|-------|---------|--------|
| 0-25 | Likely false positive | Skip |
| 50-75 | Moderate confidence | Note only |
| 80-100 | Certain | Report to user |

### Example: API Design Request

```
User: "Design REST API for user authentication with OAuth2"

Routing Analysis:
- Keywords: "API", "REST" → api-designer (Tier 1) ✅
- Keywords: "authentication", "OAuth2" → security-auditor (Tier 1, from ops)
- Context: API design with security requirements

Agents Activated:
- api-designer (Primary) - Designs endpoints and schemas
- security-auditor (Support) - Reviews auth implementation
```

### Token Optimization

PopKit's routing reduces context usage by **40.5%**:
- Tier 1 baseline: ~15.3k tokens (10 always-active agents across all plugins)
- Tier 2 activation: ~0.3k tokens per specialist (only when needed)
- Total savings: 25.7k → 15.3k tokens

**Learn More**: See [Agent Routing Guide](../../docs/AGENT_ROUTING_GUIDE.md) for complete documentation.

---

## Power Mode

Power Mode enables parallel multi-agent workflows through intelligent mode selection:

### Native Async Mode (Recommended)

**Zero setup** - uses Claude Code 2.0.64+'s native background Task tool for true parallelism:

```
Main Agent (Coordinator)
      ↓
┌─────┼─────┐
↓     ↓     ↓
Agent1 Agent2 Agent3 (parallel background tasks)
↓     ↓     ↓
Share via .claude/popkit/insights.json
↓     ↓     ↓
TaskOutput polling → Aggregated Results
```

**Key Features:**
- **No external dependencies**: No Docker, no Redis required
- **True parallelism**: 5 agents (Premium) or 10 agents (Pro)
- **Cross-platform**: Windows/macOS/Linux
- **File-based communication**: Agents share insights via JSON
- **Sync barriers**: Phase-aware coordination between agents

**Requirements:** Claude Code 2.0.64+, Premium or Pro tier

### Other Modes

- **Upstash Redis Mode** (Pro tier, optional): 10+ agents, advanced coordination via Upstash cloud
- **File-Based Mode** (Free tier): 2-3 agents sequential, automatic fallback

**No Docker or local Redis installation required.** Native Async mode works out of the box.

### Usage

```bash
/popkit:power init          # Check mode availability
/popkit:power start         # Start orchestration (auto-selects best mode)
/popkit:power status        # Check active agents and progress
/popkit:power stop          # Stop all agents gracefully
```

**Deep Dive:** See [docs/POWER_MODE_ASYNC.md](../../docs/POWER_MODE_ASYNC.md) for architecture details, examples, and troubleshooting.

## Installation

This plugin is part of the PopKit ecosystem and depends on `popkit-shared`.

```bash
# Install via Claude Code plugin manager
/plugin install popkit-core@popkit-claude
```

## Usage Examples

### Plugin Management

```bash
# Test plugin integrity
/popkit:plugin test

# Validate plugin structure
/popkit:plugin sync
```

### Project Analysis

```bash
# Initialize PopKit in project
/popkit:project init

# Analyze project structure
/popkit:project analyze

# Generate project board
/popkit:project board

# Generate MCP server
/popkit:project mcp

# Embed project for semantic search
/popkit:project embed
```

### Power Mode

```bash
# Initialize Power Mode (one-time setup)
/popkit:power init

# Start Power Mode
/popkit:power start --agents 5

# Check status
/popkit:power status

# Stop Power Mode
/popkit:power stop
```

### Dashboard

```bash
# Add project to dashboard
/popkit:dashboard add

# Switch between projects
/popkit:dashboard switch

# Remove project
/popkit:dashboard remove

# Discover projects
/popkit:dashboard discover
```

### Statistics

```bash
# Session stats
/popkit:stats session

# Today's stats
/popkit:stats today

# Weekly stats
/popkit:stats week

# Cloud sync stats (requires API key)
/popkit:stats cloud

# Reset stats
/popkit:stats reset
```

### Privacy

```bash
# Check privacy status
/popkit:privacy status

# Manage consent
/popkit:privacy consent

# Export data
/popkit:privacy export

# Delete data
/popkit:privacy delete

# Set privacy level
/popkit:privacy level strict    # strict | moderate | minimal
```

### Bug Reporting

```bash
# Report a bug
/popkit:bug report "description"

# Search bugs
/popkit:bug search "keyword"

# Share bug with context
/popkit:bug share --issue 123
```

## Privacy & Data

PopKit Core respects user privacy:

- **Local-first**: All core features work locally without cloud
- **Opt-in Analytics**: Usage stats are opt-in only
- **Data Export**: Full data export available anytime
- **Right to Deletion**: Complete data deletion on request

Privacy levels:
- **Strict**: No telemetry, no cloud sync
- **Moderate**: Basic usage stats, opt-in cloud features
- **Minimal**: All features with maximum data sharing

## Dependencies

- `popkit-shared>=1.0.0` - Shared utilities package
- Optional: Redis for Power Mode orchestration
- Optional: Voyage AI API key for semantic embeddings

**Minimum Requirements**:
- Claude Code 2.0.67+ (for extended thinking and plan mode)
- Python 3.8+

## Development Status

**Version**: 1.0.0-beta.1
**Status**: Ready for marketplace publication
**Epic #580**: Complete - Plugin modularization finished

## License

MIT

## Author

Joseph Cannon <joseph@thehouseofdeals.com>
