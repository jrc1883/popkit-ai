# Epic: Claude Code 2.1.0 Feature Integration

**Created:** 2026-01-07
**Status:** Planned
**Priority:** High
**Target Version:** PopKit 1.0.0-beta.4

## Executive Summary

Claude Code 2.1.0 introduces 10+ powerful features that significantly enhance PopKit's capabilities. This epic outlines a phased implementation plan to integrate these features, improving developer experience, reducing token overhead, and expanding functionality.

**Key Benefits:**
- Reduced token usage through forked skill contexts
- Enhanced security with granular tool permissions
- Improved developer workflow with skill hot-reload
- More powerful hook system with agent/skill scoping
- Foundation for dynamic tool loading (MCP list_changed)

---

## Feature Analysis & Implementation Plan

### Phase 1: Foundation & Quick Wins (Week 1)

#### 1.1 Skill Hot-Reload Documentation ✅ DONE
**Feature:** Skills now hot-reload without session restart

**Tasks:**
- [x] Update CLAUDE.md with hot-reload documentation
- [ ] Update `/popkit:skill-generator` to mention instant availability
- [ ] Add hot-reload indicator to Power Mode statusline

**Files to Modify:**
- `CLAUDE.md` (line 99-120)
- `packages/popkit-core/skills/pop-skill-generator/SKILL.md`
- `packages/popkit-core/power-mode/statusline.py`

**Priority:** P2 | **Effort:** 2 hours

---

#### 1.2 Forked Skill Contexts
**Feature:** `context: fork` frontmatter field for isolated execution

**Why This Matters:**
- Reduces token overhead for one-time operations
- Isolates expensive operations (embeddings, web research)
- Enables true parallel execution

**Target Skills (5 skills):**

| Skill | Current Context | Benefit |
|-------|----------------|---------|
| `pop-research-capture` | Shared | Isolate web research, reduce bloat |
| `pop-embed-content` | Shared | Expensive embedding gen in isolation |
| `pop-systematic-debugging` | Shared | Clean debugging environment |
| `pop-assessment-security` | Shared | One-time security scans |
| `pop-assessment-performance` | Shared | One-time performance analysis |

**Implementation:**
```yaml
# packages/popkit-research/skills/pop-research-capture/SKILL.md
---
description: Capture web research findings
context: fork  # ← Add this line
---
```

**Priority:** P0 | **Effort:** 1 hour

---

#### 1.3 YAML List Migration
**Feature:** Cleaner YAML list syntax for `allowed-tools`

**Before:**
```yaml
allowed-tools: ["Bash", "Read", "Write"]
```

**After:**
```yaml
allowed-tools:
  - Bash
  - Read
  - Write
```

**Scope:** Update all 22 agents across 4 plugins

**Priority:** P2 | **Effort:** 2 hours

---

### Phase 2: Hook Modernization (Week 2)

#### 2.1 Agent-Scoped Hooks
**Feature:** Hooks in agent frontmatter (PreToolUse, PostToolUse, Stop)

**Target Agents:**

**A. Security Auditor** (`packages/popkit-ops/agents/tier-1-always-active/security-auditor/AGENT.md`)
```yaml
---
name: security-auditor
hooks:
  PreToolUse:
    - script: "${CLAUDE_PLUGIN_ROOT}/../../shared-py/hooks/validate-security-tool.py"
      once: false
---
```

**Purpose:** Block dangerous commands before execution

**B. Test Writer/Fixer** (`packages/popkit-ops/agents/tier-1-always-active/test-writer-fixer/AGENT.md`)
```yaml
---
name: test-writer-fixer
hooks:
  PostToolUse:
    - script: "${CLAUDE_PLUGIN_ROOT}/../../shared-py/hooks/auto-run-tests.py"
      once: false
---
```

**Purpose:** Auto-run tests after code changes

**Priority:** P0 | **Effort:** 4 hours

---

#### 2.2 Skill-Scoped Hooks with `once: true`
**Feature:** Cleanup operations that run once at skill completion

**Target Skills:**

