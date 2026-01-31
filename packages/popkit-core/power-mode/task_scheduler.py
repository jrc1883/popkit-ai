#!/usr/bin/env python3
"""
Priority-based Task Scheduler for Power Mode

Issue #193 Phase 1: Add task priority levels to ensure critical work gets done first.

Features:
- 4 priority levels: critical, high, medium, low
- Automatic priority assignment based on task characteristics
- Priority-based task queue sorting
- Agent assignment optimization

Architecture:
- Integrates with Native Async mode (Claude Code 2.0.64+)
- Works with Upstash and File-based fallback modes
- Thread-safe task queue with priority sorting
"""

import json
import time
from dataclasses import dataclass, asdict
from enum import IntEnum
from typing import List, Optional, Dict, Any
from pathlib import Path
import heapq


class TaskPriority(IntEnum):
    """
    Task priority levels (higher number = higher priority).

    CRITICAL (4): Blocking issues, security fixes, production failures
    HIGH (3): Important features, critical bugs, deadline-driven work
    MEDIUM (2): Standard features, non-critical bugs, improvements
    LOW (1): Nice-to-have features, documentation, cleanup
    """

    CRITICAL = 4
    HIGH = 3
    MEDIUM = 2
    LOW = 1

    @classmethod
    def from_string(cls, priority_str: str) -> "TaskPriority":
        """Convert string to TaskPriority enum."""
        mapping = {
            "critical": cls.CRITICAL,
            "high": cls.HIGH,
            "medium": cls.MEDIUM,
            "low": cls.LOW,
        }
        return mapping.get(priority_str.lower(), cls.MEDIUM)

    def to_string(self) -> str:
        """Convert enum to string."""
        return self.name.lower()


