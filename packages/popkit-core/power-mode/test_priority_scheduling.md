# Priority-Based Task Scheduling - Test Documentation

## Overview

Tests for Issue #193 - Power Mode Phase 1 priority scheduling implementation.

## Quick Test

Run the built-in test scenario:

```bash
cd packages/popkit-core/power-mode
python task_scheduler.py --test
```

### Expected Output

```
Priority-Based Task Scheduler Test
===================================

Scenario: 3 agents, 6 tasks with mixed priorities

Adding tasks to scheduler...
  [CRITICAL] Security vulnerability in auth module (security, urgent)
  [CRITICAL] Production API returning 500 errors (production, p0)
  [HIGH    ] Implement user dashboard feature (bug, deadline)
  [MEDIUM  ] Refactor database queries
  [LOW     ] Update API documentation (docs)
  [LOW     ] Code cleanup in utils module (cleanup)

Agent Assignment Simulation
============================

Agent-1 assigned: Security vulnerability in auth module
  Priority: CRITICAL (4)
  Tags: ['security', 'urgent']

Agent-2 assigned: Production API returning 500 errors
  Priority: CRITICAL (4)
  Tags: ['production', 'p0']

Agent-3 assigned: Implement user dashboard feature
  Priority: HIGH (3)
  Tags: ['bug', 'deadline']

Waiting for agents to complete...

Agent-1 assigned: Refactor database queries
  Priority: MEDIUM (2)
  Tags: []

Agent-2 assigned: Update API documentation
  Priority: LOW (1)
  Tags: ['docs']

Agent-3 assigned: Code cleanup in utils module
  Priority: LOW (1)
  Tags: ['cleanup']

All tasks completed!

Test Results
============
✓ CRITICAL tasks assigned first
✓ HIGH tasks assigned before MEDIUM/LOW
✓ Priority ordering maintained
✓ All tasks completed

Test PASSED
```

### Verification Checklist

- [ ] CRITICAL tasks (security, production) assigned before others
- [ ] HIGH tasks assigned before MEDIUM/LOW
- [ ] MEDIUM and LOW tasks assigned only after higher priorities
- [ ] Same-priority tasks follow FIFO order
- [ ] All 6 tasks completed

## Manual Testing

### Test 1: Priority Assignment

Test automatic priority detection from keywords:

```python
from task_scheduler import TaskScheduler

scheduler = TaskScheduler()

# Should be CRITICAL (has "security" keyword)
scheduler.add_task(
    task_id="task-1",
    description="Fix security vulnerability in auth",
    tags=["backend"]
)

# Should be HIGH (has "bug" keyword)
scheduler.add_task(
    task_id="task-2",
    description="Important bug in payment flow",
    tags=[]
)

# Should be LOW (has "documentation" keyword)
scheduler.add_task(
    task_id="task-3",
    description="Update documentation for API",
    tags=[]
)

# Verify priorities
task1 = scheduler.get_task("task-1")
task2 = scheduler.get_task("task-2")
task3 = scheduler.get_task("task-3")

assert task1.priority.value == 4  # CRITICAL
assert task2.priority.value == 3  # HIGH
assert task3.priority.value == 1  # LOW

print("✓ Priority assignment test passed")
```

### Test 2: Tag-Based Priority

Test priority detection from tags:

```python
from task_scheduler import TaskScheduler

scheduler = TaskScheduler()

# Should be CRITICAL (has "p0" tag)
scheduler.add_task(
    task_id="task-1",
    description="Regular task",
    tags=["p0", "backend"]
)

# Should be HIGH (has "deadline" tag)
scheduler.add_task(
    task_id="task-2",
    description="Regular task",
    tags=["deadline"]
)

# Should be LOW (has "docs" tag)
scheduler.add_task(
    task_id="task-3",
    description="Regular task",
    tags=["docs"]
)

task1 = scheduler.get_task("task-1")
task2 = scheduler.get_task("task-2")
task3 = scheduler.get_task("task-3")

assert task1.priority.value == 4  # CRITICAL
assert task2.priority.value == 3  # HIGH
assert task3.priority.value == 1  # LOW

print("✓ Tag-based priority test passed")
```

### Test 3: Explicit Priority Override

Test explicit priority parameter:

```python
from task_scheduler import TaskScheduler, TaskPriority

scheduler = TaskScheduler()

# Explicit CRITICAL, even without keywords
scheduler.add_task(
    task_id="task-1",
    description="Regular task",
    priority="critical"
)

# Explicit LOW, even with "important" keyword
scheduler.add_task(
    task_id="task-2",
    description="Important task",
    priority="low"
)

task1 = scheduler.get_task("task-1")
task2 = scheduler.get_task("task-2")

assert task1.priority.value == 4  # CRITICAL
assert task2.priority.value == 1  # LOW

print("✓ Explicit priority override test passed")
```

### Test 4: Task Ordering

Test that higher priority tasks are returned first:

```python
from task_scheduler import TaskScheduler

scheduler = TaskScheduler()

# Add in reverse priority order
scheduler.add_task(task_id="low-1", description="Documentation update", tags=["docs"])
scheduler.add_task(task_id="med-1", description="Refactor code")
scheduler.add_task(task_id="high-1", description="Important bug fix", tags=["bug"])
scheduler.add_task(task_id="crit-1", description="Security fix", tags=["security"])

# Get tasks - should be in priority order
task1 = scheduler.get_next_task()
task2 = scheduler.get_next_task()
task3 = scheduler.get_next_task()
task4 = scheduler.get_next_task()

assert task1.id == "crit-1"  # CRITICAL first
assert task2.id == "high-1"  # HIGH second
assert task3.id == "med-1"   # MEDIUM third
assert task4.id == "low-1"   # LOW last

print("✓ Task ordering test passed")
```

