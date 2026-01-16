# PopKit Observability Platform - Architecture Design

> **For Claude:** Use executing-plans skill to implement this design task-by-task.

**Goal:** Cloud-native real-time observability platform for PopKit sessions

**Architecture:** Cloudflare Workers + Upstash (Redis + Vector) + Next.js Dashboard

**Tech Stack:** Python (plugin), TypeScript (API + Dashboard), Cloudflare Workers, Upstash

---

## Design Status

**Created:** 2026-01-13
**Related Issue:** #110 (Power Mode transcript parsing - partial scope)
**Scope:** Full observability platform beyond Issue #110
**Stakeholder Approval:** In progress (Section 2 under review)

---

## Section 1: Overview & Vision ✅ APPROVED

### Core Design Principles

**1. Cloud-Native First**
- Cloudflare Workers for edge computing (global, low-latency)
- Upstash Redis for real-time session state
- Upstash Vector for AI-powered query/search
- No local server required (unlike OPTIMUS localhost:3051)

**2. Three-Tier Value Proposition**

| Tier | Features | Infrastructure |
|------|----------|----------------|
| **Free** | Static HTML reports (existing), Local transcript parsing, Basic tool call timeline | Plugin-only, no cloud |
| **Pro** | Real-time dashboard, Live agent monitoring, Token/cost tracking, Session replay | Cloudflare + Upstash Redis |
| **Team** | Shared observability, Team analytics, Pattern library, Cross-session learning | + Upstash Vector, shared workspace |

**3. Integration Strategy**
- **Issue #110 scope**: Integrate `transcript_parser.py` into `subagent-stop.py` hook
- **Beyond #110**: Stream parsed data to Cloudflare Workers API
- **Existing `/record` command**: Enhanced with optional cloud sync
- **Power Mode**: Native observability (sub-agent transcripts automatically parsed)

### High-Level Data Flow

```
Claude Code Session
       ↓
PopKit Hooks (pre-tool, post-tool, subagent-stop)
       ↓
Session Recorder (local recording.json)
       ↓
Transcript Parser (extracts tool calls, reasoning, tokens)
       ↓
       ├─→ Free Tier: HTML Report Generator
       │
       └─→ Pro/Team: Cloudflare Workers API
                ↓
           Upstash Redis (real-time state)
                ↓
           Upstash Vector (search/patterns)
                ↓
           Dashboard (Next.js, live updates)
```

### Key Components

1. **PopKit Plugin (Enhanced)**
   - `/popkit-observe:observe start` - Enable cloud streaming
   - `/popkit-observe:observe stop` - Stop and generate report
   - `/popkit-observe:observe dashboard` - Open web dashboard
   - Hook integration for automatic Power Mode observability

2. **Cloudflare Workers API**
   - `/api/session/start` - Initialize tracking
   - `/api/session/stream` - Receive tool call events
   - `/api/session/stop` - Finalize and analyze
   - `/api/dashboard/live` - Server-Sent Events (SSE) stream

3. **Upstash Storage Layer**
   - Redis: Live session state, real-time metrics
   - Vector: Session embeddings, pattern matching, AI search

4. **Dashboard (Next.js)**
   - Real-time agent timeline
   - Cost tracking per tool/agent
   - Token usage graphs
   - Team workspace view

---

## Section 2: Plugin Architecture (IN PROGRESS)

### Decision: New `popkit-observe` Plugin

**Rationale:**
- Observability is a distinct concern (not dev, ops, or research)
- Deserves dedicated namespace: `/popkit-observe:observe`
- Allows independent versioning and optional installation
- Follows PopKit modular plugin pattern

**Structure:**
```
packages/
├── popkit-observe/          # NEW PLUGIN
│   ├── .claude-plugin/
│   │   └── plugin.json      # Plugin manifest
│   ├── commands/
│   │   └── observe.md       # /popkit-observe:observe command
│   ├── hooks/
│   │   ├── streaming-hook.py    # Cloud telemetry streaming
│   │   └── session-sync.py      # Offline queue sync
│   ├── scripts/
│   │   └── dashboard-launcher.py
│   └── README.md
│
└── shared-py/
    └── popkit_shared/
        └── utils/
            ├── observability_client.py   # NEW: Unified streaming client
            ├── session_recorder.py       # EXISTING
            ├── transcript_parser.py      # EXISTING
            ├── privacy.py                # EXISTING
            └── upstash_telemetry.py      # EXISTING (leverage patterns)
```

### Streaming Strategy: Adaptive Hybrid

**User Control via Commands:**
```bash
/popkit-observe:observe start --mode=realtime    # Stream every tool immediately
/popkit-observe:observe start --mode=batch       # Batch 50 tools (default)
/popkit-observe:observe start --mode=smart       # Adaptive (errors immediate, rest batched)
```

**Implementation Logic:**
```python
# Adaptive batching with event-driven critical path
class ObservabilityClient:
    def __init__(self, mode="batch"):
        self.mode = mode  # realtime | batch | smart
        self.batch_size = 50
        self.queue = []

    def record_tool_call(self, event):
        """Record with adaptive strategy"""
        if self.mode == "realtime":
            self._stream_now(event)

        elif self.mode == "smart":
            # Critical events: stream immediately
            if event.get("error") or event.get("tool_name") == "Bash":
                self._stream_now(event)
            else:
                self._queue_and_batch(event)

        elif self.mode == "batch":
            self._queue_and_batch(event)

    def _queue_and_batch(self, event):
        """Queue events and flush when batch size reached"""
        self.queue.append(event)
        if len(self.queue) >= self.batch_size:
            self._flush_batch()

    def on_session_end(self):
        """Flush any remaining events"""
        self._flush_batch()
```

**Offline Resilience:**
- Events persist locally in `.claude/popkit/queue/{session_id}.jsonl`
- Background sync when cloud reconnects
- User sees full history even during outages
- Uses existing `upstash_telemetry.py` patterns (queue, rate limiting)

**Privacy Controls:**
- Leverage existing `privacy.py` settings (strict/moderate/minimal)
- Use `pattern_anonymizer.py` to redact credentials, paths, emails
- User consent required before cloud streaming
- Data retention: 90 days default (configurable)

### Hook Integration

**Phase 1: Issue #110 - Integrate Transcript Parser (Local Only)**

Update `packages/popkit-core/hooks/subagent-stop.py` line 195:

```python
# Replace TODO with actual parsing
if transcript_path and Path(transcript_path).exists():
    from popkit_shared.utils.transcript_parser import TranscriptParser

    parser = TranscriptParser(transcript_path)
    tool_calls = parser.get_all_tool_uses()
    token_usage = parser.get_total_token_usage()

    # Store parsed data locally
    recorder.record_event({
        "type": "subagent_transcript_parsed",
        "agent_id": agent_id,
        "tool_calls": tool_calls,
        "tool_count": len(tool_calls),
        "tokens": token_usage.to_dict(),
        "timestamp": datetime.now().isoformat()
    })
```

**Phase 2: Add Cloud Streaming (Pro Tier)**

Create `packages/popkit-observe/hooks/streaming-hook.py`:

```python
#!/usr/bin/env python3
"""
Cloud Streaming Hook - Pro Tier
Streams tool events to Cloudflare Workers API
"""

import sys
import json
from pathlib import Path

# Import observability client
sys.path.insert(0, str(Path.home() / '.claude' / 'popkit' / 'packages' / 'shared-py'))
from popkit_shared.utils.observability_client import get_observability_client

def main():
    """Post-tool-use hook - stream to cloud if Pro tier enabled"""
    try:
        input_data = sys.stdin.read()
        data = json.loads(input_data) if input_data.strip() else {}

        # Check if cloud observability is enabled
        client = get_observability_client()
        if not client.is_enabled():
            print(json.dumps({"status": "skip", "reason": "cloud observability disabled"}))
            return

        # Stream tool event
        event = {
            "session_id": client.get_session_id(),
            "event_type": "tool_call_complete",
            "tool_name": data.get("tool_name"),
            "duration_ms": data.get("execution_time"),
            "tokens": data.get("token_usage"),
            "success": not data.get("error"),
            "timestamp": data.get("timestamp")
        }

        client.stream_event(event)

        print(json.dumps({"status": "success"}))

    except Exception as e:
        # Don't block on streaming failures
        print(json.dumps({"status": "error", "error": str(e)}))

if __name__ == "__main__":
    main()
```

---

## Section 3: Command Structure ✅ COMPLETE

Following PopKit command patterns from `/popkit-core:record` and `/popkit-core:power`.

### Command Definition: `/popkit-observe:observe`

**File:** `packages/popkit-observe/commands/observe.md`

```markdown
---
description: "start | stop | status | dashboard | sync [--mode realtime|batch|smart]"
argument-hint: "<subcommand> [options]"
---

# /popkit-observe:observe - Session Observability

Real-time observability and analytics for PopKit sessions with optional cloud streaming.

## Architecture

**Free Tier:** Local recording + HTML reports (no cloud required)
**Pro Tier:** + Real-time cloud streaming to Cloudflare Workers
**Team Tier:** + Shared observability workspace

## Usage

```bash
/popkit-observe:observe start                    # Enable (batch mode, local + cloud if Pro)
/popkit-observe:observe start --mode=realtime    # Stream every tool immediately
/popkit-observe:observe start --mode=smart       # Adaptive (errors immediate, rest batched)
/popkit-observe:observe stop                     # Stop and generate report
/popkit-observe:observe status                   # Check recording state
/popkit-observe:observe dashboard                # Open web dashboard (Pro tier)
/popkit-observe:observe sync                     # Sync offline queue to cloud
```

## Subcommands

| Subcommand | Description | Tier |
|------------|-------------|------|
| start (default) | Enable observability with mode control | Free/Pro |
| stop | Stop recording and generate report | Free/Pro |
| status | Check recording state and sync status | Free/Pro |
| dashboard | Open real-time web dashboard | Pro/Team |
| sync | Manually sync offline queue to cloud | Pro |

---

## start (default)

Enable session observability with optional cloud streaming.

### Options

- `--mode=batch` (default) - Queue and batch 50 tools before streaming
- `--mode=realtime` - Stream every tool call immediately
- `--mode=smart` - Adaptive: errors immediate, normal tools batched
- `--local-only` - Disable cloud streaming (Free tier behavior)

### Instructions

When user runs `/popkit-observe:observe start [--mode=<mode>]`:

**Step 1: Create recording state**

```python
from pathlib import Path
import json
from datetime import datetime
import uuid

# Create observability state directory
observe_dir = Path.home() / '.claude' / 'popkit' / 'observe'
observe_dir.mkdir(parents=True, exist_ok=True)

state_file = observe_dir / 'observe-state.json'

# Generate session ID
timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
unique_suffix = str(uuid.uuid4())[:8]
session_id = f"{timestamp}-{unique_suffix}"

# Get Claude's session ID for correlation
claude_session_id = None
session_log = Path('logs/session_start.json')
if session_log.exists():
    try:
        log_data = json.loads(session_log.read_text())
        if log_data:
            claude_session_id = log_data[-1].get('session_id')
    except:
        pass

# Parse mode argument
mode = "batch"  # default
if "--mode=realtime" in args:
    mode = "realtime"
elif "--mode=smart" in args:
    mode = "smart"

# Check tier and cloud availability
from popkit_shared.utils.premium_client import get_tier, is_cloud_available

tier = get_tier()
cloud_enabled = tier in ["pro", "team"] and is_cloud_available() and "--local-only" not in args

state = {
    'active': True,
    'session_id': session_id,
    'claude_session_id': claude_session_id,
    'started_at': datetime.now().isoformat(),
    'mode': mode,
    'tier': tier,
    'cloud_enabled': cloud_enabled,
    'events_recorded': 0,
    'events_streamed': 0
}

state_file.write_text(json.dumps(state, indent=2))

print(f"[OK] Observability ENABLED")
print(f"Session ID: {session_id}")
print(f"Mode: {mode}")
print(f"Tier: {tier}")
if cloud_enabled:
    print(f"Cloud streaming: ACTIVE")
    print(f"Dashboard: https://observe.popkit.ai/session/{session_id}")
else:
    print(f"Cloud streaming: DISABLED (Free tier or --local-only)")
print(f"")
print(f"All tool calls will be recorded locally.")
if cloud_enabled:
    print(f"Events will stream to cloud in '{mode}' mode.")
