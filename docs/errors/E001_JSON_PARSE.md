# E001_JSON_PARSE - JSON Parsing Error

**Category:** JSON/Input Parsing
**Severity:** Critical
**Status:** Blocking

## Description

This error occurs when PopKit hooks receive malformed JSON input that cannot be parsed. PopKit hooks use the JSON stdin/stdout protocol for communication, and invalid JSON syntax prevents proper parsing of the request, causing the hook to block execution.

This is a **critical** error because hooks cannot proceed without valid input, and it indicates a fundamental communication failure between Claude Code and the hook.

## Common Causes

1. **Trailing Commas** - JSON specification doesn't allow trailing commas in objects or arrays
2. **Unescaped Quotes** - Strings with unescaped quotes break parsing
3. **Single Quotes** - JSON requires double quotes for strings, not single quotes
4. **Comments** - JSON doesn't support comments (unlike JavaScript)
5. **Malformed Structure** - Missing brackets, braces, or incorrect nesting

## Examples

### Scenario 1: Trailing Comma

```json
{
  "tool_name": "Read",
  "args": {
    "path": "file.txt"
  },  ← Trailing comma
}
```

**Why it fails:** The JSON specification doesn't allow trailing commas after the last property in an object. This is a common mistake for developers coming from languages that allow trailing commas.

### Scenario 2: Unescaped Quotes

```json
{
  "message": "He said "hello" to me"
}
```

**Why it fails:** The inner quotes must be escaped as `\"` to be valid JSON. Without escaping, the parser thinks the string ends at the second quote.

### Scenario 3: Single Quotes

```json
{
  'tool_name': 'Read',
  'args': {'path': 'file.txt'}
}
```

**Why it fails:** JSON requires double quotes (`"`) for both keys and string values. Single quotes are not valid JSON syntax.

## Resolution Steps

1. **Validate JSON Syntax with jq**
   ```bash
   # Test your JSON with jq
   echo '{"tool":"Read"}' | jq '.'

   # If valid: formatted JSON output
   # If invalid: error message with line number
   ```
   jq is a command-line JSON processor that provides clear error messages for syntax issues.

2. **Use Online JSON Validator**
   - Visit [JSONLint](https://jsonlint.com)
   - Paste your JSON
   - Fix highlighted syntax errors
   - The validator will show exactly where the syntax error occurs

3. **Check Common JSON Mistakes**
   - Remove trailing commas after last array/object items
   - Use double quotes (`"`) not single quotes (`'`)
   - Escape special characters in strings: `\"`, `\\`, `\n`, `\t`
   - Remove any comments (use a separate documentation file)
   - Ensure all brackets `[]` and braces `{}` are properly matched

## Prevention

- **Use JSON-aware editors** - VS Code, Sublime Text, or other editors with JSON syntax highlighting catch errors immediately
- **Enable linters** - ESLint with JSON plugins or Prettier can catch JSON errors before execution
- **Test with jq** - Always validate JSON with `jq` before sending to hooks: `cat file.json | jq '.'`
- **Use JSON.stringify()** - When generating JSON programmatically, use language built-ins (e.g., `JSON.stringify()` in JavaScript, `json.dumps()` in Python) rather than string concatenation
- **Automated testing** - Include JSON validation in your test suite

## Related Errors

- [E002_INVALID_SCHEMA](E002_INVALID_SCHEMA.md) - Structure is valid JSON but doesn't match the expected schema
- [E701_INVALID_CONFIG](E701_INVALID_CONFIG.md) - Configuration file has JSON parsing issues

## References

- [JSON Specification](https://www.json.org) - Official JSON standard
- [PopKit Hook Protocol](../../CLAUDE.md#hook-standards) - How hooks use JSON for communication
- [jq Manual](https://stedolan.github.io/jq/manual/) - JSON command-line processor
- [Issue #104](https://github.com/jrc1883/popkit-claude/issues/104) - Error code system implementation

---

*This error code is part of PopKit's standardized error system (Issue #104). See [Error Codes Reference](README.md) for the complete list.*
