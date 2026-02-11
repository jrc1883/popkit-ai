# Future Enhancements

## Phase 2: Comparison Mode

Compare multiple routines side-by-side in a single invocation:

```
/popkit:routine morning --measure --compare pk,p-1
```

Output:

```
Routine Comparison
------------------
                    pk        p-1       Difference
Duration:          8.2s      12.3s      +4.1s (+50%)
Tokens:          5,234      8,023      +2,789 (+53%)
Cost:          $0.0786    $0.1205     +$0.0419 (+53%)
```

## Phase 3: Trend Analysis

Analyze measurements over time periods:

```
/popkit:routine morning --measure --trend 7d
```

Output:

- Average metrics over past 7 days
- Peak and low measurements
- Trend line visualization
- Anomaly detection

## Phase 4: Optimization Suggestions

Automatically suggest optimizations based on measurement data:

```
Tool breakdown shows Bash taking 60% of tokens.
Suggestion: Cache git status results to reduce redundant calls.

Estimated savings: ~2,400 tokens per run (~$0.036 per routine)
```

## Phase 5: Budget Alerts

Set token budgets and receive alerts:

```yaml
budget:
  daily_tokens: 50000
  cost_alert: 1.00 # Alert if daily cost exceeds $1
```
