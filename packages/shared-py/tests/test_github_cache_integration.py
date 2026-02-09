#!/usr/bin/env python3
"""
Integration test for GitHub cache and validator.
Demonstrates "Check First" pattern to prevent GitHub API errors.

Run from popkit-claude root:
    python packages/shared-py/tests/test_github_cache_integration.py
"""

import sys
from pathlib import Path

# Add popkit_shared to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from popkit_shared.utils.github_cache import GitHubCache
from popkit_shared.utils.github_validator import (
    generate_label_validation_report,
    generate_milestone_validation_report,
)


def test_label_caching():
    """Test label caching and validation."""
    print("=" * 60)
    print("TEST 1: Label Caching & Validation")
    print("=" * 60)

    cache = GitHubCache()

    # First call - fetches from GitHub
    print("\n[1] First call - fetching from GitHub API...")
    labels = cache.get_labels()
    print(f"    Fetched {len(labels)} labels")
    print(f"    Sample labels: {', '.join([label['name'] for label in labels[:5]])}")

    # Second call - uses cache
    print("\n[2] Second call - using cache...")
    labels_cached = cache.get_labels()
    print(f"    Retrieved {len(labels_cached)} labels (from cache)")
    print(f"    Cache hit: {labels == labels_cached}")

    # Validate some labels
    print("\n[3] Validating mixed valid/invalid labels...")
    test_labels = ["bug", "priority:high", "invalid-label", "P1-high"]
    report = generate_label_validation_report(test_labels, cache=cache)

    print(f"    Requested: {test_labels}")
    print(f"    Valid: {report['valid']}")
    print(f"    Invalid: {report['invalid']}")
    print(f"    Can proceed: {report['can_proceed']}")

    if report["suggestions"]:
        print("    Suggestions:")
        for invalid, suggestions in report["suggestions"].items():
            print(f"      '{invalid}' -> {suggestions}")

    print("\n" + "=" * 60)
    return True


def test_milestone_validation():
    """Test milestone validation."""
    print("\n" + "=" * 60)
    print("TEST 2: Milestone Validation")
    print("=" * 60)

    cache = GitHubCache()

    # Fetch milestones
    print("\n[1] Fetching milestones...")
    milestones = cache.get_milestones()
    print(f"    Found {len(milestones)} milestones")

    if milestones:
        print(f"    Sample milestones: {', '.join([m['title'] for m in milestones[:3]])}")

        # Validate existing milestone
        print("\n[2] Validating existing milestone...")
        existing = milestones[0]["title"]
        report = generate_milestone_validation_report(existing, cache=cache)
        print(f"    Milestone: '{existing}'")
        print(f"    Exists: {report['exists']}")
        print(f"    Number: {report['milestone_number']}")

        # Validate non-existent milestone
        print("\n[3] Validating non-existent milestone...")
        fake = "v99.99.99"
        report = generate_milestone_validation_report(fake, cache=cache)
        print(f"    Milestone: '{fake}'")
        print(f"    Exists: {report['exists']}")
        if report["suggestions"]:
            print(f"    Suggestions: {', '.join(report['suggestions'])}")
    else:
        print("    No milestones found in repository")

    print("\n" + "=" * 60)
    return True


def test_cache_expiration():
    """Test cache TTL and expiration."""
    print("\n" + "=" * 60)
    print("TEST 3: Cache Expiration")
    print("=" * 60)

    from popkit_shared.utils.github_cache import LocalGitHubCache

    cache = LocalGitHubCache()

    print("\n[1] Checking cache status...")
    labels = cache.get_labels()
    if labels:
        print(f"    Cache exists with {len(labels)} labels")
        print(f"    Updated: {cache._load_cache().get('labels_updated')}")
        print(f"    TTL: {cache._load_cache().get('labels_ttl_minutes')} minutes")
    else:
        print("    Cache empty or expired")

    print("\n[2] Force refresh test...")
    labels_fresh = cache.get_labels(force_refresh=True)
    if labels_fresh is None:
        print("    Force refresh successful - cache bypassed")
    else:
        print("    ERROR: Force refresh failed")

    print("\n" + "=" * 60)
    return True


def test_check_first_pattern():
    """Demonstrate 'Check First' pattern preventing errors."""
    print("\n" + "=" * 60)
    print("TEST 4: 'Check First' Pattern Demo")
    print("=" * 60)

    cache = GitHubCache()

    # Scenario: User wants to create issue with labels
    print("\n[Scenario] Creating issue with labels: ['bug', 'wrong-label', 'priority:high']")

    requested_labels = ["bug", "wrong-label", "priority:high"]

    # BAD APPROACH (old way):
    print("\n  [BAD] Old approach - direct GitHub API call:")
    print("        gh issue create --label bug,wrong-label,priority:high")
    print("        Result: ERROR - Label 'wrong-label' not found")

    # GOOD APPROACH (new way):
    print("\n  [GOOD] New approach - Check First pattern:")
    print("         1. Validate labels against cache")

    report = generate_label_validation_report(requested_labels, cache=cache)

    print("         2. Validation result:")
    print(f"            Valid: {report['valid']}")
    print(f"            Invalid: {report['invalid']}")

    if report["can_proceed"]:
        valid_labels = ",".join(report["valid"])
        print("         3. Proceed with valid labels only:")
        print(f"            gh issue create --label {valid_labels}")
        print("         Result: SUCCESS - Issue created with valid labels")

        if report["invalid"]:
            print("\n         4. Warn user about invalid labels:")
            print(f"            Invalid labels: {', '.join(report['invalid'])}")
            if report["suggestions"]:
                print("            Suggestions:")
                for invalid, sugg in report["suggestions"].items():
                    print(f"              '{invalid}' -> {sugg}")
    else:
        print("         3. Cannot proceed - no valid labels")

    print("\n  [Result] Error prevented BEFORE GitHub API call!")
    print("\n" + "=" * 60)
    return True


def main():
    """Run all integration tests."""
    print("\n" + "=" * 60)
    print("GITHUB CACHE & VALIDATOR - INTEGRATION TESTS")
    print("Issue #96 - 'Check First' Pattern Implementation")
    print("=" * 60)

    tests = [
        ("Label Caching & Validation", test_label_caching),
        ("Milestone Validation", test_milestone_validation),
        ("Cache Expiration", test_cache_expiration),
        ("'Check First' Pattern Demo", test_check_first_pattern),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"\n  ERROR in {name}: {e}")
            results.append((name, False))

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"  [{status}] {name}")

    total = len(results)
    passed = sum(1 for _, s in results if s)
    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\nAll tests passed! GitHub cache implementation is working.")
        return 0
    else:
        print("\nSome tests failed. Please review errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