**A. Session Capture** (`packages/popkit-dev/skills/pop-session-capture/SKILL.md`)
```yaml
---
hooks:
  Stop:
    - script: "${CLAUDE_PLUGIN_ROOT}/../../shared-py/hooks/auto-save-state.py"
      once: true  # ← Run only at end
---
```

**B. Power Mode** (`packages/popkit-core/skills/pop-power-mode/SKILL.md`)
```yaml
---
hooks:
  Stop:
    - script: "${CLAUDE_PLUGIN_ROOT}/../../shared-py/hooks/save-power-mode-report.py"
      once: true
---
```

**Priority:** P1 | **Effort:** 3 hours

---

#### 2.3 PreToolUse Middleware with `updatedInput`
**Feature:** Hooks can modify tool inputs while still requesting consent

**Use Case:** Smart Bash safety middleware

**Create:** `packages/shared-py/hooks/smart-bash-middleware.py`

```python
#!/usr/bin/env python3
import json
import sys

DANGEROUS_COMMANDS = ["rm -rf", "git push --force", "dd if="]

def handle_pre_tool_use(data):
    if data["tool"] == "Bash":
        command = data["input"]["command"]

        # Detect dangerous commands
        for dangerous in DANGEROUS_COMMANDS:
            if dangerous in command:
                # Add --dry-run flag automatically
                return {
                    "decision": "ask",
                    "message": f"Dangerous command '{dangerous}' detected. Auto-added --dry-run.",
                    "updatedInput": {
                        "command": command + " --dry-run",
                        "description": "[PROTECTED] " + data["input"].get("description", "")
                    }
                }

    return {"decision": "allow"}

if __name__ == "__main__":
    data = json.loads(sys.stdin.read())
    result = handle_pre_tool_use(data)
    print(json.dumps(result))
```

**Register in:** `packages/popkit-core/hooks/hooks.json`

**Priority:** P1 | **Effort:** 3 hours

---

### Phase 3: Advanced Permissions (Week 3)

#### 3.1 Wildcard Tool Permissions
**Feature:** Fine-grained Bash command control with `*` wildcards

**Examples:**

**Test Writer Agent:**
```yaml
# packages/popkit-ops/agents/tier-1-always-active/test-writer-fixer/AGENT.md
---
allowed-tools:
  - Bash(npm test)
  - Bash(npm run test:*)  # ← All test:* scripts
  - Bash(pytest *)        # ← pytest with any args
  - Bash(vitest *)
  - Read
  - Write
---
```

**Git Operations Agent:**
```yaml
# packages/popkit-dev/commands/git.md (agent frontmatter)
---
allowed-tools:
  - Bash(git status)
  - Bash(git diff*)      # ← git diff with any args
  - Bash(git log*)
  - Bash(git add*)
  - Bash(git commit*)
  # Explicitly block force push
  # (absence means blocked)
---
```

**Scope:** Update 15+ agents with granular permissions

**Priority:** P1 | **Effort:** 6 hours

---

### Phase 4: Advanced Features (Week 4)

#### 4.1 Agent Field in Skills
**Feature:** Specify execution agent type in skill frontmatter

**Use Cases:**

**Expensive Operations → General Purpose Agent:**
```yaml
# packages/popkit-dev/skills/pop-brainstorming/SKILL.md
---
agent: general-purpose
context: fork
---
```

**Quick Utilities → Haiku Agent:**
```yaml
# packages/popkit-core/skills/pop-plugin-test/SKILL.md
---
agent: bash  # Fast, cheap execution
---
```

**Scope:** 10 skills updated

**Priority:** P2 | **Effort:** 2 hours

---

#### 4.2 MCP list_changed Research
**Feature:** Dynamic tool/resource updates without reconnection

**Vision:**
- Dynamic agent loading based on project detection
- Skill marketplace integration
- Context-aware tool provisioning

**Tasks:**
- [ ] Research MCP list_changed protocol
- [ ] Design PopKit dynamic loading architecture
- [ ] Create PoC for universal-mcp package
- [ ] Document integration path

**Priority:** P3 (Future Milestone) | **Effort:** 16+ hours

---

## Detailed Implementation Checklist

