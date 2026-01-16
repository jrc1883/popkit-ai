---
title: Hook Development
description: Creating custom lifecycle hooks
---

# Hook Development

Learn how to create custom hooks that respond to lifecycle events in Claude Code.

## Hook Basics

Hooks are event-driven scripts that execute at specific points in the Claude Code lifecycle.

**Key Characteristics**:
- Event-triggered execution
- JSON stdin/stdout protocol
- Cross-platform compatible
- Tested and validated

## Hook Events

### Session Lifecycle

- `SessionStart`: Session begins
- `SessionEnd`: Session ends
- `SessionResume`: Session restored

### Message Events

- `FirstMessage`: Before first user message
- `UserMessage`: After each user message
- `AssistantMessage`: After Claude responds

### File Events

- `FileCreate`: File created
- `FileModify`: File modified
- `FileDelete`: File deleted

### Git Events

- `GitCommit`: Before/after commits
- `GitPush`: Before/after push
- `GitPR`: Pull request created

## Hook Protocol

### Input Format (stdin)

```json
{
  "event": "SessionStart",
  "timestamp": "2026-01-14T12:00:00Z",
  "data": {
    "cwd": "/path/to/project",
    "user": "username"
  }
}
```

### Output Format (stdout)

```json
{
  "status": "success",
  "message": "Hook executed successfully",
  "data": {
    "result": "value"
  }
}
```

### Error Format (stdout)

```json
{
  "status": "error",
  "message": "Error description",
  "error": {
    "code": "ERROR_CODE",
    "details": "Additional details"
  }
}
```

## Creating Hooks

### 1. Create Hook Script

Create Python script in `hooks/` directory:

```python
#!/usr/bin/env python3
"""
SessionStart hook for my plugin
"""
import sys
import json

def main():
    # Read input from stdin
    input_data = json.loads(sys.stdin.read())

    # Extract event data
    event = input_data.get("event")
    data = input_data.get("data", {})

    # Process event
    result = process_session_start(data)

    # Output result to stdout
    output = {
        "status": "success",
        "message": "Session started successfully",
        "data": result
    }
    print(json.dumps(output))

def process_session_start(data):
    """Process session start event"""
    cwd = data.get("cwd")
    # Do something with the data
    return {"project": cwd}

if __name__ == "__main__":
    main()
```

### 2. Register Hook

Add to `hooks/hooks.json`:

```json
{
  "SessionStart": {
    "type": "command",
    "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/session-start.py\"",
    "timeout": 10000
  }
}
```

### 3. Test Hook

Create test file in `hooks/tests/`:

```python
import json
import subprocess

def test_session_start():
    """Test SessionStart hook"""
    input_data = {
        "event": "SessionStart",
        "data": {
            "cwd": "/test/project"
        }
    }

    # Run hook
    result = subprocess.run(
        ["python", "hooks/session-start.py"],
        input=json.dumps(input_data),
        capture_output=True,
        text=True
    )

    # Verify output
    output = json.loads(result.stdout)
    assert output["status"] == "success"
    assert "project" in output["data"]
```

## Portability Standards

### Path Conventions

Use `${CLAUDE_PLUGIN_ROOT}` for plugin-relative paths:

```json
{
  "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/my-hook.py\""
}
```

### Windows Compatibility

- Double-quote paths
- Use forward slashes
- Handle drive letters

```json
{
  "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/my-hook.py\""
}
```

### Python Shebang

Use portable shebang:

```python
#!/usr/bin/env python3
```

## Hook Configuration

### Timeout

Set reasonable timeout (milliseconds):

```json
{
  "SessionStart": {
    "type": "command",
    "command": "...",
    "timeout": 10000  // 10 seconds
  }
}
```

### Error Handling

Always handle errors gracefully:

```python
def main():
    try:
        input_data = json.loads(sys.stdin.read())
        result = process_event(input_data)
        output = {
            "status": "success",
            "data": result
        }
    except Exception as e:
        output = {
            "status": "error",
            "message": str(e),
            "error": {
                "code": "HOOK_ERROR",
                "details": traceback.format_exc()
            }
        }
    print(json.dumps(output))
```

## Advanced Hooks

### Async Operations

For long-running operations:

```python
import asyncio

async def process_async(data):
    # Long operation
    result = await fetch_data()
    return result

def main():
    input_data = json.loads(sys.stdin.read())
    result = asyncio.run(process_async(input_data["data"]))
    output = {"status": "success", "data": result}
    print(json.dumps(output))
```

### File Operations

Read/write files safely:

```python
import os
from pathlib import Path

def main():
    input_data = json.loads(sys.stdin.read())
    cwd = input_data["data"]["cwd"]

    # Safe file path
    project_file = Path(cwd) / ".popkit" / "state.json"

    # Ensure directory exists
    project_file.parent.mkdir(parents=True, exist_ok=True)

    # Write data
    with open(project_file, "w") as f:
        json.dump({"state": "ready"}, f)
```

### External Commands

Run external commands:

```python
import subprocess

def main():
    input_data = json.loads(sys.stdin.read())

    # Run git command
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=input_data["data"]["cwd"],
        capture_output=True,
        text=True
    )

    output = {
        "status": "success",
        "data": {"git_status": result.stdout}
    }
    print(json.dumps(output))
```

## Best Practices

1. **Fast Execution**: Keep hooks under 10 seconds
2. **Error Handling**: Always handle and report errors
3. **JSON Protocol**: Strict adherence to protocol
4. **Portability**: Use standards for cross-platform
5. **Testing**: Comprehensive test coverage
6. **Documentation**: Clear purpose and behavior
7. **Logging**: Log to file, not stdout

## Example: Custom Git Hook

```python
#!/usr/bin/env python3
"""
GitCommit hook for custom validation
"""
import sys
import json
import subprocess
from pathlib import Path

def main():
    try:
        input_data = json.loads(sys.stdin.read())
        data = input_data.get("data", {})

        # Validate commit
        validation = validate_commit(data)

        if not validation["valid"]:
            output = {
                "status": "error",
                "message": validation["message"]
            }
        else:
            output = {
                "status": "success",
                "message": "Commit validation passed",
                "data": validation
            }

        print(json.dumps(output))

    except Exception as e:
        output = {
            "status": "error",
            "message": str(e)
        }
        print(json.dumps(output))

def validate_commit(data):
    """Validate commit meets requirements"""
    cwd = data.get("cwd")

    # Check for required patterns
    result = subprocess.run(
        ["git", "diff", "--staged"],
        cwd=cwd,
        capture_output=True,
        text=True
    )

    diff = result.stdout

    # Custom validation logic
    if "TODO" in diff:
        return {
            "valid": False,
            "message": "Commit contains TODO comments"
        }

    return {
        "valid": True,
        "message": "Commit validation passed"
    }

if __name__ == "__main__":
    main()
```

## Troubleshooting

### Hook Not Executing

**Symptom**: Hook doesn't run

**Solution**:
- Check `hooks.json` syntax
- Verify script permissions
- Test script manually
- Check timeout value

### JSON Parse Errors

**Symptom**: Hook fails with parse error

**Solution**:
- Validate JSON output
- Check for extra stdout
- Remove debug prints
- Use proper JSON encoding

### Timeout Errors

**Symptom**: Hook times out

**Solution**:
- Optimize hook execution
- Increase timeout value
- Move slow operations to background
- Use async for long operations

## Next Steps

- Review [Custom Skills](/guides/custom-skills/)
- Learn about [Agent Configuration](/guides/agent-config/)
- Explore existing hooks in PopKit packages