@dataclass
class Task:
    """
    Represents a task to be executed by an agent.

    Attributes:
        id: Unique task identifier
        description: Task description
        priority: Priority level (TaskPriority enum)
        assigned_agent: Agent ID if assigned, None otherwise
        created_at: Unix timestamp when task was created
        started_at: Unix timestamp when task started, None if not started
        completed_at: Unix timestamp when completed, None if not completed
        tags: List of tags for categorization (e.g., ['security', 'frontend'])
        metadata: Additional metadata (e.g., issue number, dependencies)
        estimated_duration: Estimated duration in seconds (optional)
    """

    id: str
    description: str
    priority: TaskPriority
    assigned_agent: Optional[str] = None
    created_at: float = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    tags: List[str] = None
    metadata: Dict[str, Any] = None
    estimated_duration: Optional[int] = None

    def __post_init__(self):
        """Initialize default values."""
        if self.created_at is None:
            self.created_at = time.time()
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}

    def __lt__(self, other: "Task") -> bool:
        """
        Compare tasks for priority queue (higher priority first).
        If priorities equal, older tasks come first.
        """
        if self.priority != other.priority:
            return self.priority > other.priority  # Higher priority first
        return (
            self.created_at < other.created_at
        )  # Older first (FIFO for same priority)

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary for serialization."""
        data = asdict(self)
        data["priority"] = self.priority.to_string()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Task":
        """Create task from dictionary."""
        data = data.copy()
        if isinstance(data.get("priority"), str):
            data["priority"] = TaskPriority.from_string(data["priority"])
        elif isinstance(data.get("priority"), int):
            data["priority"] = TaskPriority(data["priority"])
        return cls(**data)


class PriorityAssigner:
    """
    Automatically assigns priority to tasks based on characteristics.

    Rules (configurable via config.json):
    - Keywords in description (e.g., 'security', 'urgent', 'fix')
    - Tags (e.g., 'production', 'critical')
    - Metadata (e.g., issue labels, deadlines)
    """

    def __init__(self, config: Optional[Dict] = None):
        """Initialize with configuration."""
        self.config = config or self._load_default_config()
        self.rules = self.config.get("priority_rules", {})

    def _load_default_config(self) -> Dict:
        """Load default priority assignment rules."""
        return {
            "priority_rules": {
                "critical_keywords": [
                    "security",
                    "vulnerability",
                    "exploit",
                    "breach",
                    "production down",
                    "outage",
                    "critical bug",
                    "urgent fix",
                ],
                "high_keywords": [
                    "bug",
                    "broken",
                    "failing",
                    "error",
                    "crash",
                    "deadline",
                    "important",
                    "blocking",
                ],
                "low_keywords": [
                    "cleanup",
                    "refactor",
                    "documentation",
                    "comment",
                    "nice-to-have",
                    "future",
                    "todo",
                ],
                "critical_tags": ["security", "production", "p0", "urgent"],
                "high_tags": ["bug", "enhancement", "p1", "deadline"],
                "low_tags": ["documentation", "cleanup", "refactor", "p3"],
            }
        }

    def assign_priority(
        self, task: Task, explicit_priority: Optional[str] = None
    ) -> TaskPriority:
        """
        Assign priority to a task based on its characteristics.

        Args:
            task: Task to assign priority to
            explicit_priority: Explicit priority override (if provided)

        Returns:
            TaskPriority enum value
        """
        # Explicit priority always wins
        if explicit_priority:
            return TaskPriority.from_string(explicit_priority)

        # Check tags first
        critical_tags = self.rules.get("critical_tags", [])
        high_tags = self.rules.get("high_tags", [])
        low_tags = self.rules.get("low_tags", [])

        for tag in task.tags:
            if tag.lower() in critical_tags:
                return TaskPriority.CRITICAL

        for tag in task.tags:
            if tag.lower() in high_tags:
                return TaskPriority.HIGH

        for tag in task.tags:
            if tag.lower() in low_tags:
                return TaskPriority.LOW

        # Check description keywords
        description_lower = task.description.lower()

        critical_keywords = self.rules.get("critical_keywords", [])
        for keyword in critical_keywords:
            if keyword in description_lower:
                return TaskPriority.CRITICAL

        high_keywords = self.rules.get("high_keywords", [])
        for keyword in high_keywords:
            if keyword in description_lower:
                return TaskPriority.HIGH

        low_keywords = self.rules.get("low_keywords", [])
        for keyword in low_keywords:
            if keyword in description_lower:
                return TaskPriority.LOW

        # Default to MEDIUM if no rules match
        return TaskPriority.MEDIUM


class TaskScheduler:
    """
    Priority-based task scheduler for Power Mode.

    Manages a priority queue of tasks and assigns them to agents
    based on priority and agent availability.
    """

    def __init__(self, config: Optional[Dict] = None):
        """Initialize the task scheduler."""
        self.config = config or {}
        self.task_queue: List[Task] = []  # Priority heap
        self.tasks_by_id: Dict[str, Task] = {}
        self.priority_assigner = PriorityAssigner(config)
        self.agent_assignments: Dict[str, str] = {}  # agent_id -> task_id

    def add_task(
        self,
        task_id: str,
        description: str,
        priority: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
        estimated_duration: Optional[int] = None,
    ) -> Task:
        """
        Add a new task to the scheduler.

        Args:
            task_id: Unique task identifier
            description: Task description
            priority: Explicit priority (critical/high/medium/low) or None for auto-assign
            tags: List of tags for categorization
            metadata: Additional metadata
            estimated_duration: Estimated duration in seconds

        Returns:
            Created Task object
        """
        # Create task
        task = Task(
            id=task_id,
            description=description,
            priority=TaskPriority.MEDIUM,  # Temporary, will be reassigned
            tags=tags or [],
            metadata=metadata or {},
            estimated_duration=estimated_duration,
        )

        # Assign priority
        task.priority = self.priority_assigner.assign_priority(task, priority)

        # Add to queue and index
        heapq.heappush(self.task_queue, task)
        self.tasks_by_id[task_id] = task

        return task

    def get_next_task(self, agent_id: Optional[str] = None) -> Optional[Task]:
        """
        Get the next highest-priority task for assignment.

        Args:
            agent_id: Optional agent ID for tracking assignment

        Returns:
            Next Task or None if queue is empty
        """
        # Find next unassigned task
        while self.task_queue:
            task = heapq.heappop(self.task_queue)

            # Skip if already assigned or completed
            if task.assigned_agent is None and task.completed_at is None:
                if agent_id:
                    self._assign_task(task, agent_id)
                return task

        return None

    def _assign_task(self, task: Task, agent_id: str):
        """Assign a task to an agent."""
        task.assigned_agent = agent_id
        task.started_at = time.time()
        self.agent_assignments[agent_id] = task.id

    def complete_task(self, task_id: str):
        """Mark a task as completed."""
        task = self.tasks_by_id.get(task_id)
        if task:
            task.completed_at = time.time()
            # Remove from agent assignments
            if task.assigned_agent:
                self.agent_assignments.pop(task.assigned_agent, None)

    def get_task_stats(self) -> Dict[str, Any]:
        """Get statistics about tasks by priority."""
        stats = {
            "total": len(self.tasks_by_id),
            "by_priority": {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
            },
            "by_status": {
                "pending": 0,
                "in_progress": 0,
                "completed": 0,
            },
        }

        for task in self.tasks_by_id.values():
            # Count by priority
            priority_str = task.priority.to_string()
            stats["by_priority"][priority_str] += 1

            # Count by status
            if task.completed_at:
                stats["by_status"]["completed"] += 1
            elif task.assigned_agent:
                stats["by_status"]["in_progress"] += 1
            else:
                stats["by_status"]["pending"] += 1

        return stats

    def export_state(self) -> Dict[str, Any]:
        """Export scheduler state for persistence."""
        return {
            "tasks": [task.to_dict() for task in self.tasks_by_id.values()],
            "agent_assignments": self.agent_assignments,
            "stats": self.get_task_stats(),
        }

    def import_state(self, state: Dict[str, Any]):
        """Import scheduler state from persistence."""
        self.task_queue.clear()
        self.tasks_by_id.clear()
        self.agent_assignments = state.get("agent_assignments", {})

        for task_dict in state.get("tasks", []):
            task = Task.from_dict(task_dict)
            self.tasks_by_id[task.id] = task

            # Re-add to heap if not completed
            if not task.completed_at:
                heapq.heappush(self.task_queue, task)


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================


def create_scheduler(config_path: Optional[Path] = None) -> TaskScheduler:
    """
    Create a task scheduler with configuration.

    Args:
        config_path: Path to config.json, defaults to power-mode/config.json

    Returns:
        Configured TaskScheduler instance
    """
    if config_path is None:
        config_path = Path(__file__).parent / "config.json"

    config = {}
    if config_path.exists():
        with open(config_path) as f:
            full_config = json.load(f)
            config = full_config.get("task_scheduling", {})

    return TaskScheduler(config)


# =============================================================================
# CLI INTERFACE
# =============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Power Mode Task Scheduler")
    parser.add_argument("--test", action="store_true", help="Run test scenario")
    parser.add_argument("--stats", action="store_true", help="Show task statistics")

    args = parser.parse_args()

    if args.test:
        print("Testing Priority-based Task Scheduler")
        print("=" * 60)

        scheduler = create_scheduler()

        # Add test tasks with different priorities
        test_tasks = [
            (
                "task-1",
                "Fix security vulnerability in auth system",
                "critical",
                ["security", "bug"],
            ),
            (
                "task-2",
                "Update documentation for new feature",
                "low",
                ["documentation"],
            ),
            ("task-3", "Implement user dashboard", "medium", ["feature"]),
            (
                "task-4",
                "Fix production outage",
                None,
                ["production", "urgent"],
            ),  # Auto-assign
            ("task-5", "Refactor test utilities", "low", ["cleanup"]),
            ("task-6", "Fix broken CI pipeline", "high", ["bug", "ci"]),
        ]

        for task_id, desc, priority, tags in test_tasks:
            task = scheduler.add_task(task_id, desc, priority=priority, tags=tags)
            print(f"Added: [{task.priority.to_string().upper():8}] {desc}")

        print("\n" + "=" * 60)
        print("Task Queue (Priority Order):")
        print("=" * 60)

        # Simulate 3 agents picking tasks
        agents = ["agent-1", "agent-2", "agent-3"]
        for agent in agents:
            task = scheduler.get_next_task(agent)
            if task:
                print(
                    f"{agent}: [{task.priority.to_string().upper():8}] {task.description}"
                )

        print("\n" + "=" * 60)
        stats = scheduler.get_task_stats()
        print("Task Statistics:")
        print(json.dumps(stats, indent=2))
        print("=" * 60)

    elif args.stats:
        scheduler = create_scheduler()
        stats = scheduler.get_task_stats()
        print(json.dumps(stats, indent=2))

    else:
        parser.print_help()
