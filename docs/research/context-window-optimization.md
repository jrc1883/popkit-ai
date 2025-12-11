# Research: Context Window Optimization for Complex GitHub Issues

**Date**: December 2025
**Author**: Claude Code Analysis
**Status**: Research Document
**Topic**: Context Pruning & Optimization Strategies for PopKit Development Workflows

---

## Executive Summary

This document explores **context pruning** - selectively clearing conversation history at strategic workflow boundaries - to optimize Claude's performance on complex GitHub issues within PopKit. Research shows that focused, pruned context can improve performance by 29-39% compared to broad context, while reducing token consumption by up to 84%.

**Key Finding**: Starting a complex issue with a **cleared context window** containing only the well-defined issue details + essential PopKit capabilities can significantly improve efficiency and reasoning quality.

---

## Table of Contents

1. [Problem Statement](#problem-statement)
2. [Claude Official Guidance on Context](#claude-official-guidance-on-context)
3. [Current PopKit Architecture](#current-popkit-architecture)
4. [Context Pruning Concept](#context-pruning-concept)
5. [Proposed Implementation Strategy](#proposed-implementation-strategy)
6. [Integration Points](#integration-points)
7. [Detailed Design Patterns](#detailed-design-patterns)
8. [Implementation Roadmap](#implementation-roadmap)
9. [Open Questions & Future Work](#open-questions--future-work)

---

## Problem Statement

### Current Challenge

When starting work on a complex GitHub issue within PopKit:

1. **Accumulated Conversation History**: Previous tool calls, failed attempts, and unrelated context persist in the conversation
2. **Stale File Contents**: Read operations from earlier in the session no longer reflect current file state
3. **Noise from Discovery**: Search results and explorations for abandoned approaches clutter the context
4. **Token Inefficiency**: Claude's context window is filled with content that's already documented externally:
   - Issue details are in GitHub
   - Changes are in Git commits
   - Task status is in STATUS.json
   - Previous decisions are in comments

### Performance Impact

- **Bloated context**: Conversation can exceed 50K tokens before meaningful work begins
- **Model confusion**: Older context can conflict with new understandings
- **Cost**: Every token costs money; 50K unnecessary tokens = 25% of a 200K context window wasted
- **Reasoning quality**: Claude performs better with focused context vs. scattered information

---

## Claude Official Guidance on Context

### 1. Focus Improves Performance

**Official Finding**: "Focusing on only relevant context increases effective model performance."

**Quantified Results**:
- **Context editing + memory tool**: 39% performance improvement over baseline
- **Context editing alone**: 29% performance improvement
- **Token reduction**: 84% reduction in token consumption for agent workflows

**Source**: Anthropic's official guidance on long context window optimization

### 2. Context Positioning Matters

For long documents (>20K tokens):
- **Place documents near the top** of the prompt hierarchy (above instructions)
- **Quote extraction first**: Ask Claude to quote relevant sections before proceeding
- **Results**: Significantly improves recall and accuracy across all models

### 3. Extended Thinking Trades Latency for Quality

- **Thinking budgets**: Claude can allocate computation to reasoning (10K-48K tokens depending on model)
- **Performance**: High effort levels exceed lower effort by 4.3% while using 48% fewer tokens
- **Best for**: Complex tasks requiring deep reasoning (exactly like complex GitHub issues)

### 4. Automatic Context Editing (Claude Sonnet 4.5)

Built-in features:
- Tracks available tokens throughout conversations
- **Removes stale tool results** from context automatically
- Preserves thinking blocks from previous turns
- Enables longer conversations without manual intervention

### 5. Prompt Caching Strategy

For reusable content:
- Cache system instructions and background knowledge
- Separate caching layers for different content types
- **Results**: Up to 90% cost reduction, 85% latency reduction

---

## Current PopKit Architecture

### Session Management (Already Implemented)

PopKit has a **three-tier session management system**:

#### Tier 1: Session Capture & Resume
- **`pop-session-capture`** skill: Saves complete state to `STATUS.json`
  - Git state (branch, commits, uncommitted files)
  - Task tracking (in-progress, completed, blocked)
  - Focus area and blockers
  - Key decisions and project data

- **`pop-session-resume`** skill: Restores context intelligently
  - Detects session type: Continuation (<30 min), Resume (30 min-4 hrs), Fresh Start (>4 hrs)
  - Auto-triggered by `session-start.py` hook

- **`pop-context-restore`** skill: Full context restoration for complex work

#### Tier 2: Checkpoints for Long-Running Work
- **`checkpoint.py`**: Creates snapshots with recovery support
- Auto-triggers on: build failure, test failure, stuck detection, phase completion
- Stored in `~/.claude/popkit/checkpoints/[session_id]/`
- Max 10 checkpoints per session

#### Tier 3: Token Monitoring
- **`context-monitor.py`** hook: Tracks token usage with thresholds
  - 60% usage: Informational
  - 80% usage: Suggest summarization
  - 90% usage: Suggest session capture
  - 95% usage: Urgent warning

### Hook System for Integration

PopKit hooks fire at strategic points:
- **PreToolUse**: Before any tool execution (safety checks, coordination)
- **PostToolUse**: After tools complete (analysis, metrics, decisions)
- **UserPromptSubmit**: When user submits input (routing, security)
- **SessionStart**: When Claude Code starts
- **Stop**: When user ends session

**Key Integration Points**:
- `pre-tool-use.py`: 5s timeout, runs before every tool
- `post-tool-use.py`: 5s timeout, runs after every tool
- `context-monitor.py`: 3s timeout, tracks tokens
- `user-prompt-submit.py`: 3s timeout, keyword detection and routing

### Current Context Structures

**Immutable Context Carrier** (`context_carrier.py`):
- Frozen dataclass for pure functional context passing
- JSON-serializable for persistence/transmission
- Tracks: session_id, tool_name, tool_input, message_history, tool_result, environment

**Status File** (`STATUS.json`):
```json
{
  "git": {"branch": "...", "lastCommit": "..."},
  "tasks": {"inProgress": [], "completed": []},
  "services": {"devServer": {}, "database": {}},
  "context": {"focusArea": "...", "blocker": null},
  "projectData": {"testStatus": "...", "buildStatus": "..."}
}
```

---

## Context Pruning Concept

### Definition

**Context Pruning** = Selectively clearing conversation history at strategic workflow boundaries while preserving:
1. The well-defined GitHub issue
2. Essential PopKit capabilities and instructions
3. Current task state (STATUS.json)
4. Recent critical decisions

### Why This Works

1. **Externalized State**: Everything important is documented outside the conversation:
   - Issue details → GitHub
   - Code state → Git commits
   - Task status → STATUS.json
   - Previous decisions → Git commit messages + comments

2. **Focused Window**: New conversation window contains:
   - Clear problem statement (the issue)
   - Necessary tools and capabilities (PopKit commands)
   - Current position (STATUS.json)
   - Essential context only

3. **Model Performance**: Claude performs better with:
   - Clearly defined task (GitHub issue)
   - Focused context (no noise)
   - Explicit instructions (PopKit CLAUDE.md)
   - Extended thinking enabled (for complexity)

### Mental Model

Think of it like starting a fresh day at work:

**Without Pruning** (Inefficient):
- You arrive at your desk with all yesterday's papers scattered around
- Notes from last week's failed approach still visible
- Three abandoned coffee cups taking up space
- Have to mentally filter what's still relevant

**With Pruning** (Efficient):
- Clean desk to start the day
- Today's task clearly written on top
- Essential reference materials nearby
- All context is current and relevant

---

## Proposed Implementation Strategy

### Phase 0: Research & Planning (Current)

✓ Document Claude's official guidance
✓ Analyze PopKit's current architecture
✓ Design pruning strategy
⚠️ **Open Questions**: Integration timing, preservation rules

### Phase 1: Issue-Based Context Pruning (Foundation)

**When**: When user starts working on GitHub issue with `/popkit:dev work #N`

**What Gets Pruned**:
- Conversation history from previous issue work
- Old file reads and search results
- Previous tool outputs and test results
- Abandoned exploration paths

**What Gets Preserved**:
- GitHub issue details (title, description, comments)
- STATUS.json (current task state)
- PopKit CLAUDE.md (project instructions)
- Current branch/file state
- Extended thinking for complex analysis

**Implementation**:
- Create `context-pruning.py` hook to handle issue transitions
- Extend `user-prompt-submit.py` to detect `/popkit:dev work #N` pattern
- Trigger pruning before issue context is loaded
- Preserve only essential context in new conversation window

### Phase 2: Phase Boundary Pruning (Smart Clearing)

**When**: At issue workflow phase transitions (Discovery → Architecture → Implementation → Testing)

**Integration with Existing**:
- Extends `issue-workflow.py` phase completion logic
- Uses existing context boundary concept from `context-boundary-hook.md`
- Leverages retention tier system from `tiered-retention-policy.md`

**What Gets Cleared at Each Phase**:
- **Discovery → Architecture**: Old search results, exploratory reads
- **Architecture → Implementation**: Design notes, requirement reads (preserved in planning docs)
- **Implementation → Testing**: File edits confirmations, code changes (preserved in commits)
- **Testing → Review**: Test output, debug traces (preserved in test reports)

**Implementation**:
- Extend `context-monitor.py` with phase-aware thresholds
- Create phase transition suggestions in hooks
- Auto-clear or prompt based on aggressiveness setting

### Phase 3: Tiered Retention (Automatic Expiration)

**Builds On**: `tiered-retention-policy.md` already designed

**Retention Tiers**:

| Tier | Content | TTL | Trigger |
|------|---------|-----|---------|
| **Ephemeral** | Edit confirmations, mkdir | 1 call | Next tool |
| **Short** | Search results | 5 calls | New search same pattern |
| **Medium** | File contents | Until edit | Edit or commit |
| **Session** | Test/build output | Until rerun | Same command re-run |
| **Preserved** | Errors, decisions | Never | Manual only |

**Integration**:
- Implement `retention_tracker.py` utility
- Extend `post-tool-use.py` for retention tracking
- Add expiration checking on each tool call
- Include retention status in `context-monitor.py` output

### Phase 4: GitHub Issue Optimization (Advanced)

**Concept**: Special handling when starting work on GitHub issue

**Strategy**:
1. **Load Issue Context**:
   - Fetch issue title, description, comments
   - Extract PopKit Guidance section
   - Load recent related commits
   - Check current branch vs issue branch

2. **Build Minimal Context**:
   - Issue details (essential for understanding)
   - PopKit Guidance (workflow instructions)
   - Current STATUS.json (task state)
   - Recent decision comments (context)

3. **Preserve Window for Work**:
   - Clear conversation history
   - Load issue + guidance + status
   - Run extended thinking if complexity detected
   - Begin fresh work session

**Implementation**:
- Create `github-issue-context.py` hook
- Implement issue-aware pruning in `user-prompt-submit.py`
- Integrate with `/popkit:dev work #N` command
- Auto-detect issue complexity → enable extended thinking

### Phase 5: Memory & External Brain (Future)

**Concept**: Move discoveries to persistent storage at pruning boundaries

**Storage**:
- `~/.claude/popkit/brain/insights.json` - Learned patterns
- `~/.claude/popkit/brain/decisions.db` - Previous decisions
- `~/.claude/popkit/brain/discoveries/` - Category-based learnings

**Retrieval**:
- Semantic search for related insights
- Decision history for similar issues
- Pattern matching against current issue

**When to Use**: At context pruning boundaries, externalize insights for cross-issue learning

---

## Integration Points

### 1. Hook System Integration

**New Hooks to Create**:

```
hooks/
├── context-pruning.py          NEW: Issue-based pruning
├── github-issue-context.py     NEW: GitHub issue optimization
└── utils/
    └── retention_tracker.py    NEW: Tiered retention management
```

**Modified Hooks**:
- `post-tool-use.py`: Add retention tracking
- `context-monitor.py`: Add phase/issue-aware thresholds
- `user-prompt-submit.py`: Detect issue start, trigger pruning

**Hook Configuration** (`hooks/hooks.json`):
```json
{
  "PreToolUse": [
    {
      "matcher": "Task",
      "hooks": [
        "github-issue-context.py"  // NEW: Detect issue work
      ]
    }
  ],
  "PostToolUse": [
    {
      "matcher": "Bash|Read|Edit",
      "hooks": [
        "context-pruning.py"  // NEW: Track pruning points
      ]
    }
  ]
}
```

### 2. Command Integration

**Modify `/popkit:dev work` Command**:
- Add flags: `--context-clear`, `--preserve-context`
- Detect issue complexity automatically
- Enable extended thinking for epics/architecture

**New `/popkit:context` Command**:
- `status`: Show context usage
- `retention`: View retention tiers
- `prune`: Manually trigger pruning
- `clear`: Clear specific tiers

### 3. Configuration Integration

**New Config File**: `packages/plugin/hooks/pruning-config.json`

```json
{
  "issue_pruning": {
    "enabled": true,
    "preserve_on_start": [
      "issue_details",
      "status_json",
      "popkit_guidance",
      "recent_commits:3"
    ],
    "clear_on_issue_change": true,
    "complexity_detection": {
      "enable_thinking": true,
      "epic_budget_tokens": 24000,
      "architecture_budget_tokens": 16000,
      "bug_budget_tokens": 8000
    }
  },
  "phase_boundaries": {
    "enabled": true,
    "aggressive_clear": ["test_passed", "pr_created"],
    "moderate_clear": ["phase_complete"],
    "conservative_clear": ["issue_closed"]
  },
  "retention_tiers": {
    "ephemeral": {"ttl_tools": 1},
    "short": {"ttl_tools": 5},
    "medium": {"expiry_events": ["edit", "commit"]},
    "session": {"expiry_events": ["supersede"]},
    "preserved": {"expiry_events": ["manual"]}
  }
}
```

### 4. Status Line Display

**Extend Power Mode Status Line**:
```
[POP] #57 Phase: impl (2/4) | CTX: 62k/200k [pruning: ready]
```

Show when pruning would be beneficial:
- Token usage trending high
- Phase boundary approaching
- Large file reads accumulating

### 5. Output Style Integration

**Create `context-pruning.md` output style**:
- Summary of what's being pruned
- Tokens reclaimed
- What's being preserved
- Confirmation before proceeding

---

## Detailed Design Patterns

### Pattern 1: Issue-Start Context Optimization

**Trigger**: `/popkit:dev work #N`

```python
class IssueContextOptimizer:
    def __init__(self, issue_number: int):
        self.issue = self.fetch_issue(issue_number)
        self.guidance = self.parse_popkit_guidance(self.issue.body)
        self.complexity = self.detect_complexity()

    def build_minimal_context(self) -> Dict:
        """Build context window with issue + guidance + status."""
        return {
            "issue": {
                "number": self.issue.number,
                "title": self.issue.title,
                "description": self.issue.body,
                "labels": self.issue.labels,
                "complexity": self.complexity
            },
            "guidance": self.guidance,
            "status": self.load_status_json(),
            "branch": self.get_current_branch(),
            "recent_commits": self.get_recent_commits(n=3)
        }

    def should_enable_extended_thinking(self) -> bool:
        """Enable thinking for epic/architecture issues."""
        return self.complexity in ["epic", "architecture", "large"]

    def get_thinking_budget(self) -> int:
        """Budget tokens based on complexity."""
        budgets = {
            "small": 5000,
            "medium": 10000,
            "large": 16000,
            "architecture": 20000,
            "epic": 24000
        }
        return budgets.get(self.complexity, 10000)
```

**Flow**:
1. User types `/popkit:dev work #57`
2. Hook detects pattern
3. Fetch issue #57 from GitHub
4. Parse PopKit Guidance section
5. Detect complexity (epic/architecture/bug/feature)
6. **PRUNE**: Clear old conversation history
7. **LOAD**: Issue details + guidance + STATUS.json
8. **ENABLE**: Extended thinking if epic/architecture
9. **READY**: Fresh context window, focused task

### Pattern 2: Phase Boundary Pruning

**Trigger**: Issue workflow phase completion

```python
class PhaseBoundaryPruner:
    def on_phase_complete(self, phase_name: str, issue_number: int):
        """Handle pruning at phase boundaries."""

        # Get current retention state
        tracker = RetentionTracker.load(session_id)

        # Identify what can be safely cleared
        expired = tracker.get_expired_items()

        # Content safe to clear at this phase
        phase_safe = {
            "discovery": ["search_results", "exploratory_reads"],
            "architecture": ["requirement_files", "design_notes"],
            "implementation": ["edit_confirmations", "file_contents"],
            "testing": ["test_output", "debug_traces"]
        }

        # Build clearing suggestion
        suggestion = {
            "phase": phase_name,
            "safe_to_clear": phase_safe.get(phase_name, []),
            "tokens_reclaimable": self.estimate_tokens(expired),
            "preserve": ["current_task", "last_error", "decision_log"]
        }

        # Suggest or auto-clear based on setting
        if self.aggressiveness == "aggressive":
            return self.execute_clear(suggestion)
        else:
            return self.suggest_clear(suggestion)
```

**Benefits**:
- Each phase starts with relevant context only
- Old discoveries don't interfere with new phases
- Natural clearing points match workflow
- User can opt-in or auto-enable

### Pattern 3: Tiered Retention System

**Trigger**: Every tool call

```python
class RetentionTracker:
    TOOL_TIERS = {
        "Read": "medium",        # Expires on edit/commit
        "Grep": "short",         # Expires after 5 calls
        "Edit": "ephemeral",     # Gone next call
        "Bash": {
            "default": "session",
            "npm test": "session",
            "git commit": "ephemeral"
        }
    }

    def track_tool_result(self, tool_name: str, tool_input: Dict, result: str):
        """Assign retention tier to tool result."""

        tier = self._get_tier(tool_name, tool_input)
        meta = ToolResultMeta(
            tool_name=tool_name,
            retention_tier=tier,
            expiry_trigger=self._get_expiry(tier, tool_input),
            token_estimate=estimate_tokens(result),
            timestamp=now()
        )

        self.results[meta.id] = meta
        self.save_state()

        # Check for expirations
        expired = self.check_expirations()
        return {
            "tier": tier,
            "expires_on": meta.expiry_trigger,
            "expired_count": len(expired),
            "reclaimable_tokens": sum(r.token_estimate for r in expired)
        }
```

**Efficiency Gains**:
- Automatically removes stale content
- Prevents false positives (no premature clearing)
- Metrics track what's being cleared and why
- Configurable per-project

### Pattern 4: Issue-Aware Context Loading

**Trigger**: Before any GitHub issue work

```python
class GitHubIssueContextLoader:
    def load_for_issue(self, issue_number: int) -> str:
        """Build Claude-ready context for issue work."""

        issue = self.fetch_issue(issue_number)
        guidance = self.parse_guidance(issue.body)

        # Build minimal context
        context = f"""
# Issue #{issue_number}: {issue.title}

## Description
{issue.body}

## Current Status
{json.dumps(self.load_status_json(), indent=2)}

## Your Task
Based on the PopKit Guidance below, your job is to:
1. {guidance['primary_task']}
2. Follow the phases: {' → '.join(guidance['phases'])}
3. Use suggested agents: {', '.join(guidance['agents'])}

## Important
- Don't re-read files already in Git
- Reference commits instead: git show HEAD:file.ts
- Focus on what's NOT yet committed
- Check STATUS.json for recent context

{self.build_popkit_instructions()}
"""

        return context
```

**Key Features**:
- Issue is the center of context
- Guidance drives workflow
- STATUS.json shows current position
- PopKit instructions are always available
- Reference external state, don't repeat it

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

**Goal**: Enable issue-start context pruning

**Tasks**:
1. Create `context-pruning.py` hook
   - Detect `/popkit:dev work #N` patterns
   - Fetch issue from GitHub
   - Parse PopKit Guidance
   - Trigger pruning signal

2. Extend `user-prompt-submit.py`
   - Recognize issue start patterns
   - Trigger context clearing before issue loading
   - Preserve essential context

3. Create `pruning-config.json`
   - Issue pruning settings
   - Preservation rules
   - Aggressiveness levels

**Testing**:
- Test with sample issues
- Verify context is cleared
- Confirm issue details are loaded

**Deliverable**: `/popkit:dev work #N` clears old context, loads issue fresh

### Phase 2: Phase Boundaries (Week 2-3)

**Goal**: Smart clearing at issue workflow phases

**Tasks**:
1. Extend `context-monitor.py`
   - Add phase-aware thresholds
   - Different clearing rules per phase
   - Phase transition detection

2. Enhance `issue-workflow.py`
   - Trigger pruning on phase completion
   - Generate phase-specific clearing suggestions
   - Preserve phase-critical context

3. Create phase transition output style
   - Show what's being cleared
   - Why it's safe to clear
   - Tokens being reclaimed

**Testing**:
- Test phase transitions
- Verify appropriate items cleared
- Check preservation rules

**Deliverable**: Phase transitions trigger intelligent context pruning

### Phase 3: Tiered Retention (Week 3-4)

**Goal**: Automatic expiration based on content type

**Tasks**:
1. Create `hooks/utils/retention_tracker.py`
   - Implement tier assignment logic
   - TTL and supersession tracking
   - State persistence

2. Extend `post-tool-use.py`
   - Track retention on each tool
   - Check for expirations
   - Generate clearing opportunities

3. Add retention to `context-monitor.py`
   - Include expired items in output
   - Suggest tier-based clearing
   - Track reclamable tokens

4. Create `/popkit:context` command
   - View retention status
   - Clear specific tiers
   - Adjust aggressiveness

**Testing**:
- Verify tier assignments
- Test TTL expiration
- Check supersession detection
- Track token savings

**Deliverable**: Automatic context expiration with retention tiers

### Phase 4: GitHub Integration (Week 4-5)

**Goal**: Issue-optimized context loading

**Tasks**:
1. Create `github-issue-context.py` hook
   - Fetch issue from GitHub
   - Parse guidance + metadata
   - Detect complexity

2. Create `IssueContextOptimizer` class
   - Build minimal context window
   - Enable extended thinking for epics
   - Load essential references

3. Integrate with existing commands
   - `/popkit:dev work #N` uses optimizer
   - Auto-detect issue complexity
   - Set thinking budget

**Testing**:
- Test with sample complex issues
- Verify extended thinking enabled
- Check context quality

**Deliverable**: `/popkit:dev work #N` optimizes context for issue

### Phase 5: Analytics & Refinement (Week 5-6)

**Goal**: Measure impact and optimize

**Tasks**:
1. Add efficiency metrics
   - Track tokens saved by pruning
   - Monitor context size trends
   - Measure phase completion times

2. Create analytics dashboard
   - Pruning frequency/impact
   - Retention tier distribution
   - Cost savings

3. Gather feedback
   - Are users getting better results?
   - What's the right aggressiveness level?
   - What edge cases need handling?

**Deliverable**: Metrics showing efficiency improvements

---

## Open Questions & Future Work

### Design Questions

**Q1: When to Prune Automatically vs. Prompt?**
- **Option A**: Auto-prune when issue changes (disruptive but efficient)
- **Option B**: Always ask before pruning (safer but slower)
- **Option C**: Prune in Power Mode, ask otherwise (balanced)
- **Recommendation**: Option C - Power Mode is for complex work where efficiency matters

**Q2: What's the Minimum Preservation Set?**
- **Current Proposal**: Issue + Guidance + STATUS.json + 3 recent commits
- **Question**: Is this enough? Do we need:
  - Last error/blocker context?
  - Decision log?
  - Recently edited files?
- **Approach**: Start conservative, expand based on feedback

**Q3: How to Handle Cross-Issue Context?**
- **Challenge**: Sometimes solution to issue #57 depends on context from #56
- **Options**:
  - Load as "related issue" context
  - Use git blame to reference earlier work
  - Don't preserve cross-issue (rely on Git)
- **Recommendation**: Use Git as source of truth, load related issues explicitly if needed

**Q4: Extended Thinking Budget Strategy?**
- **Current Proposal**: 5k for bugs, 10k for features, 20k for architecture, 24k for epics
- **Questions**:
  - Should budget vary by model (Sonnet vs Haiku)?
  - Should users be able to override?
  - What's the cost-benefit tradeoff?
- **Approach**: Start with above, measure performance impact

**Q5: User Control / Override?**
- **Proposal**: Flags `--context-clear`, `--preserve-context`, `--aggressive`, `--conservative`
- **Questions**:
  - Should users be able to "pin" items to preserved tier?
  - Environment variable to set default aggressiveness?
  - `/popkit:context` commands for manual control?
- **Recommendation**: Yes to all - give users control but smart defaults

### Technical Debt / Edge Cases

**Edge Case 1: What if user manually reads file before edit?**
- Scenario: Read file.ts, think about it, then edit
- Current TTL: Expires on edit (correct!)
- Edge case: What if user wants to see before/after?
- Solution: Keep edit confirmation with diff, not full file

**Edge Case 2: Partial file reads**
- Scenario: Read lines 1-100, then 50-150
- Are these related? Should second read extend TTL?
- Solution: Hash-based deduplication - if overlap, track together

**Edge Case 3: Long-running debugging sessions**
- Scenario: 50+ test runs, each produces output
- Current: Each run "supersedes" the previous
- Edge case: Sometimes you want to compare two test runs
- Solution: Pin important test outputs manually before they expire

**Edge Case 4: Context boundary in middle of task**
- Scenario: Building feature, context fills up mid-phase
- Current: Can't prune (would lose needed context)
- Solution: Suggest checkpoint instead of prune

### Future Enhancements

**A. Cross-Issue Learning (External Brain)**
```
~/.claude/popkit/brain/
├── insights/
│   ├── authentication-patterns.json
│   ├── performance-optimization.json
│   └── error-handling-strategies.json
├── decisions.db
└── learnings.md
```

- Automatically externalize insights at pruning boundaries
- Retrieve related learnings when starting new issue
- Cross-project learning for PopKit users

**B. Smart Context Reconstruction**
- If user needs old context after pruning, suggest:
  - Git blame to find relevant commit
  - GitHub search for related discussion
  - Semantic search in external brain
- Minimize manual re-reading

**C. Predictive Pruning**
- ML model predicts when context will become irrelevant
- Proactively suggest pruning before user hits limits
- Learn from user's patterns over time

**D. Context Watermarking**
- Mark important context with retention hints
- "This decision matters for Phase 3" → extend TTL
- User can mark critical context for preservation

**E. Session Merge/Split**
- Split long session into multiple shorter sessions
- Each gets fresh context + relevant state
- Automatic session boundaries based on:
  - Phase transitions
  - Time-based (4+ hours)
  - Token usage (approaching limit)

---

## Conclusion

**Context pruning is the missing link** between PopKit's excellent session management and Claude's preference for focused, relevant context.

### Key Takeaways

1. **Claude performs better with focused context**: 29-39% improvement documented by Anthropic
2. **PopKit already externalizes state**: Issue, commits, STATUS.json mean context pruning is safe
3. **Natural pruning points exist**: Phase transitions, issue changes, phase boundaries
4. **Implementation is straightforward**: Hooks + config + optional user flags
5. **Benefits are quantifiable**: Token savings, performance gains, efficiency metrics

### Next Steps

1. **Get Feedback**: Share this research with PopKit team
2. **Phase 1 Implementation**: Start with issue-start context pruning
3. **User Testing**: Test with real complex issues
4. **Measure Impact**: Track efficiency gains and refine approach
5. **Iterate**: Expand to phase boundaries, retention tiers based on learnings

### Vision

PopKit will evolve to be not just a plugin that automates workflow, but one that **optimizes the conversation itself** - pruning noise, preserving signal, keeping Claude focused and efficient.

---

## Appendix: Code Sketch Examples

### Hook: context-pruning.py

```python
#!/usr/bin/env python3
"""
Context Pruning Hook
Detects workflow boundaries and suggests/executes context clearing.
"""

import json
import sys
from pathlib import Path

class ContextPruningHook:
    def __init__(self):
        self.config = self.load_config()

    def detect_issue_start(self, prompt: str) -> Optional[int]:
        """Detect /popkit:dev work #N pattern."""
        import re
        match = re.search(r'/popkit:dev\s+work\s+#(\d+)', prompt)
        return int(match.group(1)) if match else None

    def detect_phase_transition(self, tool_result: str) -> Optional[str]:
        """Detect phase completion."""
        if "Phase transition" in tool_result:
            import re
            match = re.search(r'Phase: (\w+) → (\w+)', tool_result)
            return match.group(2) if match else None
        return None

    def build_pruning_suggestion(self, event_type: str, context: Dict) -> Dict:
        """Build what should be pruned."""
        suggestions = {
            "issue_start": {
                "preserve": ["issue_details", "popkit_guidance", "status_json"],
                "clear": ["old_tool_results", "previous_issue_context"],
                "action": "prune_aggressive"
            },
            "phase_transition": {
                "preserve": ["current_task", "phase_decision"],
                "clear": self.get_phase_specific_clears(context.get("phase")),
                "action": "prune_moderate"
            }
        }
        return suggestions.get(event_type, {})

    def process(self, input_data: Dict) -> Dict:
        tool_input = input_data.get("tool_input", {})
        prompt = input_data.get("user_prompt", "")

        # Check for issue start
        issue_num = self.detect_issue_start(prompt)
        if issue_num:
            suggestion = self.build_pruning_suggestion("issue_start", {"issue": issue_num})
            return {
                "type": "issue_start",
                "issue_number": issue_num,
                "suggestion": suggestion,
                "action": "prune_aggressive" if self.config["auto_prune"] else "suggest"
            }

        return {"type": "no_pruning"}

if __name__ == "__main__":
    hook = ContextPruningHook()
    input_data = json.load(sys.stdin)
    result = hook.process(input_data)
    print(json.dumps(result))
```

### Config: pruning-config.json

```json
{
  "issue_pruning": {
    "enabled": true,
    "auto_prune": true,
    "preserve_on_start": [
      "issue_title",
      "issue_description",
      "popkit_guidance",
      "status_json",
      "current_branch"
    ]
  },
  "phase_boundaries": {
    "discovery": {
      "clear_tiers": ["short"],
      "clear_items": ["search_results", "exploratory_reads"]
    },
    "implementation": {
      "clear_tiers": ["ephemeral"],
      "clear_items": ["edit_confirmations"]
    }
  },
  "retention": {
    "ephemeral": 1,
    "short": 5,
    "medium": "until_edit",
    "session": "until_supersede"
  }
}
```

---

**Document Version**: 1.0
**Last Updated**: December 11, 2025
**Status**: Ready for Review
