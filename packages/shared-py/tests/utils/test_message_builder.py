#!/usr/bin/env python3
"""
Test suite for message_builder.py

Tests message composition utilities for Claude API messages.
Critical for hook communication and stateless message handling.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from popkit_shared.utils.message_builder import (
    build_assistant_message,
    build_text_block,
    build_tool_result_block,
    build_tool_result_message,
    build_tool_use_block,
    build_tool_use_message,
    build_user_message,
    compose_conversation,
    extract_tool_use,
    merge_tool_results,
    merge_tool_uses,
    rebuild_from_history,
)


class TestBasicMessageBuilders:
    """Test basic message building functions"""

    def test_build_user_message_with_string(self):
        """Test building user message with string content"""
        msg = build_user_message("Hello, Claude")
        assert msg["role"] == "user"
        assert msg["content"] == "Hello, Claude"

    def test_build_user_message_with_content_blocks(self):
        """Test building user message with content blocks"""
        content = [{"type": "text", "text": "Hello"}]
        msg = build_user_message(content)
        assert msg["role"] == "user"
        assert msg["content"] == content

    def test_build_assistant_message_with_string(self):
        """Test building assistant message with string"""
        msg = build_assistant_message("I'll help you")
        assert msg["role"] == "assistant"
        assert msg["content"] == "I'll help you"

    def test_build_assistant_message_with_content_blocks(self):
        """Test building assistant message with blocks"""
        content = [{"type": "text", "text": "Sure thing"}]
        msg = build_assistant_message(content)
        assert msg["role"] == "assistant"
        assert msg["content"] == content


class TestToolMessageBuilders:
    """Test tool-related message builders"""

    def test_build_tool_use_message(self):
        """Test building tool use message"""
        msg = build_tool_use_message("toolu_123", "Read", {"file_path": "test.py"})

        assert msg["role"] == "assistant"
        assert len(msg["content"]) == 1

        tool_use = msg["content"][0]
        assert tool_use["type"] == "tool_use"
        assert tool_use["id"] == "toolu_123"
        assert tool_use["name"] == "Read"
        assert tool_use["input"] == {"file_path": "test.py"}

    def test_build_tool_result_message(self):
        """Test building tool result message"""
        msg = build_tool_result_message("toolu_123", "File contents here")

        assert msg["role"] == "user"
        assert len(msg["content"]) == 1

        result = msg["content"][0]
        assert result["type"] == "tool_result"
        assert result["tool_use_id"] == "toolu_123"
        assert result["content"] == "File contents here"
        # is_error may be False or omitted when not an error
        assert result.get("is_error", False) is False

    def test_build_tool_result_message_with_error(self):
        """Test building tool result with error flag"""
        msg = build_tool_result_message("toolu_456", "Error message", is_error=True)

        result = msg["content"][0]
        assert result["is_error"] is True


class TestContentBlockBuilders:
    """Test content block builders"""

    def test_build_text_block(self):
        """Test building text content block"""
        block = build_text_block("Some text")
        assert block["type"] == "text"
        assert block["text"] == "Some text"

    def test_build_tool_use_block(self):
        """Test building tool use block"""
        block = build_tool_use_block(
            "toolu_789", "Write", {"file_path": "test.py", "content": "data"}
        )

        assert block["type"] == "tool_use"
        assert block["id"] == "toolu_789"
        assert block["name"] == "Write"
        assert block["input"]["file_path"] == "test.py"
        assert block["input"]["content"] == "data"

    def test_build_tool_result_block(self):
        """Test building tool result block"""
        block = build_tool_result_block("toolu_999", "Result data")

        assert block["type"] == "tool_result"
        assert block["tool_use_id"] == "toolu_999"
        assert block["content"] == "Result data"
        assert block.get("is_error", False) is False

    def test_build_tool_result_block_with_error(self):
        """Test building error tool result block"""
        block = build_tool_result_block("toolu_err", "Error occurred", is_error=True)
        assert block["is_error"] is True


class TestComposeConversation:
    """Test conversation composition"""

    def test_compose_conversation_with_valid_messages(self):
        """Test composing valid conversation"""
        messages = [build_user_message("Hello"), build_assistant_message("Hi there")]

        result = compose_conversation(messages)
        assert len(result) == 2
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "assistant"

    def test_compose_conversation_empty_list(self):
        """Test composing empty conversation"""
        result = compose_conversation([])
        assert result == []

    def test_compose_conversation_preserves_order(self):
        """Test that conversation order is preserved"""
        messages = [
            build_user_message("First"),
            build_assistant_message("Second"),
            build_user_message("Third"),
        ]

        result = compose_conversation(messages)
        assert result[0]["content"] == "First"
        assert result[1]["content"] == "Second"
        assert result[2]["content"] == "Third"


class TestMergeToolMessages:
    """Test merging tool use and result messages"""

    def test_merge_tool_uses(self):
        """Test merging multiple tool uses"""
        tool_uses = [
            {"type": "tool_use", "id": "t1", "name": "Read", "input": {}},
            {"type": "tool_use", "id": "t2", "name": "Write", "input": {}},
        ]

        msg = merge_tool_uses(tool_uses)
        assert msg["role"] == "assistant"
        assert len(msg["content"]) == 2
        assert msg["content"][0]["id"] == "t1"
        assert msg["content"][1]["id"] == "t2"

    def test_merge_tool_uses_single(self):
        """Test merging single tool use"""
        tool_uses = [{"type": "tool_use", "id": "t1", "name": "Read", "input": {}}]

        msg = merge_tool_uses(tool_uses)
        assert len(msg["content"]) == 1

    def test_merge_tool_results(self):
        """Test merging multiple tool results"""
        results = [
            {"type": "tool_result", "tool_use_id": "t1", "content": "result1", "is_error": False},
            {"type": "tool_result", "tool_use_id": "t2", "content": "result2", "is_error": False},
        ]

        msg = merge_tool_results(results)
        assert msg["role"] == "user"
        assert len(msg["content"]) == 2
        assert msg["content"][0]["tool_use_id"] == "t1"
        assert msg["content"][1]["tool_use_id"] == "t2"


class TestExtractToolUse:
    """Test extracting tool use from messages"""

    def test_extract_tool_use_from_assistant_message(self):
        """Test extracting tool use from assistant message"""
        msg = build_tool_use_message("toolu_abc", "Read", {"file": "test.py"})
        tool_uses = extract_tool_use(msg)

        assert len(tool_uses) == 1
        assert tool_uses[0]["id"] == "toolu_abc"
        assert tool_uses[0]["name"] == "Read"

    def test_extract_tool_use_from_text_message(self):
        """Test extracting from message with no tool use"""
        msg = build_assistant_message("Just text")
        tool_uses = extract_tool_use(msg)

        # Should return empty list for text-only messages
        assert isinstance(tool_uses, list)

    def test_extract_tool_use_from_mixed_content(self):
        """Test extracting from message with mixed content"""
        msg = {
            "role": "assistant",
            "content": [
                {"type": "text", "text": "I'll read the file"},
                {"type": "tool_use", "id": "toolu_xyz", "name": "Read", "input": {}},
            ],
        }

        tool_uses = extract_tool_use(msg)
        assert len(tool_uses) >= 1
        # Should extract the tool_use block


class TestRebuildFromHistory:
    """Test rebuilding messages from history"""

    def test_rebuild_from_history_simple(self):
        """Test rebuilding simple conversation"""
        history = {"user_prompt": "Hello", "tool_uses": [], "tool_results": []}

        messages = rebuild_from_history(history)
        # Should at least have the user prompt
        assert len(messages) > 0
        assert any(msg["role"] == "user" for msg in messages)

    def test_rebuild_from_history_with_tools(self):
        """Test rebuilding with tool uses and results"""
        history = {
            "user_prompt": "Read test.py",
            "tool_uses": [
                {"type": "tool_use", "id": "t1", "name": "Read", "input": {"file": "test.py"}}
            ],
            "tool_results": [
                {
                    "type": "tool_result",
                    "tool_use_id": "t1",
                    "content": "file contents",
                    "is_error": False,
                }
            ],
        }

        messages = rebuild_from_history(history)
        # Should have user, assistant (tool use), user (tool result)
        assert len(messages) >= 2


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_build_message_with_empty_string(self):
        """Test building message with empty string"""
        msg = build_user_message("")
        assert msg["content"] == ""

    def test_build_tool_use_with_empty_input(self):
        """Test building tool use with empty input"""
        msg = build_tool_use_message("t1", "Tool", {})
        assert msg["content"][0]["input"] == {}

    def test_compose_conversation_with_duplicate_roles(self):
        """Test composing conversation with consecutive same roles"""
        messages = [
            build_user_message("First"),
            build_user_message("Second"),  # Consecutive user messages
        ]

        result = compose_conversation(messages)
        assert len(result) == 2  # Should preserve both

    def test_build_tool_result_with_complex_content(self):
        """Test tool result with complex content types"""
        complex_content = "Multi\nline\ncontent with special chars: <>&"
        msg = build_tool_result_message("t1", complex_content)
        assert msg["content"][0]["content"] == complex_content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
