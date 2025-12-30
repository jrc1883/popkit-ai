# Power Mode Simplification Breakdown

**Date**: 2025-12-29
**Epic**: #580 Plugin Modularization - Phase 6
**Audit Reference**: `docs/assessments/2025-12-29-power-mode-upstash-audit.md`
**Current LOC**: 21,156 (38 files)
**Target LOC**: ~600 (8-10 files)
**Reduction**: 97.2% (20,556 LOC removed)

---

## Executive Summary

Power Mode has grown to 21,156 lines across 38 files. The audit identified that only **400 LOC is truly Upstash-specific code worth keeping**. The rest is either:
- Test files (3,600 LOC) - valuable but not production
- Example files (332 LOC) - documentation only
- Consensus protocol (3,785 LOC) - experimental, never used
- Benchmarking (846 LOC) - development tooling
- Duplicate/experimental coordinators (2,622 LOC) - replaced by native async

This document provides a detailed file-by-file breakdown of what to DELETE vs KEEP.

---

## 1. File Categories

### 1.1 Core Upstash Integration (KEEP - 400 LOC)

These files provide essential Upstash Redis functionality:

| File | LOC | Keep LOC | Keep? | Reason |
|------|-----|----------|-------|--------|
| `upstash_adapter.py` | 499 | 200 | ✅ KEEP | Upstash REST client + Redis Streams pub/sub (lines 189-482) |
| `mode_selector.py` | 311 | 50 | ✅ KEEP | Upstash detection logic (lines 113-135) |
| `check_upstash.py` | 119 | 100 | ✅ KEEP | Debugging tool for Upstash sessions |
| `start_session.py` | 166 | 50 | ✅ KEEP | Upstash session initialization |
| **TOTAL** | **1,095** | **400** | - | **Core functionality** |

**Notes**:
- `upstash_adapter.py`: Keep only Upstash-specific code (REST client, Streams pub/sub). Remove generic Redis interface (moved to shared-py).
- `mode_selector.py`: Keep Upstash detection. Remove file-based and native async logic (moved to main hook).
- `check_upstash.py`: Keep as-is - useful debugging tool.
- `start_session.py`: Keep Upstash init logic only.

### 1.2 Supporting Infrastructure (KEEP - 200 LOC)

Essential supporting files:

| File | LOC | Keep? | Reason |
|------|-----|-------|--------|
| `config.json` | 220 | ✅ KEEP | Power Mode configuration |
| `README.md` | 138 | ✅ KEEP | Documentation (simplify to match new structure) |
| **TOTAL** | **358** | - | **Documentation & config** |

**Notes**:
- `config.json`: Simplify to remove consensus and benchmark configs.
- `README.md`: Rewrite to reflect simplified architecture.

### 1.3 Test Files (DELETE - 3,600 LOC)

Comprehensive test suite - valuable but not for production:

| File | LOC | Delete? | Reason |
|------|-----|---------|--------|
| `test_coordination.py` | 345 | ❌ DELETE | Upstash coordination tests |
| `test_handoff.py` | 355 | ❌ DELETE | Agent handoff tests |
| `test_interleaved.py` | 417 | ❌ DELETE | Concurrent stream tests |
| `test_puzzle_coordination.py` | 551 | ❌ DELETE | Complex coordination tests |
| `test_*.py` (implied others) | ~1,932 | ❌ DELETE | Additional test files |
| **TOTAL** | **~3,600** | - | **Test infrastructure** |

**Action**: Archive to `packages/benchmarks/power-mode/` for future reference.

**Justification**: These tests validate Upstash coordination patterns but aren't needed in production plugin. Keep for benchmarking/validation.

### 1.4 Example & Documentation Files (DELETE - 1,413 LOC)

Tutorial and example code:

| File | LOC | Delete? | Reason |
|------|-----|---------|--------|
| `example_usage.py` | 332 | ❌ DELETE | Usage examples (move to README) |
| `SETUP-REDIS.md` | 393 | ❌ DELETE | Obsolete (we use Upstash, not local Redis) |
| `FALLBACK.md` | 358 | ❌ DELETE | File-based mode docs (replaced by native async) |
| `QUICKSTART.md` | 225 | ❌ DELETE | Quickstart guide (merge into README) |
| `consensus/README.md` | 494 | ❌ DELETE | Consensus protocol docs |
| **TOTAL** | **1,802** | - | **Documentation files** |

