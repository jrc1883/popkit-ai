#!/usr/bin/env python3
"""Tests for stateless hook v2 provider-aware features."""

import json
import os
from unittest.mock import patch

from popkit_shared.utils.context_carrier import create_context
from popkit_shared.utils.stateless_hook import StatelessHook, _detect_provider, run_hook

# =============================================================================
# Provider Detection
# =============================================================================


class TestDetectProvider:
    """Tests for _detect_provider()."""

    def test_detects_claude_code_from_plugin_data(self):
        """Detects Claude Code when CLAUDE_PLUGIN_DATA is set."""
        with patch.dict(os.environ, {"CLAUDE_PLUGIN_DATA": "/some/path"}, clear=False):
            os.environ.pop("POPKIT_PROVIDER", None)
            assert _detect_provider() == "claude-code"

    def test_detects_claude_code_from_plugin_root(self):
        """Detects Claude Code when CLAUDE_PLUGIN_ROOT is set."""
        with patch.dict(os.environ, {"CLAUDE_PLUGIN_ROOT": "/some/path"}, clear=False):
            os.environ.pop("POPKIT_PROVIDER", None)
            os.environ.pop("CLAUDE_PLUGIN_DATA", None)
            assert _detect_provider() == "claude-code"

    def test_detects_popkit_provider_env(self):
        """Respects POPKIT_PROVIDER env var."""
        with patch.dict(os.environ, {"POPKIT_PROVIDER": "cursor"}, clear=False):
            os.environ.pop("CLAUDE_PLUGIN_DATA", None)
            os.environ.pop("CLAUDE_PLUGIN_ROOT", None)
            assert _detect_provider() == "cursor"

    def test_defaults_to_claude_code(self):
        """Defaults to claude-code when nothing set."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CLAUDE_PLUGIN_DATA", None)
            os.environ.pop("CLAUDE_PLUGIN_ROOT", None)
            os.environ.pop("POPKIT_PROVIDER", None)
            assert _detect_provider() == "claude-code"


# =============================================================================
# StatelessHook Provider Property
# =============================================================================


class TestStatelessHookProvider:
    """Tests for the provider property on StatelessHook."""

    def test_provider_accessible(self):
        """Hook instances can access the provider property."""

        class TestHook(StatelessHook):
            def process(self, ctx):
                return ctx

        hook = TestHook()
        # Should return a string without crashing
        assert isinstance(hook.provider, str)

    def test_provider_from_input_json(self):
        """Provider can be set via input JSON."""

        class ProviderEchoHook(StatelessHook):
            def process(self, ctx):
                return self.update_context(ctx, tool_result=self.provider)

        input_data = {
            "session_id": "test",
            "tool_name": "Test",
            "tool_input": {},
            "provider": "cursor",
        }
        output = run_hook(ProviderEchoHook, json.dumps(input_data))
        result = json.loads(output)
        assert result["context"]["tool_result"] == "cursor"


# =============================================================================
# Response Helpers
# =============================================================================


class TestResponseHelpers:
    """Tests for respond_continue, respond_deny, respond_ask."""

    def _make_ctx(self):
        return create_context("sess", "Read", {"file_path": "test.py"})

    def test_respond_continue(self):
        """respond_continue produces a continue response."""

        class ContinueHook(StatelessHook):
            def process(self, ctx):
                return self.respond_continue(ctx)

        output = run_hook(
            ContinueHook,
            json.dumps({"session_id": "s", "tool_name": "T", "tool_input": {}}),
        )
        result = json.loads(output)
        assert result["action"] == "continue"

    def test_respond_continue_with_message(self):
        """respond_continue can include a message."""

        class MsgHook(StatelessHook):
            def process(self, ctx):
                return self.respond_continue(ctx, message="All good")

        output = run_hook(
            MsgHook,
            json.dumps({"session_id": "s", "tool_name": "T", "tool_input": {}}),
        )
        result = json.loads(output)
        assert result["action"] == "continue"
        assert result["message"] == "All good"

    def test_respond_deny(self):
        """respond_deny produces a deny response."""

        class DenyHook(StatelessHook):
            def process(self, ctx):
                return self.respond_deny(ctx, "Not allowed")

        output = run_hook(
            DenyHook,
            json.dumps({"session_id": "s", "tool_name": "T", "tool_input": {}}),
        )
        result = json.loads(output)
        assert result["action"] == "deny"
        assert result["message"] == "Not allowed"

    def test_respond_ask(self):
        """respond_ask produces an ask response."""

        class AskHook(StatelessHook):
            def process(self, ctx):
                return self.respond_ask(ctx, "Are you sure?")

        output = run_hook(
            AskHook,
            json.dumps({"session_id": "s", "tool_name": "T", "tool_input": {}}),
        )
        result = json.loads(output)
        assert result["action"] == "ask"
        assert result["message"] == "Are you sure?"


# =============================================================================
# Backward Compatibility
# =============================================================================


class TestBackwardCompatibility:
    """Ensure existing hooks work unchanged."""

    def test_old_style_hook_still_works(self):
        """Hooks that don't use respond_* default to continue."""

        class OldHook(StatelessHook):
            def process(self, ctx):
                return self.update_context(ctx, tool_result="processed")

        output = run_hook(
            OldHook,
            json.dumps({"session_id": "s", "tool_name": "T", "tool_input": {}}),
        )
        result = json.loads(output)
        assert result["action"] == "continue"
        assert result["context"]["tool_result"] == "processed"

    def test_error_handling_unchanged(self):
        """Exceptions still produce error responses."""

        class BrokenHook(StatelessHook):
            def process(self, ctx):
                raise ValueError("something broke")

        output = run_hook(
            BrokenHook,
            json.dumps({"session_id": "s", "tool_name": "T", "tool_input": {}}),
        )
        result = json.loads(output)
        assert result["action"] == "error"
        assert "something broke" in result["error"]
