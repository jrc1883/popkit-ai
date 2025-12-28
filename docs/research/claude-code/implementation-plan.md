# Claude Code 2.0.71-74 Implementation Plan

**Created:** 2025-12-19
**Research:** See [claude-code-2.0.71-74-integration.md](./claude-code-2.0.71-74-integration.md)
**Target PR:** PopKit v1.0.0 - Claude Code 2.0.74 Integration
**Branch:** `claude/quad-code-research-w0flG`

---

## Executive Summary

This plan implements integration with Claude Code versions 2.0.71-74, focusing on:
1. **Critical:** Add tool restrictions to all 68 skills (security fix from v2.0.74)
2. **High Value:** LSP integration for smarter code intelligence
3. **High Value:** Custom session IDs for better project continuity
4. **Medium Value:** Enhanced `/context` visualization for skill budgets

**Timeline:** 3-4 days for Phase 0 (critical), 1-2 weeks for Phase 1 (high value)

---

## Current State Analysis

### ✅ What PopKit Already Has
1. **Native Async Support** - Already using Claude Code 2.0.64+ background agents
2. **Power Mode** - Multi-agent orchestration working
3. **68 Skills** - Comprehensive skill library
4. **30 Agents** - Tier 1, Tier 2, and Feature Workflow agents

### ❌ What's Missing (Opportunities)
1. **Tool Restrictions** - No skills currently use `<tool_restrictions>` (security gap)
2. **LSP Integration** - Not leveraging code intelligence
3. **Custom Session IDs** - Using basic named sessions
4. **Skill Budget Tracking** - No visibility into per-skill token usage

---

## Phase 0: Critical Security Fix (1-2 days)

**Goal:** Add tool restrictions to all skills before v2.0.74 enforcement

### Task 1: Categorize All 68 Skills by Risk Level

Create skill categorization document:

**Read-Only Skills (Should only read, not modify):**
- `pop-code-review` - Review only, no auto-fixes
- `pop-root-cause-tracing` - Debugging analysis
- `pop-verify-completion` - Validation only
- `pop-analyze-project` - Project analysis
- All `pop-assessment-*` skills (6 total)
- `pop-security-scan` - Security audit

**Write-Only Skills (Should only create specific files):**
- `pop-morning-generator` - Generate morning reports
- `pop-mcp-generator` - Generate MCP servers
- `pop-skill-generator` - Generate new skills
- All `pop-deploy-*` skills (deployment artifacts)

**Limited Bash Skills (Should restrict bash commands):**
- All deployment skills - No destructive commands
- `pop-cloudflare-*` - Only cloudflare CLI commands

**Full Access Skills (Need all tools):**
- `pop-executing-plans` - Implementation requires all tools
- `pop-brainstorming` - Design phase, research
- `pop-test-driven-development` - Writing tests and code
- `pop-finish-branch` - Git operations

### Task 2: Create Tool Restriction Templates

**File:** `packages/plugin/skills/_templates/tool-restrictions.md`

```markdown
<!-- READ-ONLY TEMPLATE -->
<tool_restrictions>
  <allowed>Read, Grep, Glob, WebSearch, WebFetch</allowed>
  <denied>Write, Edit, Bash, NotebookEdit</denied>
</tool_restrictions>

<!-- WRITE-ONLY TEMPLATE -->
<tool_restrictions>
  <allowed>Read, Grep, Glob, Write</allowed>
  <denied>Edit, Bash, NotebookEdit</denied>
</tool_restrictions>

<!-- LIMITED BASH TEMPLATE -->
<tool_restrictions>
  <allowed>Read, Grep, Glob, Write, Edit, Bash</allowed>
  <bash_restrictions>
    <allowed_commands>npm, git, docker, wrangler, gh</allowed_commands>
    <denied_patterns>rm -rf, sudo, chmod +x</denied_patterns>
  </bash_restrictions>
</tool_restrictions>

<!-- FULL ACCESS (No restrictions) -->
<!-- No <tool_restrictions> block needed -->
```

### Task 3: Add Restrictions to Top 20 High-Risk Skills

Priority order (highest risk first):

