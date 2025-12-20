---
name: pop-expertise-manage
category: Development
description: Manage agent expertise files and patterns
required_tools:
  - Read
  - Write
  - AskUserQuestion
parameters:
  action:
    type: string
    description: Action to perform (list|show|export|clear|stats)
    required: true
  agent:
    type: string
    description: Agent ID (optional, depends on action)
    required: false
  options:
    type: object
    description: Action-specific options
    required: false
---

# Expertise Management Skill

Implements `/popkit:expertise` command for managing per-agent expertise files.

Part of Agent Expertise System (Issue #201).

## Actions

### list

List all agents with expertise files.

**Implementation:**

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

# Display markdown table
print("| Agent | Patterns | Preferences | Issues | Last Updated |")
print("|-------|----------|-------------|--------|--------------|")
for agent in agents:
    print(f"| {agent['agent_id']} | {agent['patterns']} | {agent['preferences']} | {agent['issues']} | {agent['updated']} |")

print(f"\nTotal: {len(agents)} agents with expertise")
print(f"Combined patterns: {sum(a['patterns'] for a in agents)}")
```

---

### show

Display full expertise YAML for an agent.

**Implementation:**

```python
from pathlib import Path
import yaml
import json

expertise_file = Path(f".claude/expertise/{agent}/expertise.yaml")

if not expertise_file.exists():
    print(f"No expertise found for agent: {agent}")
    print("Expertise files are created automatically as agents learn.")
    return

# Read and display YAML
with open(expertise_file) as f:
    content = f.read()
    print(content)

# Optionally show pending patterns
if options.get('pending'):
    pending_file = Path(f".claude/expertise/{agent}/pending.json")
    if pending_file.exists():
        print("\n--- Pending Patterns (< 3 occurrences) ---")
        pending = json.loads(pending_file.read_text())
        for key, data in pending.items():
            print(f"- {data['pattern']}: {data['occurrences']} occurrences")
```

---

### export

Export expertise to JSON file.

**Implementation:**

```python
from pathlib import Path
from datetime import datetime
import yaml
import json

expertise_file = Path(f".claude/expertise/{agent}/expertise.yaml")

if not expertise_file.exists():
    print(f"No expertise found for agent: {agent}")
    return

data = yaml.safe_load(expertise_file.read_text())

# Add export metadata
data['exported_at'] = datetime.utcnow().isoformat() + 'Z'

# Determine output path
output_path = options.get('output')
if output_path:
    output = Path(output_path)
else:
    output = Path(f"{agent}-expertise-{datetime.now().strftime('%Y-%m-%d')}.json")

# Write JSON
with open(output, 'w') as f:
    json.dump(data, f, indent=2)

print(f"Expertise exported: {output}")
print(f"Size: {output.stat().st_size / 1024:.1f} KB")
```

---

### clear

Clear pending patterns.

**Implementation:**

```python
from pathlib import Path
import json

pending_file = Path(f".claude/expertise/{agent}/pending.json")

if not pending_file.exists():
    print(f"No pending patterns for agent: {agent}")
    return

# Load and count
pending = json.loads(pending_file.read_text())
count = len(pending)

# Confirm unless --confirm flag
if not options.get('confirm'):
    # Use AskUserQuestion for confirmation
    response = AskUserQuestion(
        questions=[{
            "question": f"Clear {count} pending patterns for {agent}?",
            "header": "Confirm",
            "multiSelect": false,
            "options": [
                {"label": "Yes, clear", "description": "Delete pending patterns permanently"},
                {"label": "Cancel", "description": "Keep pending patterns"}
            ]
        }]
    )

    if response != "Yes, clear":
        print("Cancelled")
        return

# Delete pending file
pending_file.unlink()
print(f"Cleared {count} pending patterns for {agent}")
```

---

### stats

Show detailed statistics.

**Implementation:**

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
if agents_data:
    most_active = max(agents_data, key=lambda x: x['patterns'])

    print(f"Total Agents: {len(agents_data)}")
    print(f"Total Patterns: {total_patterns}")
    print(f"Total Preferences: {total_preferences}")
    print(f"Total Issues: {total_issues}")
    print(f"\nPatterns by Category:")
    for category, count in sorted(patterns_by_category.items(), key=lambda x: x[1], reverse=True):
        print(f"  {category}: {count}")
    print(f"\nMost Active Agent: {most_active['id']} ({most_active['patterns']} patterns)")
```

---

## Usage

This skill is invoked by the `/popkit:expertise` command.

**Examples:**

```bash
/popkit:expertise list
/popkit:expertise show code-reviewer
/popkit:expertise export security-auditor
/popkit:expertise clear bug-whisperer
/popkit:expertise stats
```

---

## Integration

| Component | Purpose |
|-----------|---------|
| `hooks/utils/expertise_manager.py` | Core expertise management |
| `.claude/expertise/` | Storage location |
| `hooks/session-start.py` | Loads expertise files |
| `hooks/post-tool-use.py` | Records patterns |

---

## Related Skills

| Skill | Purpose |
|-------|---------|
| `pop-stats-display` | Display learning systems stats |
| `pop-research-manage` | Tier 2 research management |

---

## See Also

- Issue #201: Agent Expertise System
- Command: `/popkit:expertise`
