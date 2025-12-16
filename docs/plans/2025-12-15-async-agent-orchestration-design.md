# Async Agent Orchestration System - Design Document

**Date:** 2025-12-15
**Status:** Draft
**Issue:** N/A (Design Request)

## Executive Summary

This document analyzes the proposed Async Agent Orchestration System and how it integrates with PopKit's existing architecture. The system would enable:

1. **GitHub-triggered async execution** - Labels/comments spawn agents automatically
2. **Multi-location spawning** - Home computer → server → cloud fallback
3. **Graceful handoffs** - Long-running tasks continue across agent sessions
4. **Platform-agnostic design** - Works with any LLM + MCP server combination

**Key Finding:** PopKit already has 70-80% of the required infrastructure. The main gaps are the GitHub trigger mechanism and spawn location intelligence.

---

## 1. Current State Analysis

### 1.1 What Already Exists

| Component | Location | Status | Gaps |
|-----------|----------|--------|------|
| **Agent Registry** | `power-mode/coordinator.py:AgentRegistry` | ✅ Complete | Needs async wrapper |
| **Sync Barriers** | `power-mode/coordinator.py:SyncManager` | ✅ Complete | Cloud version exists |
| **Insight Sharing** | `power-mode/coordinator.py:InsightPool` | ✅ Complete | Cross-session learning |
| **Message Protocol** | `power-mode/protocol.py` | ✅ Complete | 16 message types |
| **Cloud Workflows** | `cloud/src/routes/workflows.ts` | ✅ Complete | Durable state tracking |
| **Context Storage** | `hooks/utils/context_storage.py` | ✅ Complete | 3 backends (File/Upstash/Cloud) |
| **Cloud Client** | `power-mode/cloud_client.py` | ✅ Complete | 1206 lines of API client |
| **Async Utilities** | `power-mode/async_support.py` | ✅ Complete | ThreadPool, EventEmitter, Queue |
| **QStash Messaging** | `cloud/src/routes/messages.ts` | ✅ Complete | Guaranteed delivery |
| **GitHub Actions** | `.github/workflows/` | ⚠️ Partial | Auto-label only |
| **GitHub Trigger** | - | ❌ Missing | Core new feature |
| **Spawn Location Logic** | - | ❌ Missing | Core new feature |
| **Handoff State Format** | - | ❌ Missing | Core new feature |

### 1.2 Architecture Alignment

PopKit's **orchestration-only philosophy** (from `workflows.ts:9-21`) aligns perfectly with this design:

> "These workflows are ORCHESTRATION ONLY - they track state and coordinate multi-step processes, but the actual intelligent work happens in the local Claude Code session."

This means:
- Orchestrator handles triggers, routing, and state
- Agents (Claude Code, Popkit-powered, other LLMs) do the actual work
- No redundant Claude API calls from the orchestrator

---

## 2. Proposed Architecture

### 2.1 High-Level Design

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         GITHUB TRIGGER LAYER                            │
│  Labels: agent:execute, agent:review, work-now                          │
│  Comments: /agent execute, /agent review                                │
│  Tags: agent-v1.0.0, deploy-prod                                        │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      ASYNC ORCHESTRATOR LAYER                           │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────────────┐ │
│  │   GitHub    │  │    Spawn     │  │         Task Queue              │ │
│  │   Webhook   │──│   Location   │──│  (Upstash Redis + QStash)       │ │
│  │   Handler   │  │  Intelligence│  │                                 │ │
│  └─────────────┘  └──────────────┘  └─────────────────────────────────┘ │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                      HANDOFF MANAGER                                ││
│  │  - Progress checkpoints every 60s                                   ││
│  │  - Timeout detection at 80% of limit                                ││
│  │  - State serialization for continuation                             ││
│  └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              ▼                       ▼                       ▼
┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
│   HOME COMPUTER     │ │   SERVER (UNRAID)   │ │   CLOUD (UPSTASH)   │
│   (Primary)         │ │   (Fallback 1)      │ │   (Fallback 2)      │
│                     │ │                     │ │                     │
│  ┌───────────────┐  │ │  ┌───────────────┐  │ │  ┌───────────────┐  │
│  │  Claude Code  │  │ │  │  Self-hosted  │  │ │  │   Upstash     │  │
│  │    + Popkit   │  │ │  │    Runner     │  │ │  │   Workflow    │  │
│  └───────────────┘  │ │  └───────────────┘  │ │  └───────────────┘  │
└─────────────────────┘ └─────────────────────┘ └─────────────────────┘
```

### 2.2 Component Breakdown

#### A. GitHub Trigger Handler

**Location:** New GitHub App or Actions workflow

```yaml
# .github/workflows/agent-trigger.yml
name: Agent Trigger

