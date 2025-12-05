#!/usr/bin/env python3
"""
Tests for consensus protocol data structures and message handling.
"""

import json
import pytest
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "power-mode"))

from consensus.protocol import (
    ConsensusMessageType, ConsensusPhase, VoteType, TriggerType, ReactionType,
    ConsensusSession, ConsensusMessage, ConsensusParticipant, Contribution,
    Proposal, Amendment, Vote, TokenState, ConsensusRules,
    ConsensusMessageFactory, ConsensusChannels,
    create_session, calculate_vote_result
)


class TestEnums:
    """Test enum definitions."""

    def test_message_types_exist(self):
        """Verify all message types are defined."""
        assert ConsensusMessageType.CONSENSUS_START
        assert ConsensusMessageType.TOKEN_GRANT
        assert ConsensusMessageType.TOKEN_RELEASE
        assert ConsensusMessageType.CONTRIBUTION
        assert ConsensusMessageType.PROPOSAL
        assert ConsensusMessageType.VOTE
        assert ConsensusMessageType.CONSENSUS_REACHED

    def test_phases_exist(self):
        """Verify all phases are defined."""
        assert ConsensusPhase.GATHERING
        assert ConsensusPhase.PROPOSING
        assert ConsensusPhase.DISCUSSING
        assert ConsensusPhase.CONVERGING
        assert ConsensusPhase.VOTING
        assert ConsensusPhase.COMMITTED
        assert ConsensusPhase.ABORTED

    def test_vote_types_exist(self):
        """Verify all vote types are defined."""
        assert VoteType.APPROVE
        assert VoteType.APPROVE_WITH_CONCERNS
        assert VoteType.ABSTAIN
        assert VoteType.REQUEST_CHANGES
        assert VoteType.REJECT

    def test_trigger_types_exist(self):
        """Verify all trigger types are defined."""
        assert TriggerType.USER_REQUESTED
        assert TriggerType.AGENT_REQUESTED
        assert TriggerType.MONITOR_DETECTED
        assert TriggerType.CONFLICT_DETECTED
        assert TriggerType.CHECKPOINT_REACHED


class TestConsensusParticipant:
    """Test ConsensusParticipant data class."""

    def test_creation(self):
        """Test participant creation."""
        participant = ConsensusParticipant(
            agent_id="agent-1",
            agent_name="code-reviewer"
        )
        assert participant.agent_id == "agent-1"
        assert participant.agent_name == "code-reviewer"
        assert participant.is_active is True
        assert participant.contributions == 0

    def test_serialization(self):
        """Test participant serialization/deserialization."""
        participant = ConsensusParticipant(
            agent_id="agent-1",
            agent_name="code-reviewer",
            contributions=5
        )

        data = participant.to_dict()
        restored = ConsensusParticipant.from_dict(data)

        assert restored.agent_id == participant.agent_id
        assert restored.contributions == participant.contributions


class TestContribution:
    """Test Contribution data class."""

    def test_creation(self):
        """Test contribution creation."""
        contrib = Contribution(
            id="contrib-1",
            author_id="agent-1",
            author_name="code-reviewer",
            content="I think we should use REST for simplicity.",
            contribution_type="opinion",
            round_number=1
        )
        assert contrib.id == "contrib-1"
        assert contrib.contribution_type == "opinion"
        assert contrib.confidence == 0.5

    def test_references(self):
        """Test contribution with references."""
        contrib = Contribution(
            id="contrib-2",
            author_id="agent-2",
            author_name="api-designer",
            content="Building on previous point...",
            contribution_type="synthesis",
            round_number=2,
            references=["contrib-1"]
        )
        assert "contrib-1" in contrib.references


class TestProposal:
    """Test Proposal data class."""

    def test_creation(self):
        """Test proposal creation."""
        proposal = Proposal(
            id="prop-1",
            author_id="agent-1",
            title="Use REST API",
            description="Implement REST endpoints for the service",
            rationale="REST is simpler and has better caching"
        )
        assert proposal.status == "pending"
        assert len(proposal.votes) == 0

    def test_serialization(self):
        """Test proposal serialization with votes."""
        proposal = Proposal(
            id="prop-1",
            author_id="agent-1",
            title="Use REST",
            description="...",
            rationale="..."
        )

        vote = Vote(
            agent_id="agent-2",
            vote_type=VoteType.APPROVE,
            rationale="I agree"
        )
        proposal.votes["agent-2"] = vote

        data = proposal.to_dict()
        restored = Proposal.from_dict(data)

        assert "agent-2" in restored.votes
        assert restored.votes["agent-2"].vote_type == VoteType.APPROVE


