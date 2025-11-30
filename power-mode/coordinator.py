#!/usr/bin/env python3
"""
Pop Power Mode Coordinator
The mesh brain that orchestrates multi-agent collaboration via Redis pub/sub.

Inspired by ZigBee mesh coordinators and DeepMind's objective-driven systems.
"""

import json
import sys
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field
import hashlib

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from protocol import (
    Message, MessageType, MessageFactory,
    Objective, AgentState, Insight, InsightType,
    AgentIdentity, Guardrails, Channels,
    create_objective
)


# =============================================================================
# CONFIGURATION
# =============================================================================

def load_config() -> Dict:
    """Load power mode configuration."""
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    return {}


CONFIG = load_config()


# =============================================================================
# AGENT REGISTRY
# =============================================================================

@dataclass
class RegisteredAgent:
    """An agent registered with the coordinator."""
    identity: AgentIdentity
    state: Optional[AgentState] = None
    last_heartbeat: datetime = field(default_factory=datetime.now)
    assigned_task: Optional[Dict] = None
    heartbeat_misses: int = 0
    is_active: bool = True


class AgentRegistry:
    """Tracks all agents in the mesh."""

    def __init__(self):
        self.agents: Dict[str, RegisteredAgent] = {}
        self._lock = threading.Lock()

    def register(self, identity: AgentIdentity) -> RegisteredAgent:
        """Register a new agent."""
        with self._lock:
            agent = RegisteredAgent(identity=identity)
            self.agents[identity.id] = agent
            return agent

    def unregister(self, agent_id: str):
        """Remove an agent from the registry."""
        with self._lock:
            if agent_id in self.agents:
                del self.agents[agent_id]

    def update_heartbeat(self, agent_id: str, state: Optional[AgentState] = None):
        """Update agent's last heartbeat time."""
        with self._lock:
            if agent_id in self.agents:
                self.agents[agent_id].last_heartbeat = datetime.now()
                self.agents[agent_id].heartbeat_misses = 0
                if state:
                    self.agents[agent_id].state = state

    def increment_heartbeat_miss(self, agent_id: str) -> int:
        """Increment heartbeat miss count, return new count."""
        with self._lock:
            if agent_id in self.agents:
                self.agents[agent_id].heartbeat_misses += 1
                return self.agents[agent_id].heartbeat_misses
            return 0

    def mark_inactive(self, agent_id: str):
        """Mark an agent as inactive."""
        with self._lock:
            if agent_id in self.agents:
                self.agents[agent_id].is_active = False

    def get_active_agents(self) -> List[RegisteredAgent]:
        """Get all active agents."""
        with self._lock:
            return [a for a in self.agents.values() if a.is_active]

    def get_agent(self, agent_id: str) -> Optional[RegisteredAgent]:
        """Get a specific agent."""
        return self.agents.get(agent_id)

    def assign_task(self, agent_id: str, task: Dict):
        """Assign a task to an agent."""
        with self._lock:
            if agent_id in self.agents:
                self.agents[agent_id].assigned_task = task


# =============================================================================
# SYNC BARRIERS
# =============================================================================

@dataclass
class SyncBarrier:
    """A synchronization point for agents."""
    id: str
    required_agents: Set[str]
    acknowledged_agents: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    timeout_seconds: int = 120
    on_complete: Optional[Callable] = None

    def acknowledge(self, agent_id: str) -> bool:
        """Agent acknowledges the barrier. Returns True if all acknowledged."""
        if agent_id in self.required_agents:
            self.acknowledged_agents.add(agent_id)
        return self.is_complete()

    def is_complete(self) -> bool:
        """Check if all required agents have acknowledged."""
        return self.required_agents == self.acknowledged_agents

    def is_expired(self) -> bool:
        """Check if barrier has timed out."""
        elapsed = (datetime.now() - self.created_at).total_seconds()
        return elapsed > self.timeout_seconds

    def missing_agents(self) -> Set[str]:
        """Get agents that haven't acknowledged yet."""
        return self.required_agents - self.acknowledged_agents


