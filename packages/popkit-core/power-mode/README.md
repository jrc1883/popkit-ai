# PopKit Power Mode

Multi-agent orchestration for parallel agent collaboration via pub/sub messaging.

## Architecture

Power Mode uses a **zero-setup** architecture with three available modes:

| Mode              | Setup Required             | Max Agents | Parallel      | Best For              |
| ----------------- | -------------------------- | ---------- | ------------- | --------------------- |
| **Native Async**  | None (Claude Code 2.0.64+) | 5+         | True parallel | Default, recommended  |
| **Upstash Redis** | Set env vars               | 10+        | True parallel | Advanced coordination |
| **File-based**    | None (automatic fallback)  | 2-3        | Sequential    | Legacy compatibility  |

**No Docker or local Redis installation required.** Native Async mode works out of the box with Claude Code 2.0.64+.

## Setup for Upstash (Optional Advanced Feature)

To enable Upstash Redis mode for 10+ agent coordination:

```bash
export UPSTASH_REDIS_REST_URL="https://your-instance.upstash.io"
export UPSTASH_REDIS_REST_TOKEN="your-token"
```

Get free credentials at [upstash.com](https://upstash.com). No Docker required - Upstash is cloud-based.

### Verify Setup

```bash
# Check Upstash status
python upstash_adapter.py --status

# Test connection
python upstash_adapter.py --ping

# Run full test suite
python upstash_adapter.py --test
```

## Free Tier (File-Based)

Free tier users don't need any setup. Power Mode automatically uses file-based coordination when Upstash isn't configured.

Limitations:

- 2-3 agents maximum (sequential)
- No cross-session persistence
- Local-only coordination

## Files

| File                 | Purpose                                 |
| -------------------- | --------------------------------------- |
| `upstash_adapter.py` | Upstash REST API client                 |
| `mode_selector.py`   | Auto-detects best available mode        |
| `coordinator.py`     | Mesh brain for agent orchestration      |
| `protocol.py`        | Message types and serialization         |
| `checkin-hook.py`    | PostToolUse hook for periodic check-ins |
| `file_fallback.py`   | File-based coordination (free tier)     |
| `config.json`        | Power Mode configuration                |

## Redis Channels

Power Mode uses 6 pub/sub channels (via Redis Streams for Upstash):

| Channel           | Publisher   | Subscribers          | Purpose                 |
| ----------------- | ----------- | -------------------- | ----------------------- |
| `pop:broadcast`   | Coordinator | All agents           | Broadcast messages      |
| `pop:heartbeat`   | Agents      | Coordinator          | Health checks           |
| `pop:results`     | Agents      | Coordinator          | Task completions        |
| `pop:insights`    | Agents      | Coordinator + Agents | Shared discoveries      |
| `pop:coordinator` | External    | Coordinator          | Control commands        |
| `pop:human`       | Agents      | Coordinator          | Human approval requests |

## Data Stored in Redis

| Key Pattern                  | Type   | TTL     | Purpose                      |
| ---------------------------- | ------ | ------- | ---------------------------- |
| `pop:objective`              | String | Session | Current objective definition |
| `pop:state:{agent_id}`       | Hash   | Session | Agent state snapshots        |
| `pop:completed:{session_id}` | String | 24h     | Completed session results    |
| `pop:tasks:orphaned`         | List   | Session | Tasks from failed agents     |
| `pop:coordinator:status`     | String | Live    | Coordinator health           |
| `pop:patterns:{pattern_id}`  | Hash   | 24h     | Learned patterns             |

## Integration Points

### Power Mode Command

```
/popkit:power status   # Check mode and connection
/popkit:power start    # Start coordinator
/popkit:power stop     # Stop coordinator
```

### Coordinator

```python
from coordinator import PowerModeCoordinator

coordinator = PowerModeCoordinator(objective)
if coordinator.connect():  # Auto-detects Upstash or file-based
    coordinator.start()
```

### Check-In Hook

Agents publish to channels every N tool calls via `checkin-hook.py`.

## Troubleshooting

### Upstash Not Configured

```
Upstash credentials required for Power Mode Redis features.
Set UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN environment variables.
```

**Solution:** Get credentials from [upstash.com](https://upstash.com) or use free tier (file-based mode).

### Connection Failed

```
Upstash connection failed. Check your credentials.
```

**Solution:** Verify your Upstash credentials are correct and the database is active.

### File-Based Mode Active

If you see "File-based mode" when expecting Upstash, check:

1. Environment variables are set correctly
2. Upstash database is active
3. Run `python upstash_adapter.py --status` to diagnose

## Resources

- Upstash Documentation: https://upstash.com/docs
- PopKit Power Mode Guide: `/popkit:power help`
