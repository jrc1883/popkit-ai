# PopKit Setup for Claude Code

Claude Code has **native** PopKit support via the plugin system. This guide covers both options.

## Option 1: Native Plugin (Recommended)

The PopKit plugin is the recommended way to use PopKit with Claude Code. It provides:

- Full skill and command support
- Agent system with tiered activation
- Hooks for automation
- Output styles
- Power Mode coordination

### Installation

```bash
# Add the marketplace
/plugin marketplace add jrc1883/popkit-claude

# Install the plugin
/plugin install popkit@popkit-claude
```

Then restart Claude Code.

### Usage

After installation, all `/popkit:*` commands are available:

```
/popkit:routine morning     # Morning health check
/popkit:dev brainstorm      # Start brainstorming
/popkit:git commit          # Smart commit
```

See the [main PopKit README](https://github.com/jrc1883/popkit-claude) for full documentation.

## Option 2: Universal MCP Server

If you prefer the universal MCP approach (same setup as Cursor/Continue):

### Installation

```bash
npm install -g @popkit/mcp
```

### Configuration

Create `.mcp.json` in your project:

```json
{
  "mcpServers": {
    "popkit": {
      "command": "popkit-mcp",
      "env": {
        "POPKIT_API_KEY": "your-api-key-here",
        "POPKIT_CLIENT": "claude-code"
      }
    }
  }
}
```

### Usage

Access PopKit tools via MCP:

```
Use the popkit_pattern_search tool to find authentication patterns
```

## Comparison

| Feature | Native Plugin | MCP Server |
|---------|---------------|------------|
| Skills | ✅ Full | ❌ Not available |
| Slash commands | ✅ /popkit:* | ❌ Tool calls only |
| Agents | ✅ 30+ agents | ✅ Via search tool |
| Hooks | ✅ Full | ❌ Not available |
| Output styles | ✅ Full | ❌ Plain JSON |
| Power Mode | ✅ Full | ✅ Lite version |
| Pattern search | ✅ Via skill | ✅ Via tool |
| Workflows | ✅ Via command | ✅ Via tool |
| Setup complexity | Low | Medium |

**Recommendation:** Use the native plugin for the best experience. The MCP server is useful for:
- Consistency with other tools (Cursor/Continue)
- Testing the universal MCP approach
- Specific MCP-only features

## Hybrid Approach

You can use both! The native plugin and MCP server work independently:

1. Install the native plugin for commands/skills
2. Configure MCP server for additional tools
3. Claude Code will show tools from both sources

## Resources

- [PopKit Plugin Documentation](https://github.com/jrc1883/popkit-claude)
- [Claude Code Plugin Guide](https://docs.anthropic.com/claude-code/plugins)
- [PopKit Cloud](https://api.popkit.dev)
