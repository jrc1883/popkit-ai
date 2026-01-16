# MCP Wildcard Permissions Guide

**Updated for Claude Code 2.0.70+**

## Overview

Claude Code 2.0.70 introduced wildcard syntax for MCP (Model Context Protocol) tool permissions, simplifying configuration and reducing maintenance burden.

**Key benefit:** Instead of listing every tool individually, use `mcp__server-name__*` to allow all tools from a trusted server.

## Syntax

### Wildcard Format

```
mcp__{server-name}__{tool-pattern}
```

**Components:**

- `mcp__` - Required prefix
- `{server-name}` - MCP server identifier (from mcpServers config)
- `{tool-pattern}` - Tool name or wildcard (`*`)

### Examples

| Pattern                  | Matches                               |
| ------------------------ | ------------------------------------- |
| `mcp__project-health__*` | All tools from project-health server  |
| `mcp__git-tools__status` | Only the "status" tool from git-tools |
| `mcp__git-tools__git-*`  | All tools starting with "git-"        |

## Configuration Patterns

### Pattern 1: Full Trust (Recommended for First-Party Servers)

Trust all current and future tools from a server you control:

```json
{
  "mcpServers": {
    "project-health": {
      "command": "node",
      "args": [".claude/mcp-servers/project-health/dist/index.js"],
      "permissions": {
        "allowed": ["mcp__project-health__*"]
      }
    }
  }
}
```

**Use when:**

- Server is developed by you/your team
- Tools are primarily read-only (git-status, health-checks)
- You want new tools automatically available

### Pattern 2: Trust with Exceptions

Allow most tools but explicitly block dangerous operations:

```json
{
  "mcpServers": {
    "git-tools": {
      "command": "node",
      "args": [".claude/mcp-servers/git-tools/dist/index.js"],
      "permissions": {
        "allowed": ["mcp__git-tools__*"],
        "denied": [
          "mcp__git-tools__force-push",
          "mcp__git-tools__delete-branch",
          "mcp__git-tools__reset-hard"
        ]
      }
    }
  }
}
```

**Use when:**

- Server has mix of safe/risky operations
- You want explicit control over destructive actions
- Maintaining an allow-list would be tedious

### Pattern 3: Explicit Allow-List (For Third-Party Servers)

Only allow specific tools from untrusted sources:

```json
{
  "mcpServers": {
    "third-party-tools": {
      "command": "node",
      "args": ["./node_modules/third-party-mcp/dist/index.js"],
      "permissions": {
        "allowed": [
          "mcp__third-party-tools__search",
          "mcp__third-party-tools__analyze",
          "mcp__third-party-tools__report"
        ]
      }
    }
  }
}
```

**Use when:**

- Server is from external source
- You want tight security controls
- Only a subset of tools are needed

### Pattern 4: Namespace Wildcards

Allow tools matching a prefix pattern:

```json
{
  "mcpServers": {
    "project-tools": {
      "command": "node",
      "args": [".claude/mcp-servers/project-tools/dist/index.js"],
      "permissions": {
        "allowed": [
          "mcp__project-tools__health-*",
          "mcp__project-tools__git-*",
          "mcp__project-tools__quality-*"
        ]
      }
    }
  }
}
```

**Use when:**

- Tools are organized by namespace
- You want granular control by category
- Server has logical tool groupings

## Migration from Individual Tool Listings

### Before (Claude Code < 2.0.70)

```json
{
  "tools": {
    "git-status": {
      "description": "Get current git repository status",
      "server": "project-health"
    },
    "git-diff": {
      "description": "Show git diff for staged/unstaged changes",
      "server": "project-health"
    },
    "git-log": {
      "description": "Show recent commit history",
      "server": "project-health"
    },
    "health-check": {
      "description": "Run comprehensive project health checks",
      "server": "project-health"
    },
    "typecheck": {
      "description": "Run TypeScript type checking",
      "server": "project-health"
    },
    "lint": {
      "description": "Run linting checks",
      "server": "project-health"
    },
    "test": {
      "description": "Run test suite",
      "server": "project-health"
    }
  },
  "mcpServers": {
    "project-health": {
      "command": "node",
      "args": [".claude/mcp-servers/project-health/dist/index.js"]
    }
  }
}
```

### After (Claude Code 2.0.70+)

```json
{
  "mcpServers": {
    "project-health": {
      "command": "node",
      "args": [".claude/mcp-servers/project-health/dist/index.js"],
      "permissions": {
        "allowed": ["mcp__project-health__*"]
      }
    }
  },
  "resources": {
    "project-context": {
      "description": "Current project context and configuration",
      "server": "project-health"
    }
  }
}
```

**Benefits:**

- ✅ 30+ lines removed
- ✅ New tools automatically available
- ✅ Clearer intent: "trust this server"
- ✅ Less maintenance (no config updates when adding tools)

## Security Considerations

### Safe for First-Party Servers

Wildcard permissions are secure for PopKit-generated MCP servers because:

