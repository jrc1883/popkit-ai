# PopKit Upgrade Plan: Native Swarm & Sandbox Orchestration

## Executive Summary
This upgrade transitions `popkit-core` from sequential tool execution to **Native Multi-Agent Orchestration** using Claude Code's experimental `agentTeams` capability. It introduces visual concurrency via Tmux and safe remote execution via E2B Sandboxes.

## Architecture Changes

### 1. The "Team Lead" Upgrade (Coordinator)
The `power-coordinator` agent is redefined. Instead of running a loop itself, it now acts as a manager using the native `TeamCreate` tool.
* **Old Behavior:** Loop -> Tool Call -> Loop.
* **New Behavior:** `TeamCreate` -> `TaskCreate` -> Monitor via `TaskList` -> `TeamClose`.

### 2. The Sandbox Layer (Safety)
We are introducing `pop-sandbox` (wrapping the E2B SDK).
* **Why:** Native agents run in parallel. If two agents edit `utils.py` simultaneously on the local file system, they will conflict.
* **Fix:** Agents must provision ephemeral environments (`sandbox_create`) for heavy coding or testing tasks.

### 3. The Auto-Drive Hook
The `teammate-idle` hook is updated to support **Auto-Claiming**.
* **Logic:** When a teammate is idle, the hook checks `TaskList`. If an unassigned task exists, the hook forces the teammate to claim it. This removes "manager latency."

## Implementation Steps (For Agents)
1.  **Install Dependencies:** Add `e2b-code-interpreter` and `tmux` to the environment.
2.  **Deploy Skill:** Create `packages/popkit-core/skills/pop-sandbox/`.
3.  **Update Agent:** Overwrite `packages/popkit-core/agents/tier-2-on-demand/power-coordinator/AGENT.md`.
4.  **Update Hook:** Modify `packages/popkit-core/hooks/teammate-idle.py`.
5.  **Configure:** User must update `~/.claude/settings.json` with experimental flags.

## Configuration: settings.json

To enable Native Swarm features, users must add the following experimental flags to their `~/.claude/settings.json`:

```json
{
  "experimental": {
    "agentTeams": true,
    "backgroundAgents": true
  }
}
```

### E2B API Key

The E2B SDK automatically reads `E2B_API_KEY` from your system environment variables.

**Windows:** If you have `E2B_API_KEY` set as a Windows environment variable, you're all set - no additional configuration needed.

**Alternative (if not using system env vars):** Add to `~/.claude/settings.json`:
```json
{
  "env": {
    "E2B_API_KEY": "<your-e2b-api-key>"
  }
}
```

| Variable | Description | Where to Get |
|----------|-------------|--------------|
| `E2B_API_KEY` | API key for E2B sandbox service | https://e2b.dev/dashboard |

### Optional: Tmux Visual Dashboard

For visual concurrency monitoring, install tmux:

```bash
# macOS
brew install tmux

# Ubuntu/Debian
sudo apt install tmux

# Windows (via WSL or scoop)
scoop install tmux
```

### Verifying Configuration

After configuration, verify with:

```bash
# Check E2B connection
python -c "from e2b_code_interpreter import Sandbox; print('E2B OK')"

# Check tmux
tmux -V
```

## Implementation Status

- [x] Dependencies added to `requirements.txt`
- [x] Sandbox skill enhanced with full CRUD operations
- [x] Power-coordinator agent updated with TeamCreate workflow
- [x] TeammateIdle hook enhanced with auto-claiming
- [x] Configuration documented