#!/usr/bin/env python3
"""Tests for expertise_manager module."""

from popkit_shared.utils.expertise_manager import (
    ExpertiseFile,
    Issue,
    Pattern,
    PatternExample,
    PendingPatternsTracker,
)


class TestPatternExample:
    """Test PatternExample dataclass."""

    def test_creation(self):
        example = PatternExample(
            file="src/auth.py",
            before="if user == None:",
            after="if user is None:",
            outcome="Fixed identity comparison",
        )
        assert example.file == "src/auth.py"
        assert example.outcome == "Fixed identity comparison"


class TestPattern:
    """Test Pattern dataclass."""

    def test_creation(self):
        pattern = Pattern(
            id="p-001",
            category="code-quality",
            pattern="identity-comparison",
            trigger="if x == None",
            confidence=0.95,
            occurrences=5,
            first_seen="2025-01-01",
            last_seen="2025-06-01",
            context={"language": "python"},
        )
        assert pattern.id == "p-001"
        assert pattern.confidence == 0.95
        assert pattern.occurrences == 5

    def test_to_dict(self):
        pattern = Pattern(
            id="p-001",
            category="refactoring",
            pattern="extract-method",
            trigger="duplicate code",
            confidence=0.8,
            occurrences=3,
            first_seen="2025-01-01",
            last_seen="2025-06-01",
            context={},
            examples=[
                PatternExample(
                    file="app.py",
                    before="code before",
                    after="code after",
                    outcome="cleaner",
                )
            ],
        )
        d = pattern.to_dict()
        assert d["id"] == "p-001"
        assert len(d["examples"]) == 1
        assert d["examples"][0]["file"] == "app.py"

    def test_from_dict(self):
        data = {
            "id": "p-002",
            "category": "testing",
            "pattern": "missing-assertion",
            "trigger": "test without assert",
            "confidence": 0.7,
            "occurrences": 4,
            "first_seen": "2025-01-01",
            "last_seen": "2025-06-01",
            "context": {"framework": "pytest"},
            "examples": [
                {
                    "file": "test_auth.py",
                    "before": "def test_login():\n    login()",
                    "after": "def test_login():\n    assert login() is True",
                    "outcome": "Added missing assertion",
                }
            ],
        }
        pattern = Pattern.from_dict(data)
        assert pattern.id == "p-002"
        assert pattern.category == "testing"
        assert len(pattern.examples) == 1
        assert isinstance(pattern.examples[0], PatternExample)

    def test_roundtrip(self):
        """Test dict -> Pattern -> dict roundtrip."""
        original = {
            "id": "p-003",
            "category": "security",
            "pattern": "sql-injection",
            "trigger": "string concatenation in SQL",
            "confidence": 0.99,
            "occurrences": 10,
            "first_seen": "2025-01-01",
            "last_seen": "2025-12-01",
            "context": {},
            "examples": [],
        }
        pattern = Pattern.from_dict(original.copy())
        result = pattern.to_dict()
        assert result == original


class TestIssue:
    """Test Issue dataclass."""

    def test_to_dict(self):
        issue = Issue(
            id="i-001",
            pattern="missing-error-handling",
            severity="high",
            occurrences=3,
            solution="Add try/except",
            files_affected=["api.py", "auth.py"],
        )
        d = issue.to_dict()
        assert d["id"] == "i-001"
        assert d["severity"] == "high"
        assert len(d["files_affected"]) == 2

    def test_from_dict(self):
        data = {
            "id": "i-002",
            "pattern": "hardcoded-config",
            "severity": "medium",
            "occurrences": 5,
            "solution": "Use environment variables",
            "files_affected": ["config.py"],
        }
        issue = Issue.from_dict(data)
        assert issue.id == "i-002"
        assert issue.occurrences == 5


class TestExpertiseFile:
    """Test ExpertiseFile dataclass."""

    def test_from_dict_minimal(self):
        data = {"agent_id": "code-reviewer", "project": "popkit"}
        ef = ExpertiseFile.from_dict(data)
        assert ef.agent_id == "code-reviewer"
        assert ef.project == "popkit"
        assert ef.patterns == []
        assert ef.common_issues == []

    def test_to_dict(self):
        ef = ExpertiseFile(
            version="1.0.0",
            agent_id="security-auditor",
            project="myapp",
            created_at="2025-01-01",
            updated_at="2025-06-01",
            patterns=[],
            preferences={"languages": ["python"]},
            common_issues=[],
            project_context={"framework": "flask"},
            stats={"sessions": 10},
            metadata={},
        )
        d = ef.to_dict()
        assert d["agent_id"] == "security-auditor"
        assert d["preferences"]["languages"] == ["python"]

    def test_roundtrip(self):
        ef = ExpertiseFile(
            version="1.0.0",
            agent_id="test-agent",
            project="test",
            created_at="2025-01-01",
            updated_at="2025-01-01",
            patterns=[],
            preferences={},
            common_issues=[],
            project_context={},
            stats={},
            metadata={},
        )
        d = ef.to_dict()
        ef2 = ExpertiseFile.from_dict(d)
        assert ef2.agent_id == ef.agent_id
        assert ef2.version == ef.version


class TestPendingPatternsTracker:
    """Test PendingPatternsTracker."""

    def test_empty_pending(self, tmp_path):
        tracker = PendingPatternsTracker("test-agent", project_root=tmp_path)
        assert tracker.pending == {}

    def test_record_occurrence(self, tmp_path):
        tracker = PendingPatternsTracker("test-agent", project_root=tmp_path)
        count = tracker.record_occurrence(
            pattern_key="missing-type-hints",
            category="code-quality",
            pattern="Functions without type hints",
            trigger="def foo(x, y):",
        )
        assert count == 1

    def test_record_multiple_occurrences(self, tmp_path):
        tracker = PendingPatternsTracker("test-agent", project_root=tmp_path)
        for i in range(3):
            count = tracker.record_occurrence(
                pattern_key="bare-except",
                category="code-quality",
                pattern="Bare except clauses",
                trigger="except:",
            )
        assert count == 3

    def test_persistence(self, tmp_path):
        """Tracker persists data between instances."""
        tracker1 = PendingPatternsTracker("test-agent", project_root=tmp_path)
        tracker1.record_occurrence(
            pattern_key="test-key",
            category="test",
            pattern="test pattern",
            trigger="test trigger",
        )

        tracker2 = PendingPatternsTracker("test-agent", project_root=tmp_path)
        assert "test-key" in tracker2.pending
        assert tracker2.pending["test-key"]["occurrences"] == 1

    def test_creates_directory(self, tmp_path):
        """Tracker creates expertise directory."""
        tracker = PendingPatternsTracker("my-agent", project_root=tmp_path)
        expected_dir = tmp_path / ".claude" / "expertise" / "my-agent"
        assert expected_dir.exists()
