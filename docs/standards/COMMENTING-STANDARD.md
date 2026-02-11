# PopKit Code Commenting Standard v1.0

Guidelines for code comments across the PopKit plugin suite. These are guidelines, not enforced rules. Apply to new code; retroactive changes are not required.

## Principle

**Comments explain _why_, not _what_.** Code should be self-documenting through clear naming. Comments add context that the code cannot express: design decisions, tradeoffs, constraints, and non-obvious reasoning.

---

## Verbosity Levels

Choose the level that matches your file's complexity:

### Level 1: Sparse (1-3% comment ratio)

**When**: Simple utility functions, configuration files, straightforward CRUD.

```python
# Good - explains WHY this threshold exists
CONFIDENCE_THRESHOLD = 0.8  # Below this, results are unreliable (Issue #42)

# Bad - restates WHAT the code does
# Set threshold to 0.8
CONFIDENCE_THRESHOLD = 0.8
```

### Level 2: Moderate (5-8% comment ratio)

**When**: Business logic, data transformation, multi-step workflows. Most PopKit Python modules should target this level.

```python
def detect_workspace_type(root: Path) -> str:
    """Detect monorepo workspace type from marker files.

    Priority order matters: pnpm > lerna > popkit > yarn > npm.
    This matches the ecosystem convention where more specific
    tools take precedence over generic ones.
    """
```

### Level 3: Verbose (8-12% comment ratio)

**When**: Complex algorithms, security-sensitive code, performance-critical paths, pattern matching with heuristics.

```python
def calculate_confidence(edit_count: int, pattern_matches: int) -> float:
    """Calculate bug detection confidence score.

    Uses a weighted combination of edit frequency and pattern matches.
    The 0.1 weight per edit above 3 was calibrated against 200 manually
    reviewed bugs (see docs/research/confidence-calibration.md).

    Score range: 0.0-1.0, where:
    - 0.0-0.3: Low confidence, likely false positive
    - 0.3-0.7: Medium confidence, needs human review
    - 0.7-1.0: High confidence, likely true bug
    """
    # Base confidence from pattern matches (0.0-0.5 range)
    base = min(pattern_matches * 0.15, 0.5)

    # Edit frequency boost: files edited 3+ times in recent
    # commits are more likely to contain bugs (empirical)
    edit_boost = max(0, (edit_count - 3) * 0.1)

    return min(base + edit_boost, 1.0)
```

---

## Seven Comment Patterns

### 1. Design Philosophy

Explain **why** an architecture or approach was chosen.

```python
# PopKit uses CLI + caching instead of MCP for GitHub operations
# because it provides offline support and reduces token overhead.
# See CLAUDE.md "GitHub Integration Strategy" for full rationale.
```

### 2. Algorithm Explanation

Document inputs, outputs, and reasoning for non-trivial logic.

```python
def _build_stack_suggestions(detected: Optional[str]) -> List[Dict]:
    """Build ordered stack suggestions with detected stack first.

    The detected stack gets a "(Detected)" tag and is placed at
    position 0 so AskUserQuestion shows it as the default choice.
    Remaining stacks maintain their priority order (most common first).
    """
```

### 3. Security / Performance Implications

Flag security-sensitive or performance-critical code.

```python
# SECURITY: Sanitize user input before passing to subprocess.
# Raw input could enable command injection via shell metacharacters.
cmd = shlex.quote(user_input)

# PERFORMANCE: Cache GitHub labels for 60min to avoid API rate limits.
# Invalidated on label create/delete operations.
```

### 4. Issue References

Link code to the issue/PR that motivated it.

```python
# Issue #156: Ruff pre-commit hook auto-fixes Python files.
# Fails open if Ruff is not installed (never blocks on tool absence).
```

### 5. Magic Number Documentation

Every hardcoded constant needs a "why this value" comment.

```python
MAX_WORKSPACE_PROJECTS = 20  # UX limit: >20 packages overwhelms AskUserQuestion options
KEYWORD_SIMILARITY = 0.7     # Keyword match confidence (higher than file pattern's 0.6)
TIER1_MINIMUM = 3            # Always include 3 Tier 1 agents for baseline coverage
```

### 6. Integration Context

Document cross-service or cross-module dependencies.

```python
# This function is called by session-start.py (popkit-core hooks)
# and expects the AgentLoader to have been initialized with
# the embedding store. Falls back to keyword matching if not.
```

### 7. Type Assertion Explanations

When casting or asserting types, explain why it's safe.

```python
# Safe cast: config.json schema guarantees "tier" is always
# "free", "premium", or "pro" (validated at load time)
tier: str = config["tier"]  # type: ignore[assignment]
```

---

## Language-Specific Guidelines

### Python (Primary Language)

- **Module docstrings**: Required for all files. State purpose and relationship to PopKit.
- **Public function docstrings**: Required. Use Google-style format with Args/Returns.
- **Private functions**: Docstring optional, but add inline comments for non-obvious logic.
- **Constants**: Always document with inline comment explaining the value choice.
- **Target**: Level 2 (Moderate) for most modules, Level 3 for utils with heuristics.

### Markdown (Skills, Commands, Agents)

- **Frontmatter**: Description field serves as the "docstring" - make it clear and actionable.
- **Section headers**: Self-documenting; no additional comments needed.
- **HTML comments**: Use `<!-- -->` for implementation notes not shown to users.

### JSON (Configuration)

- JSON doesn't support comments. Use a companion `README.md` or inline the documentation in the schema's `description` fields.

---

## Anti-Patterns

Avoid these commenting mistakes:

```python
# BAD: Restating the code
i += 1  # Increment i by 1

# BAD: Outdated comment (worse than no comment)
# Returns a list of users  <-- actually returns a dict now
def get_users() -> Dict[str, User]: ...

# BAD: Commented-out code without explanation
# result = old_implementation(data)
result = new_implementation(data)

# GOOD: Commented-out code WITH context
# result = old_implementation(data)  # Removed in Issue #42, kept for rollback reference until v2.0
result = new_implementation(data)

# BAD: TODO without owner or issue
# TODO: fix this later

# GOOD: TODO with context
# TODO(Issue #85): Replace hardcoded timeout with config value
```

---

## Scope

- **Applies to**: All new code in `packages/shared-py/`, hook scripts, and skill scripts
- **Does not apply to**: Existing code (no retroactive changes required), test files (test names should be self-documenting), generated files
- **Enforcement**: Guidelines only for v1.0. Enforcement tooling tracked separately.
