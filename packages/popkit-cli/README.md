# PopKit CLI

CLI for installing, configuring, and managing PopKit across AI coding tools.

## Commands

```bash
popkit install [package]     # Install packages to ~/.popkit/
popkit provider list         # Show detected AI coding tool providers
popkit provider wire         # Auto-detect tools, generate configs
popkit mcp start             # Launch the MCP server
popkit status                # Show system status
popkit version               # Show version info
```

## Installation

```bash
pip install popkit-cli
popkit install
popkit provider wire
```

## Requirements

- Python 3.11+
- PopKit packages (auto-detected from repo or POPKIT_HOME)
