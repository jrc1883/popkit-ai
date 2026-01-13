# PopKit Shared Hooks

This directory contains shared hook scripts for PopKit plugins, implementing Claude Code 2.1.0 hook system enhancements.

## Overview

All hooks follow the Claude Code JSON stdin/stdout protocol:

- **Input**: JSON data via stdin
- **Output**: JSON response via stdout
- **Exit code**: 0 (success)

## Hooks

### Agent-Scoped Hooks

#### 1. validate-security-tool.py

- **Type**: PreToolUse
- **Scope**: security-auditor agent
- **Once**: false (runs on every tool use)
- **Purpose**: Block dangerous commands during security audits

**Protections:**

- Blocks critical commands: `rm -rf /`, `dd if=`, fork bombs
- Requests approval for protected files: `.env`, credentials, SSH keys
- Validates WebFetch URLs to prevent SSRF

**Response:**

- `decision: "deny"` - Critical dangerous commands
- `decision: "ask"` - Protected file access, internal URLs
- `decision: "allow"` - Safe operations

#### 2. auto-run-tests.py

- **Type**: PostToolUse
- **Scope**: test-writer-fixer agent
- **Once**: false (runs after every tool use)
- **Purpose**: Auto-run tests after code changes

**Features:**

- Detects test framework (pytest, npm test, go test, cargo test, etc.)
- Runs tests automatically after file modifications
- Returns pass/fail status with timing

**Response:**

- `decision: "allow"` (always)
- `message: "✓ Auto-test passed (pytest, 2.3s)"` - Success
- `message: "✗ Auto-test failed ..."` - Failure with preview

### Skill-Scoped Hooks (once: true)

#### 3. auto-save-state.py

- **Type**: Stop
- **Scope**: session-capture skill
- **Once**: true (runs only at skill completion)
- **Purpose**: Auto-save session state to STATUS.json

**Features:**

- Captures git state (branch, commits, uncommitted files)
- Saves to `.claude/STATUS.json` or project root
- Includes project name from package.json/pyproject.toml

**Response:**

- `decision: "allow"` (always)
- `message: "Session state auto-saved to <path>"`

#### 4. save-power-mode-report.py

- **Type**: Stop
- **Scope**: power-mode skill
- **Once**: true (runs only at skill completion)
- **Purpose**: Save power mode execution report

**Features:**

- Aggregates insights by agent and phase
- Counts total agents and insights
- Saves timestamped report to `.claude/popkit/power-mode-report-<timestamp>.json`

**Response:**

- `decision: "allow"` (always)
- `message: "Power mode report saved to <path>\n- Agents: N\n- Insights: M\n- Phases: P"`

### Global Middleware Hooks

#### 5. smart-bash-middleware.py

- **Type**: PreToolUse
- **Scope**: Global (all agents)
- **Once**: false (runs on every Bash tool use)
- **Purpose**: Detect dangerous bash commands and auto-add safety flags

**Features:**

- Pattern matching for dangerous commands
- Severity levels: critical, high, medium
- Auto-modifies commands with safety flags (uses `updatedInput`)
- Demonstrates Claude Code 2.1.0 `updatedInput` feature

**Dangerous Patterns:**
| Pattern | Severity | Action |
|---------|----------|--------|
| `rm -rf /` | critical | Deny |
| `dd if=` | critical | Deny |
| `mkfs.` | critical | Deny |
| `git push --force` | high | Ask + modify to `--force-with-lease --dry-run` |
| `chmod -R 777 /` | high | Ask |

**Response:**

- `decision: "deny"` - Critical severity
- `decision: "ask"` + `updatedInput` - High severity with safety modifications
- `decision: "ask"` - High severity without modifications
- `decision: "allow"` - Safe commands

## JSON Protocol

All hooks follow this structure:

### Input Format

```json
{
  "tool": "Bash",
  "input": {
    "command": "...",
    "description": "..."
  },
  "agent": "security-auditor",
  "skill": "session-capture"
}
```

### Output Format

```json
{
  "decision": "allow|deny|ask",
  "message": "Optional explanation",
  "updatedInput": {
    "command": "Modified command",
    "description": "Modified description"
  }
}
```

## Testing

Run hook tests:

```bash
cd packages/shared-py/hooks
python test_hooks.py
```

Test individual hook:

```bash
echo '{"tool":"Bash","input":{"command":"ls -la"}}' | python validate-security-tool.py
```

## Integration

Hooks are referenced in agent/skill frontmatter using `${CLAUDE_PLUGIN_ROOT}`:

### Agent Hook Example

```yaml
---
name: security-auditor
hooks:
  PreToolUse:
    - script: "${CLAUDE_PLUGIN_ROOT}/../../shared-py/hooks/validate-security-tool.py"
      once: false
---
```

### Skill Hook Example

```yaml
---
name: session-capture
hooks:
  Stop:
    - script: "${CLAUDE_PLUGIN_ROOT}/../../shared-py/hooks/auto-save-state.py"
      once: true
---
```

## Portability

All hooks follow Claude Code portability standards:

- ✅ Shebang: `#!/usr/bin/env python3`
- ✅ JSON stdin/stdout protocol
- ✅ Paths use `${CLAUDE_PLUGIN_ROOT}`
- ✅ Double-quoted paths for Windows
- ✅ Forward slashes for cross-platform
- ✅ Exit code 0 on success

## Error Handling

All hooks include try/except blocks that:

1. Catch any exceptions
2. Return `decision: "allow"` with error message
3. Exit with code 0 (never fail the operation)

This ensures hooks never block Claude Code execution even if they encounter errors.

## Claude Code Version Requirements

- **Minimum**: Claude Code 2.1.0
- **Features used**:
  - Agent-scoped hooks (frontmatter)
  - Skill-scoped hooks (frontmatter)
  - `once: true` flag
  - `updatedInput` in PreToolUse hooks

## License

MIT
