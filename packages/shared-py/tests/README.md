# PopKit Shared - Test Suite

Comprehensive test suite for the `popkit_shared` utility modules.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── test_complexity_scoring.py  # Complexity analysis tests
└── utils/                   # Utility module tests
    ├── test_safe_json.py       # JSON handling and security
    ├── test_flag_parser.py     # Command argument parsing
    ├── test_platform_detector.py  # Platform/shell detection
    └── test_privacy.py         # Privacy and anonymization
```

## Running Tests

### Run All Tests

```bash
cd packages/shared-py
pytest
```

### Run Specific Test File

```bash
pytest tests/utils/test_safe_json.py
```

### Run Specific Test Class

```bash
pytest tests/utils/test_safe_json.py::TestReadHookInput
```

### Run Specific Test

```bash
pytest tests/utils/test_safe_json.py::TestReadHookInput::test_valid_json_input
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Coverage Report

```bash
pytest --cov=popkit_shared --cov-report=html
```

Then open `htmlcov/index.html` in a browser.

## Test Categories

Tests are organized by markers:

- `unit`: Unit tests (default)
- `integration`: Integration tests
- `security`: Security-related tests
- `slow`: Slower running tests

### Run Only Unit Tests

```bash
pytest -m unit
```

### Run Security Tests

```bash
pytest -m security
```

### Exclude Slow Tests

```bash
pytest -m "not slow"
```

## Test Coverage

Current test coverage for critical utility modules:

| Module                 | Coverage Target | Status |
| ---------------------- | --------------- | ------ |
| `safe_json.py`         | 80%+            | ✓      |
| `flag_parser.py`       | 80%+            | ✓      |
| `platform_detector.py` | 80%+            | ✓      |
| `privacy.py`           | 80%+            | ✓      |

## Writing New Tests

### Test File Template

```python
#!/usr/bin/env python3
"""
Test suite for module_name.py

Brief description of what this module does and why it's critical.
"""

import sys
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from popkit_shared.utils.module_name import function_to_test


class TestFunctionName:
    """Test function_name"""

    def test_basic_functionality(self):
        """Test basic function behavior"""
        result = function_to_test("input")
        assert result == "expected_output"

    def test_edge_case_empty_input(self):
        """Test edge case: empty input"""
        result = function_to_test("")
        assert result == default_value

    def test_error_handling(self):
        """Test error handling"""
        with pytest.raises(ValueError):
            function_to_test(invalid_input)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

### Using Fixtures

```python
def test_with_fixture(temp_dir, sample_json_data):
    """Test using shared fixtures"""
    # temp_dir is a temporary directory
    # sample_json_data is sample JSON data

    file_path = temp_dir / "test.json"
    file_path.write_text(json.dumps(sample_json_data))

    # Test logic here
```

## Best Practices

1. **Test Both Success and Failure Cases**: Always test happy path and error conditions
2. **Test Edge Cases**: Empty inputs, None values, special characters, large data
3. **Use Fixtures**: Reuse test data and setup with fixtures
4. **Mock External Dependencies**: Use `unittest.mock` for file system, network, etc.
5. **Clear Test Names**: Use descriptive names like `test_parse_issue_number_with_hash`
6. **Arrange-Act-Assert**: Structure tests clearly with setup, execution, and validation
7. **One Assertion Per Test**: Focus each test on a single behavior
8. **Test Isolation**: Tests should not depend on each other or shared state

## Common Testing Patterns

### Testing JSON I/O

```python
from unittest.mock import patch
import io

def test_read_json_input():
    test_input = '{"key": "value"}'
    with patch('sys.stdin', io.StringIO(test_input)):
        result = read_hook_input()
        assert result == {"key": "value"}
```

### Testing File Operations

```python
def test_file_operation(temp_dir):
    file_path = temp_dir / "test.txt"
    file_path.write_text("content")

    result = process_file(file_path)
    assert result is not None
```

### Testing Platform Detection

```python
@patch('sys.platform', 'linux')
def test_linux_detection():
    result = detect_os()
    assert result == OSType.LINUX
```

### Testing Privacy/Anonymization

```python
def test_anonymize_sensitive_data():
    content = 'apiKey = "sk_live_123"'
    anonymized, removed = anonymize_content(content)

    assert "sk_live_123" not in anonymized
    assert "[API_KEY]" in anonymized
    assert "api_key" in removed
```

## Continuous Integration

Tests are automatically run on:

- Pull requests
- Commits to main branch
- Pre-commit hooks (if configured)

## Troubleshooting

### Import Errors

If you get import errors, ensure you're running from the correct directory:

```bash
cd packages/shared-py
pytest
```

### Path Issues

The tests add the parent directory to sys.path:

```python
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
```

### Module Not Found

Ensure `popkit_shared` package is properly structured with `__init__.py` files.

## Coverage Reports

Generate detailed coverage reports:

```bash
# HTML report (opens in browser)
pytest --cov=popkit_shared --cov-report=html
open htmlcov/index.html

# Terminal report
pytest --cov=popkit_shared --cov-report=term

# Missing lines report
pytest --cov=popkit_shared --cov-report=term-missing
```

## Future Additions

Planned test coverage for additional modules:

- [ ] `validate_commit.py` - Git commit validation
- [ ] `version.py` - Version management
- [ ] `changelog_generator.py` - Changelog generation
- [ ] Additional utility modules as identified

## Contributing

When adding new utility modules:

1. Create corresponding test file in `tests/utils/`
2. Aim for 80%+ code coverage
3. Include success, failure, and edge case tests
4. Update this README with coverage status
5. Run full test suite before committing

---

**Last Updated**: 2026-01-08
**Test Framework**: pytest 7.0+
**Coverage Tool**: pytest-cov (optional)
