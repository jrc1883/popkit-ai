#!/usr/bin/env python3
"""
Expertise Manager - Per-Agent Learning System

Manages agent-specific expertise files with conservative update logic.
Requires 3+ occurrences before adding new patterns.

Part of Agent Expertise System (Issue #201).

IMPORTANT: Agent identification currently requires POPKIT_ACTIVE_AGENT environment
variable to be set by the agent routing system (Issue #80).
This variable is now set by session-start.py and semantic_router.py.
"""

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# =============================================================================
# CONFIGURATION
# =============================================================================

EXPERTISE_DIR = ".claude/expertise"
MIN_OCCURRENCES = 3  # Conservative threshold
CONFIDENCE_THRESHOLD = 0.7
MAX_PATTERNS = 50
RETENTION_DAYS = 90


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class PatternExample:
    """Example of a pattern application."""

    file: str
    before: str
    after: str
    outcome: str


@dataclass
class Pattern:
    """A learned pattern."""

    id: str
    category: str
    pattern: str
    trigger: str
    confidence: float
    occurrences: int
    first_seen: str
    last_seen: str
    context: Dict[str, Any]
    examples: List[PatternExample] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        d = asdict(self)
        d["examples"] = [asdict(e) for e in self.examples]
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Pattern":
        """Create from dictionary."""
        examples = [PatternExample(**e) for e in d.pop("examples", [])]
        return cls(**d, examples=examples)


@dataclass
class Issue:
    """A common issue this agent encounters."""

    id: str
    pattern: str
    severity: str
    occurrences: int
    solution: str
    files_affected: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Issue":
        """Create from dictionary."""
        return cls(**d)


@dataclass
class ExpertiseFile:
    """Agent expertise file structure."""

    version: str
    agent_id: str
    project: str
    created_at: str
    updated_at: str
    patterns: List[Pattern]
    preferences: Dict[str, List[str]]
    common_issues: List[Issue]
    project_context: Dict[str, Any]
    stats: Dict[str, Any]
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "version": self.version,
            "agent_id": self.agent_id,
            "project": self.project,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "patterns": [p.to_dict() for p in self.patterns],
            "preferences": self.preferences,
            "common_issues": [i.to_dict() for i in self.common_issues],
            "project_context": self.project_context,
            "stats": self.stats,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ExpertiseFile":
        """Create from dictionary."""
        return cls(
            version=d.get("version", "1.0.0"),
            agent_id=d.get("agent_id", ""),
            project=d.get("project", ""),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            patterns=[Pattern.from_dict(p) for p in d.get("patterns", [])],
            preferences=d.get("preferences", {}),
            common_issues=[Issue.from_dict(i) for i in d.get("common_issues", [])],
            project_context=d.get("project_context", {}),
            stats=d.get("stats", {}),
            metadata=d.get("metadata", {}),
        )


# =============================================================================
# PENDING PATTERNS TRACKER
# =============================================================================


