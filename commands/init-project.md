---
description: Initialize new project with .claude/ directory structure and optional Power Mode setup
---

# /popkit:init-project - Project Initialization

Scaffold a new project with complete Claude Code configuration, including optional Power Mode for multi-agent orchestration.

## Usage

```
/popkit:init-project                  # Initialize current directory
/popkit:init-project my-app           # Initialize named project
/popkit:init-project --power          # Initialize with Power Mode setup
```

## Process

Invokes the **project-init** skill:

1. Detect project type (Node.js, Python, Rust, Go)
2. Create `.claude/` directory structure
3. Generate CLAUDE.md with project instructions
4. Initialize STATUS.json for session continuity
5. Update .gitignore
6. **Ask about Power Mode setup** (Redis for multi-agent orchestration)
7. Report and offer next steps

## What Gets Created

```
.claude/
├── agents/           # Project-specific agents
├── commands/         # Custom slash commands
├── hooks/            # Hook scripts
├── skills/           # Project-specific skills
├── scripts/          # Utility scripts
├── logs/             # Log files
├── plans/            # Implementation plans
├── STATUS.json       # Session state
└── settings.json     # Claude settings

CLAUDE.md             # Project instructions
```

## Power Mode Setup (Optional)

When Power Mode is enabled, additional files are created:

```
.claude/
├── power-mode-state.json   # Power Mode session state
└── docker-compose.yml      # Redis container config (if using Docker)
```

Power Mode provides:
- Multi-agent orchestration via Redis pub/sub
- File-based fallback (works without Docker)
- Status line integration (`[POP] #N Phase: X`)
- Issue-driven workflows with `/popkit:work #N -p`

## Example

```
/popkit:init-project

Detecting project type...
[+] Node.js (Next.js 14) detected

Creating .claude/ structure...
[+] Directories created
[+] CLAUDE.md generated
[+] STATUS.json initialized
[+] .gitignore updated

Would you like to set up Power Mode for multi-agent orchestration?
  - Redis Mode: Full parallel agents (requires Docker)
  - File Mode: Simpler coordination (no dependencies)
  - Skip: Set up later with /popkit:power-init

[User selects Redis Mode]

Setting up Power Mode...
[+] docker-compose.yml created
[+] Run 'docker compose up -d' to start Redis

Project initialized!

Recommended next steps:
1. Review and customize CLAUDE.md
2. Run /popkit:morning for project health check
3. Run /popkit:power init start to start Redis (if Docker installed)
4. Run /popkit:issue list to see GitHub issues with Power Mode recommendations

Would you like me to run any of these?
```

## Architecture Integration

| Component | Integration |
|-----------|-------------|
| Project Detection | Analyzes package.json, requirements.txt, go.mod, Cargo.toml |
| Power Mode State | Writes to `.claude/power-mode-state.json` |
| Redis Config | Generates `docker-compose.yml` for containerized Redis |
| Status Line | Configures statusLine in `settings.json` |

## Related Commands

| Command | Relationship |
|---------|--------------|
| `/popkit:power init` | Start/stop Redis after init |
| `/popkit:morning` | Project health check |
| `/popkit:issue work #N -p` | Work on issue with Power Mode |
