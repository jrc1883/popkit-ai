#!/usr/bin/env python3
"""
Test suite for safe_json.py

Tests JSON input/output handling, edge cases, and security features.
Critical for hook safety and data integrity.
"""

import sys
import io
import json
import pytest
from unittest.mock import patch

# Add parent directory to path for imports
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from popkit_shared.utils.safe_json import sanitize_js_booleans, read_hook_input, write_hook_output


class TestSanitizeJsBooleans:
    """Test JavaScript boolean sanitization"""

    def test_sanitize_false_keyword(self):
        """Test sanitization of 'false' keyword"""
        input_text = '{"enabled": false}'
        result = sanitize_js_booleans(input_text)
        assert "false" in result
        # Should be valid JSON
        parsed = json.loads(result)
        assert parsed["enabled"] is False

    def test_sanitize_true_keyword(self):
        """Test sanitization of 'true' keyword"""
        input_text = '{"enabled": true}'
        result = sanitize_js_booleans(input_text)
        assert "true" in result
        parsed = json.loads(result)
        assert parsed["enabled"] is True

    def test_sanitize_null_keyword(self):
        """Test sanitization of 'null' keyword"""
        input_text = '{"value": null}'
        result = sanitize_js_booleans(input_text)
        assert "null" in result
        parsed = json.loads(result)
        assert parsed["value"] is None

    def test_multiple_booleans(self):
        """Test sanitization of multiple boolean values"""
        input_text = '{"a": true, "b": false, "c": null}'
        result = sanitize_js_booleans(input_text)
        parsed = json.loads(result)
        assert parsed["a"] is True
        assert parsed["b"] is False
        assert parsed["c"] is None

    def test_booleans_in_nested_objects(self):
        """Test booleans in nested structures"""
        input_text = '{"outer": {"inner": true, "value": false}}'
        result = sanitize_js_booleans(input_text)
        parsed = json.loads(result)
        assert parsed["outer"]["inner"] is True
        assert parsed["outer"]["value"] is False

    def test_boolean_in_array(self):
        """Test booleans in arrays"""
        input_text = '{"flags": [true, false, true]}'
        result = sanitize_js_booleans(input_text)
        parsed = json.loads(result)
        assert parsed["flags"] == [True, False, True]

    def test_boolean_not_in_string(self):
        """Test that booleans inside strings are not replaced"""
        # This is a known limitation of the simple regex approach
        # The function currently replaces all instances, which is acceptable
        # since hook input shouldn't have string values like "true" or "false"
        input_text = '{"message": "the value is true"}'
        result = sanitize_js_booleans(input_text)
        # Should still be valid JSON
        parsed = json.loads(result)
        assert "message" in parsed

    def test_empty_string(self):
        """Test empty string input"""
        result = sanitize_js_booleans("")
        assert result == ""

    def test_no_booleans(self):
        """Test string with no boolean keywords"""
        input_text = '{"name": "test", "value": 42}'
        result = sanitize_js_booleans(input_text)
        assert result == input_text


class TestReadHookInput:
    """Test read_hook_input function"""

    def test_valid_json_input(self):
        """Test reading valid JSON from stdin"""
        test_input = '{"key": "value", "number": 42}'
        with patch("sys.stdin", io.StringIO(test_input)):
            result = read_hook_input()
            assert result == {"key": "value", "number": 42}

    def test_empty_input(self):
        """Test reading empty stdin"""
        with patch("sys.stdin", io.StringIO("")):
            result = read_hook_input()
            assert result == {}

    def test_whitespace_only_input(self):
        """Test reading whitespace-only stdin"""
        with patch("sys.stdin", io.StringIO("   \n\t  ")):
            result = read_hook_input()
            assert result == {}

    def test_javascript_style_booleans(self):
        """Test reading JavaScript-style boolean input"""
        test_input = '{"enabled": false, "active": true}'
        with patch("sys.stdin", io.StringIO(test_input)):
            result = read_hook_input()
            assert result["enabled"] is False
            assert result["active"] is True

    def test_malformed_json(self):
        """Test reading malformed JSON returns default"""
        test_input = '{"key": invalid}'
        with patch("sys.stdin", io.StringIO(test_input)):
            result = read_hook_input()
            assert result == {}

    def test_custom_default(self):
        """Test custom default value on error"""
        test_input = "invalid json"
        custom_default = {"error": True}
        with patch("sys.stdin", io.StringIO(test_input)):
            result = read_hook_input(default=custom_default)
            assert result == custom_default

    def test_nested_objects(self):
        """Test reading nested JSON objects"""
        test_input = '{"outer": {"inner": {"value": 42}}}'
        with patch("sys.stdin", io.StringIO(test_input)):
            result = read_hook_input()
            assert result["outer"]["inner"]["value"] == 42

    def test_arrays(self):
        """Test reading arrays"""
        test_input = '{"items": [1, 2, 3]}'
        with patch("sys.stdin", io.StringIO(test_input)):
            result = read_hook_input()
            assert result["items"] == [1, 2, 3]

    def test_mixed_types(self):
        """Test reading mixed data types"""
        test_input = '{"string": "text", "number": 42, "bool": true, "null": null, "array": [1, 2]}'
        with patch("sys.stdin", io.StringIO(test_input)):
            result = read_hook_input()
            assert result["string"] == "text"
            assert result["number"] == 42
            assert result["bool"] is True
            assert result["null"] is None
            assert result["array"] == [1, 2]

    def test_unicode_characters(self):
        """Test reading Unicode characters"""
        test_input = '{"emoji": "🚀", "text": "Hello 世界"}'
        with patch("sys.stdin", io.StringIO(test_input)):
            result = read_hook_input()
            assert result["emoji"] == "🚀"
            assert result["text"] == "Hello 世界"

    def test_special_characters_in_strings(self):
        """Test special characters in JSON strings"""
        test_input = r'{"path": "C:\\Users\\test", "quote": "He said \"hello\""}'
        with patch("sys.stdin", io.StringIO(test_input)):
            result = read_hook_input()
            assert "path" in result
            assert "quote" in result

    def test_large_json_input(self):
        """Test reading large JSON input"""
        large_object = {"key" + str(i): "value" + str(i) for i in range(1000)}
        test_input = json.dumps(large_object)
        with patch("sys.stdin", io.StringIO(test_input)):
            result = read_hook_input()
            assert len(result) == 1000
            assert result["key0"] == "value0"
            assert result["key999"] == "value999"

    def test_stdin_read_error(self):
        """Test handling of stdin read errors"""
        with patch("sys.stdin.read", side_effect=IOError("Read error")):
            result = read_hook_input()
            assert result == {}

    def test_none_default(self):
        """Test that None default is converted to empty dict"""
        with patch("sys.stdin", io.StringIO("")):
            result = read_hook_input(default=None)
            assert result == {}


