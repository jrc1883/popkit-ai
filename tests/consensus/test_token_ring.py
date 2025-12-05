#!/usr/bin/env python3
"""
Tests for Token Ring Manager.
"""

import pytest
import time
from threading import Event

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "power-mode"))

from consensus.coordinator import TokenRingManager


class TestTokenRingManager:
    """Test TokenRingManager functionality."""

    def test_initialization(self):
        """Test token ring initialization."""
        manager = TokenRingManager(timeout_seconds=60)
        manager.initialize(["agent-1", "agent-2", "agent-3"])

        assert manager.get_turn_order() == ["agent-1", "agent-2", "agent-3"]
        assert manager.get_current_holder() is None

    def test_grant_token(self):
        """Test token granting."""
        manager = TokenRingManager()
        manager.initialize(["agent-1", "agent-2"])

        holder = manager.grant_token()
        assert holder == "agent-1"
        assert manager.get_current_holder() == "agent-1"

    def test_release_token(self):
        """Test token release."""
        manager = TokenRingManager()
        manager.initialize(["agent-1", "agent-2"])

        manager.grant_token()
        result = manager.release_token("agent-1")

        assert result is True
        assert manager.get_current_holder() is None

    def test_release_wrong_agent(self):
        """Test that wrong agent cannot release token."""
        manager = TokenRingManager()
        manager.initialize(["agent-1", "agent-2"])

        manager.grant_token()  # agent-1 has token
        result = manager.release_token("agent-2")

        assert result is False
        assert manager.get_current_holder() == "agent-1"

    def test_round_robin_order(self):
        """Test round robin token passing."""
        manager = TokenRingManager()
        manager.initialize(["agent-1", "agent-2", "agent-3"])

        # First round
        holder = manager.grant_token()
        assert holder == "agent-1"
        manager.release_token("agent-1")

        holder = manager.grant_token()
        assert holder == "agent-2"
        manager.release_token("agent-2")

        holder = manager.grant_token()
        assert holder == "agent-3"
        manager.release_token("agent-3")

        # Second round - back to start
        holder = manager.grant_token()
        assert holder == "agent-1"

    def test_skip_turn(self):
        """Test skipping a turn."""
        manager = TokenRingManager()
        manager.initialize(["agent-1", "agent-2"])

        manager.grant_token()  # agent-1
        result = manager.skip_turn("agent-1")

        assert result is True
        assert "agent-1" in manager.state.skipped_agents

    def test_add_participant(self):
        """Test adding participant to ring."""
        manager = TokenRingManager()
        manager.initialize(["agent-1", "agent-2"])

        manager.add_participant("agent-3")

        assert "agent-3" in manager.get_turn_order()
        assert len(manager.get_turn_order()) == 3

    def test_add_participant_position(self):
        """Test adding participant at specific position."""
        manager = TokenRingManager()
        manager.initialize(["agent-1", "agent-3"])

        manager.add_participant("agent-2", position=1)

        order = manager.get_turn_order()
        assert order[1] == "agent-2"

    def test_remove_participant(self):
        """Test removing participant."""
        manager = TokenRingManager()
        manager.initialize(["agent-1", "agent-2", "agent-3"])

        manager.remove_participant("agent-2")

        assert "agent-2" not in manager.get_turn_order()
        assert len(manager.get_turn_order()) == 2

    def test_remove_participant_adjusts_index(self):
        """Test that removing participant adjusts current index."""
        manager = TokenRingManager()
        manager.initialize(["agent-1", "agent-2", "agent-3"])

        # Advance to agent-2
        manager.grant_token()
        manager.release_token("agent-1")
        manager.grant_token()  # Now at agent-2

        # Remove agent-1 (before current index)
        manager.release_token("agent-2")
        manager.remove_participant("agent-1")

        # Next should be agent-3
        holder = manager.grant_token()
        assert holder == "agent-3"

    def test_round_complete(self):
        """Test round completion detection."""
        manager = TokenRingManager()
        manager.initialize(["agent-1", "agent-2"])

        assert manager.is_round_complete() is False

        manager.grant_token()
        manager.release_token("agent-1")
        assert manager.is_round_complete() is False

        manager.grant_token()
        manager.release_token("agent-2")
        assert manager.is_round_complete() is True

    def test_remaining_this_round(self):
        """Test getting remaining agents for current round."""
        manager = TokenRingManager()
        manager.initialize(["agent-1", "agent-2", "agent-3"])

        remaining = manager.get_remaining_this_round()
        assert remaining == ["agent-1", "agent-2", "agent-3"]

        manager.grant_token()
        manager.release_token("agent-1")

        remaining = manager.get_remaining_this_round()
        assert remaining == ["agent-2", "agent-3"]

    def test_timeout_callback(self):
        """Test timeout callback is called."""
        timeout_event = Event()
        timed_out_agent = []

        def on_timeout(agent_id):
            timed_out_agent.append(agent_id)
            timeout_event.set()

        manager = TokenRingManager(timeout_seconds=0.1)  # 100ms timeout
        manager.initialize(["agent-1", "agent-2"])

        manager.grant_token(on_timeout=on_timeout)

        # Wait for timeout
        timeout_event.wait(timeout=1.0)

        assert len(timed_out_agent) == 1
        assert timed_out_agent[0] == "agent-1"

    def test_empty_ring(self):
        """Test behavior with empty ring."""
        manager = TokenRingManager()
        manager.initialize([])

        holder = manager.grant_token()
        assert holder is None

    def test_duplicate_participant(self):
        """Test adding duplicate participant."""
        manager = TokenRingManager()
        manager.initialize(["agent-1", "agent-2"])

        manager.add_participant("agent-1")  # Already exists

        # Should not add duplicate
        assert manager.get_turn_order().count("agent-1") == 1


class TestTokenRingIntegration:
    """Integration tests for token ring with consensus."""

    def test_full_round_simulation(self):
        """Simulate a full round of discussion."""
        manager = TokenRingManager(timeout_seconds=60)
        participants = ["reviewer", "architect", "optimizer"]
        manager.initialize(participants)

        contributions = []

        for round_num in range(2):
            for agent in participants:
                holder = manager.grant_token()
                assert holder == agent

                # Simulate contribution
                contributions.append({
                    "agent": holder,
                    "round": round_num + 1,
                    "content": f"{agent}'s thought in round {round_num + 1}"
                })

                manager.release_token(holder)

        assert len(contributions) == 6
        assert contributions[0]["agent"] == "reviewer"
        assert contributions[3]["agent"] == "reviewer"  # Second round

    def test_mixed_skip_contribute(self):
        """Test mix of skips and contributions."""
        manager = TokenRingManager()
        manager.initialize(["agent-1", "agent-2", "agent-3"])

        # Agent 1 contributes
        manager.grant_token()
        manager.release_token("agent-1")

        # Agent 2 skips
        manager.grant_token()
        manager.skip_turn("agent-2")

        # Agent 3 contributes
        holder = manager.grant_token()
        assert holder == "agent-3"

        assert "agent-2" in manager.state.skipped_agents
        assert "agent-1" not in manager.state.skipped_agents


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