on:
  issues:
    types: [labeled]
  issue_comment:
    types: [created]
  pull_request:
    types: [labeled]

jobs:
  trigger-agent:
    runs-on: ubuntu-latest
    if: |
      contains(github.event.label.name, 'agent:') ||
      startsWith(github.event.comment.body, '/agent')
    steps:
      - name: Parse trigger
        id: parse
        run: |
          # Extract agent type and task from label/comment
          echo "agent_type=..." >> $GITHUB_OUTPUT
          echo "task=..." >> $GITHUB_OUTPUT

      - name: Queue task
        run: |
          curl -X POST "${{ secrets.POPKIT_API }}/v1/agents/queue" \
            -H "Authorization: Bearer ${{ secrets.POPKIT_TOKEN }}" \
            -d '{
              "source": "github",
              "repo": "${{ github.repository }}",
              "issue": ${{ github.event.issue.number || github.event.pull_request.number }},
              "task_type": "${{ steps.parse.outputs.agent_type }}",
              "payload": "${{ steps.parse.outputs.task }}"
            }'
```

**Trigger Types:**
| Trigger | Format | Use Case |
|---------|--------|----------|
| Label | `agent:execute` | Execute implementation |
| Label | `agent:review` | Code review |
| Label | `agent:fix` | Bug fix |
| Label | `work-now` | Priority execution |
| Comment | `/agent execute` | Ad-hoc execution |
| Comment | `/agent review @file.ts` | Targeted review |
| Tag | `deploy-*` | Deployment tasks |

#### B. Task Queue (Upstash Redis + QStash)

**Leverage existing infrastructure:**

```typescript
// Extension to cloud/src/routes/agents.ts

interface AgentTask {
  id: string;
  source: 'github' | 'manual' | 'scheduled';
  type: 'execute' | 'review' | 'fix' | 'deploy';
  priority: 'low' | 'normal' | 'high' | 'urgent';
  payload: {
    repo: string;
    issue?: number;
    pr?: number;
    files?: string[];
    instructions?: string;
  };
  status: 'queued' | 'spawning' | 'running' | 'handoff' | 'complete' | 'failed';
  attempts: number;
  spawnLocation?: 'home' | 'server' | 'cloud';
  handoffState?: HandoffState;
  createdAt: string;
  updatedAt: string;
}

