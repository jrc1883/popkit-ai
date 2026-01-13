#!/usr/bin/env python3
"""
Test suite for calculate_risk.py

Tests overall security risk calculation combining multiple scans.
Critical for security assessment workflows.
"""

import sys
from pathlib import Path

import pytest

# Add popkit-ops skills to path
sys.path.insert(
    0,
    str(
        Path(__file__).parent.parent.parent.parent
        / "popkit-ops"
        / "skills"
        / "pop-assessment-security"
        / "scripts"
    ),
)

from calculate_risk import (
    calculate_weighted_risk,
    collect_all_findings,
    generate_recommendations,
    get_risk_label,
)


class TestCalculateWeightedRisk:
    """Test weighted risk calculation"""

    def test_perfect_security_score(self):
        """Test with no security issues"""
        results = [
            {"category": "secret-detection", "score": 100, "findings": []},
            {"category": "injection-prevention", "score": 100, "findings": []},
        ]

        scoring = calculate_weighted_risk(results)

        assert scoring["risk_score"] == 0
        assert scoring["compliance_score"] == 100
        assert scoring["categories"]["secret-detection"]["risk_contribution"] == 0
        assert scoring["categories"]["injection-prevention"]["risk_contribution"] == 0

    def test_maximum_risk_score(self):
        """Test with maximum security issues"""
        results = [
            {"category": "secret-detection", "score": 0, "findings": [1, 2, 3]},
            {"category": "injection-prevention", "score": 0, "findings": [1, 2]},
        ]

        scoring = calculate_weighted_risk(results)

        # Risk score should be 100 (maximum risk)
        assert scoring["risk_score"] == 100
        assert scoring["compliance_score"] == 0

    def test_mixed_security_scores(self):
        """Test with mixed security results"""
        results = [
            {"category": "secret-detection", "score": 75, "findings": []},
            {"category": "injection-prevention", "score": 50, "findings": []},
        ]

        scoring = calculate_weighted_risk(results)

        # Risk = (40 * 25/100) + (40 * 50/100) = 10 + 20 = 30
        # Total weight = 80 (40 + 40)
        # Weighted risk = 30 * 100 / 80 = 37.5
        assert 37 <= scoring["risk_score"] <= 38
        assert 62 <= scoring["compliance_score"] <= 63

    def test_category_weights(self):
        """Test that category weights are applied correctly"""
        results = [
            {"category": "secret-detection", "score": 0, "findings": []},  # Weight: 40
            {"category": "access-control", "score": 0, "findings": []},  # Weight: 10
        ]

        scoring = calculate_weighted_risk(results)

        # secret-detection should have more impact
        assert scoring["categories"]["secret-detection"]["weight"] == 40
        assert scoring["categories"]["access-control"]["weight"] == 10
        assert (
            scoring["categories"]["secret-detection"]["weighted_risk"]
            > scoring["categories"]["access-control"]["weighted_risk"]
        )

    def test_empty_results(self):
        """Test with empty results list"""
        results = []

        scoring = calculate_weighted_risk(results)

        assert scoring["risk_score"] == 0
        assert len(scoring["categories"]) == 0

    def test_unknown_category(self):
        """Test handling of unknown category"""
        results = [{"category": "unknown-category", "score": 50, "findings": []}]

        scoring = calculate_weighted_risk(results)

        # Should use default weight of 10
        assert scoring["categories"]["unknown-category"]["weight"] == 10

    def test_findings_count_included(self):
        """Test that findings count is included in results"""
        results = [{"category": "secret-detection", "score": 75, "findings": [1, 2, 3, 4, 5]}]

        scoring = calculate_weighted_risk(results)

        assert scoring["categories"]["secret-detection"]["findings_count"] == 5

    def test_all_standard_categories(self):
        """Test with all standard security categories"""
        results = [
            {"category": "secret-detection", "score": 90, "findings": []},
            {"category": "injection-prevention", "score": 85, "findings": []},
            {"category": "access-control", "score": 95, "findings": []},
            {"category": "input-validation", "score": 80, "findings": []},
        ]

        scoring = calculate_weighted_risk(results)

        assert len(scoring["categories"]) == 4
        assert scoring["total_weight"] == 100  # 40 + 40 + 10 + 10


