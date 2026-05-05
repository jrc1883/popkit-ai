<!-- synthetic: true -->
<!-- fixture-purpose: path-filter -->
<!-- expected-tier1-action: never_send -->

# Path-Filter Fixture

This fixture lives under `packages/popkit-core/tests/redaction-fixtures/`. The redaction policy's Tier 1 path filter ships with `**/__tests__/fixtures/**` as a built-in `paths_never_send` default, but this fixtures directory uses `redaction-fixtures/` as the path segment instead — Tier 1's PopKit defaults additionally include `**/redaction-fixtures/**` so this file is unreachable to the verifier.

The fixture contents below are SYNTHETIC and would not actually leak real PII even if the path filter failed; they exist to validate that the dispatcher correctly substitutes a placeholder line when this path is referenced in a claim ledger.

## Synthetic content (would be path-filtered before reaching verifier)

```
test_child_email: synthetic_alice@example.com
fake_age: 8
fixture_dob: 2017-04-12
example_address: 123 Synthetic St, Test City
```

## Expected redaction-policy behavior

When a claim ledger references this file in `changed_files`, the dispatcher MUST:

1. Recognize the path matches the built-in `**/redaction-fixtures/**` glob.
2. Write `<file path filtered: redaction.paths_never_send>` into the bundle in place of this file's content.
3. NOT pass any of the synthetic content above to the verifier — even though it's synthetic, the policy is data-shape-agnostic at Tier 1.

## Test assertion

The Phase 0a redaction-fixture test asserts:
- The verifier-bundle artifact for a turn that touches this file contains the placeholder line.
- The verifier-bundle does NOT contain `synthetic_alice@example.com` (or any other content from this fixture).
