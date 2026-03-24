---
title: Troubleshooting
description: Common issues and solutions for PopKit installation and usage
---

# Troubleshooting

## Installation Issues

### `popkit-mcp` command not found

After `pip install popkit-mcp`, the command may not be on your PATH.

**Fix:** Check where pip installed the script:

```bash
python -m site --user-base
# Add the Scripts/ (Windows) or bin/ (macOS/Linux) subdirectory to your PATH
```

Or run directly via Python:

```bash
python -m popkit_mcp.server --transport stdio
```

### Python version error

PopKit requires **Python 3.11+**. Check your version:

```bash
python --version
```

If you have multiple Python versions, use `python3.11` or `python3.12` explicitly.

### pip install fails with dependency conflicts

Try installing in a clean virtual environment:

```bash
python -m venv popkit-env
source popkit-env/bin/activate  # Linux/macOS
# or: popkit-env\Scripts\activate  # Windows
pip install popkit[full]
```

---

## MCP Server Issues

### Server crashes with UnicodeDecodeError

```
UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0
```

**Cause:** A `.env` file in your home directory or project is saved as UTF-16 instead of UTF-8. The MCP SDK's `pydantic-settings` auto-reads `.env` files and can't handle UTF-16.

**Fix:** Convert the file to UTF-8:

```bash
# Find the problematic .env file
file ~/.env
# If it says "UTF-16", convert it:
iconv -f UTF-16LE -t UTF-8 ~/.env > ~/.env.tmp && mv ~/.env.tmp ~/.env
```

### Server starts but Cursor doesn't show tools

1. Check Cursor Settings > Tools & MCP — look for a green dot next to "popkit"
2. If red/missing, check the MCP log in Cursor's Output panel
3. Verify the server starts manually: `popkit-mcp --help`
4. On Windows, you may need the `cmd /c` wrapper:

```json
{
  "mcpServers": {
    "popkit": {
      "command": "cmd",
      "args": ["/c", "popkit-mcp", "--transport", "stdio"]
    }
  }
}
```

### Cursor tool limit (~40 tools)

Cursor has a limit of approximately 40 tools across all MCP servers. If you have many MCP servers installed, tools may be silently dropped.

**Fix:** Disable unused MCP servers in Cursor Settings > Tools & MCP.

---

## Claude Code Plugin Issues

### Skills/commands not appearing after install

1. Restart Claude Code completely (exit and relaunch)
2. Verify the marketplace is registered:

```bash
/plugin marketplace list
```

3. If popkit-claude isn't listed, re-add it:

```bash
/plugin marketplace add jrc1883/popkit-claude
```

### Plugin version mismatch

If you see unexpected behavior, check your installed version:

```bash
/plugin list
```

Update to the latest:

```bash
/plugin update popkit-core@popkit-claude
```

---

## Hook Failures

### Hook script fails with ImportError

PopKit hooks run as standalone Python subprocesses. They use `sys.path.insert` to find local utilities, which means they can't be imported as regular Python modules.

**If you're writing custom hooks:** Use the same `sys.path.insert` pattern found in existing hooks, and import from `popkit_shared.utils` for shared functionality.

### Hook times out

Hooks have a default timeout. If a hook performs network operations or heavy computation, it may be killed before completing.

**Fix:** Keep hooks fast and focused. Move expensive operations to skills or agents instead.

---

## Power Mode Issues

### "No background agent support" error

Power Mode's Native Async mode requires Claude Code 2.1.33+. Check your version:

```bash
claude --version
```

### Power Mode agents fail silently

Check the Power Mode status:

```bash
/popkit-core:power status
```

If agents are failing, run with debug logging:

```bash
/popkit-core:power start --verbose
```

---

## Getting Help

- **GitHub Issues:** [github.com/jrc1883/popkit-claude/issues](https://github.com/jrc1883/popkit-claude/issues)
- **Documentation:** [popkit.unjoe.me](https://popkit.unjoe.me)
