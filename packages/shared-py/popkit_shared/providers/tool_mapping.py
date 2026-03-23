#!/usr/bin/env python3
"""
Tool Category Mapping Definitions

Maps abstract tool categories to provider-specific tool names.
Each provider adapter uses these mappings to translate PopKit's
universal manifest declarations into provider-native configurations.

Part of the PopKit v2.0 provider-agnostic architecture.
"""

from .base import ToolCategory, ToolMapping

# =============================================================================
# Claude Code Tool Mappings
# =============================================================================

CLAUDE_CODE_MAPPINGS: list[ToolMapping] = [
    ToolMapping(ToolCategory.FILE_READ, "Read"),
    ToolMapping(ToolCategory.FILE_WRITE, "Write"),
    ToolMapping(ToolCategory.FILE_EDIT, "Edit"),
    ToolMapping(ToolCategory.FILE_SEARCH, "Glob"),
    ToolMapping(ToolCategory.CODE_SEARCH, "Grep"),
    ToolMapping(ToolCategory.CODE_EXECUTE, "Bash"),
    ToolMapping(ToolCategory.SHELL, "Bash"),
    ToolMapping(ToolCategory.SHELL_BACKGROUND, "Bash", {"run_in_background": True}),
    ToolMapping(ToolCategory.AGENT_SPAWN, "Agent"),
    ToolMapping(ToolCategory.AGENT_MESSAGE, "SendMessage"),
    ToolMapping(ToolCategory.TASK_MANAGE, "TaskCreate"),
    ToolMapping(ToolCategory.WEB_FETCH, "WebFetch"),
    ToolMapping(ToolCategory.WEB_SEARCH, "WebSearch"),
    ToolMapping(ToolCategory.NOTEBOOK_EDIT, "NotebookEdit"),
]

# =============================================================================
# Generic MCP Tool Mappings
# =============================================================================

GENERIC_MCP_MAPPINGS: list[ToolMapping] = [
    ToolMapping(ToolCategory.FILE_READ, "popkit/read_file"),
    ToolMapping(ToolCategory.FILE_WRITE, "popkit/write_file"),
    ToolMapping(ToolCategory.FILE_EDIT, "popkit/edit_file"),
    ToolMapping(ToolCategory.FILE_SEARCH, "popkit/search_files"),
    ToolMapping(ToolCategory.CODE_SEARCH, "popkit/search_code"),
    ToolMapping(ToolCategory.CODE_EXECUTE, "popkit/execute"),
    ToolMapping(ToolCategory.SHELL, "popkit/shell"),
    ToolMapping(ToolCategory.SHELL_BACKGROUND, "popkit/shell_background"),
    ToolMapping(ToolCategory.WEB_FETCH, "popkit/web_fetch"),
]

# =============================================================================
# Cursor Tool Mappings (MCP-based)
# =============================================================================

CURSOR_MAPPINGS: list[ToolMapping] = [
    ToolMapping(ToolCategory.FILE_READ, "read_file"),
    ToolMapping(ToolCategory.FILE_WRITE, "write_file"),
    ToolMapping(ToolCategory.FILE_EDIT, "edit_file"),
    ToolMapping(ToolCategory.FILE_SEARCH, "search_files"),
    ToolMapping(ToolCategory.CODE_SEARCH, "search_code"),
    ToolMapping(ToolCategory.CODE_EXECUTE, "run_terminal_cmd"),
    ToolMapping(ToolCategory.SHELL, "run_terminal_cmd"),
    ToolMapping(ToolCategory.WEB_FETCH, "web_fetch"),
]

# =============================================================================
# Codex CLI Tool Mappings
# =============================================================================

CODEX_MAPPINGS: list[ToolMapping] = [
    ToolMapping(ToolCategory.FILE_READ, "Read"),
    ToolMapping(ToolCategory.FILE_WRITE, "Write"),
    ToolMapping(ToolCategory.FILE_EDIT, "Edit"),
    ToolMapping(ToolCategory.FILE_SEARCH, "Glob"),
    ToolMapping(ToolCategory.CODE_SEARCH, "Grep"),
    ToolMapping(ToolCategory.CODE_EXECUTE, "Bash"),
    ToolMapping(ToolCategory.SHELL, "Bash"),
    ToolMapping(ToolCategory.SHELL_BACKGROUND, "Bash", {"run_in_background": True}),
    ToolMapping(ToolCategory.WEB_FETCH, "web_fetch"),
]

# =============================================================================
# GitHub Copilot Tool Mappings (MCP-based, similar to Cursor)
# =============================================================================

COPILOT_MAPPINGS: list[ToolMapping] = [
    ToolMapping(ToolCategory.FILE_READ, "read_file"),
    ToolMapping(ToolCategory.FILE_WRITE, "write_file"),
    ToolMapping(ToolCategory.FILE_EDIT, "edit_file"),
    ToolMapping(ToolCategory.FILE_SEARCH, "search_files"),
    ToolMapping(ToolCategory.CODE_SEARCH, "search_code"),
    ToolMapping(ToolCategory.CODE_EXECUTE, "run_terminal_cmd"),
    ToolMapping(ToolCategory.SHELL, "run_terminal_cmd"),
    ToolMapping(ToolCategory.WEB_FETCH, "web_fetch"),
]

# =============================================================================
# Helper Functions
# =============================================================================


def get_mappings_for_provider(provider_name: str) -> list[ToolMapping]:
    """Get tool mappings for a specific provider.

    Args:
        provider_name: Provider identifier

    Returns:
        List of ToolMapping instances
    """
    registry: dict[str, list[ToolMapping]] = {
        "claude-code": CLAUDE_CODE_MAPPINGS,
        "generic-mcp": GENERIC_MCP_MAPPINGS,
        "cursor": CURSOR_MAPPINGS,
        "codex": CODEX_MAPPINGS,
        "copilot": COPILOT_MAPPINGS,
    }
    return registry.get(provider_name, [])


def translate_tools(abstract_tools: list[str], provider_name: str) -> list[str]:
    """Translate abstract tool category names to provider-specific names.

    Args:
        abstract_tools: List of ToolCategory value strings (e.g., ["file_read", "shell"])
        provider_name: Target provider identifier

    Returns:
        List of provider-specific tool names
    """
    mappings = get_mappings_for_provider(provider_name)
    mapping_dict = {m.category.value: m.provider_name for m in mappings}

    result = []
    for tool in abstract_tools:
        if tool in mapping_dict:
            provider_tool = mapping_dict[tool]
            if provider_tool not in result:
                result.append(provider_tool)
        else:
            # Pass through unknown tools as-is (provider-specific tools)
            if tool not in result:
                result.append(tool)

    return result
