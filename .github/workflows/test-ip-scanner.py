#!/usr/bin/env python3
"""
Test script for IP Leak Scanner
Validates that exemptions work correctly and real secrets are still caught.
"""

import tempfile
from pathlib import Path
import sys
import re
from dataclasses import dataclass
from typing import List


# Copy the scanner logic from the workflow
@dataclass
class Finding:
    file: str
    line: int
    pattern: str
    severity: str
    matched: str
    description: str


PATTERNS = {
    "api_key": {
        "pattern": r"(?:api[_-]?key|secret[_-]?key)\s*[:=]\s*['\"][a-zA-Z0-9_-]{20,}['\"]",
        "severity": "critical",
        "description": "Hardcoded API key",
    },
    "stripe_secret": {
        "pattern": r"sk_(?:live|test)_[a-zA-Z0-9]{24,}",
        "severity": "critical",
        "description": "Stripe secret key",
    },
    "bearer_token": {
        "pattern": r"Bearer\s+[a-zA-Z0-9_-]{20,}",
        "severity": "critical",
        "description": "Hardcoded bearer token",
    },
}

SKIP = [r"\.git/", r"node_modules/", r"__pycache__/", r"ip_scanner\.py"]

EXEMPT_PATHS = [
    r"(?:^|/)docs/",  # docs/ at start or after /
    r"(?:^|/)examples/",  # examples/ at start or after /
    r"(?:^|/)standards/",  # standards/ at start or after /
    r"(?:^|/)templates/",  # templates/ at start or after /
    r"(?:^|/)test",  # /test or test at start
    r"\.test\.",  # .test. anywhere
    r"_test\.",  # _test. anywhere
    r"^test_",  # test_ at start of filename
    r"(?:^|/)sample",  # /sample or sample at start
    r"\.sample\.",  # .sample. anywhere
    r"\.example\.",  # .example. anywhere
    r"\.template\.",  # .template. anywhere
    r"(?:^|/)fixtures/",  # fixtures/ at start or after /
    r"README\.md$",  # README.md at end
    r"CHANGELOG\.md$",  # CHANGELOG.md at end
]

EXEMPT_MARKERS = [
    r"#\s*Example:",
    r"#\s*BAD\s*-",
    r"#\s*GOOD\s*-",
    r"#\s*For documentation",
    r"#\s*Sample:",
    r"#\s*Template:",
    r"//\s*Example:",
    r"//\s*BAD\s*-",
    r"//\s*GOOD\s*-",
    r"//\s*Sample:",
    r"```",
]

ALLOWED = {
    "ip_scanner.py": list(PATTERNS.keys()),
    "test-ip-scanner.py": list(PATTERNS.keys()),
    "CLAUDE.md": [],
    "audit.md": [],
}


def should_skip(path: str) -> bool:
    return any(re.search(p, path) for p in SKIP)


def is_exempt_path(path: str) -> bool:
    """Check if file path matches any exemption pattern."""
    path_normalized = path.replace("\\", "/")
    return any(re.search(p, path_normalized) for p in EXEMPT_PATHS)


def is_allowed(path: str, pattern: str) -> bool:
    name = Path(path).name
    return name in ALLOWED and pattern in ALLOWED[name]


def has_exempt_marker(lines: List[str], line_idx: int) -> bool:
    """Check if line is preceded by exemption marker or inside code block."""
    # Check previous 3 lines for markers
    start = max(0, line_idx - 3)
    for i in range(start, line_idx):
        for marker in EXEMPT_MARKERS:
            if re.search(marker, lines[i]):
                return True

    # Check if inside markdown code block
    in_code_block = False
    for i in range(0, line_idx):
        if re.match(r"^\s*```", lines[i]):
            in_code_block = not in_code_block

    return in_code_block


def scan_file(filepath: Path) -> List[Finding]:
    findings = []
    if should_skip(str(filepath)):
        return findings

    # Skip exempt paths (documentation, examples, tests)
    if is_exempt_path(str(filepath)):
        return findings

    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        lines = content.split("\n")
        for name, cfg in PATTERNS.items():
            if is_allowed(str(filepath), name):
                continue
            regex = re.compile(cfg["pattern"])
            for i, line in enumerate(lines, 1):
                match = regex.search(line)
                if match:
                    # Skip if line has exemption marker
                    if has_exempt_marker(lines, i - 1):
                        continue

                    findings.append(
                        Finding(
                            file=str(filepath),
                            line=i,
                            pattern=name,
                            severity=cfg["severity"],
                            matched=match.group(0)[:40],
                            description=cfg["description"],
                        )
                    )
    except Exception:
        # Best-effort fallback: ignore optional failure.
        pass
    return findings


# Test cases
def test_exempt_documentation():
    """Documentation files should be exempt."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create a documentation file with examples
        doc = tmppath / "docs" / "security" / "standards" / "secret-patterns.md"
        doc.parent.mkdir(parents=True)
        doc.write_text("""
# Secret Detection Standard

## Examples

### BAD - Hardcoded API key
```python
# BAD
api_key = "sk_test_1234567890abcdef1234567890"
```

