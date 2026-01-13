# MCP Generator Examples

Detailed code samples and implementation patterns extracted from the main SKILL.md for reference.

## Contents

| File                       | Purpose                                                      |
| -------------------------- | ------------------------------------------------------------ |
| `tool-implementation.ts`   | Example tool implementations (health check, semantic search) |
| `server-index.ts`          | Complete MCP server entry point                              |
| `package-json.json`        | Generated package.json template                              |
| `basic-analysis-output.md` | Example basic mode output (no API key)                       |
| `cloud-api-integration.py` | Enhanced mode cloud API integration                          |
| `auto-embedding.py`        | Tool embedding export and registration                       |

## Usage

These examples are referenced from the main SKILL.md using progressive disclosure markers:

```markdown
<details>
<summary>📄 See detailed workflow steps (optional)</summary>
...content...
</details>
```

This approach:

- Reduces main SKILL.md token count by 53.8% (3,435 → 1,588 tokens)
- Preserves all implementation details for reference
- Improves readability with focused main documentation
- Enables deep-dive when needed

## Integration

The skill references these examples in context:

- Tool implementation patterns → `tool-implementation.ts`
- Server setup → `server-index.ts`
- Basic vs Enhanced modes → `basic-analysis-output.md`, `cloud-api-integration.py`
- Semantic search → `auto-embedding.py`
