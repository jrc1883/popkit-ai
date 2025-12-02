---
description: "Debug and analyze agent routing decisions"
---

# /popkit:routing-debug - Agent Routing Debugger

Analyze and debug agent routing decisions to understand why specific agents are selected.

## Usage

```
/popkit:routing-debug "your prompt"          # Analyze routing for a prompt
/popkit:routing-debug explain <agent>        # Show agent's routing keywords
/popkit:routing-debug keywords               # List all routing keywords
/popkit:routing-debug trace "prompt"         # Show detailed routing trace
/popkit:routing-debug compare "prompt"       # Compare all agent scores
```

## Process

1. **Use the routing-debug skill** for analysis
2. **Parse the prompt** to extract keywords
3. **Match against routing rules:**
   - Keyword patterns from agents/config.json
   - File patterns from tool context
   - Error patterns from conversation context
4. **Calculate confidence scores** for each matching agent
5. **Display analysis** showing decision process

## Subcommands

| Command | Description |
|---------|-------------|
| (default) | Analyze routing for provided prompt |
| `explain <agent>` | Show what triggers routing to this agent |
| `keywords` | List all routing keywords by agent |
| `trace "prompt"` | Step-by-step routing decision trace |
| `compare "prompt"` | Show all agent scores side-by-side |

## Examples

### Analyze Routing
```
> /popkit:routing-debug "fix the login bug"

Selected Agent: bug-whisperer (0.85 confidence)

Keyword Matches:
  "fix" → bug-whisperer (+0.3)
  "bug" → bug-whisperer (+0.5)
  "login" → security-auditor (+0.2)

Top Competing Agents:
  1. bug-whisperer: 0.85 ⭐
  2. security-auditor: 0.35
```

### Explain Agent
```
> /popkit:routing-debug explain code-reviewer

code-reviewer Routing Rules
━━━━━━━━━━━━━━━━━━━━━━━━━━━

Keywords: review, quality, standards, refactor, best practices
File Patterns: *.ts, *.tsx, *.js, *.jsx
Error Patterns: (none)

Example Prompts That Route Here:
  - "review this code for best practices"
  - "refactor the authentication module"
  - "check code quality standards"
```

### List Keywords
```
> /popkit:routing-debug keywords

All Routing Keywords
━━━━━━━━━━━━━━━━━━━━

bug-whisperer: bug, fix, debug, error, issue, crash
security-auditor: security, vulnerability, audit, safe
code-reviewer: review, quality, standards, refactor
performance-optimizer: performance, speed, optimize, slow
test-writer-fixer: test, testing, unit, coverage
...
```

### Compare Scores
```
> /popkit:routing-debug compare "optimize database performance"

Agent Score Comparison
━━━━━━━━━━━━━━━━━━━━━━

query-optimizer:        ████████████████████ 0.85
performance-optimizer:  █████████░░░░░░░░░░░ 0.45
cache-optimizer:        ████░░░░░░░░░░░░░░░░ 0.20
data-integrity:         ██░░░░░░░░░░░░░░░░░░ 0.10
```

## Troubleshooting

**Q: Why is the wrong agent being selected?**
Use `trace` to see exactly which keywords matched and their weights.

**Q: How do I add routing keywords for a custom agent?**
Add keywords to `agents/config.json` under the `routing.keywords` section.

**Q: Why is confidence always low?**
Check if your prompts contain routing keywords. Use `keywords` to see available terms.
