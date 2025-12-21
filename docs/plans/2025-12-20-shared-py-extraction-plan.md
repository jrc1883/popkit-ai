# @popkit/shared-py Package Extraction - Implementation Plan

> **For Claude:** Use executing-plans skill to implement this plan task-by-task.

**Goal:** Extract 69 utility modules from the monolithic PopKit plugin into a standalone `popkit-shared` Python package that all 6 modular plugins will depend on.

**Architecture:** Create a standard Python package structure at `packages/shared-py/` with proper `pyproject.toml`, extract all utilities while preserving their functionality, update all imports in the monolithic plugin, test thoroughly, and publish to PyPI test registry.

**Tech Stack:** Python 3.8+, Poetry (package management), PyPI (distribution)

**Related:** Issue #570, Epic #580 Phase 1, Design Doc: `docs/plans/2025-12-20-plugin-modularization-design.md`

---

## Task 1: Create Package Structure

**Files:**
- Create: `packages/shared-py/pyproject.toml`
- Create: `packages/shared-py/README.md`
- Create: `packages/shared-py/popkit_shared/__init__.py`
- Create: `packages/shared-py/popkit_shared/utils/__init__.py`

**Step 1: Create directory structure**

```bash
mkdir -p packages/shared-py/popkit_shared/utils
mkdir -p packages/shared-py/tests
```

**Step 2: Create pyproject.toml**

```toml
[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.poetry]
name = "popkit-shared"
version = "0.1.0"
description = "Shared utilities for PopKit plugin ecosystem"
authors = ["Joseph Cannon <joseph@thehouseofdeals.com>"]
license = "MIT"
readme = "README.md"
packages = [{include = "popkit_shared"}]

[tool.poetry.dependencies]
python = "^3.8"
pyyaml = "^6.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.0"
pytest-cov = "^4.0"
```

**Step 3: Create README.md**

```markdown
# popkit-shared

Shared utilities for the PopKit plugin ecosystem.

## Installation

```bash
pip install popkit-shared
```

## Usage

```python
from popkit_shared.utils.context_carrier import HookContext
from popkit_shared.utils.message_builder import build_message
```

## Modules

This package contains 69 utility modules organized into:
- Core infrastructure (23 modules)
- Routing & discovery (9 modules)
- State management (8 modules)
- Cloud integration (6 modules)
- Tool intelligence (6 modules)
- Testing & validation (5 modules)
- Monitoring & metrics (5 modules)
- Specialized utilities (7 modules)

## License

MIT
```

**Step 4: Create package __init__.py**

```python
"""
PopKit Shared Utilities

Shared utilities for PopKit plugin ecosystem.
Version: 0.1.0
"""

__version__ = "0.1.0"

# Re-export commonly used utilities
from .utils import *
```

**Step 5: Create utils __init__.py**

```python
"""
PopKit Shared Utils Package

All utility modules from the monolithic plugin.
"""

# Import commonly used utilities
from .context_carrier import HookContext
from .message_builder import build_message
from .stateless_hook import StatelessHook

__all__ = [
    'HookContext',
    'build_message',
    'StatelessHook',
]
```

**Step 6: Verify directory structure**

Run: `tree packages/shared-py -L 3`

Expected:
```
packages/shared-py/
├── README.md
├── pyproject.toml
├── popkit_shared/
│   ├── __init__.py
│   └── utils/
│       └── __init__.py
└── tests/
```

**Step 7: Commit**

```bash
git add packages/shared-py/
git commit -m "feat(shared-py): create package structure for utility extraction

- Add pyproject.toml with Poetry configuration
- Add README with package documentation
- Create popkit_shared package structure
- Set up utils subpackage for 69 modules

Part of Issue #570 (Epic #580 Phase 1)"
```

---

## Task 2: Copy All 69 Utility Modules

**Files:**
- Copy: `packages/plugin/hooks/utils/*.py` → `packages/shared-py/popkit_shared/utils/`

**Step 1: Copy all utility files**

```bash
cp packages/plugin/hooks/utils/*.py packages/shared-py/popkit_shared/utils/
```

**Step 2: Verify file count**

