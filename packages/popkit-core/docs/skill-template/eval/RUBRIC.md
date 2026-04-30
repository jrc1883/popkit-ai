# Skill Rubric Template

Binary, 1 point each. Target: N/N. **Partial matches score 0.**

Copy this file into a new skill's `eval/RUBRIC.md` and delete criteria that do not apply (e.g., C7–C9 for one-shot skills with no modes or checkpointing). Replace `<skill-name>` and `<skill-path>` throughout.

Every criterion is checkable against `<skill-path>/SKILL.md` alone. A grader with no other context can score the skill.

---

## C1. Frontmatter conformance

Pass if **all** of:

- `name` matches `^[a-z0-9-]+$` and matches the skill directory name.
- `description` opens with a directive verb, contains a "Use when …" trigger phrase, and names at least one non-goal ("Do NOT use for …").
- `description` length is between 20 and 300 characters (≤200 preferred).
- `allowed-tools` names every shell/file tool the skill actually calls (Read, Grep, Glob, Bash).
- No placeholder strings (`TODO`, `TBD`, `placeholder`) appear in frontmatter.

## C2. Required sections present

Pass if **all** of:

- H1 matches the skill's human name.
- At least two of `When to Use`, `When NOT to Use`, `Process`, `Integration Points` appear as H2s.
- If `description` contains "Do NOT use", `When NOT to Use` expands the reasoning in at least two bullets.

## C3. No soft verbs in mandatory steps

Pass if:

- Running `grep -nE '\b(should|consider|evaluate|could|may|might|try to|attempt to)\b' SKILL.md` against mandatory steps (Process, Protocol, Required outputs, Hard gates) returns zero matches.

Soft verbs are permitted in descriptive glossaries and illustrative examples.

## C4. Output schemas are published inline

Pass if **all** of:

- Every user-visible artifact the skill emits (report, finding, plan, summary) appears as a template with named slots inside SKILL.md.
- No "…" or "etc." appears inside any template.
- Optional fields are labeled `Optional:` explicitly.

## C5. Finding / recommendation template (for recommendation-making skills)

Pass if **all** of:

- A `Finding Template` block appears with: three-part ID (`<section>.<n><letter>`), problem statement, evidence (path:line or runnable command), 2–3 options with S/M/L labels for effort/risk/blast/maintenance.
- A `Defer` option carries zero labels (`effort: 0, risk: 0, blast: 0, maintenance: 0`) and a one-line reason field.
- A `Recommendation` letter with a rationale tied to an engineering principle.
- The template is referenced from every review section, or defined before sections with "mandatory for all sections" stated.
- "No free-form findings" or equivalent exclusion is stated.

Skip this criterion for skills that do not emit findings.

## C6. Batched section-close question

Pass if **all** of:

- A single fixed section-close question is defined verbatim and reused every section.
- Three branches (Approve / Revise / Pause) are enumerated with their consequences.
- "One prompt per section, not per finding" or equivalent is stated.

Skip this criterion for one-shot skills.

## C7. Mode commitment (for multi-scope skills)

Pass if **all** of:

- Modes are named explicitly: `surgical`, `systematic`, `full` (or a documented equivalent set).
- Numeric caps per mode are stated (e.g., SURGICAL ≤3, SYSTEMATIC ≤4, FULL no cap).
- Step 1 calls `AskUserQuestion` and blocks until the user answers; mode passed on invocation skips Step 1.
- A scope-drift rule is documented: mid-run expansion requires re-issuing the mode question.

Skip this criterion for one-shot skills.

## C8. Hard gates (for audit / refactor skills)

Pass if **all** of:

- Characterization-tests-first: stated verbatim as a hard rule.
- Failure-mode table is a required non-skippable output with the `codepath | failure | test? | handling? | visible?` columns.
- `no-test + no-handling + silent → critical gap` rule is stated with the priority-uplift consequence.

Skip this criterion for non-refactor skills.

## C9. Checkpoint / resume (for multi-section skills)

Pass if **all** of:

- Checkpoint file path is named: `.<skill-name>/resume.md` or the equivalent.
- Resume schema lists at minimum `version`, `mode`, `target`, `written_at`, `completed_sections`, `next_section`, `findings`.
- Write-timing is specified: after each section-close resolves Approve or Pause (not Revise).
- Stale-file rule is documented (7-day threshold or explicit alternative).

Skip this criterion for skills that complete in a single section.

## C10. Degenerate / edge-case handling (for audit / generator skills)

Pass if **all** of:

- "No tests detected" path is specified (section becomes a test-creation plan; refactor-of-untested-code is blocked behind characterization tests).
- "No git history" path is specified (retrospective-learning step is skipped with a printed note).
- "No dependency manifest" path is specified (dependency section output is a single stated line).
- "Single-file or near-empty repo" path refuses the large modes with a stated reason.

Skip this criterion for skills that do not scan repos.

---

## Scoring

Total = sum of criteria applicable to the skill. Pass = N/N. Any failing criterion is a gap to fix before the PR lands.

A skill that uses "should" where the rubric requires a directive fails the relevant criterion. A skill that gestures toward a requirement without enforcing it fails.
