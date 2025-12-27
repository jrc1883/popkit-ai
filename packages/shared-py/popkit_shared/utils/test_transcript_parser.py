"""
Tests for TranscriptParser

Run with: python test_transcript_parser.py
"""

import json
from pathlib import Path
from transcript_parser import TranscriptParser, TokenUsage


def test_parser_creation():
    """Test that parser can be created and parses file"""
    # Use current session transcript
    transcript_path = Path.home() / '.claude' / 'projects' / 'C--Users-Josep-OneDrive-Documents-ElShaddai-apps-popkit' / 'ad19212c-7de5-4b0f-8a50-0d311410b902.jsonl'

    if not transcript_path.exists():
        print(f"SKIP: Transcript not found: {transcript_path}")
        return

    parser = TranscriptParser(str(transcript_path))
    print(f"✓ Parser created successfully")
    print(f"  Entries parsed: {len(parser.entries)}")
    assert len(parser.entries) > 0, "Should have parsed entries"


def test_get_all_tool_uses():
    """Test extracting all tool uses from transcript"""
    transcript_path = Path.home() / '.claude' / 'projects' / 'C--Users-Josep-OneDrive-Documents-ElShaddai-apps-popkit' / 'ad19212c-7de5-4b0f-8a50-0d311410b902.jsonl'

    if not transcript_path.exists():
        print(f"SKIP: Transcript not found")
        return

    parser = TranscriptParser(str(transcript_path))
    tool_uses = parser.get_all_tool_uses()

    print(f"✓ Found {len(tool_uses)} tool uses")

    if tool_uses:
        # Show first 3
        for i, tool in enumerate(tool_uses[:3], 1):
            print(f"  {i}. {tool['tool_name']}: {tool['tool_use_id']}")


def test_get_total_token_usage():
    """Test total token calculation"""
    transcript_path = Path.home() / '.claude' / 'projects' / 'C--Users-Josep-OneDrive-Documents-ElShaddai-apps-popkit' / 'ad19212c-7de5-4b0f-8a50-0d311410b902.jsonl'

    if not transcript_path.exists():
        print(f"SKIP: Transcript not found")
        return

    parser = TranscriptParser(str(transcript_path))
    usage = parser.get_total_token_usage()

    print(f"✓ Total token usage calculated")
    print(f"  Input tokens: {usage.input_tokens:,}")
    print(f"  Output tokens: {usage.output_tokens:,}")
    print(f"  Cache writes: {usage.cache_creation_input_tokens:,}")
    print(f"  Cache reads: {usage.cache_read_input_tokens:,}")
    print(f"  Total: {usage.total_tokens:,}")

    # Calculate cost
    cost = parser.calculate_cost(usage)
    print(f"  Estimated cost: ${cost:.3f}")

    assert usage.total_tokens > 0, "Should have token usage"


def test_get_reasoning_for_tool():
    """Test extracting reasoning for a specific tool use"""
    transcript_path = Path.home() / '.claude' / 'projects' / 'C--Users-Josep-OneDrive-Documents-ElShaddai-apps-popkit' / 'ad19212c-7de5-4b0f-8a50-0d311410b902.jsonl'

    if not transcript_path.exists():
        print(f"SKIP: Transcript not found")
        return

    parser = TranscriptParser(str(transcript_path))

    # Get a recent tool use
    tool_uses = parser.get_all_tool_uses()
    if not tool_uses:
        print("SKIP: No tool uses found")
        return

    # Test with last tool use
    last_tool = tool_uses[-1]
    tool_use_id = last_tool['tool_use_id']

    reasoning = parser.get_reasoning_before_tool(tool_use_id)

    print(f"✓ Reasoning extracted for {last_tool['tool_name']}")
    print(f"  Tool use ID: {tool_use_id}")
    print(f"  Text blocks: {len(reasoning['text'])}")
    print(f"  Thinking blocks: {len(reasoning['thinking'])}")

    if reasoning['text']:
        print(f"  Text preview: {reasoning['text'][0][:100]}...")

    if reasoning['thinking']:
        print(f"  Thinking preview: {reasoning['thinking'][0][:100]}...")


def test_get_token_usage_for_tool():
    """Test getting token usage for specific tool"""
    transcript_path = Path.home() / '.claude' / 'projects' / 'C--Users-Josep-OneDrive-Documents-ElShaddai-apps-popkit' / 'ad19212c-7de5-4b0f-8a50-0d311410b902.jsonl'

    if not transcript_path.exists():
        print(f"SKIP: Transcript not found")
        return

    parser = TranscriptParser(str(transcript_path))

    # Get a tool use
    tool_uses = parser.get_all_tool_uses()
    if not tool_uses:
        print("SKIP: No tool uses found")
        return

    # Test with last tool
    last_tool = tool_uses[-1]
    tool_use_id = last_tool['tool_use_id']

    usage = parser.get_token_usage_for_tool(tool_use_id)

    if usage:
        print(f"✓ Token usage for {last_tool['tool_name']}")
        print(f"  Input: {usage.input_tokens}")
        print(f"  Output: {usage.output_tokens}")
        print(f"  Total: {usage.total_tokens}")
        cost = parser.calculate_cost(usage)
        print(f"  Cost: ${cost:.4f}")
    else:
        print(f"✗ No usage data found for tool")


def test_get_assistant_messages():
    """Test extracting all assistant messages"""
    transcript_path = Path.home() / '.claude' / 'projects' / 'C--Users-Josep-OneDrive-Documents-ElShaddai-apps-popkit' / 'ad19212c-7de5-4b0f-8a50-0d311410b902.jsonl'

    if not transcript_path.exists():
        print(f"SKIP: Transcript not found")
        return

    parser = TranscriptParser(str(transcript_path))
    messages = parser.get_assistant_messages()

    print(f"✓ Found {len(messages)} assistant messages")

    # Show distribution
    with_text = sum(1 for m in messages if m.text_blocks)
    with_thinking = sum(1 for m in messages if m.thinking_blocks)
    with_tools = sum(1 for m in messages if m.tool_uses)

    print(f"  With text: {with_text}")
    print(f"  With thinking: {with_thinking}")
    print(f"  With tool uses: {with_tools}")


def run_all_tests():
    """Run all tests"""
    tests = [
        ("Parser Creation", test_parser_creation),
        ("Get All Tool Uses", test_get_all_tool_uses),
        ("Total Token Usage", test_get_total_token_usage),
        ("Reasoning Extraction", test_get_reasoning_for_tool),
        ("Tool Token Usage", test_get_token_usage_for_tool),
        ("Assistant Messages", test_get_assistant_messages),
    ]

    print("=" * 60)
    print("TRANSCRIPT PARSER TESTS")
    print("=" * 60)
    print()

    passed = 0
    failed = 0

    for name, test_func in tests:
        print(f"Test: {name}")
        print("-" * 40)
        try:
            test_func()
            print()
            passed += 1
        except AssertionError as e:
            print(f"✗ FAILED: {e}")
            print()
            failed += 1
        except Exception as e:
            print(f"✗ ERROR: {e}")
            print()
            failed += 1

    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)


if __name__ == "__main__":
    run_all_tests()
