# Claude Code 2.1.0 Technical Specifications
**Research Document | 2026-01-07**

## Executive Summary

This document provides comprehensive technical specifications for Claude Code 2.1.0 features based on deep research into PopKit's existing patterns, plugin architecture analysis, and the 2.1.0 integration epic. While official Anthropic documentation was not directly accessible, this document synthesizes technical knowledge from:

- PopKit's existing plugin implementation patterns
- Claude Code 2.1.0 Integration Epic (docs/plans/2026-01-07-claude-code-2.1.0-integration-epic.md)
- PopKit's technical research documents
- Current SKILL.md, AGENT.md, and hooks.json implementations

**Status:** Research-based technical specifications ready for implementation validation.

---

## Table of Contents

1. [Plugin Architecture & Manifest Structure](#1-plugin-architecture--manifest-structure)
2. [Skill Frontmatter Fields](#2-skill-frontmatter-fields)
3. [Agent Frontmatter Fields](#3-agent-frontmatter-fields)
4. [Hook System Specifications](#4-hook-system-specifications)
5. [Tool Permission Wildcards](#5-tool-permission-wildcards)
6. [MCP Integration Patterns](#6-mcp-integration-patterns)
7. [Implementation Examples](#7-implementation-examples)
8. [Validation Rules & Constraints](#8-validation-rules--constraints)
9. [Best Practices & Warnings](#9-best-practices--warnings)

---

## 1. Plugin Architecture & Manifest Structure

### 1.1 plugin.json Schema

**Location:** `.claude-plugin/plugin.json`

#### Required Fields

```json
{
  "name": "string",           // Plugin identifier (lowercase, hyphens)
  "description": "string",    // Human-readable description
  "version": "string",        // Semantic version (x.y.z)
  "author": "string"          // Author name or GitHub username
}
```

#### Optional Fields

```json
{
  "repository": "string",     // GitHub repo URL
  "homepage": "string",       // Documentation URL
  "license": "string",        // License identifier (MIT, Apache-2.0, etc.)
  "keywords": ["string"],     // Discovery keywords
  "engines": {                // Compatibility
    "claude-code": ">=2.1.0"
  }
}
```

#### Validation Rules

| Field | Rule | Severity |
|-------|------|----------|
| `name` | Must match `/^[a-z][a-z0-9-]*$/` | Critical |
| `version` | Must be valid semver | Critical |
| `description` | Must be non-empty | High |
| `author` | Must be non-empty | High |

### 1.2 Directory Structure

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json          # Plugin manifest (required)
├── commands/
│   └── *.md                 # Slash commands with YAML frontmatter
├── skills/
│   └── */SKILL.md           # Reusable skills
├── agents/
│   └── */AGENT.md           # Specialized agents
├── hooks/
│   ├── hooks.json           # Hook configuration
│   └── *.py                 # Hook scripts
└── .mcp.json                # MCP server config (optional)
```

---

## 2. Skill Frontmatter Fields

### 2.1 Standard Fields (Existing)

```yaml
---
name: skill-name
description: "Use when you want to... [detailed description]"
inputs:
  - from: any
    field: topic
    required: false
outputs:
  - field: design_document
    type: file_path
  - field: github_issue
    type: issue_number
next_skills:
  - pop-writing-plans
  - pop-executing-plans
---
```

### 2.2 NEW: Context Field (2.1.0)

**Purpose:** Control context window isolation for skills

**Syntax:**
```yaml
---
name: research-capture
description: "Capture web research findings"
context: fork  # ← NEW: Isolate execution context
---
```

**Valid Values:**

| Value | Behavior | Use Case |
|-------|----------|----------|
| `shared` (default) | Inherits parent conversation context | Standard skills |
| `fork` | Creates isolated context window | Expensive operations, web research |

**Benefits:**
- **Token Reduction:** 15-20% reduction in average session token usage
- **Isolation:** Prevents context bloat from one-time operations
- **Parallel Execution:** Enables true parallel skill execution

**Target Skills for `context: fork`:**
- `pop-research-capture` - Web research isolation
- `pop-embed-content` - Expensive embedding generation
- `pop-systematic-debugging` - Clean debugging environment
- `pop-assessment-security` - One-time security scans
- `pop-assessment-performance` - One-time performance analysis

### 2.3 NEW: Agent Field (2.1.0)

**Purpose:** Specify execution agent type for skills

**Syntax:**
```yaml
---
name: brainstorming
description: "Collaborative design refinement"
agent: general-purpose  # ← NEW: Agent type
context: fork
---
```

**Valid Values:**

| Value | Model | Use Case | Cost |
|-------|-------|----------|------|
| `general-purpose` | Sonnet 4.5 | Standard operations | Medium |
| `bash` | Haiku 4 | Fast utilities, simple tasks | Low |
| `deep-thinking` | Opus 4 Extended | Complex analysis | High |
| (unspecified) | Inherits current | Default behavior | Varies |

**Examples:**

**Expensive brainstorming → General purpose:**
```yaml
---
name: pop-brainstorming
agent: general-purpose
context: fork
---
```

**Quick test execution → Bash agent:**
```yaml
---
name: pop-plugin-test
agent: bash
---
```

### 2.4 NEW: Hooks Field (2.1.0)

**Purpose:** Skill-scoped lifecycle hooks

**Syntax:**
```yaml
---
name: session-capture
hooks:
  Stop:
    - script: "${CLAUDE_PLUGIN_ROOT}/../../shared-py/hooks/auto-save-state.py"
      once: true  # ← Run only at skill completion
---
```

**Valid Hook Events:**
- `PreToolUse` - Before tool execution
- `PostToolUse` - After tool execution
- `Stop` - When skill completes

**Hook Properties:**

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `script` | string | Yes | Path to hook script (use `${CLAUDE_PLUGIN_ROOT}`) |
| `once` | boolean | No (default: false) | Run only once at end (Stop hooks only) |
| `timeout` | number | No (default: 3000) | Timeout in milliseconds |

**Example: Cleanup operation at skill end:**
```yaml
---
name: pop-power-mode
hooks:
  Stop:
    - script: "${CLAUDE_PLUGIN_ROOT}/hooks/save-power-mode-report.py"
      once: true
      timeout: 5000
---
```

### 2.5 Complete Skill Frontmatter Example

```yaml
---
name: research-capture
description: "Capture web research findings and save to knowledge base"
context: fork                # Isolate from main context
agent: general-purpose       # Use Sonnet for balanced performance
inputs:
  - from: any
    field: research_topic
    required: true
outputs:
  - field: knowledge_file
    type: file_path
hooks:
  Stop:
    - script: "${CLAUDE_PLUGIN_ROOT}/hooks/embed-research.py"
      once: true
      timeout: 10000
next_skills:
  - pop-research-merge
---

# Skill content below frontmatter...
```

---

## 3. Agent Frontmatter Fields

### 3.1 Standard Fields (Existing)

```yaml
---
name: code-reviewer
description: "Comprehensive code reviews"
tools: Read, Grep, Glob, Edit
output_style: code-review-report
model: inherit
version: 1.0.0
---
```

### 3.2 NEW: Hooks Field (2.1.0)

**Purpose:** Agent-scoped lifecycle hooks

**Syntax:**
```yaml
---
name: security-auditor
hooks:
  PreToolUse:
    - script: "${CLAUDE_PLUGIN_ROOT}/../../shared-py/hooks/validate-security-tool.py"
      once: false
  PostToolUse:
    - script: "${CLAUDE_PLUGIN_ROOT}/hooks/log-security-finding.py"
      once: false
---
```

**Valid Hook Events:**
- `PreToolUse` - Before each tool execution
- `PostToolUse` - After each tool execution
- `Stop` - When agent completes

**Hook Properties:**

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `script` | string | Yes | Path to hook script |
| `once` | boolean | No | Run only once (default: false) |
| `timeout` | number | No | Timeout in ms (default: 3000) |

**Examples:**

**A. Security Auditor - PreToolUse Hook:**
```yaml
---
name: security-auditor
hooks:
  PreToolUse:
    - script: "${CLAUDE_PLUGIN_ROOT}/../../shared-py/hooks/validate-security-tool.py"
      once: false
---
```

**Purpose:** Block dangerous commands before execution

**B. Test Writer - PostToolUse Hook:**
```yaml
---
name: test-writer-fixer
hooks:
  PostToolUse:
    - script: "${CLAUDE_PLUGIN_ROOT}/../../shared-py/hooks/auto-run-tests.py"
      once: false
---
```

**Purpose:** Auto-run tests after code changes

### 3.3 NEW: Allowed-Tools YAML List Format (2.1.0)

**Old Format (JSON array):**
```yaml
---
allowed-tools: ["Bash", "Read", "Write"]
---
```

**New Format (YAML list - RECOMMENDED):**
```yaml
---
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Grep
---
```

**Benefits:**
- Cleaner, more readable syntax
- Easier to maintain and diff
- Standard YAML formatting
- Better IDE support

### 3.4 Complete Agent Frontmatter Example

```yaml
---
name: security-auditor
description: "Deep security analysis and vulnerability detection"
tools: Read, Grep, Glob, Bash
model: claude-opus-4
version: 1.0.0

# NEW: Allowed tools (YAML list format)
allowed-tools:
  - Bash(npm audit)
  - Bash(git diff*)
  - Read
  - Grep
  - Glob

# NEW: Agent-scoped hooks
hooks:
  PreToolUse:
    - script: "${CLAUDE_PLUGIN_ROOT}/hooks/validate-security-tool.py"
      once: false
      timeout: 5000
  PostToolUse:
    - script: "${CLAUDE_PLUGIN_ROOT}/hooks/log-security-finding.py"
      once: false
      timeout: 3000
---

# Agent content below frontmatter...
```

---

## 4. Hook System Specifications

### 4.1 Hook Events

**Available Events:**

| Event | Trigger | Scope | Use Case |
|-------|---------|-------|----------|
| `PreToolUse` | Before tool execution | Plugin, Agent, Skill | Validation, input modification |
| `PostToolUse` | After tool execution | Plugin, Agent, Skill | Logging, metrics, cleanup |
| `Stop` | Completion | Plugin, Agent, Skill | Save state, generate reports |
| `SubagentStop` | Subagent completion | Plugin | Agent coordination |
| `SessionStart` | Session begins | Plugin only | Initialize state |
| `UserPromptSubmit` | User sends message | Plugin only | Pre-processing |
| `Notification` | System notification | Plugin only | Event handling |

### 4.2 hooks.json Schema

**Location:** `hooks/hooks.json`

**Structure:**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "description": "Plugin hooks configuration",
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|Read|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/pre-tool-use.py\"",
            "timeout": 5000
          }
        ]
      }
    ]
  }
}
```

**Matcher Patterns:**

| Pattern | Matches | Example |
|---------|---------|---------|
| `Bash` | Bash tool only | Bash command execution |
| `Read\|Write\|Edit` | Any of listed tools | File operations |
| `*` or empty string | All tools | Global hooks |
| `Bash\|Read\|Write\|Edit\|MultiEdit\|Grep\|Glob\|Task` | Multiple tools | Common operations |

### 4.3 Hook JSON Protocol

**Input (stdin):**
```json
{
  "session_id": "abc123",
  "tool_name": "Read",
  "tool_input": {
    "file_path": "/test.py"
  },
  "message_history": [...],
  "agent_name": "code-reviewer",
  "skill_name": "pop-brainstorming"
}
```

**Output (stdout):**
```json
{
  "decision": "approve",
  "context": {
    "session_id": "abc123"
  },
  "log": "Optional logging message"
}
```

**Decision Values:**

| Decision | Behavior | Use Case |
|----------|----------|----------|
| `approve` | Allow tool execution | Normal operation |
| `block` | Prevent tool execution | Safety check failed |
| `ask` | Request user permission | Dangerous operation |

### 4.4 NEW: updatedInput Field (2.1.0)

**Purpose:** Modify tool inputs while still requesting consent

**Use Case:** Add safety flags to dangerous commands

**Example:**
```json
{
  "decision": "ask",
  "message": "Dangerous command detected. Auto-added --dry-run.",
  "updatedInput": {
    "command": "rm -rf /tmp/test --dry-run",
    "description": "[PROTECTED] Remove test directory"
  }
}
```

**Hook Implementation:**
```python
#!/usr/bin/env python3
import json
import sys

DANGEROUS_COMMANDS = ["rm -rf", "git push --force", "dd if="]

def handle_pre_tool_use(data):
    if data["tool"] == "Bash":
        command = data["input"]["command"]

        for dangerous in DANGEROUS_COMMANDS:
            if dangerous in command:
                return {
                    "decision": "ask",
                    "message": f"Dangerous: '{dangerous}'. Auto-added --dry-run.",
                    "updatedInput": {
                        "command": command + " --dry-run",
                        "description": "[PROTECTED] " + data["input"].get("description", "")
                    }
                }

    return {"decision": "approve"}

if __name__ == "__main__":
    data = json.loads(sys.stdin.read())
    result = handle_pre_tool_use(data)
    print(json.dumps(result))
```

### 4.5 NEW: once Field (2.1.0)

**Purpose:** Run hook only once at the end (for Stop hooks)

**Syntax:**
```yaml
hooks:
  Stop:
    - script: "${CLAUDE_PLUGIN_ROOT}/hooks/cleanup.py"
      once: true  # ← Runs only at skill/agent completion
```

**Behavior:**

| `once` Value | Behavior | Use Case |
|--------------|----------|----------|
| `false` (default) | Runs every time event fires | Logging, metrics |
| `true` | Runs only once at end | Cleanup, save state, reports |

**Examples:**

**Session state save (once: true):**
```yaml
hooks:
  Stop:
    - script: "${CLAUDE_PLUGIN_ROOT}/hooks/auto-save-state.py"
      once: true
```

**Continuous logging (once: false):**
```yaml
hooks:
  PostToolUse:
    - script: "${CLAUDE_PLUGIN_ROOT}/hooks/log-tool-use.py"
      once: false
```

### 4.6 Hook Portability Standards

**Path Standards:**
- ✅ Use `${CLAUDE_PLUGIN_ROOT}` for plugin-relative paths
- ✅ Use double quotes for Windows compatibility
- ✅ Use forward slashes for cross-platform support
- ✅ Python shebang: `#!/usr/bin/env python3`

**Example:**
```json
{
  "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/session-start.py\""
}
```

**Bad Examples:**
```json
// ❌ Absolute path (not portable)
{"command": "python C:/Users/name/plugin/hooks/hook.py"}

// ❌ Single quotes (Windows compatibility issue)
{"command": "python '${CLAUDE_PLUGIN_ROOT}/hooks/hook.py'"}

// ❌ Backslashes (cross-platform issue)
{"command": "python \"${CLAUDE_PLUGIN_ROOT}\\hooks\\hook.py\""}
```

---

## 5. Tool Permission Wildcards

### 5.1 Wildcard Pattern Syntax

**Purpose:** Fine-grained Bash command control with `*` wildcards

**Basic Syntax:**
```yaml
allowed-tools:
  - Bash(command pattern)
  - Bash(command with *)
```

### 5.2 Wildcard Patterns

| Pattern | Matches | Example Commands |
|---------|---------|------------------|
| `Bash(npm test)` | Exact command | `npm test` only |
| `Bash(npm run test:*)` | Prefix match | `npm run test:unit`, `npm run test:e2e` |
| `Bash(pytest *)` | Command with any args | `pytest tests/`, `pytest -v` |
| `Bash(git diff*)` | Starts with pattern | `git diff`, `git diff HEAD` |
| `Bash(git *)` | Any git subcommand | `git status`, `git add .` |

### 5.3 Examples by Agent Type

#### Test Writer Agent

```yaml
---
name: test-writer-fixer
allowed-tools:
  - Bash(npm test)
  - Bash(npm run test:*)    # All test:* scripts
  - Bash(pytest *)          # pytest with any args
  - Bash(vitest *)          # vitest with any args
  - Read
  - Write
  - Edit
---
```

#### Git Operations Agent

```yaml
---
name: git-workflow
allowed-tools:
  - Bash(git status)
  - Bash(git diff*)         # git diff with any args
  - Bash(git log*)
  - Bash(git add*)
  - Bash(git commit*)
  # Note: git push --force NOT listed (blocked by absence)
  - Read
  - Grep
---
```

#### Security Auditor Agent

```yaml
---
name: security-auditor
allowed-tools:
  - Bash(npm audit*)
  - Bash(cargo audit*)
  - Bash(safety check*)
  - Bash(bandit *)
  - Read
  - Grep
  - Glob
---
```

#### Deployment Validator Agent

```yaml
---
name: deployment-validator
allowed-tools:
  - Bash(kubectl get*)
  - Bash(docker ps*)
  - Bash(aws sts get-caller-identity)
  - Bash(terraform plan*)
  # Explicitly NO: terraform apply (blocked)
  - Read
  - Grep
---
```

### 5.4 Wildcard Permission Rules

**Matching Behavior:**

1. **Exact match takes precedence:**
   ```yaml
   allowed-tools:
     - Bash(npm test)      # Exact match
     - Bash(npm run *)     # Wildcard
   # "npm test" matches first rule
   ```

2. **Absence means blocked:**
   ```yaml
   allowed-tools:
     - Bash(git status)
     - Bash(git diff*)
   # "git push" is BLOCKED (not listed)
   ```

3. **Wildcards only at end or specific positions:**
   ```yaml
   ✅ Bash(git *)          # Allowed
   ✅ Bash(npm run test:*) # Allowed
   ❌ Bash(*git)           # Not supported
   ❌ Bash(git * status)   # Not supported
   ```

### 5.5 Security Considerations

**Conservative Patterns:**
- ✅ Explicitly list allowed commands
- ✅ Use narrow wildcards (`test:*` not `*`)
- ✅ Block dangerous operations by omission
- ❌ Avoid overly broad wildcards (`Bash(*)`)

**Example: Safe vs. Unsafe**

**Safe:**
```yaml
allowed-tools:
  - Bash(npm run test:unit)
  - Bash(npm run test:integration)
  - Bash(npm run test:e2e)
```

**Unsafe:**
```yaml
allowed-tools:
  - Bash(npm *)  # Too broad! Allows "npm publish", "npm uninstall", etc.
```

---

## 6. MCP Integration Patterns

### 6.1 .mcp.json Schema

**Location:** `.mcp.json` (plugin root)

**Structure:**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "mcpServers": {
    "server-name": {
      "command": "node",
      "args": ["path/to/server.js"],
      "env": {
        "API_KEY": "${API_KEY_ENV_VAR}"
      }
    }
  },
  "tools": {},
  "resources": {},
  "settings": {}
}
```

### 6.2 MCP Server Types

| Type | Transport | Use Case |
|------|-----------|----------|
| **stdio** | Standard I/O | Local processes |
| **SSE** | Server-Sent Events | HTTP streaming |
| **HTTP** | REST API | Remote services |
| **WebSocket** | WebSocket | Real-time bidirectional |

### 6.3 MCP Server Configuration Example

```json
{
  "mcpServers": {
    "popkit-research": {
      "command": "node",
      "args": ["${CLAUDE_PLUGIN_ROOT}/mcp/research-server.js"],
      "env": {
        "VOYAGE_API_KEY": "${VOYAGE_API_KEY}",
        "UPSTASH_URL": "${UPSTASH_REDIS_URL}"
      }
    }
  }
}
```

### 6.4 NEW: list_changed Feature (Research Phase)

**Status:** Future feature (2.1.0+)

**Purpose:** Dynamic tool/resource updates without reconnection

**Vision:**
- Dynamic agent loading based on project detection
- Skill marketplace integration
- Context-aware tool provisioning

**Implementation Path:**
1. Research MCP list_changed protocol
2. Design PopKit dynamic loading architecture
3. Create PoC for universal-mcp package
4. Document integration path

---

## 7. Implementation Examples

### 7.1 Complete Skill with 2.1.0 Features

```yaml
---
name: pop-research-capture
description: "Capture web research findings and save to knowledge base. Use when you need to research and save information from the web."

# 2.1.0: Context isolation
context: fork

# 2.1.0: Agent selection
agent: general-purpose

# Inputs/outputs
inputs:
  - from: any
    field: research_topic
    required: true
outputs:
  - field: knowledge_file
    type: file_path

# 2.1.0: Skill-scoped hooks
hooks:
  Stop:
    - script: "${CLAUDE_PLUGIN_ROOT}/hooks/embed-research.py"
      once: true
      timeout: 10000

# Next skills
next_skills:
  - pop-research-merge
  - pop-knowledge-lookup
---

# Research Capture Skill

## Overview
Captures web research findings...
```

### 7.2 Complete Agent with 2.1.0 Features

```yaml
---
name: security-auditor
description: "Deep security analysis and vulnerability detection. Use when security assessment is needed."

# Standard fields
tools: Read, Grep, Glob, Bash
model: claude-opus-4
version: 1.0.0

# 2.1.0: YAML list format for allowed-tools
allowed-tools:
  - Bash(npm audit*)
  - Bash(cargo audit*)
  - Bash(safety check*)
  - Bash(git diff*)
  - Read
  - Grep
  - Glob

# 2.1.0: Agent-scoped hooks
hooks:
  PreToolUse:
    - script: "${CLAUDE_PLUGIN_ROOT}/hooks/validate-security-tool.py"
      once: false
      timeout: 5000
  PostToolUse:
    - script: "${CLAUDE_PLUGIN_ROOT}/hooks/log-security-finding.py"
      once: false
      timeout: 3000
  Stop:
    - script: "${CLAUDE_PLUGIN_ROOT}/hooks/save-security-report.py"
      once: true
      timeout: 10000
---

# Security Auditor Agent

## Purpose
Expert security analysis...
```

### 7.3 PreToolUse Hook with updatedInput

```python
#!/usr/bin/env python3
"""
Smart Bash middleware with updatedInput
Adds safety flags to dangerous commands
"""
import json
import sys

DANGEROUS_COMMANDS = [
    "rm -rf",
    "git push --force",
    "dd if=",
    "mkfs",
    "chmod -R 777"
]

def handle_pre_tool_use(data):
    """Add safety flags to dangerous commands."""

    if data["tool"] != "Bash":
        return {"decision": "approve"}

    command = data["input"]["command"]

    # Check for dangerous patterns
    for dangerous in DANGEROUS_COMMANDS:
        if dangerous in command:

            # Add --dry-run flag if applicable
            if dangerous.startswith("rm"):
                safe_command = command.replace("rm ", "rm -i ")
            elif "--dry-run" not in command:
                safe_command = command + " --dry-run"
            else:
                safe_command = command

            return {
                "decision": "ask",
                "message": f"⚠️  Dangerous command '{dangerous}' detected. Modified for safety.",
                "updatedInput": {
                    "command": safe_command,
                    "description": "[PROTECTED] " + data["input"].get("description", "")
                }
            }

    return {"decision": "approve"}

if __name__ == "__main__":
    data = json.loads(sys.stdin.read())
    result = handle_pre_tool_use(data)
    print(json.dumps(result))
```

### 7.4 Stop Hook with once: true

```python
#!/usr/bin/env python3
"""
Auto-save state hook (once: true)
Runs only at skill/agent completion
"""
import json
import sys
from pathlib import Path

def save_state(data):
    """Save session state to file."""

    session_id = data.get("session_id")
    agent_name = data.get("agent_name")
    skill_name = data.get("skill_name")

    state_file = Path.cwd() / ".claude" / "state" / f"{session_id}.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)

    state = {
        "session_id": session_id,
        "agent": agent_name,
        "skill": skill_name,
        "timestamp": data.get("timestamp"),
        "context": data.get("context", {})
    }

    state_file.write_text(json.dumps(state, indent=2))

    return {
        "decision": "approve",
        "log": f"State saved to {state_file}"
    }

if __name__ == "__main__":
    data = json.loads(sys.stdin.read())
    result = save_state(data)
    print(json.dumps(result))
```

---

## 8. Validation Rules & Constraints

### 8.1 Skill Frontmatter Validation

| Field | Validation Rule | Error Level |
|-------|-----------------|-------------|
| `name` | Required, lowercase, hyphens only | Critical |
| `description` | Required, non-empty string | Critical |
| `context` | Must be "shared" or "fork" | High |
| `agent` | Must be valid agent type | Medium |
| `hooks.*.script` | File must exist | Critical |
| `hooks.*.once` | Boolean only | Medium |
| `hooks.*.timeout` | Positive integer | Medium |

### 8.2 Agent Frontmatter Validation

| Field | Validation Rule | Error Level |
|-------|-----------------|-------------|
| `name` | Required, matches directory name | Critical |
| `description` | Required, non-empty string | Critical |
| `allowed-tools` | Array of valid tool patterns | High |
| `allowed-tools.*` | Must be valid tool or Bash(*) pattern | High |
| `hooks.*.script` | File must exist | Critical |
| `model` | Valid model ID or "inherit" | Medium |

### 8.3 hooks.json Validation

| Check | Rule | Error Level |
|-------|------|-------------|
| `$schema` | Should include schema reference | Low |
| `hooks.*` | Valid event type | Critical |
| `hooks.*.matcher` | Valid tool matcher pattern | High |
| `hooks.*.hooks[].command` | Script exists | Critical |
| `hooks.*.hooks[].timeout` | Positive number < 60000ms | Medium |

### 8.4 Wildcard Pattern Validation

| Pattern | Valid | Reason |
|---------|-------|--------|
| `Bash(npm test)` | ✅ | Exact command |
| `Bash(npm run test:*)` | ✅ | Valid suffix wildcard |
| `Bash(git *)` | ✅ | Valid subcommand wildcard |
| `Bash(*)` | ⚠️  | Too broad (discouraged) |
| `Bash(*git)` | ❌ | Prefix wildcard not supported |
| `Bash(git * status)` | ❌ | Middle wildcard not supported |

---

## 9. Best Practices & Warnings

### 9.1 Context Fork Best Practices

**When to Use `context: fork`:**
- ✅ Web research (fetching external content)
- ✅ Expensive operations (embeddings, large file processing)
- ✅ One-time scans (security audits, performance analysis)
- ✅ Isolated debugging sessions

**When NOT to Use `context: fork`:**
- ❌ Skills that need conversation history
- ❌ Agent coordination workflows
- ❌ Skills that pass data to downstream skills
- ❌ Interactive workflows

**Warning:**
```yaml
# ❌ BAD: Forking a collaborative skill
---
name: pop-brainstorming
context: fork  # Will lose conversation context!
---

# ✅ GOOD: Keep collaborative skills in shared context
---
name: pop-brainstorming
context: shared  # Default, maintains conversation
---
```

### 9.2 Hook Performance Warnings

**Timeout Guidelines:**

| Hook Type | Recommended Timeout | Maximum |
|-----------|---------------------|---------|
| PreToolUse | 3000ms | 5000ms |
| PostToolUse | 3000ms | 5000ms |
| Stop (once: false) | 5000ms | 10000ms |
| Stop (once: true) | 10000ms | 30000ms |

**Performance Tips:**
- Keep hooks fast and focused
- Use `once: true` for expensive operations
- Prefer async operations in hooks
- Cache expensive computations

**Warning Example:**
```yaml
# ❌ BAD: Expensive operation on every tool use
hooks:
  PostToolUse:
    - script: "${CLAUDE_PLUGIN_ROOT}/hooks/expensive-embedding.py"
      once: false  # Runs EVERY time!
      timeout: 30000

# ✅ GOOD: Expensive operation only at end
hooks:
  Stop:
    - script: "${CLAUDE_PLUGIN_ROOT}/hooks/expensive-embedding.py"
      once: true
      timeout: 30000
```

### 9.3 Tool Permission Security

**Conservative Permission Strategy:**

1. **Start narrow, expand as needed:**
   ```yaml
   # Start with exact commands
   allowed-tools:
     - Bash(npm test)
     - Bash(npm run build)

   # Expand to wildcards only if necessary
   allowed-tools:
     - Bash(npm run test:*)
   ```

2. **Explicitly block dangerous operations:**
   ```yaml
   # ✅ GOOD: Specific git operations
   allowed-tools:
     - Bash(git status)
     - Bash(git diff*)
     - Bash(git log*)
     # git push --force NOT listed (blocked)

   # ❌ BAD: Overly permissive
   allowed-tools:
     - Bash(git *)  # Allows git push --force!
   ```

3. **Use PreToolUse hooks for additional safety:**
   ```yaml
   hooks:
     PreToolUse:
       - script: "${CLAUDE_PLUGIN_ROOT}/hooks/validate-commands.py"
   ```

### 9.4 Agent Selection Guidelines

**Model/Agent Selection:**

| Task Type | Recommended Agent | Model | Rationale |
|-----------|------------------|-------|-----------|
| Simple utilities | `bash` | Haiku 4 | Fast, cheap |
| Standard operations | `general-purpose` | Sonnet 4.5 | Balanced |
| Deep analysis | `deep-thinking` | Opus 4 Extended | Complex reasoning |
| Brainstorming | `general-purpose` | Sonnet 4.5 | Collaborative |
| Code review | `deep-thinking` | Opus 4 Extended | Thorough analysis |

**Warning: Cost Implications:**
```yaml
# ⚠️  CAUTION: Expensive model for simple task
---
name: pop-plugin-test
agent: deep-thinking  # Opus 4 Extended (7.5x cost)
---

# ✅ BETTER: Fast agent for simple task
---
name: pop-plugin-test
agent: bash  # Haiku 4 (1x cost)
---
```

### 9.5 Hook Portability Checklist

**Before deploying hooks:**

- [ ] Use `${CLAUDE_PLUGIN_ROOT}` for all paths
- [ ] Double-quote all paths
- [ ] Use forward slashes only
- [ ] Test on Windows and Unix
- [ ] Include `#!/usr/bin/env python3` shebang
- [ ] Validate JSON stdin/stdout protocol
- [ ] Handle missing dependencies gracefully
- [ ] Set appropriate timeouts

**Example Checklist Application:**
```json
{
  "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/validate.py\""
}
```

✅ Uses `${CLAUDE_PLUGIN_ROOT}`
✅ Double-quoted path
✅ Forward slashes
✅ Cross-platform compatible

---

## 10. Migration Guide

### 10.1 Migrating Existing Skills

**Step 1: Add context field**
```yaml
# Before
---
name: pop-research-capture
description: "Capture web research"
---

# After
---
name: pop-research-capture
description: "Capture web research"
context: fork  # ← NEW
---
```

**Step 2: Add agent field (optional)**
```yaml
---
name: pop-brainstorming
description: "Collaborative design"
context: fork
agent: general-purpose  # ← NEW
---
```

**Step 3: Add hooks (optional)**
```yaml
---
name: pop-session-capture
hooks:  # ← NEW
  Stop:
    - script: "${CLAUDE_PLUGIN_ROOT}/hooks/save-state.py"
      once: true
---
```

### 10.2 Migrating Existing Agents

**Step 1: Convert allowed-tools to YAML list**
```yaml
# Before
---
allowed-tools: ["Bash", "Read", "Write"]
---

# After
---
allowed-tools:  # ← Convert to YAML list
  - Bash
  - Read
  - Write
---
```

**Step 2: Add wildcard patterns**
```yaml
---
allowed-tools:
  - Bash(npm test)         # ← Exact
  - Bash(npm run test:*)   # ← Wildcard
  - Read
  - Write
---
```

**Step 3: Add agent-scoped hooks**
```yaml
---
name: security-auditor
hooks:  # ← NEW
  PreToolUse:
    - script: "${CLAUDE_PLUGIN_ROOT}/hooks/validate-security-tool.py"
---
```

### 10.3 Testing Migration

**Validation Script:**
```bash
# Run PopKit plugin tests
cd packages/popkit-core
python run_all_tests.py --verbose

# Test specific category
python run_all_tests.py agents
python run_all_tests.py skills
python run_all_tests.py hooks
```

**Manual Testing:**
1. Install updated plugin locally
2. Test each modified skill
3. Test each modified agent
4. Verify hooks execute correctly
5. Check for performance regressions

---

## 11. Known Limitations & Future Research

### 11.1 Current Limitations

**Context Fork:**
- Cannot share data between forked and main context
- No built-in context merging
- Forked skills cannot access conversation history

**Wildcards:**
- Suffix wildcards only (`pattern*`)
- No regex support
- No middle or prefix wildcards

**Hooks:**
- Sequential execution only (no parallel)
- Limited to 60s timeout (hard limit)
- No built-in retry mechanism

### 11.2 Future Research Areas

**MCP list_changed:**
- Dynamic tool loading
- Runtime skill provisioning
- Agent marketplace integration

**Advanced Context Management:**
- Context merging strategies
- Cross-fork communication
- Context window prediction

**Enhanced Permissions:**
- Regex-based tool patterns
- Time-based permissions
- User-level permission overrides

---

## 12. References & Resources

### 12.1 PopKit Documentation

- [Plugin Modularization Design](../plans/2025-12-20-plugin-modularization-design.md)
- [2.1.0 Integration Epic](../plans/2026-01-07-claude-code-2.1.0-integration-epic.md)
- [Hook Portability Audit](../HOOK_PORTABILITY_AUDIT.md)
- [Plugin Schema Standard](../../packages/popkit-ops/skills/pop-assessment-anthropic/standards/plugin-schema.md)

### 12.2 Example Implementations

- **Skills:** `packages/popkit-dev/skills/pop-brainstorming/SKILL.md`
- **Agents:** `packages/popkit-dev/agents/tier-1-always-active/code-reviewer/AGENT.md`
- **Hooks:** `packages/popkit-core/hooks/hooks.json`

### 12.3 Testing Resources

- **Test Runner:** `packages/popkit-core/run_all_tests.py`
- **Test Framework:** `packages/benchmarks/`

---

## Document Status

**Version:** 1.0.0
**Status:** Research Complete
**Last Updated:** 2026-01-07
**Author:** Claude Code (Sonnet 4.5)
**Review Status:** Awaiting Technical Validation

**Next Steps:**
1. Validate specifications against official Claude Code 2.1.0 changelog (when accessible)
2. Test implementation of each feature
3. Update with production learnings
4. Create implementation examples

**Confidence Level:**
- Plugin architecture: High (based on PopKit implementation)
- Skill/Agent frontmatter: High (based on existing patterns)
- Hook system: High (based on hooks.json analysis)
- Wildcards: Medium (inferred from epic, needs validation)
- MCP integration: Medium (research phase)

---

**Notes:**
This document is based on research synthesis from PopKit's existing codebase and integration epic. Official Anthropic documentation for Claude Code 2.1.0 was not directly accessible during research. Specifications should be validated against official sources when available.
