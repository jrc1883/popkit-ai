---
description: "code | routing [--trace, --verbose]"
argument-hint: "<mode> [options]"
---

# /popkit-ops:debug - Debugging Tools

Systematic debugging with root cause analysis and agent routing diagnostics.

## Usage

```
/popkit-ops:debug <subcommand> [options] [flags]
```

## Flags

| Flag | Description |
|------|-------------|
| `-T`, `--thinking` | Enable extended thinking for deeper root cause analysis |
| `--no-thinking` | Disable extended thinking (use default) |
| `--think-budget N` | Set thinking token budget (default: 10000) |

## Subcommands

| Subcommand | Description |
|------------|-------------|
| `code` | Systematic code debugging (default) |
| `routing` | Analyze agent routing decisions |

---

## Subcommand: code (default)

Systematic approach to finding and fixing bugs with root cause analysis.

```
/popkit-ops:debug [issue-description]
/popkit-ops:debug                         # Describe issue interactively
/popkit-ops:debug "login fails on mobile"
/popkit-ops:debug code "login fails"      # Explicit subcommand
/popkit-ops:debug --test failing-test.ts  # Debug specific test
```

### Process

Invokes the **pop-systematic-debugging** skill with 4 phases:

#### Phase 1: Root Cause Investigation

```
Starting systematic debugging...

1. Reading error messages carefully
2. Attempting to reproduce
3. Checking recent changes
4. Tracing data flow

Gathering evidence...
```

**DO NOT** propose fixes until Phase 1 is complete.

#### Phase 2: Pattern Analysis

```
Finding patterns...

1. Locating similar working code
2. Comparing against references
3. Identifying differences
4. Understanding dependencies

Pattern found: [description]
```

#### Phase 3: Hypothesis Testing

```
Forming hypothesis:
"The issue is caused by X because Y"

Testing minimally...
- Change: [single change]
- Result: [pass/fail]

Hypothesis confirmed/rejected.
```

#### Phase 4: Implementation

```
Root cause identified: [cause]

Creating failing test...
Implementing fix...
Verifying fix...

Fixed! Test now passes.
```

### Red Flags

The skill will stop and return to Phase 1 if:
- "Quick fix" is attempted without investigation
- Multiple changes made at once
- Fixes proposed without understanding

### Options

```
/popkit-ops:debug --verbose               # Show all investigation steps
/popkit-ops:debug --skip-phase-1          # If already investigated (rare)
```

### Example Session

```
/popkit-ops:debug "Users getting logged out randomly"

Phase 1: Investigation
- Error: "Token expired" in console
- Reproduces: Inconsistently, after ~30 minutes
- Recent change: Updated auth library 2 days ago
- Data flow: Token -> Storage -> Validation -> Rejection

Phase 2: Pattern Analysis
- Working: Previous version didn't have this
- Difference: New library uses shorter default expiry

Phase 3: Hypothesis
"Token expiry changed from 1 hour to 30 minutes in library update"
Testing: Check library changelog... Confirmed!

Phase 4: Fix
Test: "should maintain 1 hour session"
Fix: Configure explicit token expiry
Verify: Test passes, manual test confirms
```

### Integration with Skills

- **pop-root-cause-tracing** - When errors are deep in stack
- **pop-defense-in-depth** - Adding validation layers after fix
- **pop-test-driven-development** - Creating regression test

---

## Subcommand: routing

Analyze and debug agent routing decisions to understand why specific agents are selected.

```
/popkit-ops:debug routing "your prompt"       # Analyze routing for a prompt
/popkit-ops:debug routing explain <agent>     # Show agent's routing keywords
/popkit-ops:debug routing keywords            # List all routing keywords
/popkit-ops:debug routing trace "prompt"      # Show detailed routing trace
/popkit-ops:debug routing compare "prompt"    # Compare all agent scores
```

### Routing Analysis Commands

| Command | Description |
|---------|-------------|
| `routing "prompt"` | Analyze routing for provided prompt |
| `routing explain <agent>` | Show what triggers routing to this agent |
| `routing keywords` | List all routing keywords by agent |
| `routing trace "prompt"` | Step-by-step routing decision trace |
| `routing compare "prompt"` | Show all agent scores side-by-side |

### Process

1. Parse the prompt to extract keywords
2. Match against routing rules:
   - Keyword patterns from agents/config.json
   - File patterns from tool context
   - Error patterns from conversation context
3. Calculate confidence scores for each matching agent
4. Display analysis showing decision process

### Example: Analyze Routing

```
/popkit-ops:debug routing "fix the login bug"

Selected Agent: bug-whisperer (0.85 confidence)

Keyword Matches:
  "fix" -> bug-whisperer (+0.3)
  "bug" -> bug-whisperer (+0.5)
  "login" -> security-auditor (+0.2)

Top Competing Agents:
  1. bug-whisperer: 0.85 [selected]
  2. security-auditor: 0.35
```

### Example: Explain Agent

```
/popkit-ops:debug routing explain code-reviewer

code-reviewer Routing Rules
---

Keywords: review, quality, standards, refactor, best practices
File Patterns: *.ts, *.tsx, *.js, *.jsx
Error Patterns: (none)

Example Prompts That Route Here:
  - "review this code for best practices"
  - "refactor the authentication module"
  - "check code quality standards"
```

### Example: List Keywords

```
/popkit-ops:debug routing keywords

All Routing Keywords
---

bug-whisperer: bug, fix, debug, error, issue, crash
security-auditor: security, vulnerability, audit, safe
code-reviewer: review, quality, standards, refactor
performance-optimizer: performance, speed, optimize, slow
test-writer-fixer: test, testing, unit, coverage
...
```

### Example: Compare Scores

```
/popkit-ops:debug routing compare "optimize database performance"

Agent Score Comparison
---

query-optimizer:        ==================== 0.85
performance-optimizer:  =========            0.45
cache-optimizer:        ====                 0.20
data-integrity:         ==                   0.10
```

### Troubleshooting

**Q: Why is the wrong agent being selected?**
Use `trace` to see exactly which keywords matched and their weights.

**Q: How do I add routing keywords for a custom agent?**
Add keywords to `agents/config.json` under the `routing.keywords` section.

**Q: Why is confidence always low?**
Check if your prompts contain routing keywords. Use `keywords` to see available terms.

---

## Examples

```bash
# Debug code issues
/popkit-ops:debug "users getting logged out"
/popkit-ops:debug --test auth.test.ts

# Debug agent routing
/popkit-ops:debug routing "fix the performance issue"
/popkit-ops:debug routing explain bug-whisperer
/popkit-ops:debug routing keywords
```

---

## Architecture Integration

| Component | Integration |
|-----------|-------------|
| Code Debugging Skill | `skills/pop-systematic-debugging/SKILL.md` |
| Root Cause Tracing | `skills/pop-root-cause-tracing/SKILL.md` |
| Routing Config | `agents/config.json` |
| Routing Debug Skill | `skills/pop-routing-debug/SKILL.md` |

## Related Commands

| Command | Purpose |
|---------|---------|
| `/popkit-core:plugin test` | Run plugin self-tests |
| `/popkit-core:plugin sync` | Validate plugin integrity |
