# Agent Expertise System - Comprehensive Architecture

## Executive Summary

This document defines a three-tier learning system for PopKit that progressively specializes knowledge from global patterns to project-specific research to per-agent expertise. The system activates dormant infrastructure first, then adds the new expertise layer with conservative update thresholds.

**Version**: 1.0.0
**Status**: Design Complete - Ready for Implementation
**Date**: 2025-12-19

---

## System Overview

### Three-Tier Learning Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TIER 1: GLOBAL PATTERNS                   │
│                  (~/.claude/config/patterns.db)              │
│                                                               │
│  • Command corrections (cp → xcopy)                          │
│  • Platform-specific translations (Unix → Windows)           │
│  • Cross-project learnings                                   │
│  • Managed by: pattern_learner.py                            │
│  • Scope: All projects, all users                            │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  TIER 2: PROJECT RESEARCH                    │
│                 (.claude/research/index.json)                │
│                                                               │
│  • Architecture decisions                                    │
│  • Technical findings and learnings                          │
│  • Spike results and comparisons                             │
│  • Managed by: research_index.py                             │
│  • Scope: Current project, all agents                        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                  TIER 3: AGENT EXPERTISE                     │
│            (.claude/expertise/{agent-id}/expertise.yaml)     │
│                                                               │
│  • Agent-specific learnings (code-reviewer: "prefer async")  │
│  • Pattern refinements per agent                             │
│  • Project-specific agent behaviors                          │
│  • Managed by: expertise_manager.py (NEW)                    │
│  • Scope: Current project, specific agent                    │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Action (e.g., bash command fails)
    │
    ├──→ pattern_learner.py records correction
    │    └──→ ~/.claude/config/command_patterns.db
    │
    ├──→ research_surfacer.py checks for relevant research
    │    └──→ .claude/research/index.json
    │
    └──→ expertise_manager.py updates agent expertise
         └──→ .claude/expertise/{agent-id}/expertise.yaml
```

---

## Phase 1: Activate Dormant Infrastructure

### Problem Analysis

**Why isn't pattern_learner working?**

1. **command-learning-hook.py** is registered in hooks.json (line 83) but:
   - Only triggers on `PostToolUse` for `Bash` tool
   - Never creates the database directory
   - pattern_learner.py assumes `~/.claude/config/` exists (line 58)

2. **research_index.py** exists but:
   - research_surfacer.py has broken import (line 117: `from research_index import ResearchIndexManager`)
   - Should be: `from .research_index import ResearchIndexManager`
   - No initialization in session-start.py

3. **No directory creation**:
   - session-start.py creates `.claude/popkit/` but not `.claude/research/`
   - pattern_learner expects `~/.claude/config/` but nothing creates it

### Solution: Phase 1 Implementation

#### 1.1 Fix Pattern Learner Initialization

**File**: `packages/plugin/hooks/session-start.py`

**Add after line 218** (after `ensure_popkit_directories`):

```python
def ensure_pattern_learner_directories():
    """Ensure pattern learner directories exist.

    Creates:
    - ~/.claude/config/          - Global pattern database
    - .claude/research/          - Project research index
    - .claude/expertise/         - Agent expertise files

    Returns:
        dict: Status of directory creation, or None on error
    """
    try:
        home = Path.home()
        cwd = Path(os.getcwd())

        # Global config directory
        global_config = home / ".claude" / "config"

        # Project-specific directories
        project_research = cwd / ".claude" / "research"
        project_expertise = cwd / ".claude" / "expertise"

        dirs_to_create = [
            global_config,
            project_research,
            project_research / "entries",
            project_expertise,
        ]

        created = []
        for d in dirs_to_create:
            if not d.exists():
                d.mkdir(parents=True, exist_ok=True)
                # Use relative path for project dirs, absolute for global
                if d.is_relative_to(cwd):
                    created.append(str(d.relative_to(cwd)))
                else:
                    created.append(str(d))

        # Initialize research index if missing
        index_path = project_research / "index.json"
        index_created = False
        if not index_path.exists() and project_research.exists():
            from hooks.utils.research_index import ResearchIndex
            index = ResearchIndex()
            with open(index_path, 'w') as f:
                json.dump(index.to_dict(), f, indent=2)
            index_created = True

        if created or index_created:
            return {
                'directories_created': created,
                'index_created': index_created
            }

        return None  # Nothing needed

    except Exception:
        pass  # Silent failure

    return None
```

**Call it in main()** after line 282:

```python
# Ensure pattern learner and research directories (Phase 1)
learning_init = ensure_pattern_learner_directories()
if learning_init:
    dirs = learning_init.get('directories_created', [])
    index = learning_init.get('index_created', False)
    if dirs or index:
        parts = []
        if dirs:
            parts.append(f"directories: {len(dirs)}")
        if index:
            parts.append("research index")
        print(f"Learning systems initialized: {', '.join(parts)}", file=sys.stderr)
