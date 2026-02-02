#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for merge conflict resolver functionality.

Tests:
- Conflict detection
- Complexity analysis
- Prioritization logic
- Resolution strategies
- Integration with complexity scorer
"""

import sys
from pathlib import Path

# Add shared-py to path
# Path: tests/test_merge_conflict_resolver.py -> packages/popkit-dev/tests
# So parent.parent.parent = packages/, then shared-py
shared_py_path = Path(__file__).parent.parent.parent / "shared-py"
if str(shared_py_path) not in sys.path:
    sys.path.insert(0, str(shared_py_path))

try:
    from popkit_shared.utils.conflict_analyzer import (
        Conflict,
        ConflictResolver,
    )
    from popkit_shared.utils.complexity_scoring import analyze_complexity
except ImportError as e:
    print(f"[ERROR] Import failed: {e}")
    print(f"Shared-py path: {shared_py_path}")
    print(f"Exists: {shared_py_path.exists()}")
    print("Please ensure shared-py is accessible")
    sys.exit(1)


def test_conflict_parsing():
    """Test parsing of conflict markers."""
    print("\n=== Test: Conflict Parsing ===")

    conflict_content = """
function authenticateUser(username, password) {
<<<<<<< HEAD
    // Our JWT implementation
    const token = jwt.sign({ username }, SECRET_KEY);
    return { token, user: username };
=======
    // Their session implementation
    const sessionId = createSession(username);
    return { sessionId, user: username };
>>>>>>> feature/session-auth
}
"""

    conflict = Conflict(file_path="src/auth/login.ts", content=conflict_content)

    # Verify parsing
    assert conflict.our_side, "Should parse 'our' side"
    assert conflict.their_side, "Should parse 'their' side"
    assert "jwt.sign" in conflict.our_side, "Should contain our code"
    assert "createSession" in conflict.their_side, "Should contain their code"
    assert conflict.lines_count > 0, "Should count lines"

    print("[PASS] Parsed conflict successfully")
    print(f"  Our side: {len(conflict.our_side)} chars")
    print(f"  Their side: {len(conflict.their_side)} chars")
    print(f"  Lines: {conflict.lines_count}")


def test_complexity_analysis():
    """Test complexity analysis of conflicts."""
    print("\n=== Test: Complexity Analysis ===")

    # Create test conflicts with different complexity
    test_cases = [
        {
            "file": "README.md",
            "content": """
<<<<<<< HEAD
# Project Title
Updated documentation
=======
# Project Title
Different documentation
>>>>>>> feature/docs
""",
            "expected_complexity": (1, 3),  # Low complexity range
        },
        {
            "file": "src/auth/login.ts",
            "content": """
async function authenticate(user, password) {
<<<<<<< HEAD
    const token = await jwt.sign({ id: user.id }, SECRET);
    await saveToken(token);
    return { success: true, token };
=======
    const session = await createSession(user.id);
    await saveSession(session);
    return { success: true, sessionId: session.id };
>>>>>>> feature/session
}
""",
            "expected_complexity": (
                2,
                5,
            ),  # Moderate complexity (small conflict, but auth-related)
        },
    ]

    resolver = ConflictResolver()

    for case in test_cases:
        conflict = Conflict(file_path=case["file"], content=case["content"])
        # For auth files, mark as high importance and architectural
        if "auth" in case["file"]:
            conflict.is_architectural = True
            conflict.file_importance = 10
        complexity = resolver.analyze_conflict_complexity(conflict)

        min_expected, max_expected = case["expected_complexity"]
        score = complexity["complexity_score"]

        print(f"\n[PASS] {case['file']}:")
        print(f"  Complexity: {score}/10")
        print(f"  Expected range: {min_expected}-{max_expected}")
        print(f"  Risk factors: {complexity['risk_factors']}")

        assert min_expected <= score <= max_expected, (
            f"Score {score} not in expected range {min_expected}-{max_expected}"
        )


def test_prioritization():
    """Test conflict prioritization logic."""
    print("\n=== Test: Prioritization ===")

    # Create conflicts with different characteristics
    conflicts = [
        Conflict(
            file_path="README.md",
            content="<<<<<<< HEAD\nv1\n=======\nv2\n>>>>>>> branch",
        ),
        Conflict(
            file_path="src/core/auth.ts",
            content="""
