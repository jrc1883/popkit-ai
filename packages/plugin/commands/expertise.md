---
name: expertise
category: Development
description: Manage agent expertise files and patterns
usage: |
  /popkit:expertise list [agent]        - List expertise for agent(s)
  /popkit:expertise show <agent>        - Show full expertise for agent
  /popkit:expertise export <agent>      - Export expertise to JSON
  /popkit:expertise clear <agent>       - Clear pending patterns
  /popkit:expertise stats               - Show expertise statistics
argument-hint: "<subcommand> [agent] [options]"
examples:
  - /popkit:expertise list
  - /popkit:expertise show code-reviewer
  - /popkit:expertise export security-auditor
  - /popkit:expertise clear bug-whisperer --confirm
  - /popkit:expertise stats --json
---

# /popkit:expertise - Expertise Management

Manage per-agent expertise files in the three-tier learning system (Issue #201).

Agents accumulate project-specific knowledge over time through conservative learning (3+ occurrences required before patterns are promoted to expertise).

## Usage

```
/popkit:expertise <subcommand> [agent] [options]
```

## Subcommands

| Subcommand | Description |
|------------|-------------|
| `list` | List expertise summary for all agents (default) |
| `show` | Display full expertise YAML for specific agent |
| `export` | Export expertise to JSON file |
| `clear` | Clear pending patterns (< 3 occurrences) |
| `stats` | Show detailed statistics across all agents |

---

## Subcommand: list (default)

List all agents with expertise files and their summary statistics.

```
/popkit:expertise                    # List all agents
/popkit:expertise list               # Same as above
/popkit:expertise list code-reviewer # Show specific agent only
```

### Output Format

```
Agent Expertise Summary:

| Agent | Patterns | Preferences | Issues | Last Updated |
|-------|----------|-------------|--------|--------------|
| code-reviewer    | 18 | 34 | 5 | 2 hours ago |
| bug-whisperer    | 12 | 21 | 3 | 1 day ago   |
| security-auditor | 15 | 29 | 8 | 4 hours ago |

Total: 3 agents with expertise
Combined patterns: 45
Combined preferences: 84

Use /popkit:expertise show <agent> to view full details
```

### Implementation

```python
from pathlib import Path
import yaml
from datetime import datetime

expertise_dir = Path(".claude/expertise")

if not expertise_dir.exists():
    print("No expertise files found. Agents will create them as they learn.")
    return

agents = []
for agent_dir in expertise_dir.iterdir():
    if agent_dir.is_dir():
        expertise_file = agent_dir / "expertise.yaml"
        if expertise_file.exists():
            data = yaml.safe_load(expertise_file.read_text())

            # Calculate time since last update
            updated = datetime.fromisoformat(data['updated_at'].replace('Z', ''))
            delta = datetime.utcnow() - updated
            if delta.days > 0:
                time_ago = f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
            elif delta.seconds // 3600 > 0:
                hours = delta.seconds // 3600
                time_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
            else:
                time_ago = "just now"

            agents.append({
                'agent_id': data['agent_id'],
                'patterns': data['stats']['total_patterns'],
                'preferences': sum(len(v) for v in data['preferences'].values()),
                'issues': data['stats']['total_issues'],
                'updated': time_ago
            })

# Sort by patterns (most active first)
agents.sort(key=lambda x: x['patterns'], reverse=True)

# Display table
print(format_table(agents))
```

---

## Subcommand: show

Display full expertise YAML content for a specific agent.

```
/popkit:expertise show code-reviewer
/popkit:expertise show bug-whisperer --patterns    # Show only patterns section
/popkit:expertise show security-auditor --pending  # Include pending patterns
```

### Flags

| Flag | Description |
|------|-------------|
| `--patterns` | Show only patterns section |
| `--preferences` | Show only preferences section |
| `--pending` | Include pending.json (patterns < 3 occurrences) |

### Output Format

```yaml
# Agent Expertise - code-reviewer
# Last updated: 2025-12-19T15:30:00Z

version: "1.0.0"
agent_id: "code-reviewer"
project: "popkit"

patterns:
  - id: "pat-001"
    category: "error-handling"
    pattern: "wrap async functions in try/catch"
    trigger: "unhandled promise rejection"
    confidence: 0.85
    occurrences: 5
    examples:
      - file: "src/api/users.ts"
        before: "async login() { await db.query(...) }"
        after: "async login() { try { await db.query(...) } catch (e) { ... } }"

preferences:
  code_style:
    - "use 2-space indentation (project standard)"
    - "prefer named exports over default exports"

common_issues:
  - id: "iss-001"
    pattern: "missing null checks on API responses"
    severity: "medium"
    occurrences: 12
    solution: "add optional chaining or null guards"

stats:
  total_patterns: 18
  total_issues: 5
  reviews_conducted: 45
  avg_confidence: 0.885
```

### Implementation

```python
from pathlib import Path
import yaml

expertise_file = Path(f".claude/expertise/{agent_id}/expertise.yaml")

if not expertise_file.exists():
    print(f"No expertise found for agent: {agent_id}")
    print("Expertise files are created automatically as agents learn.")
    return

data = yaml.safe_load(expertise_file.read_text())

# Display full YAML or filtered sections based on flags
if flags.patterns:
    print(yaml.dump({'patterns': data['patterns']}, default_flow_style=False))
elif flags.preferences:
    print(yaml.dump({'preferences': data['preferences']}, default_flow_style=False))
else:
    print(expertise_file.read_text())

# Optionally show pending patterns
if flags.pending:
    pending_file = Path(f".claude/expertise/{agent_id}/pending.json")
    if pending_file.exists():
        print("\n--- Pending Patterns (< 3 occurrences) ---")
        pending = json.loads(pending_file.read_text())
        for key, data in pending.items():
            print(f"{data['pattern']}: {data['occurrences']} occurrences")
```

---

## Subcommand: export

Export agent expertise to JSON file for sharing or backup.

```
/popkit:expertise export code-reviewer
/popkit:expertise export code-reviewer --output ~/expertise-backup.json
/popkit:expertise export --all  # Export all agents
```

### Flags

| Flag | Description |
|------|-------------|
| `--output <path>` | Specify output file path |
| `--all` | Export all agents to separate files |
| `--merge` | Merge all agents into single JSON |

### Output

Creates JSON file with full expertise data:

```json
{
  "version": "1.0.0",
  "agent_id": "code-reviewer",
  "project": "popkit",
  "exported_at": "2025-12-19T16:00:00Z",
  "patterns": [...],
  "preferences": {...},
  "common_issues": [...],
  "stats": {...}
}
```

**File saved:** `code-reviewer-expertise-2025-12-19.json`

### Implementation

```python
from pathlib import Path
from datetime import datetime
import json

expertise_file = Path(f".claude/expertise/{agent_id}/expertise.yaml")

if not expertise_file.exists():
    print(f"No expertise found for agent: {agent_id}")
    return

data = yaml.safe_load(expertise_file.read_text())

# Add export metadata
data['exported_at'] = datetime.utcnow().isoformat() + 'Z'

# Determine output path
if output_path:
    output = Path(output_path)
else:
    output = Path(f"{agent_id}-expertise-{datetime.now().strftime('%Y-%m-%d')}.json")

# Write JSON
with open(output, 'w') as f:
    json.dump(data, f, indent=2)

print(f"Expertise exported: {output}")
print(f"Size: {output.stat().st_size / 1024:.1f} KB")
```

---

## Subcommand: clear

Clear pending patterns (those with fewer than 3 occurrences).

```
/popkit:expertise clear code-reviewer
/popkit:expertise clear code-reviewer --confirm  # Skip confirmation
/popkit:expertise clear --all                     # Clear all agents
```

### Flags

| Flag | Description |
|------|-------------|
| `--confirm` | Skip confirmation prompt |
| `--all` | Clear pending patterns for all agents |

### Confirmation Prompt

```
Use AskUserQuestion tool with:
- question: "Clear pending patterns for code-reviewer? (12 patterns with < 3 occurrences will be deleted)"
- header: "Confirm"
- options:
  1. label: "Yes, clear"
     description: "Delete pending patterns permanently"
  2. label: "Cancel"
     description: "Keep pending patterns"
- multiSelect: false
```

### Implementation

```python
from pathlib import Path
import json

pending_file = Path(f".claude/expertise/{agent_id}/pending.json")

if not pending_file.exists():
    print(f"No pending patterns for agent: {agent_id}")
    return

# Load and show count
pending = json.loads(pending_file.read_text())
count = len(pending)

if not confirm_flag:
    # Use AskUserQuestion for confirmation
    response = ask_user(f"Clear {count} pending patterns for {agent_id}?")
    if response != "Yes, clear":
        print("Cancelled")
        return

# Delete pending file
pending_file.unlink()
print(f"Cleared {count} pending patterns for {agent_id}")
```

---

## Subcommand: stats

Show detailed statistics across all agents.

```
/popkit:expertise stats
/popkit:expertise stats --json
/popkit:expertise stats --by-category  # Group patterns by category
```

### Output Format

```
+===================================================================+
|                   Agent Expertise Statistics                       |
+===================================================================+
| Total Agents: 3                                                    |
| Total Patterns: 45                                                 |
| Total Preferences: 84                                              |
| Total Issues: 16                                                   |
+-------------------------------------------------------------------+
| Patterns by Category:                                              |
|   error-handling: 18                                               |
|   code-style: 12                                                   |
|   performance: 8                                                   |
|   security: 7                                                      |
+-------------------------------------------------------------------+
| Most Active Agent: code-reviewer (18 patterns)                     |
| Highest Confidence: security-auditor (avg 0.92)                    |
| Last Updated: code-reviewer (2 hours ago)                          |
+-------------------------------------------------------------------+
| Pending Patterns:                                                  |
|   code-reviewer: 5 patterns (< 3 occurrences)                      |
|   bug-whisperer: 3 patterns (< 3 occurrences)                      |
|   security-auditor: 2 patterns (< 3 occurrences)                   |
+===================================================================+
```

### Implementation

```python
from pathlib import Path
import yaml
import json
from collections import defaultdict

expertise_dir = Path(".claude/expertise")

if not expertise_dir.exists():
    print("No expertise files found.")
    return

# Collect stats
total_patterns = 0
total_preferences = 0
total_issues = 0
patterns_by_category = defaultdict(int)
agents_data = []

for agent_dir in expertise_dir.iterdir():
    if agent_dir.is_dir():
        expertise_file = agent_dir / "expertise.yaml"
        if expertise_file.exists():
            data = yaml.safe_load(expertise_file.read_text())

            total_patterns += data['stats']['total_patterns']
            total_preferences += sum(len(v) for v in data['preferences'].values())
            total_issues += data['stats']['total_issues']

            for pattern in data['patterns']:
                patterns_by_category[pattern['category']] += 1

            agents_data.append({
                'id': data['agent_id'],
                'patterns': data['stats']['total_patterns'],
                'avg_confidence': data['stats']['avg_confidence']
            })

# Find most active
most_active = max(agents_data, key=lambda x: x['patterns'])

# Display formatted stats
print(format_stats_table({
    'total_agents': len(agents_data),
    'total_patterns': total_patterns,
    'total_preferences': total_preferences,
    'total_issues': total_issues,
    'by_category': dict(patterns_by_category),
    'most_active': most_active
}))
```

---

## Storage Structure

```
.claude/
  expertise/
    code-reviewer/
      expertise.yaml        # Promoted patterns (3+ occurrences)
      pending.json          # Patterns with < 3 occurrences
    bug-whisperer/
      expertise.yaml
      pending.json
    security-auditor/
      expertise.yaml
      pending.json
```

---

## Conservative Learning Logic

Patterns require **3+ occurrences** before promotion to expertise:

1. **First occurrence** → Recorded in `pending.json`
2. **Second occurrence** → Counter incremented in `pending.json`
3. **Third occurrence** → Promoted to `expertise.yaml`, removed from pending

This conservative threshold prevents false positives and ensures only consistent patterns are learned.

---

## Examples

```bash
# List all agents with expertise
/popkit:expertise

# Show full expertise for code-reviewer
/popkit:expertise show code-reviewer

# Show only patterns section
/popkit:expertise show code-reviewer --patterns

# Include pending patterns
/popkit:expertise show code-reviewer --pending

# Export to JSON
/popkit:expertise export code-reviewer

# Clear pending patterns
/popkit:expertise clear code-reviewer

# Show statistics
/popkit:expertise stats

# JSON output
/popkit:expertise stats --json
```

---

## Architecture Integration

| Component | Integration |
|-----------|-------------|
| Expertise Manager | `hooks/utils/expertise_manager.py` |
| Session Start | `hooks/session-start.py` (loads expertise) |
| Post Tool Use | `hooks/post-tool-use.py` (records patterns) |
| Pattern Threshold | Conservative 3+ occurrences |
| Storage Format | YAML for expertise, JSON for pending |

---

## Related Commands

| Command | Purpose |
|---------|---------|
| `/popkit:stats --learning` | Show learning systems stats |
| `/popkit:research` | Tier 2 research index management |
| `/popkit:project analyze` | Project analysis (may suggest expertise) |

---

## See Also

- Issue #201: Agent Expertise System
- Architecture: `docs/plans/2025-12-19-agent-expertise-system-architecture.md`
- Implementation: `docs/plans/2025-12-19-agent-expertise-implementation-plan.md`
