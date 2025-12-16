# Issue #254 - Benchmark CLI Never Starts (FIXED)

**Date:** 2025-12-16
**Status:** ✅ RESOLVED
**Severity:** P1-high (blocking benchmark validation)

## Summary

Fixed critical bug where Claude Code CLI never started on Windows during benchmark execution, causing all benchmark runs to timeout after 600 seconds with 0 tokens and 0 tool calls.

## Root Cause

**Problem:** Node.js `spawn()` without `shell: true` cannot find npm global commands on Windows.

**Why:**
- npm installs global commands as `.cmd` wrapper files on Windows
- `spawn()` without `shell` doesn't search PATH for `.cmd` extensions
- The `claude` command is installed via npm as `claude.cmd`
- Without shell, Windows can't find the executable → ENOENT error

## Symptoms

```
Duration: Exactly 600s (timeout)
Tokens: 0 input, 0 output
Tool calls: 0
Error: "Command timed out after 600000ms"
Exit code: -4058 (ENOENT)
Transcript: Empty
```

## Investigation Process

1. **Compared task configurations** - No significant differences between working/failing tasks
2. **Examined CLI invocation** - Found spawn() call at line 662
3. **Created manual reproduction test** - `test-issue-239.ts` to isolate the issue
4. **Discovered ENOENT error** - `spawn claude ENOENT` when running test
5. **Identified missing shell option** - spawn() needs `shell: true` on Windows
6. **Tested fix** - Confirmed Claude CLI starts and produces output

## The Fix

**File:** `packages/benchmarks/src/runners/claude-runner.ts`
**Line:** 667

```typescript
const proc: ChildProcess = spawn(command, args, {
  cwd: options.cwd,
  env: options.env || process.env,
  stdio: ['pipe', 'pipe', 'pipe'],
  windowsHide: false,
  shell: process.platform === 'win32', // FIX: Use shell on Windows
});
```

**Why this works:**
- `shell: true` on Windows uses `cmd.exe` to execute commands
- cmd.exe searches PATH and resolves `.cmd` extensions
- Now finds `claude.cmd` in npm's global bin directory

**Why only on Windows:**
- Unix systems use bash/sh which already searches PATH
- Unix executables don't need extensions (.cmd)
- Adding `shell: true` on Unix is unnecessary overhead

## Testing

**Manual Test:**
```bash
cd packages/benchmarks
npx tsx test-issue-239.ts
```

**Before fix:**
```
[Test] ❌ Process error: spawn claude ENOENT
❌ REPRODUCED: CLI never started producing output!
```

**After fix:**
```
[Test] ✓ Wrote prompt to stdin
[Test] ✓ Got stdout: {"type":"system","subtype":"init"...
✓ CLI produced output - issue NOT reproduced
```

**Benchmark Test:**
```bash
cd packages/benchmarks
npm run benchmark -- bug-fix vanilla --verbose
```

**Result:** ✅ Claude CLI starts, produces stream-json output, completes task

## Impact

**Before:**
- ❌ All benchmarks on Windows failed with timeout
- ❌ github-issue-239-cache: 0 tokens, 600s timeout
- ❌ Cannot validate self-testing framework (Issue #258)
- ❌ Cannot measure PopKit value proposition

**After:**
- ✅ Benchmarks start successfully on Windows
- ✅ CLI produces stream-json output
- ✅ Can validate behavior capture and testing framework
- ✅ Can measure qualitative differences (workflow metrics)

## Safeguards Added

1. **Manual reproduction test** - `test-issue-239.ts` for debugging
2. **Shell option only on Windows** - No performance impact on Unix
3. **Detailed commit message** - Documents root cause for future reference

## Lessons Learned

1. **spawn() vs shell**
   - Always use `shell: true` for npm global commands on Windows
   - Test on Windows when using subprocess execution
   - npm `.cmd` wrappers require shell resolution

2. **Debugging subprocess issues**
   - Check for ENOENT errors (command not found)
   - Verify PATH resolution manually
   - Create minimal reproduction tests

3. **Cross-platform considerations**
   - Windows and Unix handle executables differently
   - Test on both platforms for subprocess code
   - Use platform checks for OS-specific behavior

## Files Changed

| File | Change | Purpose |
|------|--------|---------|
| `src/runners/claude-runner.ts:667` | Added `shell: true` on Windows | Fix CLI not found |
| `test-issue-239.ts` | New file | Manual reproduction test |

## Commit

```
488c9e3 fix(benchmarks): use shell on Windows to find Claude CLI in PATH (#254)
```

## Related Issues

- #254 - Benchmark runner fails (THIS ISSUE - NOW FIXED)
- #258 - Self-testing framework (UNBLOCKED by this fix)
- #256 - Workflow metrics (UNBLOCKED by this fix)
- #257 - Vibe benchmarks (UNBLOCKED by this fix)

## Next Steps

1. ✅ Close Issue #254
2. Run full benchmark suite to validate fix
3. Continue with Issue #256 (workflow metrics integration)
4. Complete Issue #258 (self-testing framework validation)

---

**Status:** COMPLETE ✅
**Time to Fix:** ~2 hours
**Blockers Removed:** 3 issues (self-testing, metrics, vibe benchmarks)
