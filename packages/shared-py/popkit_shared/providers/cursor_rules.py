#!/usr/bin/env python3
"""
Cursor Rules Generator

Generates .cursor/rules/ files from PopKit agent definitions and hook
configurations. These rules tell Cursor's LLM how to behave when using
PopKit agents, and enforce safety checks via MCP tool calls.

Part of the PopKit v2.0 provider-agnostic architecture.
"""

from pathlib import Path
from typing import Any


def generate_safety_rules() -> str:
    """Generate the PopKit safety rules for Cursor.

    This rule instructs Cursor to call PopKit's validate_command MCP tool
    before executing any shell commands, mimicking Claude Code's hook system.

    Returns:
        Content for .cursor/rules/popkit-safety.mdc
    """
    return """---
description: PopKit safety checks for shell commands and file operations
globs: ["**/*"]
alwaysApply: true
---

# PopKit Safety Rules

Before executing any shell command via `run_terminal_cmd`, you MUST call the
`popkit/validate_command` MCP tool with the command string. Check the response:

- If `risk_level` is "blocked": DO NOT execute the command. Tell the user why.
- If `risk_level` is "caution": Warn the user about the risks before proceeding.
  List the specific warnings from the validation response.
- If `risk_level` is "safe": Proceed normally.

Example workflow:
1. User asks you to run `rm -rf /tmp/build`
2. Call `validate_command` with that command
3. Check the response risk level
4. If safe, proceed. If caution, warn first. If blocked, refuse.

## Destructive Operations

Never execute these without explicit user confirmation:
- `git push --force` or `git push -f`
- `git reset --hard`
- `rm -rf` on any directory
- `DROP TABLE`, `DROP DATABASE`, `TRUNCATE`
- Any command piped to `sh`, `bash`, or `zsh`
"""


def generate_agent_rule(
    agent_name: str,
    description: str,
    tools: list[str],
    content: str,
    tier: str = "on-demand",
) -> str:
    """Generate a Cursor rule file from a PopKit agent definition.

    Args:
        agent_name: Agent identifier
        description: Agent description
        tools: List of tool names the agent uses
        content: Full AGENT.md content (system prompt)
        tier: Agent tier (always-active or on-demand)

    Returns:
        Content for .cursor/rules/popkit-agent-{name}.mdc
    """
    # Determine glob pattern based on tier
    if tier == "always-active":
        globs = '["**/*"]'
        always_apply = "true"
    else:
        globs = '["**/*"]'
        always_apply = "false"

    tools_list = ", ".join(tools) if tools else "all available tools"

    return f"""---
description: "PopKit Agent: {agent_name} — {description[:100]}"
globs: {globs}
alwaysApply: {always_apply}
---

# PopKit Agent: {agent_name}

**Tier:** {tier}
**Tools:** {tools_list}

When the user asks you to act as the "{agent_name}" agent (or when this rule
is activated), adopt the following persona and constraints:

{content}
"""


def generate_all_rules(
    agents: list[dict[str, Any]],
    output_dir: Path,
) -> list[Path]:
    """Generate all Cursor rule files for PopKit agents.

    Args:
        agents: List of agent dicts with name, description, tools, content, tier
        output_dir: Directory to write .mdc files to

    Returns:
        List of generated file paths
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    generated = []

    # Safety rules (always generated)
    safety_path = output_dir / "popkit-safety.mdc"
    safety_path.write_text(generate_safety_rules(), encoding="utf-8")
    generated.append(safety_path)

    # Agent rules
    for agent in agents:
        rule_content = generate_agent_rule(
            agent_name=agent["name"],
            description=agent.get("description", ""),
            tools=agent.get("tools", []),
            content=agent.get("content", ""),
            tier=agent.get("tier", "on-demand"),
        )

        filename = f"popkit-agent-{agent['name']}.mdc"
        rule_path = output_dir / filename
        rule_path.write_text(rule_content, encoding="utf-8")
        generated.append(rule_path)

    return generated