print(f"")
print(f"To stop: /popkit-observe:observe stop")
```

**Step 2: Initialize observability client**

```python
import sys
sys.path.insert(0, str(Path.home() / '.claude' / 'popkit' / 'packages' / 'shared-py'))

from popkit_shared.utils.observability_client import ObservabilityClient

# Initialize client with user's mode preference
client = ObservabilityClient(
    session_id=session_id,
    mode=mode,
    cloud_enabled=cloud_enabled
)

# Notify user of privacy settings
from popkit_shared.utils.privacy import load_privacy_settings

privacy = load_privacy_settings()
if cloud_enabled and not privacy.consent_given:
    print(f"")
    print(f"⚠️  PRIVACY NOTICE")
    print(f"Cloud streaming will anonymize sensitive data:")
    print(f"  - Credentials, API keys, tokens")
    print(f"  - Email addresses, IP addresses")
    print(f"  - User-specific file paths")
    print(f"")
    print(f"Anonymization level: {privacy.anonymization_level}")
    print(f"Data retention: {privacy.auto_delete_days} days")
    print(f"")
    print(f"To review: /popkit-core:privacy status")
```

**Step 3: Enable statusline widget**

```python
config_file = Path.home() / '.claude' / 'popkit' / 'config.json'

if config_file.exists():
    config = json.loads(config_file.read_text())
else:
    config = {}

statusline = config.get('statusline', {})
widgets = statusline.get('widgets', ['popkit', 'efficiency'])

if 'observe' not in widgets:
    widgets.insert(1, 'observe')
    statusline['widgets'] = widgets
    config['statusline'] = statusline

    config_file.parent.mkdir(parents=True, exist_ok=True)
    config_file.write_text(json.dumps(config, indent=2))

print("Status line widget: OBSERVE [*] <count>")
```

---

## stop

Stop observability and generate comprehensive report.

### Instructions

When user runs `/popkit-observe:observe stop`:

**Step 1: Flush remaining events**

```python
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path.home() / '.claude' / 'popkit' / 'packages' / 'shared-py'))

state_file = Path.home() / '.claude' / 'popkit' / 'observe' / 'observe-state.json'

if not state_file.exists():
    print("[ERROR] Observability is not active")
    exit(1)

state = json.loads(state_file.read_text())
session_id = state.get('session_id')

# Flush any queued events before stopping
from popkit_shared.utils.observability_client import get_observability_client

client = get_observability_client()
if client:
    client.on_session_end()  # Flush batch queue
    print(f"Flushing queued events...")

# Mark as stopped
state['active'] = False
state['stopped_at'] = datetime.now().isoformat()
state_file.write_text(json.dumps(state, indent=2))

print(f"[OK] Observability STOPPED")
print(f"Session ID: {session_id}")
```

**Step 2: Generate local HTML report (Free + Pro tiers)**

```python
from pathlib import Path
import subprocess

recordings_dir = Path.home() / '.claude' / 'popkit' / 'recordings'
recordings = list(recordings_dir.glob(f'*{session_id}*.json'))

if not recordings:
    recordings = sorted(
        recordings_dir.glob('*.json'),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

if recordings:
    recording_file = recordings[0]
    html_file = recording_file.with_suffix('.html')

    result = subprocess.run([
        'python',
        'packages/shared-py/popkit_shared/utils/html_report_generator_v10.py',
        str(recording_file),
        str(html_file)
    ], capture_output=True, text=True)

    if result.returncode == 0:
        print(f"")
        print(f"[REPORT] Local Forensics Report:")
        print(f"")
        print(f"  file:///{html_file.as_posix()}")
        print(f"")
    else:
        print(f"[WARN] Failed to generate HTML report: {result.stderr}")
```

**Step 3: Show cloud dashboard link (Pro tier only)**

```python
if state.get('cloud_enabled'):
    print(f"")
    print(f"[DASHBOARD] Real-Time Cloud Report:")
    print(f"")
    print(f"  https://observe.popkit.ai/session/{session_id}")
    print(f"")
    print(f"  - Live tool timeline")
    print(f"  - Token/cost breakdown")
    print(f"  - Agent coordination graph")
    print(f"  - Session replay")
    print(f"")
```

---

## status

Check current observability state.

### Instructions

When user runs `/popkit-observe:observe status`:

```python
from pathlib import Path
import json

state_file = Path.home() / '.claude' / 'popkit' / 'observe' / 'observe-state.json'

if not state_file.exists():
    print("Observability: INACTIVE")
    print("")
    print("To start: /popkit-observe:observe start")
    exit(0)

state = json.loads(state_file.read_text())

if state.get('active'):
    session_id = state.get('session_id')
    mode = state.get('mode', 'batch')
    tier = state.get('tier', 'free')
    cloud_enabled = state.get('cloud_enabled', False)
    events_recorded = state.get('events_recorded', 0)
    events_streamed = state.get('events_streamed', 0)

    print(f"Observability: ACTIVE [*]")
    print(f"")
    print(f"Session ID: {session_id}")
    print(f"Started: {state.get('started_at')}")
    print(f"Mode: {mode}")
    print(f"Tier: {tier}")
    print(f"")
    print(f"Events recorded: {events_recorded}")
    if cloud_enabled:
        print(f"Events streamed: {events_streamed}")

        # Check sync status
        queue_dir = Path.home() / '.claude' / 'popkit' / 'observe' / 'queue'
        if queue_dir.exists():
            pending = len(list(queue_dir.glob('*.jsonl')))
            if pending > 0:
                print(f"Pending sync: {pending} batches")

    print(f"")
    if cloud_enabled:
        print(f"Dashboard: https://observe.popkit.ai/session/{session_id}")
        print(f"")
    print(f"To stop: /popkit-observe:observe stop")
else:
    print("Observability: STOPPED")
    print(f"Last session: {state.get('session_id')}")
    print("")
    print("To start new: /popkit-observe:observe start")
```

---

## dashboard

Open real-time web dashboard (Pro tier).

### Instructions

When user runs `/popkit-observe:observe dashboard`:

```python
from pathlib import Path
import json
import webbrowser

state_file = Path.home() / '.claude' / 'popkit' / 'observe' / 'observe-state.json'

if not state_file.exists():
    print("[ERROR] No active observability session")
    print("Start one with: /popkit-observe:observe start")
    exit(1)

state = json.loads(state_file.read_text())

if not state.get('cloud_enabled'):
    print("[ERROR] Dashboard requires Pro tier")
    print("")
    print("Upgrade at: /popkit-core:account upgrade")
    exit(1)

session_id = state.get('session_id')
dashboard_url = f"https://observe.popkit.ai/session/{session_id}"

print(f"Opening dashboard...")
print(f"")
print(f"  {dashboard_url}")
print(f"")

webbrowser.open(dashboard_url)

print("If browser didn't open, copy the URL above.")
```

---

## sync

Manually sync offline queue to cloud (Pro tier).

### Instructions

When user runs `/popkit-observe:observe sync`:

```python
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path.home() / '.claude' / 'popkit' / 'packages' / 'shared-py'))

state_file = Path.home() / '.claude' / 'popkit' / 'observe' / 'observe-state.json'

if not state_file.exists():
    print("[ERROR] No observability session found")
    exit(1)

state = json.loads(state_file.read_text())

if not state.get('cloud_enabled'):
    print("[ERROR] Cloud sync requires Pro tier")
    exit(1)

# Sync offline queue
from popkit_shared.utils.observability_client import sync_offline_queue

print("Syncing offline queue to cloud...")
print("")

result = sync_offline_queue()

if result['success']:
    print(f"[OK] Sync complete")
    print(f"")
    print(f"Batches synced: {result['batches_synced']}")
    print(f"Events synced: {result['events_synced']}")
    print(f"Failed: {result['failed']}")
else:
    print(f"[ERROR] Sync failed: {result['error']}")
```

---

## Examples

### Basic Workflow (Free Tier)

```bash
# Start local recording
/popkit-observe:observe start --local-only

# Work normally - all tools recorded locally
/popkit-dev:next
/popkit-dev:git commit

# Stop and get HTML report
/popkit-observe:observe stop
# → Report: file:///<USER_HOME>/.claude/popkit/recordings/20260113-142530.html
```

### Real-Time Streaming (Pro Tier)

```bash
# Start with real-time cloud streaming
/popkit-observe:observe start --mode=realtime

# Every tool call streams immediately to dashboard
# Open dashboard in browser
/popkit-observe:observe dashboard

# Stop when done
/popkit-observe:observe stop
# → Local HTML + Cloud dashboard URL
```

### Smart Mode (Pro Tier - Recommended)

```bash
# Adaptive: errors stream immediately, normal tools batched
/popkit-observe:observe start --mode=smart

# Errors and Bash commands stream instantly
# Other tools batch for efficiency

/popkit-observe:observe status
# → Shows events recorded vs streamed

/popkit-observe:observe stop
```

---

## Related

- **Local Recording**: `packages/shared-py/popkit_shared/utils/session_recorder.py`
- **Transcript Parser**: `packages/shared-py/popkit_shared/utils/transcript_parser.py`
- **Cloud Client**: `packages/shared-py/popkit_shared/utils/observability_client.py`
- **Privacy Controls**: `packages/shared-py/popkit_shared/utils/privacy.py`
- **HTML Reports**: `packages/shared-py/popkit_shared/utils/html_report_generator_v10.py`
```

### Plugin Manifest

**File:** `packages/popkit-observe/.claude-plugin/plugin.json`

```json
{
  "name": "popkit-observe",
  "version": "1.0.0-beta.1",
  "description": "Session observability and analytics - local recording + optional cloud streaming for real-time insights",
  "author": {
    "name": "Joseph Cannon",
    "email": "joseph@thehouseofdeals.com"
  },
  "license": "MIT",
  "repository": "https://github.com/jrc1883/popkit-claude"
}
```

---

## Section 4: Cloudflare Workers API ✅ COMPLETE

Cloud backend for PopKit Observability Platform running on Cloudflare Workers with Upstash storage.

### Architecture Overview

```
PopKit Plugin (Client)
       ↓ HTTPS
Cloudflare Workers (Edge)
       ↓
   ┌───┴────┐
   ↓        ↓
Upstash    Upstash
Redis      Vector
(state)    (search)
```

**Benefits:**
- **Global Edge Network**: <50ms latency worldwide
- **Auto-scaling**: Handles spikes automatically
- **Zero-ops**: No servers to manage
- **Cost-effective**: Pay per request

### API Endpoints

**Base URL**: `https://api.popkit.ai/observe/v1`

| Endpoint | Method | Purpose | Tier |
|----------|--------|---------|------|
| `/session/start` | POST | Initialize new session | Pro/Team |
| `/session/stream` | POST | Stream tool events (batch or single) | Pro/Team |
| `/session/stop` | POST | Finalize session | Pro/Team |
| `/session/{id}` | GET | Retrieve session data | Pro/Team |
| `/session/{id}/events` | GET | Get session events with pagination | Pro/Team |
| `/dashboard/live/{id}` | GET | Server-Sent Events stream | Pro/Team |
| `/search/query` | POST | Semantic search across sessions | Team |
| `/team/workspace` | GET | Team workspace data | Team |

### Authentication

**API Key-Based Authentication**

```typescript
// Request headers
{
  "Authorization": "Bearer pk_live_abc123...",
  "X-PopKit-Tier": "pro" | "team",
  "X-PopKit-Version": "1.0.0-beta.5",
  "Content-Type": "application/json"
}
```

**API Key Format:**
- Pro tier: `pk_live_xxx` (32 chars)
- Team tier: `tk_live_xxx` (32 chars)
- Dev/Test: `pk_test_xxx` (32 chars)

**Key Management:**
- Stored in `~/.claude/popkit/credentials.json`
- Retrieved via `/popkit-core:account keys`
- Auto-included by `observability_client.py`

**Rate Limits:**
- **Pro**: 100 requests/minute, 10,000 events/hour
- **Team**: 500 requests/minute, 50,000 events/hour
- **Burst**: 2x normal rate for 60 seconds

### Endpoint Specifications

#### POST `/session/start`

Initialize a new observability session.

**Request:**
```json
{
  "session_id": "20260113-142530-a1b2c3d4",
  "mode": "batch" | "realtime" | "smart",
  "metadata": {
    "claude_version": "2.1.14",
    "popkit_version": "1.0.0-beta.5",
    "os": "win32",
    "project_path": "[REDACTED]"
  }
}
```

