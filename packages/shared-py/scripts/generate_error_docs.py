#!/usr/bin/env python3
"""Generate error documentation from ErrorRegistry."""

import sys
from pathlib import Path

# Add parent directory to path to import popkit_shared
sys.path.insert(0, str(Path(__file__).parent.parent))

from popkit_shared.utils.error_codes import ErrorRegistry, ErrorSeverity


def generate_error_doc(error_code, output_dir):
    """Generate markdown doc for an error code."""
    doc_path = output_dir / f"{error_code.code}.md"

    # Determine blocking status
    blocking_status = (
        "Blocking"
        if error_code.severity.value in ["critical", "high"]
        else "Non-blocking"
    )

    # Format recovery steps
    recovery_steps = "\n".join(
        f"{i+1}. **{step.split(':')[0] if ':' in step else 'Step ' + str(i+1)}**\n   - {step}"
        for i, step in enumerate(error_code.recovery)
    )

    template = f"""# {error_code.code} - {error_code.message}

**Category:** {error_code.category}
**Severity:** {error_code.severity.value.title()}
**Status:** {blocking_status}

## Description

{error_code.message}

This error occurs in the **{error_code.category}** category and indicates a {error_code.severity.value} severity issue.

## Common Causes

1. [Add common cause 1]
2. [Add common cause 2]
3. [Add common cause 3]

## Resolution Steps

{recovery_steps}

## Prevention

- [Add prevention tip 1]
- [Add prevention tip 2]
- [Add prevention tip 3]

## Related Errors

- [Add related error code 1]
- [Add related error code 2]

## References

- [PopKit Documentation](https://github.com/jrc1883/popkit-claude)
- [Error Code System (Issue #104)](https://github.com/jrc1883/popkit-claude/issues/104)
"""

    doc_path.write_text(template, encoding="utf-8")
    return doc_path


def main():
    # Get output directory (docs/errors/)
    repo_root = Path(__file__).parent.parent.parent.parent
    output_dir = repo_root / "docs" / "errors"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating error documentation in: {output_dir}")
    print()

    # Get all error codes
    errors = ErrorRegistry.all_errors()
    print(f"Found {len(errors)} error codes to document")
    print()

    # Generate documentation for each error
    for error_code in errors:
        doc_path = generate_error_doc(error_code, output_dir)
        print(f"[OK] Created: {doc_path.name}")

    print()
    print(f"[OK] Generated {len(errors)} error documentation files")
    print(f"[OK] Location: {output_dir}")


if __name__ == "__main__":
    main()
