# Wildcard Permission Design for PopKit Agents

**Created:** 2026-01-08
**Status:** Implementation
**Related Epic:** Phase 3 - Claude Code 2.1.0 Integration

---

## Overview

Claude Code 2.1.0 introduces wildcard tool permissions, enabling fine-grained Bash command control. This document defines the wildcard permission scheme for 15+ PopKit agents.

**Key Principle:** Be conservative. Explicitly list allowed patterns; everything else is blocked by omission.

---

## Wildcard Syntax

### Basic Syntax

```yaml
allowed-tools:
  - Bash(command subcommand)      # Exact match
  - Bash(command *)               # Command with any arguments
  - Bash(command subcommand*)     # Subcommand with any arguments
```

### Wildcard Behavior

- `*` matches any arguments after the specified command/subcommand
- Absence of a pattern means the command is **blocked**
- Wildcards apply to the full command string

---

## Security Model

### Security Principles

1. **Explicit Allow:** Only listed patterns are permitted
2. **Block by Omission:** Unlisted patterns are automatically blocked
3. **Conservative Wildcards:** Prefer specific patterns over broad ones
4. **Audit Trail:** Document WHY each pattern is allowed

### Examples

**GOOD (Specific, Safe):**
```yaml
allowed-tools:
  - Bash(npm run test:*)       # All test:* scripts, clear scope
  - Bash(git diff*)            # Git operation, safe with wildcards
  - Bash(pytest -v*)           # Testing command with verbosity args
  - Bash(eslint --fix*)        # Linting with fix and args
```

**BAD (Too Broad, Dangerous):**
```yaml
allowed-tools:
  - Bash(rm *)                 # Can delete anything!
  - Bash(*)                    # Allows everything, defeats purpose
  - Bash(sh*)                  # Matches sh, shutdown, shred
  - Bash(node *)               # Too broad, includes node -e 'malicious'
```

**BLOCKED (By Omission):**
```yaml
# These are implicitly blocked if not listed:
# - git push --force
# - rm -rf /
# - dd if=/dev/zero of=/dev/sda
# - chmod 777 /
# - sudo anything
```

---

## Agent Category Patterns

### Category 1: Test/Debug Agents

**Purpose:** Run tests, debug code, analyze failures

**Common Patterns:**
```yaml
allowed-tools:
  # Testing frameworks
  - Bash(npm test)
  - Bash(npm run test:*)
  - Bash(pytest *)
  - Bash(vitest *)
  - Bash(jest *)
  - Bash(mocha *)

  # Debugging tools
  - Bash(npm run debug*)
  - Bash(node --inspect*)
  - Bash(python -m pdb*)

  # Coverage/analysis
  - Bash(npm run coverage)
  - Bash(pytest --cov*)
```

**Why These Patterns:**
- Testing commands are generally safe (read-only or write to test DBs)
- Debug flags (`--inspect`) don't modify code
- Coverage tools analyze without changing files

**Agents:**
1. test-writer-fixer
2. systematic-debugger
3. root-cause-analyzer

---

### Category 2: Git Operations Agents

**Purpose:** Manage version control, branches, commits

**Common Patterns:**
```yaml
allowed-tools:
  # Status/inspection (safe, read-only)
  - Bash(git status)
  - Bash(git diff*)
  - Bash(git log*)
  - Bash(git show*)

  # Local operations (safe, reversible)
  - Bash(git add*)
  - Bash(git commit*)
  - Bash(git branch*)
  - Bash(git checkout*)
  - Bash(git switch*)

  # Worktree management
  - Bash(git worktree*)

  # Merge operations (user-supervised)
  - Bash(git merge*)
  - Bash(git rebase*)
  - Bash(git cherry-pick*)

  # EXPLICITLY BLOCKED (by omission):
  # - git push --force (dangerous)
  # - git reset --hard HEAD~100 (data loss)
  # - git filter-branch (repo rewrite)
```

**Why These Patterns:**
- Read operations (`status`, `diff`, `log`) are always safe
- Local operations (`add`, `commit`, `branch`) are reversible
- Remote operations (`push --force`) are BLOCKED by omission

**Security Note:** Force push must be done manually by user, not by agent.

**Agents:**
1. git-operations-specialist
2. branch-manager
3. worktree-coordinator
4. merge-specialist

---

### Category 3: Deployment/CI Agents

**Purpose:** Build, deploy, orchestrate CI/CD

**Common Patterns:**
```yaml
allowed-tools:
  # Build commands
  - Bash(npm run build*)
  - Bash(npm run deploy*)
  - Bash(pnpm build*)
  - Bash(yarn build*)

  # Docker (read-only inspection)
  - Bash(docker ps*)
  - Bash(docker images*)
  - Bash(docker inspect*)
  - Bash(docker logs*)

  # Kubernetes (read-only)
  - Bash(kubectl get*)
  - Bash(kubectl describe*)
  - Bash(kubectl logs*)

  # CI/CD tools
  - Bash(gh workflow*)
  - Bash(gh run*)
  - Bash(circleci*)

  # BLOCKED (by omission):
  # - docker rm -f (destructive)
  # - kubectl delete (destructive)
  # - npm publish (requires manual approval)
```