class PendingPatternsTracker:
    """Tracks pattern occurrences before they become expertise."""

    def __init__(self, agent_id: str, project_root: Optional[Path] = None):
        """
        Initialize tracker.

        Args:
            agent_id: Agent identifier
            project_root: Project root path
        """
        self.agent_id = agent_id
        self.project_root = project_root or Path.cwd()
        self.pending_file = self.project_root / EXPERTISE_DIR / agent_id / "pending.json"
        self.pending_file.parent.mkdir(parents=True, exist_ok=True)

        self.pending: Dict[str, Dict[str, Any]] = self._load_pending()

    def _load_pending(self) -> Dict[str, Dict[str, Any]]:
        """Load pending patterns from disk."""
        if not self.pending_file.exists():
            return {}

        try:
            with open(self.pending_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}

    def _save_pending(self):
        """Save pending patterns to disk."""
        with open(self.pending_file, "w") as f:
            json.dump(self.pending, f, indent=2)

    def record_occurrence(
        self,
        pattern_key: str,
        category: str,
        pattern: str,
        trigger: str,
        file_path: Optional[str] = None,
        example: Optional[PatternExample] = None,
    ) -> int:
        """
        Record a pattern occurrence.

        Args:
            pattern_key: Unique key for pattern
            category: Pattern category
            pattern: Pattern description
            trigger: What triggers this pattern
            file_path: File where pattern was seen
            example: Example application

        Returns:
            Current occurrence count
        """
        if pattern_key not in self.pending:
            self.pending[pattern_key] = {
                "category": category,
                "pattern": pattern,
                "trigger": trigger,
                "occurrences": 0,
                "first_seen": datetime.utcnow().isoformat() + "Z",
                "files": [],
                "examples": [],
            }

        self.pending[pattern_key]["occurrences"] += 1
        self.pending[pattern_key]["last_seen"] = datetime.utcnow().isoformat() + "Z"

        if file_path and file_path not in self.pending[pattern_key]["files"]:
            self.pending[pattern_key]["files"].append(file_path)

        if example:
            self.pending[pattern_key]["examples"].append(asdict(example))

        self._save_pending()

        return self.pending[pattern_key]["occurrences"]

    def get_ready_patterns(self) -> List[Dict[str, Any]]:
        """Get patterns that have met the occurrence threshold."""
        ready = []
        for key, data in self.pending.items():
            if data["occurrences"] >= MIN_OCCURRENCES:
                ready.append({"key": key, **data})
        return ready

    def clear_pattern(self, pattern_key: str):
        """Clear a pending pattern (after promotion)."""
        if pattern_key in self.pending:
            del self.pending[pattern_key]
            self._save_pending()


# =============================================================================
# EXPERTISE MANAGER
# =============================================================================