**Action**: Extract useful examples into simplified `README.md`, delete the rest.

**Justification**: Over-documented for current scope. Simplify to one README with essential info.

### 1.5 Consensus Protocol (DELETE - 3,785 LOC)

Experimental multi-agent consensus - never used in production:

| File | LOC | Delete? | Reason |
|------|-----|---------|--------|
| `consensus/coordinator.py` | 1,280 | ❌ DELETE | Consensus coordinator |
| `consensus/protocol.py` | 905 | ❌ DELETE | Voting protocol |
| `consensus/triggers.py` | 791 | ❌ DELETE | Consensus triggers |
| `consensus/monitor.py` | 641 | ❌ DELETE | Consensus monitoring |
| `consensus/agent_hook.py` | 587 | ❌ DELETE | Agent consensus hooks |
| `consensus/config.json` | 207 | ❌ DELETE | Consensus configuration |
| `consensus/__init__.py` | 150 | ❌ DELETE | Package init |
| **TOTAL** | **4,561** | - | **Entire consensus/ directory** |

**Action**: DELETE entire `consensus/` directory.

**Justification**: This was an experimental feature for multi-agent voting. Never integrated with main Power Mode workflows. Native async mode (Claude Code 2.0.64+) makes this obsolete.

### 1.6 Benchmarking Infrastructure (DELETE - 846 LOC)

Performance testing and comparison:

| File | LOC | Delete? | Reason |
|------|-----|---------|--------|
| `benchmark.py` | 478 | ❌ DELETE | Benchmark suite |
| `benchmark_coordinator.py` | 368 | ❌ DELETE | Benchmark coordinator |
| **TOTAL** | **846** | - | **Benchmarking tools** |

**Action**: Archive to `packages/benchmarks/power-mode/` alongside tests.

**Justification**: Useful for performance analysis but not needed in production plugin.

### 1.7 Duplicate/Experimental Coordinators (DELETE - 2,622 LOC)

Multiple coordinator implementations - replaced by native async:

| File | LOC | Delete? | Reason |
|------|-----|---------|--------|
| `coordinator.py` | 1,690 | ❌ DELETE | Original Redis coordinator (replaced by native) |
| `native_coordinator.py` | 672 | ❌ DELETE | Native async coordinator (logic moved to hooks) |
| `coordinator_auto.py` | 252 | ❌ DELETE | Auto-selecting coordinator wrapper |
| **TOTAL** | **2,614** | - | **Obsolete coordinators** |

**Action**: DELETE all coordinator files.

**Justification**:
- `coordinator.py`: Original Redis-based coordination. Native async mode (Claude Code 2.0.64+) replaces this entirely.
- `native_coordinator.py`: Wrapper for native async. Logic moved to pre-skill-use hook.
- `coordinator_auto.py`: Auto-selects coordinator. Mode selection now in pre-skill-use hook.

### 1.8 Supporting Services (DELETE - 5,253 LOC)

Cloud integration and supporting services:

| File | LOC | Delete? | Reason |
|------|-----|---------|--------|
| `statusline.py` | 1,440 | ❌ DELETE | Visual status display (not core to Upstash) |
| `checkin-hook.py` | 1,383 | ❌ DELETE | Agent check-in hook (generic, not Upstash) |
| `cloud_client.py` | 1,205 | ❌ DELETE | PopKit Cloud API (separate from Upstash) |
| `protocol.py` | 759 | ❌ DELETE | Message protocol (generic, moved to shared) |
| `file_fallback.py` | 615 | ❌ DELETE | File-based mode (replaced by native async) |
| `metrics.py` | 559 | ❌ DELETE | Metrics collection (not Upstash-specific) |
| `stream_manager.py` | 515 | ❌ DELETE | Generic streaming (not Upstash-specific) |
| `insight_embedder.py` | 463 | ❌ DELETE | Embeddings via Cloud API (not direct Upstash) |
| `async_support.py` | 493 | ❌ DELETE | Async helpers (generic utilities) |
| `logger.py` | 429 | ❌ DELETE | Logging utilities (generic) |
| `pattern_client.py` | 351 | ❌ DELETE | Pattern DB via Cloud API (not Upstash) |
| **TOTAL** | **8,212** | - | **Supporting services** |

