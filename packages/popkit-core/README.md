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

| Command                  | Description                                        |
| ------------------------ | -------------------------------------------------- |
| `/popkit-core:plugin`    | Plugin testing and management                      |
| `/popkit-core:stats`     | Efficiency metrics and usage statistics            |
| `/popkit-core:privacy`   | Privacy controls and data management               |
| `/popkit-core:account`   | Account management (status, keys, billing, logout) |
| `/popkit-core:dashboard` | Multi-project management dashboard                 |
| `/popkit-core:bug`       | Bug reporting (report, search, share)              |
| `/popkit-core:power`     | Power Mode multi-agent orchestration               |
| `/popkit-core:project`   | Project analysis, initialization, and tooling      |
| `/popkit-core:record`    | Session recording and playback                     |

## Skills

PopKit Core provides 15 specialized skills:

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

### Meta Features (6)

- `pop-bug-reporter` - Bug capture and reporting
- `pop-dashboard` - Multi-project dashboard
- `pop-power-mode` - Multi-agent orchestration
- `pop-sandbox` - E2B sandbox management for safe remote execution
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

| Score  | Meaning               | Action         |
| ------ | --------------------- | -------------- |
| 0-25   | Likely false positive | Skip           |
| 50-75  | Moderate confidence   | Note only      |
| 80-100 | Certain               | Report to user |

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

Power Mode enables parallel multi-agent workflows through intelligent mode selection.

### Native Swarm Mode (New in v1.0.0-beta.9)

**Team-based orchestration** using Claude's native `agentTeams` capability with E2B sandbox isolation:

```
┌─────────────────────────────────────────────────────────┐
│                    NATIVE SWARM MODE                     │
├─────────────────────────────────────────────────────────┤
│   Team Lead (power-coordinator)                         │
│        ↓ TeamCreate                                     │
│   ┌────┴────┬────────┬────────┐                        │
│   ↓         ↓        ↓        ↓                        │
│ Engineer Researcher Tester  Architect                  │
│   ↓         ↓        ↓        ↓                        │
│   └─────────┴────────┴────────┘                        │
│              ↓                                          │
│        E2B Sandboxes (isolated execution)               │
│              ↓                                          │
│        TeamClose → Results                              │
└─────────────────────────────────────────────────────────┘
```

**Key Features:**

- **E2B Sandbox Integration**: Safe, isolated code execution for conflict-free parallel work
- **Auto-Drive Teammates**: Idle agents automatically claim matching tasks (reduces manager latency)
- **Role-Based Assignment**: Engineer, Researcher, Architect, Tester, Security Auditor, Documentation
- **True parallelism**: 5 agents (Premium) or 10 agents (Pro)
- **Cross-platform**: Windows/macOS/Linux

**Configuration:**

Add to `~/.claude/settings.json`:

```json
{
  "experimental": {
    "agentTeams": true,
    "backgroundAgents": true
  }
}
```

Set `E2B_API_KEY` environment variable (or add to settings.json `env` section).

### Native Async Mode

**Zero setup** - uses Claude Code's native background Task tool for simpler parallelism:

- **No external dependencies**: No Docker, no Redis required
- **File-based communication**: Agents share insights via JSON
- **Sync barriers**: Phase-aware coordination between agents

**Requirements:** Claude Code 2.1.33+, Premium or Pro tier

### Other Modes

- **Upstash Redis Mode** (Pro tier, optional): 10+ agents, advanced coordination via Upstash cloud
- **File-Based Mode** (Free tier): 2-3 agents sequential, automatic fallback

### Usage

```bash
/popkit-core:power init          # Check mode availability
/popkit-core:power start         # Start orchestration (auto-selects best mode)
/popkit-core:power status        # Check active agents and progress
/popkit-core:power stop          # Stop all agents gracefully
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
/popkit-core:plugin test

# Validate plugin structure
/popkit-core:plugin sync
```

### Project Analysis

```bash
# Initialize PopKit in project
/popkit-core:project init

# Analyze project structure
/popkit-core:project analyze

# Generate project board
/popkit-core:project board

# Generate MCP server
/popkit-core:project mcp

# Embed project for semantic search
/popkit-core:project embed
```

