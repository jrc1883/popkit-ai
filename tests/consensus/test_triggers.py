#!/usr/bin/env python3
"""
Tests for consensus trigger mechanisms.
"""

import pytest
from datetime import datetime, timedelta

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "power-mode"))

from consensus.protocol import TriggerType
from consensus.triggers import (
    TriggerConfig, TriggerContext,
    UserRequestTrigger, AgentRequestTrigger, ConflictTrigger,
    ThresholdTrigger, CheckpointTrigger, PhaseTransitionTrigger,
    ScheduledTrigger, TriggerManager
)


class TestTriggerConfig:
    """Test trigger configuration."""

    def test_default_config(self):
        """Test default configuration."""
        config = TriggerConfig()
        assert config.enabled is True
        assert config.priority == "normal"
        assert config.cooldown_seconds == 300

    def test_custom_config(self):
        """Test custom configuration."""
        config = TriggerConfig(
            enabled=False,
            priority="high",
            cooldown_seconds=60
        )
        assert config.enabled is False
        assert config.priority == "high"


class TestTriggerContext:
    """Test trigger context data class."""

    def test_creation(self):
        """Test context creation."""
        context = TriggerContext(
            trigger_type=TriggerType.USER_REQUESTED,
            source="user",
            topic="Test topic",
            description="Test description"
        )
        assert context.trigger_type == TriggerType.USER_REQUESTED
        assert context.priority == "normal"

    def test_serialization(self):
        """Test context serialization."""
        context = TriggerContext(
            trigger_type=TriggerType.AGENT_REQUESTED,
            source="agent-1",
            topic="Architecture",
            description="Need consensus",
            suggested_agents=["agent-2", "agent-3"]
        )
        data = context.to_dict()

        assert data["trigger_type"] == "agent_requested"
        assert len(data["suggested_agents"]) == 2


class TestUserRequestTrigger:
    """Test user request trigger."""

    def test_request(self):
        """Test user request."""
        trigger = UserRequestTrigger()

        context = trigger.request(
            topic="API Design",
            agents=["agent-1", "agent-2"],
            description="Choose REST or GraphQL",
            priority="high"
        )

        assert context is not None
        assert context.trigger_type == TriggerType.USER_REQUESTED
        assert context.topic == "API Design"
        assert context.priority == "high"

    def test_check_with_flag(self):
        """Test check method with user_requested flag."""
        trigger = UserRequestTrigger()

        context = trigger.check({
            "user_requested": True,
            "topic": "Test",
            "agents": ["agent-1"]
        })

        assert context is not None

    def test_check_without_flag(self):
        """Test check method without flag."""
        trigger = UserRequestTrigger()

        context = trigger.check({
            "topic": "Test"
        })

        assert context is None


class TestAgentRequestTrigger:
    """Test agent request trigger."""

    def test_valid_request(self):
        """Test valid agent request."""
        trigger = AgentRequestTrigger()

        context = trigger.check({
            "agent_id": "code-architect",
            "reason": "Need consensus on architecture decision",
            "confidence": 0.8,
            "topic": "Architecture"
        })

        assert context is not None
        assert context.trigger_type == TriggerType.AGENT_REQUESTED
        assert context.source == "code-architect"

    def test_invalid_reason(self):
        """Test request with invalid reason."""
        trigger = AgentRequestTrigger()

        context = trigger.check({
            "agent_id": "agent-1",
            "reason": "Just because",  # No valid keywords
            "confidence": 0.8
        })

        assert context is None

    def test_low_confidence(self):
        """Test request with low confidence."""
        trigger = AgentRequestTrigger()

        context = trigger.check({
            "agent_id": "agent-1",
            "reason": "Architecture decision needed",
            "confidence": 0.3  # Below threshold
        })

        assert context is None

    def test_various_valid_reasons(self):
        """Test various valid reason keywords."""
        trigger = AgentRequestTrigger()

        valid_reasons = [
            "Architecture decision needed",
            "Design conflict detected",
            "Conflicting approaches",
            "Security trade-off",
            "Performance decision"
        ]

        for reason in valid_reasons:
            context = trigger.check({
                "agent_id": "agent-1",
                "reason": reason,
                "confidence": 0.7
            })
            assert context is not None, f"Should accept: {reason}"