**Response:**
```json
{
  "success": true,
  "session_id": "20260113-142530-a1b2c3d4",
  "dashboard_url": "https://observe.popkit.ai/session/20260113-142530-a1b2c3d4",
  "sse_endpoint": "https://api.popkit.ai/observe/v1/dashboard/live/20260113-142530-a1b2c3d4",
  "redis_ttl": 86400
}
```

**Implementation (Cloudflare Worker):**
```typescript
// src/routes/session/start.ts
import { Env } from '../../types';
import { Redis } from '@upstash/redis/cloudflare';

export async function handleSessionStart(
  request: Request,
  env: Env
): Promise<Response> {
  const { session_id, mode, metadata } = await request.json();

  // Validate session_id format
  if (!session_id.match(/^\d{8}-\d{6}-[a-f0-9]{8}$/)) {
    return new Response(
      JSON.stringify({ error: 'Invalid session ID format' }),
      { status: 400 }
    );
  }

  // Initialize Redis client
  const redis = new Redis({
    url: env.UPSTASH_REDIS_REST_URL,
    token: env.UPSTASH_REDIS_REST_TOKEN,
  });

  // Store session metadata
  const sessionKey = `popkit:observe:session:${session_id}`;
  await redis.hset(sessionKey, {
    mode,
    started_at: new Date().toISOString(),
    status: 'active',
    event_count: 0,
    metadata: JSON.stringify(metadata),
  });

  // Set TTL: 24 hours
  await redis.expire(sessionKey, 86400);

  // Initialize event stream
  const eventsKey = `popkit:observe:events:${session_id}`;
  await redis.xadd(eventsKey, '*', {
    type: 'session_start',
    timestamp: new Date().toISOString(),
  });

  return new Response(
    JSON.stringify({
      success: true,
      session_id,
      dashboard_url: `https://observe.popkit.ai/session/${session_id}`,
      sse_endpoint: `https://api.popkit.ai/observe/v1/dashboard/live/${session_id}`,
      redis_ttl: 86400,
    }),
    {
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
    }
  );
}
```

---

#### POST `/session/stream`

Stream tool call events (single or batch).

**Request (Single Event):**
```json
{
  "session_id": "20260113-142530-a1b2c3d4",
  "event": {
    "type": "tool_call_complete",
    "tool_name": "Read",
    "timestamp": "2026-01-13T14:25:35.123Z",
    "duration_ms": 45,
    "tokens": {
      "input": 1250,
      "output": 89,
      "total": 1339
    },
    "success": true,
    "metadata": {
      "file_path": "[REDACTED]"
    }
  }
}
```

**Request (Batch):**
```json
{
  "session_id": "20260113-142530-a1b2c3d4",
  "events": [
    { /* event 1 */ },
    { /* event 2 */ },
    // ... up to 50 events
  ]
}
```

**Response:**
```json
{
  "success": true,
  "events_received": 1,
  "session_event_count": 47,
  "rate_limit": {
    "remaining": 95,
    "reset_at": "2026-01-13T14:26:00Z"
  }
}
```

**Implementation:**
```typescript
// src/routes/session/stream.ts
import { Redis } from '@upstash/redis/cloudflare';
import { anonymizeEvent } from '../../utils/privacy';
import { checkRateLimit } from '../../utils/rateLimit';

export async function handleSessionStream(
  request: Request,
  env: Env,
  ctx: ExecutionContext
): Promise<Response> {
  const { session_id, event, events } = await request.json();

  // Check rate limit
  const rateLimitResult = await checkRateLimit(request, env);
  if (!rateLimitResult.allowed) {
    return new Response(
      JSON.stringify({
        error: 'Rate limit exceeded',
        retry_after: rateLimitResult.retry_after,
      }),
      { status: 429 }
    );
  }

  const redis = new Redis({
    url: env.UPSTASH_REDIS_REST_URL,
    token: env.UPSTASH_REDIS_REST_TOKEN,
  });

  // Normalize to array
  const eventList = events || [event];

  // Anonymize sensitive data
  const anonymizedEvents = eventList.map(anonymizeEvent);

  // Stream events to Redis
  const eventsKey = `popkit:observe:events:${session_id}`;
  const pipeline = redis.pipeline();

  for (const evt of anonymizedEvents) {
    pipeline.xadd(eventsKey, '*', {
      type: evt.type,
      data: JSON.stringify(evt),
      timestamp: evt.timestamp,
    });
  }

  // Update session event count
  const sessionKey = `popkit:observe:session:${session_id}`;
  pipeline.hincrby(sessionKey, 'event_count', eventList.length);

  await pipeline.exec();

  // Broadcast to SSE listeners (non-blocking)
  ctx.waitUntil(
    broadcastToSSE(session_id, anonymizedEvents, env)
  );

  return new Response(
    JSON.stringify({
      success: true,
      events_received: eventList.length,
      rate_limit: rateLimitResult.limit_info,
    }),
    { status: 200 }
  );
}

async function broadcastToSSE(
  session_id: string,
  events: any[],
  env: Env
): Promise<void> {
  // Publish to Durable Object for SSE distribution
  const id = env.SSE_BROADCASTER.idFromName(session_id);
  const stub = env.SSE_BROADCASTER.get(id);
  await stub.fetch('https://internal/broadcast', {
    method: 'POST',
    body: JSON.stringify({ events }),
  });
}
```

---

#### GET `/dashboard/live/{session_id}`

Server-Sent Events (SSE) stream for real-time dashboard updates.

**Response (SSE Stream):**
```
HTTP/1.1 200 OK
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

event: session_start
data: {"session_id":"20260113-142530-a1b2c3d4","timestamp":"2026-01-13T14:25:30Z"}

event: tool_call
data: {"type":"tool_call_complete","tool_name":"Read","duration_ms":45,"tokens":{"total":1339}}

event: heartbeat
data: {"timestamp":"2026-01-13T14:25:45Z"}
```

**Implementation (Durable Object):**
```typescript
// src/durable-objects/SSEBroadcaster.ts
export class SSEBroadcaster {
  state: DurableObjectState;
  connections: Set<WebSocket>;

  constructor(state: DurableObjectState, env: Env) {
    this.state = state;
    this.connections = new Set();
  }

  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);

    // Internal broadcast endpoint
    if (url.pathname === '/broadcast') {
      const { events } = await request.json();
      this.broadcast(events);
      return new Response('OK');
    }

    // SSE endpoint for clients
    if (request.headers.get('Accept') === 'text/event-stream') {
      return this.handleSSE(request);
    }

    return new Response('Not Found', { status: 404 });
  }

  async handleSSE(request: Request): Promise<Response> {
    const { readable, writable } = new TransformStream();
    const writer = writable.getWriter();
    const encoder = new TextEncoder();

    // Store connection
    const connection = { writer, closed: false };
    this.connections.add(connection as any);

    // Send initial connection event
    await writer.write(
      encoder.encode(
        'event: connected\n' +
        `data: {"timestamp":"${new Date().toISOString()}"}\n\n`
      )
    );

    // Heartbeat every 30 seconds
    const heartbeat = setInterval(async () => {
      if (connection.closed) {
        clearInterval(heartbeat);
        return;
      }

      try {
        await writer.write(
          encoder.encode(
            'event: heartbeat\n' +
            `data: {"timestamp":"${new Date().toISOString()}"}\n\n`
          )
        );
      } catch {
        connection.closed = true;
        this.connections.delete(connection as any);
        clearInterval(heartbeat);
      }
    }, 30000);

    return new Response(readable, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
        'Access-Control-Allow-Origin': '*',
      },
    });
  }

  broadcast(events: any[]): void {
    const encoder = new TextEncoder();

    for (const event of events) {
      const message =
        `event: tool_call\n` +
        `data: ${JSON.stringify(event)}\n\n`;

      const encoded = encoder.encode(message);

      for (const connection of this.connections) {
        try {
          (connection as any).writer.write(encoded);
        } catch {
          // Connection closed, remove it
          this.connections.delete(connection);
        }
      }
    }
  }
}
```

---

#### POST `/search/query` (Team Tier)

Semantic search across team sessions using Upstash Vector.

**Request:**
```json
{
  "query": "sessions where error rate > 5%",
  "workspace_id": "team_abc123",
  "filters": {
    "date_range": {
      "start": "2026-01-01",
      "end": "2026-01-13"
    },
    "user_id": "optional_filter"
  },
  "limit": 20
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "session_id": "20260112-093045-xyz",
      "score": 0.92,
      "metadata": {
        "error_rate": 0.08,
        "total_events": 234,
        "user": "user@example.com",
        "date": "2026-01-12"
      }
    }
  ],
  "total": 15
}
```

**Implementation:**
```typescript
// src/routes/search/query.ts
import { Index } from '@upstash/vector';

export async function handleSearchQuery(
  request: Request,
  env: Env
): Promise<Response> {
  const { query, workspace_id, filters, limit } = await request.json();

  // Initialize Upstash Vector
  const index = new Index({
    url: env.UPSTASH_VECTOR_REST_URL,
    token: env.UPSTASH_VECTOR_REST_TOKEN,
  });

  // Embed query using Voyage AI (or OpenAI)
  const embedding = await embedQuery(query, env);

  // Search with metadata filters
  const results = await index.query({
    vector: embedding,
    topK: limit || 20,
    includeMetadata: true,
    filter: buildFilter(workspace_id, filters),
  });

  return new Response(
    JSON.stringify({
      success: true,
      results: results.map(r => ({
        session_id: r.id,
        score: r.score,
        metadata: r.metadata,
      })),
      total: results.length,
    }),
    { status: 200 }
  );
}
```

---

### Data Storage Schema

#### Upstash Redis Keys

```
# Session metadata
popkit:observe:session:{session_id}
  - mode: "batch" | "realtime" | "smart"
  - started_at: ISO timestamp
  - stopped_at: ISO timestamp (when ended)
  - status: "active" | "stopped"
  - event_count: integer
  - metadata: JSON string

# Event stream (Redis Streams)
popkit:observe:events:{session_id}
  - Stream entries with XADD
  - Each entry: { type, data, timestamp }
  - TTL: 24 hours (configurable)

# Rate limiting
popkit:ratelimit:{api_key}:{minute}
  - Counter with 60 second TTL
```

#### Upstash Vector Schema

```typescript
// Session embedding
{
  id: "session:20260113-142530-a1b2c3d4",
  vector: [0.123, 0.456, ...], // 1536-dim from Voyage AI
  metadata: {
    workspace_id: "team_abc123",
    user_id: "user@example.com",
    date: "2026-01-13",
    event_count: 234,
    error_count: 5,
    error_rate: 0.021,
    total_tokens: 45000,
    cost_usd: 0.68,
    tools_used: ["Read", "Write", "Bash", "Task"],
    duration_minutes: 45
  }
}
```

---

### Privacy & Anonymization

All events are anonymized before storage using existing `pattern_anonymizer.py` logic:

```typescript
// src/utils/privacy.ts
export function anonymizeEvent(event: any): any {
  const anonymized = { ...event };

  // Redact credentials
  if (anonymized.metadata) {
    anonymized.metadata = redactSensitiveData(anonymized.metadata);
  }

  // Redact file paths
  if (anonymized.file_path) {
    anonymized.file_path = anonymizePath(anonymized.file_path);
  }

  return anonymized;
}

function redactSensitiveData(obj: any): any {
  const str = JSON.stringify(obj);

  // API keys, tokens
  const redacted = str
    .replace(/sk[-_][a-zA-Z0-9]{32,}/g, '[REDACTED_API_KEY]')
    .replace(/pk[-_][a-zA-Z0-9]{32,}/g, '[REDACTED_API_KEY]')
    // Email addresses
    .replace(/[\w\.-]+@[\w\.-]+\.\w+/g, '[REDACTED_EMAIL]')
    // IP addresses
    .replace(/\b(?:\d{1,3}\.){3}\d{1,3}\b/g, '[REDACTED_IP]');

  return JSON.parse(redacted);
}

function anonymizePath(path: string): string {
  return path
    .replace(/C:\\Users\\[^\\]+/, 'C:\\Users\\[USER]')
    .replace(/\/Users\/[^\/]+/, '/Users/[USER]')
    .replace(/\/home\/[^\/]+/, '/home/[USER]');
}
```

---

### Rate Limiting

```typescript
// src/utils/rateLimit.ts
import { Redis } from '@upstash/redis/cloudflare';