class TestGetRiskLabel:
    """Test risk label assignment"""

    def test_risk_label_critical(self):
        """Test CRITICAL label for 75+ risk score"""
        assert get_risk_label(75) == "CRITICAL"
        assert get_risk_label(100) == "CRITICAL"
        assert get_risk_label(90) == "CRITICAL"

    def test_risk_label_high(self):
        """Test HIGH label for 50-74 risk score"""
        assert get_risk_label(50) == "HIGH"
        assert get_risk_label(65) == "HIGH"
        assert get_risk_label(74) == "HIGH"

    def test_risk_label_medium(self):
        """Test MEDIUM label for 25-49 risk score"""
        assert get_risk_label(25) == "MEDIUM"
        assert get_risk_label(35) == "MEDIUM"
        assert get_risk_label(49) == "MEDIUM"

    def test_risk_label_low(self):
        """Test LOW label for 10-24 risk score"""
        assert get_risk_label(10) == "LOW"
        assert get_risk_label(15) == "LOW"
        assert get_risk_label(24) == "LOW"

    def test_risk_label_minimal(self):
        """Test MINIMAL label for <10 risk score"""
        assert get_risk_label(0) == "MINIMAL"
        assert get_risk_label(5) == "MINIMAL"
        assert get_risk_label(9) == "MINIMAL"

    def test_risk_label_boundaries(self):
        """Test label boundaries"""
        assert get_risk_label(74.9) == "HIGH"
        assert get_risk_label(75.0) == "CRITICAL"
        assert get_risk_label(49.9) == "MEDIUM"
        assert get_risk_label(50.0) == "HIGH"


class TestCollectAllFindings:
    """Test findings collection and categorization"""

    def test_collect_findings_by_severity(self):
        """Test collecting findings grouped by severity"""
        results = [
            {
                "category": "secret-detection",
                "findings": [
                    {"id": "1", "severity": "critical", "name": "API Key"},
                    {"id": "2", "severity": "high", "name": "Password"},
                ],
            },
            {
                "category": "injection-prevention",
                "findings": [{"id": "3", "severity": "medium", "name": "SQL Injection"}],
            },
        ]

        all_findings = collect_all_findings(results)

        assert len(all_findings["critical"]) == 1
        assert len(all_findings["high"]) == 1
        assert len(all_findings["medium"]) == 1
        assert len(all_findings["low"]) == 0

    def test_collect_findings_adds_category(self):
        """Test that scan category is added to findings"""
        results = [
            {
                "category": "secret-detection",
                "findings": [{"id": "1", "severity": "critical", "name": "API Key"}],
            }
        ]

        all_findings = collect_all_findings(results)

        assert all_findings["critical"][0]["scan_category"] == "secret-detection"

    def test_collect_findings_empty_results(self):
        """Test with no findings"""
        results = [
            {"category": "secret-detection", "findings": []},
            {"category": "injection-prevention", "findings": []},
        ]

        all_findings = collect_all_findings(results)

        assert len(all_findings["critical"]) == 0
        assert len(all_findings["high"]) == 0
        assert len(all_findings["medium"]) == 0

    def test_collect_findings_invalid_severity(self):
        """Test handling of invalid severity levels"""
        results = [
            {"category": "test", "findings": [{"id": "1", "severity": "invalid", "name": "Test"}]}
        ]

        all_findings = collect_all_findings(results)

        # Invalid severity should be skipped
        total_findings = sum(len(v) for v in all_findings.values())
        assert total_findings == 0

    def test_collect_findings_non_dict_finding(self):
        """Test handling of non-dict findings"""
        results = [
            {
                "category": "test",
                "findings": [
                    "string finding",  # Invalid
                    None,  # Invalid
                    {"id": "1", "severity": "high", "name": "Valid"},  # Valid
                ],
            }
        ]

        all_findings = collect_all_findings(results)

        # Only valid dict finding should be collected
        assert len(all_findings["high"]) == 1