class TestConflictTrigger:
    """Test conflict detection trigger."""

    def test_file_conflict_detection(self):
        """Test file edit conflict detection."""
        trigger = ConflictTrigger()

        # Record conflicting edits
        trigger.record_output("agent-1", {"file_path": "src/api.ts", "change_type": "edit"})
        trigger.record_output("agent-2", {"file_path": "src/api.ts", "change_type": "edit"})
        trigger.record_output("agent-3", {"file_path": "src/utils.ts", "change_type": "edit"})

        context = trigger.check({})

        assert context is not None
        assert context.trigger_type == TriggerType.CONFLICT_DETECTED
        assert "src/api.ts" in context.description

    def test_opinion_conflict_detection(self):
        """Test opinion conflict detection."""
        trigger = ConflictTrigger()

        trigger.record_output("agent-1", {
            "opinion_on": "architecture",
            "stance": "approve"
        })
        trigger.record_output("agent-2", {
            "opinion_on": "architecture",
            "stance": "reject"
        })

        context = trigger.check({})

        assert context is not None
        assert "architecture" in context.description.lower() or "opinion" in context.description.lower()

    def test_no_conflict(self):
        """Test when there's no conflict."""
        trigger = ConflictTrigger()

        trigger.record_output("agent-1", {"file_path": "src/a.ts"})
        trigger.record_output("agent-2", {"file_path": "src/b.ts"})

        context = trigger.check({})

        assert context is None


class TestThresholdTrigger:
    """Test threshold-based trigger."""

    def test_threshold_exceeded(self):
        """Test trigger when threshold exceeded."""
        trigger = ThresholdTrigger(threshold=0.6)
        trigger.update_value(0.8)

        context = trigger.check({})

        assert context is not None
        assert context.trigger_type == TriggerType.THRESHOLD_EXCEEDED

    def test_threshold_not_exceeded(self):
        """Test no trigger when below threshold."""
        trigger = ThresholdTrigger(threshold=0.6)
        trigger.update_value(0.4)

        context = trigger.check({})

        assert context is None

    def test_context_override(self):
        """Test value override in context."""
        trigger = ThresholdTrigger(threshold=0.6)
        trigger.update_value(0.3)  # Below threshold

        # But context provides higher value
        context = trigger.check({"value": 0.9})

        assert context is not None

    def test_history_tracking(self):
        """Test value history tracking."""
        trigger = ThresholdTrigger(threshold=0.6)

        for i in range(5):
            trigger.update_value(i * 0.1)

        assert len(trigger.history) == 5
        assert trigger.history[-1] == 0.4


class TestCheckpointTrigger:
    """Test checkpoint-based trigger."""

    def test_mandatory_checkpoint(self):
        """Test mandatory checkpoint types."""
        trigger = CheckpointTrigger()

        mandatory = [
            "architecture_decision",
            "security_change",
            "api_design"
        ]

        for checkpoint in mandatory:
            context = trigger.check({
                "checkpoint_type": checkpoint
            })
            assert context is not None, f"Should trigger for: {checkpoint}"

    def test_optional_checkpoint_without_flag(self):
        """Test optional checkpoint without requires_consensus flag."""
        trigger = CheckpointTrigger()

        context = trigger.check({
            "checkpoint_type": "regular_commit"
        })

        assert context is None

    def test_optional_checkpoint_with_flag(self):
        """Test optional checkpoint with requires_consensus flag."""
        trigger = CheckpointTrigger()

        context = trigger.check({
            "checkpoint_type": "regular_commit",
            "requires_consensus": True
        })

        assert context is not None


