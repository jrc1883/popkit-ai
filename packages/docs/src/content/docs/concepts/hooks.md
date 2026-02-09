---
title: Hooks
description: Event-driven automation in PopKit
---

# Hooks

Hooks are event-driven scripts that execute at specific points in the Claude Code lifecycle. PopKit includes 23 hooks for various events.

## What are Hooks?

Hooks in PopKit:

- **Event-driven**: Triggered by specific lifecycle events
- **Portable**: Use cross-platform path conventions
- **Validated**: Follow JSON stdin/stdout protocol
- **Tested**: Have comprehensive test coverage

## Hook Events

### Session Lifecycle

- `SessionStart`: When Claude Code session begins
- `SessionEnd`: When session ends
- `SessionResume`: When session is restored

### Interaction Events

- `FirstMessage`: Before first user message
- `UserMessage`: After each user message
- `AssistantMessage`: After Claude's response

### File Events

- `FileCreate`: When file is created
- `FileModify`: When file is modified
- `FileDelete`: When file is deleted

### Git Events

- `GitCommit`: Before/after git commits
- `GitPush`: Before/after git push
- `GitPR`: When pull request is created

## Hook Protocol

All hooks use a standard JSON protocol:

**Input** (stdin):

```json
{
  "event": "SessionStart",
  "data": {
    "cwd": "/path/to/project",
    "timestamp": "2026-01-14T12:00:00Z"
  }
}
```

**Output** (stdout):

```json
{
  "status": "success",
  "message": "Hook executed successfully",
  "data": {}
}
```

## Hook Standards

PopKit hooks follow Claude Code portability standards:

- Use `${CLAUDE_PLUGIN_ROOT}` for plugin-relative paths
- Double-quoted paths for Windows compatibility
- Forward slashes for cross-platform support
- Python shebang: `#!/usr/bin/env python3`

## Creating Custom Hooks

Hooks are defined in `hooks/hooks.json` with:

```json
{
  "SessionStart": {
    "type": "command",
    "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/session-start.py\"",
    "timeout": 10000
  }
}
```

See the [Hook Development Guide](/guides/hooks/) for details.

## Next Steps

- Explore [Power Mode](/features/power-mode/)
- Learn about [Git Workflows](/features/git-workflows/)
- Review [Hook Development Guide](/guides/hooks/)