**Action**: DELETE all supporting service files.

**Justification**:
- **Cloud API files** (`cloud_client.py`, `insight_embedder.py`, `pattern_client.py`): These use PopKit Cloud API, which abstracts Upstash. Not direct Upstash integration. Keep in main plugin, not in Upstash-specific stack.
- **Generic utilities** (`protocol.py`, `logger.py`, `metrics.py`, `async_support.py`): Moved to `packages/shared-py` during Epic #580.
- **Fallback mode** (`file_fallback.py`): Obsolete - replaced by native async mode.
- **Status display** (`statusline.py`): Nice-to-have but not core. Can recreate if needed.
- **Check-in hook** (`checkin-hook.py`): Agent coordination logic, not Upstash-specific.
- **Stream manager** (`stream_manager.py`): Generic streaming, not specific to Upstash Streams.

---

## 2. Deletion Plan

### Phase 1: Archive Test & Benchmark Files

**Target**: `packages/benchmarks/power-mode/`

```bash
mkdir -p packages/benchmarks/power-mode/tests
mkdir -p packages/benchmarks/power-mode/benchmarks

# Move test files
mv packages/popkit-core/power-mode/test_*.py packages/benchmarks/power-mode/tests/

# Move benchmark files
mv packages/popkit-core/power-mode/benchmark*.py packages/benchmarks/power-mode/benchmarks/
```

**Files**:
- `test_coordination.py` (345 LOC)
- `test_handoff.py` (355 LOC)
- `test_interleaved.py` (417 LOC)
- `test_puzzle_coordination.py` (551 LOC)
- `benchmark.py` (478 LOC)
- `benchmark_coordinator.py` (368 LOC)

**Total Archived**: 2,514 LOC

### Phase 2: Delete Consensus Protocol

**Action**: DELETE entire directory

```bash
rm -rf packages/popkit-core/power-mode/consensus/
```

**Files Removed**:
- `consensus/coordinator.py` (1,280 LOC)
- `consensus/protocol.py` (905 LOC)
- `consensus/triggers.py` (791 LOC)
- `consensus/monitor.py` (641 LOC)
- `consensus/agent_hook.py` (587 LOC)
- `consensus/config.json` (207 LOC)
- `consensus/__init__.py` (150 LOC)
- `consensus/README.md` (494 LOC)

**Total Deleted**: 5,055 LOC

### Phase 3: Delete Example & Documentation Files

**Action**: Extract useful snippets to README, then delete

```bash
# Extract examples to new README.md
# Then delete:
rm packages/popkit-core/power-mode/example_usage.py
rm packages/popkit-core/power-mode/SETUP-REDIS.md
rm packages/popkit-core/power-mode/FALLBACK.md
rm packages/popkit-core/power-mode/QUICKSTART.md
```

**Files Removed**:
- `example_usage.py` (332 LOC)
- `SETUP-REDIS.md` (393 LOC)
- `FALLBACK.md` (358 LOC)
- `QUICKSTART.md` (225 LOC)

**Total Deleted**: 1,308 LOC

### Phase 4: Delete Coordinator Files

**Action**: DELETE all coordinator implementations

```bash
rm packages/popkit-core/power-mode/coordinator.py
rm packages/popkit-core/power-mode/native_coordinator.py
rm packages/popkit-core/power-mode/coordinator_auto.py
```

**Files Removed**:
- `coordinator.py` (1,690 LOC)
- `native_coordinator.py` (672 LOC)
- `coordinator_auto.py` (252 LOC)

**Total Deleted**: 2,614 LOC

### Phase 5: Delete Supporting Services

**Action**: DELETE generic utilities and cloud integration

```bash
rm packages/popkit-core/power-mode/statusline.py
rm packages/popkit-core/power-mode/checkin-hook.py
rm packages/popkit-core/power-mode/cloud_client.py
rm packages/popkit-core/power-mode/protocol.py
rm packages/popkit-core/power-mode/file_fallback.py
rm packages/popkit-core/power-mode/metrics.py
rm packages/popkit-core/power-mode/stream_manager.py
rm packages/popkit-core/power-mode/insight_embedder.py
rm packages/popkit-core/power-mode/async_support.py
rm packages/popkit-core/power-mode/logger.py
rm packages/popkit-core/power-mode/pattern_client.py
```