class TestPhaseTransitionTrigger:
    """Test phase transition trigger."""

    def test_consensus_phase_transition(self):
        """Test transition from consensus-required phase."""
        trigger = PhaseTransitionTrigger()

        context = trigger.check({
            "current_phase": "design",
            "next_phase": "implement",
            "active_agents": ["agent-1", "agent-2"]
        })

        assert context is not None
        assert "design" in context.topic

    def test_non_consensus_phase(self):
        """Test transition from non-consensus phase."""
        trigger = PhaseTransitionTrigger()

        context = trigger.check({
            "current_phase": "test",
            "next_phase": "deploy"
        })

        assert context is None

    def test_missing_phases(self):
        """Test with missing phase information."""
        trigger = PhaseTransitionTrigger()

        context = trigger.check({})

        assert context is None


class TestScheduledTrigger:
    """Test scheduled trigger."""

    def test_initial_trigger(self):
        """Test first scheduled check."""
        trigger = ScheduledTrigger(interval_minutes=30)

        context = trigger.check({
            "pending_decisions": ["decision-1"],
            "active_agents": ["agent-1", "agent-2"]
        })

        assert context is not None
        assert context.priority == "low"

    def test_cooldown_period(self):
        """Test trigger respects interval."""
        trigger = ScheduledTrigger(interval_minutes=30)

        # First check
        trigger.check({
            "pending_decisions": ["d1"],
            "active_agents": ["a1", "a2"]
        })

        # Immediate second check should fail
        context = trigger.check({
            "pending_decisions": ["d1"],
            "active_agents": ["a1", "a2"]
        })

        assert context is None

    def test_no_pending_decisions(self):
        """Test no trigger without pending decisions."""
        trigger = ScheduledTrigger(interval_minutes=30)

        context = trigger.check({
            "pending_decisions": [],
            "active_agents": ["agent-1", "agent-2"]
        })

        assert context is None


class TestTriggerManager:
    """Test trigger manager."""

    def test_initialization(self):
        """Test manager initializes with default triggers."""
        manager = TriggerManager()

        status = manager.get_trigger_status()

        assert TriggerType.USER_REQUESTED.value in status
        assert TriggerType.AGENT_REQUESTED.value in status
        assert TriggerType.CONFLICT_DETECTED.value in status

    def test_check_all(self):
        """Test checking all triggers."""
        manager = TriggerManager()

        # This should trigger user requested
        results = manager.check_all({
            "user_requested": True,
            "topic": "Test"
        })

        assert len(results) >= 1
        assert any(r.trigger_type == TriggerType.USER_REQUESTED for r in results)

    def test_trigger_by_type(self):
        """Test triggering specific type."""
        manager = TriggerManager()

        context = manager.trigger_by_type(
            TriggerType.USER_REQUESTED,
            {"user_requested": True, "topic": "Test"}
        )

        assert context is not None
        assert context.trigger_type == TriggerType.USER_REQUESTED

    def test_callback_registration(self):
        """Test callback is called on trigger."""
        manager = TriggerManager()
        triggered = []

        def callback(ctx):
            triggered.append(ctx)

        manager.on_trigger(callback)

        manager.check_all({
            "user_requested": True,
            "topic": "Test"
        })

        assert len(triggered) >= 1

    def test_global_cooldown(self):
        """Test global cooldown between triggers."""
        manager = TriggerManager()
        manager.global_cooldown_seconds = 10

        # First trigger
        results1 = manager.check_all({
            "user_requested": True,
            "topic": "Test 1"
        })

        # Immediate second trigger should be blocked by cooldown
        results2 = manager.check_all({
            "user_requested": True,
            "topic": "Test 2"
        })

        assert len(results1) >= 1
        assert len(results2) == 0


class TestTriggerCooldowns:
    """Test trigger cooldown behavior."""

    def test_can_trigger_initially(self):
        """Test trigger is available initially."""
        trigger = UserRequestTrigger()
        assert trigger.can_trigger() is True

    def test_cooldown_after_trigger(self):
        """Test cooldown prevents immediate re-trigger."""
        trigger = UserRequestTrigger(TriggerConfig(cooldown_seconds=60))

        trigger.request("Topic", ["agent-1"])

        assert trigger.can_trigger() is False

    def test_disabled_trigger(self):
        """Test disabled trigger cannot fire."""
        trigger = UserRequestTrigger(TriggerConfig(enabled=False))

        assert trigger.can_trigger() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
