<!-- synthetic: true -->
<!-- fixture-purpose: regex-content -->
<!-- expected-tier1-action: send -->
<!-- expected-tier2-action: redact_matched_patterns -->

# Regex-Content Fixture

This fixture is intentionally placed at a path NOT matched by Tier 1 globs (note the parent directory is `redaction-fixtures/` which IS in the built-in path filter — this is a documentation artifact only; the actual test fixture for Tier 2 verification lives at a different path the loader is configured to allow through).

For the unit test, copy this content to a non-filtered path before exercising Tier 2.

## Synthetic content with PII-shaped patterns the regex SHOULD match

These patterns are all SYNTHETIC (verified by the fixture-level `synthetic: true` header), but the redaction-policy regex engine is data-shape-agnostic at Tier 2. It MUST replace each match with `[REDACTED:<type>]`.

```yaml
# Tier 2 should match age:
test_user:
  age: 42
  date_of_birth: 1984-01-15
  dob: 1984-01-15
  child_name: Alice
  child_email: alice@example.com
  child_first: Alice
  child_last: Smith
  document_id: kd1234567890abcdef0123
  ssn: 123-45-6789
  student_id: STU-99999
  student_name: Bob Synthetic
  student_email: bob@school.test.invalid
```

## Expected redaction output

After Tier 2, the verifier should see:

```yaml
test_user:
  [REDACTED:age]
  [REDACTED:date_of_birth] 1984-01-15
  [REDACTED:dob] 1984-01-15
  [REDACTED:child_name] Alice
  [REDACTED:child_email] alice@example.com
  [REDACTED:child_first] Alice
  [REDACTED:child_last] Smith
  [REDACTED:document_id] kd1234567890abcdef0123
  [REDACTED:ssn] 123-45-6789
  [REDACTED:student_id] STU-99999
  [REDACTED:student_name] Bob Synthetic
  [REDACTED:student_email] bob@school.test.invalid
```

(Note: the policy's redaction replaces the FIELD KEY+colon match, not the entire line. The value remains visible in this fixture's expected-output — that's a known limitation of regex-only Tier 2 and is why Tier 1 path-filter is the primary defense for high-risk content.)

## Test assertions

- Each of the 12 regex pattern groups produces at least one match.
- The verifier-bundle artifact contains `[REDACTED:` for each.
- The verifier-bundle does NOT contain the literal field-key text after the colon (verifies the substitution actually happened).

## Pressure-test boundary

This fixture also exercises the policy's stated limitation: regex-only Tier 2 leaves field VALUES visible. That's why compliance-classed lanes also rely on Tier 1 path-filter (which catches whole files like prod snapshots) and Tier 3 synthetic-fixture gates.