class TestVote:
    """Test Vote data class."""

    def test_creation(self):
        """Test vote creation."""
        vote = Vote(
            agent_id="agent-1",
            vote_type=VoteType.APPROVE_WITH_CONCERNS,
            rationale="Good overall but needs error handling",
            conditions=["Add retry logic"]
        )
        assert vote.vote_type == VoteType.APPROVE_WITH_CONCERNS
        assert len(vote.conditions) == 1

    def test_serialization(self):
        """Test vote serialization."""
        vote = Vote(
            agent_id="agent-1",
            vote_type=VoteType.REQUEST_CHANGES,
            requested_changes=["Fix security issue"]
        )

        data = vote.to_dict()
        assert data["vote_type"] == "request_changes"

        restored = Vote.from_dict(data)
        assert restored.vote_type == VoteType.REQUEST_CHANGES


class TestTokenState:
    """Test TokenState data class."""

    def test_creation(self):
        """Test token state creation."""
        state = TokenState(
            turn_order=["agent-1", "agent-2", "agent-3"],
            timeout_seconds=60
        )
        assert len(state.turn_order) == 3
        assert state.current_holder is None

    def test_serialization(self):
        """Test token state serialization with set."""
        state = TokenState(
            turn_order=["agent-1", "agent-2"],
            skipped_agents={"agent-2"}
        )

        data = state.to_dict()
        assert "agent-2" in data["skipped_agents"]

        restored = TokenState.from_dict(data)
        assert "agent-2" in restored.skipped_agents


class TestConsensusSession:
    """Test ConsensusSession data class."""

    def test_creation(self):
        """Test session creation."""
        session = create_session(
            topic="API Design",
            description="Choose between REST and GraphQL",
            trigger_type=TriggerType.USER_REQUESTED
        )
        assert session.topic == "API Design"
        assert session.phase == ConsensusPhase.GATHERING
        assert len(session.id) > 0

    def test_full_serialization(self):
        """Test full session serialization."""
        session = create_session(
            topic="Test Topic",
            description="Test description",
            trigger_type=TriggerType.AGENT_REQUESTED
        )

        # Add participant
        session.participants["agent-1"] = ConsensusParticipant(
            agent_id="agent-1",
            agent_name="reviewer"
        )

        # Add contribution
        session.contributions.append(Contribution(
            id="c-1",
            author_id="agent-1",
            author_name="reviewer",
            content="Test content",
            contribution_type="opinion",
            round_number=1
        ))

        # Add proposal
        session.proposals["p-1"] = Proposal(
            id="p-1",
            author_id="agent-1",
            title="Test Proposal",
            description="...",
            rationale="..."
        )

        data = session.to_dict()
        restored = ConsensusSession.from_dict(data)

        assert restored.topic == session.topic
        assert len(restored.participants) == 1
        assert len(restored.contributions) == 1
        assert len(restored.proposals) == 1


class TestConsensusRules:
    """Test ConsensusRules configuration."""

    def test_default_rules(self):
        """Test default rules."""
        rules = ConsensusRules()
        assert rules.quorum_percentage == 0.67
        assert rules.approval_threshold == 0.60
        assert rules.max_rounds == 5

    def test_permissive_rules(self):
        """Test permissive preset."""
        rules = ConsensusRules.permissive()
        assert rules.quorum_percentage == 0.50
        assert rules.max_rounds == 3

    def test_strict_rules(self):
        """Test strict preset."""
        rules = ConsensusRules.strict()
        assert rules.quorum_percentage == 0.80
        assert rules.early_consensus_threshold == 0.95


class TestConsensusMessage:
    """Test ConsensusMessage data class."""

    def test_creation(self):
        """Test message creation."""
        msg = ConsensusMessage(
            id="msg-1",
            type=ConsensusMessageType.CONTRIBUTION,
            session_id="session-1",
            from_agent="agent-1",
            to_agent="*",
            payload={"content": "My contribution"}
        )
        assert msg.type == ConsensusMessageType.CONTRIBUTION
        assert msg.to_agent == "*"

    def test_json_serialization(self):
        """Test JSON serialization."""
        msg = ConsensusMessage(
            id="msg-1",
            type=ConsensusMessageType.TOKEN_GRANT,
            session_id="session-1",
            from_agent="coordinator",
            to_agent="agent-1",
            payload={"timeout": 120}
        )

        json_str = msg.to_json()
        restored = ConsensusMessage.from_json(json_str)

        assert restored.type == ConsensusMessageType.TOKEN_GRANT
        assert restored.payload["timeout"] == 120


