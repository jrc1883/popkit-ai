# GitHub Actions CI Examples

## Listing Workflow Runs

```bash
/popkit:git ci                            # Recent runs (default)
/popkit:git ci list                       # Same as above
/popkit:git ci list --workflow ci.yml     # Specific workflow
/popkit:git ci list --branch main         # By branch
/popkit:git ci list --status failure      # Failed only
/popkit:git ci list --limit 20            # More results
```

Output:
```
Recent Workflow Runs:
[ok] CI #234 - main - 2m ago - 3m 45s
[x] CI #233 - feature/auth - 1h ago - 2m 12s
[ok] Deploy #89 - main - 2h ago - 5m 30s
[...] CI #235 - fix/bug - running - 1m 20s
```

## Viewing Runs

```bash
/popkit:git ci view 234
/popkit:git ci view 234 --log
/popkit:git ci view 234 --job build
```

## Rerunning Workflows

```bash
/popkit:git ci rerun 233              # Rerun all jobs
/popkit:git ci rerun 233 --failed     # Rerun failed jobs only
/popkit:git ci rerun 233 --job test   # Rerun specific job
```

## Watching & Canceling

```bash
/popkit:git ci watch 235              # Watch running workflow
/popkit:git ci cancel 235             # Cancel running workflow
```

## Artifacts & Logs

```bash
/popkit:git ci download 234           # All artifacts
/popkit:git ci download 234 --name dist
/popkit:git ci logs 234               # All logs
/popkit:git ci logs 234 --job build   # Specific job
/popkit:git ci logs 234 --failed      # Failed steps only
```

## Workflow Status Icons

- [ok] success
- [x] failure
- [...] in_progress
- [ ] queued
- [~] cancelled
- [!] skipped