**Priority 1: Security-Critical (Day 1)**
1. `pop-assessment-security/SKILL.md` - READ-ONLY
2. `pop-security-scan/SKILL.md` - READ-ONLY
3. `pop-code-review/SKILL.md` - READ-ONLY
4. `pop-root-cause-tracing/SKILL.md` - READ-ONLY
5. `pop-verify-completion/SKILL.md` - READ-ONLY

**Priority 2: Analysis Skills (Day 1)**
6. `pop-analyze-project/SKILL.md` - READ-ONLY
7. `pop-assessment-architecture/SKILL.md` - READ-ONLY
8. `pop-assessment-documentation/SKILL.md` - READ-ONLY
9. `pop-assessment-performance/SKILL.md` - READ-ONLY
10. `pop-assessment-ux/SKILL.md` - READ-ONLY

**Priority 3: Generator Skills (Day 2)**
11. `pop-mcp-generator/SKILL.md` - WRITE-ONLY
12. `pop-skill-generator/SKILL.md` - WRITE-ONLY
13. `pop-morning-generator/SKILL.md` - WRITE-ONLY
14. `pop-auto-docs/SKILL.md` - WRITE-ONLY
15. `pop-doc-sync/SKILL.md` - LIMITED (docs only)

**Priority 4: Deployment Skills (Day 2)**
16. `pop-deploy-cloudflare-worker/SKILL.md` - LIMITED BASH
17. `pop-deploy-netlify/SKILL.md` - LIMITED BASH
18. `pop-deploy-vercel/SKILL.md` - LIMITED BASH
19. `pop-deploy-github-releases/SKILL.md` - LIMITED BASH
20. `pop-deploy-rollback/SKILL.md` - LIMITED BASH (extra careful!)

### Task 4: Test Tool Restrictions

**Test Script:** `packages/plugin/tests/test-tool-restrictions.py`

```python
"""
Test that tool restrictions are enforced correctly.
Requires Claude Code 2.0.74+
"""
import subprocess
import json

def test_read_only_skill():
    # pop-code-review should NOT be able to write files
    result = subprocess.run([
        "claude", "skill", "invoke", "pop-code-review",
        "--input", "review staged changes"
    ], capture_output=True)

    # Should succeed without Write tool access
    assert result.returncode == 0
    assert "Write tool denied" not in result.stderr

def test_write_only_skill():
    # pop-mcp-generator should NOT be able to run bash
    result = subprocess.run([
        "claude", "skill", "invoke", "pop-mcp-generator",
        "--input", "generate MCP for current project"
    ], capture_output=True)

    # Should fail if tries to use Bash
    # Success = properly restricted
    assert result.returncode == 0

# Run all tests
if __name__ == "__main__":
    test_read_only_skill()
    test_write_only_skill()
    print("✅ All tool restriction tests passed")
```

### Deliverable: PopKit v0.9.10

**Changes:**
- 20+ skills with tool restrictions
- Test suite for restriction enforcement
- Documentation in CHANGELOG.md

**Files Changed:**
- `packages/plugin/skills/*/SKILL.md` (20 files)
- `packages/plugin/tests/test-tool-restrictions.py` (new)
- `packages/plugin/skills/_templates/tool-restrictions.md` (new)
- `CHANGELOG.md` (document changes)
- `README.md` (mention security improvements)

---

## Phase 1: High-Value Integrations (1 week)

### 1.1: LSP Integration (2-3 days)

**Goal:** Enable LSP-powered code intelligence in skills

#### Step 1: Create LSP Client Utility

**File:** `packages/plugin/utils/lsp-client.ts`

```typescript
/**
 * LSP Client for PopKit skills
 * Requires Claude Code 2.0.74+
 */

export interface LSPDiagnostic {
  file: string;
  line: number;
  column: number;
  severity: 'error' | 'warning' | 'info';
  message: string;
  source: string;
}

export interface LSPSymbol {
  name: string;
  kind: string; // function, class, interface, etc.
  location: {
    file: string;
    range: { start: number; end: number; };
  };
}

export class LSPClient {
  /**
   * Get diagnostics for a file
   */
  async getDiagnostics(filePath: string): Promise<LSPDiagnostic[]> {
    // Use Claude Code's LSP integration
    // Implementation depends on Claude Code LSP API
    return [];
  }

  /**
   * Get symbol at position
   */
  async getSymbolAt(filePath: string, line: number, column: number): Promise<LSPSymbol | null> {
    // Get symbol info for function/class at position
    return null;
  }

  /**
   * Get function signature
   */
  async getFunctionSignature(filePath: string, functionName: string): Promise<string | null> {
    // Returns: "function authenticate(email: string, password: string): Promise<User>"
    return null;
  }

  /**
   * Find all references to symbol
   */
  async findReferences(filePath: string, symbolName: string): Promise<string[]> {
    // Returns list of file paths where symbol is used
    return [];
  }
}

export const lsp = new LSPClient();
```