// Queue a task
app.post('/v1/agents/queue', async (c) => {
  const task: AgentTask = {
    id: generateId(),
    ...await c.req.json(),
    status: 'queued',
    attempts: 0,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
  };

  await redis.lpush('agent:tasks:queued', JSON.stringify(task));

  // Use QStash for guaranteed delivery to spawn handler
  await qstash.publishJSON({
    url: `${env.POPKIT_API}/v1/agents/spawn`,
    body: task,
    retries: 3,
    delay: '5s', // Allow time for spawn location detection
  });

  return c.json({ taskId: task.id, status: 'queued' });
});
```

#### C. Spawn Location Intelligence

**New file:** `packages/plugin/power-mode/spawn_locator.py`

```python
"""
Spawn Location Intelligence

Determines the best available location to spawn an agent:
1. Home computer (if awake and connected)
2. Server (Unraid/Docker)
3. Cloud (Upstash Workflow)
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum
import asyncio

class SpawnLocation(Enum):
    HOME = "home"
    SERVER = "server"
    CLOUD = "cloud"

@dataclass
class LocationStatus:
    location: SpawnLocation
    available: bool
    latency_ms: Optional[int]
    capacity: float  # 0.0 to 1.0
    last_seen: Optional[str]

class SpawnLocator:
    """Determine optimal spawn location with fallback."""

    def __init__(self, config: dict):
        self.locations = config.get('spawn_locations', [])
        self.timeout_ms = config.get('health_check_timeout', 5000)

    async def find_best_location(
        self,
        task_type: str,
        priority: str = 'normal'
    ) -> Optional[SpawnLocation]:
        """
        Find the best available spawn location.

        Priority order:
        1. Home computer (Claude Code native experience)
        2. Server (Docker/Unraid self-hosted runner)
        3. Cloud (Upstash Workflow for basic tasks)

        High-priority tasks skip slow locations.
        """
        statuses = await self._check_all_locations()

        # Sort by preference and availability
        available = [s for s in statuses if s.available]

        if not available:
            return None

        # High priority skips locations with high latency
        if priority in ('high', 'urgent'):
            available = [s for s in available if (s.latency_ms or 0) < 500]

        # Prefer home for full Claude Code experience
        for loc in [SpawnLocation.HOME, SpawnLocation.SERVER, SpawnLocation.CLOUD]:
            match = next((s for s in available if s.location == loc), None)
            if match:
                return match.location

        return available[0].location if available else None

    async def _check_all_locations(self) -> List[LocationStatus]:
        """Check health of all spawn locations concurrently."""
        tasks = [
            self._check_location(SpawnLocation.HOME, self._home_endpoint()),
            self._check_location(SpawnLocation.SERVER, self._server_endpoint()),
            self._check_location(SpawnLocation.CLOUD, self._cloud_endpoint()),
        ]
        return await asyncio.gather(*tasks)

    async def _check_location(
        self,
        location: SpawnLocation,
        endpoint: str
    ) -> LocationStatus:
        """Health check a single location."""
        try:
            start = asyncio.get_event_loop().time()
            # HTTP health check with timeout
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    endpoint,
                    timeout=aiohttp.ClientTimeout(total=self.timeout_ms/1000)
                ) as resp:
                    latency = int((asyncio.get_event_loop().time() - start) * 1000)
                    data = await resp.json()
                    return LocationStatus(
                        location=location,
                        available=resp.status == 200,
                        latency_ms=latency,
                        capacity=data.get('capacity', 1.0),
                        last_seen=data.get('timestamp'),
                    )
        except Exception:
            return LocationStatus(
                location=location,
                available=False,
                latency_ms=None,
                capacity=0.0,
                last_seen=None,
            )
```

#### D. Handoff Manager

**New file:** `packages/plugin/power-mode/handoff_manager.py`

```python
"""
Handoff Manager