**Files Removed**:
- `statusline.py` (1,440 LOC)
- `checkin-hook.py` (1,383 LOC)
- `cloud_client.py` (1,205 LOC)
- `protocol.py` (759 LOC)
- `file_fallback.py` (615 LOC)
- `metrics.py` (559 LOC)
- `stream_manager.py` (515 LOC)
- `insight_embedder.py` (463 LOC)
- `async_support.py` (493 LOC)
- `logger.py` (429 LOC)
- `pattern_client.py` (351 LOC)

**Total Deleted**: 8,212 LOC

### Phase 6: Simplify Remaining Files

**Action**: Edit core files to remove non-Upstash code

| File | Current LOC | Target LOC | Changes |
|------|-------------|------------|---------|
| `upstash_adapter.py` | 499 | 200 | Remove generic Redis interface (moved to shared-py), keep only Upstash REST + Streams |
| `mode_selector.py` | 311 | 50 | Keep only Upstash detection, remove file/native logic |
| `check_upstash.py` | 119 | 100 | Minor cleanup |
| `start_session.py` | 166 | 50 | Keep only Upstash init logic |
| `config.json` | 220 | 100 | Remove consensus/benchmark configs |
| `README.md` | 138 | 100 | Rewrite for simplified structure |

**Total Reduction**: 700 LOC

---

## 3. Final Structure

After simplification, Power Mode will contain:

```
packages/popkit-core/power-mode/
├── upstash_adapter.py        (200 LOC) - Upstash REST client + Streams pub/sub
├── mode_selector.py          ( 50 LOC) - Upstash availability detection
├── check_upstash.py          (100 LOC) - Debugging tool
├── start_session.py          ( 50 LOC) - Session initialization
├── config.json               (100 LOC) - Configuration
└── README.md                 (100 LOC) - Documentation

Total: ~600 LOC (6 files)
```

**Reduction**: 21,156 → 600 LOC (97.2% reduction)

---

## 4. LOC Summary

### Current State (38 files, 21,156 LOC)

| Category | Files | LOC | % of Total |
|----------|-------|-----|------------|
| Core Upstash | 4 | 1,095 | 5.2% |
| Supporting Infrastructure | 2 | 358 | 1.7% |
| **Tests** | 4+ | 3,600 | 17.0% |
| **Examples/Docs** | 5 | 1,802 | 8.5% |
| **Consensus Protocol** | 8 | 5,055 | 23.9% |
| **Benchmarking** | 2 | 846 | 4.0% |
| **Coordinators** | 3 | 2,614 | 12.4% |
| **Supporting Services** | 11 | 8,212 | 38.8% |
| **TOTAL** | **38** | **21,156** | **100%** |

### After Simplification (6 files, ~600 LOC)

| Category | Files | LOC | % of Final |
|----------|-------|-----|------------|
| Core Upstash Integration | 4 | 400 | 66.7% |
| Configuration & Docs | 2 | 200 | 33.3% |
| **TOTAL** | **6** | **600** | **100%** |

### What Happens to Deleted Files?

| Category | LOC | Action |
|----------|-----|--------|
| Tests | 3,600 | Archive to `packages/benchmarks/power-mode/tests/` |
| Benchmarks | 846 | Archive to `packages/benchmarks/power-mode/benchmarks/` |
| Consensus | 5,055 | DELETE (experimental, never used) |
| Examples/Docs | 1,802 | DELETE (merge into README) |
| Coordinators | 2,614 | DELETE (replaced by native async) |
| Supporting Services | 8,212 | DELETE (moved to shared-py or cloud API) |
| **TOTAL REMOVED** | **22,129** | - |

**Note**: Some LOC counts overlap (e.g., consensus includes docs), so total removed > 20,556.

---

## 5. Risks & Mitigation

### Risk 1: Losing Test Coverage

**Concern**: Deleting tests reduces confidence in Upstash integration.

**Mitigation**:
- Archive tests to `packages/benchmarks/power-mode/tests/`
- Can re-run archived tests anytime
- Document how to run archived tests in README

### Risk 2: Breaking Existing Power Mode Users

**Concern**: Users on older versions might break.

**Mitigation**:
- This is Epic #580 modularization - already breaking changes
- Power Mode is Pro tier (small user base)
- Clear migration guide in CHANGELOG

