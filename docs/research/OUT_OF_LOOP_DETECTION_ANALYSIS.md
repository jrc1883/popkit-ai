# PopKit Out-of-Loop Detection: Comprehensive Analysis & Roadmap

**Date:** 2025-12-12
**Status:** Ready for design & prototyping phase
**Confidence:** HIGH (verified against source code)

---

## EXECUTIVE SUMMARY

PopKit has **9 distinct orchestration patterns** running simultaneously across multiple coordination modes. Current out-of-loop detection is **fragmented** — heartbeats exist in Redis, activity logs exist per-session, but there's **no unified activity view**.

**Key Finding:** You already have the infrastructure. You need to **wire it together** using Upstash Redis Streams as a central activity ledger.

---

## PART 1: REDIS VERIFICATION & TECH STACK

### ✅ Hybrid Redis Architecture (CONFIRMED)

**Local Development (Power Mode):**
- **Docker Redis** on `localhost:16379`
- Spawned via: `docker-compose.yml` in `packages/plugin/power-mode/`
- Setup command: `/popkit:power init`
- **Status:** Works, but requires Docker
- **Plan:** Can be deprecated after native async mode is production-ready

**Cloud Backend (PopKit Cloud API):**
- **Upstash Redis REST API** in `packages/cloud/src/routes/redis.ts`
- Config: `UPSTASH_REDIS_REST_URL` + `UPSTASH_REDIS_REST_TOKEN` in `wrangler.toml`
- **Status:** Ready for production
- **Endpoints Already Implemented:**
  - `/redis/state` - Agent state storage
  - `/redis/insights` - Insight pool queries
  - `/redis/messages` - Inter-agent messaging
  - `/redis/objective` - Current objective tracking
  - `/redis/publish` + `/redis/subscribe` - Polling-based pub/sub (REST workaround)

### 🎯 Upstash Stack Integration Status

| Service | Status | Use Case | Integration |
|---------|--------|----------|-------------|
| **Redis** | ✅ Active | Pub/sub messaging, state storage | Cloud API endpoints exist |
| **Vector** | 🟡 Planned | Semantic agent discovery, pattern learning | High priority (3-5 days to implement) |
| **Workflow** | 🟡 Recommended | Durable orchestration, scheduled routines | **100% alignment with Power Mode v2** |
| **QStash** | 🔴 Deprecated | Was recommended for routines | **Superseded by Upstash Workflow** |

**Verdict:** Redis stack is modern (Upstash cloud), Docker can be safely deprecated later.

---

## PART 2: THE 9 ORCHESTRATION PATTERNS (COMPLETE MAP)

PopKit orchestrates work through **9 concurrent patterns**. Each can run independently OR together, but currently **there's no unified view of what's active**.

### Pattern Matrix

| # | Pattern | Type | Active/Passive | Runs In Loop? | Can Parallel? | Communication |
|---|---------|------|---|---|---|---|
| **1** | **Skills** (36 total) | Tool wrapper | Active | Yes | Unlimited parallel | Tool output |
| **2** | **Tier-1 Agents** (11: reviewer, bug-whisperer, security, etc.) | Router + Active | Active | Yes | Multiple | Agent output + Redis |
| **3** | **Tier-2 Agents** (17: ai-eng, deploy-validator, etc.) | Triggered by context | Active | Yes | Conditional | Protocol messages |
| **4** | **Feature-Workflow Agents** (3: explorer, architect, reviewer) | Orchestrated sequence | Active | Yes | Sync-barrier ordered | Redis + Phase barriers |
| **5** | **Hooks** (18 Python scripts) | Middleware/interceptor | Passive | Yes | All tool invocations | Hook JSON responses |
| **6** | **Power Mode Coordinator** | Orchestrator mesh | Active (supervises) | Yes | Up to 6 agents | Redis pub/sub + heartbeats |
| **7** | **Native Async Mode** | Orchestrator (new) | Active | Yes | 5-10 agents parallel | Task polling + file |
| **8** | **File-Based Fallback** | Coordinator (free tier) | Active | Yes | 2 agents sequential | JSON file I/O |
| **9** | **Agent Orchestrator Hook** | Router/passive | Passive | Yes | Every prompt | Hook suggestions |

### Key Insight: They All Coexist

