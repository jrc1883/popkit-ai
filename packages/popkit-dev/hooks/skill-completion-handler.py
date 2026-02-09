#!/usr/bin/env python3
"""
Skill Completion Handler (PostToolUse Hook)

This hook runs after any Skill tool invocation and checks if the skill
output contains PopKit Way instructions for AskUserQuestion.

If found, it PROGRAMMATICALLY invokes AskUserQuestion, making it 100%
reliable instead of relying on Claude's instruction-following.

Input (stdin): JSON with skill execution data
Output (stdout): JSON with hook action (ask_user_question or passthrough)

Protocol:
- type: "ask_user_question" - Programmatically invoke AskUserQuestion
- type: "passthrough" - No action needed
"""

import json
import re
import sys
from typing import Any, Dict, Optional


def extract_ask_user_question_config(skill_output: str) -> Optional[Dict[str, Any]]:
    """
    Extract AskUserQuestion configuration from skill output.

    Looks for the marker:
    **IMPORTANT - The PopKit Way**: You MUST now use the AskUserQuestion tool.

    Then extracts the JSON configuration from the code block.

    Args:
        skill_output: The markdown output from the skill

    Returns:
        AskUserQuestion config dict or None if not found
    """
    # Check for PopKit Way marker
    if "**IMPORTANT - The PopKit Way**" not in skill_output:
        return None

    if "You MUST now use the AskUserQuestion tool" not in skill_output:
        return None

    # Extract JSON configuration from code block
    # Pattern: ```json\n{...}\n```
    json_pattern = r"```json\s*\n(.*?)\n```"
    matches = re.findall(json_pattern, skill_output, re.DOTALL)

    if not matches:
        return None

    # Get the last JSON block (most likely to be the AskUserQuestion config)
    json_str = matches[-1]

    try:
        config = json.loads(json_str)

        # Validate it has the expected structure
        if "questions" in config and isinstance(config["questions"], list):
            return config

    except json.JSONDecodeError as e:
        print(f"[WARN] Failed to parse AskUserQuestion JSON: {e}", file=sys.stderr)
        return None

    return None


def handle_skill_completion(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle skill completion by checking for AskUserQuestion instructions.

    Args:
        input_data: Hook input data from Claude Code

    Returns:
        Hook response: either ask_user_question or passthrough
    """
    # Extract skill output
    # The exact structure depends on Claude Code's PostToolUse hook format
    # This may need adjustment based on actual format

    tool_name = input_data.get("tool", "")
    tool_result = input_data.get("result", "")

    # Only process Skill tool invocations
    if tool_name != "Skill":
        return {"type": "passthrough"}

    # Check if this is a string result (skill output)
    if not isinstance(tool_result, str):
        return {"type": "passthrough"}

    # Try to extract AskUserQuestion configuration
    ask_config = extract_ask_user_question_config(tool_result)

    if ask_config:
        # Found PopKit Way instructions - invoke AskUserQuestion programmatically
        return {"type": "ask_user_question", "questions": ask_config["questions"]}

    # No AskUserQuestion instructions found - pass through
    return {"type": "passthrough"}


def main():
    """Main entry point for hook script."""
    try:
        # Read input from stdin
        input_data = json.loads(sys.stdin.read())

        # Process the hook
        response = handle_skill_completion(input_data)

        # Output response to stdout
        print(json.dumps(response))
        sys.exit(0)

    except Exception as e:
        # Log error but don't fail the hook
        print(f"[ERROR] Skill completion handler failed: {e}", file=sys.stderr)

        # Passthrough on error (fail gracefully)
        print(json.dumps({"type": "passthrough"}))
        sys.exit(0)


if __name__ == "__main__":
    main()
