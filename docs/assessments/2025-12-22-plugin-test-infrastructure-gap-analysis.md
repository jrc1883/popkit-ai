# Plugin Test Infrastructure - Gap Analysis

**Date**: 2025-12-22
**Context**: Foundation architecture complete, testing infrastructure needed
**Epic**: #580 Phase 6 - Documentation & Release

## Current State

### ✅ What Exists

1. **Command Definition**
   - `packages/popkit-core/commands/plugin.md` - Full specification

2. **Shared Utilities** (in `packages/shared-py/popkit_shared/utils/`)
   - `doc_sync.py` - Documentation synchronization
   - `plugin_detector.py` - Plugin conflict detection
   - 68 other utility modules

3. **Hooks** (in `packages/popkit-core/hooks/`)
   - 25 hook files including:
     - `doc-sync.py` (hook that uses doc_sync utility)
     - `pre-tool-use.py`, `post-tool-use.py` (orchestration)
     - `quality-gate.py`, `session-start.py`, etc.

4. **Existing Skills** (in `packages/popkit-core/skills/`)
   - `pop-skill-generator` - Can generate new skills
   - `pop-mcp-generator` - MCP server generation
   - `pop-project-init`, `pop-analyze-project`, etc.

### ❌ What's Missing

1. **Test Skills** (None exist)
   - `pop-plugin-test/` - Main test runner skill
   - `pop-sandbox-test/` - Sandbox testing skill
   - `pop-auto-docs/` - Documentation generation skill
   - `pop-doc-sync/` - Documentation sync skill (wrapper around hook)
   - `pop-validation-engine/` - Validation skill

2. **Test Definitions** (No tests/ directory anywhere)
   - `tests/hooks/` - Hook protocol tests
   - `tests/agents/` - Agent routing tests
   - `tests/skills/` - Skill format tests
   - `tests/routing/` - Routing logic tests
   - `tests/structure/` - Plugin structure tests
   - `tests/sandbox/` - Sandbox analytics tests
   - `tests/sandbox/analytics.py` - Sandbox analytics script

3. **Test Examples** (No examples/ directory)
   - `examples/plugin/test-examples.md`
   - `examples/plugin/sync-detect-version.md`

## Implementation Strategy

### Phase 1: Core Testing Infrastructure ⭐ START HERE

1. **Create test definitions directory structure**
   ```
   packages/popkit-core/tests/
   ├── hooks/
   │   ├── test_pre_tool_use.json
   │   ├── test_post_tool_use.json
   │   └── test_session_start.json
   ├── agents/
   │   ├── test_routing.json
   │   └── test_keywords.json
   ├── skills/
   │   ├── test_format.json
   │   └── test_execution.json
   ├── routing/
   │   └── test_confidence.json
   └── structure/
       └── test_plugin_integrity.json
   ```

2. **Create pop-plugin-test skill**
   - Test runner that executes test definitions
   - Supports categories: hooks, agents, skills, routing, structure
   - Options: --verbose, --fail-fast, --json
   - Reports results in structured format

3. **Create pop-validation-engine skill**
   - Validates plugin integrity
   - Checks: YAML syntax, field presence, reference validity
   - Safe auto-fixes: frontmatter, orphaned agents, missing schemas

### Phase 2: Documentation Skills

4. **Create pop-doc-sync skill**
   - Wrapper around `doc_sync.py` utility
   - Generates AUTO-GEN sections in CLAUDE.md
   - Options: --check, --sync, --json

5. **Create pop-auto-docs skill**
   - Analyzes codebase and generates documentation
   - Updates README, CHANGELOG, API docs

### Phase 3: Advanced Testing (Future)

6. **Create sandbox testing infrastructure**
   - `tests/sandbox/analytics.py`
   - `pop-sandbox-test` skill
   - E2B integration for isolated testing
   - Options: --mode local|e2b

7. **Create example documentation**
   - `examples/plugin/test-examples.md`
   - `examples/plugin/sync-detect-version.md`

## Test Definition Format

Test definitions should be JSON files with this structure:

```json
{
  "test_name": "Pre-Tool-Use Hook Protocol",
  "category": "hooks",
  "description": "Verify pre-tool-use.py follows JSON stdin/stdout protocol",
  "test_cases": [
    {
      "name": "Valid input produces valid output",
      "input": {
        "tool": "Bash",
        "args": {"command": "echo test"}
      },
      "expected": {
        "status": "success",
        "has_stdout": true,
        "json_valid": true
      }
    }
  ]
}
```

## Priority Ranking

| Priority | Component | Why |
|----------|-----------|-----|
| **P0** | `pop-plugin-test` skill | Enables all other testing |
| **P0** | Basic test definitions | Validates current architecture |
| **P1** | `pop-validation-engine` | Ensures plugin integrity |
| **P1** | `pop-doc-sync` | Keeps docs up to date |
| **P2** | `pop-auto-docs` | Improves documentation quality |
| **P3** | Sandbox testing | Advanced isolated testing |

## Dependencies

- ✅ `popkit_shared.utils.doc_sync` - Available
- ✅ `popkit_shared.utils.plugin_detector` - Available
- ✅ Hook infrastructure - Working programmatically
- ❌ Test definitions - Need to create
- ❌ Test runner skill - Need to create

## Success Criteria

After implementation, `/popkit:plugin test` should:

1. Execute all test definitions
2. Validate hook JSON protocol
3. Verify agent routing logic
4. Check skill format compliance
5. Confirm plugin structure integrity
6. Report results in structured format (text or JSON)

## Next Steps

1. ✅ Confirm hooks are firing (DONE - verified in this session)
2. ⏭️ Create `pop-plugin-test` skill (START HERE)
3. ⏭️ Create initial test definitions
4. ⏭️ Test the test infrastructure 🎯
5. ⏭️ Create remaining skills (validation, doc-sync, auto-docs)
6. ⏭️ Add sandbox testing (future)

## Notes

- Test infrastructure should live in `popkit-core` (foundation plugin)
- All plugins can use `/popkit:plugin test` to validate themselves
- Sandbox testing (E2B) is optional and can be added later
- Focus on programmatic validation first, manual testing second
