<!-- DELIBERATELY MISSING the synthetic: true header -->
<!-- fixture-purpose: synthetic-rejection -->
<!-- expected-tier3-action: gate_failure -->

# Synthetic-Rejection Fixture

**This fixture intentionally fails Tier 3's synthetic-data check.** It does not declare `<!-- synthetic: true -->` in its header, and its content uses fields that LOOK like real PII without `test_`, `fake_`, `synthetic_`, `fixture_`, or `example_` prefixes.

The Tier 3 gate runs as a deterministic gate for any lane with `compliance_class != none`. When this fixture (or anything resembling it) is added under `__tests__/fixtures/`, the gate MUST fail and short-circuit the LLM verifier.

## Content that fails the synthetic-data check

```yaml
user:
  name: Sarah Johnson # Not test_/fake_/synthetic_/fixture_/example_ prefixed
  age: 7
  email: sarah.johnson@gmail.com # Not @example.com / @test.invalid / @fixtures.local
  dob: 2018-03-21
```

## Expected gate behavior

When the deterministic gate runner encounters this fixture and the active lane has `compliance_class: child-data` (or any compliance class):

1. Gate `synthetic-data-check` fails.
2. Gate runner returns `pass: false, reason: "fixture missing 'synthetic: true' header AND uses non-synthetic-prefixed names/emails: synthetic-rejection.md"`.
3. Dispatcher sees the failed required gate, sets `verdict: human` with reason `claim_ledger_missing_or_invalid` (claim ledger touching a non-synthetic fixture is itself an invalid state for compliance lanes).
4. NO TOKENS spent on the LLM verifier.

## Test assertion

The Phase 0a redaction-fixture test asserts:

- A simulated lane with `compliance_class: child-data` and a claim ledger touching this fixture causes the gate runner to return `pass: false` for the `synthetic-data-check` gate.
- The dispatcher's verdict for that turn is `verdict: human`.
- Codex CLI was NOT invoked (token usage = 0 for this turn in the cost ledger).

## Why this matters

Compliance lanes are the highest-risk surface for PII leakage. The synthetic-fixtures-only policy creates a forcing function: contributors cannot accidentally introduce realistic-looking PII into test fixtures even if redaction Tier 1 + Tier 2 fail. The gate is the catch-all.

## What does NOT make a fixture synthetic

- A `// synthetic` comment on a single line — the gate looks for the structured header.
- A made-up but realistic name like `John Smith` — the prefix rule is strict on purpose.
- An `@gmail.com` email — only the three explicit synthetic domains pass.

The strictness is intentional. The cost of a false-positive is one extra header line; the cost of a false-negative is real PII in a verifier prompt.
