# Hook Script Portability Audit - Issue #260

**Date:** 2025-12-16
**Auditor:** Agent 3 (Power Mode Session: power-20251216-213050)
**Scope:** All 23 hook scripts in `packages/plugin/hooks/`
**Status:** ✅ COMPLETE

---

## Executive Summary

All 23 hook scripts have been audited for cross-platform portability (Windows, macOS, Linux). The overall assessment is **GOOD** with minor recommendations for improvement. The hooks are generally well-designed for portability using Python's cross-platform libraries (`pathlib`, `subprocess`, `os`).

### Key Findings

- ✅ **All hooks use proper shebangs** (`#!/usr/bin/env python3`)
- ✅ **Cross-platform path handling** via `pathlib.Path`
- ✅ **Platform detection** via dedicated `platform_detector.py` utility
- ⚠️ **3 minor portability issues** requiring attention
- ✅ **hooks.json uses generic `python` command** (relies on PATH)

---

## Inventory: All 23 Hook Scripts

### Core Hooks (Always Active)
1. `pre-tool-use.py` - Safety checks and coordination
2. `post-tool-use.py` - Logging and metrics
3. `agent-orchestrator.py` - Intelligent agent selection
4. `chain-validator.py` - Validation checks
5. `agent-observability.py` - Observability events
6. `context-monitor.py` - Context tracking
7. `quality-gate.py` - Code integrity validation
8. `doc-sync.py` - Documentation sync
9. `chain-metrics.py` - Metrics collection
10. `command-learning-hook.py` - Command learning
11. `bug_reporter_hook.py` - Bug reporting
12. `feedback_hook.py` - Feedback collection
13. `user-prompt-submit.py` - User prompt handling
14. `session-start.py` - Session initialization
15. `knowledge-sync.py` - Knowledge synchronization
16. `stop.py` - Session stop
17. `subagent-stop.py` - Subagent cleanup
18. `output-validator.py` - Output validation
19. `notification.py` - Notification formatting

### Workflow Hooks (Conditional)
20. `issue-workflow.py` - Issue workflow management
21. `agent-context-integration.py` - Agent context integration

### Stateless Variants (Legacy/Testing)
22. `pre_tool_use_stateless.py`
23. `post_tool_use_stateless.py`

---

## Detailed Findings

### ✅ STRENGTHS

#### 1. Consistent Shebangs
All 23 hooks + 60+ utils use `#!/usr/bin/env python3`:
- Works on Unix (macOS, Linux)
- Windows ignores shebangs, relies on `.py` file association
- Proper fallback behavior across platforms

#### 2. Cross-Platform Path Handling
All hooks use `pathlib.Path` consistently:
```python
# Good examples from hooks
Path.home() / '.claude'                    # Works on all platforms
Path(__file__).parent / "utils"            # Relative imports
```

**Locations checked:**
- `~/.claude/` directory: 11 hooks
- `~/.popkit/` directory: 1 hook (test telemetry)
- All use `Path.home()` (cross-platform)

#### 3. Platform Detection Infrastructure
Dedicated `utils/platform_detector.py` with:
- OS detection (Windows, macOS, Linux)
- Shell detection (Bash, PowerShell, CMD, Zsh, etc.)
- Capability detection (Unix commands, PowerShell cmdlets)
- Command availability checking

#### 4. Subprocess Handling
Proper use of `subprocess.run()` with cross-platform considerations:
```python
# Good pattern (most hooks)
subprocess.run(
    ["git", "status"],
    capture_output=True,
    text=True,
    timeout=5
)
```

#### 5. Python Invocation in hooks.json
All hooks use generic `python` command:
```json
"command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/pre-tool-use.py\""
```
- Relies on PATH to resolve `python` → `python.exe` (Windows) or `python3` (Unix)
- Works if Python is properly installed and in PATH

---

### ⚠️ ISSUES REQUIRING ATTENTION

#### Issue 1: Shell Injection Risk with `shell=True`
**Severity:** MEDIUM (Security/Portability)
**Locations:** 10 instances across 3 files

**Affected Files:**
- `issue-workflow.py` (5 instances)
- `quality-gate.py` (5 instances)

**Example:**
```python
# Lines 689-690 in both files
subprocess.run("git checkout .", shell=True, cwd=str(self.cwd), check=True)
subprocess.run("git clean -fd", shell=True, cwd=str(self.cwd), check=True)
```

**Problems:**
1. **Security:** Vulnerable to shell injection if `self.cwd` is user-controlled
2. **Portability:** `shell=True` behaves differently on Windows vs Unix
   - Windows: Uses `cmd.exe` or PowerShell
   - Unix: Uses `/bin/sh`
3. **Reliability:** Shell parsing can vary across platforms

