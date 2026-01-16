# Multi-Model Skill Documentation Guide

**Version:** 1.0
**Last Updated:** December 2025
**Purpose:** Guidelines for documenting skills to work across AI coding tools

## Overview

PopKit skills are currently optimized for Claude Code. To support multi-model expansion, skill documentation should include metadata and guidance that enables:

1. **MCP clients** (Cursor, Continue) to understand skill capabilities
2. **Cloud API** to route requests appropriately
3. **Fallback behavior** when native features aren't available

---

## Enhanced SKILL.md Schema

### Current Schema

```yaml
---
name: skill-name
description: "What this skill does"
inputs:
  - field: input_name
    type: string
outputs:
  - field: output_name
    type: file_path
next_skills:
  - related-skill
---
```

### Multi-Model Enhanced Schema

```yaml
---
name: skill-name
description: "What this skill does"

# Input/Output (unchanged)
inputs:
  - field: input_name
    type: string
outputs:
  - field: output_name
    type: file_path

# NEW: Multi-model compatibility
compatibility:
  # Which AI tools can use this skill natively
  native:
    - claude-code
  # Which tools can use via MCP
  mcp:
    - cursor
    - continue
  # Tools that cannot use this skill
  unsupported:
    - copilot # No MCP support yet

# NEW: Required capabilities
capabilities:
  required:
    - file_read
    - file_write
  optional:
    - hooks # Only in Claude Code
    - background_tasks

# NEW: Cloud API dependencies
api_endpoints:
  required:
    - POST /v2/patterns/search
  optional:
    - POST /v2/workflows/start

# NEW: MCP tool mapping
mcp_tools:
  primary:
    - popkit_pattern_search
  supporting:
    - popkit_memory_recall

# Existing fields
next_skills:
  - related-skill
---
```

---

## Compatibility Levels

### Native Support

Full skill functionality with all features:

| Feature          | Claude Code | Notes                 |
| ---------------- | ----------- | --------------------- |
| Hooks (pre/post) | Yes         | Automation triggers   |
| Background Tasks | Yes         | Async agent spawning  |
| Skill Chaining   | Yes         | Direct skill-to-skill |
| Output Styles    | Yes         | Formatted output      |
| Agent Routing    | Yes         | Context-based routing |

### MCP Support

Skills adapted for MCP clients (Cursor, Continue):

| Feature          | Via MCP | Adaptation             |
| ---------------- | ------- | ---------------------- |
| Core logic       | Yes     | MCP tool calls         |
| Hooks            | No      | Skip or manual trigger |
| Background Tasks | No      | Run inline             |
| Skill Chaining   | Partial | User-directed          |
| Output Styles    | No      | Plain text             |
| Agent Routing    | Partial | Explicit selection     |

### Unsupported

Skills that cannot work on certain platforms:

| Reason              | Example         | Handling             |
| ------------------- | --------------- | -------------------- |
| No MCP              | Copilot (older) | Show warning, skip   |
| Missing capability  | No file write   | Graceful degradation |
| Platform limitation | No terminal     | Alternative approach |

---

## Documentation Patterns

### Pattern 1: Capability Detection

Document how the skill detects and adapts to capabilities:

```markdown
## Capability Requirements

This skill requires:

- **File read/write** - To create output documents
- **Git operations** - For version control (optional)

### Fallback Behavior

| Capability | If Missing            |
| ---------- | --------------------- |
| Git        | Skip commit step      |
| Terminal   | Use file-based output |
| Hooks      | Manual validation     |
```

### Pattern 2: MCP Adaptation

Document how the skill maps to MCP tools:

```markdown
## MCP Integration

When running via MCP client (Cursor, Continue):

| Skill Step      | MCP Tool                | Notes            |
| --------------- | ----------------------- | ---------------- |
| Search patterns | `popkit_pattern_search` | Identical        |
| Store memory    | `popkit_memory_store`   | Identical        |
| Quality check   | `popkit_quality_check`  | Subset of checks |
| Save document   | Native file write       | Client handles   |

### MCP-Specific Limitations

- No hook automation - triggers must be manual
- No background tasks - all operations inline
- No output styles - plain markdown output
```

