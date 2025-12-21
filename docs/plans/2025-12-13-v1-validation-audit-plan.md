# PopKit v1.0.0 Validation Audit Plan

> **⚠️ ARCHITECTURE CHANGE (December 20, 2025)**
>
> This document was created under PopKit's original subscription model (free/pro/team tiers).
> PopKit's architecture has been redesigned to use an **API key enhancement model**:
>
> - All features work FREE locally
> - API key adds semantic intelligence enhancements
> - No subscription tiers or feature gating
>
> **New design:** See Epic #580 and `docs/plans/2025-12-20-plugin-modularization-design.md`
>
> The content below is preserved for reference but may not reflect current architecture.

---

**Created:** 2025-12-13
**Status:** ~~Planning~~ **DEPRECATED**
**Goal:** Comprehensive validation before public release

---

## Executive Summary

This plan outlines the complete validation strategy for PopKit v1.0.0 release. The goal is to ensure the plugin is production-ready, well-documented, and provides genuine value over baseline Claude Code usage.

### Current State

| Category | Count | Status |
|----------|-------|--------|
| Skills | 66+ | Need validation |
| Commands | 24 | Need testing |
| Agents (Tier 1) | 11 | Need validation |
| Agents (Tier 2) | 17 | Need validation |
| Hook utilities | 60+ | Mostly functional |
| Output styles | 15+ | Need review |
| Tests | 58+ hook tests | Passing |

### Milestones

| Milestone | Purpose | Issues |
|-----------|---------|--------|
| **v1.0.0** | Claude Code marketplace release | Active development |
| **v2.0.0** | Multi-model support, Universal MCP | #112, #113, #114, #115 |

---

## Part 1: Documentation Validation

### 1.1 Core Documentation Files

| File | Location | Priority | Checks |
|------|----------|----------|--------|
| CLAUDE.md | Root | P0 | Accurate counts, valid examples, up-to-date sections |
| README.md | packages/plugin | P0 | Working links, accurate commands, valid installation |
| CONTRIBUTING.md | packages/plugin | P1 | Clear guidelines, valid workflows |
| CHANGELOG.md | Root | P1 | Version accuracy, complete history |

**Validation Actions:**
- [ ] Verify all auto-generated sections match reality
- [ ] Test all code examples in documentation
- [ ] Validate all internal links resolve
- [ ] Check version numbers are synchronized

### 1.2 Skill Documentation (66+ skills)

Each skill SKILL.md should have:
- [ ] Proper YAML frontmatter (name, description)
- [ ] Clear trigger conditions
- [ ] Process steps that actually work
- [ ] Valid output format examples
- [ ] Related skills listed

**Automated Checks:**
```bash
# Validate frontmatter exists
for skill in packages/plugin/skills/*/SKILL.md; do
  if ! head -3 "$skill" | grep -q "^---"; then
    echo "Missing frontmatter: $skill"
  fi
done
```

### 1.3 Agent Documentation (28+ agents)

Each agent AGENT.md should have:
- [ ] Proper YAML frontmatter
- [ ] Clear purpose statement
- [ ] Valid tool list
- [ ] Routing triggers documented

### 1.4 Command Documentation (24 commands)

Each command .md should have:
- [ ] Description that matches actual behavior
- [ ] Valid subcommands and flags
- [ ] Working examples

---

## Part 2: Structure Validation

### 2.1 Expected Directory Structure

```
packages/plugin/
├── .claude-plugin/
│   ├── plugin.json          # Version: 0.2.1
│   └── marketplace.json     # Version: 0.2.1
├── agents/
│   ├── config.json          # All routing rules
│   ├── tier-1-always-active/  # 11 agents
│   ├── tier-2-on-demand/      # 17 agents
│   └── feature-workflow/      # 2 agents
├── skills/                    # 66+ skills
├── commands/                  # 24 commands
├── hooks/
│   ├── hooks.json            # Hook configuration
│   ├── pre-tool-use.py
│   ├── post-tool-use.py
│   └── utils/                # 60+ utilities
├── output-styles/            # 15+ templates
├── power-mode/               # Multi-agent orchestration
└── templates/mcp-server/     # MCP generator
```

