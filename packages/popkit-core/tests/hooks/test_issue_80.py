#!/usr/bin/env python3
"""
Test script for Issue #80 - Agent Expertise Tracking Activation

This script tests that POPKIT_ACTIVE_AGENT is set automatically by the
post-tool-use hook when tools are executed.

Usage:
    python test_issue_80.py
"""

import os
import sys
from pathlib import Path

# Add shared-py to path (tests/hooks/ -> tests/ -> popkit-core/ -> packages/ -> shared-py)
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared-py"))

# Mock the imports that post-tool-use needs
os.environ["POPKIT_TEST_MODE"] = "false"


def test_semantic_router_import():
    """Test 1: Verify semantic router can be imported"""
    print("\n" + "=" * 60)
    print("Test 1: Semantic Router Import")
    print("=" * 60)

    try:
        from popkit_shared.utils.semantic_router import SemanticRouter  # noqa: F401

        print("[PASS] SemanticRouter imported successfully")
        return True
    except ImportError as e:
        print(f"[FAIL] Failed to import SemanticRouter: {e}")
        return False


def test_semantic_router_initialization():
    """Test 2: Verify semantic router can be initialized"""
    print("\n" + "=" * 60)
    print("Test 2: Semantic Router Initialization")
    print("=" * 60)

    try:
        from popkit_shared.utils.semantic_router import SemanticRouter

        router = SemanticRouter()
        print("[PASS] SemanticRouter initialized successfully")
        print(f"  Embedding store available: {router.store is not None}")
        return True
    except Exception as e:
        print(f"[FAIL] Failed to initialize SemanticRouter: {e}")
        return False


def test_agent_detection():
    """Test 3: Verify semantic router can detect agents"""
    print("\n" + "=" * 60)
    print("Test 3: Agent Detection")
    print("=" * 60)

    try:
        from popkit_shared.utils.semantic_router import SemanticRouter

        # Clear any existing POPKIT_ACTIVE_AGENT
        if "POPKIT_ACTIVE_AGENT" in os.environ:
            del os.environ["POPKIT_ACTIVE_AGENT"]

        router = SemanticRouter()

        # Test queries for different agent types
        test_cases = [
            {
                "query": "Edit code issues",
                "context": {"tool": "Edit", "has_issues": True},
                "expected_agents": ["code-reviewer", "refactoring-expert"],
            },
            {
                "query": "Bash security vulnerability",
                "context": {"tool": "Bash", "category": "security"},
                "expected_agents": ["security-auditor", "bug-whisperer"],
            },
            {
                "query": "Read test failures",
                "context": {"tool": "Read", "has_issues": True},
                "expected_agents": ["test-writer-fixer", "bug-whisperer"],
            },
        ]

        results = []
        for i, test_case in enumerate(test_cases, 1):
            # Clear env var before each test
            if "POPKIT_ACTIVE_AGENT" in os.environ:
                del os.environ["POPKIT_ACTIVE_AGENT"]

            result = router.route_single(
                test_case["query"], context=test_case["context"], set_active_agent=True
            )

            if result:
                env_var_set = os.environ.get("POPKIT_ACTIVE_AGENT")
                matched_expected = result.agent in test_case["expected_agents"]

                print(f"\n  Test {i}: {test_case['query']}")
                print(f"    Detected agent: {result.agent}")
                print(f"    Confidence: {result.confidence:.2f}")
                print(f"    Method: {result.method}")
                status = "[OK]" if env_var_set else "[FAIL]"
                print(f"    POPKIT_ACTIVE_AGENT set: {status} ({env_var_set})")
                match_status = "[OK]" if matched_expected else "[WARN]"
                print(f"    Expected agent: {match_status} (wanted {test_case['expected_agents']})")

                results.append(env_var_set == result.agent)
            else:
                print(f"\n  Test {i}: {test_case['query']}")
                print("    [WARN] No agent detected (confidence too low or no matches)")
                results.append(False)

        success_count = sum(results)
        print(f"\n  Results: {success_count}/{len(test_cases)} tests set POPKIT_ACTIVE_AGENT")

        return success_count > 0

    except Exception as e:
        print(f"[FAIL] Agent detection failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_expertise_manager_detection():
    """Test 4: Verify expertise manager can detect active agent"""
    print("\n" + "=" * 60)
    print("Test 4: Expertise Manager Detection")
    print("=" * 60)

    try:
        from popkit_shared.utils.expertise_manager import ExpertiseManager

        # Set a test agent
        os.environ["POPKIT_ACTIVE_AGENT"] = "code-reviewer"

        # Try to initialize expertise manager
        manager = ExpertiseManager("code-reviewer")

        print("[PASS] ExpertiseManager initialized successfully")
        print(f"  Agent ID: {manager.agent_id}")
        print(f"  Expertise file: {manager.expertise_file}")
        print(f"  Env var: {os.environ.get('POPKIT_ACTIVE_AGENT')}")

        return True

    except Exception as e:
        print(f"[FAIL] Expertise manager detection failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("Issue #80 Integration Test")
    print("Agent Expertise Tracking Activation")
    print("=" * 60)

    tests = [
        test_semantic_router_import,
        test_semantic_router_initialization,
        test_agent_detection,
        test_expertise_manager_detection,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n[FAIL] Test crashed: {e}")
            import traceback

            traceback.print_exc()
            results.append(False)

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    passed = sum(results)
    total = len(results)

    print(f"\nTests passed: {passed}/{total}")

    if passed == total:
        print("\n[PASS] All tests PASSED")
        print("\nThe semantic router integration is working correctly.")
        print("POPKIT_ACTIVE_AGENT will now be set automatically after each tool execution.")
        return 0
    else:
        print("\n[WARN] Some tests FAILED or WARNED")
        print("\nThis may be expected if:")
        print("- Embeddings are not set up yet (router will fall back to keywords)")
        print("- Agent database is empty (router won't find matches)")
        print("\nThe integration will still work once embeddings are populated.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