#### Step 2: Enhance `pop-test-driven-development` with LSP

**File:** `packages/plugin/skills/pop-test-driven-development/SKILL.md`

Add LSP-enhanced workflow:

```markdown
---
name: test-driven-development
description: "LSP-enhanced test generation with type-safe scaffolds"
lsp_enabled: true
---

## LSP Integration (Claude Code 2.0.74+)

When available, this skill uses LSP to:
1. **Infer function signatures** - Generate tests with correct types
2. **Detect return types** - Mock return values accurately
3. **Find dependencies** - Import required modules automatically
4. **Validate tests** - Check for type errors before running

### Example Workflow

**Without LSP:**
```typescript
// Manual test generation (error-prone)
test('should authenticate user', () => {
  // Have to manually figure out function signature
  const result = authenticate(/* what params? */);
  // Have to manually figure out return type
  expect(result).toBe(/* what type? */);
});
```

**With LSP:**
```typescript
// LSP-enhanced test generation (type-safe)
// 1. LSP finds: function authenticate(email: string, password: string): Promise<User>
// 2. Generate test with correct signature:
test('should authenticate user', async () => {
  const result = await authenticate('test@example.com', 'password123');
  expect(result).toEqual(expect.objectContaining({
    id: expect.any(String),
    email: 'test@example.com',
  }));
});
```

## Tool Restrictions
<tool_restrictions>
  <allowed>Read, Grep, Glob, Write, Edit, Bash</allowed>
  <bash_restrictions>
    <allowed_commands>npm test, npm run test, jest, vitest, pytest</allowed_commands>
  </bash_restrictions>
</tool_restrictions>
```

#### Step 3: Add LSP Health Check to `/popkit:morning`

**File:** `packages/plugin/commands/routine.md`

Enhance morning routine:

```markdown
## LSP Health Check (Claude Code 2.0.74+)

```
Code Health (LSP-powered):
  ✅ No TypeScript errors (0)
  ⚠️  3 unused imports detected
  ✅ All tests passing
  ℹ️  2 deprecated APIs in use

  Run: npx tsc --noEmit  (to fix errors)
  Run: /popkit:code-cleanup  (to remove unused imports)
```
```

### 1.2: Custom Session IDs (2 days)

**Goal:** Programmatic session management with predictable IDs

#### Step 1: Update Session Capture Skill

**File:** `packages/plugin/skills/pop-session-capture/SKILL.md`

```markdown
## Custom Session IDs (Claude Code 2.0.73+)

PopKit now generates stable session IDs:

**Format:** `popkit-{context}-{timestamp}`

**Examples:**
- `popkit-issue-42-20251219-1530`
- `popkit-power-auth-feature-20251219-1600`
- `popkit-morning-routine-20251219-0900`

### Resume Session

```bash
# Latest session for issue #42
claude --resume popkit-issue-42-latest

# Specific timestamp
claude --resume popkit-issue-42-20251219-1530

# Fork for experiment
claude --fork popkit-issue-42-experiment-1
```

### Session ID in Captured State

```json
{
  "session_id": "popkit-issue-42-20251219-1530",
  "can_resume_with": [
    "popkit-issue-42-latest",
    "popkit-issue-42-20251219-1530"
  ],
  "issue": 42,
  "started": "2025-12-19T15:30:00Z",
  "phase": "implementation"
}
```
```

#### Step 2: Update Power Mode Session IDs

**File:** `packages/plugin/commands/power.md`

Add to the "start" subcommand:

```markdown
### Session ID Generation

Power Mode generates stable session IDs:

```bash
/popkit:power start "Build auth system"
# Creates session: popkit-power-auth-{hash8}-{timestamp}

