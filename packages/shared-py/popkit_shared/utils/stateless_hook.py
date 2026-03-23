#!/usr/bin/env python3
"""
Stateless Hook Base Class

Provides a foundation for building hooks that follow stateless message composition.
Hooks extending this class receive explicit context, use message builder utilities,
and return complete output including updated context.

Supports multi-provider hook execution (v2.0):
- provider property detects the current provider from environment
- respond() method returns provider-agnostic HookResponse
- run() auto-formats output for the detected provider
- Fully backward compatible: existing hooks work unchanged

Part of the popkit plugin stateless hook architecture.
"""

import json
import os
from abc import ABC, abstractmethod
from typing import Optional, Type

from .context_carrier import (
    HookContext,
    create_context,
    serialize_context,
    update_context,
)
from .message_builder import (
    build_assistant_message,
    build_tool_result_message,
    build_tool_use_message,
    build_user_message,
    compose_conversation,
    rebuild_from_history,
)


def _detect_provider() -> str:
    """Detect the current provider from environment.

    Returns:
        Provider identifier string
    """
    # Claude Code sets these env vars
    if os.environ.get("CLAUDE_PLUGIN_DATA") or os.environ.get("CLAUDE_PLUGIN_ROOT"):
        return "claude-code"

    # PopKit sets this when running under a specific provider
    popkit_provider = os.environ.get("POPKIT_PROVIDER")
    if popkit_provider:
        return popkit_provider

    # Default: assume Claude Code for backward compatibility
    return "claude-code"