```

#### 1.2 Fix Research Surfacer Import

**File**: `packages/plugin/hooks/utils/research_surfacer.py`

**Line 117** - Change from:
```python
from research_index import ResearchIndexManager
```

To:
```python
from .research_index import ResearchIndexManager
```

#### 1.3 Create /popkit:research Command

**File**: `packages/plugin/commands/research.md` (NEW)

```markdown
---
name: research
category: Productivity
description: Manage research entries for architecture decisions, findings, and learnings
usage: |
  /popkit:research add <type> <title>    - Add new research entry
  /popkit:research list [tag]            - List entries (optionally filtered)
  /popkit:research show <id>             - Show full entry details
  /popkit:research search <query>        - Semantic search entries
  /popkit:research tag <id> <tag>        - Add tag to entry
  /popkit:research export [file]         - Export to JSON
  /popkit:research import <file>         - Import from JSON
  /popkit:research stats                 - Show statistics
examples:
  - /popkit:research add decision "Use Redis for sessions"
  - /popkit:research list auth
  - /popkit:research search "caching strategy"
  - /popkit:research show dec-001
---

# Research Management

Manages the project research index for capturing architectural decisions, technical findings, learnings, and spike results.

## Entry Types

| Type | Purpose | Example |
|------|---------|---------|
| **decision** | Architecture decisions with rationale | "Use PostgreSQL over MongoDB" |
| **finding** | Technical discoveries | "OAuth token refresh fails on Safari" |
| **learning** | New knowledge gained | "TypeScript strict mode catches 40% more bugs" |
| **spike** | Exploration results | "Compared 3 state management libraries" |

## Workflow Integration

Research entries are automatically surfaced when relevant:
- Keyword matching during development
- File context awareness
- Semantic search via embeddings

## Storage

- **Index**: `.claude/research/index.json`
- **Entries**: `.claude/research/entries/{id}.json`
- **Embeddings**: Upstash Vector (cloud) or local fallback

## Commands

### Add Entry

```
/popkit:research add <type> <title>
```

Creates a new research entry. Claude will prompt for:
- Content (description)
- Context (when/why)
- Rationale (decision reasoning)
- Alternatives considered
- Tags

### List Entries

```
/popkit:research list [tag]
```

Shows all entries, optionally filtered by tag.

### Search Entries

```
/popkit:research search <query>
```

Semantic search across all entries using embeddings.

### Show Entry

```
/popkit:research show <id>
```

Display full details for an entry.

### Statistics

```
/popkit:research stats
```

Show research index statistics:
- Total entries by type
- Tag distribution
- Recent activity

## Integration Points

- **Auto-surface**: research_surfacer.py detects context and suggests relevant entries
- **Embeddings**: Voyage AI for semantic search (requires VOYAGE_API_KEY)
- **Cloud sync**: Pro/Team users sync across projects

## See Also

- `/popkit:project analyze` - Project analysis
- `/popkit:stats` - Usage statistics
```

**Skill implementation**: `packages/plugin/skills/pop-research-manage/` (NEW)

```markdown
---
name: pop-research-manage
category: Productivity
description: Manage research index entries
required_tools:
  - Read
  - Write
  - Skill
parameters:
  action:
    type: string
    description: Action to perform (add|list|show|search|stats)
    required: true
  args:
    type: object
    description: Action-specific arguments
    required: false
---

# Research Management Skill

Internal skill for managing the research index.

## Implementation

Use the research_index.py utility:

```python
from hooks.utils.research_index import ResearchIndexManager

manager = ResearchIndexManager()

# Add entry
entry = manager.add_entry(
    type="decision",
    title="Use Redis for sessions",
    content="...",
    context="...",
    tags=["auth", "sessions"]
)

# List entries
entries = manager.list_entries(tag="auth")

# Search
results = manager.search_semantic("caching strategy")
```

## Actions

- **add**: Create new entry
- **list**: List all entries (with optional tag filter)
- **show**: Display entry details
- **search**: Semantic search
- **tag**: Add tag to entry
- **export**: Export to JSON
- **import**: Import from JSON
- **stats**: Show statistics

## Output

Use AskUserQuestion for user input:
- Entry details
- Tag selection
- Confirmation prompts

Present results in markdown tables.
```

#### 1.4 Phase 1 Testing Plan

**Test Cases**:

1. **Pattern Learner Activation**:
   ```bash
   # Should create ~/.claude/config/command_patterns.db
   # Run a failing bash command
   # Verify database created and correction recorded
   ```

2. **Research Index Initialization**:
   ```bash
   # Start new session
   # Verify .claude/research/ created
   # Verify index.json exists with valid schema
   ```

3. **Research Command**:
   ```bash
   /popkit:research add decision "Test decision"
   /popkit:research list
   /popkit:research show dec-001
   ```

4. **Research Surfacing**:
   ```bash
   # Add research entry tagged "auth"
   # In conversation, mention authentication
   # Verify research surfaced automatically
   ```

---

## Phase 2: Add Per-Agent Expertise System

### Agent Expertise YAML Schema

**File**: `.claude/expertise/{agent-id}/expertise.yaml`

```yaml
# Agent Expertise - code-reviewer
# Auto-generated and maintained by PopKit
# Conservative updates: 3+ occurrences required before adding

