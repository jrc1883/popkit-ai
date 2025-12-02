---
description: List GitHub issues with Power Mode recommendations - see which issues benefit from multi-agent orchestration
---

# /popkit:issues - List Issues with Power Mode Status

List repository issues with Power Mode recommendations parsed from PopKit Guidance sections.

## Usage

```
/popkit:issues [flags]
```

## Flags

| Flag | Short | Description |
|------|-------|-------------|
| `--power` | `-p` | Show only issues recommending Power Mode |
| `--label` | `-l` | Filter by label: `--label bug` |
| `--state` | | Filter by state: `open` (default), `closed`, `all` |
| `--assignee` | | Filter by assignee: `--assignee @me` |
| `--limit` | `-n` | Limit results: `-n 10` (default: 20) |

## Examples

```bash
# List all open issues with Power Mode recommendations
/popkit:issues

# Show only issues that recommend Power Mode
/popkit:issues --power
/popkit:issues -p

# Filter by label
/popkit:issues --label bug
/popkit:issues -l architecture

# Combine filters
/popkit:issues --label feature --assignee @me

# Limit results
/popkit:issues -n 5
```

## Process

### Step 1: Fetch Issues

```bash
gh issue list --state open --json number,title,body,labels,createdAt,author --limit 50
```

### Step 2: Parse PopKit Guidance

For each issue, extract from body:
- `power_mode`: recommended | optional | not_needed
- `complexity`: small | medium | large | epic
- `phases`: List of checked phases
- Phase count

### Step 3: Generate Table

Display issues with Power Mode status:

```
Open Issues with Power Mode Recommendations:

| #   | Title                          | Complexity | Power Mode  | Phases |
|-----|--------------------------------|------------|-------------|--------|
| 3   | Add user authentication        | medium     | optional    | 4      |
| 11  | Unified orchestration system   | epic       | RECOMMENDED | 6      |
| 15  | Fix login regression           | small      | not_needed  | 2      |
| 18  | Refactor database layer        | large      | RECOMMENDED | 5      |
| 22  | Update documentation           | small      | not_needed  | 1      |

Legend:
  RECOMMENDED = Power Mode beneficial for this issue
  optional    = Power Mode available but not required
  not_needed  = Sequential execution preferred

Hint: Use /popkit:work #11 to start working on an issue
      Use /popkit:work #11 -p to force Power Mode
```

### Step 4: Apply Filters

**`--power` flag:**
Only show issues where:
- `power_mode == "recommended"` OR
- `complexity == "epic"` OR
- `complexity == "large"`

**`--label` flag:**
Filter by GitHub label.

**`--state` flag:**
Filter by issue state.

## Output Formats

### Default (Table)
```
Open Issues with Power Mode Recommendations:

| #   | Title                          | Complexity | Power Mode  | Phases |
|-----|--------------------------------|------------|-------------|--------|
| 3   | Add user authentication        | medium     | optional    | 4      |
| 11  | Unified orchestration system   | epic       | RECOMMENDED | 6      |

Total: 2 issues
```

### Filtered by Power Mode (`--power`)
```
Issues Recommending Power Mode:

| #   | Title                          | Complexity | Phases |
|-----|--------------------------------|------------|--------|
| 11  | Unified orchestration system   | epic       | 6      |
| 18  | Refactor database layer        | large      | 5      |

Total: 2 issues recommending Power Mode
```

### No PopKit Guidance
```
Open Issues:

| #   | Title                          | Labels     | Power Mode  |
|-----|--------------------------------|------------|-------------|
| 25  | Fix typo in README             | docs       | (unknown)   |
| 26  | Add logging                    | feature    | (unknown)   |

Note: Issues without PopKit Guidance show "(unknown)"
      Use /popkit:work #N to auto-generate orchestration plan
```

## Inference for Issues Without Guidance

When an issue lacks PopKit Guidance, infer from:

| Indicator | Inferred Complexity | Power Mode |
|-----------|---------------------|------------|
| Label: `epic` | epic | RECOMMENDED |
| Label: `architecture` | large | RECOMMENDED |
| Label: `bug` | small-medium | optional |
| Label: `feature` | medium | optional |
| Label: `docs` | small | not_needed |
| No labels | unknown | (unknown) |

## Relationship to Other Commands

| Command | Purpose |
|---------|---------|
| `/popkit:work #N` | Start working on issue |
| `/popkit:issue view #N` | View full issue details |
| `/popkit:issue create` | Create new issue |
| `/popkit:power status` | Check Power Mode status |

## Architecture Integration

| Component | Integration |
|-----------|-------------|
| Issue Fetching | `gh issue list` via GitHub CLI |
| Guidance Parsing | `hooks/utils/github_issues.py` |
| Issue List Utility | `hooks/utils/issue_list.py` |
| Table Formatting | Terminal ASCII table |