Run: `ls packages/shared-py/popkit_shared/utils/*.py | wc -l`

Expected: 69 files

**Step 3: List copied files for verification**

Run: `ls packages/shared-py/popkit_shared/utils/*.py | head -20`

Expected: Files like agent_loader.py, context_carrier.py, message_builder.py, etc.

**Step 4: Commit**

```bash
git add packages/shared-py/popkit_shared/utils/
git commit -m "feat(shared-py): copy 69 utility modules from monolithic plugin

Copied all utilities from packages/plugin/hooks/utils/ to shared package.
Next step: Fix imports to remove 'hooks.utils' references.

Part of Issue #570 (Epic #580 Phase 1)"
```

---

## Task 3: Fix Internal Imports in Copied Modules (Batch 1: Core Infrastructure - 23 files)

**Files:**
- Modify: All files in `packages/shared-py/popkit_shared/utils/`

**Note:** Internal imports need to change from `from hooks.utils.X import Y` to `from popkit_shared.utils.X import Y` or `from .X import Y` (relative imports).

**Step 1: Identify files with internal imports**

Run: `grep -l "from hooks.utils" packages/shared-py/popkit_shared/utils/*.py | wc -l`

Expected: Multiple files

**Step 2: Fix imports using find-and-replace**

Run the following for all files:
```bash
cd packages/shared-py/popkit_shared/utils/
for file in *.py; do
    sed -i 's/from hooks\.utils\./from popkit_shared.utils./g' "$file"
    sed -i 's/import hooks\.utils\./import popkit_shared.utils./g' "$file"
done
```

**Step 3: Verify no 'hooks.utils' references remain**

Run: `grep -r "from hooks.utils" packages/shared-py/popkit_shared/utils/`

Expected: No output (all references removed)

**Step 4: Commit**

```bash
git add packages/shared-py/popkit_shared/utils/
git commit -m "fix(shared-py): update internal imports to use popkit_shared

Changed all 'from hooks.utils' imports to 'from popkit_shared.utils'.
All 69 modules now have correct package-relative imports.

Part of Issue #570 (Epic #580 Phase 1)"
```

---

## Task 4: Update Monolithic Plugin Imports (Batch 1: Hook Files)

**Files:**
- Modify: `packages/plugin/hooks/*.py` (all hook files)

**Step 1: List hook files that import from utils**

Run: `grep -l "from hooks.utils" packages/plugin/hooks/*.py`

Expected: Files like pre-tool-use.py, post-tool-use.py, session-start.py, etc.

**Step 2: Count imports to update**

Run: `grep "from hooks.utils" packages/plugin/hooks/*.py | wc -l`

Expected: Multiple import statements

**Step 3: Update imports in hook files**

For each hook file, change:
- OLD: `from hooks.utils.context_carrier import HookContext`
- NEW: `from popkit_shared.utils.context_carrier import HookContext`

Run:
```bash
cd packages/plugin/hooks/
for file in *.py; do
    sed -i 's/from hooks\.utils\./from popkit_shared.utils./g' "$file"
done
```