### Week 1: Foundation (8 hours)
- [x] Add `.workspace/` to .gitignore
- [ ] Document skill hot-reload in CLAUDE.md
- [ ] Add `context: fork` to 5 target skills
- [ ] Update Power Mode statusline with hot-reload indicator
- [ ] Migrate 22 agents to YAML list format

### Week 2: Hooks (10 hours)
- [ ] Create `smart-bash-middleware.py` hook
- [ ] Add agent-scoped hooks to security-auditor
- [ ] Add agent-scoped hooks to test-writer-fixer
- [ ] Add skill-scoped hooks to session-capture (Stop/once)
- [ ] Add skill-scoped hooks to power-mode (Stop/once)
- [ ] Test hook execution and verify middleware behavior

### Week 3: Permissions (8 hours)
- [ ] Design wildcard permission scheme
- [ ] Update test-writer-fixer with npm/pytest wildcards
- [ ] Update git command agents with git operation wildcards
- [ ] Update deployment-validator with CI/CD wildcards
- [ ] Document wildcard patterns in CLAUDE.md
- [ ] Test permission enforcement

### Week 4: Advanced (10 hours)
- [ ] Add `agent` field to 10 target skills
- [ ] Research MCP list_changed specification
- [ ] Design dynamic loading architecture
- [ ] Create PoC implementation
- [ ] Document findings and integration path

---

## Testing & Validation

### Test Matrix

| Feature | Test Case | Success Criteria |
|---------|-----------|------------------|
| Forked Context | Run `pop-research-capture` | Isolated execution, no context bloat |
| Agent Hooks | Trigger security-auditor PreToolUse | Hook blocks dangerous command |
| Skill Hooks | Complete session-capture | State auto-saved on Stop |
| Wildcard Perms | Run `npm test:unit` | Allowed via `Bash(npm run test:*)` |
| PreToolUse Middleware | Run `rm -rf /tmp` | Auto-adds `--dry-run`, asks permission |

### Validation Steps
1. **Token Measurement:** Measure context before/after fork implementation
2. **Hook Execution:** Verify hooks fire at correct lifecycle events
3. **Permission Enforcement:** Confirm wildcards allow/block correctly
4. **Hot-Reload:** Test skill modification → immediate availability

---

## Rollout Strategy

### Beta Testing (v1.0.0-beta.4)
- Deploy Phase 1 & 2 to beta users
- Gather feedback on hook behavior
- Measure token reduction from forked contexts

### Stable Release (v1.0.0)
- Include all Phase 1-3 features
- Document all new capabilities
- Provide migration guide for existing plugins

### Future (v1.1.0)
- Phase 4: MCP list_changed integration
- Dynamic agent loading
- Skill marketplace

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Forked context breaks agent coordination | High | Test carefully, document when NOT to use fork |
| Wildcard permissions too permissive | Medium | Conservative patterns, explicit blocking |
| Hook performance overhead | Low | Profile hook execution, use `once: true` |
| MCP list_changed complexity | Medium | Phase 4 as separate milestone, PoC first |

---

## Success Metrics

**Token Reduction:**
- Target: 15-20% reduction in average session token usage
- Measure: Before/after fork context implementation

**Developer Experience:**
- Hot-reload reduces iteration time (no restart needed)
- Granular permissions improve security posture
- Hooks automate tedious tasks

**Code Quality:**
- Hook-driven test execution increases coverage
- Security hooks prevent dangerous operations
- Middleware reduces user errors

---

## Related Issues

- #22 - Dependabot vulnerability alerts (security hooks help)
- #21 - Context bloat from oversized skills (forked context fixes)
- #20 - Command injection vulnerabilities (middleware protection)

---

## References

- [Claude Code 2.1.0 Changelog](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md#210)
- [PopKit Hook Standards](../HOOK_PORTABILITY_AUDIT.md)
- [Agent Architecture Guide](../AGENT_ROUTING_GUIDE.md)

---

## Approval & Sign-off

**Epic Owner:** Joseph Cannon
**Reviewers:** TBD
**Estimated Effort:** 36 hours
**Target Completion:** 2026-02-07

**Status:** ⏸️ Awaiting approval to proceed