### 2.2 Structure Validation Script

```python
# packages/plugin/tests/validate_structure.py
EXPECTED_COUNTS = {
    "skills": 55,      # Minimum expected
    "commands": 24,
    "tier-1-agents": 11,
    "tier-2-agents": 17,
    "hook-utils": 50,
    "output-styles": 15
}
```

### 2.3 Version Synchronization

Files that must have matching versions:
- packages/plugin/.claude-plugin/plugin.json
- packages/plugin/.claude-plugin/marketplace.json
- CHANGELOG.md header

---

## Part 3: Functional Validation

### 3.1 Command Testing Matrix

| Command | Subcommands | Test Status | Notes |
|---------|-------------|-------------|-------|
| `/popkit:dev` | full, work, brainstorm, plan, execute, quick, prd, suite | Pending | Core workflow |
| `/popkit:git` | commit, push, pr, review, ci, release, finish, prune | Pending | Git operations |
| `/popkit:routine` | morning, nightly | Pending | Day routines |
| `/popkit:project` | init, analyze, embed, generate, setup | Pending | Project setup |
| `/popkit:issue` | create, list, view, close, comment, edit, link | Pending | GitHub integration |
| `/popkit:power` | init, start, status, stop | Pending | Multi-agent |
| `/popkit:debug` | code, routing | Pending | Debugging |
| `/popkit:assess` | anthropic, security, performance, ux, architect, docs | Pending | Assessment |
| `/popkit:next` | quick, verbose | Pending | Recommendations |
| `/popkit:plugin` | test, docs, sync | Pending | Plugin meta |

### 3.2 Skill Testing Strategy

**Tier 1 Skills (Always Test):**
- pop-brainstorming
- pop-code-review
- pop-morning-generator
- pop-session-capture/resume
- pop-plugin-test

**Tier 2 Skills (Sample Test):**
- Random 20% of remaining skills
- Focus on premium-gated features

### 3.3 Agent Routing Validation

```bash
# Test routing decisions
/popkit:debug routing --verbose
```

Test cases:
1. "Fix this bug" → Should route to bug-whisperer
2. "Review my code" → Should route to code-reviewer
3. "Make it faster" → Should route to performance-optimizer
4. Working with .test.ts → Should activate test-writer-fixer

### 3.4 Hook Protocol Testing

Existing tests: `packages/plugin/tests/hooks/`
- 58 tests covering stateless hook pattern
- Message builder validation
- Context carrier tests

Run with: `/popkit:plugin test hooks`

---

## Part 4: Integration Validation

### 4.1 Fresh Installation Test

Test on a completely new project:

```bash
# 1. Create fresh project
mkdir test-project && cd test-project
git init

# 2. Install popkit from marketplace
/plugin marketplace add jrc1883/popkit-claude
/plugin install popkit@popkit-claude

# 3. Restart Claude Code

# 4. Verify commands available
/popkit:routine morning
/popkit:dev brainstorm "test feature"
```

### 4.2 Multi-Project Compatibility

Test PopKit in different project types:
- [ ] Fresh empty project
- [ ] Existing TypeScript project
- [ ] Python project
- [ ] Monorepo structure
- [ ] Non-git directory

### 4.3 Cloud Integration (api.thehouseofdeals.com)

| Endpoint | Purpose | Status |
|----------|---------|--------|
| `/v1/health` | Basic health | Working |
| `/v1/health/detailed` | Redis check | Working (109ms) |
| `/v1/patterns` | Pattern storage | Pending test |
| `/v1/checkins` | Power mode | Pending test |

### 4.4 Power Mode Validation

```bash
# Test Power Mode initialization
/popkit:power init

# Verify connection
/popkit:power status
```

Test scenarios:
1. File-based fallback (no Redis)
2. Upstash Redis connection
3. Multi-agent coordination

---

## Part 5: Quality Gates

### 5.1 Pre-Release Checklist

