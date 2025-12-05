---
description: "DEPRECATED → Use /popkit:project init"
deprecated: true
deprecated_in_favor_of: /popkit:project
---

> **DEPRECATED:** This command is deprecated. Use `/popkit:project init` instead:
> - `/popkit:init-project` → `/popkit:project init`
> - `/popkit:init-project my-app` → `/popkit:project init my-app`
> - `/popkit:init-project --power` → `/popkit:project init --power`

# /popkit:init-project - Project Initialization

Scaffold a new project with complete Claude Code configuration, including optional Power Mode for multi-agent orchestration.

## Usage

```
/popkit:init-project                  # Initialize current directory
/popkit:init-project my-app           # Initialize named project
/popkit:init-project --power          # Initialize with Power Mode setup
```

## Process

Invokes the **pop-project-init** skill with these steps:

### Step 1: Detect Project Type

**Check for project markers:**
```bash
# Node.js
test -f package.json && cat package.json | grep -E '"(next|react|vue|express)"'

# Python
test -f requirements.txt || test -f pyproject.toml || test -f setup.py

# Rust
test -f Cargo.toml

# Go
test -f go.mod
```

### Step 2: Create Directory Structure

**Execute:**
```bash
mkdir -p .claude/{agents,commands,hooks,skills,scripts,logs,plans}
```

### Step 3: Generate CLAUDE.md

Create project-specific instructions based on detected stack. Include:
- Project overview (from README.md or package.json description)
- Development notes (build commands, test commands)
- Architecture patterns (detected from codebase)
- Key files for reference

### Step 4: Initialize STATUS.json

**Execute:**
```bash
echo '{"session_type":"new","last_updated":"'$(date -Iseconds)'","focus":"project_initialization"}' > .claude/STATUS.json
```

### Step 5: Configure settings.json

**Create settings with statusLine enabled:**
```bash
cat > .claude/settings.json << 'EOF'
{
  "statusLine": {
    "enabled": true,
    "format": "default"
  }
}
EOF
```

### Step 6: Update .gitignore

**Append Claude-specific entries:**
```bash
cat >> .gitignore << 'EOF'

# Claude Code
.claude/logs/
.claude/STATUS.json
.claude/power-mode-state.json
EOF
```

### Step 7: Ask About Power Mode

Prompt user with options:
1. **Redis Mode** - Full parallel agents (requires Docker)
2. **File Mode** - Simpler coordination (no dependencies)
3. **Skip** - Set up later with `/popkit:power init`

If Redis Mode selected:
```bash
cat > docker-compose.yml << 'EOF'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
volumes:
  redis-data:
EOF
```

### Step 8: Report and Offer Next Steps

Display summary and recommend:
- `/popkit:morning` for health check
- `/popkit:issue list` to see GitHub issues
- `/popkit:power init start` to start Redis (if selected)

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
- Issue-driven workflows with `/popkit:issue work #N -p`

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
  - Skip: Set up later with /popkit:power init

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
| Skill | `skills/pop-project-init/SKILL.md` |
| Project Detection | Analyzes package.json, requirements.txt, go.mod, Cargo.toml |
| Directory Structure | Creates `.claude/` with agents, commands, hooks, skills, scripts, logs, plans |
| CLAUDE.md Generation | Detects stack, build commands, test commands, architecture patterns |
| Session State | Initializes `STATUS.json` for session continuity |
| Settings | Creates `settings.json` with statusLine enabled |
| Git Integration | Appends Claude-specific entries to `.gitignore` |
| Power Mode State | Writes to `.claude/power-mode-state.json` (optional) |
| Redis Config | Generates `docker-compose.yml` for containerized Redis (optional) |
| Related Skill | `pop-session-capture` / `pop-session-resume` for STATUS.json |

## Related Commands

| Command | Relationship |
|---------|--------------|
| `/popkit:project` | Post-init analysis, MCP generation, quality setup |
| `/popkit:power init` | Start/stop Redis after init |
| `/popkit:morning` | Project health check |
| `/popkit:issue work #N -p` | Work on issue with Power Mode |