class TestGenerateRecommendations:
    """Test recommendation generation"""

    def test_recommendations_with_critical_issues(self):
        """Test recommendations when critical issues exist"""
        findings = {
            "critical": [{"id": "1", "cwe": "CWE-798"}, {"id": "2", "cwe": "CWE-321"}],
            "high": [],
            "medium": [],
            "low": [],
            "info": [],
        }

        recommendations = generate_recommendations(findings, 75)

        assert len(recommendations) >= 1
        crit_rec = next(r for r in recommendations if r["priority"] == "CRITICAL")
        assert crit_rec["action"] == "IMMEDIATE"
        assert "2 critical" in crit_rec["message"]
        assert "CWE-798" in crit_rec["cwes"]

    def test_recommendations_with_high_issues(self):
        """Test recommendations when high issues exist"""
        findings = {
            "critical": [],
            "high": [
                {"id": "1", "cwe": "CWE-89"},
                {"id": "2", "cwe": "CWE-78"},
                {"id": "3", "cwe": "CWE-94"},
            ],
            "medium": [],
            "low": [],
            "info": [],
        }

        recommendations = generate_recommendations(findings, 50)

        high_rec = next(r for r in recommendations if r["priority"] == "HIGH")
        assert high_rec["action"] == "REQUIRED"
        assert "3 high" in high_rec["message"]

    def test_recommendations_with_medium_issues(self):
        """Test recommendations when medium issues exist"""
        findings = {
            "critical": [],
            "high": [],
            "medium": [{"id": "1"}, {"id": "2"}],
            "low": [],
            "info": [],
        }

        recommendations = generate_recommendations(findings, 30)

        med_rec = next(r for r in recommendations if r["priority"] == "MEDIUM")
        assert med_rec["action"] == "RECOMMENDED"

    def test_recommendations_with_no_issues(self):
        """Test recommendations when security is excellent"""
        findings = {"critical": [], "high": [], "medium": [], "low": [], "info": []}

        recommendations = generate_recommendations(findings, 5)

        info_rec = next(r for r in recommendations if r["priority"] == "INFO")
        assert info_rec["action"] == "MAINTAIN"
        assert "strong" in info_rec["message"].lower()

    def test_recommendations_priority_order(self):
        """Test that recommendations are in priority order"""
        findings = {
            "critical": [{"id": "1", "cwe": "CWE-798"}],
            "high": [{"id": "2", "cwe": "CWE-89"}],
            "medium": [{"id": "3"}],
            "low": [],
            "info": [],
        }

        recommendations = generate_recommendations(findings, 70)

        priorities = [r["priority"] for r in recommendations]
        # Critical should come before high, high before medium
        assert priorities.index("CRITICAL") < priorities.index("HIGH")
        assert priorities.index("HIGH") < priorities.index("MEDIUM")

    def test_recommendations_all_have_required_fields(self):
        """Test that all recommendations have required fields"""
        findings = {
            "critical": [{"id": "1", "cwe": "CWE-798"}],
            "high": [{"id": "2", "cwe": "CWE-89"}],
            "medium": [],
            "low": [],
            "info": [],
        }

        recommendations = generate_recommendations(findings, 60)

        for rec in recommendations:
            assert "priority" in rec
            assert "action" in rec
            assert "message" in rec


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_calculate_risk_with_missing_score(self):
        """Test handling of missing score field"""
        results = [
            {"category": "secret-detection", "findings": []}
            # Missing 'score' field
        ]

        scoring = calculate_weighted_risk(results)

        # Should use default score of 100
        assert scoring["categories"]["secret-detection"]["compliance_score"] == 100

    def test_calculate_risk_with_negative_score(self):
        """Test handling of negative scores"""
        results = [{"category": "secret-detection", "score": -50, "findings": []}]

        scoring = calculate_weighted_risk(results)

        # Should handle gracefully
        assert isinstance(scoring["risk_score"], (int, float))

    def test_calculate_risk_with_score_over_100(self):
        """Test handling of scores over 100"""
        results = [{"category": "secret-detection", "score": 150, "findings": []}]

        scoring = calculate_weighted_risk(results)

        # Risk contribution should handle gracefully (negative is fine, clamped at output)
        assert isinstance(scoring["risk_score"], (int, float))

    def test_collect_findings_missing_fields(self):
        """Test handling of findings with missing fields"""
        results = [
            {
                "category": "test",
                "findings": [
                    {},  # Missing all fields
                    {"id": "1"},  # Missing severity
                    {"severity": "high"},  # Missing other fields
                ],
            }
        ]

        all_findings = collect_all_findings(results)

        # Should handle gracefully
        assert isinstance(all_findings, dict)

    def test_recommendations_with_empty_findings(self):
        """Test recommendations with all empty finding lists"""
        findings = {"critical": [], "high": [], "medium": [], "low": [], "info": []}

        recommendations = generate_recommendations(findings, 0)

        # Should still generate recommendations
        assert len(recommendations) > 0

    def test_risk_label_with_float(self):
        """Test risk label with float values"""
        assert isinstance(get_risk_label(45.7), str)
        assert isinstance(get_risk_label(75.3), str)

    def test_risk_label_with_extreme_values(self):
        """Test risk label with extreme values"""
        assert isinstance(get_risk_label(-100), str)
        assert isinstance(get_risk_label(1000), str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
