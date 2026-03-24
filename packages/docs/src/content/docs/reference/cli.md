---
title: CLI Reference
description: PopKit CLI commands for installing, configuring, and managing PopKit
---

# CLI Reference

The PopKit CLI (`popkit`) manages installation, provider detection, and MCP server lifecycle.

## Installation

```bash
pip install popkit-cli
# or install everything:
pip install popkit[full]
```

## Commands

### popkit install

Install PopKit packages to `~/.popkit/`.

```bash
popkit install              # Install all packages
popkit install popkit-core  # Install a specific package
```

### popkit update

Update installed packages to the latest version.

```bash
popkit update               # Update all
popkit update popkit-dev    # Update a specific package
```

### popkit provider list

Show detected AI coding tools on your system.

```bash
popkit provider list
```

Example output:

```
Detected Providers:
  ✓ Claude Code    ~/.claude/
  ✓ Cursor         ~/.cursor/
  ✗ Codex CLI      not found
  ✗ Copilot CLI    not found
```

### popkit provider wire

Auto-detect installed AI tools and generate the appropriate configuration files.

```bash
popkit provider wire
```

This creates MCP config entries for each detected tool, pointing to the `popkit-mcp` server.

### popkit mcp start

Launch the MCP server directly.

```bash
popkit mcp start                          # stdio (default)
popkit mcp start --transport sse          # SSE transport
popkit mcp start --port 8080              # Custom port
```

### popkit status

Show PopKit system status — installed packages, detected providers, MCP server health.

```bash
popkit status
```

### popkit version

Show version information.

```bash
popkit version
```

## Environment Variables

| Variable           | Default     | Description                   |
| ------------------ | ----------- | ----------------------------- |
| `POPKIT_HOME`      | `~/.popkit` | PopKit installation directory |
| `POPKIT_DEBUG`     | `false`     | Enable debug logging          |
| `POPKIT_CACHE_TTL` | `86400`     | Cache TTL in seconds          |

## Requirements

- Python 3.11+
- PopKit packages (installed via `popkit install` or `pip install popkit[full]`)
