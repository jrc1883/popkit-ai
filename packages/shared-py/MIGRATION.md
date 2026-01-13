# Migration Guide: Shared Python Package Extraction

## Overview

All 69 utility modules have been successfully extracted from the monolithic PopKit plugin into a standalone `popkit-shared` package.

## What Changed

### Package Structure

**Before:**

```
packages/plugin/hooks/utils/
├── context_carrier.py
├── skill_context.py
├── voyage_client.py
└── ... (66 more modules)
```

**After:**

```
packages/shared-py/popkit_shared/utils/
├── context_carrier.py
├── skill_context.py
├── voyage_client.py
└── ... (66 more modules)
```

### Import Path Changes

**Old imports:**

```python
from hooks.utils.context_carrier import HookContext
from utils.skill_context import save_skill_context
```

**New imports:**

```python
from popkit_shared.utils.context_carrier import HookContext
from popkit_shared.utils.skill_context import save_skill_context
```

### Files Updated

1. **Hook Files** (4 files)
   - `command-learning-hook.py`
   - `post-tool-use.py`
   - `session-start.py`
   - `subagent-stop.py`

2. **Skill Documentation** (19 SKILL.md files)
   - Updated import examples in all skill documentation

3. **Power Mode** (3 files)
   - `checkin-hook.py`
   - `insight_embedder.py`
   - `statusline.py`
   - Removed sys.path manipulations

4. **Plugin Dependencies**
   - Added `popkit-shared>=0.1.0` to `requirements.txt`

## Installation

The shared package is installed in editable mode for development:

```bash
cd packages/shared-py
pip install -e .
```

## Verification

All imports have been verified to work correctly:

```python
# Core utilities
from popkit_shared.utils.context_carrier import HookContext
from popkit_shared.utils.skill_context import save_skill_context

# Message building
from popkit_shared.utils.message_builder import build_user_message

# Embeddings
from popkit_shared.utils.voyage_client import VoyageClient
```

## Module Categories

The 69 extracted modules are organized into 8 categories:

1. **Core Infrastructure** (23 modules)
   - context_carrier, message_builder, stateless_hook, etc.

2. **Routing & Discovery** (9 modules)
   - semantic_router, agent_loader, response_router, etc.

3. **State Management** (8 modules)
   - skill_context, context_storage, checkpoint, etc.

4. **Cloud Integration** (6 modules)
   - pattern_client, project_client, premium_client, etc.

5. **Tool Intelligence** (6 modules)
   - tool_filter, command_translator, mcp_detector, etc.

6. **Testing & Validation** (5 modules)
   - test_telemetry, bug_detector, security_scanner, etc.

7. **Monitoring & Metrics** (5 modules)
   - local_telemetry, upstash_telemetry, efficiency_tracker, etc.

8. **Specialized Utilities** (7 modules)
   - voyage*client, embedding*_, workflow\__, etc.

## Next Steps

1. ✅ Package structure created
2. ✅ All modules extracted
3. ✅ All imports updated
4. ✅ Package installed locally
5. ✅ Imports verified
6. ⏳ Publish to PyPI test registry (future)
7. ⏳ Update plugin installation to use published package (future)

## Breaking Changes

None - This is a transparent refactoring. All functionality remains the same, only import paths changed.

## Rollback Plan

If issues are discovered, the original utils modules still exist at `packages/plugin/hooks/utils/` and can be restored by reverting the import changes.

## Issues Addressed

- **Issue #570**: Extract shared foundation package (@popkit/shared-py)
- **Epic #580**: PopKit Plugin Modularization (Phase 1)