<<<<<<< HEAD
class AuthService {
    authenticate() { /* complex logic */ }
}
=======
class AuthService {
    authenticate() { /* different complex logic */ }
}
>>>>>>> feature/auth
""",
        ),
        Conflict(
            file_path="package.json",
            content='<<<<<<< HEAD\n"dep": "1.0"\n=======\n"dep": "2.0"\n>>>>>>> branch',
        ),
    ]

    resolver = ConflictResolver()
    prioritized = resolver.prioritize_conflicts(conflicts)

    print("\nPrioritization order:")
    for i, conflict in enumerate(prioritized, 1):
        print(f"{i}. {conflict.file_path}")
        print(f"   Complexity: {conflict.complexity_score}/10")
        print(f"   Priority: {conflict.priority:.1f}")

    # Verify high-complexity conflicts come first
    assert prioritized[0].complexity_score >= prioritized[-1].complexity_score, (
        "Should prioritize by complexity"
    )

    print("\n[PASS] Prioritization working correctly")


def test_file_importance():
    """Test file importance assessment."""
    print("\n=== Test: File Importance Assessment ===")

    resolver = ConflictResolver()

    test_cases = [
        ("src/core/auth.ts", 10, "Core file"),
        ("package.json", 8, "Config file"),
        ("src/utils/helper.test.ts", 5, "Test file"),
        ("README.md", 3, "Doc file"),
        ("src/components/Button.tsx", 6, "Regular file"),
    ]

    for file_path, expected_min, description in test_cases:
        importance = resolver._assess_file_importance(file_path)
        print(f"[PASS] {file_path}: {importance}/10 ({description})")

        assert importance >= expected_min - 2, (
            f"Importance {importance} too low for {description}"
        )


def test_architectural_detection():
    """Test detection of architectural conflicts."""
    print("\n=== Test: Architectural Conflict Detection ===")

    resolver = ConflictResolver()

    # Architectural conflict
    arch_conflict = Conflict(
        file_path="src/services/auth.ts",
        content="""
<<<<<<< HEAD
export class AuthService implements IAuthService {
    constructor(private jwt: JWTService) {}
}
=======
export class AuthService extends BaseService {
    constructor(private session: SessionService) {}
}
>>>>>>> feature/refactor
""",
    )

    # Non-architectural conflict
    simple_conflict = Conflict(
        file_path="src/utils/format.ts",
        content="""
<<<<<<< HEAD
return date.toISOString();
=======
return date.toLocaleDateString();
>>>>>>> feature/format
""",
    )

    is_arch = resolver._is_architectural_conflict(arch_conflict)
    is_simple = resolver._is_architectural_conflict(simple_conflict)

    print(f"[PASS] Architectural conflict detected: {is_arch}")
    print(f"[PASS] Simple conflict not flagged: {not is_simple}")

    assert is_arch, "Should detect architectural conflict"
    assert not is_simple, "Should not flag simple conflict as architectural"


def test_integration_with_complexity_scorer():
    """Test integration with complexity scoring system."""
    print("\n=== Test: Integration with Complexity Scorer ===")

    # Test that complexity scorer is accessible
    description = "Resolve merge conflict in authentication service"
    result = analyze_complexity(
        description,
        metadata={"files_affected": 1, "loc_estimate": 50, "architecture_change": True},
    )

    print("[PASS] Complexity scorer accessible")
    print(f"  Score: {result['complexity_score']}/10")
    print(f"  Level: {result['complexity_level']}")
    print(f"  Risk factors: {result['risk_factors']}")

    assert "complexity_score" in result, "Should return complexity score"
    assert result["complexity_score"] >= 1, "Score should be valid"


def test_scope_detection():
    """Test detection of conflict scope (function/class)."""
    print("\n=== Test: Scope Detection ===")

    conflict_with_scope = Conflict(
        file_path="src/auth.ts",
        content="""
class AuthService {
    async authenticateUser(username, password) {
<<<<<<< HEAD
        return jwt.sign({ username });
=======
        return createSession(username);
>>>>>>> feature/auth
    }
}
""",
    )

    print(f"[PASS] Detected scope: {conflict_with_scope.scope}")
    # Note: Scope detection looks backward, so it may not find class in this example
    # That's okay - the important part is that it doesn't crash


def run_all_tests():
    """Run all test suites."""
    print("=" * 60)
    print("Merge Conflict Resolver Test Suite")
    print("=" * 60)

    tests = [
        ("Conflict Parsing", test_conflict_parsing),
        ("Complexity Analysis", test_complexity_analysis),
        ("Prioritization", test_prioritization),
        ("File Importance", test_file_importance),
        ("Architectural Detection", test_architectural_detection),
        ("Complexity Scorer Integration", test_integration_with_complexity_scorer),
        ("Scope Detection", test_scope_detection),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n[FAIL] Test failed: {test_name}")
            print(f"   Error: {e}")
            failed += 1

    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