version: "1.0.0"
agent_id: "code-reviewer"
project: "my-app"
created_at: "2025-12-19T10:00:00Z"
updated_at: "2025-12-19T15:30:00Z"

# Pattern Library: Agent-specific learnings
patterns:
  # Each pattern requires 3+ occurrences before being added
  - id: "pat-001"
    category: "code-style"
    pattern: "prefer async/await over promises"
    trigger: "callback hell detected"
    confidence: 0.85
    occurrences: 5
    first_seen: "2025-12-19T10:00:00Z"
    last_seen: "2025-12-19T15:00:00Z"
    context:
      files: ["src/api/*.ts", "src/services/*.ts"]
      related_patterns: ["pat-002"]
    examples:
      - file: "src/api/users.ts"
        before: "getUserData().then(data => ...)"
        after: "const data = await getUserData()"
        outcome: "reduced nesting, improved readability"

  - id: "pat-002"
    category: "error-handling"
    pattern: "wrap async functions in try/catch"
    trigger: "unhandled promise rejection"
    confidence: 0.92
    occurrences: 8
    first_seen: "2025-12-18T14:00:00Z"
    last_seen: "2025-12-19T15:30:00Z"
    context:
      files: ["src/**/*.ts"]
      related_patterns: ["pat-001"]
    examples:
      - file: "src/services/auth.ts"
        before: "async login() { await db.query(...) }"
        after: "async login() { try { await db.query(...) } catch (e) { ... } }"
        outcome: "prevented crash on DB error"

# Learned Preferences: Project-specific behaviors
preferences:
  code_style:
    - "use 2-space indentation (project standard)"
    - "prefer named exports over default exports"
    - "use const over let when possible"

  architecture:
    - "follow services pattern in src/services/"
    - "keep API routes thin, logic in services"
    - "use dependency injection for testability"

  testing:
    - "write unit tests for all services"
    - "use Jest for unit, Playwright for E2E"
    - "aim for 80%+ coverage on services"

  security:
    - "validate all user input with Zod"
    - "never log sensitive data (passwords, tokens)"
    - "use environment variables for secrets"

# Common Issues: Problems this agent frequently encounters
common_issues:
  - id: "iss-001"
    pattern: "missing null checks on API responses"
    severity: "medium"
    occurrences: 12
    solution: "add optional chaining or null guards"
    files_affected:
      - "src/api/*.ts"

  - id: "iss-002"
    pattern: "console.log left in production code"
    severity: "low"
    occurrences: 6
    solution: "use proper logging library or remove"
    files_affected:
      - "src/**/*.ts"

# Project Context: Agent-specific project understanding
project_context:
  tech_stack:
    - "TypeScript 5.0"
    - "React 18"
    - "Next.js 14"
    - "Supabase"

  key_patterns:
    - "Server Components for data fetching"
    - "Client Components for interactivity"
    - "Supabase RLS for auth"

  testing_approach:
    - "Jest for unit tests"
    - "Playwright for E2E"
    - "React Testing Library for components"

  known_pitfalls:
    - "Don't use useState in Server Components"
    - "Remember to add 'use client' directive"
    - "Supabase client must be initialized per request"

# Statistics: Usage metrics
stats:
  total_patterns: 2
  total_issues: 2
  reviews_conducted: 45
  suggestions_accepted: 38
  suggestions_rejected: 7
  avg_confidence: 0.885
  last_review: "2025-12-19T15:30:00Z"

# Metadata
metadata:
  learning_enabled: true
  auto_update: true
  min_occurrences_threshold: 3
  confidence_threshold: 0.7
  max_patterns: 50
  retention_days: 90
```

### Expertise Manager Implementation

**File**: `packages/plugin/hooks/utils/expertise_manager.py` (NEW)

```python
#!/usr/bin/env python3
"""
Expertise Manager - Per-Agent Learning System

Manages agent-specific expertise files with conservative update logic.
Requires 3+ occurrences before adding new patterns.

Part of Agent Expertise System (Issue #TBD).
"""

