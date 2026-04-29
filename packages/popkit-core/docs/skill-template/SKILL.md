---
name: skill-template
description: >
  Reference template for PopKit skill authoring. Not a runnable skill — lives under
  docs/skill-template/ so it is excluded from the skill scanner. Use when starting
  a new skill or refactoring an existing one to the standard. Do NOT copy verbatim
  without replacing every <placeholder>.
argument-hint: "[surgical|systematic|full] [path]"
allowed-tools:
  - Read
  - Grep
  - Glob
  - Bash
version: 0.1.0
---

# <Skill Human Name>

One-sentence statement of what the skill does and the user outcome. No hedging.

## When to Use

- <concrete trigger phrase, e.g. "User runs `/popkit:<command>`">
- <secondary trigger, e.g. "Agent detects <condition>">
- <third trigger if applicable>

## When NOT to Use

- <explicit non-goal 1>
- <explicit non-goal 2>

If the skill's description contains `Do NOT use for …`, this section expands the reasoning.

## Modes

Multi-scope skills offer modes upfront and block until the user picks one.

| Mode         | Scope                  | Cap            |
| ------------ | ---------------------- | -------------- |
| `surgical`   | One theme, one session | ≤3 findings    |
| `systematic` | Section-by-section     | ≤4 per section |
| `full`       | Exhaustive, phased     | no cap         |

Scope drift triggers a re-prompt; it is never silent.

## Process

### Step 0: Preflight

Every probe has a runnable command and a fallback.

| Check  | Command                   | Fallback on absent                          |
| ------ | ------------------------- | ------------------------------------------- |
| `git`  | `git rev-parse --git-dir` | Skip retrospective learning; note in output |
| `bd`   | `command -v bd`           | Deferred work becomes a plain checklist     |
| <tool> | <command>                 | <fallback>                                  |

Print the preflight table before Step 1.

### Step 1: Scope

`AskUserQuestion` with three options (surgical / systematic / full). Block until the user answers. If a mode was passed on invocation, skip this step.

### Step 2 ... N: Review sections

Every section:

1. Runs its checks against the repo.
2. Emits findings using the Finding Template below.
3. Closes with the **fixed section-close question**.

### Finding Template

```
### Finding <section>.<n><letter>   [<module-tag>]

Problem:    <one sentence, no hedging>
Evidence:   <file:line> or <command>
Options:
  A) <action>   — effort: S|M|L, risk: S|M|L, blast: S|M|L, maintenance: S|M|L
  B) <action>   — effort: S|M|L, risk: S|M|L, blast: S|M|L, maintenance: S|M|L
  Defer        — effort: 0, risk: 0, blast: 0, maintenance: 0, reason: <one line>
Recommendation: <LETTER> — <rationale tied to an engineering principle>
```

No free-form findings. The Defer option is always present with zero labels.

### Section-close question (verbatim, reused every section)

> Section <N>: <name> — <count> findings.
> Approve (A) — proceed to next section.
> Revise (B) — which finding numbers to revisit?
> Pause (C) — write resume file and exit.

One prompt per section, not one per finding.

## Required outputs

Publish every output as a template. Examples:

### Impact/effort matrix

```
                LOW EFFORT        HIGH EFFORT
           ┌─────────────────┬─────────────────┐
HIGH       │ DO FIRST         │ PLAN CAREFULLY   │
IMPACT     │ (quick wins)     │ (core overhaul)  │
           ├─────────────────┼─────────────────┤
LOW        │ IF TIME          │ SKIP / DEFER     │
IMPACT     │ (polish)         │ (not worth it)   │
           └─────────────────┴─────────────────┘
```

### Failure-mode table

| codepath | failure | test? | handling? | visible? |
| -------- | ------- | ----- | --------- | -------- |

`no + no + silent` is a **critical gap**; uplift its priority one step.

### Completion summary

```
╔════════════════════════════════════════════════╗
║             <SKILL NAME> SUMMARY               ║
╠════════════════════════════════════════════════╣
║ Mode:              ___                         ║
║ Status:            complete | paused           ║
║ Findings approved: ___                         ║
║ Findings deferred: ___                         ║
║ Critical gaps:     ___                         ║
║ Resume file:       <path> | —                  ║
╚════════════════════════════════════════════════╝
```

## Checkpoint / resume (for multi-section skills)

After each section-close resolves (Approve or Pause, not Revise), write `.<skill-name>/resume.md`:

```yaml
version: 0.1.0
mode: surgical | systematic | full
target: <absolute path>
written_at: <ISO-8601>
completed_sections: [1, 2]
next_section: 3
findings:
  - id: 2.1A
    tag: <module-tag>
    title: <one line>
    chosen: A | B | Defer
```

Resume files older than 7 days trigger a fresh-vs-resume prompt.

## Integration Points

| Component             | Purpose        |
| --------------------- | -------------- |
| `<path/to/helper.py>` | <what it does> |
| `<other integration>` | <purpose>      |

## Anti-patterns

- Free-form findings — every finding uses the template.
- Per-item `AskUserQuestion` — batch at section close instead.
- Soft verbs in mandatory steps — replace with directives.
- Silent scope reduction — re-issue the mode question.
- Stale diagrams — update or delete.