class StatelessHook(ABC):
    """Base class for stateless hooks.

    Hooks extending this class:
    - Receive explicit context (no hidden state)
    - Use message builder utilities for composition
    - Return complete output including updated context
    - Can detect and adapt to different providers (v2.0)

    Example:
        class MyHook(StatelessHook):
            def process(self, ctx: HookContext) -> HookContext:
                # Do processing
                return self.update_context(ctx, tool_result="done")

    Provider-aware example (v2.0):
        class SafetyHook(StatelessHook):
            def process(self, ctx: HookContext) -> HookContext:
                if self.provider == "cursor":
                    # Cursor-specific handling
                    pass
                return self.respond_continue(ctx)

    The hook can then be run via JSON protocol:
        output = run_hook(MyHook, input_json)
    """

    def __init__(self):
        """Initialize hook - no external state."""
        self._provider: Optional[str] = None

    @property
    def provider(self) -> str:
        """Current provider (auto-detected from environment).

        Returns:
            Provider identifier (e.g., "claude-code", "cursor", "generic-mcp")
        """
        if self._provider is None:
            self._provider = _detect_provider()
        return self._provider

    @abstractmethod
    def process(self, ctx: HookContext) -> HookContext:
        """Process the hook with given context.

        This is the main method to implement. Receive context,
        do processing, return updated context.

        Args:
            ctx: Immutable hook context

        Returns:
            New context with updates (original unchanged)
        """
        pass

    # =========================================================================
    # Context Helpers
    # =========================================================================

    def create_context(self, **kwargs) -> HookContext:
        """Create a new hook context.

        Args:
            **kwargs: Context fields (session_id, tool_name, tool_input, etc.)

        Returns:
            New HookContext instance
        """
        return create_context(**kwargs)

    def update_context(self, ctx: HookContext, **updates) -> HookContext:
        """Update context with new values (returns new context).

        Args:
            ctx: Existing context
            **updates: Fields to update

        Returns:
            New context with updates applied
        """
        return update_context(ctx, **updates)

    # =========================================================================
    # Message Builder Helpers
    # =========================================================================

    def build_user_message(self, content):
        """Build a user role message.

        Args:
            content: String or list of content blocks

        Returns:
            Message dict with role="user"
        """
        return build_user_message(content)

    def build_assistant_message(self, content):
        """Build an assistant role message.

        Args:
            content: String or list of content blocks

        Returns:
            Message dict with role="assistant"
        """
        return build_assistant_message(content)

    def build_tool_use(self, tool_use_id, name, input):
        """Build an assistant message with tool use.

        Args:
            tool_use_id: Unique ID for this tool use
            name: Tool name
            input: Tool input parameters

        Returns:
            Message dict with tool_use content block
        """
        return build_tool_use_message(tool_use_id, name, input)

    def build_tool_result(self, tool_use_id, content, is_error=False):
        """Build a user message with tool result.

        Args:
            tool_use_id: ID matching the tool_use
            content: Result content
            is_error: Whether this is an error result

        Returns:
            Message dict with tool_result content block
        """
        return build_tool_result_message(tool_use_id, content, is_error)

    def compose_messages(self, messages):
        """Compose a conversation from a list of messages.

        Args:
            messages: List of message dicts

        Returns:
            Validated conversation array
        """
        return compose_conversation(messages)

    def rebuild_messages(self, history):
        """Rebuild message array from history dict.

        Args:
            history: Dict with user_prompt, tool_uses, tool_results

        Returns:
            Complete conversation array
        """
        return rebuild_from_history(history)

    # =========================================================================
    # Provider-Aware Response Helpers (v2.0)
    # =========================================================================

    def respond_continue(self, ctx: HookContext, message: Optional[str] = None) -> HookContext:
        """Mark the hook response as CONTINUE (allow the action).

        Args:
            ctx: Current context
            message: Optional informational message

        Returns:
            Updated context with response metadata
        """
        updates = {"hook_output": ("_response", {"action": "continue"})}
        if message:
            updates["hook_output"] = ("_response", {"action": "continue", "message": message})
        return update_context(ctx, **updates)

    def respond_deny(self, ctx: HookContext, message: str) -> HookContext:
        """Mark the hook response as DENY (block the action).

        Args:
            ctx: Current context
            message: Explanation of why the action was denied

        Returns:
            Updated context with deny response
        """
        return update_context(
            ctx, hook_output=("_response", {"action": "deny", "message": message})
        )

    def respond_ask(self, ctx: HookContext, message: str) -> HookContext:
        """Mark the hook response as ASK (prompt user for confirmation).

        Args:
            ctx: Current context
            message: Question to ask the user

        Returns:
            Updated context with ask response
        """
        return update_context(ctx, hook_output=("_response", {"action": "ask", "message": message}))

    # =========================================================================
    # JSON Protocol
    # =========================================================================

    def run(self, input_json: str) -> str:
        """Run the hook with JSON input.

        Implements the hook JSON protocol with provider-aware output:
        - Receive JSON on stdin with tool_name, tool_input, session_id
        - Process the hook
        - Return JSON formatted for the current provider

        For Claude Code: {"action": "continue|deny|ask", "context": {...}}
        For other providers: same format (protocol originated from Claude Code)

        Args:
            input_json: JSON string with hook input

        Returns:
            JSON string with action and context

        Example:
            >>> input_json = '{"tool_name": "Read", "tool_input": {...}}'
            >>> output = hook.run(input_json)
            >>> # output: '{"action": "continue", "context": {...}}'
        """
        try:
            input_data = json.loads(input_json)

            # Detect provider from input or environment
            if "provider" in input_data:
                self._provider = input_data["provider"]

            # Create context from input
            ctx = create_context(
                session_id=input_data.get("session_id", "unknown"),
                tool_name=input_data.get("tool_name", ""),
                tool_input=input_data.get("tool_input", {}),
                message_history=input_data.get("message_history", []),
            )

            # Process
            result_ctx = self.process(ctx)

            # Check if hook used respond_* helpers
            response_meta = None
            if hasattr(result_ctx, "hook_outputs") and isinstance(result_ctx.hook_outputs, dict):
                response_meta = result_ctx.hook_outputs.get("_response")

            if isinstance(response_meta, dict) and "action" in response_meta:
                output = dict(response_meta)
                output["context"] = json.loads(serialize_context(result_ctx))
            else:
                # Backward compatible: default to continue
                output = {
                    "action": "continue",
                    "context": json.loads(serialize_context(result_ctx)),
                }

            return json.dumps(output)

        except Exception as e:
            return json.dumps({"action": "error", "error": str(e)})


def run_hook(hook_class: Type[StatelessHook], input_json: str) -> str:
    """Run a hook class with JSON input.

    Convenience function that instantiates the hook class and runs it.

    Args:
        hook_class: StatelessHook subclass to instantiate
        input_json: JSON input string

    Returns:
        JSON output string

    Example:
        >>> output = run_hook(MyHook, '{"tool_name": "Read", ...}')
    """
    hook = hook_class()
    return hook.run(input_json)


# =============================================================================
# Testing
# =============================================================================

if __name__ == "__main__":
    # Quick manual test
    print("Testing stateless_hook.py...")

    class TestHook(StatelessHook):
        def process(self, ctx):
            return self.update_context(ctx, tool_result="test passed")

    # Test direct processing
    ctx = create_context("sess_123", "Read", {"file_path": "test.py"})
    hook = TestHook()
    result = hook.process(ctx)
    print(f"Direct process: {result.tool_result}")

    # Test JSON protocol
    input_json = json.dumps(
        {"session_id": "sess_456", "tool_name": "Read", "tool_input": {"file_path": "test.py"}}
    )
    output = run_hook(TestHook, input_json)
    output_data = json.loads(output)
    print(f"JSON protocol: {output_data['action']}, {output_data['context']['tool_result']}")

    print("\nAll tests passed!")
