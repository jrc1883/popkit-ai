# Skill: E2B Sandbox Manager
# Description: Provides safe, isolated environments for code execution and testing. Essential for multi-agent swarms to avoid local file conflicts.

## Tools

### sandbox_create
Create a new ephemeral sandbox environment.
- **template** (string): The environment template (default: "claude-code-sandbox").
- **timeout** (integer): Timeout in seconds (default: 300).
- **returns**: `sandbox_id` (string)

### sandbox_run_command
Execute a shell command inside a specific sandbox.
- **sandbox_id** (string): The ID returned by `sandbox_create`.
- **command** (string): The shell command to execute.
- **background** (boolean): If true, runs without waiting for completion.
- **returns**: `stdout`, `stderr`, and `exit_code`.

### sandbox_write_file
Write content to a file inside the sandbox.
- **sandbox_id** (string): The sandbox ID.
- **path** (string): The file path inside the sandbox (e.g., "/home/user/app.py").
- **content** (string): The text content to write.
- **returns**: "Success" or error message.

### sandbox_read_file
Retrieve file content from the sandbox.
- **sandbox_id** (string): The sandbox ID.
- **path** (string): The path to read.
- **returns**: File content.

### sandbox_list
List all active sandboxes managed by this session.
- **returns**: JSON list of active sandboxes.

### sandbox_kill
Terminate a specific sandbox.
- **sandbox_id** (string): The ID to terminate.
- **returns**: Confirmation status.

## Script Path
`scripts/sandbox_manager.py`

## Requirements
`e2b-code-interpreter`
`python-dotenv`