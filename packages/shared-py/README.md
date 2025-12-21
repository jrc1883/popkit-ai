# PopKit Shared

Shared utilities for PopKit plugin ecosystem.

## Overview

This package contains 69 utility modules extracted from the monolithic PopKit plugin. All modular PopKit plugins depend on this shared foundation.

## Installation

```bash
pip install popkit-shared
```

## Usage

```python
from popkit_shared.utils.context_carrier import HookContext
from popkit_shared.utils.message_builder import MessageBuilder
from popkit_shared.utils.skill_context import save_skill_context
```

## Modules

See [docs/modules.md](docs/modules.md) for complete module listing.

## Development

```bash
# Install in development mode
poetry install

# Run tests
poetry run pytest
```

## License

MIT
