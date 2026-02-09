#!/usr/bin/env python3
"""
Test suite for stateless_hook.py

Tests the base class for all PopKit hooks. Critical for hook system reliability
since all hooks inherit from this class.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from popkit_shared.utils.stateless_hook import StatelessHook, run_hook


class TestStatelessHookAbstractBehavior:
    """Test abstract base class behavior"""

    def test_cannot_instantiate_stateless_hook_directly(self):
        """Test that StatelessHook cannot be instantiated (abstract class)"""
        with pytest.raises(TypeError):
            # Should fail because process() is abstract
            StatelessHook()

    def test_must_implement_process_method(self):
        """Test that subclass must implement process() method"""
        # Incomplete subclass (missing process)
        with pytest.raises(TypeError):

            class IncompleteHook(StatelessHook):
                pass

            IncompleteHook()


class TestConcreteHookImplementation:
    """Test concrete hook implementation"""

    def test_can_instantiate_complete_subclass(self):
        """Test that complete subclass can be instantiated"""

        class CompleteHook(StatelessHook):
            def process(self, ctx):
                return ctx

        hook = CompleteHook()
        assert isinstance(hook, StatelessHook)

    def test_process_method_called(self):
        """Test that process() method is called during execution"""
        process_called = False

        class TestHook(StatelessHook):
            def process(self, ctx):
                nonlocal process_called
                process_called = True
                return ctx

        # Mock the create_context to return a simple object
        with patch("popkit_shared.utils.stateless_hook.create_context") as mock_create:
            mock_ctx = MagicMock()
            mock_create.return_value = mock_ctx

            with patch("popkit_shared.utils.stateless_hook.serialize_context", return_value="{}"):
                hook = TestHook()
                input_json = json.dumps({"tool_name": "Test"})
                hook.run(input_json)

                assert process_called is True

    def test_process_receives_context(self):
        """Test that process() receives correct context object"""
        received_ctx = None

        class TestHook(StatelessHook):
            def process(self, ctx):
                nonlocal received_ctx
                received_ctx = ctx
                return ctx

        mock_ctx = MagicMock()
        with patch("popkit_shared.utils.stateless_hook.create_context", return_value=mock_ctx):
            with patch("popkit_shared.utils.stateless_hook.serialize_context", return_value="{}"):
                hook = TestHook()
                input_json = json.dumps({"tool_name": "Test"})
                hook.run(input_json)

                assert received_ctx == mock_ctx


class TestContextHelpers:
    """Test context management helper methods"""

    def test_create_context_helper(self):
        """Test create_context helper delegates correctly"""

        class TestHook(StatelessHook):
            def process(self, ctx):
                return ctx

        with patch("popkit_shared.utils.stateless_hook.create_context") as mock_create:
            mock_ctx = MagicMock()
            mock_create.return_value = mock_ctx

            hook = TestHook()
            result = hook.create_context(session_id="test", tool_name="Read")

            mock_create.assert_called_once_with(session_id="test", tool_name="Read")
            assert result == mock_ctx

    def test_update_context_helper(self):
        """Test update_context helper delegates correctly"""

        class TestHook(StatelessHook):
            def process(self, ctx):
                return ctx

        with patch("popkit_shared.utils.stateless_hook.update_context") as mock_update:
            mock_ctx = MagicMock()
            mock_updated_ctx = MagicMock()
            mock_update.return_value = mock_updated_ctx

            hook = TestHook()
            result = hook.update_context(mock_ctx, tool_result="done")

            mock_update.assert_called_once_with(mock_ctx, tool_result="done")
            assert result == mock_updated_ctx

    def test_context_immutability_pattern(self):
        """Test that update_context returns new context (immutability)"""

        class TestHook(StatelessHook):
            def process(self, ctx):
                updated = self.update_context(ctx, new_field="value")
                return updated

        with patch("popkit_shared.utils.stateless_hook.create_context") as mock_create:
            with patch("popkit_shared.utils.stateless_hook.update_context") as mock_update:
                with patch(
                    "popkit_shared.utils.stateless_hook.serialize_context", return_value="{}"
                ):
                    original_ctx = MagicMock()
                    updated_ctx = MagicMock()

                    mock_create.return_value = original_ctx
                    mock_update.return_value = updated_ctx

                    hook = TestHook()
                    input_json = json.dumps({"tool_name": "Test"})
                    hook.run(input_json)

                    # Verify update_context was called with original
                    mock_update.assert_called_once()
                    # Verify returned context is the updated one
                    assert mock_update.return_value == updated_ctx


class TestMessageBuilderHelpers:
    """Test message building helper methods"""

    def test_build_user_message_helper(self):
        """Test build_user_message helper"""

        class TestHook(StatelessHook):
            def process(self, ctx):
                return ctx

        with patch("popkit_shared.utils.stateless_hook.build_user_message") as mock_build:
            mock_msg = {"role": "user", "content": "test"}
            mock_build.return_value = mock_msg

            hook = TestHook()
            result = hook.build_user_message("test")

            mock_build.assert_called_once_with("test")
            assert result == mock_msg

    def test_build_assistant_message_helper(self):
        """Test build_assistant_message helper"""

        class TestHook(StatelessHook):
            def process(self, ctx):
                return ctx

        with patch("popkit_shared.utils.stateless_hook.build_assistant_message") as mock_build:
            mock_msg = {"role": "assistant", "content": "response"}
            mock_build.return_value = mock_msg

            hook = TestHook()
            result = hook.build_assistant_message("response")

            mock_build.assert_called_once_with("response")
            assert result == mock_msg

    def test_build_tool_use_helper(self):
        """Test build_tool_use helper"""

        class TestHook(StatelessHook):
            def process(self, ctx):
                return ctx

        with patch("popkit_shared.utils.stateless_hook.build_tool_use_message") as mock_build:
            mock_msg = {"role": "assistant", "content": [{"type": "tool_use"}]}
            mock_build.return_value = mock_msg

            hook = TestHook()
            result = hook.build_tool_use("tool123", "Read", {"file": "test.py"})

            mock_build.assert_called_once_with("tool123", "Read", {"file": "test.py"})
            assert result == mock_msg

    def test_build_tool_result_helper(self):
        """Test build_tool_result helper"""

        class TestHook(StatelessHook):
            def process(self, ctx):
                return ctx

        with patch("popkit_shared.utils.stateless_hook.build_tool_result_message") as mock_build:
            mock_msg = {"role": "user", "content": [{"type": "tool_result"}]}
            mock_build.return_value = mock_msg

            hook = TestHook()
            result = hook.build_tool_result("tool123", "result content", is_error=False)

            mock_build.assert_called_once_with("tool123", "result content", False)
            assert result == mock_msg

    def test_compose_messages_helper(self):
        """Test compose_messages helper"""

        class TestHook(StatelessHook):
            def process(self, ctx):
                return ctx

        with patch("popkit_shared.utils.stateless_hook.compose_conversation") as mock_compose:
            messages = [{"role": "user", "content": "test"}]
            mock_result = [{"role": "user", "content": "test"}]
            mock_compose.return_value = mock_result

            hook = TestHook()
            result = hook.compose_messages(messages)

            mock_compose.assert_called_once_with(messages)
            assert result == mock_result

    def test_rebuild_messages_helper(self):
        """Test rebuild_messages helper"""

        class TestHook(StatelessHook):
            def process(self, ctx):
                return ctx

        with patch("popkit_shared.utils.stateless_hook.rebuild_from_history") as mock_rebuild:
            history = {"user_prompt": "test", "tool_uses": [], "tool_results": []}
            mock_result = [{"role": "user", "content": "test"}]
            mock_rebuild.return_value = mock_result

            hook = TestHook()
            result = hook.rebuild_messages(history)

            mock_rebuild.assert_called_once_with(history)
            assert result == mock_result


class TestJSONProtocol:
    """Test JSON stdin/stdout protocol"""

    def test_run_with_valid_json(self):
        """Test run() with valid JSON input"""

        class TestHook(StatelessHook):
            def process(self, ctx):
                return ctx

        mock_ctx = MagicMock()
        with patch("popkit_shared.utils.stateless_hook.create_context", return_value=mock_ctx):
            with patch(
                "popkit_shared.utils.stateless_hook.serialize_context",
                return_value='{"session_id":"test"}',
            ):
                hook = TestHook()
                input_json = json.dumps(
                    {
                        "session_id": "sess_123",
                        "tool_name": "Read",
                        "tool_input": {"file_path": "test.py"},
                    }
                )
                output = hook.run(input_json)

                # Should return valid JSON
                output_data = json.loads(output)
                assert "action" in output_data
                assert "context" in output_data
                assert output_data["action"] == "continue"

    def test_run_creates_context_from_input(self):
        """Test that run() creates context with correct input data"""

        class TestHook(StatelessHook):
            def process(self, ctx):
                return ctx

        with patch("popkit_shared.utils.stateless_hook.create_context") as mock_create:
            with patch("popkit_shared.utils.stateless_hook.serialize_context", return_value="{}"):
                mock_ctx = MagicMock()
                mock_create.return_value = mock_ctx

                hook = TestHook()
                input_data = {
                    "session_id": "sess_123",
                    "tool_name": "Read",
                    "tool_input": {"file_path": "test.py"},
                    "message_history": [],
                }
                input_json = json.dumps(input_data)
                hook.run(input_json)

                # Verify create_context was called with correct params
                mock_create.assert_called_once_with(
                    session_id="sess_123",
                    tool_name="Read",
                    tool_input={"file_path": "test.py"},
                    message_history=[],
                )

    def test_run_handles_missing_optional_fields(self):
        """Test run() handles missing optional fields with defaults"""

        class TestHook(StatelessHook):
            def process(self, ctx):
                return ctx

        with patch("popkit_shared.utils.stateless_hook.create_context") as mock_create:
            with patch("popkit_shared.utils.stateless_hook.serialize_context", return_value="{}"):
                mock_ctx = MagicMock()
                mock_create.return_value = mock_ctx

                hook = TestHook()
                # Minimal input (missing session_id, tool_input, message_history)
                input_json = json.dumps({"tool_name": "Read"})
                hook.run(input_json)

                # Should use defaults
                mock_create.assert_called_once_with(
                    session_id="unknown", tool_name="Read", tool_input={}, message_history=[]
                )

    def test_run_serializes_result_context(self):
        """Test that run() serializes result context to JSON"""

        class TestHook(StatelessHook):
            def process(self, ctx):
                return ctx

        mock_ctx = MagicMock()
        with patch("popkit_shared.utils.stateless_hook.create_context", return_value=mock_ctx):
            with patch("popkit_shared.utils.stateless_hook.serialize_context") as mock_serialize:
                mock_serialize.return_value = '{"session_id":"sess_123","result":"done"}'

                hook = TestHook()
                input_json = json.dumps({"tool_name": "Test"})
                output = hook.run(input_json)

                # Verify serialize_context was called
                mock_serialize.assert_called_once_with(mock_ctx)

                # Verify output includes serialized context
                output_data = json.loads(output)
                assert output_data["context"]["session_id"] == "sess_123"
                assert output_data["context"]["result"] == "done"


class TestErrorHandling:
    """Test error handling in JSON protocol"""

    def test_run_handles_invalid_json(self):
        """Test run() handles invalid JSON input"""

        class TestHook(StatelessHook):
            def process(self, ctx):
                return ctx

        hook = TestHook()
        invalid_json = "not json"
        output = hook.run(invalid_json)

        # Should return error JSON
        output_data = json.loads(output)
        assert output_data["action"] == "error"
        assert "error" in output_data
        assert len(output_data["error"]) > 0

    def test_run_handles_process_exception(self):
        """Test run() handles exceptions during process()"""

        class FailingHook(StatelessHook):
            def process(self, ctx):
                raise ValueError("Process failed")

        with patch("popkit_shared.utils.stateless_hook.create_context", return_value=MagicMock()):
            hook = FailingHook()
            input_json = json.dumps({"tool_name": "Test"})
            output = hook.run(input_json)

            # Should return error JSON
            output_data = json.loads(output)
            assert output_data["action"] == "error"
            assert "Process failed" in output_data["error"]

    def test_run_handles_context_creation_error(self):
        """Test run() handles errors during context creation"""

        class TestHook(StatelessHook):
            def process(self, ctx):
                return ctx

        with patch(
            "popkit_shared.utils.stateless_hook.create_context",
            side_effect=RuntimeError("Context creation failed"),
        ):
            hook = TestHook()
            input_json = json.dumps({"tool_name": "Test"})
            output = hook.run(input_json)

            # Should return error JSON
            output_data = json.loads(output)
            assert output_data["action"] == "error"
            assert "Context creation failed" in output_data["error"]

    def test_run_handles_serialization_error(self):
        """Test run() handles errors during context serialization"""

        class TestHook(StatelessHook):
            def process(self, ctx):
                return ctx

        with patch("popkit_shared.utils.stateless_hook.create_context", return_value=MagicMock()):
            with patch(
                "popkit_shared.utils.stateless_hook.serialize_context",
                side_effect=TypeError("Cannot serialize"),
            ):
                hook = TestHook()
                input_json = json.dumps({"tool_name": "Test"})
                output = hook.run(input_json)

                # Should return error JSON
                output_data = json.loads(output)
                assert output_data["action"] == "error"
                assert "Cannot serialize" in output_data["error"]


class TestRunHookConvenienceFunction:
    """Test run_hook convenience function"""

    def test_run_hook_instantiates_and_runs(self):
        """Test run_hook() instantiates hook class and runs it"""

        class TestHook(StatelessHook):
            def process(self, ctx):
                return ctx

        with patch("popkit_shared.utils.stateless_hook.create_context", return_value=MagicMock()):
            with patch("popkit_shared.utils.stateless_hook.serialize_context", return_value="{}"):
                input_json = json.dumps({"tool_name": "Test"})
                output = run_hook(TestHook, input_json)

                # Should return valid JSON output
                output_data = json.loads(output)
                assert "action" in output_data
                assert output_data["action"] == "continue"

    def test_run_hook_passes_input_to_hook(self):
        """Test run_hook() passes input correctly to hook instance"""
        received_input = None

        class TestHook(StatelessHook):
            def run(self, input_json):
                nonlocal received_input
                received_input = input_json
                return '{"action":"continue","context":{}}'

            def process(self, ctx):
                return ctx

        input_json = json.dumps({"tool_name": "Test", "custom_field": "value"})
        run_hook(TestHook, input_json)

        # Verify input was passed
        assert received_input == input_json
        received_data = json.loads(received_input)
        assert received_data["custom_field"] == "value"


class TestRealWorldScenarios:
    """Test real-world hook usage scenarios"""

    def test_simple_passthrough_hook(self):
        """Test simple hook that passes context through"""

        class PassthroughHook(StatelessHook):
            def process(self, ctx):
                return ctx

        with patch("popkit_shared.utils.stateless_hook.create_context", return_value=MagicMock()):
            with patch(
                "popkit_shared.utils.stateless_hook.serialize_context",
                return_value='{"status":"ok"}',
            ):
                hook = PassthroughHook()
                input_json = json.dumps({"tool_name": "Read"})
                output = hook.run(input_json)

                output_data = json.loads(output)
                assert output_data["action"] == "continue"
                assert output_data["context"]["status"] == "ok"

    def test_hook_with_context_modification(self):
        """Test hook that modifies context"""

        class ModifyingHook(StatelessHook):
            def process(self, ctx):
                return self.update_context(ctx, modified=True, result="processed")

        mock_ctx = MagicMock()
        modified_ctx = MagicMock()

        with patch("popkit_shared.utils.stateless_hook.create_context", return_value=mock_ctx):
            with patch(
                "popkit_shared.utils.stateless_hook.update_context", return_value=modified_ctx
            ):
                with patch(
                    "popkit_shared.utils.stateless_hook.serialize_context",
                    return_value='{"modified":true}',
                ):
                    hook = ModifyingHook()
                    input_json = json.dumps({"tool_name": "Test"})
                    output = hook.run(input_json)

                    output_data = json.loads(output)
                    assert output_data["action"] == "continue"
                    assert output_data["context"]["modified"] is True

    def test_hook_with_message_building(self):
        """Test hook that builds messages"""

        class MessageBuildingHook(StatelessHook):
            def process(self, ctx):
                # Build some messages
                user_msg = self.build_user_message("Hello")
                assistant_msg = self.build_assistant_message("Hi there")
                messages = self.compose_messages([user_msg, assistant_msg])
                return self.update_context(ctx, messages=messages)

        mock_ctx = MagicMock()
        mock_user_msg = {"role": "user", "content": "Hello"}
        mock_assistant_msg = {"role": "assistant", "content": "Hi there"}
        mock_composed = [mock_user_msg, mock_assistant_msg]

        with patch("popkit_shared.utils.stateless_hook.create_context", return_value=mock_ctx):
            with patch(
                "popkit_shared.utils.stateless_hook.build_user_message", return_value=mock_user_msg
            ):
                with patch(
                    "popkit_shared.utils.stateless_hook.build_assistant_message",
                    return_value=mock_assistant_msg,
                ):
                    with patch(
                        "popkit_shared.utils.stateless_hook.compose_conversation",
                        return_value=mock_composed,
                    ):
                        with patch(
                            "popkit_shared.utils.stateless_hook.update_context",
                            return_value=mock_ctx,
                        ):
                            with patch(
                                "popkit_shared.utils.stateless_hook.serialize_context",
                                return_value='{"status":"ok"}',
                            ):
                                hook = MessageBuildingHook()
                                input_json = json.dumps({"tool_name": "Test"})
                                output = hook.run(input_json)

                                output_data = json.loads(output)
                                assert output_data["action"] == "continue"


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_empty_input_json(self):
        """Test handling of empty JSON object"""

        class TestHook(StatelessHook):
            def process(self, ctx):
                return ctx

        with patch("popkit_shared.utils.stateless_hook.create_context", return_value=MagicMock()):
            with patch("popkit_shared.utils.stateless_hook.serialize_context", return_value="{}"):
                hook = TestHook()
                input_json = "{}"
                output = hook.run(input_json)

                output_data = json.loads(output)
                assert output_data["action"] == "continue"

    def test_process_returns_none(self):
        """Test handling when process() returns None"""

        class NoneReturningHook(StatelessHook):
            def process(self, ctx):
                return None

        with patch("popkit_shared.utils.stateless_hook.create_context", return_value=MagicMock()):
            with patch(
                "popkit_shared.utils.stateless_hook.serialize_context",
                side_effect=TypeError("Cannot serialize None"),
            ):
                hook = NoneReturningHook()
                input_json = json.dumps({"tool_name": "Test"})
                output = hook.run(input_json)

                # Should handle gracefully with error
                output_data = json.loads(output)
                assert output_data["action"] == "error"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
