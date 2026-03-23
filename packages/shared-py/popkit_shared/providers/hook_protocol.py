#!/usr/bin/env python3
"""
PopKit-Native Hook Response Protocol

Defines a provider-agnostic hook response format that adapters translate
to their provider's specific format. Claude Code adapter passes through
unchanged since PopKit's format originated from Claude Code's protocol.

Part of the PopKit v2.0 provider-agnostic architecture.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class HookAction(str, Enum):
    """Universal hook response actions."""

    CONTINUE = "continue"
    DENY = "deny"
    ASK = "ask"
    ERROR = "error"


@dataclass
class HookResponse:
    """Provider-agnostic hook response.

    This is the format that PopKit hooks produce. Each provider adapter
    translates this into its native format.

    Attributes:
        action: What to do (continue, deny, ask, error)
        message: Optional message to display to user
        modified_input: Modified tool input (for input-rewriting hooks)
        metadata: Additional provider-specific metadata
        error: Error message if action is ERROR
    """

    action: HookAction = HookAction.CONTINUE
    message: Optional[str] = None
    modified_input: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None

    def to_claude_code(self) -> Dict[str, Any]:
        """Convert to Claude Code hook response format.

        Claude Code expects: {"action": "continue|deny|ask", ...}
        This is a direct passthrough since PopKit's protocol matches.

        Returns:
            Dict compatible with Claude Code hook protocol
        """
        response: Dict[str, Any] = {"action": self.action.value}

        if self.message:
            response["message"] = self.message

        if self.modified_input is not None:
            response["tool_input"] = self.modified_input

        if self.error:
            response["error"] = self.error

        return response

    def to_generic(self) -> Dict[str, Any]:
        """Convert to generic JSON response format.

        For providers that don't have a native hook protocol,
        this provides a standardized JSON format.

        Returns:
            Dict with universal hook response fields
        """
        response: Dict[str, Any] = {
            "action": self.action.value,
            "provider": "popkit",
            "version": "2.0",
        }

        if self.message:
            response["message"] = self.message

        if self.modified_input is not None:
            response["modified_input"] = self.modified_input

        if self.error:
            response["error"] = self.error

        if self.metadata:
            response["metadata"] = self.metadata

        return response

    def for_provider(self, provider_name: str) -> Dict[str, Any]:
        """Convert to a specific provider's format.

        Args:
            provider_name: Provider identifier

        Returns:
            Dict in the provider's expected format
        """
        formatters = {
            "claude-code": self.to_claude_code,
            "generic-mcp": self.to_generic,
            "cursor": self.to_generic,
            "codex": self.to_generic,
        }
        formatter = formatters.get(provider_name, self.to_generic)
        return formatter()


def create_continue(message: Optional[str] = None) -> HookResponse:
    """Create a CONTINUE response."""
    return HookResponse(action=HookAction.CONTINUE, message=message)


def create_deny(message: str) -> HookResponse:
    """Create a DENY response with explanation."""
    return HookResponse(action=HookAction.DENY, message=message)


def create_ask(message: str) -> HookResponse:
    """Create an ASK response prompting user confirmation."""
    return HookResponse(action=HookAction.ASK, message=message)


def create_error(error: str) -> HookResponse:
    """Create an ERROR response."""
    return HookResponse(action=HookAction.ERROR, error=error)