# Example: popkit-power-auth-a3f9d2b1-20251219-1530
```

**Benefits:**
- Agents can reference session ID for coordination
- Easy to resume after interruption
- Predictable naming for automation

**Session State Includes:**
```json
{
  "session_id": "popkit-power-auth-a3f9d2b1-20251219-1530",
  "agents": [
    "code-explorer",
    "code-architect",
    "test-writer-fixer"
  ],
  "phase": "implementation",
  "insights_shared": 12
}
```
```

### 1.3: Enhanced `/context` Visualization (1 day)

**Goal:** Show per-skill token usage and optimization recommendations

#### Step 1: Add to Morning Routine

**File:** `packages/plugin/commands/routine.md`

```markdown
## Skill Optimization (Claude Code 2.0.74+)

```
PopKit Skills:
  Loaded: 12/68 skills (22.3K tokens)

  Development (4 skills, 8.2K tokens):
    • pop-brainstorming (2.1K)
    • pop-writing-plans (2.8K)
    • pop-executing-plans (1.9K)
    • pop-test-driven-development (1.4K)

  Quality (3 skills, 4.5K tokens):
    • pop-code-review (2.1K)
    • pop-verify-completion (1.2K)
    • pop-root-cause-tracing (1.2K)

  Power Mode (2 skills, 6.1K tokens):
    • pop-power-mode (4.8K)
    • pop-worktrees (1.3K)

  Session (3 skills, 3.8K tokens):
    • pop-session-capture (1.5K)
    • pop-session-resume (1.1K)
    • pop-context-restore (1.2K)

💡 Optimization Opportunities:
  - 5 unused skills in last 7 days (12K tokens)
    Recommend: /plugin disable pop-worktrees pop-finish-branch
  - 3 skills rarely used (loaded but <1 use/week)
```
```

#### Step 2: Add to Power Mode Status

**File:** `packages/plugin/commands/power.md`

Update the "status" subcommand output:

```markdown
### Output When Active (Enhanced)

```
[+] POWER MODE ACTIVE (Native Async)

Session: popkit-power-auth-a3f9d2b1-20251219-1530
Issue: #11 - Unified orchestration system
...

Agent Context Budgets:
  Agent 1 (code-architect): 42K/200K (21%)
    └─ Skills loaded: 5 (8.2K tokens)
  Agent 2 (test-writer-fixer): 31K/200K (15%)
    └─ Skills loaded: 3 (4.1K tokens)
  Agent 3 (code-reviewer): 18K/200K (9%)
    └─ Skills loaded: 2 (2.8K tokens)

  Total: 73K/200K (36%)
  Skill Overhead: 15.1K (7.5% of total)

💡 Tip: Agent 1 approaching 50% - consider /popkit:power compact
```
```

---

## Phase 2: Premium Features (1-2 weeks - Optional)

### 2.1: Claude in Chrome Integration (3-4 days)

**Goal:** Browser automation for web-based workflows

**Files to Create:**
1. `packages/plugin/skills/pop-browser-automation/SKILL.md`
2. `packages/plugin/commands/browser.md`

**Use Cases:**
- Deploy validation (visual testing)
- GitHub issue creation with rich formatting
- Documentation extraction with screenshots

**Gated:** Premium tier only (requires Chrome)

### 2.2: Advanced LSP Workflows (2 days)

**Goal:** Multi-agent LSP coordination

**Files to Create:**
1. `packages/cloud/src/powerMode/lspCoordinator.ts`
2. `packages/plugin/skills/lsp/pop-lsp-refactor.md`

**Use Cases:**
- Detect conflicting changes between agents
- Real-time conflict resolution
- LSP-powered refactoring with validation

**Gated:** Pro tier only (requires Upstash coordination)

---

## Testing Strategy

### Unit Tests
```bash
# Test tool restrictions
npm run test -- test-tool-restrictions.spec.ts

# Test LSP client
npm run test -- lsp-client.spec.ts

# Test session ID generation
npm run test -- session-id.spec.ts
```

### Integration Tests
```bash
# Test full workflow with LSP
/popkit:test-driven-development --test-mode

# Test Power Mode with custom session IDs
/popkit:power start "Test task" --test-mode

# Test skill restrictions enforcement
/popkit:code-review --test-mode
```