class SyncManager:
    """Manages synchronization barriers."""

    def __init__(self):
        self.barriers: Dict[str, SyncBarrier] = {}
        self._lock = threading.Lock()

    def create_barrier(
        self,
        barrier_id: str,
        required_agents: List[str],
        timeout: int = 120,
        on_complete: Optional[Callable] = None
    ) -> SyncBarrier:
        """Create a new sync barrier."""
        with self._lock:
            barrier = SyncBarrier(
                id=barrier_id,
                required_agents=set(required_agents),
                timeout_seconds=timeout,
                on_complete=on_complete
            )
            self.barriers[barrier_id] = barrier
            return barrier

    def acknowledge(self, barrier_id: str, agent_id: str) -> Optional[bool]:
        """
        Acknowledge a barrier.
        Returns True if complete, False if not, None if barrier doesn't exist.
        """
        with self._lock:
            if barrier_id not in self.barriers:
                return None

            barrier = self.barriers[barrier_id]
            complete = barrier.acknowledge(agent_id)

            if complete and barrier.on_complete:
                barrier.on_complete()

            return complete

    def cleanup_expired(self) -> List[str]:
        """Remove expired barriers, return their IDs."""
        with self._lock:
            expired = [bid for bid, b in self.barriers.items() if b.is_expired()]
            for bid in expired:
                del self.barriers[bid]
            return expired


# =============================================================================
# INSIGHT POOL
# =============================================================================

class InsightPool:
    """Manages shared insights between agents."""

    def __init__(self, max_insights: int = 100):
        self.insights: List[Insight] = []
        self.max_insights = max_insights
        self._lock = threading.Lock()

    def add(self, insight: Insight):
        """Add an insight to the pool."""
        with self._lock:
            # Deduplication check
            for existing in self.insights:
                if self._is_duplicate(existing, insight):
                    return

            self.insights.append(insight)

            # Trim if over limit
            if len(self.insights) > self.max_insights:
                self.insights = self.insights[-self.max_insights:]

    def get_relevant(
        self,
        tags: List[str],
        exclude_agent: Optional[str] = None,
        limit: int = 3
    ) -> List[Insight]:
        """Get insights relevant to the given tags."""
        with self._lock:
            relevant = []
            for insight in reversed(self.insights):  # Most recent first
                # Skip if from the requesting agent
                if exclude_agent and insight.from_agent == exclude_agent:
                    continue

                # Check tag overlap
                tag_overlap = set(insight.relevance_tags) & set(tags)
                if tag_overlap:
                    relevant.append(insight)
                    if len(relevant) >= limit:
                        break

            return relevant

    def mark_consumed(self, insight_id: str, agent_id: str):
        """Mark an insight as consumed by an agent."""
        with self._lock:
            for insight in self.insights:
                if insight.id == insight_id:
                    insight.consumed_by.append(agent_id)
                    break

    def _is_duplicate(self, a: Insight, b: Insight) -> bool:
        """Check if two insights are duplicates."""
        # Simple content similarity check
        return (
            a.type == b.type and
            a.content.lower().strip() == b.content.lower().strip()
        )


# =============================================================================
# PATTERN LEARNING
# =============================================================================

@dataclass
class LearnedPattern:
    """A pattern learned from agent behavior."""
    id: str
    approach: str
    context: str
    outcome: str  # "success", "failed", "partial"
    confidence: float
    learned_at: datetime = field(default_factory=datetime.now)
    usage_count: int = 0