export async function checkRateLimit(
  request: Request,
  env: Env
): Promise<{ allowed: boolean; limit_info: any; retry_after?: number }> {
  const apiKey = request.headers.get('Authorization')?.replace('Bearer ', '');
  const tier = getTierFromKey(apiKey);

  const limits = {
    pro: { requests: 100, window: 60 },
    team: { requests: 500, window: 60 },
  };

  const limit = limits[tier];
  const redis = new Redis({
    url: env.UPSTASH_REDIS_REST_URL,
    token: env.UPSTASH_REDIS_REST_TOKEN,
  });

  const minute = Math.floor(Date.now() / 60000);
  const key = `popkit:ratelimit:${apiKey}:${minute}`;

  const current = await redis.incr(key);
  if (current === 1) {
    await redis.expire(key, 60);
  }

  const remaining = Math.max(0, limit.requests - current);
  const resetAt = new Date((minute + 1) * 60000);

  return {
    allowed: current <= limit.requests,
    limit_info: {
      remaining,
      reset_at: resetAt.toISOString(),
      limit: limit.requests,
    },
    retry_after: current > limit.requests ? 60 : undefined,
  };
}
```

---

### Error Handling

**Standard Error Response:**
```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": { /* optional */ },
  "timestamp": "2026-01-13T14:25:30Z"
}
```

**Error Codes:**
- `INVALID_SESSION_ID` (400)
- `SESSION_NOT_FOUND` (404)
- `RATE_LIMIT_EXCEEDED` (429)
- `INVALID_API_KEY` (401)
- `TIER_INSUFFICIENT` (403)
- `INTERNAL_ERROR` (500)

---

### Deployment Configuration

**File:** `packages/popkit-cloud/wrangler.toml` (in ElShaddai repo)

```toml
name = "popkit-observe-api"
main = "src/index.ts"
compatibility_date = "2024-01-01"

[env.production]
route = "api.popkit.ai/observe/*"

[[durable_objects.bindings]]
name = "SSE_BROADCASTER"
class_name = "SSEBroadcaster"

[vars]
ENVIRONMENT = "production"

# Secrets (via wrangler secret put)
# UPSTASH_REDIS_REST_URL
# UPSTASH_REDIS_REST_TOKEN
# UPSTASH_VECTOR_REST_URL
# UPSTASH_VECTOR_REST_TOKEN
# VOYAGE_API_KEY
```

---

### Testing

**Local Development:**
```bash
cd packages/popkit-cloud
npm install
wrangler dev

# Test endpoint
curl -X POST http://localhost:8787/observe/v1/session/start \
  -H "Authorization: Bearer pk_test_abc123" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"20260113-142530-test","mode":"batch"}'
```

**Integration Tests:**
```typescript
// tests/api.test.ts
describe('Observability API', () => {
  test('POST /session/start creates session', async () => {
    const response = await fetch(`${API_BASE}/session/start`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${TEST_API_KEY}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        session_id: '20260113-142530-test',
        mode: 'batch',
      }),
    });

    expect(response.status).toBe(200);
    const data = await response.json();
    expect(data.success).toBe(true);
    expect(data.dashboard_url).toContain(data.session_id);
  });
});
```

---

## Section 5: Dashboard

### Overview

The PopKit Observability Dashboard is a Next.js 14+ application hosted at `observe.popkit.ai` that provides real-time visualization of Claude Code sessions. It integrates with the Cloudflare Workers API via SSE (Server-Sent Events) for live updates and supports three tiers: Free (local HTML reports), Pro (cloud streaming + dashboard), and Team (shared workspace + semantic search).

**Key Features:**
- Real-time session monitoring with SSE
- Interactive tool call timeline
- Cost tracking and token usage visualization
- Agent coordination graph (Power Mode)
- Session replay functionality
- Team workspace with cross-session insights

---

### Architecture

**Tech Stack:**
- **Framework**: Next.js 14 (App Router)
- **UI Library**: React 18
- **Styling**: Tailwind CSS + shadcn/ui components
- **State Management**: Zustand (lightweight, fast)
- **Data Fetching**: SWR for caching, SSE for real-time
- **Charts**: Recharts (built on D3, responsive)
- **Authentication**: NextAuth.js with API key validation

**Project Structure:**
```
packages/popkit-dashboard/
├── src/
│   ├── app/
│   │   ├── layout.tsx           # Root layout
│   │   ├── page.tsx             # Landing page
│   │   ├── session/
│   │   │   └── [id]/
│   │   │       └── page.tsx     # Individual session view
│   │   ├── sessions/
│   │   │   └── page.tsx         # Session history
│   │   └── workspace/
│   │       └── page.tsx         # Team workspace (Team tier)
│   ├── components/
│   │   ├── ui/                  # shadcn/ui components
│   │   ├── session/
│   │   │   ├── SessionTimeline.tsx
│   │   │   ├── ToolCallCard.tsx
│   │   │   ├── CostTracker.tsx
│   │   │   └── AgentGraph.tsx
│   │   ├── workspace/
│   │   │   ├── SessionGrid.tsx
│   │   │   └── SearchBar.tsx
│   │   └── realtime/
│   │       └── SSEProvider.tsx
│   ├── lib/
│   │   ├── api-client.ts        # Cloudflare API wrapper
│   │   ├── sse-client.ts        # SSE connection manager
│   │   └── store.ts             # Zustand store
│   └── types/
│       └── session.ts           # TypeScript types
├── public/
│   └── static assets
├── next.config.js
└── package.json
```

---

### Real-Time Updates (SSE Integration)

**SSE Client Manager:**
```typescript
// src/lib/sse-client.ts
import { useEffect, useRef, useState } from 'react';

export interface SSEClientOptions {
  apiKey: string;
  sessionId: string;
  onConnect?: () => void;
  onEvent?: (event: any) => void;
  onError?: (error: Error) => void;
  reconnectInterval?: number;
}

export function useSSEClient(options: SSEClientOptions) {
  const {
    apiKey,
    sessionId,
    onConnect,
    onEvent,
    onError,
    reconnectInterval = 3000,
  } = options;

  const eventSourceRef = useRef<EventSource | null>(null);
  const [connectionState, setConnectionState] = useState<
    'connecting' | 'connected' | 'disconnected' | 'error'
  >('disconnected');

  useEffect(() => {
    let reconnectTimeout: NodeJS.Timeout;
    let shouldReconnect = true;

    const connect = () => {
      setConnectionState('connecting');

      const url = `https://api.popkit.ai/observe/v1/dashboard/live/${sessionId}`;
      const eventSource = new EventSource(url, {
        withCredentials: true,
      });

      // Add Authorization header via interceptor
      // (EventSource doesn't support custom headers, so we use query param)
      const urlWithAuth = `${url}?key=${apiKey}`;
      const es = new EventSource(urlWithAuth);

      es.addEventListener('connected', () => {
        setConnectionState('connected');
        onConnect?.();
      });

      es.addEventListener('tool_call', (e) => {
        try {
          const data = JSON.parse(e.data);
          onEvent?.(data);
        } catch (err) {
          console.error('Failed to parse SSE event:', err);
        }
      });

      es.addEventListener('session_complete', (e) => {
        try {
          const data = JSON.parse(e.data);
          onEvent?.(data);
          es.close();
          setConnectionState('disconnected');
        } catch (err) {
          console.error('Failed to parse session_complete:', err);
        }
      });

      es.addEventListener('heartbeat', () => {
        // Keep connection alive
      });

      es.onerror = (error) => {
        console.error('SSE error:', error);
        setConnectionState('error');
        onError?.(new Error('SSE connection failed'));
        es.close();

        // Auto-reconnect
        if (shouldReconnect) {
          reconnectTimeout = setTimeout(connect, reconnectInterval);
        }
      };

      eventSourceRef.current = es;
    };

    connect();

    return () => {
      shouldReconnect = false;
      clearTimeout(reconnectTimeout);
      eventSourceRef.current?.close();
    };
  }, [apiKey, sessionId, reconnectInterval]);

  return { connectionState };
}
```

**SSE Provider Component:**
```typescript
// src/components/realtime/SSEProvider.tsx
'use client';

import { createContext, useContext, useEffect, useState } from 'react';
import { useSSEClient } from '@/lib/sse-client';
import { useSessionStore } from '@/lib/store';

interface SSEContextValue {
  isConnected: boolean;
  connectionState: 'connecting' | 'connected' | 'disconnected' | 'error';
}

const SSEContext = createContext<SSEContextValue>({
  isConnected: false,
  connectionState: 'disconnected',
});

export function SSEProvider({
  children,
  sessionId,
  apiKey,
}: {
  children: React.ReactNode;
  sessionId: string;
  apiKey: string;
}) {
  const addEvent = useSessionStore((state) => state.addEvent);
  const updateSession = useSessionStore((state) => state.updateSession);

  const { connectionState } = useSSEClient({
    apiKey,
    sessionId,
    onConnect: () => {
      console.log('SSE connected');
    },
    onEvent: (event) => {
      if (event.type === 'tool_call') {
        addEvent(sessionId, event);
      } else if (event.type === 'session_complete') {
        updateSession(sessionId, { status: 'completed' });
      }
    },
    onError: (error) => {
      console.error('SSE error:', error);
    },
  });

  return (
    <SSEContext.Provider
      value={{
        isConnected: connectionState === 'connected',
        connectionState,
      }}
    >
      {children}
    </SSEContext.Provider>
  );
}

export const useSSE = () => useContext(SSEContext);
```

---

### State Management (Zustand Store)

**Session Store:**
```typescript
// src/lib/store.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface ToolCallEvent {
  tool_use_id: string;
  tool_name: string;
  timestamp: string;
  duration_ms: number;
  tokens_used: number;
  cost_usd: number;
  error?: string;
}

interface Session {
  session_id: string;
  status: 'active' | 'completed';
  started_at: string;
  completed_at?: string;
  events: ToolCallEvent[];
  total_tokens: number;
  total_cost: number;
  error_count: number;
}

interface SessionStore {
  sessions: Record<string, Session>;
  addSession: (session: Session) => void;
  updateSession: (sessionId: string, updates: Partial<Session>) => void;
  addEvent: (sessionId: string, event: ToolCallEvent) => void;
  getSession: (sessionId: string) => Session | undefined;
}

export const useSessionStore = create<SessionStore>()(
  persist(
    (set, get) => ({
      sessions: {},

      addSession: (session) =>
        set((state) => ({
          sessions: {
            ...state.sessions,
            [session.session_id]: session,
          },
        })),

      updateSession: (sessionId, updates) =>
        set((state) => ({
          sessions: {
            ...state.sessions,
            [sessionId]: {
              ...state.sessions[sessionId],
              ...updates,
            },
          },
        })),

      addEvent: (sessionId, event) =>
        set((state) => {
          const session = state.sessions[sessionId];
          if (!session) return state;

          const newEvents = [...session.events, event];
          const totalTokens = newEvents.reduce(
            (sum, e) => sum + e.tokens_used,
            0
          );
          const totalCost = newEvents.reduce((sum, e) => sum + e.cost_usd, 0);
          const errorCount = newEvents.filter((e) => e.error).length;

          return {
            sessions: {
              ...state.sessions,
              [sessionId]: {
                ...session,
                events: newEvents,
                total_tokens: totalTokens,
                total_cost: totalCost,
                error_count: errorCount,
              },
            },
          };
        }),

      getSession: (sessionId) => get().sessions[sessionId],
    }),
    {
      name: 'popkit-observe-sessions',
    }
  )
);
```

---

### UI Components

#### 1. Session Timeline

```typescript
// src/components/session/SessionTimeline.tsx
'use client';

import { useSessionStore } from '@/lib/store';
import { ToolCallCard } from './ToolCallCard';
import { ScrollArea } from '@/components/ui/scroll-area';

export function SessionTimeline({ sessionId }: { sessionId: string }) {
  const session = useSessionStore((state) => state.getSession(sessionId));

  if (!session) {
    return <div>Session not found</div>;
  }

  return (
    <div className="flex flex-col h-full">
      <div className="border-b p-4">
        <h2 className="text-2xl font-bold">Session Timeline</h2>
        <p className="text-sm text-muted-foreground">
          {session.events.length} tool calls • {session.total_tokens.toLocaleString()} tokens • ${session.total_cost.toFixed(4)}
        </p>
      </div>

      <ScrollArea className="flex-1 p-4">
        <div className="space-y-4">
          {session.events.map((event, index) => (
            <ToolCallCard
              key={event.tool_use_id}
              event={event}
              index={index}
              isLatest={index === session.events.length - 1}
            />
          ))}
        </div>
      </ScrollArea>
    </div>
  );
}
```

#### 2. Tool Call Card

```typescript
// src/components/session/ToolCallCard.tsx
'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatDistanceToNow } from 'date-fns';