**Recommendation:**
```python
# RECOMMENDED FIX
subprocess.run(
    ["git", "checkout", "."],
    cwd=str(self.cwd),
    check=True,
    capture_output=True
)
subprocess.run(
    ["git", "clean", "-fd"],
    cwd=str(self.cwd),
    check=True,
    capture_output=True
)
```

**Impact:** 10 subprocess calls need refactoring

---

#### Issue 2: Hardcoded Unix Paths in Security Checks
**Severity:** LOW (False positives on Windows)
**Location:** `pre-tool-use.py`

**Details:**
```python
# Lines 109, 111, 156
"Write:/etc/",
"Edit:/etc/",
"restricted_tools": ["Bash:rm -rf", "Write:/etc/"]
```

**Problem:**
- `/etc/` doesn't exist on Windows (system config is in `C:\Windows\System32\config\`)
- Security check is Unix-centric
- Won't trigger false positives on Windows, but conceptually incomplete

**Recommendation:**
Add Windows equivalent paths to security checks:
```python
RESTRICTED_PATHS = [
    "/etc/",                    # Unix system config
    "/var/",                    # Unix system data
    "C:\\Windows\\System32",    # Windows system dir
    "C:\\Windows\\config",      # Windows config
]
```

**Impact:** LOW - Security enhancement, not a blocker

---

#### Issue 3: Git Bash Path Fallback Hardcoded
**Severity:** LOW (Minor inconsistency)
**Location:** `utils/platform_detector.py:166`

**Details:**
```python
return ShellType.GIT_BASH, bash_path or "/usr/bin/bash"
```

**Problem:**
- Fallback to `/usr/bin/bash` doesn't exist on Windows
- Should be more defensive

**Recommendation:**
```python
return ShellType.GIT_BASH, bash_path or shutil.which("bash") or "bash"
```

**Impact:** VERY LOW - Fallback rarely triggered

---

#### Issue 4: Missing Dependency Documentation
**Severity:** LOW (Documentation)
**Location:** Plugin root (`packages/plugin/`)

**Problem:**
- No `requirements.txt` in plugin root
- Only exists in `power-mode/requirements.txt` (Redis-specific)
- Hooks depend on:
  - `requests` (11 hooks)
  - `sqlite3` (11 hooks - built-in to Python)

**Current state:**
- `requests` is **not** in stdlib (must be installed)
- `sqlite3` is built-in (no install needed)

**Recommendation:**
Create `packages/plugin/requirements.txt`:
```txt
# PopKit Plugin - Python Dependencies
# Required for hooks to function

# HTTP client (used in 11+ hooks)
requests>=2.31.0,<3.0.0

# Note: sqlite3 is built-in to Python, no install needed
```

**Impact:** LOW - Installation documentation, not runtime

---

### ✅ VERIFIED CROSS-PLATFORM FEATURES

#### 1. Home Directory Detection
All hooks correctly use `Path.home()`:
- Windows: `C:\Users\<username>`
- macOS: `/Users/<username>`
- Linux: `/home/<username>`

**Locations:**
- 22 instances across hooks and utils
- Consistent usage everywhere

#### 2. File Permissions
**Windows behavior:**
- Shebang (`#!/usr/bin/env python3`) is ignored
- `.py` files execute via file association (`.py` → `python.exe`)
- `chmod +x` has no effect (NTFS ACLs used instead)

**Unix behavior:**
- Shebang determines interpreter
- `chmod +x` makes files executable
- All 23 hooks have execute permission (`-rwxr-xr-x`)

**Verification:**
```bash
# On this Windows system (Git Bash):
$ ls -la *.py | head -5
-rwxr-xr-x 1 Josep 197609  7887 Dec 12 12:04 agent-context-integration.py
-rwxr-xr-x 1 Josep 197609  4478 Nov 27 22:06 agent-observability.py
-rwxr-xr-x 1 Josep 197609 18341 Dec 15 22:47 agent-orchestrator.py
```

✅ **Conclusion:** Permissions are portable (tracked in Git)

#### 3. Text-to-Speech (Platform-Specific)
`notification.py` (lines 308-328) handles TTS correctly:
```python
# Windows TTS
if os.name == 'nt':
    subprocess.run([
        'powershell', '-Command',
        f'Add-Type -AssemblyName System.Speech; ...'
    ], ...)
# macOS TTS
elif sys.platform == 'darwin':
    subprocess.run(['say', message], ...)
```

✅ **Conclusion:** Proper platform detection, graceful fallback

#### 4. Python Path Resolution
`hooks.json` uses `python` (not `python3`):
- **Windows:** `python` → `C:\Program Files\Python313\python.exe`
- **macOS/Linux:** `python` → `/usr/bin/python3` (if aliased/symlinked)

**Current system:**
```bash
$ python --version
Python 3.13.3

$ which python
C:\Program Files\Python313\python.exe
```

✅ **Conclusion:** Works if Python is in PATH (standard installation)

---

## Dependencies Analysis