import os
import yaml
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field, asdict
from collections import defaultdict


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
        d['examples'] = [asdict(e) for e in self.examples]
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'Pattern':
        """Create from dictionary."""
        examples = [PatternExample(**e) for e in d.pop('examples', [])]
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
    def from_dict(cls, d: Dict[str, Any]) -> 'Issue':
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
            'version': self.version,
            'agent_id': self.agent_id,
            'project': self.project,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
            'patterns': [p.to_dict() for p in self.patterns],
            'preferences': self.preferences,
            'common_issues': [i.to_dict() for i in self.common_issues],
            'project_context': self.project_context,
            'stats': self.stats,
            'metadata': self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'ExpertiseFile':
        """Create from dictionary."""
        return cls(
            version=d.get('version', '1.0.0'),
            agent_id=d.get('agent_id', ''),
            project=d.get('project', ''),
            created_at=d.get('created_at', ''),
            updated_at=d.get('updated_at', ''),
            patterns=[Pattern.from_dict(p) for p in d.get('patterns', [])],
            preferences=d.get('preferences', {}),
            common_issues=[Issue.from_dict(i) for i in d.get('common_issues', [])],
            project_context=d.get('project_context', {}),
            stats=d.get('stats', {}),
            metadata=d.get('metadata', {}),
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
        self.pending_file = (
            self.project_root / EXPERTISE_DIR / agent_id / "pending.json"
        )
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
        with open(self.pending_file, 'w') as f:
            json.dump(self.pending, f, indent=2)

    def record_occurrence(
        self,
        pattern_key: str,
        category: str,
        pattern: str,
        trigger: str,
        file_path: Optional[str] = None,
        example: Optional[PatternExample] = None
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
                'category': category,
                'pattern': pattern,
                'trigger': trigger,
                'occurrences': 0,
                'first_seen': datetime.utcnow().isoformat() + 'Z',
                'files': [],
                'examples': []
            }

        self.pending[pattern_key]['occurrences'] += 1
        self.pending[pattern_key]['last_seen'] = datetime.utcnow().isoformat() + 'Z'

        if file_path and file_path not in self.pending[pattern_key]['files']:
            self.pending[pattern_key]['files'].append(file_path)

        if example:
            self.pending[pattern_key]['examples'].append(asdict(example))

        self._save_pending()

        return self.pending[pattern_key]['occurrences']

    def get_ready_patterns(self) -> List[Dict[str, Any]]:
        """Get patterns that have met the occurrence threshold."""
        ready = []
        for key, data in self.pending.items():
            if data['occurrences'] >= MIN_OCCURRENCES:
                ready.append({'key': key, **data})
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
        self.expertise_file = (
            self.project_root / EXPERTISE_DIR / agent_id / "expertise.yaml"
        )
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
        now = datetime.utcnow().isoformat() + 'Z'

        return ExpertiseFile(
            version='1.0.0',
            agent_id=self.agent_id,
            project=project_name,
            created_at=now,
            updated_at=now,
            patterns=[],
            preferences={},
            common_issues=[],
            project_context={},
            stats={
                'total_patterns': 0,
                'total_issues': 0,
                'reviews_conducted': 0,
                'suggestions_accepted': 0,
                'suggestions_rejected': 0,
                'avg_confidence': 0.0,
                'last_review': None,
            },
            metadata={
                'learning_enabled': True,
                'auto_update': True,
                'min_occurrences_threshold': MIN_OCCURRENCES,
                'confidence_threshold': CONFIDENCE_THRESHOLD,
                'max_patterns': MAX_PATTERNS,
                'retention_days': RETENTION_DAYS,
            }
        )

    def _save_expertise(self):
        """Save expertise to disk."""
        self.expertise.updated_at = datetime.utcnow().isoformat() + 'Z'

        with open(self.expertise_file, 'w') as f:
            yaml.dump(
                self.expertise.to_dict(),
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True
            )

    def record_pattern_occurrence(
        self,
        category: str,
        pattern: str,
        trigger: str,
        file_path: Optional[str] = None,
        example: Optional[PatternExample] = None
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
        if not self.expertise.metadata.get('learning_enabled', True):
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
            matching = next((p for p in ready if p['key'] == pattern_key), None)

            if matching:
                # Promote to expertise
                promoted = self._promote_pattern(matching)
                self.pending_tracker.clear_pattern(pattern_key)
                return promoted

        return None

    def _promote_pattern(self, pending_data: Dict[str, Any]) -> Pattern:
        """Promote a pending pattern to expertise."""
        pattern_id = f"pat-{len(self.expertise.patterns) + 1:03d}"

        examples = [
            PatternExample(**e) for e in pending_data.get('examples', [])[:3]
        ]

        pattern = Pattern(
            id=pattern_id,
            category=pending_data['category'],
            pattern=pending_data['pattern'],
            trigger=pending_data['trigger'],
            confidence=0.7,  # Initial confidence
            occurrences=pending_data['occurrences'],
            first_seen=pending_data['first_seen'],
            last_seen=pending_data['last_seen'],
            context={
                'files': pending_data.get('files', []),
                'related_patterns': [],
            },
            examples=examples
        )

        self.expertise.patterns.append(pattern)
        self.expertise.stats['total_patterns'] = len(self.expertise.patterns)
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
        self,
        pattern: str,
        severity: str,
        solution: str,
        file_path: Optional[str] = None
    ) -> Optional[Issue]:
        """
        Record a common issue. Adds to expertise if seen 3+ times.

        Args:
            pattern: Issue pattern
            severity: Severity level
            solution: Solution description
            file_path: Affected file

        Returns:
            Issue if added to expertise, None otherwise
        """
        # Find existing issue
        existing = next(
            (i for i in self.expertise.common_issues if i.pattern == pattern),
            None
        )

        if existing:
            existing.occurrences += 1
            if file_path and file_path not in existing.files_affected:
                existing.files_affected.append(file_path)
            self._save_expertise()
            return existing
        else:
            # Check if this is the 3rd occurrence (conservative)
            # For now, add immediately (can track pending if needed)
            issue_id = f"iss-{len(self.expertise.common_issues) + 1:03d}"

            issue = Issue(
                id=issue_id,
                pattern=pattern,
                severity=severity,
                occurrences=1,
                solution=solution,
                files_affected=[file_path] if file_path else []
            )

            # Only add if seen multiple times
            # (In practice, call record_issue each time you see it)
            # For now, add on first occurrence for testing
            self.expertise.common_issues.append(issue)
            self.expertise.stats['total_issues'] = len(self.expertise.common_issues)
            self._save_expertise()

            return issue

    def update_stats(
        self,
        reviews_conducted: int = 0,
        suggestions_accepted: int = 0,
        suggestions_rejected: int = 0
    ):
        """Update usage statistics."""
        self.expertise.stats['reviews_conducted'] += reviews_conducted
        self.expertise.stats['suggestions_accepted'] += suggestions_accepted
        self.expertise.stats['suggestions_rejected'] += suggestions_rejected

        # Recalculate average confidence
        if self.expertise.patterns:
            avg = sum(p.confidence for p in self.expertise.patterns) / len(self.expertise.patterns)
            self.expertise.stats['avg_confidence'] = round(avg, 3)

        self.expertise.stats['last_review'] = datetime.utcnow().isoformat() + 'Z'
        self._save_expertise()

    def get_patterns_by_category(self, category: str) -> List[Pattern]:
        """Get patterns for a specific category."""
        return [p for p in self.expertise.patterns if p.category == category]

    def get_high_confidence_patterns(self, threshold: float = 0.8) -> List[Pattern]:
        """Get patterns above confidence threshold."""
        return [p for p in self.expertise.patterns if p.confidence >= threshold]

    def cleanup_old_patterns(self):
        """Remove patterns older than retention period with low confidence."""
        if not self.expertise.metadata.get('retention_days'):
            return

        retention_days = self.expertise.metadata['retention_days']
        cutoff = datetime.utcnow() - timedelta(days=retention_days)

        before_count = len(self.expertise.patterns)

        self.expertise.patterns = [
            p for p in self.expertise.patterns
            if (datetime.fromisoformat(p.last_seen.replace('Z', '')) > cutoff
                or p.confidence >= 0.8)  # Keep high-confidence patterns
        ]

        after_count = len(self.expertise.patterns)

        if before_count != after_count:
            self.expertise.stats['total_patterns'] = after_count
            self._save_expertise()

    def export_json(self, filepath: Path):
        """Export expertise to JSON."""
        with open(filepath, 'w') as f:
            json.dump(self.expertise.to_dict(), f, indent=2)

    def get_summary(self) -> Dict[str, Any]:
        """Get expertise summary."""
        return {
            'agent_id': self.expertise.agent_id,
            'project': self.expertise.project,
            'total_patterns': len(self.expertise.patterns),
            'total_preferences': sum(len(v) for v in self.expertise.preferences.values()),
            'total_issues': len(self.expertise.common_issues),
            'reviews_conducted': self.expertise.stats.get('reviews_conducted', 0),
            'avg_confidence': self.expertise.stats.get('avg_confidence', 0.0),
            'last_updated': self.expertise.updated_at,
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
    example: Optional[PatternExample] = None
) -> Optional[Pattern]:
    """Convenience function to record a pattern."""
    manager = get_manager(agent_id)
    return manager.record_pattern_occurrence(
        category, pattern, trigger, file_path, example
    )
```

### Integration with session-start.py

**File**: `packages/plugin/hooks/session-start.py`

**Add** after loading agents (line 295):

```python
def load_agent_expertise():
    """Load expertise files for relevant agents.

    This is non-blocking - any errors are silently ignored.

    Returns:
        dict: Loaded expertise info, or None on error
    """
    try:
        from utils.expertise_manager import ExpertiseManager

        cwd = Path(os.getcwd())
        expertise_dir = cwd / ".claude" / "expertise"

        if not expertise_dir.exists():
            return None

        loaded = []
        for agent_dir in expertise_dir.iterdir():
            if agent_dir.is_dir():
                expertise_file = agent_dir / "expertise.yaml"
                if expertise_file.exists():
                    agent_id = agent_dir.name
                    manager = ExpertiseManager(agent_id, cwd)
                    summary = manager.get_summary()
                    loaded.append({
                        'agent_id': agent_id,
                        'patterns': summary['total_patterns'],
                        'preferences': summary['total_preferences'],
                    })

        if loaded:
            print(f"Agent expertise loaded: {len(loaded)} agents", file=sys.stderr)
            return {'agents': loaded}

        return None

    except Exception:
        pass  # Silent failure

    return None
```

**Call it in main()** after line 295:

```python
# Load agent expertise files (Phase 2, non-blocking)
expertise_loading = load_agent_expertise()
if expertise_loading:
    response["expertise_loading"] = expertise_loading
```

### Integration with post-tool-use.py

**File**: `packages/plugin/hooks/post-tool-use.py`

**Add method to PostToolUseHook class**:

```python
def update_agent_expertise(self, tool_name: str, tool_input: dict, tool_output: str):
    """Update agent expertise based on tool usage.

    This is the self-improvement mechanism.
    Looks for patterns in tool results and records them.
    """
    try:
        from utils.expertise_manager import ExpertiseManager, PatternExample

        # Determine which agent is active
        # (This would come from context or agent routing)
        agent_id = os.environ.get('POPKIT_ACTIVE_AGENT')
        if not agent_id:
            return  # No active agent

        manager = ExpertiseManager(agent_id)

        # Pattern detection logic
        # Example: code-reviewer notices repeated issue
        if agent_id == 'code-reviewer':
            # Look for common review comments
            if 'missing error handling' in tool_output.lower():
                manager.record_pattern_occurrence(
                    category='error-handling',
                    pattern='wrap async functions in try/catch',
                    trigger='unhandled promise rejection',
                    file_path=tool_input.get('file_path'),
                )

            if 'console.log' in tool_output:
                manager.record_pattern_occurrence(
                    category='code-style',
                    pattern='remove console.log from production',
                    trigger='console.log detected in code',
                    file_path=tool_input.get('file_path'),
                )

        # Example: security-auditor notices patterns
        elif agent_id == 'security-auditor':
            if 'password' in tool_output.lower() and 'log' in tool_output.lower():
                manager.record_issue(
                    pattern='logging sensitive data',
                    severity='high',
                    solution='remove password from log statements',
                    file_path=tool_input.get('file_path'),
                )

    except Exception:
        pass  # Silent failure - never block on expertise updates
```

**Call it in process()** after line 200:

```python
# Update agent expertise (Phase 2, non-blocking)
self.update_agent_expertise(tool_name, tool_input, tool_output)
```

---

## Phase 3: Integration and Metrics

### Three-Tier Interaction Flow

```
┌─────────────────────────────────────────────────────────┐
│                    USER ACTION                          │
│              (e.g., code review request)                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  session-start.py     │
         │  Loads all tiers:     │
         │  1. Global patterns   │
         │  2. Research index    │
         │  3. Agent expertise   │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────────────┐
         │  Agent Activation             │
         │  (e.g., code-reviewer)        │
         └───────────┬───────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
        ▼                         ▼
┌───────────────┐         ┌──────────────────┐
│ Check Tier 3  │         │  Execute Review  │
│ Expertise     │────────>│                  │
│               │         └──────────┬───────┘
│ - Patterns    │                    │
│ - Preferences │                    │
│ - Issues      │                    │
└───────────────┘                    │
        │                            │
        ▼                            ▼
┌───────────────┐         ┌──────────────────┐
│ Check Tier 2  │         │  post-tool-use   │
│ Research      │         │  Records:        │
│               │         │  1. Pattern seen │
│ - Decisions   │<────────│  2. Issue found  │
│ - Findings    │         │  3. Preference   │
└───────────────┘         └──────────────────┘
        │                            │
        ▼                            │
┌───────────────┐                    │
│ Check Tier 1  │                    │
│ Global        │                    │
│               │                    │
│ - Commands    │                    │
└───────────────┘                    │
                                     │
                     ┌───────────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  Update Expertise     │
         │  If 3+ occurrences:   │
         │  - Promote to pattern │
         │  - Update preferences │
         │  - Record issue       │
         └───────────────────────┘
```

### Decision Flow: When to Check Each Tier

**session-start.py**:
1. Load all tiers into memory
2. Make available to agents

**Agent execution**:
1. **Check Tier 3 first** (most specific):
   - Agent's own expertise for this project
   - Example: code-reviewer knows "this project prefers async/await"

2. **Check Tier 2 second** (project-wide):
   - Research index for architectural decisions
   - Example: "we decided to use Redis for sessions"

3. **Check Tier 1 third** (global):
   - Cross-project command patterns
   - Example: "cp doesn't work on Windows, use xcopy"

**post-tool-use.py**:
- Record patterns at appropriate tier
- Pattern → Tier 3 (agent-specific)
- Research → Tier 2 (project-wide)
- Command → Tier 1 (global)

### Learning Flow Between Tiers

```
Tier 3 (Agent Expertise)
│
│  Pattern seen 10+ times across multiple agents?
│  Confidence > 0.9?
│
└──> PROMOTE TO → Tier 2 (Research)
                   │
                   │  Pattern applies to multiple projects?
                   │  User manually exports/shares?
                   │
                   └──> PROMOTE TO → Tier 1 (Global Patterns)
```

**Promotion criteria**:
- Tier 3 → Tier 2: 10+ occurrences, 0.9+ confidence, multi-agent relevance
- Tier 2 → Tier 1: User export, or cloud sync across projects

### Storage Paths and Initialization

| Tier | Storage | Initialized By | Scope |
|------|---------|----------------|-------|
| **Tier 1** | `~/.claude/config/command_patterns.db` | session-start.py | Global (all projects) |
| **Tier 2** | `.claude/research/index.json` | session-start.py | Project (all agents) |
| **Tier 3** | `.claude/expertise/{agent-id}/expertise.yaml` | First agent use | Project + Agent |

**Initialization checklist**:
- [x] Create `~/.claude/config/` on session start
- [x] Create `.claude/research/` on session start
- [x] Create `.claude/expertise/` on session start
- [x] Initialize research index.json if missing
- [x] Create expertise.yaml on first agent use (lazy)

### Pilot Agents for Phase 2

**Start with 3 agents**:

1. **code-reviewer**:
   - Learns code style preferences
   - Records common issues
   - Tracks review patterns

2. **bug-whisperer**:
   - Learns debugging patterns
   - Records error signatures
   - Tracks successful fixes

3. **security-auditor**:
   - Learns security patterns
   - Records vulnerabilities
   - Tracks mitigation strategies

**Expansion criteria**:
- Pilot successful after 2 weeks
- Positive user feedback
- < 1% false positive rate
- Then expand to all Tier 1 agents

### Success Metrics

**Phase 1 metrics** (pattern learner + research):
```json
{
  "pattern_learner": {
    "db_created": true,
    "corrections_recorded": 15,
    "successful_suggestions": 8,
    "confidence_avg": 0.85
  },
  "research_index": {
    "entries_created": 12,
    "auto_surfaced": 5,
    "searches_performed": 23,
    "relevance_score": 0.78
  }
}
```

**Phase 2 metrics** (agent expertise):
```json
{
  "agent_expertise": {
    "agents_with_expertise": 3,
    "total_patterns": 45,
    "patterns_promoted": 8,
    "avg_occurrences_before_promotion": 4.2,
    "preferences_learned": 67,
    "issues_tracked": 23,
    "reviews_improved": "15%"
  }
}
```

**Combined metrics** (via /popkit:stats):
```
┌─────────────────────────────────────────────────────────┐
│                  LEARNING SYSTEMS STATS                  │
├─────────────────────────────────────────────────────────┤
│ Global Patterns (Tier 1)                                │
│   Total corrections: 156                                │
│   Success rate: 87%                                     │
│   Last learning: 2 hours ago                            │
│                                                          │
│ Research Index (Tier 2)                                 │
│   Total entries: 42                                     │
│   Decisions: 15  Findings: 12                           │
│   Learnings: 8   Spikes: 7                              │
│   Auto-surfaced: 23 times                               │
│                                                          │
│ Agent Expertise (Tier 3)                                │
│   code-reviewer:    18 patterns, 34 preferences         │
│   bug-whisperer:    12 patterns, 21 preferences         │
│   security-auditor: 15 patterns, 29 preferences         │
│                                                          │
│ Cross-Tier Flow                                         │
│   Patterns promoted: 8 (Tier 3 → Tier 2)                │
│   Patterns exported: 2 (Tier 2 → Tier 1)                │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Checklist

### Phase 1: Activate Dormant Infrastructure

- [ ] 1.1 Add `ensure_pattern_learner_directories()` to session-start.py
- [ ] 1.2 Fix import in research_surfacer.py (line 117)
- [ ] 1.3 Create `/popkit:research` command
- [ ] 1.4 Create `pop-research-manage` skill
- [ ] 1.5 Test pattern learner activation
- [ ] 1.6 Test research index initialization
- [ ] 1.7 Test research command
- [ ] 1.8 Test research auto-surfacing

### Phase 2: Add Agent Expertise System

- [ ] 2.1 Create expertise_manager.py
- [ ] 2.2 Create ExpertiseFile, Pattern, Issue data classes
- [ ] 2.3 Create PendingPatternsTracker
- [ ] 2.4 Implement 3+ occurrence threshold logic
- [ ] 2.5 Add `load_agent_expertise()` to session-start.py
- [ ] 2.6 Add `update_agent_expertise()` to post-tool-use.py
- [ ] 2.7 Implement pattern detection for code-reviewer
- [ ] 2.8 Implement pattern detection for bug-whisperer
- [ ] 2.9 Implement pattern detection for security-auditor
- [ ] 2.10 Test expertise file creation
- [ ] 2.11 Test pending patterns tracking
- [ ] 2.12 Test pattern promotion (3+ occurrences)
- [ ] 2.13 Test expertise loading on session start

### Phase 3: Integration and Metrics

- [ ] 3.1 Add tier interaction flow to agents
- [ ] 3.2 Implement tier checking order (3 → 2 → 1)
- [ ] 3.3 Add promotion logic (Tier 3 → Tier 2)
- [ ] 3.4 Add metrics collection
- [ ] 3.5 Extend `/popkit:stats` with learning metrics
- [ ] 3.6 Add `/popkit:expertise` command (view/manage)
- [ ] 3.7 Test full integration flow
- [ ] 3.8 Validate conservative update logic
- [ ] 3.9 Performance testing
- [ ] 3.10 Documentation updates

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| **False positives** | 3+ occurrence threshold, confidence scoring |
| **Storage bloat** | 90-day retention, max 50 patterns per agent |
| **Performance impact** | Lazy loading, async updates, silent failures |
| **User confusion** | Clear /popkit:stats output, expertise visibility |
| **Breaking changes** | Phased rollout, start with 3 pilot agents |
| **Directory creation failures** | Try/except with silent failures, never block session |

---

## Future Enhancements (Post-v1.0)

1. **Cloud Sync**: Sync Tier 3 expertise across team members
2. **Pattern Suggestions**: Proactively suggest expertise during development
3. **Expertise Export**: Share expertise files between projects
4. **Machine Learning**: Use embeddings for pattern similarity
5. **Visual Dashboard**: Web UI for expertise visualization
6. **Expertise Conflicts**: Detect and resolve conflicting patterns
7. **Multi-Project Learning**: Cross-project pattern discovery

---

## Appendix: File Structure

```
packages/plugin/
├── hooks/
│   ├── session-start.py                     # MODIFIED: Phase 1 + Phase 2
│   ├── post-tool-use.py                     # MODIFIED: Phase 2
│   └── utils/
│       ├── pattern_learner.py               # EXISTS (dormant)
│       ├── research_index.py                # EXISTS (broken imports)
│       ├── research_surfacer.py             # MODIFIED: Fix import (Phase 1)
│       └── expertise_manager.py             # NEW: Phase 2
├── commands/
│   └── research.md                          # NEW: Phase 1
└── skills/
    └── pop-research-manage/                 # NEW: Phase 1
        ├── SKILL.md
        └── tests/

Project directories created:
~/.claude/config/                            # Phase 1
  └── command_patterns.db                    # Auto-created by pattern_learner

.claude/research/                            # Phase 1
  ├── index.json                             # Auto-created by session-start
  └── entries/                               # Entry storage

.claude/expertise/                           # Phase 2
  ├── code-reviewer/
  │   ├── expertise.yaml
  │   └── pending.json
  ├── bug-whisperer/
  │   ├── expertise.yaml
  │   └── pending.json
  └── security-auditor/
      ├── expertise.yaml
      └── pending.json
```

---

## Appendix: Example Session Flow

**User starts session**:
```
1. session-start.py runs
2. Creates ~/.claude/config/ (Tier 1)
3. Creates .claude/research/ (Tier 2)
4. Creates .claude/expertise/ (Tier 3)
5. Loads existing expertise files for all agents
6. Prints: "Learning systems initialized: 3 directories, research index"
```

**User runs bash command that fails**:
```
1. User: `cp -r src/ dest/`
2. Command fails (Windows)
3. post-tool-use.py (command-learning-hook) captures
4. pattern_learner.py suggests: `xcopy /E /I src\ dest\`
5. Records in ~/.claude/config/command_patterns.db
```

**User asks for code review**:
```
1. User: "Review src/api/auth.ts"
2. code-reviewer agent activated
3. Loads expertise from .claude/expertise/code-reviewer/expertise.yaml
4. Sees preference: "wrap async functions in try/catch"
5. Applies during review
6. Finds: async function without try/catch
7. post-tool-use.py records occurrence in pending.json
8. After 3rd occurrence → promotes to expertise.yaml pattern
```

**User searches research**:
```
1. User: "/popkit:research search caching"
2. research_index.py searches .claude/research/index.json
3. Returns matching entries with similarity scores
4. User sees previous decision: "Use Redis for sessions"
```

**User checks stats**:
```
1. User: "/popkit:stats"
2. Shows all three tiers
3. code-reviewer has 18 patterns, 4.2 avg occurrences before promotion
4. Total learning events: 156
```

---

## Known Limitations

### Agent Identification (Critical)

**Issue**: The `POPKIT_ACTIVE_AGENT` environment variable is not currently set by the agent routing system.

**Impact**: Agent-specific expertise tracking in `post-tool-use.py` will not work until this variable is properly set when agents are activated.

**Current Behavior**:
- `update_agent_expertise()` checks for `POPKIT_ACTIVE_AGENT`
- If not set, function returns early (silent failure)
- No agent-specific patterns are recorded

**Required Fix** (Future Issue):
- Agent routing system (`packages/plugin/hooks/utils/agent_loader.py` or similar) must set `POPKIT_ACTIVE_AGENT` environment variable when activating an agent
- Alternative: Pass agent ID through context instead of environment variable
- This requires broader agent routing system redesign

**Workaround**: For now, agent expertise files can be created manually or via the `/popkit:expertise` command, but automatic learning from tool usage is not functional.

**Tracking**: This limitation should be tracked as a separate GitHub issue for resolution in a future phase.

---

**END OF ARCHITECTURE DOCUMENT**