- **Skills** can run while **Tier-1 Agents** are active
- **Power Mode** can supervise multiple **Tier-2 Agents**
- **Hooks** intercept ALL tool calls regardless of which pattern is running
- **Native Async** is an alternative to Power Mode (not replacement)
- **File Fallback** is a degradation mode when Redis unavailable

**The Problem:** No component knows what the OTHER components are doing.

---

## PART 3: THE NOVEL COMMUNICATION PROTOCOL

PopKit has a **sophisticated multi-channel pub/sub system** (coordinator.py + protocol.py):

### Message Types (All In Use)

**Core Operations:**
- `TASK` → Coordinator assigns work to agent
- `PROGRESS` → Agent reports progress mid-task
- `RESULT` → Agent completes work
- `HEARTBEAT` → "I'm alive" check-in

**Coordination:**
- `SYNC` → Sync barrier (wait for all agents)
- `SYNC_ACK` → Agent acknowledges sync point

**Knowledge Sharing (Insight Pool):**
- `INSIGHT` → Agent shares discovery (with tags, confidence, type)
- `QUERY` → Agent asks for info
- `RESPONSE` → Response to query

**Objective Tracking:**
- `OBJECTIVE_UPDATE` → Goal clarification
- `DRIFT_ALERT` → Agent off track
- `COURSE_CORRECT` → Redirect agent

**Failover:**
- `AGENT_DOWN` → Agent stopped responding
- `TASK_ORPHANED` → Task needs reassignment
- `TASK_CLAIMED` → Agent picks up orphaned task

**Guardrails:**
- `HUMAN_REQUIRED` → Need human decision
- `BOUNDARY_ALERT` → Approaching limits

**Streaming (New):**
- `STREAM_START/CHUNK/END/ERROR` → Real-time data

### Redis Channels (Current Pub/Sub)

```
pop:broadcast       → Coordinator → All agents (broadcasts)
pop:heartbeat       → Agents → Coordinator (health checks)
pop:results         → Agents → Coordinator (completions)
pop:insights        → Agents → Coordinator + Agents (discoveries)
pop:coordinator     → External → Coordinator (control)
pop:human           → Agents → Coordinator (human approval)
```

### Storage Keys (Current)

```
pop:objective           → Current objective definition
pop:state:{agent_id}    → Agent state snapshots
pop:patterns            → Learned patterns
pop:sync:{barrier_id}   → Sync barrier state
pop:insights            → Insight pool (TTL: 10 min)
```

**This infrastructure already exists.** You just need to **add activity stream tracking on top of it**.

---

## PART 4: REVISED APPROACH 1 (USERPROMPTESUBMIT HOOK)

**Original Issue:** Only checks `is_skill_active()` — misses other PopKit components.

### Revised Approach 1: Comprehensive Activity Detection

Instead of checking one skill state, check **all 9 orchestration patterns**:

```python
# In hooks/user-prompt-submit.py (NEW)

def check_orchestration_state() -> dict:
    """Check if ANY PopKit component is orchestrating."""

    state = {
        "is_in_loop": False,
        "active_components": [],
        "idle_time_seconds": None,
        "recommendation": None
    }

    # Check Pattern 1: Skill active?
    if tracker.is_skill_active():
        state["is_in_loop"] = True
        state["active_components"].append("skill")
        return state

    # Check Pattern 2-4: Agents active?
    agent_status = query_redis(f"pop:state:*")  # Get all agent states
    if agent_status and agent_status.get("is_active"):
        state["is_in_loop"] = True
        state["active_components"].append("agent")
        return state

    # Check Pattern 6: Power Mode coordinator active?
    coordinator_heartbeat = query_redis("pop:coordinator:heartbeat")
    if coordinator_heartbeat:
        elapsed = time.time() - coordinator_heartbeat["timestamp"]
        if elapsed < 30:  # Heartbeat within 30 seconds
            state["is_in_loop"] = True
            state["active_components"].append("power-mode")
            state["idle_time_seconds"] = elapsed
            return state

    # Check Pattern 7: Native Async tasks?
    if has_background_tasks():
        state["is_in_loop"] = True
        state["active_components"].append("native-async")
        return state

    # Check Pattern 8: File fallback active?
    fallback_state = read_fallback_state_file()
    if fallback_state.get("last_update") and \
       time.time() - fallback_state["last_update"] < 30:
        state["is_in_loop"] = True
        state["active_components"].append("file-fallback")
        state["idle_time_seconds"] = time.time() - fallback_state["last_update"]
        return state

    # No active component found
    state["is_in_loop"] = False
    state["idle_time_seconds"] = compute_time_since_last_activity()

    if state["idle_time_seconds"] > 300:  # >5 minutes idle
        state["recommendation"] = {
            "action": "suggest_reengagement",
            "command": "/popkit:workflow status",
            "reason": f"PopKit out of loop for {state['idle_time_seconds']}s"
        }

    return state
```