class TestConsensusMessageFactory:
    """Test message factory."""

    def test_consensus_start(self):
        """Test consensus start message creation."""
        session = create_session(
            topic="Test",
            description="Test desc",
            trigger_type=TriggerType.USER_REQUESTED
        )
        msg = ConsensusMessageFactory.consensus_start(
            session=session,
            invited_agents=["agent-1", "agent-2"]
        )
        assert msg.type == ConsensusMessageType.CONSENSUS_START
        assert msg.from_agent == "coordinator"
        assert msg.requires_ack is True

    def test_token_grant(self):
        """Test token grant message."""
        msg = ConsensusMessageFactory.token_grant(
            session_id="session-1",
            to_agent="agent-1",
            round_number=2,
            context={"summary": "Discussion ongoing"},
            timeout_seconds=60
        )
        assert msg.type == ConsensusMessageType.TOKEN_GRANT
        assert msg.to_agent == "agent-1"
        assert msg.payload["timeout_seconds"] == 60

    def test_contribution(self):
        """Test contribution message."""
        msg = ConsensusMessageFactory.contribution(
            session_id="session-1",
            from_agent="agent-1",
            content="I think we should...",
            contribution_type="opinion",
            round_number=1,
            confidence=0.8
        )
        assert msg.type == ConsensusMessageType.CONTRIBUTION
        assert msg.payload["confidence"] == 0.8

    def test_vote(self):
        """Test vote message."""
        msg = ConsensusMessageFactory.vote(
            session_id="session-1",
            from_agent="agent-2",
            proposal_id="prop-1",
            vote_type=VoteType.APPROVE,
            rationale="Looks good"
        )
        assert msg.type == ConsensusMessageType.VOTE
        assert msg.payload["vote_type"] == "approve"


class TestConsensusChannels:
    """Test channel name generation."""

    def test_session_channel(self):
        """Test session channel name."""
        channel = ConsensusChannels.session("abc123")
        assert "consensus" in channel
        assert "abc123" in channel

    def test_agent_channel(self):
        """Test agent channel name."""
        channel = ConsensusChannels.agent("agent-1")
        assert "agent-1" in channel

    def test_session_key(self):
        """Test session state key."""
        key = ConsensusChannels.session_key("session-1")
        assert "state" in key


class TestVoteCalculation:
    """Test vote result calculation."""

    def test_simple_approval(self):
        """Test simple majority approval."""
        proposal = Proposal(
            id="prop-1",
            author_id="agent-1",
            title="Test",
            description="...",
            rationale="...",
            votes={
                "agent-1": Vote(agent_id="agent-1", vote_type=VoteType.APPROVE),
                "agent-2": Vote(agent_id="agent-2", vote_type=VoteType.APPROVE),
                "agent-3": Vote(agent_id="agent-3", vote_type=VoteType.REJECT)
            }
        )
        rules = ConsensusRules()

        result = calculate_vote_result(proposal, rules, 3)

        assert result["quorum_met"] is True
        assert result["total_votes"] == 3
        assert result["approved"] is True
        assert result["approval_rate"] == 2/3

    def test_rejection(self):
        """Test majority rejection."""
        proposal = Proposal(
            id="prop-1",
            author_id="agent-1",
            title="Test",
            description="...",
            rationale="...",
            votes={
                "agent-1": Vote(agent_id="agent-1", vote_type=VoteType.APPROVE),
                "agent-2": Vote(agent_id="agent-2", vote_type=VoteType.REJECT),
                "agent-3": Vote(agent_id="agent-3", vote_type=VoteType.REJECT)
            }
        )
        rules = ConsensusRules()

        result = calculate_vote_result(proposal, rules, 3)

        assert result["approved"] is False
        assert result["approval_rate"] == 1/3

    def test_quorum_not_met(self):
        """Test quorum not met."""
        proposal = Proposal(
            id="prop-1",
            author_id="agent-1",
            title="Test",
            description="...",
            rationale="...",
            votes={
                "agent-1": Vote(agent_id="agent-1", vote_type=VoteType.APPROVE)
            }
        )
        rules = ConsensusRules()

        result = calculate_vote_result(proposal, rules, 3)

        assert result["quorum_met"] is False
        assert result["approved"] is False

    def test_approve_with_concerns(self):
        """Test that approve_with_concerns counts as approval."""
        proposal = Proposal(
            id="prop-1",
            author_id="agent-1",
            title="Test",
            description="...",
            rationale="...",
            votes={
                "agent-1": Vote(agent_id="agent-1", vote_type=VoteType.APPROVE),
                "agent-2": Vote(agent_id="agent-2", vote_type=VoteType.APPROVE_WITH_CONCERNS),
                "agent-3": Vote(agent_id="agent-3", vote_type=VoteType.ABSTAIN)
            }
        )
        rules = ConsensusRules()

        result = calculate_vote_result(proposal, rules, 3)

        assert result["approved"] is True
        assert result["has_concerns"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