class PatternLearner:
    """Tracks and learns from successful/failed approaches."""

    def __init__(self):
        self.patterns: Dict[str, LearnedPattern] = {}
        self._lock = threading.Lock()

    def record(self, approach: str, context: str, outcome: str, confidence: float = 0.5):
        """Record a pattern from agent behavior."""
        pattern_id = hashlib.md5(f"{approach}{context}".encode()).hexdigest()[:8]

        with self._lock:
            if pattern_id in self.patterns:
                # Update existing pattern
                existing = self.patterns[pattern_id]
                existing.usage_count += 1
                # Adjust confidence based on new outcome
                if outcome == existing.outcome:
                    existing.confidence = min(1.0, existing.confidence + 0.1)
                else:
                    existing.confidence = max(0.0, existing.confidence - 0.2)
            else:
                # New pattern
                self.patterns[pattern_id] = LearnedPattern(
                    id=pattern_id,
                    approach=approach,
                    context=context,
                    outcome=outcome,
                    confidence=confidence
                )

    def get_recommendations(self, context: str, limit: int = 3) -> List[Dict]:
        """Get pattern recommendations for a given context."""
        with self._lock:
            recommendations = []
            context_lower = context.lower()

            for pattern in self.patterns.values():
                if pattern.context.lower() in context_lower:
                    if pattern.outcome == "success" and pattern.confidence > 0.6:
                        recommendations.append({
                            "approach": pattern.approach,
                            "confidence": pattern.confidence,
                            "reason": f"Worked {pattern.usage_count} times in similar context"
                        })
                    elif pattern.outcome == "failed" and pattern.confidence > 0.6:
                        recommendations.append({
                            "avoid": pattern.approach,
                            "confidence": pattern.confidence,
                            "reason": f"Failed in similar context"
                        })

            # Sort by confidence
            recommendations.sort(key=lambda x: x.get("confidence", 0), reverse=True)
            return recommendations[:limit]


# =============================================================================
# COORDINATOR
# =============================================================================