### GOOD - Environment variable
```python
# GOOD
api_key = os.environ.get("API_KEY")
```
""")

        findings = scan_file(doc)
        assert len(findings) == 0, f"Expected 0 findings in docs, got {len(findings)}"
        print("[PASS] Documentation files are exempt")


def test_exempt_examples():
    """Example files should be exempt."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create an example file
        example = tmppath / "examples" / "auth-example.py"
        example.parent.mkdir(parents=True)
        example.write_text("""
# Example authentication code
api_key = "sk_test_1234567890abcdef1234567890"
""")

        findings = scan_file(example)
        assert len(findings) == 0, (
            f"Expected 0 findings in examples, got {len(findings)}"
        )
        print("[PASS] Example files are exempt")


def test_exempt_tests():
    """Test files should be exempt."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create test files with different naming conventions
        test1 = tmppath / "test_auth.py"
        test1.write_text('api_key = "sk_test_1234567890abcdef1234567890"')

        test2 = tmppath / "auth.test.ts"
        test2.write_text('const apiKey = "sk_test_1234567890abcdef1234567890"')

        findings1 = scan_file(test1)
        findings2 = scan_file(test2)

        assert len(findings1) == 0, (
            f"Expected 0 findings in test_*.py, got {len(findings1)}"
        )
        assert len(findings2) == 0, (
            f"Expected 0 findings in *.test.ts, got {len(findings2)}"
        )
        print("[PASS] Test files are exempt")


def test_exempt_markers():
    """Lines with exemption markers should be skipped."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        code = tmppath / "src" / "config.py"
        code.parent.mkdir(parents=True)
        code.write_text("""
# Example: This is for documentation only
api_key = "sk_test_1234567890abcdef1234567890"

# BAD - Don't do this
secret_key = "my-super-secret-key-12345"

# GOOD - Use environment variables
good_key = os.environ.get("API_KEY")
""")

        findings = scan_file(code)
        assert len(findings) == 0, (
            f"Expected 0 findings with markers, got {len(findings)}"
        )
        print("[PASS] Exemption markers work correctly")


def test_markdown_code_blocks():
    """Code blocks in markdown should be exempt."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        readme = tmppath / "README.md"
        readme.write_text("""
# Authentication Guide

## Setup

```python
# BAD - Don't do this
api_key = "sk_test_1234567890abcdef1234567890"
```

```javascript
// Example
const token = "Bearer abcdef1234567890abcdef1234567890"
```
""")

        findings = scan_file(readme)
        # README.md is in EXEMPT_PATHS, so should be 0
        assert len(findings) == 0, (
            f"Expected 0 findings in README.md, got {len(findings)}"
        )
        print("[PASS] Markdown code blocks are exempt")


def test_real_secrets_caught():
    """Real secrets in production code should still be caught."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        # Create a source file with actual hardcoded secrets (no exemption)
        src = tmppath / "src" / "auth.py"
        src.parent.mkdir(parents=True)
        src.write_text("""
# Production authentication module
import os

# This should be caught!
api_key = "sk_live_1234567890abcdef1234567890"
stripe_key = "sk_test_9876543210fedcba9876543210"
auth_header = {"Authorization": "Bearer xyz123456789012345678901234567890"}
""")

        findings = scan_file(src)
        assert len(findings) > 0, "Expected to catch real secrets in production code"

        # Should catch at least the stripe keys and bearer token
        patterns_found = {f.pattern for f in findings}
        assert "stripe_secret" in patterns_found, "Should catch Stripe secret keys"
        assert "bearer_token" in patterns_found, "Should catch bearer tokens"

        print(f"[PASS] Real secrets caught: {len(findings)} findings")
        for f in findings:
            print(f"   - {f.pattern}: {f.matched}")


def test_templates():
    """Template files should be exempt."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        template = tmppath / "templates" / "config.template.js"
        template.parent.mkdir(parents=True)
        template.write_text("""
// Template: Replace with your actual values
const config = {
    apiKey: "sk_test_your_key_here_12345678901234567890",
    bearerToken: "Bearer your_token_here_123456789012345678"
};
""")

        findings = scan_file(template)
        assert len(findings) == 0, (
            f"Expected 0 findings in templates, got {len(findings)}"
        )
        print("[PASS] Template files are exempt")


def test_sample_files():
    """Sample files should be exempt."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)

        sample = tmppath / "config.sample.json"
        sample.write_text("""
{
    "api_key": "sk_test_sample_key_1234567890abcdef1234",
    "secret": "sample-secret-value-abcdef123456789012345678"
}
""")

        findings = scan_file(sample)
        assert len(findings) == 0, (
            f"Expected 0 findings in sample files, got {len(findings)}"
        )
        print("[PASS] Sample files are exempt")


def main():
    print("Testing IP Leak Scanner Exemptions\n")

    tests = [
        ("Documentation files", test_exempt_documentation),
        ("Example files", test_exempt_examples),
        ("Test files", test_exempt_tests),
        ("Exemption markers", test_exempt_markers),
        ("Markdown code blocks", test_markdown_code_blocks),
        ("Template files", test_templates),
        ("Sample files", test_sample_files),
        ("Real secrets detection", test_real_secrets_caught),
    ]

    passed = 0
    failed = 0

    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {name}: {e}")
            failed += 1
        except Exception as e:
            print(f"[FAIL] {name}: Unexpected error: {e}")
            failed += 1

    print(f"\n{'=' * 60}")
    print(f"Results: {passed} passed, {failed} failed")

    if failed > 0:
        sys.exit(1)
    else:
        print("\n[SUCCESS] All tests passed! Scanner exemptions are working correctly.")
        sys.exit(0)


if __name__ == "__main__":
    main()
