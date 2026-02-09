#!/usr/bin/env python3
"""
Test script for skill-completion-handler.py

Tests that the PostToolUse hook correctly extracts and invokes
AskUserQuestion when PopKit Way instructions are present.
"""

import json
import subprocess
import sys
from pathlib import Path


def test_extract_ask_user_question():
    """Test extraction of AskUserQuestion configuration from skill output."""

    # Sample skill output with PopKit Way instructions
    skill_output = """
# ☀️ Morning Routine Report

**Ready to Code Score**: 75/100 👍

## Score Breakdown
...

## 🎯 Next Steps

**IMPORTANT - The PopKit Way**: You MUST now use the AskUserQuestion tool to keep PopKit in control of the workflow.

Use AskUserQuestion with the following configuration:

```json
{
  "questions": [
    {
      "question": "What would you like to do next?",
      "header": "Next Action",
      "multiSelect": false,
      "options": [
        {
          "label": "Fix environment issues (Recommended)",
          "description": "Start redis, pull 3 commits"
        },
        {
          "label": "Continue: previous task",
          "description": "Pick up where you left off"
        },
        {
          "label": "Other",
          "description": "I have something else in mind"
        }
      ]
    }
  ]
}
```

**DO NOT** just end the session. You MUST invoke AskUserQuestion.
"""

    # Create test input
    test_input = {
        "tool": "Skill",
        "result": skill_output,
        "timestamp": "2026-01-09T12:00:00Z",
    }

    # Run the hook script
    script_path = Path(__file__).parent / "skill-completion-handler.py"

    result = subprocess.run(
        ["python", str(script_path)],
        input=json.dumps(test_input),
        capture_output=True,
        text=True,
        timeout=5,
    )

    # Check output
    if result.returncode != 0:
        print(f"[FAIL] Hook script failed with exit code {result.returncode}")
        print(f"STDERR: {result.stderr}")
        return False

    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"❌ Hook output is not valid JSON: {e}")
        print(f"OUTPUT: {result.stdout}")
        return False

    # Verify output structure
    if output.get("type") != "ask_user_question":
        print(f"❌ Expected type 'ask_user_question', got '{output.get('type')}'")
        return False

    if "questions" not in output:
        print("❌ Missing 'questions' in output")
        return False

    questions = output["questions"]
    if len(questions) != 1:
        print(f"❌ Expected 1 question, got {len(questions)}")
        return False

    question = questions[0]
    if question.get("question") != "What would you like to do next?":
        print(f"❌ Incorrect question text: {question.get('question')}")
        return False

    if len(question.get("options", [])) != 3:
        print(f"❌ Expected 3 options, got {len(question.get('options', []))}")
        return False

    print("[PASS] Test passed: Hook correctly extracted AskUserQuestion configuration")
    print(f"   Questions: {len(questions)}")
    print(f"   Options: {len(question.get('options', []))}")
    return True


def test_passthrough_without_marker():
    """Test that hook passes through when no PopKit Way marker is present."""

    skill_output = """
# Some Regular Skill Output

This skill doesn't use The PopKit Way pattern.
Just regular output with no AskUserQuestion.
"""

    test_input = {
        "tool": "Skill",
        "result": skill_output,
        "timestamp": "2026-01-09T12:00:00Z",
    }

    script_path = Path(__file__).parent / "skill-completion-handler.py"

    result = subprocess.run(
        ["python", str(script_path)],
        input=json.dumps(test_input),
        capture_output=True,
        text=True,
        timeout=5,
    )

    if result.returncode != 0:
        print(f"[FAIL] Hook script failed with exit code {result.returncode}")
        return False

    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"❌ Hook output is not valid JSON: {e}")
        return False

    if output.get("type") != "passthrough":
        print(f"❌ Expected 'passthrough', got '{output.get('type')}'")
        return False

    print("[PASS] Test passed: Hook correctly passes through without marker")
    return True


def test_passthrough_for_non_skill_tools():
    """Test that hook passes through for non-Skill tools."""

    test_input = {
        "tool": "Bash",  # Not a Skill
        "result": "some bash output",
        "timestamp": "2026-01-09T12:00:00Z",
    }

    script_path = Path(__file__).parent / "skill-completion-handler.py"

    result = subprocess.run(
        ["python", str(script_path)],
        input=json.dumps(test_input),
        capture_output=True,
        text=True,
        timeout=5,
    )

    if result.returncode != 0:
        print(f"[FAIL] Hook script failed with exit code {result.returncode}")
        return False

    try:
        output = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("❌ Hook output is not valid JSON")
        return False

    if output.get("type") != "passthrough":
        print(f"❌ Expected 'passthrough' for non-Skill tool, got '{output.get('type')}'")
        return False

    print("[PASS] Test passed: Hook passes through for non-Skill tools")
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing Skill Completion Handler (PostToolUse Hook)")
    print("=" * 60)
    print()

    tests = [
        ("Extract AskUserQuestion Config", test_extract_ask_user_question),
        ("Passthrough Without Marker", test_passthrough_without_marker),
        ("Passthrough for Non-Skill Tools", test_passthrough_for_non_skill_tools),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"Running: {test_name}")
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"[FAIL] Test failed with exception: {e}")
            failed += 1
        print()

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
