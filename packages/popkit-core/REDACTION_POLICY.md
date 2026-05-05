# Redaction Policy

Verifier inputs (claim ledger, git diff, evidence artifacts) are treated as regulated until proven safe. This policy defines what gets stripped before any content reaches the LLM verifier (Codex CLI), regardless of plan-stage vs code-stage, and regardless of whether the lane's `compliance_class` is `none`.

> Codex round 5 directive: "Redaction is data-dependent, not phase-dependent. If a plan contains real names, screenshots, child data, student records, logs, or production IDs, redaction applies regardless of stage."

## Three-tier defense

### Tier 1 — Path filter (never sent)

Globs declared in the lane manifest's `redaction.paths_never_send`, plus built-in defaults that apply to every lane:

- `**/__tests__/fixtures/**` — test fixture content (often realistic-looking sample data)
- `**/*.audit-log` — audit log dumps
- `**/*-prod-snapshot.*` — production data snapshots
- `**/qa/screenshots/**` — UI screenshots (may contain real names, real events, real children's faces)
- `**/.env*` — environment files (secrets)
- Anything matching the lane's `redaction.paths_never_send` globs

Files under these paths NEVER reach the verifier. The dispatcher writes a placeholder line (`<file path filtered: redaction.paths_never_send>`) into the bundle so the verifier can see the file existed without seeing its contents.

### Tier 2 — Content scan (regex pre-pass on what does get sent)

Runs against everything that survives Tier 1. Lane manifest's `redaction.content_redact_patterns` is concatenated with these built-in defaults:

- `\bage:\s*\d+` — explicit age fields
- `\bdate_of_birth:` / `\bdob:` — DOB fields
- `\bchild_(?:name|email|first|last):` — child identifying fields
- `\bdocument_id:\s*kd[A-Za-z0-9]{16,}` — Convex doc IDs (these can be real production references)
- `\bssn[:\s]\d{3}-?\d{2}-?\d{4}` — SSN-shaped strings
- `\b\d{4}-\d{4}-\d{4}-\d{4}\b` — credit-card-shaped strings
- `(?i)\bstudent_(?:id|name|email):` — FERPA-scoped fields

Matches are replaced with `[REDACTED]` plus a 1-byte type hint (e.g., `[REDACTED:age]`) so the verifier can reason about the _kind_ of redacted value without seeing the value itself.

### Tier 3 — Synthetic-fixtures-only policy (compliance lanes)

For lanes with `compliance_class != none`, the deterministic gates include a "synthetic-data check" gate. Any new test fixture under `__tests__/fixtures/` (or lane-declared equivalent) must pass an "all fields synthetic" check before the gate passes:

- All names match `^(test|fake|synthetic|fixture|example)_\w+$`
- All ages match `\b(?:test|fake)_age:\s*\d+\b` or are within a clearly-synthetic range marker
- All emails end in `@example.com`, `@test.invalid`, or `@fixtures.local`
- File header includes `<!-- synthetic: true -->` marker

Fixtures without these markers fail the gate, blocking the LLM verifier from being invoked at all (deterministic gate failure short-circuits before token spend).

## What does NOT get redacted

- Code-shape: function names, class names, file paths, type signatures, imports
- Comments: kept as-is unless they match a Tier 2 regex
- Test names: `describe(...)` / `it(...)` strings (the test names themselves are not PII)
- Synthetic fixtures that pass Tier 3

The principle is: redact data, not structure. The verifier needs to reason about what changed; it shouldn't see who's affected.

## Per-lane overrides

Lane manifests can ADD to the path filter and content patterns, but cannot DISABLE the built-in defaults. Even a `compliance_class: none` lane gets the SSN/credit-card/FERPA-id defaults.

## Failure modes

- **Over-redaction** (regex flags a legitimate value as PII) — the verifier sees `[REDACTED]` and may flag the over-redaction as a finding. Operator triages by adding an exception to the lane's `redaction.exceptions` field (planned, not yet implemented).
- **Under-redaction** (real PII slips through both tiers) — Tier 3's synthetic-fixtures-only policy is the catch-all for compliance lanes. Non-compliance lanes accept residual risk by definition; if real PII is showing up there, the lane's `compliance_class` was misclassified.
- **Tier conflicts** (a path is in `paths_never_send` AND has its content match a Tier 2 regex) — Tier 1 wins. The path is filtered entirely; Tier 2 never runs on filtered content.

## Schema version

This policy applies to manifest schema_version: 1. Future versions can extend the redaction config (e.g., adding `redaction.exceptions`) but cannot remove the built-in defaults without a major-version bump.