**Why These Patterns:**
- Build commands are project-specific, safe in context
- Inspection commands (`ps`, `get`, `describe`) are read-only
- Destructive operations (delete, rm) are blocked

**Agents:**
1. deployment-validator
2. ci-cd-coordinator
3. performance-optimizer

---

### Category 4: Security/Quality Agents

**Purpose:** Audit dependencies, check code quality, scan vulnerabilities

**Common Patterns:**
```yaml
allowed-tools:
  # Security scanning
  - Bash(npm audit*)
  - Bash(snyk test*)
  - Bash(safety check*)
  - Bash(trivy scan*)

  # Dependency management (read-only checks)
  - Bash(npm outdated*)
  - Bash(pip list --outdated*)
  - Bash(poetry show --outdated*)

  # Code quality (linting, formatting)
  - Bash(eslint*)
  - Bash(pylint*)
  - Bash(ruff check*)
  - Bash(black --check*)

  # BLOCKED (by omission):
  # - npm install (modifies package.json/lock)
  # - pip install (modifies environment)
  # - eslint --fix (auto-fixes code)
```

**Why These Patterns:**
- Audit/scan commands are read-only
- Linters in check mode don't modify code
- Installation commands blocked to prevent dependency injection

**Note:** Auto-fix commands require explicit user approval.

**Agents:**
1. security-auditor
2. dependency-manager
3. code-quality-auditor

---

### Category 5: Database/API Agents

**Purpose:** Query databases, test APIs, inspect services

**Common Patterns:**
```yaml
allowed-tools:
  # Database clients (read-only queries)
  - Bash(psql -c "SELECT*")
  - Bash(mysql -e "SELECT*")
  - Bash(mongosh --eval "db.*.find*")
  - Bash(redis-cli GET*)

  # API testing
  - Bash(curl*)
  - Bash(http GET*)
  - Bash(httpie*)

  # BLOCKED (by omission):
  # - psql -c "DROP DATABASE" (destructive)
  # - mysql -e "DELETE FROM" (destructive)
  # - curl -X DELETE (destructive)
```

**Why These Patterns:**
- Read-only queries (SELECT, GET, find) are safe
- Destructive operations (DROP, DELETE, POST/PUT/DELETE) blocked

**Security Note:** Write operations must be manually approved by user.

**Agents:**
1. database-specialist
2. api-design-specialist

---

## Implementation Strategy

### Step 1: Audit Current Permissions

For each agent:
1. Read current `allowed-tools` (likely broad `Bash`)
2. Identify actual Bash commands the agent needs
3. Map to wildcard patterns
4. Document WHY each pattern is allowed

### Step 2: Apply Conservative Patterns

**Template:**
```yaml
---
name: agent-name
allowed-tools:
  # Category: Description
  - Bash(specific-command)           # Why: justification
  - Bash(specific-command arg*)      # Why: justification

  # Non-Bash tools (no change)
  - Read
  - Write
  - Grep
---
```

### Step 3: Test Validation

Create test scenarios:
```yaml
# test-writer-fixer agent
✅ ALLOWED:
  - Bash(npm test)              → Exact match
  - Bash(npm run test:unit)     → Matches Bash(npm run test:*)
  - Bash(pytest -v --tb=short)  → Matches Bash(pytest *)

❌ BLOCKED:
  - Bash(npm run build)         → Not listed
  - Bash(rm test/*.js)          → Not listed
  - Bash(git push)              → Not listed
```

---

## Migration Checklist

### Pre-Migration
- [ ] Read all agent files to understand current permissions
- [ ] Document intended Bash commands per agent
- [ ] Design wildcard patterns per category

### During Migration
- [ ] Update agent frontmatter with wildcard patterns
- [ ] Add inline comments explaining each pattern
- [ ] Ensure consistency across similar agents

### Post-Migration
- [ ] Test allowed commands execute successfully
- [ ] Test blocked commands fail appropriately
- [ ] Document findings in completion summary

---

## Pattern Reference

### Quick Reference Table

| Command Type | Pattern | Example | Safe? |
|--------------|---------|---------|-------|
| Exact match | `Bash(command)` | `Bash(git status)` | ✅ |
| With args | `Bash(command *)` | `Bash(pytest *)` | ⚠️ Check args |
| Subcommand | `Bash(cmd sub*)` | `Bash(npm run test:*)` | ✅ Usually safe |
| Wildcard start | `Bash(*)` | `Bash(*)` | ❌ Too broad |
| Glob chars | `Bash(rm *.txt)` | - | ❌ Dangerous |

### Common Safe Patterns

```yaml
# Read-only inspection
- Bash(git status)
- Bash(git diff*)
- Bash(docker ps*)
- Bash(kubectl get*)

# Testing (safe in test env)
- Bash(npm test)
- Bash(pytest *)
- Bash(vitest *)

# Build (project-specific)
- Bash(npm run build*)
- Bash(pnpm build*)

# Linting (check mode)
- Bash(eslint*)
- Bash(pylint*)
```