### Power Mode

```bash
# Initialize Power Mode (one-time setup)
/popkit-core:power init

# Start Power Mode
/popkit-core:power start --agents 5

# Check status
/popkit-core:power status

# Stop Power Mode
/popkit-core:power stop
```

### Dashboard

```bash
# Add project to dashboard
/popkit-core:dashboard add

# Switch between projects
/popkit-core:dashboard switch

# Remove project
/popkit-core:dashboard remove

# Discover projects
/popkit-core:dashboard discover
```

### Statistics

```bash
# Session stats
/popkit-core:stats session

# Today's stats
/popkit-core:stats today

# Weekly stats
/popkit-core:stats week

# Cloud sync stats (requires API key)
/popkit-core:stats cloud

# Reset stats
/popkit-core:stats reset
```

### Privacy

```bash
# Check privacy status
/popkit-core:privacy status

# Manage consent
/popkit-core:privacy consent

# Configure telemetry mode
/popkit-core:privacy settings telemetry off
/popkit-core:privacy settings telemetry anonymous

# Export data
/popkit-core:privacy export

# Delete data
/popkit-core:privacy delete

# Set project sharing level
/popkit-core:privacy settings level strict    # strict | moderate | minimal
```

### Bug Reporting

```bash
# Report a bug
/popkit-core:bug report "description"

# Search bugs
/popkit-core:bug search "keyword"

# Share bug with context
/popkit-core:bug share --issue 123
```

## Hooks

PopKit Core provides several lifecycle hooks that enhance workflow quality and automation:

### Pre-Commit Hook

**Automatic Ruff validation** on staged Python files before every commit (Issue #156):

- **Auto-fixes**: Automatically fixes formatting and linting issues
- **Re-staging**: Auto-fixed files are re-staged transparently
- **Fail-open**: If Ruff is not installed, commits proceed with a warning
- **Performance**: Completes in <5s for typical commits
- **Blocking**: Only blocks on unfixable errors

**Behavior**:

1. Detects staged Python files (`git diff --cached --name-only`)
2. Runs `ruff check --fix` on staged files
3. Runs `ruff format` on staged files
4. Re-stages files if auto-fixes were applied
5. Blocks commit only on unfixable errors

**Installation**:

```bash
pip install ruff  # Required for pre-commit validation
```

**Note**: The hook is automatically active once PopKit Core is installed. No additional setup required.

### Other Hooks

- **SessionStart**: Initializes session context, loads agents, checks for updates
- **PreToolUse**: Validates tool usage and agent coordination
- **PostToolUse**: Captures metrics, observability, and quality gates
- **Stop**: Cleanup and session summary

See `hooks/hooks.json` for complete hook configuration.

## Privacy & Data

PopKit Core respects user privacy:

- **Local-first**: All core features work locally without cloud
- **Telemetry Separation**: Machine-level telemetry is separate from project sharing
- **Opt-in Analytics**: Remote observability is opt-in only
- **Data Export**: Full data export available anytime
- **Right to Deletion**: Complete data deletion on request

Telemetry modes:

- **Off**: No background network observability or project registration
- **Anonymous**: Remote observability without project identity fields
- **Community**: Remote observability with project identity for full insights

Project sharing levels:

- **Strict**: Abstract patterns only, no code snippets
- **Moderate**: Patterns plus generic code (default)
- **Minimal**: More context preserved for open-source style sharing

## Dependencies

- `popkit-shared>=1.0.0` - Shared utilities package
- `e2b-code-interpreter>=1.0.0` - E2B sandbox for Native Swarm mode
- `python-dotenv>=1.0.0` - Environment management
- Optional: Redis for Power Mode orchestration (Upstash mode)
- Optional: Voyage AI API key for semantic embeddings

**Minimum Requirements**:

- Claude Code 2.1.33+ (for extended thinking and plan mode)
- Python 3.11+
- E2B API key (for Native Swarm sandbox features)

## Development Status

**Version**: 1.0.0-beta.12
**Status**: Ready for marketplace publication
**Epic #580**: Complete - Plugin modularization finished

## License

MIT

## Author

Joseph Cannon <joseph@thehouseofdeals.com>
