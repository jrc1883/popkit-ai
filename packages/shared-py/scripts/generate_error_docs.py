#!/usr/bin/env python3
"""Generate consolidated error documentation from ErrorRegistry."""

from __future__ import annotations

import sys
from pathlib import Path

# Add parent directory to path to import popkit_shared
sys.path.insert(0, str(Path(__file__).parent.parent))

from popkit_shared.utils.error_codes import ErrorRegistry


def generate_readme() -> str:
    """Build markdown for docs/errors/README.md."""
    errors = sorted(ErrorRegistry.all_errors(), key=lambda item: item.code)

    lines = [
        "# PopKit Error Codes",
        "",
        "This file is generated from `packages/shared-py/popkit_shared/utils/error_codes.py`.",
        "",
        "## Quick Reference",
        "",
        "| Code | Severity | Category | Message |",
        "| --- | --- | --- | --- |",
    ]

    for error in errors:
        lines.append(
            f"| `{error.code}` | {error.severity.value} | {error.category} | {error.message} |"
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "- `E`: blocking error",
            "- `W`: non-blocking warning",
            "- `S`: safety/security violation",
            "- `I`: informational status",
        ]
    )

    return "\n".join(lines) + "\n"


def main() -> None:
    repo_root = Path(__file__).parent.parent.parent.parent
    output_path = repo_root / "docs" / "errors" / "README.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(generate_readme(), encoding="utf-8")
    print(f"[OK] Wrote {output_path}")


if __name__ == "__main__":
    main()