### Manual Testing Checklist
- [ ] Install Claude Code 2.0.74+
- [ ] Test 5 read-only skills (should not modify files)
- [ ] Test 3 write-only skills (should not run bash)
- [ ] Test LSP integration with TypeScript project
- [ ] Test custom session ID generation
- [ ] Test Power Mode session resumption
- [ ] Test `/context` visualization

---

## Documentation Updates

### Files to Update
1. `README.md` - Mention Claude Code 2.0.74 compatibility
2. `CHANGELOG.md` - Document all changes
3. `packages/plugin/docs/LSP_INTEGRATION.md` (new) - LSP guide
4. `packages/plugin/docs/TOOL_RESTRICTIONS.md` (new) - Security guide
5. `packages/plugin/docs/SESSION_MANAGEMENT.md` (new) - Session ID guide

---

## Rollout Plan

### Version Progression

**v0.9.10 (Phase 0 - Critical):**
- Tool restrictions for 20+ high-risk skills
- Test suite for enforcement
- Security documentation
- **Timeline:** 1-2 days
- **Breaking Changes:** None (additive only)

**v1.0.0 (Phase 1 - High Value):**
- LSP integration in 3 skills
- Custom session IDs
- Enhanced `/context` visualization
- Morning routine improvements
- **Timeline:** 1 week after v0.9.10
- **Breaking Changes:** None (all features opt-in)

**v1.1.0 (Phase 2 - Premium):**
- Browser automation (Premium)
- Advanced LSP workflows (Pro)
- Multi-agent LSP coordination (Pro)
- **Timeline:** 2 weeks after v1.0.0
- **Breaking Changes:** None (premium features only)

---

## Success Metrics

### Phase 0 (Critical)
- ✅ 100% of security-critical skills have tool restrictions
- ✅ 0 security vulnerabilities in skill execution
- ✅ All tests pass with Claude Code 2.0.74

### Phase 1 (High Value)
- ✅ LSP reduces test generation errors by 50%
- ✅ Custom session IDs used in 80%+ of Power Mode sessions
- ✅ Users report 30% faster context restoration

### Phase 2 (Premium)
- ✅ 20%+ of Premium users try browser automation
- ✅ Multi-agent LSP coordination prevents 5+ conflicts/session

---

## Risk Mitigation

### Risk 1: Tool Restrictions Too Strict
**Impact:** Skills fail unexpectedly
**Mitigation:**
- Test extensively before release
- Provide clear error messages
- Allow skill authors to override restrictions

### Risk 2: LSP Not Available
**Impact:** Features fail on older Claude Code versions
**Mitigation:**
- Feature detection: `if (lspAvailable) { ... } else { fallback }`
- Graceful degradation
- Clear version requirements in docs

### Risk 3: Session ID Collisions
**Impact:** Sessions overwrite each other
**Mitigation:**
- Include timestamp + hash in ID
- Validate uniqueness before creating
- Warn user if session already exists

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Create Phase 0 branch** from main
3. **Implement tool restrictions** for top 20 skills
4. **Test enforcement** with Claude Code 2.0.74
5. **Create PR** with comprehensive testing
6. **Merge Phase 0** → release v0.9.10
7. **Start Phase 1** implementation

---

## Questions for Discussion

1. **Tool restrictions approach:** Should we be conservative (restrict more) or permissive (restrict less)?
2. **LSP fallback:** What should happen when LSP is unavailable?
3. **Session ID format:** Is `popkit-{context}-{hash}-{timestamp}` the right format?
4. **Browser automation:** Should this be Premium or Pro tier?
5. **Testing requirements:** What's the minimum test coverage for Phase 0?

---

## Conclusion

This implementation plan provides a clear path to integrate Claude Code 2.0.71-74 features into PopKit. Phase 0 addresses critical security concerns, while Phase 1 unlocks significant value for users.

**Estimated Total Effort:**
- Phase 0: 1-2 days (critical)
- Phase 1: 1 week (high value)
- Phase 2: 1-2 weeks (optional premium)

**Expected Outcome:**
- More secure skills (tool restrictions)
- Smarter code generation (LSP)
- Better session management (custom IDs)
- Improved visibility (`/context` visualization)