Handles graceful handoffs when agents approach timeout:
1. Detects when agent is at 80% of timeout limit
2. Serializes progress, remaining steps, and context
3. Stores handoff state in Redis
4. Triggers continuation agent spawn
"""

from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import json

@dataclass
class HandoffState:
    """State passed between agent sessions."""
    task_id: str
    session_number: int
    total_sessions: int

    # Progress tracking
    completed_steps: List[str]
    current_step: str
    remaining_steps: List[str]

    # Context for continuation
    context: Dict[str, Any]
    working_files: List[str]
    pending_changes: List[Dict[str, str]]

    # Metadata
    started_at: str
    handoff_at: str
    reason: str  # 'timeout', 'checkpoint', 'error'

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> 'HandoffState':
        return cls(**json.loads(data))

class HandoffManager:
    """Manage agent handoffs for long-running tasks."""

    TIMEOUT_THRESHOLD = 0.8  # Trigger handoff at 80% of timeout
    CHECKPOINT_INTERVAL = 60  # Checkpoint every 60 seconds

    def __init__(self, redis_client, timeout_seconds: int = 300):
        self.redis = redis_client
        self.timeout_seconds = timeout_seconds
        self.start_time = datetime.now()
        self.last_checkpoint = datetime.now()
        self.state: Optional[HandoffState] = None

    def should_handoff(self) -> bool:
        """Check if we're approaching timeout."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return elapsed >= self.timeout_seconds * self.TIMEOUT_THRESHOLD

    def should_checkpoint(self) -> bool:
        """Check if we should save a checkpoint."""
        elapsed = (datetime.now() - self.last_checkpoint).total_seconds()
        return elapsed >= self.CHECKPOINT_INTERVAL

    async def checkpoint(
        self,
        task_id: str,
        completed_steps: List[str],
        current_step: str,
        remaining_steps: List[str],
        context: Dict[str, Any],
        working_files: List[str] = None,
        pending_changes: List[Dict[str, str]] = None,
    ) -> None:
        """Save a progress checkpoint."""
        self.state = HandoffState(
            task_id=task_id,
            session_number=self._get_session_number(task_id),
            total_sessions=0,  # Updated on completion
            completed_steps=completed_steps,
            current_step=current_step,
            remaining_steps=remaining_steps,
            context=context,
            working_files=working_files or [],
            pending_changes=pending_changes or [],
            started_at=self.start_time.isoformat(),
            handoff_at=datetime.now().isoformat(),
            reason='checkpoint',
        )

        await self.redis.set(
            f"handoff:checkpoint:{task_id}",
            self.state.to_json(),
            ex=3600  # 1 hour TTL
        )
        self.last_checkpoint = datetime.now()

    async def initiate_handoff(
        self,
        task_id: str,
        reason: str = 'timeout'
    ) -> HandoffState:
        """
        Initiate a handoff to a new agent session.

        1. Finalize current state
        2. Store in Redis for pickup
        3. Queue continuation task
        """
        if self.state:
            self.state.handoff_at = datetime.now().isoformat()
            self.state.reason = reason

            # Store handoff state
            await self.redis.set(
                f"handoff:state:{task_id}",
                self.state.to_json(),
                ex=86400  # 24 hour TTL
            )

            # Queue continuation task
            await self._queue_continuation(task_id, self.state)

            return self.state
        return None

    async def resume_from_handoff(
        self,
        task_id: str
    ) -> Optional[HandoffState]:
        """
        Resume a task from a previous handoff.

        Called by continuation agent to pick up where previous left off.
        """
        state_json = await self.redis.get(f"handoff:state:{task_id}")
        if state_json:
            self.state = HandoffState.from_json(state_json)
            self.state.session_number += 1
            return self.state
        return None

    async def _queue_continuation(
        self,
        task_id: str,
        state: HandoffState
    ) -> None:
        """Queue a continuation task in the task queue."""
        continuation_task = {
            'id': f"{task_id}-cont-{state.session_number + 1}",
            'parent_task_id': task_id,
            'type': 'continuation',
            'handoff_state': state.to_json(),
            'status': 'queued',
            'created_at': datetime.now().isoformat(),
        }

        await self.redis.lpush(
            'agent:tasks:queued',
            json.dumps(continuation_task)
        )

    def _get_session_number(self, task_id: str) -> int:
        """Get current session number from task ID."""
        if '-cont-' in task_id:
            return int(task_id.split('-cont-')[-1])
        return 1
```

---

## 3. Implementation Options Comparison

### 3.1 Option A: Node.js Long-Running Orchestrator

**Description:** A persistent Node.js process that polls GitHub and manages the task queue.

**Pros:**
- Full control over execution flow
- Can run on home computer or server
- Real-time responsiveness
- No GitHub Actions minutes consumed

**Cons:**
- Requires always-on process
- More complex deployment
- Need to handle process management (PM2, systemd)

**Implementation:**

```typescript
// packages/orchestrator/src/index.ts

import { Octokit } from '@octokit/rest';
import { Redis } from '@upstash/redis';

class AsyncOrchestrator {
  private octokit: Octokit;
  private redis: Redis;
  private spawnLocator: SpawnLocator;

  async start() {
    console.log('Starting Async Agent Orchestrator...');

    // Start parallel loops
    await Promise.all([
      this.pollGitHubLoop(),
      this.processTaskQueue(),
      this.monitorActiveAgents(),
    ]);
  }

  private async pollGitHubLoop() {
    while (true) {
      try {
        // Check for new triggers (labels, comments)
        const triggers = await this.checkGitHubTriggers();
        for (const trigger of triggers) {
          await this.queueTask(trigger);
        }
      } catch (error) {
        console.error('GitHub poll error:', error);
      }
      await sleep(30000); // 30 second poll interval
    }
  }