class ExpertiseManager:
    """Manages per-agent expertise files."""

    def __init__(self, agent_id: str, project_root: Optional[Path] = None):
        """
        Initialize expertise manager.

        Args:
            agent_id: Agent identifier
            project_root: Project root path
        """
        self.agent_id = agent_id
        self.project_root = project_root or Path.cwd()
        self.expertise_file = self.project_root / EXPERTISE_DIR / agent_id / "expertise.yaml"
        self.expertise_file.parent.mkdir(parents=True, exist_ok=True)

        self.expertise = self._load_or_create_expertise()
        self.pending_tracker = PendingPatternsTracker(agent_id, project_root)

    def _load_or_create_expertise(self) -> ExpertiseFile:
        """Load existing expertise or create new file."""
        if self.expertise_file.exists():
            try:
                with open(self.expertise_file) as f:
                    data = yaml.safe_load(f)
                return ExpertiseFile.from_dict(data)
            except (yaml.YAMLError, IOError):
                pass  # Fall through to create new

        # Create new expertise file
        project_name = self.project_root.name
        now = datetime.utcnow().isoformat() + "Z"

        expertise = ExpertiseFile(
            version="1.0.0",
            agent_id=self.agent_id,
            project=project_name,
            created_at=now,
            updated_at=now,
            patterns=[],
            preferences={},
            common_issues=[],
            project_context={},
            stats={
                "total_patterns": 0,
                "total_issues": 0,
                "reviews_conducted": 0,
                "suggestions_accepted": 0,
                "suggestions_rejected": 0,
                "avg_confidence": 0.0,
                "last_review": None,
            },
            metadata={
                "learning_enabled": True,
                "auto_update": True,
                "min_occurrences_threshold": MIN_OCCURRENCES,
                "confidence_threshold": CONFIDENCE_THRESHOLD,
                "max_patterns": MAX_PATTERNS,
                "retention_days": RETENTION_DAYS,
            },
        )

        # Save initial file
        self._save_expertise_internal(expertise)
        return expertise

    def _save_expertise_internal(self, expertise: ExpertiseFile):
        """Save expertise to disk (internal method)."""
        with open(self.expertise_file, "w") as f:
            yaml.dump(
                expertise.to_dict(),
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )

    def _save_expertise(self):
        """Save expertise to disk."""
        self.expertise.updated_at = datetime.utcnow().isoformat() + "Z"
        self._save_expertise_internal(self.expertise)

    def record_pattern_occurrence(
        self,
        category: str,
        pattern: str,
        trigger: str,
        file_path: Optional[str] = None,
        example: Optional[PatternExample] = None,
    ) -> Optional[Pattern]:
        """
        Record a pattern occurrence. Promotes to expertise if threshold met.

        Args:
            category: Pattern category
            pattern: Pattern description
            trigger: What triggers this pattern
            file_path: File where pattern was seen
            example: Example application

        Returns:
            Pattern if promoted to expertise, None otherwise
        """
        if not self.expertise.metadata.get("learning_enabled", True):
            return None

        # Create unique key for pattern
        pattern_key = f"{category}:{pattern}"

        # Record occurrence
        count = self.pending_tracker.record_occurrence(
            pattern_key, category, pattern, trigger, file_path, example
        )

        # Check if ready for promotion
        if count >= MIN_OCCURRENCES:
            ready = self.pending_tracker.get_ready_patterns()
            matching = next((p for p in ready if p["key"] == pattern_key), None)

            if matching:
                # Promote to expertise
                promoted = self._promote_pattern(matching)
                self.pending_tracker.clear_pattern(pattern_key)
                return promoted

        return None

    def _promote_pattern(self, pending_data: Dict[str, Any]) -> Pattern:
        """Promote a pending pattern to expertise."""
        pattern_id = f"pat-{len(self.expertise.patterns) + 1:03d}"

        examples = [PatternExample(**e) for e in pending_data.get("examples", [])[:3]]

        pattern = Pattern(
            id=pattern_id,
            category=pending_data["category"],
            pattern=pending_data["pattern"],
            trigger=pending_data["trigger"],
            confidence=0.7,  # Initial confidence
            occurrences=pending_data["occurrences"],
            first_seen=pending_data["first_seen"],
            last_seen=pending_data["last_seen"],
            context={
                "files": pending_data.get("files", []),
                "related_patterns": [],
            },
            examples=examples,
        )

        self.expertise.patterns.append(pattern)
        self.expertise.stats["total_patterns"] = len(self.expertise.patterns)
        self._save_expertise()

        return pattern

    def add_preference(self, category: str, preference: str):
        """Add a learned preference."""
        if category not in self.expertise.preferences:
            self.expertise.preferences[category] = []

        if preference not in self.expertise.preferences[category]:
            self.expertise.preferences[category].append(preference)
            self._save_expertise()

    def record_issue(
        self, pattern: str, severity: str, solution: str, file_path: Optional[str] = None
    ) -> Optional[Issue]:
        """
        Record a common issue. Requires 3+ occurrences before adding to expertise (conservative threshold).

        Args:
            pattern: Issue pattern
            severity: Severity level
            solution: Solution description
            file_path: Affected file

        Returns:
            Issue if promoted to expertise, None otherwise
        """
        # Check if already in expertise
        existing = next((i for i in self.expertise.common_issues if i.pattern == pattern), None)

        if existing:
            # Already promoted - just increment
            existing.occurrences += 1
            if file_path and file_path not in existing.files_affected:
                existing.files_affected.append(file_path)
            self._save_expertise()
            return existing

        # Not in expertise yet - use pending tracker
        issue_key = f"issue:{pattern}"
        count = self.pending_tracker.record_occurrence(
            pattern_key=issue_key,
            category="issue",  # Mark as issue type
            pattern=pattern,
            trigger=f"{severity} severity issue",
            file_path=file_path,
        )

        # Promote to expertise if threshold met
        if count >= MIN_OCCURRENCES:
            ready = self.pending_tracker.get_ready_patterns()
            matching = next((p for p in ready if p["key"] == issue_key), None)

            if matching:
                # Promote to expertise
                issue_id = f"iss-{len(self.expertise.common_issues) + 1:03d}"

                issue = Issue(
                    id=issue_id,
                    pattern=pattern,
                    severity=severity,
                    occurrences=matching["occurrences"],
                    solution=solution,
                    files_affected=matching.get("files", []),
                )

                self.expertise.common_issues.append(issue)
                self.expertise.stats["total_issues"] = len(self.expertise.common_issues)
                self._save_expertise()

                # Clear from pending
                self.pending_tracker.clear_pattern(issue_key)

                return issue

        return None  # Not promoted yet

    def update_stats(
        self,
        reviews_conducted: int = 0,
        suggestions_accepted: int = 0,
        suggestions_rejected: int = 0,
    ):
        """Update usage statistics."""
        self.expertise.stats["reviews_conducted"] += reviews_conducted
        self.expertise.stats["suggestions_accepted"] += suggestions_accepted
        self.expertise.stats["suggestions_rejected"] += suggestions_rejected

        # Recalculate average confidence
        if self.expertise.patterns:
            avg = sum(p.confidence for p in self.expertise.patterns) / len(self.expertise.patterns)
            self.expertise.stats["avg_confidence"] = round(avg, 3)

        self.expertise.stats["last_review"] = datetime.utcnow().isoformat() + "Z"
        self._save_expertise()

    def get_patterns_by_category(self, category: str) -> List[Pattern]:
        """Get patterns for a specific category."""
        return [p for p in self.expertise.patterns if p.category == category]

    def get_high_confidence_patterns(self, threshold: float = 0.8) -> List[Pattern]:
        """Get patterns above confidence threshold."""
        return [p for p in self.expertise.patterns if p.confidence >= threshold]

    def cleanup_old_patterns(self):
        """Remove patterns older than retention period with low confidence."""
        if not self.expertise.metadata.get("retention_days"):
            return

        retention_days = self.expertise.metadata["retention_days"]
        cutoff = datetime.utcnow() - timedelta(days=retention_days)

        before_count = len(self.expertise.patterns)

        self.expertise.patterns = [
            p
            for p in self.expertise.patterns
            if (
                datetime.fromisoformat(p.last_seen.replace("Z", "")) > cutoff or p.confidence >= 0.8
            )  # Keep high-confidence patterns
        ]

        after_count = len(self.expertise.patterns)

        if before_count != after_count:
            self.expertise.stats["total_patterns"] = after_count
            self._save_expertise()

    def export_json(self, filepath: Path):
        """Export expertise to JSON."""
        with open(filepath, "w") as f:
            json.dump(self.expertise.to_dict(), f, indent=2)

    def get_summary(self) -> Dict[str, Any]:
        """Get expertise summary."""
        return {
            "agent_id": self.expertise.agent_id,
            "project": self.expertise.project,
            "total_patterns": len(self.expertise.patterns),
            "total_preferences": sum(len(v) for v in self.expertise.preferences.values()),
            "total_issues": len(self.expertise.common_issues),
            "reviews_conducted": self.expertise.stats.get("reviews_conducted", 0),
            "avg_confidence": self.expertise.stats.get("avg_confidence", 0.0),
            "last_updated": self.expertise.updated_at,
        }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================


def get_manager(agent_id: str, project_root: Optional[Path] = None) -> ExpertiseManager:
    """Get expertise manager instance."""
    return ExpertiseManager(agent_id, project_root)


def record_pattern(
    agent_id: str,
    category: str,
    pattern: str,
    trigger: str,
    file_path: Optional[str] = None,
    example: Optional[PatternExample] = None,
) -> Optional[Pattern]:
    """Convenience function to record a pattern."""
    manager = get_manager(agent_id)
    return manager.record_pattern_occurrence(category, pattern, trigger, file_path, example)
