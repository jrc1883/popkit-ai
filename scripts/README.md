# PopKit Development Scripts

This directory contains utility scripts for PopKit development.

## Available Scripts

### `fix-shared-imports.py`

Fixes import statements in the shared Python utilities package to use relative imports.

```bash
# Run from repository root
python scripts/fix-shared-imports.py
```

**Use case:** After adding new modules to `packages/shared-py/popkit_shared/utils/`, this script ensures all internal imports use the correct relative import syntax.

### `validate-orchestration.py`

Validates the PopKit plugin structure and orchestration setup.

```bash
# Run from repository root
python scripts/validate-orchestration.py
```

**What it checks:**
- Modular plugin hooks are present
- Shared Python package is installable
- Plugin dependencies are correctly declared
- Skills are properly distributed

**Use case:** Run after making structural changes to verify the plugin architecture is intact.

## Prerequisites

Both scripts require Python 3.7+:

```bash
# Install shared Python package for validation script
pip install -e packages/shared-py
```

## License

MIT - Same as PopKit project
