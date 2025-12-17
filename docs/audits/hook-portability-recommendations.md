# Hook Portability - Action Items

**Generated:** 2025-12-16
**Source:** [Full Audit Report](./hook-portability-audit-2025-12-16.md)
**Issue:** #260

---

## Priority 1: Must Fix Before v1.0.0

### 1. Remove `shell=True` from subprocess calls
**Files:** `issue-workflow.py`, `quality-gate.py`
**Instances:** 10 total

**Current (unsafe):**
```python
subprocess.run("git checkout .", shell=True, cwd=str(self.cwd), check=True)
subprocess.run("git clean -fd", shell=True, cwd=str(self.cwd), check=True)
```

**Fixed (safe):**
```python
subprocess.run(["git", "checkout", "."], cwd=str(self.cwd), check=True)
subprocess.run(["git", "clean", "-fd"], cwd=str(self.cwd), check=True)
```

**Why:**
- Security: Prevents shell injection
- Portability: Consistent behavior across Windows/Unix
- Reliability: No shell parsing differences

**Effort:** 2-3 hours
**Risk:** Medium (security vulnerability)

---

## Priority 2: Should Fix for v1.0.0

### 2. Add Windows paths to security checks
**File:** `pre-tool-use.py`
**Lines:** 109, 111, 156

**Current:**
```python
"Write:/etc/",
"Edit:/etc/",
```

**Enhanced:**
```python
RESTRICTED_PATHS = {
    # Unix
    "/etc/", "/var/", "/usr/",
    # Windows
    "C:\\Windows\\System32", "C:\\Windows\\config",
    # macOS
    "/System/", "/Library/System"
}
```

**Effort:** 30 minutes
**Risk:** Low (enhancement)

---

### 3. Create requirements.txt for plugin
**Location:** `packages/plugin/requirements.txt`

**Content:**
```txt
# PopKit Plugin - Python Dependencies
# Required for hooks to function

# HTTP client (used in 11+ hooks)
requests>=2.31.0,<3.0.0

# Note: sqlite3 is built-in to Python, no install needed
```

**Also update:** Installation docs to mention `pip install -r requirements.txt`

**Effort:** 15 minutes
**Risk:** None (documentation)

---

## Priority 3: Nice to Have (v1.1.0+)

### 4. Fix Git Bash fallback path
**File:** `utils/platform_detector.py`
**Line:** 166

**Current:**
```python
return ShellType.GIT_BASH, bash_path or "/usr/bin/bash"
```

**Fixed:**
```python
return ShellType.GIT_BASH, bash_path or shutil.which("bash") or "bash"
```

**Effort:** 5 minutes
**Risk:** Very low (edge case)

---

### 5. Add automated portability tests
**Location:** `packages/plugin/tests/test_hook_portability.py`

**Tests to add:**
- Verify all hooks have shebangs
- Flag any `subprocess.run(shell=True)`
- Verify no hardcoded Unix paths
- Verify all paths use `pathlib.Path`

**Effort:** 4-6 hours
**Risk:** None (testing only)

---

## Quick Wins (Do These First)

1. Create `requirements.txt` (15 min)
2. Fix Git Bash fallback (5 min)
3. Add Windows security paths (30 min)

**Total time:** 50 minutes for 3 improvements

---

## Implementation Checklist

### Phase 1: Quick Fixes (1 hour)
- [ ] Create `packages/plugin/requirements.txt`
- [ ] Fix `platform_detector.py` line 166
- [ ] Add Windows paths to `pre-tool-use.py` security checks
- [ ] Update installation docs

### Phase 2: Security Hardening (2-3 hours)
- [ ] Refactor `issue-workflow.py` subprocess calls (5 instances)
- [ ] Refactor `quality-gate.py` subprocess calls (5 instances)
- [ ] Test on Windows (Git Bash, PowerShell, CMD)
- [ ] Test on macOS
- [ ] Test on Linux

### Phase 3: Long-term (Future)
- [ ] Create automated portability tests
- [ ] Set up CI/CD matrix testing (Windows, macOS, Linux)
- [ ] Document platform-specific behaviors

---

## Testing Plan

### Manual Testing
1. **Windows 10/11:**
   - Git Bash
   - PowerShell
   - CMD
   - Python 3.8, 3.9, 3.10, 3.11, 3.12, 3.13

2. **macOS:**
   - Bash (default on older macOS)
   - Zsh (default on macOS 10.15+)
   - Python 3.8+

3. **Linux (Ubuntu):**
   - Bash
   - Zsh
   - Python 3.8+

### Automated Testing (Future)
```yaml
# .github/workflows/hook-portability.yml
strategy:
  matrix:
    os: [ubuntu-latest, macos-latest, windows-latest]
    python: ['3.8', '3.9', '3.10', '3.11', '3.12', '3.13']
```

---

## Risk Assessment

| Issue | Risk Level | Impact | Likelihood | Mitigation |
|-------|-----------|--------|-----------|-----------|
| shell=True injection | MEDIUM | High | Low | Refactor to list syntax |
| Missing Windows paths | LOW | Low | Medium | Add to security checks |
| Missing requirements.txt | LOW | Medium | High | Create file, update docs |
| Git Bash fallback | VERY LOW | Low | Very Low | Use shutil.which() |

---

## Success Criteria

✅ **All hooks work on:**
- Windows 10/11 (Git Bash, PowerShell, CMD)
- macOS 10.15+ (Bash, Zsh)
- Linux Ubuntu 20.04+ (Bash, Zsh)

✅ **No security warnings from:**
- Bandit (Python security linter)
- CodeQL (GitHub security scanning)

✅ **All tests pass on:**
- CI/CD matrix (Windows, macOS, Linux)

---

## Resources

- [Full Audit Report](./hook-portability-audit-2025-12-16.md)
- [subprocess Security Best Practices](https://docs.python.org/3/library/subprocess.html#security-considerations)
- [pathlib Documentation](https://docs.python.org/3/library/pathlib.html)
- [Platform Detection in Python](https://docs.python.org/3/library/sys.html#sys.platform)

---

**Next Step:** Start with Phase 1 (Quick Fixes) - should take ~1 hour total.