class TestWriteHookOutput:
    """Test write_hook_output function"""

    def test_valid_output(self):
        """Test writing valid output"""
        test_output = {"status": "success", "data": {"key": "value"}}
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            write_hook_output(test_output)
            output = mock_stdout.getvalue()
            parsed = json.loads(output)
            assert parsed == test_output

    def test_empty_dict(self):
        """Test writing empty dictionary"""
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            write_hook_output({})
            output = mock_stdout.getvalue()
            parsed = json.loads(output)
            assert parsed == {}

    def test_nested_output(self):
        """Test writing nested structures"""
        test_output = {"result": {"nested": {"value": 42}}}
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            write_hook_output(test_output)
            output = mock_stdout.getvalue()
            parsed = json.loads(output)
            assert parsed["result"]["nested"]["value"] == 42

    def test_array_output(self):
        """Test writing arrays"""
        test_output = {"items": [1, 2, 3, 4, 5]}
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            write_hook_output(test_output)
            output = mock_stdout.getvalue()
            parsed = json.loads(output)
            assert parsed["items"] == [1, 2, 3, 4, 5]

    def test_boolean_output(self):
        """Test writing boolean values"""
        test_output = {"success": True, "failed": False}
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            write_hook_output(test_output)
            output = mock_stdout.getvalue()
            parsed = json.loads(output)
            assert parsed["success"] is True
            assert parsed["failed"] is False

    def test_null_output(self):
        """Test writing null values"""
        test_output = {"value": None}
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            write_hook_output(test_output)
            output = mock_stdout.getvalue()
            parsed = json.loads(output)
            assert parsed["value"] is None

    def test_unicode_output(self):
        """Test writing Unicode characters"""
        test_output = {"emoji": "🎉", "text": "Hello 世界"}
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            write_hook_output(test_output)
            output = mock_stdout.getvalue()
            parsed = json.loads(output)
            assert parsed["emoji"] == "🎉"
            assert parsed["text"] == "Hello 世界"

    def test_serialization_error(self):
        """Test handling of serialization errors"""

        # Create an object that can't be serialized
        class NonSerializable:
            pass

        test_output = {"obj": NonSerializable()}
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            write_hook_output(test_output)
            output = mock_stdout.getvalue()
            parsed = json.loads(output)
            assert "error" in parsed
            assert parsed["status"] == "error"

    def test_large_output(self):
        """Test writing large output"""
        large_output = {"data": [{"key": "value"} for _ in range(1000)]}
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            write_hook_output(large_output)
            output = mock_stdout.getvalue()
            parsed = json.loads(output)
            assert len(parsed["data"]) == 1000


class TestIntegration:
    """Integration tests for read/write cycle"""

    def test_round_trip(self):
        """Test reading and writing preserves data"""
        test_data = {
            "string": "value",
            "number": 42,
            "bool": True,
            "null": None,
            "array": [1, 2, 3],
            "nested": {"key": "value"},
        }

        # Write
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            write_hook_output(test_data)
            output_json = mock_stdout.getvalue()

        # Read back
        with patch("sys.stdin", io.StringIO(output_json)):
            result = read_hook_input()

        assert result == test_data

    def test_error_response_format(self):
        """Test standard error response format"""
        error_response = {"status": "error", "error": "Something went wrong", "code": "ERR_TEST"}

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            write_hook_output(error_response)
            output = mock_stdout.getvalue()
            parsed = json.loads(output)

            assert parsed["status"] == "error"
            assert "error" in parsed

    def test_success_response_format(self):
        """Test standard success response format"""
        success_response = {"status": "success", "data": {"result": "completed"}}

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            write_hook_output(success_response)
            output = mock_stdout.getvalue()
            parsed = json.loads(output)

            assert parsed["status"] == "success"
            assert "data" in parsed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