  private async processTaskQueue() {
    while (true) {
      try {
        const task = await this.redis.rpop('agent:tasks:queued');
        if (task) {
          await this.spawnAgent(JSON.parse(task));
        }
      } catch (error) {
        console.error('Task processing error:', error);
      }
      await sleep(1000);
    }
  }

  private async spawnAgent(task: AgentTask) {
    // Find best spawn location
    const location = await this.spawnLocator.findBestLocation(
      task.type,
      task.priority
    );

    switch (location) {
      case 'home':
        await this.spawnLocalAgent(task);
        break;
      case 'server':
        await this.spawnServerAgent(task);
        break;
      case 'cloud':
        await this.spawnCloudAgent(task);
        break;
    }
  }
}
```

### 3.2 Option B: GitHub Actions Self-Hosted Runner

**Description:** Event-driven execution using GitHub's webhook system with self-hosted runners.

**Pros:**
- Event-driven (no polling)
- Native GitHub integration
- Built-in logging and monitoring
- Easier to set up

**Cons:**
- Runners must be pre-configured
- Less control over spawn location
- Actions minutes may apply

**Implementation:**

```yaml
# .github/workflows/agent-orchestrator.yml
name: Agent Orchestrator

on:
  workflow_dispatch:
    inputs:
      task_type:
        required: true
        type: choice
        options: [execute, review, fix, deploy]
      issue_number:
        required: false
        type: number
  issues:
    types: [labeled]
  issue_comment:
    types: [created]

jobs:
  spawn-agent:
    runs-on: [self-hosted, popkit-agent]  # Self-hosted runner

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup environment
        run: |
          # Install Claude Code if not present
          npm install -g @anthropic-ai/claude-code

      - name: Parse task
        id: parse
        uses: actions/github-script@v7
        with:
          script: |
            // Extract task from event
            const taskType = '${{ github.event.inputs.task_type }}' ||
                            context.payload.label?.name?.replace('agent:', '') ||
                            'execute';
            core.setOutput('task_type', taskType);

      - name: Execute with Claude Code
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          POPKIT_API: ${{ secrets.POPKIT_API }}
        run: |
          # Run Claude Code with Popkit
          claude --plugin popkit <<EOF
          Task: ${{ steps.parse.outputs.task_type }}
          Issue: #${{ github.event.issue.number }}

          Please analyze and execute this task following Popkit guardrails.
          EOF
```

### 3.3 Option C: Hybrid Approach (Recommended)

**Description:** Combine GitHub Actions for triggering with Node.js orchestrator for control.

```
GitHub Actions → Queue Task → Node.js Orchestrator → Spawn Agent
     ↓                              ↓
   Webhook                    Location Intelligence
                                     ↓
                         Home / Server / Cloud
```

**Why Hybrid:**
1. GitHub Actions handles event capture (reliable, no polling)
2. Node.js orchestrator handles spawn logic (flexible, controllable)
3. Cloud fallback via Upstash Workflow (resilient)

---

## 4. Agent Types Deep Dive

### 4.1 Claude Code Agents (Primary)

**Best for:** Code implementations, complex reviews, bug fixes

```python
# How to spawn a Claude Code agent