1. **Trusted Source** - Servers are generated by PopKit or your team
2. **Read-Only Focus** - Most tools are informational (status, checks, reports)
3. **Explicit Denial** - Risky operations can be explicitly blocked
4. **User Control** - Users can override with specific tool lists

### Caution for Third-Party Servers

For external MCP servers:

- ✅ Review server source code before wildcarding
- ✅ Use explicit allow-lists for untrusted sources
- ✅ Prefer namespace wildcards over full wildcards
- ✅ Monitor server updates for new tools

### Recommended Defaults

| Server Type             | Recommended Pattern                       |
| ----------------------- | ----------------------------------------- |
| PopKit-generated        | Full wildcard (`*`)                       |
| First-party (your team) | Full wildcard (`*`)                       |
| Community/verified      | Namespace wildcards (`health-*`, `git-*`) |
| Third-party/unverified  | Explicit allow-list                       |

## Backward Compatibility

### Hybrid Approach

Keep `tools` section for documentation while using wildcard permissions:

```json
{
  "tools": {
    "health-check": {
      "description": "Run comprehensive project health checks",
      "server": "project-health",
      "note": "Actual permissions via wildcard below"
    },
    "git-status": {
      "description": "Get current git repository status",
      "server": "project-health",
      "note": "Actual permissions via wildcard below"
    }
  },
  "mcpServers": {
    "project-health": {
      "permissions": {
        "allowed": ["mcp__project-health__*"]
      }
    }
  }
}
```

**Benefits:**

- Documentation of available tools
- Permission control via wildcard
- Discoverable capabilities
- Works with older Claude Code versions (tools section ignored if wildcards present)

## PopKit Integration

### Generated MCP Servers

PopKit's `/popkit:project mcp` command generates servers with wildcard permissions by default:

```json
{
  "mcpServers": {
    "{project-name}-dev": {
      "command": "node",
      "args": [".claude/mcp-servers/{project-name}-dev/dist/index.js"],
      "permissions": {
        "allowed": ["mcp__{project-name}-dev__*"]
      }
    }
  }
}
```

### Overriding Defaults

Users can customize permissions after generation:

```bash
# Generate MCP server
/popkit:project mcp

# Edit .claude/settings.json to customize permissions
# Change from wildcard to explicit allow-list if needed
```

## Troubleshooting

### Tools Not Appearing

**Problem:** Tools don't show up in Claude Code after adding wildcard

**Solutions:**

1. Verify server name matches: `"project-health"` in mcpServers vs `mcp__project-health__*`
2. Restart Claude Code to reload MCP configuration
3. Check server logs: `node .claude/mcp-servers/{server}/dist/index.js`
4. Verify server builds successfully: `cd .claude/mcp-servers/{server} && npm run build`

### Permission Denied

**Problem:** Tool call fails with permission error

**Solutions:**

1. Check if tool is in denied list: `"denied": ["mcp__server__tool"]`
2. Verify wildcard syntax: must be `mcp__server__*` not `mcp__server_*`
3. Ensure server name is exact match (case-sensitive)

### Wildcard Not Working

**Problem:** Wildcard syntax not recognized

**Solutions:**

1. Verify Claude Code version: `claude --version` (need 2.0.70+)
2. Check .mcp.json syntax (valid JSON, correct structure)
3. Try explicit tool list as fallback

## Examples

### Full Example: Multi-Server Configuration

```json
{
  "$schema": "https://claude.ai/schemas/mcp.json",
  "version": "1.0.0",
  "mcpServers": {
    "project-health": {
      "command": "node",
      "args": [".claude/mcp-servers/project-health/dist/index.js"],
      "permissions": {
        "allowed": ["mcp__project-health__*"]
      }
    },
    "git-tools": {
      "command": "node",
      "args": [".claude/mcp-servers/git-tools/dist/index.js"],
      "permissions": {
        "allowed": ["mcp__git-tools__*"],
        "denied": ["mcp__git-tools__force-push", "mcp__git-tools__delete-branch"]
      }
    },
    "third-party-analyzer": {
      "command": "npx",
      "args": ["third-party-mcp@latest"],
      "permissions": {
        "allowed": ["mcp__third-party-analyzer__analyze", "mcp__third-party-analyzer__report"]
      }
    }
  },
  "resources": {
    "project-context": {
      "description": "Current project configuration and context",
      "server": "project-health"
    },
    "git-history": {
      "description": "Recent commit history and branch information",
      "server": "git-tools"
    }
  }
}
```

## References

- [Claude Code CHANGELOG 2.0.70](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md#2070)
- PopKit Issue [#93](https://github.com/jrc1883/popkit-claude/issues/93)
- [MCP Specification](https://spec.modelcontextprotocol.io/)

## See Also

- `/popkit:project mcp` - Generate project-specific MCP server
- `packages/popkit-core/skills/pop-mcp-generator/` - MCP generation skill
- `examples/.mcp.json` - Reference configuration