**Code Quality:**
- [ ] No critical security vulnerabilities
- [ ] No hardcoded secrets
- [ ] All Python hooks have proper error handling
- [ ] TypeScript templates compile

**Documentation Quality:**
- [ ] README has working installation instructions
- [ ] All commands documented with examples
- [ ] Changelog is up to date
- [ ] Version numbers synchronized

**Testing Quality:**
- [ ] Hook tests passing
- [ ] At least one test per tier-1 skill
- [ ] Routing tests passing
- [ ] Fresh install test passing

**User Experience:**
- [ ] Commands use AskUserQuestion (not plain text prompts)
- [ ] Clear error messages
- [ ] Reasonable defaults
- [ ] Help text available

### 5.2 Known Issues Tracking

Create issue for each validation failure:
```
Title: [Validation] {category}: {specific issue}
Labels: bug, P1-high, phase:now
```

### 5.3 Release Blockers

**P0 (Must Fix):**
- Installation failure
- Core command crashes
- Security vulnerability
- Data loss potential

**P1 (Should Fix):**
- Documentation inaccuracy
- Minor UX issues
- Performance problems

**P2 (Nice to Fix):**
- Edge cases
- Polish items

---

## Part 6: Visual Assets (Issue #2)

### 6.1 Current Status

| Asset | Status | Location |
|-------|--------|----------|
| popkit-banner.png | Missing | assets/images/ |
| before-after.gif | Tape exists, GIF pending | assets/tapes/core-features/ |
| morning-routine.gif | Tape exists, GIF pending | assets/tapes/core-features/ |
| slash-command-discovery.gif | Tape exists, GIF pending | assets/tapes/core-features/ |

### 6.2 GIF Generation

VHS tapes are created but GIFs need generation:

```bash
# Requires VHS installed
# https://github.com/charmbracelet/vhs

cd packages/plugin/assets/tapes/core-features
vhs before-after/before-after.tape
vhs morning-routine/morning-routine.tape
vhs slash-command-discovery/slash-command-discovery.tape
```

### 6.3 README Badges

Already present in README:
- Version badge
- License badge
- Claude Code Plugin badge

---

## Part 7: Analytics & Observability

### 7.1 Local File Logging

Implement in hooks for session tracking:
```
~/.popkit/
├── sessions/
│   └── {date}-{id}.json
├── patterns/
│   └── learned-patterns.json
└── metrics/
    └── usage-stats.json
```

### 7.2 Cloud Analytics (Premium)

When API key is configured:
- Session duration
- Commands used
- Agent routing frequency
- Error rates

### 7.3 User Feedback Collection

`/popkit:bug report` flow:
1. Capture current state
2. Anonymize sensitive data
3. Submit to cloud (with consent)
4. Create GitHub issue if critical

---

## Part 8: Execution Plan

### Phase 1: Documentation Audit (1-2 days)

1. Run automated CLAUDE.md section validators
2. Verify all auto-generated sections
3. Test all code examples
4. Fix broken links

### Phase 2: Structure Validation (1 day)

1. Count validation for all categories
2. Version synchronization check
3. Missing file detection
4. Config.json validation

### Phase 3: Functional Testing (2-3 days)

1. Command testing matrix
2. Skill sampling
3. Agent routing tests
4. Hook protocol tests

### Phase 4: Integration Testing (1-2 days)

1. Fresh installation test
2. Multi-project compatibility
3. Cloud endpoint testing
4. Power Mode validation

### Phase 5: Polish & Release (1-2 days)

1. Generate visual assets
2. Update issue #2 checklist
3. Final version bump
4. Publish to public repo

---

## Appendix: Validation Commands

```bash
# Run all plugin tests
/popkit:plugin test

# Test specific category
/popkit:plugin test hooks
/popkit:plugin test routing
/popkit:plugin test skills

# Validate documentation
/popkit:assess docs

# Check routing
/popkit:debug routing --verbose

# Health check
/popkit:routine morning
```

---

## Next Steps

1. Create GitHub issue for validation epic
2. Break into actionable sub-issues
3. Assign to v1.0.0 milestone
4. Begin Phase 1: Documentation Audit
