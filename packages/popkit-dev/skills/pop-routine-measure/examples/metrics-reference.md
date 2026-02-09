# Metrics Reference

## Collected Metrics

| Metric            | Description                             | Source              |
| ----------------- | --------------------------------------- | ------------------- |
| **Duration**      | Total execution time in seconds         | Tracker start/stop  |
| **Tool Calls**    | Number of tools invoked                 | Hook tracking       |
| **Input Tokens**  | Estimated input tokens (~20% of total)  | Content length / 4  |
| **Output Tokens** | Estimated output tokens (~80% of total) | Content length / 4  |
| **Total Tokens**  | Input + Output                          | Sum                 |
| **Characters**    | Raw character count                     | Content length      |
| **Cost**          | Estimated API cost (Sonnet 4.5 pricing) | Token count × price |

## Token Estimation

Uses rough heuristic: **~4 characters per token**

This is an approximation. Actual tokenization varies by:

- Language (code vs natural language)
- Repetition and patterns
- Special characters

For more accurate counts, use Claude API's token counting endpoint (future enhancement).

## Cost Calculation

Based on Claude Sonnet 4.5 pricing (as of Dec 2025):

- **Input:** $3.00 per million tokens
- **Output:** $15.00 per million tokens

Costs are **estimates only** - actual costs depend on caching, context reuse, and other factors.

## Output Format

```
======================================================================
Routine Measurement Report
======================================================================
Routine: PopKit Full Validation (p-1)
Duration: 12.34s
Tool Calls: 15

Context Usage:
  Input Tokens:  1,234 (~1k)
  Output Tokens: 6,789 (~6k)
  Total Tokens:  8,023 (~8k)
  Characters:    32,092

Cost Estimate (Claude Sonnet 4.5):
  Input:  $0.0037
  Output: $0.1018
  Total:  $0.1055

Tool Breakdown:
----------------------------------------------------------------------
Tool                 Calls    Tokens       Duration   Chars
----------------------------------------------------------------------
Bash                 8        3,456        2.34s      13,824
Read                 4        2,123        1.12s      8,492
Grep                 2        1,234        0.56s      4,936
Skill                1        1,210        8.32s      4,840
======================================================================
```