### Common Blocked Patterns

```yaml
# BLOCKED by omission (never list these):
# - Bash(rm -rf*)           # File deletion
# - Bash(git push --force*) # Force push
# - Bash(dd*)               # Disk operations
# - Bash(chmod 777*)        # Permission changes
# - Bash(sudo*)             # Privilege escalation
# - Bash(npm publish*)      # Publishing (manual only)
```

---

## Testing & Validation

### Test Scenarios

#### Scenario 1: Test Writer Agent
```yaml
Agent: test-writer-fixer
Patterns:
  - Bash(npm test)
  - Bash(npm run test:*)
  - Bash(pytest *)

Tests:
  ✅ PASS: Bash(npm test)
  ✅ PASS: Bash(npm run test:unit)
  ✅ PASS: Bash(npm run test:integration)
  ✅ PASS: Bash(pytest tests/)
  ❌ FAIL: Bash(npm run build)  # Not listed
  ❌ FAIL: Bash(rm tests/*.js)  # Not listed
```

#### Scenario 2: Git Operations Agent
```yaml
Agent: git-operations-specialist
Patterns:
  - Bash(git status)
  - Bash(git diff*)
  - Bash(git add*)
  - Bash(git commit*)

Tests:
  ✅ PASS: Bash(git status)
  ✅ PASS: Bash(git diff --staged)
  ✅ PASS: Bash(git add .)
  ✅ PASS: Bash(git commit -m "test")
  ❌ FAIL: Bash(git push)           # Not listed
  ❌ FAIL: Bash(git push --force)   # Not listed
  ❌ FAIL: Bash(git reset --hard)   # Not listed
```

#### Scenario 3: Security Auditor Agent
```yaml
Agent: security-auditor
Patterns:
  - Bash(npm audit*)
  - Bash(snyk test*)
  - Bash(safety check*)

Tests:
  ✅ PASS: Bash(npm audit)
  ✅ PASS: Bash(npm audit --json)
  ✅ PASS: Bash(snyk test --severity-threshold=high)
  ❌ FAIL: Bash(npm install)    # Not listed
  ❌ FAIL: Bash(npm audit fix)  # Not listed (requires approval)
```

---

## Edge Cases & Considerations

### Edge Case 1: Multi-word Commands
```yaml
# Problem: How to match "npm run" vs "npm"?
# Solution: Use full subcommand in pattern

❌ BAD:
  - Bash(npm *)  # Too broad, matches npm install, npm publish

✅ GOOD:
  - Bash(npm test)
  - Bash(npm run test:*)
  - Bash(npm run build*)
```

### Edge Case 2: Chained Commands
```yaml
# Problem: What about command chaining (&&, ||, ;)?
# Solution: Block by omission. Agents should use sequential tool calls.

❌ BLOCKED:
  - Bash(npm test && npm run build)  # Not listed, blocked

✅ ALLOWED (sequential tool calls):
  1. Bash(npm test)
  2. Bash(npm run build)  # If build pattern allowed
```

### Edge Case 3: Shell Redirection
```yaml
# Problem: What about output redirection (>, >>)?
# Solution: Block by default unless explicitly needed.

❌ BLOCKED:
  - Bash(npm test > output.txt)  # Redirection not in pattern

✅ IF NEEDED:
  - Bash(npm test >*)  # Explicit redirection allowed
```

---

## Rollout Plan

### Phase 1: Category 1 (Test/Debug) - 3 agents
- test-writer-fixer
- systematic-debugger
- root-cause-analyzer

**Validation:** Run test commands, verify blocking works

### Phase 2: Category 2 (Git Ops) - 4 agents
- git-operations-specialist
- branch-manager
- worktree-coordinator
- merge-specialist

**Validation:** Test git operations, verify force push blocked

### Phase 3: Category 3 (Deploy/CI) - 3 agents
- deployment-validator
- ci-cd-coordinator
- performance-optimizer

**Validation:** Test build/deploy commands, verify destructive ops blocked

### Phase 4: Category 4 (Security/Quality) - 3 agents
- security-auditor
- dependency-manager
- code-quality-auditor

**Validation:** Test audit commands, verify install/fix blocked

### Phase 5: Category 5 (Database/API) - 2 agents
- database-specialist
- api-design-specialist

**Validation:** Test read queries, verify destructive queries blocked

---

## Success Criteria

- [ ] 15+ agents updated with wildcard permissions
- [ ] All patterns documented with justification
- [ ] Test scenarios validate allow/block behavior
- [ ] No overly broad patterns (`Bash(*)`)
- [ ] Destructive operations blocked by omission
- [ ] Documentation complete (CLAUDE.md, this doc)

---

## References

- [Epic: Claude Code 2.1.0 Integration](../plans/2026-01-07-claude-code-2.1.0-integration-epic.md)
- [PopKit Agent Architecture](../AGENT_ROUTING_GUIDE.md)
- [Hook Portability Audit](../HOOK_PORTABILITY_AUDIT.md)

---

**Author:** Joseph Cannon
**Implementation Date:** 2026-01-08
