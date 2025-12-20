---
description: "clear | stats | list | invalidate <key>"
argument-hint: "<subcommand> [options]"
---

# /popkit:cache - Cache Management

Manage routine execution cache for token optimization. The cache stores results of expensive operations (git status, test results, lint) to reduce token usage in subsequent routine runs.

## Usage

```
/popkit:cache <subcommand> [options]
```

## Subcommands

| Subcommand | Description |
|------------|-------------|
| `clear` | Clear all cache entries (default) |
| `stats` | Display cache statistics |
| `list` | List all cached entries with expiration |
| `invalidate <key>` | Remove specific cache entry |

---

## Cache Clear

Remove all cached data and force fresh execution on next routine run.

```
/popkit:cache clear                   # Clear all cache
/popkit:cache                         # Same as clear (default)
```

**Use when:**
- After major code changes (merges, rebases)
- After dependency updates
- Cache giving stale results
- Before critical checks

**Implementation:**
```python
from routine_cache import RoutineCache

cache = RoutineCache()
cache.clear()
print("All cache entries cleared")
```

---

## Cache Stats

View cache health and storage statistics.

```
/popkit:cache stats                   # Display statistics
/popkit:cache stats --json            # JSON output
```

**Output:**
```
Cache Statistics:
  Valid entries: 5
  Expired entries: 2
  Cache size: 1,234 bytes
  Cache file: .claude/popkit/cache/routine_cache.json

Entry Details:
  git_status: Valid (expires in 4m 23s)
  test_results: Valid (expires in 55m 12s)
  lint_results: Expired (2m 15s ago)
```

**Implementation:**
```python
from routine_cache import RoutineCache, get_cache_stats_report

cache = RoutineCache()
print(get_cache_stats_report(cache))
```

---

## Cache List

Display all cache entries with their expiration status.

```
/popkit:cache list                    # List all entries
/popkit:cache list --verbose          # Include cached values
/popkit:cache list --expired          # Only expired entries
```

**Output:**
```
Cached Entries (7):

[VALID] git_status
  Cached: 2m 15s ago
  Expires: in 2m 45s
  TTL: 5 minutes
  Hash: abc123...

[VALID] test_results
  Cached: 12m ago
  Expires: in 48m
  TTL: 1 hour
  Data: {"passed": true, "latest_mtime": 1734567890}

[EXPIRED] lint_results
  Cached: 35m ago
  Expired: 5m ago
  TTL: 30 minutes
```

**Implementation:**
```python
from routine_cache import RoutineCache
import time

cache = RoutineCache()
for key, entry in cache.cache.items():
    status = "[EXPIRED]" if entry.is_expired() else "[VALID]"
    age = time.time() - entry.timestamp
    print(f"{status} {key} (age: {age:.0f}s, ttl: {entry.ttl}s)")
```

---

## Cache Invalidate

Remove specific cache entry by key.

```
/popkit:cache invalidate git_status   # Invalidate git status
/popkit:cache invalidate test_results # Invalidate tests
```

**Available Keys:**
- `git_status` - Git working directory state
- `git_diff_stat` - Changes diff statistics
- `test_results` - Test execution results
- `lint_results` - Linting results
- `type_check` - TypeScript type checking
- `last_commit` - Latest commit info
- `branch_info` - Branch metadata

**Implementation:**
```python
from routine_cache import RoutineCache, CACHE_KEYS

cache = RoutineCache()
cache.invalidate(CACHE_KEYS["GIT_STATUS"])
print(f"Cache entry invalidated: git_status")
```

---

## Cache Location

All cache data stored in:
```
.claude/popkit/cache/
└── routine_cache.json
```

**Structure:**
```json
{
  "git_status": {
    "key": "git_status",
    "value": " M file.py\n A new_file.py",
    "hash": "abc123...",
    "timestamp": 1734567890.123,
    "ttl": 300
  },
  "test_results": {
    "key": "test_results",
    "value": {
      "output": "...test output...",
      "passed": true,
      "latest_mtime": 1734567800.0
    },
    "hash": "def456...",
    "timestamp": 1734567850.0,
    "ttl": 3600
  }
}
```

---

## Cache TTL Settings

Default time-to-live for each cache type:

| Cache Type | TTL | Rationale |
|------------|-----|-----------|
| `git_status` | 5 min | Frequently changes during development |
| `git_diff_stat` | 5 min | Same as git status |
| `test_results` | 1 hour | Expensive to run, stable between edits |
| `lint_results` | 30 min | Medium cost, medium stability |
| `type_check` | 30 min | Medium cost, TypeScript errors persist |
| `last_commit` | 5 min | Rarely changes unless committing |
| `branch_info` | 5 min | Changes with branch switches |

---

## Examples

```bash
# Daily workflow
/popkit:routine morning --optimized    # Uses cache (96% token savings on 2nd run)

# After git merge
/popkit:cache clear                    # Clear stale cache
/popkit:routine morning --optimized    # Fresh run (24% savings vs standard)

# Check cache health
/popkit:cache stats                    # View statistics
/popkit:cache list                     # See what's cached

# Selective invalidation
/popkit:cache invalidate test_results  # Re-run tests only
/popkit:routine morning --optimized    # Other checks use cache

# Debug cache issues
/popkit:cache list --verbose           # See cached values
/popkit:cache clear                    # Force fresh execution
/popkit:routine morning --no-cache     # Bypass cache for one run
```

---

## Integration with Routine Optimization

Cache management works with:
- `/popkit:routine morning --optimized` - Uses cache automatically
- `/popkit:routine nightly --optimized` - Uses cache automatically
- `/popkit:routine --measure` - Tracks cache hit rate
- `--no-cache` flag - Bypasses cache for single run

**Token Savings:**
- First run with cache: 40-50% savings (compact flags)
- Cached run: 90-96% savings (skip expensive ops)
- See `.workspace/ROUTINE_OPTIMIZATION_GUIDE.md` for details

---

## Architecture

| Component | Integration |
|-----------|-------------|
| Cache Implementation | `hooks/utils/routine_cache.py` |
| Cache Storage | `.claude/popkit/cache/routine_cache.json` |
| Optimized Routine | `skills/pop-routine-optimized` |
| Measurement Tracking | `hooks/utils/routine_measurement.py` |

## Related Commands

| Command | Purpose |
|---------|---------|
| `/popkit:routine --optimized` | Execute routine with caching |
| `/popkit:routine --no-cache` | Bypass cache for one run |
| `/popkit:routine --measure` | Track cache effectiveness |
| `/popkit:stats` | View usage metrics including cache hits |
