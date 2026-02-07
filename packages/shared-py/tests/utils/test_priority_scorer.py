#!/usr/bin/env python3
"""Tests for priority_scorer module."""

from datetime import datetime, timedelta

from popkit_shared.utils.priority_scorer import (
    LabelPriority,
    PriorityScorer,
    ScoredIssue,
)


class TestLabelPriority:
    """Test LabelPriority enum."""

    def test_critical_value(self):
        assert LabelPriority.CRITICAL.value == 100

    def test_high_value(self):
        assert LabelPriority.HIGH.value == 75

    def test_medium_value(self):
        assert LabelPriority.MEDIUM.value == 50

    def test_low_value(self):
        assert LabelPriority.LOW.value == 25

    def test_none_value(self):
        assert LabelPriority.NONE.value == 0

    def test_ordering(self):
        assert LabelPriority.CRITICAL.value > LabelPriority.HIGH.value
        assert LabelPriority.HIGH.value > LabelPriority.MEDIUM.value
        assert LabelPriority.MEDIUM.value > LabelPriority.LOW.value
        assert LabelPriority.LOW.value > LabelPriority.NONE.value


class TestScoredIssue:
    """Test ScoredIssue dataclass."""

    def test_default_scores(self):
        issue = ScoredIssue(
            number=1,
            title="Test issue",
            labels=["bug"],
            state="open",
            created_at="2025-01-01T00:00:00Z",
            updated_at="2025-01-01T00:00:00Z",
        )
        assert issue.vote_score == 0
        assert issue.staleness_score == 0.0
        assert issue.label_score == 0.0
        assert issue.epic_score == 0.0
        assert issue.priority_score == 0.0
        assert issue.vote_breakdown == {}

    def test_to_dict(self):
        issue = ScoredIssue(
            number=42,
            title="Feature request",
            labels=["enhancement"],
            state="open",
            created_at="2025-01-01",
            updated_at="2025-06-01",
            vote_score=10,
            label_score=50.0,
            priority_score=75.5,
        )
        d = issue.to_dict()
        assert d["number"] == 42
        assert d["priority_score"] == 75.5
        assert d["components"]["votes"] == 10
        assert d["components"]["labels"] == 50.0


class TestPriorityScorer:
    """Test PriorityScorer class."""

    def setup_method(self):
        self.scorer = PriorityScorer()

    def test_default_weights(self):
        assert self.scorer.weights["votes"] == 0.35
        assert self.scorer.weights["staleness"] == 0.20
        assert self.scorer.weights["labels"] == 0.30
        assert self.scorer.weights["epic"] == 0.15

    def test_custom_weights(self):
        scorer = PriorityScorer(weights={"votes": 0.5, "labels": 0.5})
        assert scorer.weights["votes"] == 0.5
        assert scorer.weights["labels"] == 0.5

    def test_label_score_critical(self):
        assert self.scorer.calculate_label_score(["critical"]) == 100
        assert self.scorer.calculate_label_score(["blocker"]) == 100
        assert self.scorer.calculate_label_score(["p0"]) == 100

    def test_label_score_high(self):
        assert self.scorer.calculate_label_score(["high-priority"]) == 75
        assert self.scorer.calculate_label_score(["p1"]) == 75

    def test_label_score_medium(self):
        assert self.scorer.calculate_label_score(["enhancement"]) == 50
        assert self.scorer.calculate_label_score(["feature"]) == 50

    def test_label_score_low(self):
        assert self.scorer.calculate_label_score(["low-priority"]) == 25
        assert self.scorer.calculate_label_score(["nice-to-have"]) == 25

    def test_label_score_empty(self):
        """Empty labels default to medium."""
        assert self.scorer.calculate_label_score([]) == 50

    def test_label_score_bug(self):
        """Bug label without priority label gives high priority."""
        assert self.scorer.calculate_label_score(["bug"]) == 75

    def test_label_score_highest_wins(self):
        """When multiple priority labels, highest wins."""
        assert self.scorer.calculate_label_score(["low", "critical"]) == 100

    def test_label_score_case_insensitive(self):
        """Label matching is case-insensitive."""
        assert self.scorer.calculate_label_score(["Critical"]) == 100
        assert self.scorer.calculate_label_score(["HIGH"]) == 75

    def test_staleness_recent_issue(self):
        """Recently created and updated issue."""
        now = datetime.now()
        created = (now - timedelta(days=1)).isoformat()
        updated = now.isoformat()
        score = self.scorer.calculate_staleness(created, updated)
        assert 0 <= score <= 100

    def test_staleness_old_active_issue(self):
        """Old issue that was recently updated."""
        now = datetime.now()
        created = (now - timedelta(days=180)).isoformat()
        updated = (now - timedelta(days=2)).isoformat()
        score = self.scorer.calculate_staleness(created, updated)
        assert score > 30  # Should have high age score + activity bonus

    def test_staleness_stale_issue(self):
        """Issue with no recent activity."""
        now = datetime.now()
        created = (now - timedelta(days=180)).isoformat()
        updated = (now - timedelta(days=120)).isoformat()
        score = self.scorer.calculate_staleness(created, updated)
        # Stale penalty applies but age score is still there
        assert 0 <= score <= 100

    def test_staleness_invalid_dates(self):
        """Invalid dates return default score."""
        score = self.scorer.calculate_staleness("not-a-date", "also-not-a-date")
        assert score == 50.0

    def test_epic_score_is_epic(self):
        assert self.scorer.calculate_epic_score(["epic"]) == 100.0
        assert self.scorer.calculate_epic_score(["meta"]) == 100.0

    def test_epic_score_child_of_epic(self):
        assert self.scorer.calculate_epic_score(["enhancement"], parent_issue=88) == 75.0

    def test_epic_score_no_epic(self):
        assert self.scorer.calculate_epic_score(["bug"]) == 0.0
