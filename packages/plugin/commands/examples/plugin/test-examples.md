# Plugin Test Examples

## Basic Usage

```bash
/popkit:plugin                        # Run all tests (default)
/popkit:plugin test                   # Same as above
/popkit:plugin test hooks             # Test hooks only
/popkit:plugin test agents            # Test agents only
/popkit:plugin test skills            # Test skills only
/popkit:plugin test routing           # Test agent routing
/popkit:plugin test structure         # Test file structure
/popkit:plugin test sandbox           # Run sandbox tests (P0 smoke)
/popkit:plugin test sandbox --full    # Full sandbox test suite (P0+P1)
/popkit:plugin test sandbox --skill X # Test specific skill in sandbox
```

## Test Categories

| Category | What It Tests |
|----------|---------------|
| `hooks` | JSON stdin/stdout, error handling, timeouts |
| `agents` | Definitions, tools, routing keywords |
| `skills` | SKILL.md format, descriptions, dependencies |
| `routing` | Agent selection based on prompts |
| `structure` | File existence, YAML validity, references |
| `sandbox` | Isolated execution tests with telemetry capture |

## Sample Output

```
Running plugin self-tests...

[Structure Tests]
[ok] agents/config.json valid
[ok] hooks/hooks.json valid
[ok] All 29 agents have definitions
[ok] All 22 skills have SKILL.md

[Hook Tests]
[ok] pre-tool-use: JSON protocol
[ok] post-tool-use: JSON protocol
[ok] session-start: JSON protocol
...

[Agent Tests]
[ok] bug-whisperer: definition valid
[ok] code-reviewer: routing keywords work
...

[Routing Tests]
[ok] "fix bug" -> bug-whisperer (0.8 confidence)
[ok] "review code" -> code-reviewer (0.9 confidence)
...

---
Results: 54 passed, 0 failed, 2 skipped
Time: 12.3s
---
```

## Test Files

Test definitions are stored in:
- `tests/hooks/` - Hook input/output tests
- `tests/agents/` - Agent definition tests
- `tests/skills/` - Skill structure tests
- `tests/routing/` - Agent routing tests
- `tests/sandbox/` - Sandbox test infrastructure and matrix