def spawn_claude_code_agent(task: AgentTask) -> None:
    """Spawn Claude Code with Popkit plugin for the task."""

    # Prepare handoff state if continuing
    handoff_file = None
    if task.handoff_state:
        handoff_file = write_handoff_context(task.handoff_state)

    # Build Claude Code command
    cmd = [
        'claude',
        '--plugin', 'popkit@popkit-claude',
        '--no-interactive',  # Run in non-interactive mode
    ]

    if handoff_file:
        cmd.extend(['--context', handoff_file])

    # Set up task prompt
    prompt = build_task_prompt(task)

    # Execute with timeout monitoring
    process = subprocess.Popen(
        cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Monitor for handoff threshold
    while process.poll() is None:
        if should_handoff(task):
            initiate_handoff(task, process)
            break
        time.sleep(10)
```

### 4.2 Popkit-Powered Agents (Platform-Agnostic)

**Best for:** Tasks that need Popkit skills but can use any LLM

```python
# Popkit agent with any LLM backend

class PopkitAgent:
    """
    Platform-agnostic agent using Popkit skills.
    Can work with Claude, GPT, Gemini, or local LLMs.
    """

    def __init__(self, llm_provider: str = 'claude'):
        self.llm = self._get_llm_client(llm_provider)
        self.skills = self._load_popkit_skills()
        self.guardrails = self._load_guardrails()

    async def execute_task(self, task: AgentTask) -> TaskResult:
        """Execute a task using Popkit skills and guardrails."""

        # Load relevant skills for task type
        skills = self.skills.get_for_task(task.type)

        # Apply guardrails
        validated_task = self.guardrails.validate(task)

        # Build prompt with skill context
        prompt = self._build_prompt(validated_task, skills)

        # Execute with LLM
        result = await self.llm.complete(prompt)

        # Validate result against guardrails
        if not self.guardrails.validate_result(result):
            return TaskResult(status='needs_review', output=result)

        return TaskResult(status='complete', output=result)
```

### 4.3 Specialized MCP Agents

**Best for:** Tasks requiring specific tool access

```typescript
// MCP agent with custom tools

import { Client } from '@modelcontextprotocol/sdk/client/index.js';

class MCPAgent {
  private client: Client;
  private tools: Map<string, Tool>;

  async executeTask(task: AgentTask): Promise<TaskResult> {
    // Connect to relevant MCP servers
    await this.connectToServers(task.requiredTools);

    // Discover available tools
    const availableTools = await this.client.listTools();

    // Execute task with tool access
    const result = await this.runWithTools(task, availableTools);

    return result;
  }
}
```

---

## 5. Handoff Mechanism Details

### 5.1 Handoff State Format

```json
{
  "task_id": "task-abc123",
  "session_number": 2,
  "total_sessions": 0,

  "completed_steps": [
    "Analyzed issue #42",
    "Identified root cause in auth.ts:156",
    "Created fix in auth.ts"
  ],
  "current_step": "Running tests",
  "remaining_steps": [
    "Fix any failing tests",
    "Update documentation",
    "Create PR"
  ],

  "context": {
    "issue_url": "https://github.com/org/repo/issues/42",
    "root_cause": "Race condition in token refresh",
    "files_modified": ["src/auth.ts"],
    "test_status": "running"
  },
  "working_files": [
    "src/auth.ts",
    "tests/auth.test.ts"
  ],
  "pending_changes": [
    {
      "file": "src/auth.ts",
      "diff": "...",
      "committed": false
    }
  ],

  "started_at": "2025-12-15T10:00:00Z",
  "handoff_at": "2025-12-15T10:04:00Z",
  "reason": "timeout"
}
```

### 5.2 Handoff Triggers

| Trigger | Threshold | Action |
|---------|-----------|--------|
| Timeout | 80% of limit | Serialize state, spawn continuation |
| Checkpoint | Every 60s | Save progress to Redis |
| Error | Unrecoverable | Save state, alert user |
| User interrupt | Manual | Save state, pause task |
| Rate limit | API limit hit | Handoff to different LLM |

### 5.3 Continuation Agent Behavior

```python
async def run_continuation_agent(task: AgentTask) -> None:
    """Run an agent that continues from a handoff."""

    # Load handoff state
    handoff = await redis.get(f"handoff:state:{task.parent_task_id}")
    state = HandoffState.from_json(handoff)

    # Build continuation prompt
    prompt = f"""
    # Continuing Task: {task.parent_task_id}

    You are picking up a task from a previous agent session.

    ## What Was Completed (Sessions 1-{state.session_number}):
    {format_completed_steps(state.completed_steps)}

    ## Current Step (In Progress):
    {state.current_step}

    ## Remaining Steps:
    {format_remaining_steps(state.remaining_steps)}

    ## Context:
    {json.dumps(state.context, indent=2)}

    ## Working Files:
    {format_files(state.working_files)}

    ## Pending Changes (Not Yet Committed):
    {format_pending_changes(state.pending_changes)}

    Please continue from where the previous session left off.
    Start by verifying the current state, then proceed with the remaining work.
    """

    # Execute with new agent
    await execute_agent(prompt, task)
```

---

## 6. Fallback Strategy

### 6.1 Spawn Location Fallback Chain

```
┌─────────────────────────────────────────────────────────────────────┐
│                     SPAWN LOCATION FALLBACK                         │
├─────────────────────────────────────────────────────────────────────┤
│  1. HOME COMPUTER                                                   │
│     ├─ Health check: GET http://home.local:8080/health              │
│     ├─ Timeout: 5 seconds                                           │
│     └─ If unavailable → try SERVER                                  │
├─────────────────────────────────────────────────────────────────────┤
│  2. SERVER (Unraid/Docker)                                          │
│     ├─ Health check: GET http://server.local:8080/health            │
│     ├─ Timeout: 5 seconds                                           │
│     └─ If unavailable → try CLOUD                                   │
├─────────────────────────────────────────────────────────────────────┤
│  3. CLOUD (Upstash Workflow)                                        │
│     ├─ Health check: GET https://api.thehouseofdeals.com/health     │
│     ├─ Always available (99.9% SLA)                                 │
│     └─ Limited capabilities (orchestration only)                    │
└─────────────────────────────────────────────────────────────────────┘
```

### 6.2 Capability Matrix by Location

| Capability | Home | Server | Cloud |
|------------|------|--------|-------|
| Claude Code | ✅ Full | ✅ Full | ❌ N/A |
| Popkit Skills | ✅ All | ✅ All | ⚠️ Subset |
| File Access | ✅ Local | ✅ Cloned | ❌ N/A |
| MCP Servers | ✅ All | ✅ All | ⚠️ HTTP only |
| Real-time | ✅ Yes | ✅ Yes | ⚠️ Delayed |
| Cost | Free | Free | Usage-based |

### 6.3 Wake-on-LAN for Home Computer

```python
# Optional: Wake sleeping home computer for high-priority tasks

import wakeonlan

async def wake_home_computer(
    mac_address: str,
    wait_seconds: int = 60
) -> bool:
    """
    Send Wake-on-LAN packet to home computer.
    Wait for it to come online.
    """
    wakeonlan.send_magic_packet(mac_address)

    # Wait for computer to boot
    start = time.time()
    while time.time() - start < wait_seconds:
        if await check_home_health():
            return True
        await asyncio.sleep(5)

    return False
```

---

## 7. Security Considerations

### 7.1 Guardrails for Autonomous Execution

```python
# Guardrails for self-healing/autonomous fixes

AUTONOMOUS_GUARDRAILS = {
    # What autonomous agents CAN do
    'allowed': [
        'run_tests',
        'run_linters',
        'format_code',
        'create_branch',
        'commit_changes',
        'create_draft_pr',
        'add_comments',
    ],

    # What requires human approval
    'requires_approval': [
        'push_to_main',
        'merge_pr',
        'deploy_to_production',
        'delete_files',
        'modify_ci_config',
        'change_secrets',
    ],

    # Never allowed autonomously
    'forbidden': [
        'push_force',
        'delete_branch',
        'modify_security_settings',
        'access_secrets_directly',
    ],
}
```

### 7.2 Task Validation

```python
def validate_task(task: AgentTask) -> ValidationResult:
    """Validate a task before execution."""

    errors = []

    # Check source is trusted
    if task.source == 'github':
        if not is_trusted_repo(task.payload.repo):
            errors.append('Repository not in trusted list')
        if not is_authorized_user(task.created_by):
            errors.append('User not authorized for agent execution')

    # Check task type is allowed
    if task.type not in ALLOWED_TASK_TYPES:
        errors.append(f'Task type {task.type} not allowed')

    # Check for forbidden patterns in instructions
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in (task.payload.instructions or ''):
            errors.append(f'Forbidden pattern detected: {pattern}')

    return ValidationResult(
        valid=len(errors) == 0,
        errors=errors,
    )
```

---

## 8. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

1. **GitHub Trigger Workflow**
   - Create `.github/workflows/agent-trigger.yml`
   - Support label triggers (`agent:execute`, `agent:review`)
   - Support comment triggers (`/agent execute`)

2. **Task Queue API**
   - Add `/v1/agents/queue` endpoint
   - Add `/v1/agents/status/:taskId` endpoint
   - Integrate with QStash for guaranteed delivery

3. **Basic Spawn Handler**
   - Cloud-only spawning via Upstash Workflow
   - Simple task execution without handoffs

### Phase 2: Multi-Location (Week 3-4)

4. **Spawn Location Intelligence**
   - Create `spawn_locator.py`
   - Health checks for home/server/cloud
   - Fallback chain implementation

5. **Self-Hosted Runner Setup**
   - Docker container for agent runner
   - PM2/systemd process management
   - Health endpoint for location detection

6. **Home Computer Integration**
   - Local agent daemon
   - Wake-on-LAN support (optional)
   - Secure tunnel for remote access

### Phase 3: Handoffs (Week 5-6)

7. **Handoff Manager**
   - Create `handoff_manager.py`
   - Checkpoint saving (every 60s)
   - Timeout detection (80% threshold)

8. **Continuation Agents**
   - Resume from handoff state
   - Context restoration
   - Progress merging

9. **Long-Running Task Support**
   - Multi-session task tracking
   - Aggregate results across sessions
   - Final PR creation

### Phase 4: Polish (Week 7-8)

10. **Monitoring Dashboard**
    - Task status visualization
    - Agent activity timeline
    - Handoff history

11. **Cost Controls** (Optional)
    - Usage tracking per task
    - Budget limits
    - Alert thresholds

12. **Documentation & Testing**
    - User guide
    - API documentation
    - Integration tests

---

## 9. File Structure

```
packages/
  orchestrator/                    # NEW: Node.js orchestrator
    src/
      index.ts                     # Main entry point
      github/
        triggers.ts                # GitHub trigger handlers
        webhook.ts                 # Webhook receiver
      queue/
        task-queue.ts              # Task queue management
        processor.ts               # Task processor
      spawn/
        locator.ts                 # Spawn location intelligence
        home.ts                    # Home computer spawner
        server.ts                  # Server spawner
        cloud.ts                   # Cloud spawner
      handoff/
        manager.ts                 # Handoff management
        state.ts                   # State serialization
        continuation.ts            # Continuation logic
    package.json

  plugin/
    power-mode/
      spawn_locator.py             # NEW: Python spawn locator
      handoff_manager.py           # NEW: Python handoff manager
      async_coordinator.py         # NEW: Async wrapper for coordinator

  cloud/
    src/routes/
      agents.ts                    # EXTEND: Add queue/spawn endpoints

.github/
  workflows/
    agent-trigger.yml              # NEW: GitHub trigger workflow
```

---

## 10. Open Questions

1. **Authentication**: How do we securely authenticate spawned agents back to PopKit Cloud?

2. **Cost Allocation**: For business tier, how do we track costs per-task and per-location?

3. **LLM Routing**: When a task could use any LLM, how do we decide which to use?

4. **Conflict Resolution**: If two agents try to modify the same file, how do we handle merges?

5. **Rollback**: If an autonomous fix breaks something, what's the recovery process?

---

## 11. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Trigger-to-spawn latency | <30s | Time from label to agent start |
| Handoff success rate | >95% | Continuations that complete |
| Location fallback time | <10s | Time to detect unavailable + fallback |
| Task completion rate | >90% | Tasks that complete without human intervention |
| Mean sessions per task | <3 | Average number of handoffs needed |

---

## 12. Conclusion

The Async Agent Orchestration System builds on PopKit's strong existing foundation. The primary new components are:

1. **GitHub Trigger Handler** - Event-driven task capture
2. **Spawn Location Intelligence** - Smart fallback chain
3. **Handoff Manager** - Graceful timeout handling

The recommended approach is the **Hybrid Architecture** (Option C), combining GitHub Actions for reliable event capture with a Node.js orchestrator for flexible spawn control.

This design enables truly autonomous async development workflows while maintaining the guardrails and observability that make PopKit valuable.