### Risk 3: Losing Valuable Code

**Concern**: Some "deleted" code might be needed later.

**Mitigation**:
- Git history preserves everything
- Archive tests/benchmarks instead of deleting
- Document what was removed and why in this file

### Risk 4: Documentation Gaps

**Concern**: Deleting 5 docs might lose important info.

**Mitigation**:
- Extract key examples into simplified README
- Link to audit document for technical details
- Reference git history for deleted docs

---

## 6. Implementation Checklist

### Pre-Deletion
- [ ] Backup current state: `git checkout -b backup/power-mode-pre-simplification`
- [ ] Create archive directories: `packages/benchmarks/power-mode/{tests,benchmarks}`
- [ ] Review each file marked for deletion
- [ ] Extract useful examples from `example_usage.py` to new README

### Deletion Phases
- [ ] Phase 1: Archive tests & benchmarks (2,514 LOC)
- [ ] Phase 2: Delete consensus/ directory (5,055 LOC)
- [ ] Phase 3: Delete example/doc files (1,308 LOC)
- [ ] Phase 4: Delete coordinator files (2,614 LOC)
- [ ] Phase 5: Delete supporting services (8,212 LOC)
- [ ] Phase 6: Simplify remaining files (700 LOC reduction)

### Post-Deletion
- [ ] Verify plugin still loads: `claude --plugin-dir ./packages/popkit-core`
- [ ] Test Upstash detection: `/popkit:power status`
- [ ] Update `packages/popkit-core/README.md`
- [ ] Update `CHANGELOG.md` with breaking changes
- [ ] Commit with message: "refactor(power-mode): simplify to 600 LOC Upstash-specific code"

### Validation
- [ ] Run archived tests manually to verify they still work
- [ ] Test Power Mode with real Upstash credentials
- [ ] Verify mode selection (native > upstash > disabled)
- [ ] Check that shared-py utilities are imported correctly

---

## 7. Breaking Changes (CHANGELOG Entry)

```markdown
## [1.0.0-beta.1] - 2025-12-29

### BREAKING CHANGES - Power Mode Simplification

**Epic #580**: Simplified Power Mode from 21,156 LOC (38 files) to 600 LOC (6 files).

**Removed**:
- **Consensus Protocol**: Entire `consensus/` directory (5,055 LOC) - experimental feature, never used
- **Coordinator Files**: `coordinator.py`, `native_coordinator.py`, `coordinator_auto.py` (2,614 LOC) - replaced by native async mode
- **File-Based Fallback**: `file_fallback.py` (615 LOC) - replaced by native async mode (Claude Code 2.0.64+)
- **Supporting Services**: 11 files (8,212 LOC) - moved to shared-py or cloud API
- **Examples/Docs**: 5 files (1,802 LOC) - merged into simplified README

**Archived** (available in `packages/benchmarks/power-mode/`):
- Test suite: `test_*.py` (3,600 LOC)
- Benchmarks: `benchmark*.py` (846 LOC)

**Migration**:
- Power Mode now requires Claude Code 2.0.64+ (native async mode)
- Upstash Redis optional (Pro tier) - set `UPSTASH_REDIS_REST_URL` and `UPSTASH_REDIS_REST_TOKEN`
- No action needed for most users - mode auto-detects

**Kept** (Upstash-specific code):
- `upstash_adapter.py` (200 LOC) - Upstash REST client + Redis Streams pub/sub
- `mode_selector.py` (50 LOC) - Upstash detection
- `check_upstash.py` (100 LOC) - Debugging tool
- `start_session.py` (50 LOC) - Session initialization
```

---

## 8. Next Steps

1. **Review this breakdown** - Ensure all deletions are justified
2. **Extract examples** - Pull useful snippets from `example_usage.py` into new README
3. **Create archive structure** - Set up `packages/benchmarks/power-mode/`
4. **Execute deletion plan** - Follow Phase 1-6 in order
5. **Update documentation** - Rewrite README, update CHANGELOG
6. **Test thoroughly** - Verify Power Mode still works with Upstash
7. **Commit changes** - Clear commit message referencing Epic #580

---

## Appendix A: File-by-File Decision Matrix

