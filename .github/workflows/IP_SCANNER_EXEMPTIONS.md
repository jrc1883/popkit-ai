# IP Leak Scanner Exemptions Guide

This document explains how the IP Leak Scanner handles false positives through smart exemptions.

## Overview

The IP Leak Scanner prevents accidentally leaking proprietary code, credentials, and sensitive patterns to the public repository. However, documentation, examples, and test files often contain these patterns for legitimate educational purposes.

**Solution**: Smart exemptions based on file paths and content markers.

## Exemption Categories

### 1. Path-Based Exemptions

Files in these paths are **automatically exempt** from scanning:

| Path Pattern | Purpose | Examples |
|-------------|---------|----------|
| `/docs/` | Documentation files | `docs/security/auth-guide.md` |
| `/examples/` | Code examples | `examples/auth-example.py` |
| `/standards/` | Standards and patterns | `standards/secret-patterns.md` |
| `/templates/` | Template files | `templates/config.template.js` |
| `/test`, `*.test.*`, `test_*` | Test files | `test_auth.py`, `auth.test.ts` |
| `*.sample.*`, `*.example.*`, `*.template.*` | Sample/example files | `config.sample.json` |
| `/fixtures/` | Test fixtures | `fixtures/mock-data.json` |
| `README.md`, `CHANGELOG.md` | Project documentation | Any README or CHANGELOG |

**Implementation**:
```python
EXEMPT_PATHS = [
    r"/docs/",
    r"/examples/",
    r"/standards/",
    r"/templates/",
    r"/test",
    r"\.test\.",
    r"_test\.",
    r"/sample",
    r"\.sample\.",
    r"\.example\.",
    r"\.template\.",
    r"/fixtures/",
    r"README\.md$",
    r"CHANGELOG\.md$",
]
```

### 2. Content-Based Exemptions

Lines with these markers in the **previous 3 lines** are exempt:

| Marker | Purpose | Example |
|--------|---------|---------|
| `# Example:` | Python example code | See below |
| `# BAD -` | Anti-pattern example | See below |
| `# GOOD -` | Best practice example | See below |
| `# For documentation` | Documentation-only code | See below |
| `# Sample:` | Sample code | See below |
| `# Template:` | Template code | See below |
| `// Example:` | JavaScript/TypeScript example | See below |
| `// BAD -`, `// GOOD -` | JS anti-patterns/best practices | See below |
| ` ``` ` | Markdown code block | See below |

**Example Usage**:

```python
# Example: This demonstrates an anti-pattern
api_key = "sk_test_1234567890abcdef1234567890"  # ✅ Exempt (has "Example:" marker)

# BAD - Never hardcode API keys
secret_key = "my-super-secret-key-12345"  # ✅ Exempt (has "BAD -" marker)

# GOOD - Use environment variables
good_key = os.environ.get("API_KEY")  # ✅ Exempt (has "GOOD -" marker)

# Production code without markers
actual_key = "sk_live_real_key_here"  # ❌ Will be flagged!
```

**Markdown Code Blocks**:
```markdown
# Authentication Guide

## Setup

```python
# BAD - Don't do this
api_key = "sk_test_1234567890abcdef1234567890"  # ✅ Exempt (inside code block)
```

```javascript
const token = "Bearer abc123..."  # ✅ Exempt (inside code block)
```
```

### 3. Legacy File Exemptions

Specific files can be exempt for all patterns or specific patterns:

```python
ALLOWED = {
    "ip_scanner.py": ["all"],  # Scanner itself is exempt
    "CLAUDE.md": ["cloud_code", "cloud_billing"],  # Only specific patterns
    "audit.md": ["cloud_code", "cloud_billing"],
}
```

## How Exemptions Work

### Scanning Flow

```
1. File discovered
   ↓
2. Check SKIP patterns (git, node_modules) → Skip if matched
   ↓
3. Check EXEMPT_PATHS (docs, examples, tests) → Skip if matched
   ↓
4. Check ALLOWED (legacy exemptions) → Skip specific patterns
   ↓
5. Scan file line-by-line
   ↓
6. For each match:
   - Check EXEMPT_MARKERS in previous 3 lines → Skip if found
   - Check if inside markdown code block → Skip if true
   - Otherwise → Report as finding
```

### Code Block Detection

The scanner tracks markdown code blocks across the entire file:

```python
in_code_block = False
for i in range(0, line_idx):
    if re.match(r'^\s*```', lines[i]):
        in_code_block = not in_code_block
```

## Testing Exemptions

Run the test suite to verify exemptions work correctly:

```bash
cd .github/workflows
python test-ip-scanner.py
```

### Test Coverage

The test suite validates:

1. ✅ Documentation files are exempt
2. ✅ Example files are exempt
3. ✅ Test files are exempt (all naming conventions)
4. ✅ Exemption markers work (# Example:, # BAD -, etc.)
5. ✅ Markdown code blocks are exempt
6. ✅ Template files are exempt
7. ✅ Sample files are exempt
8. ✅ Real secrets in production code are still caught

## Adding New Exemptions

### Add Path-Based Exemption

Edit `.github/workflows/ip-scan.yml`:

```python
EXEMPT_PATHS = [
    # ... existing patterns ...
    r"/your-new-path/",  # Add your pattern here
]
```

Patterns use Python regex. Common patterns:
- `/path/` - Match directory anywhere
- `\.ext$` - Match file extension
- `filename\.md$` - Match specific filename

### Add Content Marker

Edit `.github/workflows/ip-scan.yml`:

```python
EXEMPT_MARKERS = [
    # ... existing patterns ...
    r"#\s*YourMarker:",  # Python-style marker
    r"//\s*YourMarker:",  # JavaScript-style marker
]
```

### Add File-Specific Exemption

Edit `.github/workflows/ip-scan.yml`:

```python
ALLOWED = {
    # ... existing files ...
    "your-file.md": ["pattern1", "pattern2"],
}
```

## Verification

After making changes, verify exemptions work:

1. **Run test suite**:
   ```bash
   python .github/workflows/test-ip-scanner.py
   ```

2. **Test on real repository**:
   ```bash
   python ip_scanner.py
   ```

3. **Check specific file**:
   ```python
   from pathlib import Path
   findings = scan_file(Path("your/file/path"))
   print(f"Findings: {len(findings)}")
   ```

## Real Secrets Still Caught

Despite exemptions, the scanner will **always flag** real secrets in production code:

```python
# ❌ This WILL be caught (no exemption marker)
stripe_key = "sk_live_actual_production_key"

# ❌ This WILL be caught (not in exempt path)
# File: src/config.py
api_key = "real-api-key-here"
```

## Troubleshooting

### False Positive Not Exempt

**Problem**: Documentation file still flagged

**Solution**: Check that path matches an EXEMPT_PATHS pattern:
```bash
python -c "import re; path='your/file/path'; print(any(re.search(p, path) for p in [r'/docs/', r'/examples/']))"
```

### Real Secret Not Caught

**Problem**: Actual secret not detected

**Solution**:
1. Verify pattern exists in PATTERNS dict
2. Check file isn't in EXEMPT_PATHS
3. Ensure no exemption marker in previous 3 lines

### Exemption Marker Not Working

**Problem**: Line with marker still flagged

**Solution**:
1. Marker must be within 3 lines **before** the match
2. Marker must match regex exactly (check spaces, colons)
3. For markdown, ensure inside code block (` ``` `)

## References

- Scanner workflow: `.github/workflows/ip-scan.yml`
- Test suite: `.github/workflows/test-ip-scanner.py`
- This guide: `.github/workflows/IP_SCANNER_EXEMPTIONS.md`
