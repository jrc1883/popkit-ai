# Issue #69 Implementation Fixes - Execution Plan

**Date**: 2026-02-02
**Status**: In Progress
**Related**: Issue #69, PR #226

## Problem Statement

The initial implementation of generic workspace routine templates has several critical gaps:

1. **Duplicate Logic**: `morning_workflow.py` overwrites generic dependency state with hardcoded pnpm logic
2. **No Caching**: Expensive project detection runs on every routine execution
3. **No Error Handling**: `TechStackDetector.detect_all()` can crash the routine
4. **Generic Services**: Expected services are hardcoded per language, not per-project
5. **No Integration**: Not part of PopKit initialization or project setup
6. **No Overrides**: Can't customize detected project configuration

## Solution Architecture

### 1. Project Configuration File: `.popkit/project.json`

```json
{
  "version": "1.0",
  "detected_at": "2026-02-02T13:00:00Z",
  "cache_ttl_hours": 24,
  "project_type": {
    "language": "TypeScript",
    "package_manager": "pnpm",
    "test_framework": "jest",
    "build_tool": "pnpm run build",
    "linter": "eslint",
    "formatter": "prettier"
  },
  "overrides": {
    "expected_services": [
      {"name": "dev server", "port": 4200, "description": "Angular dev server"},
      {"name": "api", "port": 3000, "description": "NestJS API"}
    ],
    "package_manager": "pnpm",
    "check_outdated": "pnpm outdated --format json"
  },
  "auto_detect": true
}
```

### 2. Smart Caching Strategy

```python
def get_project_type(project_path: Path, force_refresh: bool = False) -> ProjectType:
    """
    Get project type with smart caching.

    Flow:
    1. Check .popkit/project.json cache
    2. If cache valid and auto_detect=false, use cache
    3. If cache expired or force_refresh=true, re-detect
    4. If detection fails, fall back to cache
    5. If no cache, detect and create cache
    """
```

### 3. Error Handling Strategy

```python
try:
    project_type = detector.detect()
except Exception as e:
    logger.warning(f"Detection failed: {e}")
    # Try cache
    cached = load_cache()
    if cached:
        return cached
    # Fall back to basic detection
    return detect_fallback()
```

## Implementation Steps

### Phase 1: Core Infrastructure (30 min)

**Files to Create:**
- `packages/shared-py/popkit_shared/utils/project_config.py`

**Key Functions:**
- `load_project_config(project_path)` - Load from .popkit/project.json
- `save_project_config(config, project_path)` - Save to .popkit/project.json
- `get_cached_project_type(project_path)` - Get with cache validation
- `merge_overrides(detected, overrides)` - Apply user overrides

### Phase 2: Update Detection Logic (20 min)

**Files to Modify:**
- `packages/shared-py/popkit_shared/utils/generic_project_detector.py`

**Changes:**
- Add error handling to `detect()` method
- Add caching support via `project_config.py`
- Add `force_refresh` parameter

### Phase 3: Fix Morning Workflow (15 min)

**Files to Modify:**
- `packages/popkit-dev/skills/pop-morning/scripts/morning_workflow.py`

**Changes:**
- Remove hardcoded pnpm dependency check (lines 341-362)
- Trust generic_state_capture dependency state
- Keep morning-specific checks (PRs, issues, worktrees)

### Phase 4: Service Detection Enhancement (20 min)

**Changes:**
- Read expected_services from config overrides first
- Fall back to language defaults
- Add process detection as alternative (scan for dev server processes)

### Phase 5: Project Initialization (30 min)

**Files to Create:**
- `packages/popkit-dev/commands/project-configure.py`

**Features:**
- `/popkit:project init` - Initialize .popkit/project.json
- `/popkit:project configure` - Update overrides
- `/popkit:project detect` - Force re-detection

## Testing Plan

1. **Test Caching**:
   - Run morning routine twice, verify second is faster
   - Modify .popkit/project.json, verify overrides work
   - Delete cache, verify fresh detection works

2. **Test Error Handling**:
   - Corrupt config file, verify fallback works
   - Break tech_stack_detector, verify graceful degradation

3. **Test Override**:
   - Override expected_services, verify correct ports checked
   - Override package_manager, verify correct commands used

4. **Test Integration**:
   - Run on fresh project, verify .popkit/project.json created
   - Run on existing project, verify cache loaded

## Success Criteria

- [ ] Morning routine doesn't overwrite dependency state
- [ ] Second morning routine run is <5s faster (no detection)
- [ ] Config file created on first run
- [ ] Overrides work for expected_services and package_manager
- [ ] Routine gracefully handles detection failures
- [ ] Works on Python, Rust, Go projects (not just Node.js)

## Rollout Plan

1. Implement Phase 1-3 (core fixes)
2. Test with PopKit project
3. Implement Phase 4-5 (enhancements)
4. Update PR #226 with fixes
5. Document usage in SKILL.md files