interface ToolCallCardProps {
  event: {
    tool_use_id: string;
    tool_name: string;
    timestamp: string;
    duration_ms: number;
    tokens_used: number;
    cost_usd: number;
    error?: string;
  };
  index: number;
  isLatest: boolean;
}

export function ToolCallCard({ event, index, isLatest }: ToolCallCardProps) {
  const toolIcons: Record<string, string> = {
    Read: '📖',
    Write: '✍️',
    Edit: '✏️',
    Bash: '🔧',
    Grep: '🔍',
    Task: '🤖',
  };

  return (
    <Card className={isLatest ? 'border-primary' : ''}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-base flex items-center gap-2">
            <span>{toolIcons[event.tool_name] || '🔧'}</span>
            <span>{event.tool_name}</span>
            <Badge variant={event.error ? 'destructive' : 'secondary'}>
              #{index + 1}
            </Badge>
          </CardTitle>
          <span className="text-xs text-muted-foreground">
            {formatDistanceToNow(new Date(event.timestamp), {
              addSuffix: true,
            })}
          </span>
        </div>
      </CardHeader>

      <CardContent className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <div className="flex gap-4">
            <span>⏱️ {event.duration_ms}ms</span>
            <span>🎟️ {event.tokens_used} tokens</span>
            <span>💰 ${event.cost_usd.toFixed(6)}</span>
          </div>
        </div>

        {event.error && (
          <div className="mt-2 p-2 bg-destructive/10 rounded-md">
            <p className="text-sm text-destructive font-mono">{event.error}</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
```

#### 3. Cost Tracker

```typescript
// src/components/session/CostTracker.tsx
'use client';

import { useSessionStore } from '@/lib/store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

export function CostTracker({ sessionId }: { sessionId: string }) {
  const session = useSessionStore((state) => state.getSession(sessionId));

  if (!session) return null;

  // Calculate cumulative cost over time
  const cumulativeData = session.events.reduce(
    (acc, event, index) => {
      const prev = acc[acc.length - 1];
      const cumCost = (prev?.cumulative_cost || 0) + event.cost_usd;
      const cumTokens = (prev?.cumulative_tokens || 0) + event.tokens_used;

      return [
        ...acc,
        {
          index: index + 1,
          cumulative_cost: cumCost,
          cumulative_tokens: cumTokens,
          timestamp: event.timestamp,
        },
      ];
    },
    [] as Array<{
      index: number;
      cumulative_cost: number;
      cumulative_tokens: number;
      timestamp: string;
    }>
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Cost & Token Tracking</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div>
            <p className="text-sm text-muted-foreground">Total Cost</p>
            <p className="text-2xl font-bold">
              ${session.total_cost.toFixed(4)}
            </p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Total Tokens</p>
            <p className="text-2xl font-bold">
              {session.total_tokens.toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-sm text-muted-foreground">Avg Cost/Tool</p>
            <p className="text-2xl font-bold">
              ${(session.total_cost / session.events.length).toFixed(6)}
            </p>
          </div>
        </div>

        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={cumulativeData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="index" label={{ value: 'Tool Call #' }} />
            <YAxis
              yAxisId="left"
              label={{ value: 'Cost ($)', angle: -90, position: 'insideLeft' }}
            />
            <YAxis
              yAxisId="right"
              orientation="right"
              label={{ value: 'Tokens', angle: 90, position: 'insideRight' }}
            />
            <Tooltip />
            <Line
              yAxisId="left"
              type="monotone"
              dataKey="cumulative_cost"
              stroke="#8884d8"
              name="Cost"
            />
            <Line
              yAxisId="right"
              type="monotone"
              dataKey="cumulative_tokens"
              stroke="#82ca9d"
              name="Tokens"
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
```

#### 4. Agent Graph (Power Mode)

```typescript
// src/components/session/AgentGraph.tsx
'use client';

import { useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface AgentGraphProps {
  sessionId: string;
}

export function AgentGraph({ sessionId }: AgentGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Simple agent coordination visualization
    // In production, use D3.js or Cytoscape.js for complex graphs
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw main agent
    ctx.fillStyle = '#8884d8';
    ctx.beginPath();
    ctx.arc(200, 150, 30, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = '#fff';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Main', 200, 155);

    // Draw sub-agents
    const subAgents = [
      { x: 100, y: 80, name: 'Explore' },
      { x: 300, y: 80, name: 'Plan' },
      { x: 100, y: 220, name: 'Review' },
      { x: 300, y: 220, name: 'Test' },
    ];

    subAgents.forEach((agent) => {
      // Draw connection line
      ctx.strokeStyle = '#ccc';
      ctx.beginPath();
      ctx.moveTo(200, 150);
      ctx.lineTo(agent.x, agent.y);
      ctx.stroke();

      // Draw agent node
      ctx.fillStyle = '#82ca9d';
      ctx.beginPath();
      ctx.arc(agent.x, agent.y, 25, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#fff';
      ctx.fillText(agent.name, agent.x, agent.y + 5);
    });
  }, [sessionId]);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Agent Coordination (Power Mode)</CardTitle>
      </CardHeader>
      <CardContent>
        <canvas
          ref={canvasRef}
          width={400}
          height={300}
          className="w-full h-auto border rounded"
        />
        <p className="text-sm text-muted-foreground mt-2">
          Visual representation of multi-agent collaboration during Power Mode sessions.
        </p>
      </CardContent>
    </Card>
  );
}
```

---

### Pages & Routes

#### 1. Individual Session Page

```typescript
// src/app/session/[id]/page.tsx
import { Suspense } from 'react';
import { SessionTimeline } from '@/components/session/SessionTimeline';
import { CostTracker } from '@/components/session/CostTracker';
import { AgentGraph } from '@/components/session/AgentGraph';
import { SSEProvider } from '@/components/realtime/SSEProvider';
import { Skeleton } from '@/components/ui/skeleton';

export default function SessionPage({
  params,
}: {
  params: { id: string };
}) {
  return (
    <SSEProvider sessionId={params.id} apiKey={getApiKey()}>
      <div className="container mx-auto p-6">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2">
            <Suspense fallback={<Skeleton className="h-[600px]" />}>
              <SessionTimeline sessionId={params.id} />
            </Suspense>
          </div>

          <div className="space-y-6">
            <Suspense fallback={<Skeleton className="h-[300px]" />}>
              <CostTracker sessionId={params.id} />
            </Suspense>

            <Suspense fallback={<Skeleton className="h-[300px]" />}>
              <AgentGraph sessionId={params.id} />
            </Suspense>
          </div>
        </div>
      </div>
    </SSEProvider>
  );
}

function getApiKey(): string {
  // In production, fetch from authenticated session
  return process.env.NEXT_PUBLIC_API_KEY || '';
}
```

#### 2. Session History Page

```typescript
// src/app/sessions/page.tsx
'use client';

import { useSessionStore } from '@/lib/store';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatDistanceToNow } from 'date-fns';
import Link from 'next/link';

export default function SessionsPage() {
  const sessions = useSessionStore((state) => Object.values(state.sessions));

  // Sort by most recent first
  const sortedSessions = [...sessions].sort(
    (a, b) =>
      new Date(b.started_at).getTime() - new Date(a.started_at).getTime()
  );

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Session History</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sortedSessions.map((session) => (
          <Link key={session.session_id} href={`/session/${session.session_id}`}>
            <Card className="hover:border-primary transition-colors cursor-pointer">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-base">
                    {session.session_id}
                  </CardTitle>
                  <Badge
                    variant={session.status === 'active' ? 'default' : 'secondary'}
                  >
                    {session.status}
                  </Badge>
                </div>
              </CardHeader>

              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Started</span>
                    <span>
                      {formatDistanceToNow(new Date(session.started_at), {
                        addSuffix: true,
                      })}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Tool Calls</span>
                    <span>{session.events.length}</span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Cost</span>
                    <span>${session.total_cost.toFixed(4)}</span>
                  </div>

                  {session.error_count > 0 && (
                    <div className="flex justify-between text-destructive">
                      <span>Errors</span>
                      <span>{session.error_count}</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      {sortedSessions.length === 0 && (
        <Card>
          <CardContent className="p-12 text-center">
            <p className="text-muted-foreground">
              No sessions yet. Start recording with{' '}
              <code className="bg-muted px-2 py-1 rounded">/popkit-observe:observe start</code>
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
```

#### 3. Team Workspace Page (Team Tier)

```typescript
// src/app/workspace/page.tsx
'use client';

import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Search } from 'lucide-react';

export default function WorkspacePage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);

  const handleSearch = async () => {
    // Call semantic search API
    const response = await fetch('/api/search/query', {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${getApiKey()}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: searchQuery,
        workspace_id: 'team_abc123',
        limit: 20,
      }),
    });

    const data = await response.json();
    setSearchResults(data.results);
  };

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Team Workspace</h1>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Semantic Search</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Input
              placeholder="Search across all team sessions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
            <Button onClick={handleSearch}>
              <Search className="w-4 h-4 mr-2" />
              Search
            </Button>
          </div>
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {searchResults.map((result) => (
          <Card key={result.session_id}>
            <CardHeader>
              <CardTitle className="text-base">
                Session {result.session_id}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Similarity</span>
                  <span>{(result.score * 100).toFixed(1)}%</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">User</span>
                  <span>{result.user_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Tools</span>
                  <span>{result.event_count} calls</span>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}

function getApiKey(): string {
  return process.env.NEXT_PUBLIC_API_KEY || '';
}
```

---

### Responsive Design

**Tailwind Configuration:**
```typescript
// tailwind.config.ts
import type { Config } from 'tailwindcss';

const config: Config = {
  darkMode: ['class'],
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        border: 'hsl(var(--border))',
        input: 'hsl(var(--input))',
        ring: 'hsl(var(--ring))',
        background: 'hsl(var(--background))',
        foreground: 'hsl(var(--foreground))',
        primary: {
          DEFAULT: 'hsl(var(--primary))',
          foreground: 'hsl(var(--primary-foreground))',
        },
        secondary: {
          DEFAULT: 'hsl(var(--secondary))',
          foreground: 'hsl(var(--secondary-foreground))',
        },
        destructive: {
          DEFAULT: 'hsl(var(--destructive))',
          foreground: 'hsl(var(--destructive-foreground))',
        },
        muted: {
          DEFAULT: 'hsl(var(--muted))',
          foreground: 'hsl(var(--muted-foreground))',
        },
        accent: {
          DEFAULT: 'hsl(var(--accent))',
          foreground: 'hsl(var(--accent-foreground))',
        },
        popover: {
          DEFAULT: 'hsl(var(--popover))',
          foreground: 'hsl(var(--popover-foreground))',
        },
        card: {
          DEFAULT: 'hsl(var(--card))',
          foreground: 'hsl(var(--card-foreground))',
        },
      },
      borderRadius: {
        lg: 'var(--radius)',
        md: 'calc(var(--radius) - 2px)',
        sm: 'calc(var(--radius) - 4px)',
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
};

export default config;
```

**Mobile-First Approach:**
- All components use `grid-cols-1` by default
- Breakpoint progression: `md:grid-cols-2 lg:grid-cols-3`
- Touch-friendly interactive elements (min 44px tap targets)
- Collapsible sidebar navigation on mobile
- Responsive charts that adapt to container width

---

### Tier-Specific Features

**Feature Gates:**
```typescript
// src/lib/tier-gate.ts
export type Tier = 'free' | 'pro' | 'team';

export interface TierFeatures {
  cloudSync: boolean;
  realTimeDashboard: boolean;
  semanticSearch: boolean;
  teamWorkspace: boolean;
  sessionReplay: boolean;
  exportData: boolean;
}

export const tierFeatures: Record<Tier, TierFeatures> = {
  free: {
    cloudSync: false,
    realTimeDashboard: false,
    semanticSearch: false,
    teamWorkspace: false,
    sessionReplay: false,
    exportData: true, // Local HTML export
  },
  pro: {
    cloudSync: true,
    realTimeDashboard: true,
    semanticSearch: false,
    teamWorkspace: false,
    sessionReplay: true,
    exportData: true,
  },
  team: {
    cloudSync: true,
    realTimeDashboard: true,
    semanticSearch: true,
    teamWorkspace: true,
    sessionReplay: true,
    exportData: true,
  },
};

export function hasFeature(tier: Tier, feature: keyof TierFeatures): boolean {
  return tierFeatures[tier][feature];
}
```

**Feature Gate Component:**
```typescript
// src/components/TierGate.tsx
'use client';

import { hasFeature, Tier, TierFeatures } from '@/lib/tier-gate';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Lock } from 'lucide-react';

interface TierGateProps {
  feature: keyof TierFeatures;
  userTier: Tier;
  children: React.ReactNode;
}

export function TierGate({ feature, userTier, children }: TierGateProps) {
  if (hasFeature(userTier, feature)) {
    return <>{children}</>;
  }

  return (
    <Card className="border-dashed">
      <CardContent className="p-12 text-center space-y-4">
        <Lock className="w-12 h-12 mx-auto text-muted-foreground" />
        <div>
          <h3 className="text-xl font-semibold mb-2">
            {getFeatureName(feature)} (Pro/Team)
          </h3>
          <p className="text-muted-foreground mb-4">
            Upgrade to unlock {getFeatureName(feature).toLowerCase()} and more advanced features.
          </p>
          <Button asChild>
            <a href="/upgrade">Upgrade Now</a>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function getFeatureName(feature: keyof TierFeatures): string {
  const names: Record<keyof TierFeatures, string> = {
    cloudSync: 'Cloud Sync',
    realTimeDashboard: 'Real-Time Dashboard',
    semanticSearch: 'Semantic Search',
    teamWorkspace: 'Team Workspace',
    sessionReplay: 'Session Replay',
    exportData: 'Data Export',
  };
  return names[feature];
}
```

**Usage Example:**
```typescript
// In a page or component
<TierGate feature="semanticSearch" userTier={userTier}>
  <SearchBar />
</TierGate>
```

---

### Deployment

**Environment Variables:**
```bash
# .env.production
NEXT_PUBLIC_API_BASE_URL=https://api.popkit.ai/observe/v1
NEXT_PUBLIC_DASHBOARD_URL=https://observe.popkit.ai
NEXTAUTH_URL=https://observe.popkit.ai
NEXTAUTH_SECRET=your-secret-key
```

**Next.js Configuration:**
```typescript
// next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'standalone', // Optimized for Cloudflare Pages
  images: {
    unoptimized: true, // Cloudflare Images handles optimization
  },
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL,
  },
};

module.exports = nextConfig;
```

**Build & Deploy (Cloudflare Pages):**
```bash
# Build
npm run build

# Deploy to Cloudflare Pages
npx wrangler pages deploy .next/standalone --project-name=popkit-observe-dashboard

# Preview deployment
npx wrangler pages dev .next/standalone
```

**Continuous Deployment:**
```yaml
# .github/workflows/deploy-dashboard.yml
name: Deploy Dashboard

on:
  push:
    branches: [main]
    paths:
      - 'packages/popkit-dashboard/**'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18

      - name: Install dependencies
        run: |
          cd packages/popkit-dashboard
          npm ci

      - name: Build
        run: |
          cd packages/popkit-dashboard
          npm run build

      - name: Deploy to Cloudflare Pages
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          command: pages deploy .next/standalone --project-name=popkit-observe-dashboard
```

---

### Performance Optimizations

**1. React Server Components:**
- Use RSC for static content (session history, workspace data)
- Client components only for interactive features (SSE, charts)

**2. Data Caching with SWR:**
```typescript
// src/lib/api-client.ts
import useSWR from 'swr';

export function useSession(sessionId: string) {
  const { data, error, isLoading } = useSWR(
    `/api/session/${sessionId}`,
    fetcher,
    {
      refreshInterval: 0, // Don't poll, rely on SSE
      revalidateOnFocus: false,
    }
  );

  return { session: data, error, isLoading };
}
```

**3. Virtualized Lists:**
For sessions with 1000+ tool calls, use `react-window`:
```typescript
import { FixedSizeList } from 'react-window';

<FixedSizeList
  height={600}
  itemCount={session.events.length}
  itemSize={120}
  width="100%"
>
  {({ index, style }) => (
    <div style={style}>
      <ToolCallCard event={session.events[index]} index={index} />
    </div>
  )}
</FixedSizeList>
```

**4. Image Optimization:**
- Use Next.js `<Image>` component for logos/avatars
- Lazy load charts with `loading="lazy"`

---

### Testing

**Unit Tests (Vitest):**
```typescript
// src/components/session/__tests__/ToolCallCard.test.tsx
import { render, screen } from '@testing-library/react';
import { ToolCallCard } from '../ToolCallCard';

describe('ToolCallCard', () => {
  const mockEvent = {
    tool_use_id: 'test-123',
    tool_name: 'Read',
    timestamp: new Date().toISOString(),
    duration_ms: 150,
    tokens_used: 500,
    cost_usd: 0.001,
  };

  it('renders tool name and metrics', () => {
    render(<ToolCallCard event={mockEvent} index={0} isLatest={false} />);

    expect(screen.getByText('Read')).toBeInTheDocument();
    expect(screen.getByText('150ms')).toBeInTheDocument();
    expect(screen.getByText('500 tokens')).toBeInTheDocument();
  });

  it('highlights latest tool call', () => {
    const { container } = render(
      <ToolCallCard event={mockEvent} index={0} isLatest={true} />
    );

    expect(container.firstChild).toHaveClass('border-primary');
  });
});
```

**Integration Tests (Playwright):**
```typescript
// tests/e2e/session-view.spec.ts
import { test, expect } from '@playwright/test';

test('session page displays real-time updates', async ({ page }) => {
  await page.goto('/session/20260113-142530-test');

  // Wait for SSE connection
  await expect(page.locator('[data-testid="sse-status"]')).toHaveText(
    'Connected'
  );

  // Verify initial tool calls loaded
  const toolCards = page.locator('[data-testid="tool-call-card"]');
  await expect(toolCards).toHaveCount(10);

  // Wait for new tool call to appear via SSE
  await expect(toolCards).toHaveCount(11, { timeout: 5000 });
});
```

---

### Summary

Section 5 defines a comprehensive Next.js dashboard with:

✅ **Real-time updates** via SSE (no WebSocket complexity)
✅ **State management** with Zustand (lightweight, persistent)
✅ **UI components** for timeline, cost tracking, agent graphs
✅ **Three main pages**: Session view, history, team workspace
✅ **Responsive design** with Tailwind CSS and shadcn/ui
✅ **Tier gates** for Free/Pro/Team feature differentiation
✅ **Performance optimizations** (RSC, SWR, virtualization)
✅ **Testing strategy** (Vitest for units, Playwright for E2E)
✅ **Cloudflare Pages deployment** with CI/CD

**Next: Section 6 - Migration & Implementation Roadmap**

---

## Section 6: Migration & Implementation Roadmap

### Overview

This section outlines the phased migration from the existing `/popkit-core:record` system to the new `/popkit-observe:observe` architecture. The migration prioritizes backwards compatibility, minimal disruption, and incremental value delivery.

**Migration Goals:**
1. ✅ Preserve existing recording functionality during transition
2. ✅ Enable Pro/Team users to adopt cloud features incrementally
3. ✅ Maintain Free tier local HTML reports
4. ✅ Zero breaking changes to existing workflows

---

### Current State Analysis

**Existing Components:**
```
packages/popkit-core/
├── commands/record.md           # /popkit-core:record command
├── hooks/
│   ├── pre-tool-use.py          # Hook fired before tool execution
│   ├── post-tool-use.py         # Hook fired after tool execution
│   └── subagent-stop.py         # Hook fired when subagent stops (line 195 TODO)
└── ...

packages/shared-py/popkit_shared/utils/
├── session_recorder.py          # Local recording to JSON
├── transcript_parser.py         # JSONL parsing (complete, not integrated)
├── privacy.py                   # Privacy settings and consent
├── pattern_anonymizer.py        # Credential/PII redaction
└── ...
```

**Key Findings:**
1. ✅ **transcript_parser.py** exists and is complete with tests
2. ❌ **Not yet integrated** into `subagent-stop.py:195` (Issue #110 scope)
3. ✅ **session_recorder.py** handles local recording
4. ✅ **Privacy infrastructure** already in place
5. ⚠️ **No cloud streaming** currently implemented

---

### Migration Strategy

**Approach: Parallel Systems with Gradual Cutover**

```
Phase 1: Foundation (Issue #110)
├─ Integrate transcript_parser.py into subagent-stop.py
├─ Extract tool calls, reasoning, token usage
└─ Store in local recording.json (no behavior change)

Phase 2: New Plugin (popkit-observe)
├─ Create popkit-observe plugin structure
├─ Implement /popkit-observe:observe command
├─ Add observability_client.py with streaming logic
└─ Keep /popkit-core:record as fallback (deprecated)

Phase 3: Cloudflare Workers API
├─ Deploy API endpoints (Section 4)
├─ Configure Upstash Redis + Vector
├─ Test with internal Pro tier accounts
└─ Enable opt-in beta for Pro users

Phase 4: Dashboard Launch
├─ Deploy Next.js dashboard (Section 5)
├─ SSE live updates functional
├─ Cost tracking and visualization live
└─ Public beta for Pro/Team tiers

Phase 5: Deprecation & Cleanup
├─ Deprecate /popkit-core:record (redirect to observe)
├─ Remove legacy recording code after 6 months
├─ Migrate existing HTML reports to cloud (optional)
└─ Document migration path in CHANGELOG.md
```

---

### Phase 1: Foundation (Issue #110)

**Objective:** Integrate `transcript_parser.py` into `subagent-stop.py` to extract structured data from Power Mode transcripts.

**Scope:**
- File: `packages/popkit-core/hooks/subagent-stop.py:195`
- Status: Complete parsing logic exists, just needs integration
- Impact: Zero user-facing changes (internal enhancement)

**Implementation:**

```python
# packages/popkit-core/hooks/subagent-stop.py (line 195)

# Before (current TODO):
# TODO(#687): Parse transcript_path and extract individual tool calls
# For now, just record that the sub-agent completed

# After (Issue #110 implementation):
from popkit_shared.utils.transcript_parser import TranscriptParser

def parse_and_record_transcript(transcript_path: str, subagent_id: str):
    """Parse Power Mode transcript and extract tool call details."""
    try:
        parser = TranscriptParser(transcript_path)

        # Extract all tool uses
        tool_uses = parser.get_all_tool_uses()

        # Calculate token usage
        token_usage = parser.get_total_token_usage()

        # Record structured data to session_recorder
        from popkit_shared.utils.session_recorder import record_subagent_completion

        record_subagent_completion(
            subagent_id=subagent_id,
            tool_count=len(tool_uses),
            input_tokens=token_usage.input_tokens,
            output_tokens=token_usage.output_tokens,
            total_tokens=token_usage.total_tokens,
            tool_details=tool_uses[:10]  # Store first 10 for summary
        )

    except Exception as e:
        print(f"[WARN] Failed to parse transcript: {e}", file=sys.stderr)
        # Don't fail the hook - gracefully degrade
```

**Testing:**
```bash
# Run existing transcript_parser tests
cd packages/shared-py
pytest tests/test_transcript_parser.py -v

# Integration test with Power Mode
cd packages/popkit-core
/popkit-core:power start
# ... run some work with subagents ...
/popkit-core:power stop

# Verify recording.json contains tool_count and token_usage
cat ~/.claude/popkit/recording.json | jq '.subagents[0]'
```

**Success Criteria:**
- ✅ `subagent-stop.py` parses JSONL transcripts successfully
- ✅ Tool count and token usage recorded in `recording.json`
- ✅ No errors in hook execution
- ✅ Existing recording functionality unchanged

**Timeline:** 1-2 days (primarily testing and integration)

---

### Phase 2: New Plugin (popkit-observe)

**Objective:** Create `popkit-observe` plugin with cloud-ready command structure.

**File Structure:**
```
packages/popkit-observe/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   └── observe.md                    # /popkit-observe:observe command
├── hooks/
│   ├── streaming-hook.py             # Real-time streaming logic
│   └── session-sync.py               # Batch sync after session
├── scripts/
│   └── generate-html-report.py       # Migrated from popkit-core
└── README.md
```

**Plugin Manifest:**
```json
{
  "name": "popkit-observe",
  "version": "1.0.0-beta.1",
  "description": "Real-time observability for Claude Code sessions with cloud streaming, cost tracking, and team collaboration",
  "author": {
    "name": "Joseph Cannon",
    "email": "joseph@thehouseofdeals.com"
  },
  "license": "MIT",
  "repository": "https://github.com/jrc1883/popkit-claude",
  "min_claude_version": "2.1.0",
  "dependencies": ["popkit-core"],
  "tier": "core"
}
```

**Command Implementation:**
Copy from Section 3 (`observe.md`), but add deprecation notice for `/popkit-core:record`:

```markdown
---
description: "start | stop | status | dashboard | sync - Real-time session observability"
argument-hint: "<subcommand> [mode]"
---

# /popkit-observe:observe

**Supersedes:** `/popkit-core:record` (deprecated as of v1.1.0)

Real-time observability for Claude Code sessions. Stream tool calls, track costs, and visualize agent coordination with optional cloud dashboard.

## Migration from /popkit-core:record

If you were using `/popkit-core:record`, the migration is seamless:

**Before (deprecated):**
```bash
/popkit-core:record start
# ... work ...
/popkit-core:record stop
```

**After (new):**
```bash
/popkit-observe:observe start
# ... work ...
/popkit-observe:observe stop
```

**What's Different:**
- ✅ Same local HTML reports (Free tier)
- ✅ NEW: Real-time cloud streaming (Pro/Team tier)
- ✅ NEW: Cost tracking and visualization
- ✅ NEW: Team workspace and semantic search

[Rest of command documentation from Section 3...]
```

**Backwards Compatibility:**

Option 1: **Redirect Command** (add to `popkit-core/commands/record.md`):
```markdown
---
description: "[DEPRECATED] Use /popkit-observe:observe instead"
argument-hint: "<subcommand>"
deprecated: true
redirect: "popkit-observe:observe"
---

# /popkit-core:record [DEPRECATED]

⚠️ **This command is deprecated.** Please use `/popkit-observe:observe` instead.

**Automatic Migration:**
All `/popkit-core:record` commands now redirect to `/popkit-observe:observe` with the same arguments.

**Why the change?**
- Observability now has its own dedicated plugin
- Enhanced features require separate namespace
- Better separation of concerns

**Timeline:**
- v1.1.0: Deprecation notice added (you are here)
- v1.4.0: Command removed (ETA: 6 months)

[Show migration instructions...]
```

Option 2: **Hook-Based Redirect** (add to `popkit-core/hooks/command-intercept.py`):
```python
# Intercept /popkit-core:record and redirect to /popkit-observe:observe
import sys
import json

def intercept_deprecated_command(command: str):
    if command.startswith("/popkit-core:record"):
        # Extract subcommand
        parts = command.split()
        subcommand = parts[1] if len(parts) > 1 else "status"

        # Show deprecation warning
        print("⚠️  /popkit-core:record is deprecated. Use /popkit-observe:observe instead.")
        print(f"Redirecting to: /popkit-observe:observe {subcommand}")

        # Invoke new command
        # (Claude Code will handle the actual invocation)
        return {
            "redirect": f"/popkit-observe:observe {subcommand}",
            "deprecated": True
        }
```

**Shared Utilities:**

Update `shared-py` with new observability client:
```
packages/shared-py/popkit_shared/utils/
├── observability_client.py       # NEW - Cloud streaming client
├── session_recorder.py           # EXISTING - Keep for Free tier
├── transcript_parser.py          # EXISTING - Used by both
└── ...
```

**Testing:**
```bash
# Install new plugin
/plugin install ./packages/popkit-observe

# Test basic recording (Free tier)
/popkit-observe:observe start
# ... work ...
/popkit-observe:observe stop

# Verify HTML report generated
open ~/.claude/popkit/reports/recording-*.html

# Test cloud streaming (Pro tier, requires API key)
export POPKIT_API_KEY="pk_test_abc123"
/popkit-observe:observe start --mode realtime
# Verify dashboard URL printed

# Test deprecation redirect
/popkit-core:record start
# Should see deprecation warning and redirect
```

**Success Criteria:**
- ✅ New plugin installs without errors
- ✅ `/popkit-observe:observe start/stop` functional
- ✅ Free tier HTML reports still work
- ✅ `/popkit-core:record` shows deprecation notice
- ✅ No breaking changes to existing workflows

**Timeline:** 1-2 weeks (plugin structure, command implementation, testing)

---

### Phase 3: Cloudflare Workers API

**Objective:** Deploy cloud API from Section 4 and enable Pro tier streaming.

**Infrastructure Setup:**

1. **Upstash Redis:**
```bash
# Create Upstash Redis database
# Via Upstash dashboard: https://console.upstash.com

# Get credentials:
UPSTASH_REDIS_REST_URL=https://popkit-observe.upstash.io
UPSTASH_REDIS_REST_TOKEN=AY...
```

2. **Upstash Vector (Team tier):**
```bash
# Create Upstash Vector index
# Dimension: 1536 (Voyage AI embeddings)
# Metric: cosine

UPSTASH_VECTOR_REST_URL=https://popkit-vector.upstash.io
UPSTASH_VECTOR_REST_TOKEN=AY...
```

3. **Cloudflare Workers:**
```bash
cd packages/popkit-cloud/workers
npm install

# Configure secrets
npx wrangler secret put UPSTASH_REDIS_REST_URL
npx wrangler secret put UPSTASH_REDIS_REST_TOKEN
npx wrangler secret put UPSTASH_VECTOR_REST_URL
npx wrangler secret put UPSTASH_VECTOR_REST_TOKEN

# Deploy
npx wrangler deploy
# Output: https://api.popkit.ai/observe/v1
```

**API Key Generation:**

```python
# packages/shared-py/popkit_shared/utils/premium_client.py

def generate_api_key(tier: str, user_id: str) -> str:
    """Generate API key for Pro/Team tier."""
    import secrets
    import hashlib

    prefix = "pk_live" if tier == "team" else "pk_pro"
    random_part = secrets.token_urlsafe(24)

    # Store in Upstash Redis:
    # Key: popkit:api_keys:{key_hash}
    # Value: {"tier": tier, "user_id": user_id, "created_at": ...}

    return f"{prefix}_{random_part}"
```

**Client Integration:**

Update `observability_client.py` to use Cloudflare API:
```python
# packages/shared-py/popkit_shared/utils/observability_client.py

import requests
from typing import Optional

class ObservabilityClient:
    def __init__(self, api_key: Optional[str] = None, mode: str = "batch"):
        self.api_key = api_key or os.getenv("POPKIT_API_KEY")
        self.api_base = "https://api.popkit.ai/observe/v1"
        self.mode = mode

    def start_session(self, session_id: str):
        """Initialize cloud session."""
        response = requests.post(
            f"{self.api_base}/session/start",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"session_id": session_id, "mode": self.mode}
        )
        return response.json()

    def stream_event(self, session_id: str, event: dict):
        """Stream single event to cloud."""
        response = requests.post(
            f"{self.api_base}/session/stream",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"session_id": session_id, "events": [event]}
        )
        return response.json()
```

**Testing:**

```bash
# Generate test API key
python -c "from popkit_shared.utils.premium_client import generate_api_key; print(generate_api_key('pro', 'test@example.com'))"

# Test API endpoints
export POPKIT_API_KEY="pk_test_abc123"

# Start session
curl -X POST https://api.popkit.ai/observe/v1/session/start \
  -H "Authorization: Bearer $POPKIT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"session_id":"20260113-142530-test","mode":"batch"}'

# Stream event
curl -X POST https://api.popkit.ai/observe/v1/session/stream \
  -H "Authorization: Bearer $POPKIT_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id":"20260113-142530-test",
    "events":[{
      "tool_use_id":"test-123",
      "tool_name":"Read",
      "timestamp":"2026-01-13T14:25:30Z",
      "duration_ms":150,
      "tokens_used":500,
      "cost_usd":0.001
    }]
  }'

# Verify in Upstash Redis
redis-cli -u $UPSTASH_REDIS_REST_URL
> HGETALL popkit:observe:session:20260113-142530-test
> XRANGE popkit:observe:events:20260113-142530-test - +
```

**Success Criteria:**
- ✅ Cloudflare Workers API deployed and responding
- ✅ Upstash Redis storing session data
- ✅ Rate limiting functional (Pro: 100 req/min, Team: 500 req/min)
- ✅ Privacy/anonymization working
- ✅ Python client can stream events
- ✅ SSE endpoint returns events

**Timeline:** 2-3 weeks (infrastructure setup, deployment, testing, security audit)

---

### Phase 4: Dashboard Launch

**Objective:** Deploy Next.js dashboard from Section 5 and enable Pro/Team users.

**Dashboard Deployment:**

```bash
cd packages/popkit-dashboard
npm install

# Configure environment
cat > .env.production <<EOF
NEXT_PUBLIC_API_BASE_URL=https://api.popkit.ai/observe/v1
NEXT_PUBLIC_DASHBOARD_URL=https://observe.popkit.ai
NEXTAUTH_URL=https://observe.popkit.ai
NEXTAUTH_SECRET=$(openssl rand -base64 32)
EOF

# Build
npm run build

# Deploy to Cloudflare Pages
npx wrangler pages deploy .next/standalone --project-name=popkit-observe-dashboard
# Output: https://observe.popkit.ai
```

**Authentication Setup:**

```typescript
// src/app/api/auth/[...nextauth]/route.ts
import NextAuth from 'next-auth';
import CredentialsProvider from 'next-auth/providers/credentials';

export const authOptions = {
  providers: [
    CredentialsProvider({
      name: 'API Key',
      credentials: {
        apiKey: { label: 'API Key', type: 'password' },
      },
      async authorize(credentials) {
        // Validate API key against Upstash Redis
        const response = await fetch(
          'https://api.popkit.ai/observe/v1/auth/verify',
          {
            headers: { Authorization: `Bearer ${credentials?.apiKey}` },
          }
        );

        if (response.ok) {
          const user = await response.json();
          return user; // { id, tier, email }
        }
        return null;
      },
    }),
  ],
  callbacks: {
    async session({ session, token }) {
      session.user.tier = token.tier;
      return session;
    },
  },
};

const handler = NextAuth(authOptions);
export { handler as GET, handler as POST };
```

**Testing:**

```bash
# Local development
cd packages/popkit-dashboard
npm run dev
# Open: http://localhost:3000

# Test authentication
# Enter API key: pk_test_abc123
# Should redirect to /sessions

# Test real-time updates
# In separate terminal:
/popkit-observe:observe start --mode realtime
# Dashboard should show live updates via SSE

# Test session history
# Navigate to /sessions
# Should see all previous sessions

# Test team workspace (Team tier only)
# Navigate to /workspace
# Search: "authentication bug"
# Should return semantically similar sessions
```

**Monitoring:**

```yaml
# packages/popkit-dashboard/sentry.client.config.ts
import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  tracesSampleRate: 0.1,
  environment: process.env.NODE_ENV,
});
```

**Success Criteria:**
- ✅ Dashboard deployed at observe.popkit.ai
- ✅ Authentication via API key functional
- ✅ SSE live updates working
- ✅ Session timeline displays correctly
- ✅ Cost tracking charts render
- ✅ Team workspace search functional (Team tier)
- ✅ Mobile responsive layout works
- ✅ Error monitoring configured

**Timeline:** 2-3 weeks (dashboard deployment, authentication, testing, UX polish)

---

### Phase 5: Deprecation & Cleanup

**Objective:** Remove legacy `/popkit-core:record` after 6-month deprecation period.

**Deprecation Timeline:**

| Date | Version | Action |
|------|---------|--------|
| 2026-01-20 | v1.1.0 | Deprecation notice added to `/popkit-core:record` |
| 2026-03-01 | v1.2.0 | Warning shown on every use |
| 2026-05-01 | v1.3.0 | Error shown, command no longer functional |
| 2026-07-01 | v1.4.0 | Command removed entirely |

**Migration Notifications:**

```python
# packages/popkit-core/commands/record.md (v1.1.0)

def show_deprecation_notice(phase: int):
    if phase == 1:  # v1.1.0 - Soft deprecation
        print("ℹ️  /popkit-core:record is deprecated. Use /popkit-observe:observe instead.")
        print("Migration guide: https://popkit.ai/docs/migration")

    elif phase == 2:  # v1.2.0 - Warning
        print("⚠️  WARNING: /popkit-core:record will be removed in v1.4.0 (July 2026)")
        print("Migrate to /popkit-observe:observe now.")
        print("Run: /popkit-observe:observe --help")

    elif phase == 3:  # v1.3.0 - Error
        print("❌ ERROR: /popkit-core:record has been removed.")
        print("Use /popkit-observe:observe instead.")
        print("Migration guide: https://popkit.ai/docs/migration")
        return False  # Block execution

    return True  # Allow execution
```

**Data Migration (Optional):**

For users with existing local HTML reports:
```python
# packages/popkit-observe/scripts/migrate-reports.py

def migrate_legacy_reports():
    """Migrate old recording-*.html reports to new observe-*.html format."""
    from pathlib import Path
    import shutil

    old_reports = Path.home() / '.claude' / 'popkit' / 'reports'
    new_reports = Path.home() / '.claude' / 'popkit' / 'observe' / 'reports'

    new_reports.mkdir(parents=True, exist_ok=True)

    for old_report in old_reports.glob('recording-*.html'):
        # Rename recording-* to observe-*
        new_name = old_report.name.replace('recording-', 'observe-')
        new_path = new_reports / new_name

        shutil.copy2(old_report, new_path)
        print(f"Migrated: {old_report.name} → {new_name}")
```

**Cleanup:**

```bash
# v1.4.0 - Remove legacy files
rm packages/popkit-core/commands/record.md
rm packages/popkit-core/hooks/recording-*.py

# Update dependencies
# No plugin should depend on /popkit-core:record anymore
```

**Documentation Updates:**

```markdown
# CHANGELOG.md

## v1.4.0 (2026-07-01)

### Breaking Changes
- **REMOVED:** `/popkit-core:record` command (deprecated since v1.1.0)
- **Migration:** Use `/popkit-observe:observe` instead
- **Impact:** No impact if you migrated to `popkit-observe` plugin

### Migration Guide
See: https://popkit.ai/docs/migration-guide

## v1.1.0 (2026-01-20)

### Deprecated
- `/popkit-core:record` - Use `/popkit-observe:observe` instead
- Automatic redirect added, no immediate action required

### Added
- **NEW PLUGIN:** `popkit-observe` - Real-time observability
- Cloud streaming for Pro/Team tiers
- Cost tracking and visualization
- Team workspace with semantic search
```

**Success Criteria:**
- ✅ 90%+ users migrated before hard removal
- ✅ No user complaints about unexpected breakage
- ✅ Documentation updated across all channels
- ✅ Legacy code removed cleanly
- ✅ No regressions in new system

**Timeline:** 6 months deprecation period + 1 week cleanup

---

### Rollback Plan

**If Phase 3 or 4 fails catastrophically:**

```bash
# Emergency rollback procedure

# 1. Disable cloud API
npx wrangler workers delete popkit-observe-api

# 2. Revert plugin changes
git revert <commit-hash>
/plugin uninstall popkit-observe

# 3. Re-enable /popkit-core:record
git checkout main -- packages/popkit-core/commands/record.md

# 4. Notify users
echo "⚠️  Cloud observability temporarily disabled. Local recording still functional."

# 5. Root cause analysis
# - Check Upstash Redis logs
# - Review Cloudflare Workers errors
# - Investigate SSE connection issues

# 6. Fix and re-deploy
# - Address root cause
# - Test in staging environment
# - Gradual rollout (10% → 50% → 100%)
```

---

### Success Metrics

**Technical Metrics:**
- API uptime: >99.9%
- SSE connection success rate: >98%
- Average latency: <100ms (session/stream)
- Dashboard page load: <2s (75th percentile)

**User Metrics:**
- Migration rate: >90% within 3 months
- Cloud adoption (Pro tier): >60%
- Error rate: <0.1%
- Support tickets: <10/week

**Business Metrics:**
- Pro tier conversion: Track uplift from observability
- Team tier adoption: Monitor workspace usage
- Cost savings: Measure efficiency gains from cost tracking

---

### Risk Mitigation

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| API downtime | High | Low | Offline queue, graceful fallback to local |
| SSE connection failures | Medium | Medium | Auto-reconnect, poll fallback |
| Privacy concerns | High | Low | Clear consent flow, anonymization by default |
| Performance degradation | Medium | Medium | Adaptive batching, smart mode |
| Migration friction | Low | High | Automatic redirect, extensive docs |
| Data loss | High | Very Low | Redundant storage, regular backups |

---

### Summary

**Complete Migration Path:**
1. ✅ **Phase 1 (1-2 days):** Integrate transcript parsing (Issue #110)
2. ✅ **Phase 2 (1-2 weeks):** Create popkit-observe plugin
3. ✅ **Phase 3 (2-3 weeks):** Deploy Cloudflare Workers API
4. ✅ **Phase 4 (2-3 weeks):** Launch Next.js dashboard
5. ✅ **Phase 5 (6 months):** Deprecate legacy /popkit-core:record

**Total Timeline:** ~2 months development + 6 months deprecation = 8 months

**Key Principles:**
- ✅ Zero breaking changes during migration
- ✅ Backwards compatibility maintained
- ✅ Gradual rollout with feature flags
- ✅ Free tier functionality preserved
- ✅ Clear communication at every step

---

---

## Open Questions

1. **Commands/Skills Merge (2.1.14)**: User mentioned January 12, 2026 release merged commands and skills. Design implications?
   - **Answer:** Claude Code 2.1.14 merged the distinction between commands and skills, allowing skills to be invoked like commands. This design uses both:
     - `/popkit-observe:observe` remains a command (not a skill) since it has subcommands
     - The implementation can optionally create a `pop-observe` skill for programmatic invocation
     - No major design changes needed - the command structure is compatible

2. **OPTIMUS Harvest**: Which UI patterns from OPTIMUS worth keeping? WebSocket engine? Agent viz?
   - **Decision:** Started fresh instead of harvesting OPTIMUS code (user choice: "Start fresh")
   - **Rationale:** Clean architecture, no legacy baggage, SSE simpler than WebSocket
   - **Agent Viz:** Simple canvas-based visualization in Section 5, can enhance with D3.js/Cytoscape later

3. **Voyage Embeddings**: User mentioned embeddings service for privacy - investigate Voyage vs Upstash Vector
   - **Answer:** Use **Upstash Vector** with **Voyage AI embeddings**:
     - Voyage AI: Generate 1536-dim embeddings from session metadata
     - Upstash Vector: Store embeddings with cosine similarity search
     - Privacy: Only store anonymized metadata, not raw tool inputs/outputs
   - **Alternative:** Could use Upstash Vector's built-in embedding if Voyage not needed

4. **Tier Gates**: How to gracefully upgrade Free → Pro? In-dashboard prompts? CLI upgrade flow?
   - **Answer:** Multi-touch upgrade flow:
     - **CLI Notice:** When cloud features attempted on Free tier: "Upgrade to Pro for cloud streaming"
     - **Dashboard Tier Gates:** Show locked features with upgrade CTA (Section 5)
     - **Email Campaigns:** Trigger upgrade emails after 3+ sessions (outside this design)
     - **Trial Period:** First 7 days of Pro features free for all users (soft conversion)

---

## Implementation Roadmap

**See Section 6 for complete phase-by-phase implementation plan.**

**Quick Reference:**
- **Phase 1 (1-2 days):** Issue #110 - Integrate transcript parsing
- **Phase 2 (1-2 weeks):** Create popkit-observe plugin
- **Phase 3 (2-3 weeks):** Deploy Cloudflare Workers API
- **Phase 4 (2-3 weeks):** Launch Next.js dashboard
- **Phase 5 (6 months):** Deprecate /popkit-core:record

**Total Timeline:** ~2 months development + 6 months deprecation = 8 months

---

## Design Document Summary

This comprehensive design document covers the complete PopKit Observability Platform architecture:

### What Was Designed

**6 Complete Sections:**

1. **Overview & Vision** (Section 1)
   - High-level architecture and data flow
   - Three-tier model (Free, Pro, Team)
   - Key components and integration points

2. **Plugin Architecture** (Section 2)
   - New `popkit-observe` plugin structure
   - Adaptive streaming strategy (realtime/batch/smart)
   - Privacy-first approach with existing infrastructure

3. **Command Structure** (Section 3)
   - `/popkit-observe:observe` command with 5 subcommands
   - Complete Python implementation for each subcommand
   - Tier-specific behavior and feature gates
   - Examples for Free, Pro, and Team tiers

4. **Cloudflare Workers API** (Section 4)
   - 8 RESTful endpoints with full TypeScript implementations
   - Authentication, rate limiting, SSE broadcasting
   - Upstash Redis + Vector integration
   - Privacy/anonymization in TypeScript

5. **Dashboard (Next.js UI)** (Section 5)
   - Complete Next.js 14 app with SSE real-time updates
   - Zustand state management
   - UI components: Timeline, Cost Tracker, Agent Graph
   - Three main pages: Session view, History, Team workspace
   - Tailwind CSS + shadcn/ui responsive design
   - Tier gates and feature differentiation
   - Testing strategy (Vitest + Playwright)

6. **Migration & Implementation Roadmap** (Section 6)
   - 5-phase migration plan from /popkit-core:record
   - Issue #110 as foundation (Phase 1)
   - New plugin creation (Phase 2)
   - Cloud API deployment (Phase 3)
   - Dashboard launch (Phase 4)
   - Legacy deprecation (Phase 5)
   - Rollback plan and success metrics

### Key Design Decisions

✅ **Architecture:**
- Cloud-native with Cloudflare Workers + Upstash
- SSE (not WebSocket) for real-time updates
- Adaptive streaming with three modes (realtime/batch/smart)
- Offline queue for resilience

✅ **Monetization:**
- Free: Local HTML reports (no cloud)
- Pro: Cloud streaming + dashboard + cost tracking
- Team: + Shared workspace + semantic search

✅ **Privacy:**
- Consent-based opt-in for cloud features
- Three anonymization levels (strict/moderate/minimal)
- Existing privacy infrastructure reused

✅ **Migration:**
- Zero breaking changes
- Backwards compatibility via redirects
- 6-month deprecation period
- Gradual rollout with feature flags

### What's Ready to Implement

**This design document provides:**
- ✅ Complete file structures
- ✅ Full code implementations (Python + TypeScript)
- ✅ API endpoint specifications
- ✅ Database schemas (Redis + Vector)
- ✅ UI component implementations (React/Next.js)
- ✅ Testing strategies
- ✅ Deployment configurations
- ✅ Migration paths
- ✅ Success criteria for each phase

**Next Steps:**
1. **Review & Approve:** User reviews complete design
2. **Create Implementation Plan:** Use `/popkit:dev plan` to generate detailed task breakdown
3. **Phase 1 Start:** Integrate transcript parsing (Issue #110) - 1-2 days
4. **Iterate:** Build, test, and refine each phase

**Design Philosophy:**
- ✅ **DRY:** Reuse existing utilities (transcript_parser, privacy, session_recorder)
- ✅ **YAGNI:** Only build what's needed for three tiers (no over-engineering)
- ✅ **TDD:** Tests defined for all phases
- ✅ **PopKit Way:** Backwards compatible, careful, thorough

---

## Document Metadata

**Created:** 2026-01-13
**Author:** Claude Sonnet 4.5 (via brainstorming + writing-plans skills)
**Status:** Complete (all 6 sections)
**Total Length:** 3,600+ lines
**Related Issue:** #110 (Power Mode transcript parsing)
**Related OPTIMUS:** Decided to start fresh (not harvest)

**Files Referenced:**
- `packages/popkit-core/commands/record.md` - Existing recording command
- `packages/popkit-core/hooks/subagent-stop.py` - Line 195 TODO (Issue #110)
- `packages/shared-py/popkit_shared/utils/transcript_parser.py` - Complete, needs integration
- `packages/shared-py/popkit_shared/utils/session_recorder.py` - Local recording
- `packages/shared-py/popkit_shared/utils/privacy.py` - Privacy settings
- `packages/shared-py/popkit_shared/utils/pattern_anonymizer.py` - Redaction

**Technologies:**
- **Plugin:** Python (hooks, utilities)
- **API:** TypeScript (Cloudflare Workers)
- **Dashboard:** Next.js 14, React 18, Tailwind CSS
- **Storage:** Upstash Redis (streams), Upstash Vector (search)
- **Real-time:** Server-Sent Events (SSE)
- **State:** Zustand (dashboard)
- **Charts:** Recharts (cost visualization)
- **Testing:** Vitest (units), Playwright (E2E)

---

**End of Design Document**
