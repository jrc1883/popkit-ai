# pop-bug-reporter SKILL.md rubric

7 criteria, 1 point each. Target: 7/7. Partial matches score 0.

This skill is capture-shaped (not audit-shaped), so rubric criteria C5–C10 from the PopKit skill-authoring template are not applicable. See `packages/popkit-core/docs/skill-template/eval/RUBRIC.md` for the full template.

---

## C1. Frontmatter conformance

Pass if **all** of:

- `name` is `pop-bug-reporter`, matches the directory name, and matches `^[a-z0-9-]+$`.
- `description` opens with a directive verb.
- `description` contains a "Use when …" trigger phrase.
- `description` contains "Do NOT use for …" with at least one explicit non-goal.
- `description` length is between 20 and 300 characters.
- No placeholder strings (`TODO`, `TBD`, `placeholder`) appear in frontmatter.

## C2. Required sections present

Pass if **all** of:

- H1 is `Bug Reporter`.
- `## When to Use` is present with at least three bullets.
- `## When NOT to Use` is present with at least three bullets and expands the "Do NOT use" cases from the description.
- `## Process` (or its numbered step sections `### 1. Parse Request`, `### 2. Capture Context`, etc.) is present.
- `## Integration Points` is present.

## C3. No soft verbs in mandatory steps

Pass if:

- Running `grep -nE '\b(should|consider|evaluate|could|may |might|try to|attempt to)\b'` against the Process steps, Schema, and Suggested-action rules returns zero matches — excluding the one line that enumerates banned words as a rule statement.

## C4. Bug Report schema is rigid

Pass if **all** of:

- A `Schema:` block appears under `### 3. Generate Report` with named slots (ID, Time, Description, Context, Recent Actions, Errors Detected, Stuck Patterns, Suggested Actions).
- Every required slot is labeled; optional slots are labeled `Optional:` explicitly.
- "No free-form fields" or equivalent exclusion is stated.
- A filled `Example:` follows the schema and matches the schema's slots exactly.

## C5. Suggested-action discipline

Pass if **all** of:

- Imperative-verb rule is stated (no `consider`, `try`, `may`, `should`).
- Each action must name a concrete object (file, function, or test) — stated verbatim.
- Maximum-action cap is numeric (3).
- Ranking rule is stated (shortest unblock time first).

## C6. Flag and subcommand contract

Pass if **all** of:

- Every flag (`--issue`, `--share`, `--verbose`, `--no-context`) is documented in the `## Input` section.
- Every subcommand (`list`, `view <id>`, `clear`) has a handler in `## Subcommand Handlers`.
- GitHub label validation path is documented under `--issue` (C1 #96 reference).
- The anonymization rule set is documented under `--share`.

## C7. Integration points are enumerated

Pass if:

- `## Integration Points` contains a table with at least four rows, each row naming a component path and its purpose.

---

## Scoring

Total = sum of criteria. Pass = 7/7. Any failing criterion is a gap to fix before the PR lands.

The sibling grader in `eval/GRADER.md` runs against this rubric. Paste the grader output into any PR that modifies `SKILL.md`.
