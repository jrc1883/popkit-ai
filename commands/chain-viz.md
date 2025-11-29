---
name: chain-viz
description: Visualize workflow chains with validation and performance metrics
---

# /popkit:chain-viz

Visualize workflow chains from `agents/config.json` with ASCII diagrams, validation status, and performance metrics.

## Usage

```bash
/popkit:chain-viz                    # List all workflows
/popkit:chain-viz feature-dev        # Visualize specific workflow
/popkit:chain-viz feature-dev status # Show execution status
/popkit:chain-viz feature-dev metrics # Show performance metrics
/popkit:chain-viz validate           # Validate all chains
```

## Instructions

You are the chain visualization engine. Your job is to display workflow chains in an easy-to-understand format.

### Subcommand: List (default)

When called without arguments, list all available workflows:

```bash
# Read workflow definitions
python -c "
import json
with open('agents/config.json') as f:
    config = json.load(f)
    workflows = config.get('workflows', {})
    for wid, w in workflows.items():
        phases = len(w.get('phases', []))
        agents = w.get('agents', [])
        if phases:
            print(f'{wid}: {phases} phases')
        else:
            print(f'{wid}: {len(agents)} agents ({\"sequential\" if w.get(\"sequential\") else \"parallel\"})')
"
```

Display format:
```
Available Workflows
===================

1. feature-dev      7 phases, 3 agents
2. debug            2 agents, sequential
3. security-audit   1 agent, parallel

Use /popkit:chain-viz <workflow-id> to visualize a specific workflow.
```

### Subcommand: Visualize Workflow

When user specifies a workflow ID, show ASCII visualization:

```
Workflow: feature-dev (7-Phase Feature Development)
====================================================

  [Discovery]
       |
       v
  [Exploration]  code-explorer
       |
       v
  [Questions]
       |
       v
  [Architecture]  code-architect
       |
       v
  [Implementation]
       |
       v
  [Review]  code-reviewer
       |
       v
  [Summary]

Phases: 7 | Agents: 3 | Success Rate: 87%
```

For sequential workflows:
```
Workflow: debug (Debug Workflow)
================================

  [bug-whisperer]
       |
       v
  [log-analyzer]

Agents: 2 | Mode: sequential
```

For parallel workflows:
```
Workflow: security-audit (Security Audit)
==========================================

  [parallel execution]
    - security-auditor

Agents: 1 | Mode: parallel
```

### Subcommand: Status

Show current/recent execution status:

```bash
# Read chain metrics
cat ~/.claude/chain-metrics.json
```

Display format:
```
Workflow: feature-dev - Recent Runs
====================================

Run #1 (abc123) - 2h ago
  Status: COMPLETED
  Duration: 12m 30s
  Steps:
    [Discovery]      DONE      00:45
    [Exploration]    DONE      02:15  confidence: 85
    [Questions]      DONE      01:30
    [Architecture]   DONE      03:20
    [Implementation] DONE      04:10
    [Review]         DONE      01:45
    [Summary]        DONE      00:35

Run #2 (def456) - Yesterday
  Status: COMPLETED
  Duration: 15m 10s
  ...
```

### Subcommand: Metrics

Show performance metrics and bottlenecks:

```bash
# Read and analyze chain metrics
python hooks/chain-metrics.py
```

Display format:
```
Workflow: feature-dev - Metrics
===============================

Overall Stats:
  Total runs:     15
  Success rate:   87%
  Avg duration:   12m 30s

Step Performance:
  Step              Avg Time   Success   Bottleneck
  ---------------   --------   -------   ----------
  Discovery         0:45       100%
  Exploration       2:15       93%
  Questions         1:30       100%
  Architecture      3:20       87%       [!]
  Implementation    4:10       80%       [!]
  Review            1:45       93%
  Summary           0:35       100%

Top Bottlenecks:
  1. Implementation (4:10 avg)
  2. Architecture (3:20 avg)
  3. Exploration (2:15 avg)
```

### Subcommand: Validate

Run chain validation on all workflows:

```bash
# Run validator
python hooks/chain-validator.py
```

Display format:
```
Chain Validation Results
========================

feature-dev:
  Status: VALID
  Phases: 7
  Agents: 3 (all found)
  Warnings: 0

debug:
  Status: VALID
  Agents: 2 (all found)
  Warnings: 0

security-audit:
  Status: VALID
  Agents: 1 (all found)
  Warnings: 0

---
Total: 3 workflows | 0 errors | 0 warnings
```

If there are warnings:
```
feature-dev:
  Status: VALID (with warnings)
  Warnings:
    - Phase 'Architecture': Agent 'code-architect-v2' not found in tier definitions
```

## Workflow Configuration

Workflows are defined in `agents/config.json`:

```json
{
  "workflows": {
    "feature-dev": {
      "phases": [
        {"name": "Discovery", "agents": []},
        {"name": "Exploration", "agents": ["code-explorer"]},
        {"name": "Questions", "agents": []},
        {"name": "Architecture", "agents": ["code-architect"]},
        {"name": "Implementation", "agents": []},
        {"name": "Review", "agents": ["code-reviewer"]},
        {"name": "Summary", "agents": []}
      ]
    },
    "debug": {
      "agents": ["bug-whisperer", "log-analyzer"],
      "sequential": true
    }
  }
}
```

## Metrics Storage

Metrics are stored in `~/.claude/chain-metrics.json` and include:
- Run history with timestamps and durations
- Step-level timing and status
- Aggregate statistics per workflow
- Bottleneck identification

## Related

- `pop-chain-management` skill - Programmatic chain operations
- `chain-validator.py` hook - Validates chains before execution
- `chain-metrics.py` hook - Tracks execution metrics
