<!-- synthetic: true -->
<!-- fixture-purpose: safe-control -->
<!-- expected-tier1-action: send -->
<!-- expected-tier2-action: pass_through_unchanged -->
<!-- expected-tier3-action: pass -->

# Safe-Control Fixture

This fixture exists to prove redaction does NOT over-fire. It contains:

- A `synthetic: true` header (passes Tier 3)
- Code-shape content (function names, class names, type signatures, file paths)
- Comments that describe behavior without PII
- No matches against any Tier 2 regex
- No paths that would trigger Tier 1 filter beyond the fixture-directory default (which DOES filter this file at Tier 1; for the test, the runner copies the content to a non-filtered path before assertion)

## Content (should pass through redaction unchanged)

```typescript
// Pure code, no PII.
export function applyBudgetTruncation(
  typedMessage: string,
  attachments: AttachmentForPrompt[],
): BudgetTruncationResult {
  // ... iterative-trim algorithm ...
}

interface AttachmentForPrompt {
  id: string;
  fileName: string;
  fileType: string;
  extractedText: string;
}

// File path reference (not PII):
// packages/popkit-core/output-styles/schemas/claim-ledger.schema.json

// Test name (not PII):
// describe('applyBudgetTruncation', () => { ... });

// Comment about ADR (not PII):
// See ADR 0004: Power Mode is legacy implementation language.
```

## Expected redaction output

After Tier 1 (when copied to a non-filtered path) + Tier 2:

The output is byte-identical to the input. No `[REDACTED]` markers anywhere. No content stripped. No fields altered.

## Test assertions

The Phase 0a redaction-fixture test asserts (with this fixture relocated to a non-filtered path for the run):

- Tier 1 path filter does NOT match the relocated path → content passes Tier 1.
- Tier 2 regex pre-pass produces ZERO substitutions.
- Tier 3 synthetic-data check passes (header present, no fixture-content fields used).
- The verifier-bundle artifact contains the file's content byte-for-byte.

## Why this matters

A redaction policy that's too aggressive is its own failure mode — the verifier sees `[REDACTED]` everywhere and either over-flags (false positives) or stops trusting its own input. The safe-control fixture proves redaction stays surgical: it only acts on real matches, and code-shape content (the bulk of what the verifier reasons about) is left intact.