**Step 4: Verify no old imports remain in hooks/**

Run: `grep "from hooks.utils" packages/plugin/hooks/*.py`

Expected: No output

**Step 5: Commit**

```bash
git add packages/plugin/hooks/
git commit -m "refactor(plugin): update hook imports to use popkit_shared package

Changed all hook files to import from popkit_shared.utils instead of hooks.utils.
Hooks now depend on the extracted shared package.

Part of Issue #570 (Epic #580 Phase 1)"
```

---

## Task 5: Update Monolithic Plugin Imports (Batch 2: Skill Scripts)

**Files:**
- Modify: `packages/plugin/skills/*/scripts/*.py` (all skill scripts)

**Step 1: Find skill scripts with utils imports**

Run: `find packages/plugin/skills/ -name "*.py" -exec grep -l "from hooks.utils\|import hooks.utils" {} \; | head -20`

Expected: Multiple skill script files

**Step 2: Count files to update**

Run: `find packages/plugin/skills/ -name "*.py" -exec grep -l "from hooks.utils" {} \; | wc -l`

Expected: Number of skill scripts using utils

**Step 3: Update imports in all skill scripts**

```bash
find packages/plugin/skills/ -name "*.py" -exec sed -i 's/from hooks\.utils\./from popkit_shared.utils./g' {} \;
find packages/plugin/skills/ -name "*.py" -exec sed -i 's/import hooks\.utils\./import popkit_shared.utils./g' {} \;
```

**Step 4: Verify updates**

Run: `find packages/plugin/skills/ -name "*.py" -exec grep "from hooks.utils" {} \;`

Expected: No output

**Step 5: Commit**

```bash
git add packages/plugin/skills/
git commit -m "refactor(plugin): update skill script imports to use popkit_shared

Changed all skill scripts to import from popkit_shared.utils.
Skills now depend on the extracted shared package.

Part of Issue #570 (Epic #580 Phase 1)"
```

---

## Task 6: Update Monolithic Plugin Imports (Batch 3: Power Mode)

**Files:**
- Modify: `packages/plugin/power-mode/*.py`

**Step 1: Check power-mode imports**

Run: `grep -r "from hooks.utils" packages/plugin/power-mode/`

Expected: Import statements if any exist

**Step 2: Update imports**

```bash
cd packages/plugin/power-mode/
for file in *.py; do
    sed -i 's/from hooks\.utils\./from popkit_shared.utils./g' "$file"
done
```

**Step 3: Verify**

Run: `grep "from hooks.utils" packages/plugin/power-mode/*.py`

Expected: No output

**Step 4: Commit**

```bash
git add packages/plugin/power-mode/
git commit -m "refactor(plugin): update Power Mode imports to use popkit_shared

Changed power-mode coordination to import from popkit_shared.utils.

Part of Issue #570 (Epic #580 Phase 1)"
```

---

## Task 7: Update Monolithic Plugin Imports (Batch 4: Scripts)

**Files:**
- Modify: `packages/plugin/scripts/*.py`

**Step 1: Check script imports**

Run: `grep -r "from hooks.utils" packages/plugin/scripts/`

Expected: Import statements if any exist

**Step 2: Update imports**

```bash
cd packages/plugin/scripts/
for file in *.py; do
    sed -i 's/from hooks\.utils\./from popkit_shared.utils./g' "$file"
done
```

**Step 3: Verify**

Run: `grep "from hooks.utils" packages/plugin/scripts/*.py`

Expected: No output

**Step 4: Commit**

```bash
git add packages/plugin/scripts/
git commit -m "refactor(plugin): update scripts imports to use popkit_shared

Changed all utility scripts to import from popkit_shared.utils.

Part of Issue #570 (Epic #580 Phase 1)"
```

---

## Task 8: Update Monolithic Plugin Dependencies

**Files:**
- Create: `packages/plugin/requirements.txt` (if doesn't exist)
- Modify: `packages/plugin/requirements.txt` or add dependency reference

**Step 1: Check if requirements.txt exists**

Run: `test -f packages/plugin/requirements.txt && echo "exists" || echo "missing"`

**Step 2: Add popkit-shared dependency**

If file exists, add to it. If not, create it:

```txt
# PopKit Plugin Dependencies
popkit-shared>=0.1.0
```

**Step 3: Commit**

```bash
git add packages/plugin/requirements.txt
git commit -m "feat(plugin): add popkit-shared package dependency

Monolithic plugin now depends on extracted shared package.
All utilities are imported from popkit_shared.utils.

Part of Issue #570 (Epic #580 Phase 1)"
```

---

## Task 9: Install Shared Package Locally for Testing

**Files:**
- N/A (installation task)

**Step 1: Install in development mode**

```bash
cd packages/shared-py
poetry install
```

Expected: Package installs successfully with all dependencies

**Step 2: Verify installation**

```bash
python -c "from popkit_shared.utils.context_carrier import HookContext; print('Import successful')"
```

Expected: "Import successful"

**Step 3: Run Python tests if any exist**

```bash
cd packages/shared-py
poetry run pytest -v
```

Expected: Tests pass or "no tests ran" if none exist yet

**Step 4: Document installation**

No commit needed - this is a verification step.

---

## Task 10: Test Monolithic Plugin After Extraction

**Files:**
- N/A (testing task)

**Step 1: Run plugin self-tests**

```bash
# Assuming there's a test command
cd packages/plugin
python -m pytest tests/ -v
```

Expected: All tests pass

**Step 2: Test a sample hook manually**

```bash
# Test that imports work
python -c "import sys; sys.path.insert(0, 'packages/plugin/hooks'); from pre_tool_use import *; print('Hook imports successful')"
```

Expected: No import errors

**Step 3: Test a sample skill script**

```bash
# Pick a skill with a script
cd packages/plugin/skills/pop-brainstorming/scripts/
python -c "import main; print('Skill script imports successful')"
```

Expected: No import errors

**Step 4: Document test results**

Create a test report if needed, but main validation is "no errors".

---

## Task 11: Update Shared Package __init__.py with All Exports

**Files:**
- Modify: `packages/shared-py/popkit_shared/utils/__init__.py`

**Step 1: Generate list of all modules**

```bash
cd packages/shared-py/popkit_shared/utils/
ls *.py | grep -v "__init__.py" | sed 's/\.py$//' | sort
```

**Step 2: Update __init__.py to export all utilities**

```python
"""
PopKit Shared Utils Package

All 69 utility modules extracted from monolithic plugin.
"""

# Core Infrastructure (23 modules)
from .context_carrier import HookContext
from .message_builder import build_message
from .stateless_hook import StatelessHook
from .safe_json import safe_load, safe_dump
from .version import get_current_version, check_for_updates
# ... (import from all 69 modules)

__all__ = [
    # Core Infrastructure
    'HookContext',
    'build_message',
    'StatelessHook',
    # ... (export all imports)
]
```

**Step 3: Verify no import errors**

```bash
cd packages/shared-py
poetry run python -c "from popkit_shared.utils import *; print('All imports successful')"
```

Expected: "All imports successful"

**Step 4: Commit**

```bash
git add packages/shared-py/popkit_shared/utils/__init__.py
git commit -m "feat(shared-py): export all 69 utility modules in __init__.py

Added re-exports for all utilities to simplify imports.
Users can now: from popkit_shared.utils import HookContext

Part of Issue #570 (Epic #580 Phase 1)"
```

---

## Task 12: Create Basic Tests for Shared Package

**Files:**
- Create: `packages/shared-py/tests/test_imports.py`
- Create: `packages/shared-py/tests/test_version.py`

**Step 1: Create import test**

```python
"""Test that all modules can be imported."""

def test_import_context_carrier():
    from popkit_shared.utils.context_carrier import HookContext
    assert HookContext is not None

def test_import_message_builder():
    from popkit_shared.utils.message_builder import build_message
    assert build_message is not None

def test_import_stateless_hook():
    from popkit_shared.utils.stateless_hook import StatelessHook
    assert StatelessHook is not None

# Add tests for other critical imports
```

**Step 2: Create version test**

```python
"""Test package version."""

from popkit_shared import __version__

def test_version_exists():
    assert __version__ is not None

def test_version_format():
    # Should be semver format
    parts = __version__.split('.')
    assert len(parts) == 3
```

**Step 3: Run tests**

```bash
cd packages/shared-py
poetry run pytest tests/ -v
```

Expected: All tests pass

**Step 4: Commit**

```bash
git add packages/shared-py/tests/
git commit -m "test(shared-py): add basic import and version tests

Verify all critical modules can be imported.
Verify package version is set correctly.

Part of Issue #570 (Epic #580 Phase 1)"
```

---

## Task 13: Build and Verify Package Distribution

**Files:**
- Create: `packages/shared-py/dist/*.whl`
- Create: `packages/shared-py/dist/*.tar.gz`

**Step 1: Build distribution packages**

```bash
cd packages/shared-py
poetry build
```

Expected: Creates .whl and .tar.gz in dist/

**Step 2: Verify package contents**

```bash
tar -tzf dist/popkit_shared-0.1.0.tar.gz | head -20
```

Expected: Lists package files

**Step 3: Test installation from built package**

```bash
pip install dist/popkit_shared-0.1.0-py3-none-any.whl
python -c "from popkit_shared import __version__; print(__version__)"
```

Expected: Prints "0.1.0"

**Step 4: Document build**

No commit needed - dist/ should be in .gitignore

---

## Task 14: Publish to PyPI Test Registry

**Files:**
- N/A (publishing task)

**Step 1: Configure PyPI Test credentials**

```bash
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry config pypi-token.testpypi <TOKEN>
```

**Step 2: Publish to Test PyPI**

```bash
cd packages/shared-py
poetry publish -r testpypi
```

Expected: Package uploaded successfully

**Step 3: Test installation from Test PyPI**

```bash
pip install --index-url https://test.pypi.org/simple/ popkit-shared
python -c "from popkit_shared import __version__; print(__version__)"
```

Expected: Installs and prints "0.1.0"

**Step 4: Document publication**

Add note to Issue #570 with Test PyPI link.

---

## Task 15: Update Documentation

**Files:**
- Create: `packages/shared-py/CHANGELOG.md`
- Modify: `packages/plugin/README.md` (if exists)
- Create: `packages/shared-py/docs/MIGRATION.md`

**Step 1: Create CHANGELOG**

```markdown
# Changelog

## [0.1.0] - 2025-12-20

### Added
- Initial release of popkit-shared package
- Extracted 69 utility modules from monolithic PopKit plugin
- Core infrastructure utilities (23 modules)
- Routing & discovery utilities (9 modules)
- State management utilities (8 modules)
- Cloud integration utilities (6 modules)
- Tool intelligence utilities (6 modules)
- Testing & validation utilities (5 modules)
- Monitoring & metrics utilities (5 modules)
- Specialized utilities (7 modules)

### Changed
- All imports updated from `hooks.utils` to `popkit_shared.utils`
```

**Step 2: Create migration guide**

```markdown
# Migration Guide: hooks.utils → popkit_shared

## For Plugin Developers

If you're updating code that used the old monolithic plugin:

### Before
```python
from hooks.utils.context_carrier import HookContext
from hooks.utils.message_builder import build_message
```

### After
```python
from popkit_shared.utils.context_carrier import HookContext
from popkit_shared.utils.message_builder import build_message
```

## Installation

```bash
pip install popkit-shared
```

## Available Modules

See README.md for full list of 69 utility modules.
```

**Step 3: Commit**

```bash
git add packages/shared-py/CHANGELOG.md packages/shared-py/docs/
git commit -m "docs(shared-py): add changelog and migration guide

Document initial release and provide migration instructions.

Part of Issue #570 (Epic #580 Phase 1)"
```

---

## Task 16: Final Integration Testing

**Files:**
- N/A (testing task)

**Step 1: Test full workflow with monolithic plugin**

```bash
# Test a full workflow that uses multiple utilities
# E.g., run a hook that uses context_carrier, message_builder, etc.
```

Expected: Workflow completes without errors

**Step 2: Verify no remaining 'hooks.utils' imports**

```bash
grep -r "from hooks.utils" packages/plugin/ --include="*.py" | grep -v "shared-py"
```

Expected: No output (all imports updated)

**Step 3: Run comprehensive tests**

```bash
# Run all available tests
cd packages/plugin
pytest tests/ -v --tb=short
```

Expected: All tests pass

**Step 4: Update Issue #570**

Add comment with completion status and test results.

---

## Success Criteria

- [ ] Package structure created at `packages/shared-py/`
- [ ] All 69 modules copied and imports fixed
- [ ] `pyproject.toml` created with Poetry configuration
- [ ] Package installable via `pip install popkit-shared`
- [ ] All imports updated in monolithic plugin
- [ ] No functionality regression (tests pass)
- [ ] Package published to PyPI test registry
- [ ] Documentation created (README, CHANGELOG, migration guide)
- [ ] Issue #570 marked as complete

## Post-Completion

After all tasks complete:

1. Update Epic #580 with Phase 1 completion
2. Begin Phase 2: Extract popkit-dev plugin (Issue #571)
3. All future plugins will depend on popkit-shared package
