# PopKit Skill Authoring Standard

House style for writing `SKILL.md` under `packages/*/skills/*/`. The goal is skills that behave like protocols instead of prose: same shape every run, no silent scope reduction, measurable compliance.

Inspired by [`ehmo/code-overhaul-skill`](https://github.com/ehmo/code-overhaul-skill), which pairs a rigid protocol with a binary grader and drives iteration off the grader's output.

---

## Why this exists

Skills are instructions to an LLM. Vague instructions produce variable output; directives produce comparable output. This document is the minimum bar for new skills and the target for existing ones.

Two invariants:

1. Every user-visible artifact the skill emits has a **fixed schema** — templates, tables, and ASCII boxes with named slots, not prose.
2. Every skill that makes recommendations ships with an **`eval/RUBRIC.md`** whose criteria are binary and the skill is scored against it before merge.

---

## 1. Frontmatter contract

```yaml
---
name: <lowercase-hyphen-case>
description: >
  <directive verb> <what it does>. Use when <trigger phrase the user says>.
  Do NOT use for <explicit non-goal>.
argument-hint: "[mode] [path]" # only if the skill takes arguments
allowed-tools: # only if the skill scopes its tools
  - Read
  - Grep
  - Glob
  - Bash
---
```

Rules:

- **`name`** matches the regex `^[a-z0-9-]+$` and matches the directory name. Enforced by `tests/skills/test-skill-format.json`.
- **`description`** opens with a directive verb (the action), contains natural-language trigger phrases ("Use when ..."), and names at least one non-goal ("Do NOT use for ..."). Target ≤200 characters; 300 is the ceiling.
- **`argument-hint`** lists every valid argument verbatim when arguments exist.
- **`allowed-tools`** names every shell/file tool the skill actually calls. Built-ins (`AskUserQuestion`, `TodoWrite`) may be omitted.
- No placeholder strings (`TODO`, `TBD`, `placeholder`) anywhere in frontmatter.

## 2. Required sections

H1 matches the skill's human name. Every skill includes at least two of:

- `## When to Use`
- `## When NOT to Use`
- `## Process` (or `## Protocol` for audit-shaped skills)
- `## Integration Points`

Minimum section count is enforced by `tests/skills/test-skill-format.json`. `When NOT to Use` is mandatory when `description` contains "Do NOT use" — the section must expand the reasoning.

## 3. Output schema discipline

If the skill emits a report, finding, plan, or summary, publish its **exact shape** inside SKILL.md. Free-form output is forbidden.

### 3.1 Finding template (for audit/review skills)

```
### Finding <section>.<n><letter>   [<module-tag>]

Problem:    <one sentence, no hedging>
Evidence:   <file:line> or <command that reproduces>
Options:
  A) <action>   — effort: S|M|L, risk: S|M|L, blast: S|M|L, maintenance: S|M|L
  B) <action>   — effort: S|M|L, risk: S|M|L, blast: S|M|L, maintenance: S|M|L
  Defer        — effort: 0, risk: 0, blast: 0, maintenance: 0, reason: <one line>
Recommendation: <LETTER> — <one-sentence rationale tied to an engineering principle>
```

The Defer option is always present and always carries zero labels so the grammar is uniform.

### 3.2 Report template (for capture/generator skills)

Publish the exact structure the skill prints. Every field is named, every field has a source. No "…" or "etc." in the template — if a field is optional, label it `Optional:` explicitly.

### 3.3 Summary box

If a skill runs end-to-end over multiple steps, close with an ASCII summary box with named rows. No narrative prose in the summary — numbers and statuses only.

## 4. Mode commitment (for multi-scope skills)

Audit-shaped, generator-shaped, and refactor-shaped skills expose a **fixed set of modes** at the top and block until the user picks one. Mode caps are numeric.

Recommended schema:

| Mode         | Scope                           | Cap            |
| ------------ | ------------------------------- | -------------- |
| `surgical`   | One theme, one session          | ≤3 findings    |
| `systematic` | Section-by-section, interactive | ≤4 per section |
| `full`       | Exhaustive, phased roadmap      | no cap         |

Scope drift is not silent: if the user expands scope mid-run, re-issue the mode question before complying.

## 5. Batched confirmation

Do **not** ask for approval after every finding. Emit all findings for a section, then fire **one** `AskUserQuestion` with three branches:

- **Approve** → next section
- **Revise** → re-emit the affected findings and re-ask
- **Pause** → write the checkpoint file, jump to summary with `Status: paused`

One prompt per section, not one prompt per finding. Measured impact: the code-overhaul skill reports "eliminates up to 20 prompts per full audit" after this change.

## 6. Soft-verb ban

Mandatory steps use directives. These verbs are banned from any step marked **must**, **required**, or mandatory:

> `consider`, `evaluate`, `should`, `could`, `may`, `might`, `try to`, `attempt to`, `think about`

Replace with: `do`, `run`, `stop`, `write`, `emit`, `file`, `assert`, `require`.

Soft verbs are allowed only in descriptive glossaries, illustrative examples, or user-facing explanations of optional behavior.

## 7. Hard gates

Two invariants that catch the most common regressions. Include them verbatim in any audit/refactor skill.

- **Characterization-tests-first:** if a recommendation touches untested code, the first execution step is the characterization-test plan, not the change.
- **Failure-mode gate:** for every modified codepath, emit a row in a `codepath | failure | test? | handling? | visible?` table. `no + no + silent` is a **critical gap** with automatic priority uplift.

## 8. Checkpointing (for multi-step skills)

Skills that span more than three interactive sections write `.<skill-name>/resume.md` after each section-close resolves. Schema:

```yaml
version: <semver matching SKILL.md frontmatter>
mode: surgical | systematic | full
target: <absolute path>
written_at: <ISO-8601>
completed_sections: [1, 2, 3]
next_section: 4
findings:
  - id: 2.1A
    tag: <module-tag>
    title: <one line>
    chosen: A | B | Defer
```

Stale-file rule: if `written_at` is older than 7 days, prompt fresh-vs-resume on invocation. Document the staleness threshold in SKILL.md; do not hardcode a different value.

## 9. Eval harness

Every skill that makes recommendations ships a grading kit:

```
packages/<pkg>/skills/<skill>/
├── SKILL.md
└── eval/
    ├── RUBRIC.md      # binary criteria, 1 point each, no partial credit
    ├── GRADER.md      # grader prompt (read RUBRIC, read SKILL, score)
    └── SCENARIOS.md   # optional: 3-5 real-repo walk-throughs
```

Rubric rules:

- Criteria are **binary** (0 or 1). No half credit. Partial matches score 0.
- Every criterion is checkable against SKILL.md text alone — a grader with no other context can score it.
- Target score is `N/N`. Failing criteria are gaps to fix before merge.
- When SKILL.md changes, re-run the grader before the PR lands. Grader output goes in the PR description.

See `packages/popkit-core/docs/skill-template/eval/` for the template.

## 10. Versioning (for skills with on-disk state or public protocols)

Skills that write files, emit artifacts, or publish slash-commands users rely on follow semver:

- **MAJOR** — protocol-breaking (changes to argument shape, on-disk schema, or required tool set).
- **MINOR** — additive (new modes, new sections, new addendums).
- **PATCH** — clarifications, soft-verb scrubs, rubric fixes.

Track version in SKILL.md frontmatter (`version: 2.1.0`). Maintain a sibling `CHANGELOG.md` in the skill directory if the skill is versioned. Mark protocol-breaking changes explicitly — on-disk state written by an older version must either be readable or trigger a fresh-vs-resume prompt.

## 11. Pre-merge checklist

Before opening a PR that adds or changes a skill, verify:

- [ ] Frontmatter passes `skill-format-validation` (name regex, description length, no placeholders).
- [ ] H1 matches the skill's human name; at least two required sections present.
- [ ] `When NOT to Use` expands on any `Do NOT use` in the description.
- [ ] Every output shape appears as a template inside SKILL.md.
- [ ] No banned soft verbs in mandatory steps (grep: `-E "\b(should|consider|evaluate|could|may|might|try to|attempt to)\b"`).
- [ ] `eval/RUBRIC.md` exists and the skill scores N/N under `eval/GRADER.md`.
- [ ] Grader output is pasted into the PR description.
- [ ] Argument-hint (if any) matches the modes the skill accepts.
- [ ] Version bumped in frontmatter when protocol or on-disk schema changed; CHANGELOG entry written if skill is versioned.

## 12. What this standard does **not** require

To keep authoring costs honest:

- One-shot skills with no modes, no recommendations, and no on-disk state (e.g. a pure formatter) may skip sections 4, 7, 8, and 10.
- SCENARIOS.md is optional; RUBRIC.md and GRADER.md are not.
- Stack addendums (iOS/Go/Web-style split inside one SKILL.md) are a pattern, not a requirement.

---

## Appendix: the meta-lesson

The code-overhaul skill's biggest contribution is not any single rule in SKILL.md — it is the closed loop: **skill → rubric → grader → CHANGELOG → skill v+1**. Its v2.1 release notes credit the grader for every tightening. Skills that follow this standard without the loop will drift; skills that adopt the loop improve every release.

Default action for PopKit skill authors: write the rubric _first_, then the SKILL.md, then run the grader before opening the PR.