### Pattern 3: Cross-Model Examples

Include examples for different tools:

```markdown
## Usage Examples

### Claude Code (Native)
```

/popkit:dev brainstorm "user authentication"

```

Or invoke skill directly:
```

Use Skill tool with skill="popkit:pop-brainstorming"

```

### Cursor (MCP)

Via chat:
```

Use the popkit_workflow_start tool with goal "Design user authentication"

```

### Continue.dev (MCP)

Via agent mode:
```

Start a PopKit workflow for "user authentication design"

```

```

---

## Migration Checklist

When updating existing skills for multi-model support:

- [ ] Add `compatibility` section to YAML frontmatter
- [ ] Add `capabilities` section listing required features
- [ ] Add `api_endpoints` section for cloud dependencies
- [ ] Add `mcp_tools` section for MCP mapping
- [ ] Document fallback behavior for missing capabilities
- [ ] Add usage examples for non-Claude Code clients
- [ ] Test skill logic without Claude Code-specific features
- [ ] Update skill description to mention multi-model support

---

## Example: Enhanced Brainstorming Skill

```yaml
---
name: brainstorming
description: >
  Collaborative design refinement that transforms rough ideas into
  fully-formed specifications. Works natively in Claude Code and
  via MCP in Cursor/Continue.

compatibility:
  native: [claude-code]
  mcp: [cursor, continue]
  unsupported: []

capabilities:
  required:
    - file_read
    - file_write
    - user_interaction
  optional:
    - hooks
    - background_tasks
    - git_operations

api_endpoints:
  required:
    - GET /v2/patterns/search
  optional:
    - POST /v2/workflows/start
    - POST /v2/memory/store

mcp_tools:
  primary:
    - popkit_pattern_search
    - popkit_workflow_start
  supporting:
    - popkit_memory_store

inputs:
  - field: topic
    type: string
    required: false
outputs:
  - field: design_document
    type: file_path
next_skills:
  - pop-writing-plans
---

# Brainstorming Skill

## Overview

Transform rough ideas into fully-formed designs through Socratic questioning.

## Multi-Model Support

### Claude Code
Full functionality with hooks, background tasks, and output styles.

### Cursor / Continue (MCP)
Core functionality via MCP tools. Limitations:
- No automatic hook triggers
- Manual quality checks
- Plain text output

### Fallback Behavior

| Feature | If Missing | Alternative |
|---------|------------|-------------|
| Hooks | Skip automation | Manual validation |
| Background | Run inline | Longer response time |
| Output styles | Plain markdown | Readable but unstyled |

## Usage

[Rest of skill documentation...]
```

---

## Priority Skills for Enhancement

Focus on these high-value skills first:

| Skill               | Value  | Effort | Priority |
| ------------------- | ------ | ------ | -------- |
| pop-brainstorming   | High   | Medium | P1       |
| pop-writing-plans   | High   | Medium | P1       |
| pop-executing-plans | High   | High   | P1       |
| pop-session-capture | Medium | Low    | P2       |
| pop-session-resume  | Medium | Low    | P2       |
| pop-project-init    | Medium | Medium | P2       |

---

## Testing Multi-Model Skills

### Local Testing

1. Remove Claude Code-specific features temporarily
2. Run skill logic with mock MCP tools
3. Verify fallback behavior works

### Integration Testing

1. Set up Cursor with MCP configuration
2. Call PopKit MCP tools
3. Verify expected behavior

### Checklist

- [ ] Works in Claude Code (native)
- [ ] Works in Cursor (MCP)
- [ ] Works in Continue (MCP)
- [ ] Fallbacks work when features missing
- [ ] Error messages are helpful

---

_This document is part of PopKit's Multi-Model Foundation epic (#111)_