**Triggers On:** User submits new prompt
**Advantage:** Works across ALL patterns, not just skills
**Disadvantage:** Only fires when user types (doesn't detect proactive idle)

---

## PART 5: REVISED APPROACH 2 (WORKFLOW STATE MACHINE)

**Original Issue:** Only supports 7-phase feature workflow; PopKit has many orchestration patterns.

### Revised Approach 2: Multi-Pattern Orchestration State

Extend `skill_state.py` to track **all 9 patterns**, not just skills:

```python
# In hooks/utils/orchestration_state.py (NEW)

@dataclass
class OrchestrationState:
    """Unified state across all 9 PopKit patterns."""

    # Currently active pattern
    active_pattern: str = None  # "skill", "agent", "power-mode", "native-async", etc.
    started_at: datetime = None

    # For feature-workflow pattern (existing 7 phases)
    workflow_phase: str = None  # "Discovery", "Exploration", "Implementation", etc.

    # For agent-based patterns
    active_agents: List[str] = field(default_factory=list)
    agent_tasks: Dict[str, str] = field(default_factory=dict)

    # For skill-based patterns
    active_skill: str = None
    skill_decisions_pending: Dict = field(default_factory=dict)

    # For any pattern
    last_activity: datetime = None
    activity_history: List[Dict] = field(default_factory=list)  # Last 10 activities

    def is_abandoned(self, threshold_seconds: int = 900) -> bool:
        """Check if current orchestration is stalled (>15 min)."""
        if not self.active_pattern:
            return False
        elapsed = (datetime.now() - self.last_activity).total_seconds()
        return elapsed > threshold_seconds

    def get_next_expected_pattern(self) -> str:
        """Suggest which pattern should activate next based on context."""
        # Router logic: could return "agent" if code detected, "power-mode" if complex, etc.
        pass
```

**Usage in post-tool-use.py:**

```python
# After any tool execution
if orchestration.is_abandoned():
    # Output reminder
    print(f"""
    ⏸️  ORCHESTRATION PAUSED

    Active Pattern: {orchestration.active_pattern}
    Workflow Phase: {orchestration.workflow_phase}
    Idle Time: {idle_seconds}s

    Resume with: /popkit:orchestration resume
    """)
```

**Advantage:** Supports ALL 9 patterns, not just 7-phase workflows
**Disadvantage:** Requires mapping which pattern should be active (routing logic)

---

## PART 6: REVISED APPROACH 3 (UPSTASH REDIS STREAMS)

**Original Issue:** Relies on STATUS.json which is only updated manually.

### Revised Approach 3: Durable Activity Stream

Use **Upstash Redis Streams** (not pub/sub) to create a **durable activity timeline**:

```typescript
// In packages/cloud/src/routes/activity.ts (NEW)

export const handleActivityStream = async (request: Request): Promise<Response> => {
    const { method, url } = request;
    const path = new URL(url).pathname;

    // POST /activity/push - Any component logs activity
    if (method === 'POST' && path === '/activity/push') {
        const event = await request.json();

        // Add to Redis Streams
        await redis.xadd(
            'pop:activity-stream',
            '*',  // auto-generate ID
            {
                timestamp: Date.now(),
                event_type: event.type,  // "skill_started", "agent_heartbeat", etc.
                component_id: event.component_id,
                component_type: event.component_type,  // "skill", "agent", "hook", etc.
                status: event.status  // "started", "progress", "completed", "error"
            }
        );

        // Also update aggregate status
        await redis.setex(
            'pop:activity-status',
            300,  // 5 min TTL
            JSON.stringify({
                last_update: Date.now(),
                active_count: event.active_component_count,
                components: event.active_components
            })
        );

        return new Response('OK', { status: 200 });
    }

    // GET /activity/status - Query current status
    if (method === 'GET' && path === '/activity/status') {
        const status = await redis.get('pop:activity-status');
        return new Response(JSON.stringify(status || { is_active: false }));
    }

    // GET /activity/timeline - Query last N events
    if (method === 'GET' && path.startsWith('/activity/timeline')) {
        const minutes = parseInt(new URL(url).searchParams.get('minutes') || '5');
        const since = Date.now() - (minutes * 60 * 1000);

        const events = await redis.xrange(
            'pop:activity-stream',
            '-',
            '+'
            // Filter could go here for time range
        );

        return new Response(JSON.stringify(events));
    }
};
```

**How All 9 Patterns Push Events:**

```python
# Pattern 1 (Skill): In post-tool-use.py
if tool_name == "Skill":
    cloud_client.push_activity({
        "type": "skill_started",
        "component_id": f"skill-{skill_name}",
        "component_type": "skill",
        "status": "started"
    })

# Pattern 6 (Power Mode): In coordinator.py register()
def register(self, identity):
    cloud_client.push_activity({
        "type": "agent_registered",
        "component_id": identity.id,
        "component_type": "power-mode-agent",
        "status": "active"
    })

# Pattern 7 (Native Async): In native async orchestrator
when task_started():
    cloud_client.push_activity({
        "type": "async_task_started",
        "component_id": task_id,
        "component_type": "native-async",
        "status": "started"
    })

# Pattern 8 (File Fallback): In fallback coordinator
def update_state():
    # Also write to file for free tier
    push_activity_to_file({
        "timestamp": now(),
        "event": "fallback_coordination_update"
    })
```

**Query Out-of-Loop Status:**

```python
# Client-side (hooks or skills)
activity_status = cloud_client.get_activity_status()

if not activity_status['is_active'] and activity_status['idle_seconds'] > 60:
    # Out of loop! Suggest reengagement
    suggest_command("/popkit:workflow status")
```

**Advantages:**
- ✅ Durable (survives session restarts)
- ✅ Works across ALL 9 patterns
- ✅ Timeline queryable (debugging aid)
- ✅ Upstash native (scales, managed)
- ✅ Free tier has file-based equivalent

**Disadvantage:**
- Requires cloud API (pro/pro tier feature)
- But file fallback available for free tier

---

## PART 7: YOUR "BUBBLE GUM" FOOTPRINTS CONCEPT

The activity stream provides the **"footprints in the sand"** you're looking for:

```
Timeline View (Last 5 minutes):
┌──────────────────────────────────────────────┐
│ 14:35:22 → skill-test-writer started        │ 👣
│ 14:35:45 → skill-test-writer completed      │ 👣
│ 14:35:48 → agent:bug-whisperer activated    │ 👣
│ 14:36:10 → agent:bug-whisperer progress     │ 👣
│ 14:36:45 → (silence)                        │
│ 14:37:12 → (silence)                        │
│ 14:37:38 → (silence)                        │   ← OUT OF LOOP DETECTED
│ 14:38:04 → user-prompt submitted            │ 👣
└──────────────────────────────────────────────┘
```

Each activity is a "footprint" — emoji could show: 👣 🫧 💨 ✨ (your bubble gum theme!)

---

## PART 8: IMPLEMENTATION ROADMAP (Most Logical Path)

### **Phase 1: Activity Stream Foundation (5-7 days)**

**Goal:** Get unified activity tracking working end-to-end

1. **Add Upstash Redis Streams endpoint** (2 days)
   - File: `packages/cloud/src/routes/activity.ts`
   - Implement: `POST /activity/push`, `GET /activity/status`, `GET /activity/timeline`
   - Add to wrangler.toml

2. **Integrate activity tracking into all 9 patterns** (2 days)
   - Pattern 1 (Skill): Modify `hooks/post-tool-use.py`
   - Pattern 6 (Power Mode): Modify `power-mode/coordinator.py`
   - Pattern 7 (Native Async): New native async orchestrator
   - Pattern 8 (File Fallback): Write to `.claude/activity.json`
   - Others: Hooks intercept and log

3. **Test activity detection** (1 day)
   - Run `/popkit:plugin-test` with activity tracking
   - Verify timeline captures all patterns
   - Test free tier file fallback

### **Phase 2: Out-of-Loop Detection (3-5 days)**

**Goal:** Detect when PopKit is idle and suggest reengagement

1. **Add orchestration state machine** (2 days)
   - File: `hooks/utils/orchestration_state.py`
   - Replaces/extends current `skill_state.py`
   - Tracks all 9 patterns

2. **Add out-of-loop detection hook** (1 day)
   - File: `hooks/user-prompt-submit.py` or new `orchestration-monitor.py`
   - Checks activity stream
   - Suggests `/popkit:orchestration resume`

3. **Test reengagement suggestions** (1 day)
   - Simulate 5-min idle period
   - Verify suggestion fires
   - Check suggestion quality

### **Phase 3: Smart Reengagement (5-7 days)**

**Goal:** Automatically suggest next best action based on context

1. **Implement orchestration router** (2 days)
   - Given current git state, codebase, git issues → suggest next pattern
   - Example: "Detected bug fix → activate bug-whisperer"

2. **Create `/popkit:orchestration resume` skill** (2 days)
   - Reads last activity
   - Suggests which pattern to restart
   - Or: "Nothing active, what would you like to work on?"

3. **Add theme/visuals** (1-2 days)
   - "Bubble gum" emoji indicators (👣 🫧 💨 ✨)
   - Status line shows activity stream
   - Timeline output in CLI

---

## PART 9: WHICH APPROACH TO START WITH?

### **Recommended: Start with Phase 1 (Approach 3)**

**Why:**
1. ✅ Builds on existing infrastructure (Upstash already configured)
2. ✅ Doesn't break any current patterns
3. ✅ Enables both Approach 1 and 2
4. ✅ Highest ROI (small effort, big visibility)
5. ✅ Free tier compatible (file fallback)

**Then layer in Approach 1 (UserPromptSubmit hook):**
- Quick to implement (1-2 days)
- Immediate user feedback
- Tests out-of-loop detection

**Then build Approach 2 (State Machine):**
- Enables smart reengagement
- Works when user isn't typing
- Most powerful detection

---

## PART 10: CRITICAL INSIGHT

You already have **80% of the infrastructure**:
- ✅ 9 orchestration patterns (defined)
- ✅ Communication protocol (built)
- ✅ Upstash integration (configured)
- ✅ Heartbeat monitoring (in Power Mode)
- ✅ Activity logging per-pattern (scattered)

**What's missing (20%):**
- ❌ Unified activity view (Redis Streams)
- ❌ Out-of-loop detection hook (UserPromptSubmit)
- ❌ Orchestration state machine (multi-pattern tracking)
- ❌ Reengagement logic (suggestion router)

**Solution:** Wire together what you have using Upstash Redis Streams as the linchpin.

---

## SUMMARY: Decision Matrix

| Approach | Implementation | Best For | Time | Risk |
|----------|---|---|---|---|
| **1: UserPromptSubmit** | Check all 9 patterns on each prompt | Quick feedback | 1-2 days | Low |
| **2: State Machine** | Track multi-pattern orchestration | Smart decisions | 3-5 days | Low |
| **3: Redis Streams** | Durable activity timeline | Unified visibility | 5-7 days | Low |
| **All Three** | Combined (recommended) | Full solution | 9-14 days | Low |

**Recommendation:** Start with **Phase 1 (Approach 3)** as foundation, immediately add **Approach 1** (UserPromptSubmit) for quick win, then build **Approach 2** (State Machine) for intelligence.

---

## FILES TO CREATE/MODIFY

### New Files
- `packages/cloud/src/routes/activity.ts` - Activity stream API
- `hooks/utils/orchestration_state.py` - Multi-pattern state tracking
- `hooks/orchestration-monitor.py` - Out-of-loop detection
- `skills/pop-orchestration-resume/SKILL.md` - Reengagement skill

### Modify Existing
- `hooks/post-tool-use.py` - Add activity push calls
- `power-mode/coordinator.py` - Add activity push on heartbeat
- `hooks/user-prompt-submit.py` - Add comprehensive activity check (or use orchestration-monitor.py)
- `wrangler.toml` - Ensure Upstash Redis configured

---

**Ready to move to design & prototyping phase?**