### Test 5: FIFO Within Same Priority

Test that same-priority tasks follow FIFO order:

```python
from task_scheduler import TaskScheduler
import time

scheduler = TaskScheduler()

# Add 3 MEDIUM priority tasks
scheduler.add_task(task_id="med-1", description="First medium task")
time.sleep(0.01)  # Ensure different timestamps
scheduler.add_task(task_id="med-2", description="Second medium task")
time.sleep(0.01)
scheduler.add_task(task_id="med-3", description="Third medium task")

task1 = scheduler.get_next_task()
task2 = scheduler.get_next_task()
task3 = scheduler.get_next_task()

assert task1.id == "med-1"  # First added
assert task2.id == "med-2"  # Second added
assert task3.id == "med-3"  # Third added

print("✓ FIFO within same priority test passed")
```

### Test 6: Agent Assignment

Test agent assignment tracking:

```python
from task_scheduler import TaskScheduler

scheduler = TaskScheduler()

scheduler.add_task(task_id="task-1", description="First task", tags=["security"])
scheduler.add_task(task_id="task-2", description="Second task", tags=["bug"])

# Assign to agents
task1 = scheduler.get_next_task(agent_id="agent-1")
task2 = scheduler.get_next_task(agent_id="agent-2")

assert task1.assigned_agent == "agent-1"
assert task2.assigned_agent == "agent-2"

# Verify agent assignments tracked
assert scheduler.agent_assignments["agent-1"] == "task-1"
assert scheduler.agent_assignments["agent-2"] == "task-2"

print("✓ Agent assignment test passed")
```

### Test 7: Task Completion

Test task completion and stats:

```python
from task_scheduler import TaskScheduler

scheduler = TaskScheduler()

scheduler.add_task(task_id="task-1", description="First task", tags=["security"])
task = scheduler.get_next_task(agent_id="agent-1")

# Complete the task
scheduler.complete_task("task-1")

completed_task = scheduler.get_task("task-1")
assert completed_task.completed_at is not None

# Check stats
stats = scheduler.get_stats()
assert stats["completed"] == 1
assert stats["remaining"] == 0

print("✓ Task completion test passed")
```

## Integration Testing

### Test with Power Mode Coordinator

```python
# Example integration with power mode coordinator
from task_scheduler import TaskScheduler, TaskPriority

class PowerModeCoordinator:
    def __init__(self):
        self.scheduler = TaskScheduler()

    def assign_work(self):
        """Assign next highest-priority task to available agent"""
        available_agents = self.get_available_agents()

        for agent in available_agents:
            task = self.scheduler.get_next_task(agent_id=agent.id)
            if task:
                self.send_task_to_agent(agent, task)

    def on_task_complete(self, task_id: str):
        """Mark task as complete and reassign agent"""
        self.scheduler.complete_task(task_id)
        self.assign_work()  # Assign next task
```

## Performance Testing

### Test Large Task Queue

```bash
python task_scheduler.py --test --tasks 1000
```

Expected performance:
- Add 1000 tasks: < 100ms
- Get next task: < 5ms (O(log n) with heapq)
- Complete task: < 1ms

## Configuration Testing

### Test Custom Priority Rules

Create custom config.json with different keywords:

```json
{
  "task_scheduling": {
    "priority_rules": {
      "critical_keywords": ["p0", "sev1", "outage"],
      "high_keywords": ["p1", "sev2"],
      "low_keywords": ["p3", "sev4", "backlog"]
    }
  }
}
```

Test that custom keywords work:

```python
from task_scheduler import TaskScheduler

scheduler = TaskScheduler(config={"task_scheduling": {...}})

scheduler.add_task(task_id="t1", description="P0 incident - outage")
scheduler.add_task(task_id="t2", description="P1 bug fix")
scheduler.add_task(task_id="t3", description="P3 backlog item")

task1 = scheduler.get_task("t1")
task2 = scheduler.get_task("t2")
task3 = scheduler.get_task("t3")

assert task1.priority.value == 4  # CRITICAL
assert task2.priority.value == 3  # HIGH
assert task3.priority.value == 1  # LOW
```

## Troubleshooting

### Issue: Tasks not assigned in priority order

**Check:**
1. Verify priority assignment: `task.priority.value`
2. Check task timestamps: `task.created_at`
3. Verify heapq is working: `print(scheduler.task_queue)`

### Issue: Same-priority tasks not following FIFO

**Check:**
1. Timestamps are different: `task.created_at`
2. Task.__lt__() comparison logic
3. Time precision (use time.time() not datetime)

### Issue: Priority rules not working

**Check:**
1. Config loaded correctly: `scheduler.priority_assigner.config`
2. Keywords in description: case-insensitive matching
3. Tags in task: exact match required

## Acceptance Criteria

- [x] Task scheduler created with 4 priority levels
- [x] Automatic priority assignment from keywords
- [x] Automatic priority assignment from tags
- [x] Explicit priority override works
- [x] Higher priority tasks returned first
- [x] Same-priority tasks follow FIFO order
- [x] Agent assignment tracked
- [x] Task completion tracked
- [x] Statistics reporting works
- [x] O(log n) performance with heapq
- [x] Configuration-driven priority rules
- [x] CLI test interface works

## Next Steps (Future Phases)

- [ ] Phase 2: Inter-agent dependencies
- [ ] Phase 3: Dynamic reprioritization
- [ ] Phase 4: Load balancing
- [ ] Phase 5: Deadline-aware scheduling