| File | LOC | Keep? | Reason | Action |
|------|-----|-------|--------|--------|
| `upstash_adapter.py` | 499 | ✅ Partial | Upstash REST + Streams (200 LOC) | Edit to 200 LOC |
| `mode_selector.py` | 311 | ✅ Partial | Upstash detection (50 LOC) | Edit to 50 LOC |
| `check_upstash.py` | 119 | ✅ Yes | Debugging tool | Minor cleanup to 100 LOC |
| `start_session.py` | 166 | ✅ Partial | Session init (50 LOC) | Edit to 50 LOC |
| `config.json` | 220 | ✅ Partial | Configuration | Edit to 100 LOC |
| `README.md` | 138 | ✅ Partial | Documentation | Rewrite to 100 LOC |
| `test_coordination.py` | 345 | ❌ Archive | Tests | Move to benchmarks/ |
| `test_handoff.py` | 355 | ❌ Archive | Tests | Move to benchmarks/ |
| `test_interleaved.py` | 417 | ❌ Archive | Tests | Move to benchmarks/ |
| `test_puzzle_coordination.py` | 551 | ❌ Archive | Tests | Move to benchmarks/ |
| `benchmark.py` | 478 | ❌ Archive | Benchmarking | Move to benchmarks/ |
| `benchmark_coordinator.py` | 368 | ❌ Archive | Benchmarking | Move to benchmarks/ |
| `example_usage.py` | 332 | ❌ Delete | Examples | Extract to README |
| `SETUP-REDIS.md` | 393 | ❌ Delete | Obsolete docs | Delete |
| `FALLBACK.md` | 358 | ❌ Delete | Obsolete docs | Delete |
| `QUICKSTART.md` | 225 | ❌ Delete | Docs | Merge to README |
| `coordinator.py` | 1,690 | ❌ Delete | Replaced by native | Delete |
| `native_coordinator.py` | 672 | ❌ Delete | Logic in hooks now | Delete |
| `coordinator_auto.py` | 252 | ❌ Delete | Logic in hooks now | Delete |
| `statusline.py` | 1,440 | ❌ Delete | Not core | Delete |
| `checkin-hook.py` | 1,383 | ❌ Delete | Generic, not Upstash | Delete |
| `cloud_client.py` | 1,205 | ❌ Delete | Cloud API, not Upstash | Delete |
| `protocol.py` | 759 | ❌ Delete | Moved to shared-py | Delete |
| `file_fallback.py` | 615 | ❌ Delete | Replaced by native | Delete |
| `metrics.py` | 559 | ❌ Delete | Moved to shared-py | Delete |
| `stream_manager.py` | 515 | ❌ Delete | Generic, not Upstash | Delete |
| `insight_embedder.py` | 463 | ❌ Delete | Cloud API, not Upstash | Delete |
| `async_support.py` | 493 | ❌ Delete | Moved to shared-py | Delete |
| `logger.py` | 429 | ❌ Delete | Moved to shared-py | Delete |
| `pattern_client.py` | 351 | ❌ Delete | Cloud API, not Upstash | Delete |
| `consensus/coordinator.py` | 1,280 | ❌ Delete | Experimental, unused | Delete |
| `consensus/protocol.py` | 905 | ❌ Delete | Experimental, unused | Delete |
| `consensus/triggers.py` | 791 | ❌ Delete | Experimental, unused | Delete |
| `consensus/monitor.py` | 641 | ❌ Delete | Experimental, unused | Delete |
| `consensus/agent_hook.py` | 587 | ❌ Delete | Experimental, unused | Delete |
| `consensus/config.json` | 207 | ❌ Delete | Experimental, unused | Delete |
| `consensus/__init__.py` | 150 | ❌ Delete | Experimental, unused | Delete |
| `consensus/README.md` | 494 | ❌ Delete | Experimental, unused | Delete |

**Total Files**: 38
**Files to Keep**: 6 (after editing)
**Files to Archive**: 6
**Files to Delete**: 26

---

**Document Status**: Ready for Review
**Next Action**: Extract examples from `example_usage.py` and rewrite `README.md`
**Estimated Effort**: 2-3 hours for full implementation
**Risk Level**: Low (all changes reversible via git, tests archived)

---

**References**:
- Audit: `docs/assessments/2025-12-29-power-mode-upstash-audit.md`
- Epic: #580 Plugin Modularization
- Current structure: `packages/popkit-core/power-mode/`
- Archive target: `packages/benchmarks/power-mode/`