class PowerModeCoordinator:
    """
    The mesh brain that orchestrates multi-agent collaboration.

    Responsibilities:
    - Track agent states and heartbeats
    - Route messages between agents
    - Manage sync barriers
    - Share insights intelligently
    - Detect and handle agent failures
    - Enforce guardrails
    - Track objective progress
    """

    def __init__(self, objective: Optional[Objective] = None):
        self.objective = objective
        self.session_id = hashlib.md5(
            datetime.now().isoformat().encode()
        ).hexdigest()[:8]

        # Core components
        self.registry = AgentRegistry()
        self.sync_manager = SyncManager()
        self.insight_pool = InsightPool()
        self.pattern_learner = PatternLearner()
        self.guardrails = Guardrails(objective)

        # Redis connection
        self.redis: Optional[redis.Redis] = None
        self.pubsub: Optional[redis.client.PubSub] = None

        # State
        self.is_running = False
        self.current_phase = 0
        self.phase_results: Dict[str, List[Dict]] = {}
        self.human_pending: List[Message] = []

        # Threads
        self._listener_thread: Optional[threading.Thread] = None
        self._monitor_thread: Optional[threading.Thread] = None

    def connect(self) -> bool:
        """Connect to Redis."""
        if not REDIS_AVAILABLE:
            print("Redis not available. Install with: pip install redis", file=sys.stderr)
            return False

        try:
            redis_config = CONFIG.get("redis", {})
            self.redis = redis.Redis(
                host=redis_config.get("host", "localhost"),
                port=redis_config.get("port", 6379),
                db=redis_config.get("db", 0),
                password=redis_config.get("password"),
                socket_timeout=redis_config.get("socket_timeout", 5),
                retry_on_timeout=redis_config.get("retry_on_timeout", True),
                decode_responses=True
            )
            self.redis.ping()
            self.pubsub = self.redis.pubsub()
            return True
        except redis.ConnectionError as e:
            print(f"Failed to connect to Redis: {e}", file=sys.stderr)
            return False

    def start(self):
        """Start the coordinator."""
        if not self.redis:
            if not self.connect():
                return False

        self.is_running = True

        # Subscribe to coordinator channel
        self.pubsub.subscribe(Channels.coordinator())
        self.pubsub.subscribe(Channels.heartbeat())
        self.pubsub.subscribe(Channels.results())
        self.pubsub.subscribe(Channels.insights())
        self.pubsub.subscribe(Channels.human())

        # Start listener thread
        self._listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listener_thread.start()

        # Start monitor thread
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

        # Store objective in Redis
        if self.objective:
            self.redis.set(
                Channels.objective_key(),
                json.dumps(self.objective.to_dict())
            )

        print(f"Coordinator started. Session: {self.session_id}")
        return True

    def stop(self):
        """Stop the coordinator."""
        self.is_running = False

        if self.pubsub:
            self.pubsub.unsubscribe()

        if self._listener_thread:
            self._listener_thread.join(timeout=2)

        if self._monitor_thread:
            self._monitor_thread.join(timeout=2)

        print("Coordinator stopped.")

    def _listen_loop(self):
        """Main message listening loop."""
        while self.is_running:
            try:
                message = self.pubsub.get_message(timeout=1)
                if message and message["type"] == "message":
                    self._handle_message(message["channel"], message["data"])
            except Exception as e:
                print(f"Listener error: {e}", file=sys.stderr)

    def _monitor_loop(self):
        """Monitor agent health and sync barriers."""
        while self.is_running:
            try:
                self._check_agent_health()
                self._cleanup_expired_barriers()
                time.sleep(CONFIG.get("intervals", {}).get("heartbeat_seconds", 15))
            except Exception as e:
                print(f"Monitor error: {e}", file=sys.stderr)

    def _handle_message(self, channel: str, data: str):
        """Handle an incoming message."""
        try:
            msg = Message.from_json(data)
        except json.JSONDecodeError:
            return

        handlers = {
            MessageType.HEARTBEAT: self._handle_heartbeat,
            MessageType.PROGRESS: self._handle_progress,
            MessageType.RESULT: self._handle_result,
            MessageType.INSIGHT: self._handle_insight,
            MessageType.SYNC_ACK: self._handle_sync_ack,
            MessageType.HUMAN_REQUIRED: self._handle_human_required,
            MessageType.BOUNDARY_ALERT: self._handle_boundary_alert,
        }

        handler = handlers.get(msg.type)
        if handler:
            handler(msg)

    def _handle_heartbeat(self, msg: Message):
        """Handle agent heartbeat."""
        agent_id = msg.from_agent
        state_data = msg.payload

        # Update registry
        self.registry.update_heartbeat(agent_id)

        # Store state in Redis
        if state_data:
            self.redis.hset(
                Channels.state_key(agent_id),
                mapping={k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
                         for k, v in state_data.items()}
            )

            # Check for drift
            if "agent" in state_data:
                state = AgentState(**state_data)
                drift = self.guardrails.check_drift(state)
                if drift:
                    self._broadcast_drift_alert(agent_id, drift)

    def _handle_progress(self, msg: Message):
        """Handle progress update."""
        agent_id = msg.from_agent
        progress = msg.payload.get("progress", 0)

        agent = self.registry.get_agent(agent_id)
        if agent and agent.state:
            agent.state.progress = progress

        # Broadcast progress to other agents (they might be waiting)
        self._broadcast(MessageFactory.progress(
            "coordinator",
            progress,
            {"agent": agent_id, "phase": self.current_phase}
        ))

    def _handle_result(self, msg: Message):
        """Handle task completion result."""
        agent_id = msg.from_agent
        result = msg.payload

        # Store phase results
        phase = self.objective.phases[self.current_phase] if self.objective else "default"
        if phase not in self.phase_results:
            self.phase_results[phase] = []
        self.phase_results[phase].append({
            "agent": agent_id,
            "result": result,
            "timestamp": datetime.now().isoformat()
        })

        # Learn from result
        if result.get("approach"):
            self.pattern_learner.record(
                approach=result["approach"],
                context=result.get("context", ""),
                outcome="success" if result.get("success") else "failed",
                confidence=result.get("confidence", 0.5)
            )

        # Check if phase is complete
        self._check_phase_completion()

    def _handle_insight(self, msg: Message):
        """Handle shared insight."""
        insight_data = msg.payload

        try:
            insight = Insight.from_dict(insight_data)
            self.insight_pool.add(insight)

            # Route to relevant agents
            for agent in self.registry.get_active_agents():
                if agent.identity.id == msg.from_agent:
                    continue  # Don't send back to sender

                if agent.assigned_task:
                    task_tags = agent.assigned_task.get("tags", [])
                    if set(insight.relevance_tags) & set(task_tags):
                        self._send_to_agent(agent.identity.id, msg)

        except Exception as e:
            print(f"Error handling insight: {e}", file=sys.stderr)

    def _handle_sync_ack(self, msg: Message):
        """Handle sync barrier acknowledgment."""
        barrier_id = msg.payload.get("barrier_id")
        agent_id = msg.from_agent

        complete = self.sync_manager.acknowledge(barrier_id, agent_id)
        if complete:
            # Broadcast that barrier is complete
            self._broadcast(Message(
                id=hashlib.md5(f"sync-complete-{barrier_id}".encode()).hexdigest()[:12],
                type=MessageType.SYNC,
                from_agent="coordinator",
                to_agent="*",
                payload={"barrier_id": barrier_id, "status": "complete"}
            ))

    def _handle_human_required(self, msg: Message):
        """Handle request for human decision."""
        self.human_pending.append(msg)

        # Store in Redis for human to see
        self.redis.lpush(
            Channels.human(),
            msg.to_json()
        )

        # Pause the requesting agent
        self._send_to_agent(msg.from_agent, Message(
            id=hashlib.md5(f"pause-{msg.from_agent}".encode()).hexdigest()[:12],
            type=MessageType.COURSE_CORRECT,
            from_agent="coordinator",
            to_agent=msg.from_agent,
            payload={
                "action": "pause",
                "reason": "Waiting for human decision",
                "decision_id": msg.id
            }
        ))

    def _handle_boundary_alert(self, msg: Message):
        """Handle boundary violation alert."""
        violation = msg.payload

        # Log violation
        self.guardrails.violations.append({
            "agent": msg.from_agent,
            "violation": violation,
            "timestamp": datetime.now().isoformat()
        })

        # Determine action based on severity
        if violation.get("requires_human"):
            self._handle_human_required(MessageFactory.human_required(
                msg.from_agent,
                {
                    "description": f"Boundary violation: {violation.get('description')}",
                    "context": violation,
                    "recommendation": "Review and decide whether to allow"
                }
            ))
        else:
            # Send course correction
            self._send_to_agent(msg.from_agent, Message(
                id=hashlib.md5(f"correct-{msg.from_agent}".encode()).hexdigest()[:12],
                type=MessageType.COURSE_CORRECT,
                from_agent="coordinator",
                to_agent=msg.from_agent,
                payload={
                    "action": "redirect",
                    "reason": violation.get("reason", "Stay within boundaries"),
                    "suggestion": violation.get("suggestion")
                }
            ))

    def _check_agent_health(self):
        """Check agent health and handle failures."""
        timeout = CONFIG.get("intervals", {}).get("agent_timeout_seconds", 60)
        max_misses = CONFIG.get("failover", {}).get("heartbeat_miss_threshold", 3)

        for agent in self.registry.get_active_agents():
            elapsed = (datetime.now() - agent.last_heartbeat).total_seconds()

            if elapsed > timeout:
                misses = self.registry.increment_heartbeat_miss(agent.identity.id)

                if misses >= max_misses:
                    self._handle_agent_failure(agent)

    def _handle_agent_failure(self, agent: RegisteredAgent):
        """Handle an agent that has failed."""
        self.registry.mark_inactive(agent.identity.id)

        # Broadcast agent down
        self._broadcast(Message(
            id=hashlib.md5(f"down-{agent.identity.id}".encode()).hexdigest()[:12],
            type=MessageType.AGENT_DOWN,
            from_agent="coordinator",
            to_agent="*",
            payload={
                "agent": agent.identity.id,
                "agent_name": agent.identity.name,
                "last_state": agent.state.to_dict() if agent.state else None,
                "assigned_task": agent.assigned_task
            }
        ))

        # Create orphaned task if there was work in progress
        if agent.assigned_task and CONFIG.get("failover", {}).get("auto_reassign_orphaned"):
            self._create_orphaned_task(agent)

    def _create_orphaned_task(self, agent: RegisteredAgent):
        """Create an orphaned task for reassignment."""
        orphaned = {
            "original_agent": agent.identity.id,
            "original_agent_name": agent.identity.name,
            "task": agent.assigned_task,
            "progress": agent.state.progress if agent.state else 0,
            "context": agent.state.to_dict() if agent.state else {},
            "created_at": datetime.now().isoformat()
        }

        # Store in Redis
        self.redis.lpush("pop:tasks:orphaned", json.dumps(orphaned))

        # Broadcast availability
        self._broadcast(Message(
            id=hashlib.md5(f"orphan-{agent.identity.id}".encode()).hexdigest()[:12],
            type=MessageType.TASK_ORPHANED,
            from_agent="coordinator",
            to_agent="*",
            payload=orphaned
        ))

    def _cleanup_expired_barriers(self):
        """Clean up expired sync barriers."""
        expired = self.sync_manager.cleanup_expired()
        for barrier_id in expired:
            self._broadcast(Message(
                id=hashlib.md5(f"barrier-expired-{barrier_id}".encode()).hexdigest()[:12],
                type=MessageType.SYNC,
                from_agent="coordinator",
                to_agent="*",
                payload={"barrier_id": barrier_id, "status": "expired"}
            ))

    def _check_phase_completion(self):
        """Check if current phase is complete."""
        if not self.objective:
            return

        active_agents = self.registry.get_active_agents()
        all_complete = all(
            agent.state and agent.state.progress >= 1.0
            for agent in active_agents
            if agent.assigned_task
        )

        if all_complete:
            self._advance_phase()

    def _advance_phase(self):
        """Advance to the next phase."""
        if not self.objective:
            return

        self.current_phase += 1

        if self.current_phase >= len(self.objective.phases):
            self._complete_objective()
            return

        phase_name = self.objective.phases[self.current_phase]

        # Create sync barrier for phase transition
        active_ids = [a.identity.id for a in self.registry.get_active_agents()]
        self.sync_manager.create_barrier(
            f"phase-{self.current_phase}",
            active_ids,
            on_complete=lambda: self._start_phase(phase_name)
        )

        # Broadcast phase transition
        self._broadcast(MessageFactory.sync(
            f"phase-{self.current_phase}",
            active_ids
        ))

    def _start_phase(self, phase_name: str):
        """Start a new phase."""
        # Aggregate insights from previous phase
        recommendations = self.pattern_learner.get_recommendations(phase_name)

        self._broadcast(Message(
            id=hashlib.md5(f"phase-start-{phase_name}".encode()).hexdigest()[:12],
            type=MessageType.OBJECTIVE_UPDATE,
            from_agent="coordinator",
            to_agent="*",
            payload={
                "phase": phase_name,
                "phase_index": self.current_phase,
                "recommendations": recommendations,
                "previous_results": self.phase_results.get(
                    self.objective.phases[self.current_phase - 1], []
                ) if self.current_phase > 0 else []
            }
        ))

    def _complete_objective(self):
        """Handle objective completion."""
        # Aggregate all results
        final_results = {
            "objective": self.objective.description,
            "phases_completed": len(self.objective.phases),
            "results_by_phase": self.phase_results,
            "patterns_learned": len(self.pattern_learner.patterns),
            "insights_shared": len(self.insight_pool.insights),
            "violations": len(self.guardrails.violations),
            "completed_at": datetime.now().isoformat()
        }

        # Store final results
        self.redis.set(
            f"pop:completed:{self.session_id}",
            json.dumps(final_results)
        )

        # Broadcast completion
        self._broadcast(Message(
            id=hashlib.md5(f"complete-{self.session_id}".encode()).hexdigest()[:12],
            type=MessageType.OBJECTIVE_UPDATE,
            from_agent="coordinator",
            to_agent="*",
            payload={
                "status": "complete",
                "summary": final_results
            }
        ))

    def _broadcast(self, msg: Message):
        """Broadcast a message to all agents."""
        self.redis.publish(Channels.broadcast(), msg.to_json())

    def _broadcast_drift_alert(self, agent_id: str, drift: Dict):
        """Broadcast a drift alert."""
        self._send_to_agent(agent_id, Message(
            id=hashlib.md5(f"drift-{agent_id}".encode()).hexdigest()[:12],
            type=MessageType.DRIFT_ALERT,
            from_agent="coordinator",
            to_agent=agent_id,
            payload=drift
        ))

    def _send_to_agent(self, agent_id: str, msg: Message):
        """Send a message to a specific agent."""
        self.redis.publish(Channels.agent(agent_id), msg.to_json())

    # =========================================================================
    # PUBLIC API
    # =========================================================================

    def register_agent(self, name: str) -> AgentIdentity:
        """Register a new agent with the coordinator."""
        identity = AgentIdentity(
            id=hashlib.md5(f"{name}{datetime.now()}".encode()).hexdigest()[:8],
            name=name,
            session_id=self.session_id
        )
        self.registry.register(identity)
        return identity

    def assign_task(self, agent_id: str, task: Dict):
        """Assign a task to an agent."""
        self.registry.assign_task(agent_id, task)

        msg = MessageFactory.task("coordinator", agent_id, task)
        self._send_to_agent(agent_id, msg)

    def create_sync_barrier(self, name: str, agents: List[str]) -> str:
        """Create a sync barrier and notify agents."""
        barrier_id = f"{name}-{hashlib.md5(datetime.now().isoformat().encode()).hexdigest()[:6]}"
        self.sync_manager.create_barrier(barrier_id, agents)

        msg = MessageFactory.sync(barrier_id, agents)
        self._broadcast(msg)

        return barrier_id

    def get_insights_for_agent(self, agent_id: str, tags: List[str]) -> List[Dict]:
        """Get relevant insights for an agent."""
        insights = self.insight_pool.get_relevant(
            tags=tags,
            exclude_agent=agent_id,
            limit=CONFIG.get("limits", {}).get("max_insights_per_pull", 3)
        )
        return [i.to_dict() for i in insights]

    def get_pattern_recommendations(self, context: str) -> List[Dict]:
        """Get pattern recommendations for a context."""
        return self.pattern_learner.get_recommendations(context)

    def get_human_pending(self) -> List[Dict]:
        """Get pending human decisions."""
        return [m.payload for m in self.human_pending]

    def resolve_human_decision(self, decision_id: str, approved: bool, notes: str = ""):
        """Resolve a pending human decision."""
        for msg in self.human_pending:
            if msg.id == decision_id:
                self.human_pending.remove(msg)

                # Send resolution to agent
                self._send_to_agent(msg.from_agent, Message(
                    id=hashlib.md5(f"resolve-{decision_id}".encode()).hexdigest()[:12],
                    type=MessageType.COURSE_CORRECT,
                    from_agent="coordinator",
                    to_agent=msg.from_agent,
                    payload={
                        "action": "resume" if approved else "abort",
                        "decision_id": decision_id,
                        "approved": approved,
                        "notes": notes
                    }
                ))
                break

    def get_status(self) -> Dict:
        """Get coordinator status."""
        return {
            "session_id": self.session_id,
            "is_running": self.is_running,
            "objective": self.objective.description if self.objective else None,
            "current_phase": self.current_phase,
            "phase_name": self.objective.phases[self.current_phase] if self.objective and self.current_phase < len(self.objective.phases) else None,
            "active_agents": len(self.registry.get_active_agents()),
            "insights_pooled": len(self.insight_pool.insights),
            "patterns_learned": len(self.pattern_learner.patterns),
            "human_pending": len(self.human_pending),
            "violations": len(self.guardrails.violations)
        }


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """CLI entry point for the coordinator."""
    import argparse

    parser = argparse.ArgumentParser(description="Pop Power Mode Coordinator")
    parser.add_argument("command", choices=["start", "status", "stop"])
    parser.add_argument("--objective", help="Objective description")
    parser.add_argument("--phases", nargs="+", help="Phase names")
    parser.add_argument("--success-criteria", nargs="+", help="Success criteria")

    args = parser.parse_args()

    if args.command == "start":
        objective = None
        if args.objective:
            objective = create_objective(
                description=args.objective,
                success_criteria=args.success_criteria or ["Task completed"],
                phases=args.phases or ["explore", "implement", "review"]
            )

        coordinator = PowerModeCoordinator(objective)
        if coordinator.start():
            print("Press Ctrl+C to stop...")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                coordinator.stop()
        else:
            print("Failed to start coordinator")
            sys.exit(1)

    elif args.command == "status":
        # Check Redis for coordinator status
        if not REDIS_AVAILABLE:
            print("Redis not available")
            sys.exit(1)

        r = redis.Redis(decode_responses=True)
        status = r.get("pop:coordinator:status")
        if status:
            print(json.dumps(json.loads(status), indent=2))
        else:
            print("No active coordinator found")

    elif args.command == "stop":
        # Signal coordinator to stop
        if not REDIS_AVAILABLE:
            print("Redis not available")
            sys.exit(1)

        r = redis.Redis(decode_responses=True)
        r.publish("pop:coordinator", json.dumps({"command": "stop"}))
        print("Stop signal sent")


if __name__ == "__main__":
    main()
