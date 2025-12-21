#!/usr/bin/env python3
"""
Phase 5 Testing: Verify all critical imports work from popkit_shared package
"""

import sys
from pathlib import Path

# Add shared package to path
shared_path = Path(__file__).parent / "packages" / "shared-py"
sys.path.insert(0, str(shared_path))

def test_imports():
    """Test critical imports from popkit_shared"""
    results = []

    # Test 1: Context Carrier
    try:
        from popkit_shared.utils.context_carrier import HookContext
        results.append(("context_carrier.HookContext", "PASS"))
    except ImportError as e:
        results.append(("context_carrier.HookContext", f"FAIL: {e}"))

    # Test 2: Message Builder (functions)
    try:
        from popkit_shared.utils.message_builder import build_user_message
        results.append(("message_builder.build_user_message", "PASS"))
    except ImportError as e:
        results.append(("message_builder.build_user_message", f"FAIL: {e}"))

    # Test 3: Skill Context
    try:
        from popkit_shared.utils.skill_context import SkillContext
        results.append(("skill_context.SkillContext", "PASS"))
    except ImportError as e:
        results.append(("skill_context.SkillContext", f"FAIL: {e}"))

    # Test 4: Voyage Client
    try:
        from popkit_shared.utils.voyage_client import VoyageClient
        results.append(("voyage_client.VoyageClient", "PASS"))
    except ImportError as e:
        results.append(("voyage_client.VoyageClient", f"FAIL: {e}"))

    # Test 5: Workflow Engine
    try:
        from popkit_shared.utils.workflow_engine import FileWorkflowEngine
        results.append(("workflow_engine.FileWorkflowEngine", "PASS"))
    except ImportError as e:
        results.append(("workflow_engine.FileWorkflowEngine", f"FAIL: {e}"))

    # Test 6: Cloudflare API
    try:
        from popkit_shared.utils.cloudflare_api import Zone
        results.append(("cloudflare_api.Zone", "PASS"))
    except ImportError as e:
        results.append(("cloudflare_api.Zone", f"FAIL: {e}"))

    # Test 7: GitHub Issues
    try:
        from popkit_shared.utils.github_issues import fetch_issue
        results.append(("github_issues.fetch_issue", "PASS"))
    except ImportError as e:
        results.append(("github_issues.fetch_issue", f"FAIL: {e}"))

    # Print results
    print("\n=== PopKit Shared Package Import Tests ===\n")
    passed = 0
    failed = 0

    for module, status in results:
        if status == "PASS":
            print(f"[PASS] {module}")
            passed += 1
        else:
            print(f"[FAIL] {module}: {status}")
            failed += 1

    print(f"\n=== Summary ===")
    print(f"Passed: {passed}/{len(results)}")
    print(f"Failed: {failed}/{len(results)}")

    return failed == 0

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