### Built-in Modules (✅ Always Available)
- `os`, `sys`, `json`, `re`, `sqlite3`
- `subprocess`, `pathlib`, `datetime`
- `typing`, `dataclasses`, `enum`
- `hashlib`, `shutil`

### External Dependencies (⚠️ Require Installation)
1. **`requests`** - Used in 11 hooks
   - HTTP client for API calls
   - NOT in stdlib
   - **Status:** Likely installed (common package), but not documented

### Verification
```python
# Tested on this system:
$ python -c "import requests; import sqlite3; print('OK')"
OK
```

✅ Both dependencies available on audit system

---

## hooks.json Configuration Review

### Command Invocation Pattern
All hooks use:
```json
{
  "type": "command",
  "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/<hook-name>.py\"",
  "timeout": <milliseconds>
}
```

### Portability Assessment
✅ **GOOD:**
- `${CLAUDE_PLUGIN_ROOT}` is cross-platform environment variable
- Quoted paths handle spaces in paths
- Generic `python` works if in PATH

⚠️ **CONSIDERATION:**
- Should it be `python` or `python3`?
  - **Windows:** `python` is correct (no `python3.exe`)
  - **macOS/Linux:** `python3` is more explicit (avoid Python 2.x)

**Current approach:** Using `python` assumes:
1. Python 3.x is installed
2. `python` command points to Python 3
3. No Python 2.x in PATH with higher priority

**Recommendation:** Keep `python` but document requirement:
> "Requires Python 3.7+ available as `python` command in PATH"

---

## Test Recommendations

### 1. Cross-Platform CI/CD Testing
Set up GitHub Actions matrix:
```yaml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
    python-version: ['3.8', '3.9', '3.10', '3.11', '3.12', '3.13']
```

### 2. Manual Testing Checklist
- [ ] Test all hooks on Windows 10/11
- [ ] Test all hooks on macOS (Intel + Apple Silicon)
- [ ] Test all hooks on Linux (Ubuntu, Fedora)
- [ ] Test with different shells (Bash, Zsh, PowerShell, CMD)
- [ ] Test with Python in different PATH locations
- [ ] Test with spaces in installation paths

### 3. Automated Portability Tests
Create `packages/plugin/tests/test_hook_portability.py`:
```python
def test_all_hooks_have_shebangs():
    """Verify all hooks start with #!/usr/bin/env python3"""
    pass

def test_no_shell_true_in_subprocess():
    """Flag any subprocess.run with shell=True"""
    pass

def test_all_paths_use_pathlib():
    """Verify no hardcoded Unix paths"""
    pass
```

---

## Recommendations Summary

### Priority 1: Security & Portability (Must Fix)
1. **Remove `shell=True` from subprocess calls** (10 instances)
   - Files: `issue-workflow.py`, `quality-gate.py`
   - Impact: Security and cross-platform reliability
   - Effort: 2-3 hours

### Priority 2: Enhancement (Should Fix)
2. **Add Windows paths to security checks** (`pre-tool-use.py`)
   - Impact: Comprehensive security coverage
   - Effort: 30 minutes

3. **Create `requirements.txt`** for plugin dependencies
   - Impact: Installation clarity
   - Effort: 15 minutes

### Priority 3: Nice to Have (Optional)
4. **Fix Git Bash fallback path** (`platform_detector.py:166`)
   - Impact: Edge case handling
   - Effort: 5 minutes

5. **Add automated portability tests**
   - Impact: CI/CD confidence
   - Effort: 4-6 hours

---

## Conclusion

**Overall Assessment:** ✅ **GOOD PORTABILITY**

The PopKit hook scripts demonstrate strong cross-platform design:
- Proper use of Python's cross-platform abstractions
- Dedicated platform detection utilities
- Consistent coding patterns across all hooks

**Blocker Issues:** None
**Security Issues:** 1 (Medium - shell injection risk)
**Portability Issues:** 2 (Low severity)

**Recommendation:** Address Priority 1 issues before v1.0.0 release. Priority 2-3 can be scheduled for v1.1.0.

---

## Appendix: File Permissions on Audit System

```bash
# All hooks have execute permissions (Git preserves this)
$ ls -la packages/plugin/hooks/*.py
-rwxr-xr-x 1 Josep 197609  7887 Dec 12 12:04 agent-context-integration.py
-rwxr-xr-x 1 Josep 197609  4478 Nov 27 22:06 agent-observability.py
-rwxr-xr-x 1 Josep 197609 18341 Dec 15 22:47 agent-orchestrator.py
# ... (all 23 files)
```

**Platform:** Windows 10/11 (Git Bash showing Unix-style permissions)
**Python:** 3.13.3 (`C:\Program Files\Python313\python.exe`)
**Git Bash:** Emulates Unix permissions via Git metadata

---

**Audit completed:** 2025-12-16
**Signed:** Agent 3 (Power Mode)
