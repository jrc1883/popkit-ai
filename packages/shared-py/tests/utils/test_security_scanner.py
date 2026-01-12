#!/usr/bin/env python3
"""
Test suite for security_scanner.py

Tests security vulnerability scanning with npm audit integration.
Critical for automated security vulnerability detection and tracking.
"""

import sys
import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from popkit_shared.utils.security_scanner import (
    Vulnerability,
    ScanResult,
    ExistingIssue,
    SecurityScanner,
    format_scan_report,
    format_github_issue_body
)


class TestVulnerabilityDataClass:
    """Test Vulnerability dataclass"""

    def test_vulnerability_creation(self):
        """Test creating a vulnerability"""
        vuln = Vulnerability(
            name="lodash",
            severity="high",
            title="Prototype Pollution",
            url="https://github.com/advisories/GHSA-1234",
            vulnerable_versions="<4.17.21",
            patched_versions="4.17.21",
            cve="CVE-2021-1234",
            ghsa="GHSA-1234-5678-90ab",
            fix_available=True,
            direct=True
        )

        assert vuln.name == "lodash"
        assert vuln.severity == "high"
        assert vuln.cve == "CVE-2021-1234"
        assert vuln.fix_available is True
        assert vuln.direct is True

    def test_vulnerability_identifier_cve(self):
        """Test identifier property prefers CVE"""
        vuln = Vulnerability(
            name="test",
            severity="high",
            title="Test",
            url="",
            vulnerable_versions="*",
            patched_versions=None,
            cve="CVE-2021-1234",
            ghsa="GHSA-1234"
        )

        assert vuln.identifier == "CVE-2021-1234"

    def test_vulnerability_identifier_ghsa(self):
        """Test identifier property falls back to GHSA"""
        vuln = Vulnerability(
            name="test",
            severity="high",
            title="Test",
            url="",
            vulnerable_versions="*",
            patched_versions=None,
            cve=None,
            ghsa="GHSA-1234"
        )

        assert vuln.identifier == "GHSA-1234"

    def test_vulnerability_identifier_fallback(self):
        """Test identifier property fallback to name-version"""
        vuln = Vulnerability(
            name="test-package",
            severity="high",
            title="Test",
            url="",
            vulnerable_versions="<1.0.0",
            patched_versions=None
        )

        assert vuln.identifier == "test-package-<1.0.0"

    def test_vulnerability_severity_score(self):
        """Test severity score mapping"""
        critical = Vulnerability(
            name="test", severity="critical", title="", url="",
            vulnerable_versions="*", patched_versions=None
        )
        high = Vulnerability(
            name="test", severity="high", title="", url="",
            vulnerable_versions="*", patched_versions=None
        )
        moderate = Vulnerability(
            name="test", severity="moderate", title="", url="",
            vulnerable_versions="*", patched_versions=None
        )
        low = Vulnerability(
            name="test", severity="low", title="", url="",
            vulnerable_versions="*", patched_versions=None
        )
        unknown = Vulnerability(
            name="test", severity="unknown", title="", url="",
            vulnerable_versions="*", patched_versions=None
        )

        assert critical.severity_score == 4
        assert high.severity_score == 3
        assert moderate.severity_score == 2
        assert low.severity_score == 1
        assert unknown.severity_score == 0


class TestScanResultDataClass:
    """Test ScanResult dataclass"""

    def test_scan_result_creation(self):
        """Test creating a scan result"""
        result = ScanResult()

        assert result.vulnerabilities == []
        assert result.total_packages == 0
        assert result.error is None
        # scan_time should be set automatically
        assert result.scan_time is not None

    def test_scan_result_with_vulnerabilities(self):
        """Test scan result with vulnerabilities"""
        vulns = [
            Vulnerability(
                name="test1", severity="critical", title="", url="",
                vulnerable_versions="*", patched_versions=None
            ),
            Vulnerability(
                name="test2", severity="high", title="", url="",
                vulnerable_versions="*", patched_versions=None
            )
        ]

        result = ScanResult(vulnerabilities=vulns, total_packages=10)

        assert len(result.vulnerabilities) == 2
        assert result.total_packages == 10

    def test_by_severity_property(self):
        """Test grouping by severity"""
        vulns = [
            Vulnerability(
                name="test1", severity="critical", title="", url="",
                vulnerable_versions="*", patched_versions=None
            ),
            Vulnerability(
                name="test2", severity="high", title="", url="",
                vulnerable_versions="*", patched_versions=None
            ),
            Vulnerability(
                name="test3", severity="high", title="", url="",
                vulnerable_versions="*", patched_versions=None
            ),
            Vulnerability(
                name="test4", severity="moderate", title="", url="",
                vulnerable_versions="*", patched_versions=None
            )
        ]

        result = ScanResult(vulnerabilities=vulns)
        by_sev = result.by_severity

        assert len(by_sev["critical"]) == 1
        assert len(by_sev["high"]) == 2
        assert len(by_sev["moderate"]) == 1
        assert len(by_sev["low"]) == 0

    def test_counts_property(self):
        """Test count by severity"""
        vulns = [
            Vulnerability(
                name="test1", severity="critical", title="", url="",
                vulnerable_versions="*", patched_versions=None
            ),
            Vulnerability(
                name="test2", severity="high", title="", url="",
                vulnerable_versions="*", patched_versions=None
            )
        ]

        result = ScanResult(vulnerabilities=vulns)
        counts = result.counts

        assert counts["critical"] == 1
        assert counts["high"] == 1
        assert counts["moderate"] == 0
        assert counts["low"] == 0

    def test_fixable_count_property(self):
        """Test counting auto-fixable vulnerabilities"""
        vulns = [
            Vulnerability(
                name="test1", severity="high", title="", url="",
                vulnerable_versions="*", patched_versions=None,
                fix_available=True
            ),
            Vulnerability(
                name="test2", severity="high", title="", url="",
                vulnerable_versions="*", patched_versions=None,
                fix_available=False
            ),
            Vulnerability(
                name="test3", severity="moderate", title="", url="",
                vulnerable_versions="*", patched_versions=None,
                fix_available=True
            )
        ]

        result = ScanResult(vulnerabilities=vulns)

        assert result.fixable_count == 2

    def test_score_impact(self):
        """Test calculating score impact"""
        vulns = [
            Vulnerability(
                name="test1", severity="critical", title="", url="",
                vulnerable_versions="*", patched_versions=None
            ),
            Vulnerability(
                name="test2", severity="high", title="", url="",
                vulnerable_versions="*", patched_versions=None
            ),
            Vulnerability(
                name="test3", severity="moderate", title="", url="",
                vulnerable_versions="*", patched_versions=None
            ),
            Vulnerability(
                name="test4", severity="low", title="", url="",
                vulnerable_versions="*", patched_versions=None
            )
        ]

        result = ScanResult(vulnerabilities=vulns)
        # critical(20) + high(10) + moderate(5) + low(2) = 37, capped at 30
        assert result.score_impact() == 30

    def test_score_impact_under_cap(self):
        """Test score impact under cap"""
        vulns = [
            Vulnerability(
                name="test1", severity="moderate", title="", url="",
                vulnerable_versions="*", patched_versions=None
            ),
            Vulnerability(
                name="test2", severity="low", title="", url="",
                vulnerable_versions="*", patched_versions=None
            )
        ]

        result = ScanResult(vulnerabilities=vulns)
        # moderate(5) + low(2) = 7
        assert result.score_impact() == 7


class TestExistingIssueDataClass:
    """Test ExistingIssue dataclass"""

    def test_existing_issue_creation(self):
        """Test creating an existing issue"""
        issue = ExistingIssue(
            number=123,
            title="[HIGH] Security vulnerability in lodash",
            state="open",
            url="https://github.com/owner/repo/issues/123"
        )

        assert issue.number == 123
        assert issue.title == "[HIGH] Security vulnerability in lodash"
        assert issue.state == "open"


class TestSecurityScannerInit:
    """Test SecurityScanner initialization"""

    def test_init_default_path(self):
        """Test initialization with default path"""
        scanner = SecurityScanner()
        # Should use current working directory
        assert scanner.project_path is not None

    def test_init_custom_path(self):
        """Test initialization with custom path"""
        scanner = SecurityScanner(project_path="/custom/path")
        assert scanner.project_path == "/custom/path"


class TestSecurityScannerScan:
    """Test SecurityScanner scan method"""

    def test_scan_no_package_json(self):
        """Test scan with no package.json"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = SecurityScanner(project_path=tmpdir)
            result = scanner.scan()

            assert result.error == "No package.json found"
            assert len(result.vulnerabilities) == 0

    def test_scan_npm_not_found(self):
        """Test scan with npm not in PATH"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create package.json
            package_json = Path(tmpdir) / "package.json"
            package_json.write_text('{"name": "test"}')

            scanner = SecurityScanner(project_path=tmpdir)

            with patch("subprocess.run", side_effect=FileNotFoundError()):
                result = scanner.scan()

            assert result.error == "npm not found in PATH"

    def test_scan_timeout(self):
        """Test scan timeout"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create package.json
            package_json = Path(tmpdir) / "package.json"
            package_json.write_text('{"name": "test"}')

            scanner = SecurityScanner(project_path=tmpdir)

            import subprocess
            with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("npm", 120)):
                result = scanner.scan()

            assert result.error == "npm audit timed out"

    def test_scan_invalid_json(self):
        """Test scan with invalid JSON output"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create package.json
            package_json = Path(tmpdir) / "package.json"
            package_json.write_text('{"name": "test"}')

            scanner = SecurityScanner(project_path=tmpdir)

            mock_proc = MagicMock()
            mock_proc.stdout = "invalid json{{{"
            mock_proc.returncode = 1

            with patch("subprocess.run", return_value=mock_proc):
                result = scanner.scan()

            assert result.error is not None
            assert "Failed to parse npm audit output" in result.error

    def test_scan_success_no_vulnerabilities(self):
        """Test successful scan with no vulnerabilities"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create package.json
            package_json = Path(tmpdir) / "package.json"
            package_json.write_text('{"name": "test"}')

            scanner = SecurityScanner(project_path=tmpdir)

            audit_output = {
                "metadata": {"totalDependencies": 50},
                "vulnerabilities": {}
            }

            mock_proc = MagicMock()
            mock_proc.stdout = json.dumps(audit_output)
            mock_proc.returncode = 0

            with patch("subprocess.run", return_value=mock_proc):
                result = scanner.scan()

            assert result.error is None
            assert result.total_packages == 50
            assert len(result.vulnerabilities) == 0

    def test_scan_success_with_vulnerabilities(self):
        """Test successful scan with vulnerabilities"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create package.json
            package_json = Path(tmpdir) / "package.json"
            package_json.write_text('{"name": "test"}')

            scanner = SecurityScanner(project_path=tmpdir)

            audit_output = {
                "metadata": {"totalDependencies": 50},
                "vulnerabilities": {
                    "lodash": {
                        "severity": "high",
                        "via": [
                            {
                                "title": "Prototype Pollution",
                                "url": "https://github.com/advisories/GHSA-1234",
                                "cve": "CVE-2021-1234",
                                "ghsa": "GHSA-1234-5678-90ab"
                            }
                        ],
                        "range": "<4.17.21",
                        "fixAvailable": {"version": "4.17.21"},
                        "isDirect": True
                    }
                }
            }

            mock_proc = MagicMock()
            mock_proc.stdout = json.dumps(audit_output)
            mock_proc.returncode = 1

            with patch("subprocess.run", return_value=mock_proc):
                result = scanner.scan()

            assert result.error is None
            assert result.total_packages == 50
            assert len(result.vulnerabilities) == 1

            vuln = result.vulnerabilities[0]
            assert vuln.name == "lodash"
            assert vuln.severity == "high"
            assert vuln.cve == "CVE-2021-1234"
            assert vuln.fix_available is True
            assert vuln.direct is True

    def test_extract_ghsa(self):
        """Test GHSA extraction from URL"""
        scanner = SecurityScanner()

        url1 = "https://github.com/advisories/GHSA-1234-5678-90ab"
        assert scanner._extract_ghsa(url1) == "GHSA-1234-5678-90ab"

        url2 = "https://example.com/no-ghsa"
        assert scanner._extract_ghsa(url2) is None

        url3 = ""
        assert scanner._extract_ghsa(url3) is None


class TestGitHubIntegration:
    """Test GitHub integration methods"""

    def test_get_existing_issues_success(self):
        """Test getting existing issues"""
        scanner = SecurityScanner()

        gh_output = [
            {
                "number": 123,
                "title": "[HIGH] Security vulnerability in lodash",
                "state": "open",
                "url": "https://github.com/owner/repo/issues/123"
            },
            {
                "number": 124,
                "title": "[CRITICAL] CVE-2021-1234",
                "state": "open",
                "url": "https://github.com/owner/repo/issues/124"
            }
        ]

        mock_proc = MagicMock()
        mock_proc.stdout = json.dumps(gh_output)
        mock_proc.returncode = 0

        with patch("subprocess.run", return_value=mock_proc):
            issues = scanner.get_existing_issues()

        assert len(issues) == 2
        assert issues[0].number == 123
        assert issues[1].number == 124

    def test_get_existing_issues_gh_not_available(self):
        """Test getting existing issues when gh not available"""
        scanner = SecurityScanner()

        with patch("subprocess.run", side_effect=FileNotFoundError()):
            issues = scanner.get_existing_issues()

        # Should return empty list, not fail
        assert issues == []

    def test_find_existing_issue_by_cve(self):
        """Test finding existing issue by CVE"""
        scanner = SecurityScanner()

        vuln = Vulnerability(
            name="lodash",
            severity="high",
            title="Test",
            url="",
            vulnerable_versions="*",
            patched_versions=None,
            cve="CVE-2021-1234"
        )

        existing = [
            ExistingIssue(
                number=123,
                title="[HIGH] CVE-2021-1234: lodash vulnerability",
                state="open",
                url="https://github.com/owner/repo/issues/123"
            )
        ]

        found = scanner.find_existing_issue(vuln, existing)
        assert found is not None
        assert found.number == 123

    def test_find_existing_issue_by_ghsa(self):
        """Test finding existing issue by GHSA"""
        scanner = SecurityScanner()

        vuln = Vulnerability(
            name="lodash",
            severity="high",
            title="Test",
            url="",
            vulnerable_versions="*",
            patched_versions=None,
            ghsa="GHSA-1234-5678-90ab"
        )

        existing = [
            ExistingIssue(
                number=123,
                title="[HIGH] GHSA-1234-5678-90ab: lodash vulnerability",
                state="open",
                url="https://github.com/owner/repo/issues/123"
            )
        ]

        found = scanner.find_existing_issue(vuln, existing)
        assert found is not None
        assert found.number == 123

    def test_find_existing_issue_by_name(self):
        """Test finding existing issue by package name"""
        scanner = SecurityScanner()

        vuln = Vulnerability(
            name="lodash",
            severity="high",
            title="Test",
            url="",
            vulnerable_versions="*",
            patched_versions=None
        )

        existing = [
            ExistingIssue(
                number=123,
                title="Security vulnerability in lodash",
                state="open",
                url="https://github.com/owner/repo/issues/123"
            )
        ]

        found = scanner.find_existing_issue(vuln, existing)
        assert found is not None
        assert found.number == 123

    def test_find_existing_issue_not_found(self):
        """Test finding non-existent issue"""
        scanner = SecurityScanner()

        vuln = Vulnerability(
            name="other-package",
            severity="high",
            title="Test",
            url="",
            vulnerable_versions="*",
            patched_versions=None
        )

        existing = [
            ExistingIssue(
                number=123,
                title="Security vulnerability in lodash",
                state="open",
                url="https://github.com/owner/repo/issues/123"
            )
        ]

        found = scanner.find_existing_issue(vuln, existing)
        assert found is None

    def test_create_issue_dry_run(self):
        """Test creating issue in dry-run mode"""
        scanner = SecurityScanner()

        vuln = Vulnerability(
            name="lodash",
            severity="high",
            title="Prototype Pollution",
            url="https://github.com/advisories/GHSA-1234",
            vulnerable_versions="<4.17.21",
            patched_versions="4.17.21",
            cve="CVE-2021-1234"
        )

        result = scanner.create_issue(vuln, dry_run=True)
        assert result is None

    def test_create_issue_success(self):
        """Test creating issue successfully"""
        scanner = SecurityScanner()

        vuln = Vulnerability(
            name="lodash",
            severity="critical",
            title="Prototype Pollution",
            url="https://github.com/advisories/GHSA-1234",
            vulnerable_versions="<4.17.21",
            patched_versions="4.17.21",
            cve="CVE-2021-1234"
        )

        mock_proc = MagicMock()
        mock_proc.stdout = "https://github.com/owner/repo/issues/123"
        mock_proc.returncode = 0

        with patch("subprocess.run", return_value=mock_proc):
            result = scanner.create_issue(vuln, dry_run=False)

        assert result == 123

    def test_create_issue_failure(self):
        """Test creating issue failure"""
        scanner = SecurityScanner()

        vuln = Vulnerability(
            name="lodash",
            severity="high",
            title="Prototype Pollution",
            url="",
            vulnerable_versions="*",
            patched_versions=None
        )

        mock_proc = MagicMock()
        mock_proc.returncode = 1

        with patch("subprocess.run", return_value=mock_proc):
            result = scanner.create_issue(vuln, dry_run=False)

        assert result is None


class TestFixFunctionality:
    """Test npm audit fix functionality"""

    def test_run_fix_success(self):
        """Test running fix successfully"""
        with tempfile.TemporaryDirectory() as tmpdir:
            scanner = SecurityScanner(project_path=tmpdir)

            # Mock fix command
            mock_fix_proc = MagicMock()
            mock_fix_proc.stdout = "fixed 3 vulnerabilities"
            mock_fix_proc.returncode = 0

            # Mock re-scan
            audit_output = {
                "metadata": {"totalDependencies": 50},
                "vulnerabilities": {}
            }
            mock_scan_proc = MagicMock()
            mock_scan_proc.stdout = json.dumps(audit_output)
            mock_scan_proc.returncode = 0

            with patch("subprocess.run") as mock_run:
                def run_side_effect(cmd, **kwargs):
                    if "audit" in cmd and "fix" in cmd:
                        return mock_fix_proc
                    else:
                        return mock_scan_proc

                mock_run.side_effect = run_side_effect

                # Mock package.json for re-scan
                with patch.object(Path, "exists", return_value=True):
                    result = scanner.run_fix()

            assert result["success"] is True
            assert result["remaining"] == []

    def test_run_fix_with_force(self):
        """Test running fix with force flag"""
        scanner = SecurityScanner()

        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.stdout = "fixed"

        with patch("subprocess.run", return_value=mock_proc) as mock_run:
            # Mock re-scan
            with patch.object(SecurityScanner, "scan", return_value=ScanResult()):
                result = scanner.run_fix(force=True)

            # Verify --force was passed
            assert any("--force" in str(call) for call in mock_run.call_args_list)

    def test_run_fix_failure(self):
        """Test running fix failure"""
        scanner = SecurityScanner()

        with patch("subprocess.run", side_effect=Exception("Fix failed")):
            result = scanner.run_fix()

        assert result["success"] is False
        assert result["error"] == "Fix failed"


class TestReportFormatting:
    """Test report formatting functions"""

    def test_format_scan_report_error(self):
        """Test formatting report with error"""
        result = ScanResult(error="npm not found")

        report = format_scan_report(result)

        assert "Error: npm not found" in report

    def test_format_scan_report_no_vulnerabilities(self):
        """Test formatting report with no vulnerabilities"""
        result = ScanResult(total_packages=50)

        report = format_scan_report(result)

        assert "Packages Scanned: 50" in report
        assert "Critical: 0" in report
        assert "Auto-Fixable: 0" in report

    def test_format_scan_report_with_vulnerabilities(self):
        """Test formatting report with vulnerabilities"""
        vulns = [
            Vulnerability(
                name="lodash",
                severity="critical",
                title="Prototype Pollution",
                url="https://github.com/advisories/GHSA-1234",
                vulnerable_versions="<4.17.21",
                patched_versions="4.17.21",
                cve="CVE-2021-1234",
                fix_available=True
            ),
            Vulnerability(
                name="axios",
                severity="high",
                title="XSS Vulnerability",
                url="",
                vulnerable_versions="<0.21.0",
                patched_versions="0.21.0",
                fix_available=False
            )
        ]

        result = ScanResult(vulnerabilities=vulns, total_packages=50)

        report = format_scan_report(result)

        assert "Critical: 1" in report
        assert "High: 1" in report
        assert "Auto-Fixable: 1 of 2" in report
        assert "lodash" in report
        assert "axios" in report
        assert "CVE-2021-1234" in report

    def test_format_github_issue_body(self):
        """Test formatting GitHub issue body"""
        vuln = Vulnerability(
            name="lodash",
            severity="high",
            title="Prototype Pollution",
            url="https://github.com/advisories/GHSA-1234",
            vulnerable_versions="<4.17.21",
            patched_versions="4.17.21",
            cve="CVE-2021-1234"
        )

        body = format_github_issue_body(vuln)

        assert "lodash" in body
        assert "HIGH" in body
        assert "CVE-2021-1234" in body
        assert "Prototype Pollution" in body
        assert "Auto-generated by PopKit" in body


class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_vulnerability_with_minimal_data(self):
        """Test vulnerability with minimal required data"""
        vuln = Vulnerability(
            name="test",
            severity="high",
            title="Test Vulnerability",
            url="",
            vulnerable_versions="*",
            patched_versions=None
        )

        assert vuln.name == "test"
        assert vuln.cve is None
        assert vuln.ghsa is None
        assert vuln.fix_available is False

    def test_scan_result_empty(self):
        """Test scan result with no data"""
        result = ScanResult()

        assert result.vulnerabilities == []
        assert result.counts == {"critical": 0, "high": 0, "moderate": 0, "low": 0}
        assert result.fixable_count == 0
        assert result.score_impact() == 0

    def test_scan_with_via_non_list(self):
        """Test scan handling via field that's not a list"""
        with tempfile.TemporaryDirectory() as tmpdir:
            package_json = Path(tmpdir) / "package.json"
            package_json.write_text('{"name": "test"}')

            scanner = SecurityScanner(project_path=tmpdir)

            audit_output = {
                "metadata": {"totalDependencies": 10},
                "vulnerabilities": {
                    "test-package": {
                        "severity": "moderate",
                        "via": "string-instead-of-list",
                        "range": "*"
                    }
                }
            }

            mock_proc = MagicMock()
            mock_proc.stdout = json.dumps(audit_output)
            mock_proc.returncode = 1

            with patch("subprocess.run", return_value=mock_proc):
                result = scanner.scan()

            # Should handle gracefully
            assert result.error is None

    def test_scan_with_empty_via(self):
        """Test scan with empty via array"""
        with tempfile.TemporaryDirectory() as tmpdir:
            package_json = Path(tmpdir) / "package.json"
            package_json.write_text('{"name": "test"}')

            scanner = SecurityScanner(project_path=tmpdir)

            audit_output = {
                "metadata": {"totalDependencies": 10},
                "vulnerabilities": {
                    "test-package": {
                        "severity": "moderate",
                        "via": [],
                        "range": "*"
                    }
                }
            }

            mock_proc = MagicMock()
            mock_proc.stdout = json.dumps(audit_output)
            mock_proc.returncode = 1

            with patch("subprocess.run", return_value=mock_proc):
                result = scanner.scan()

            # Should handle gracefully
            assert result.error is None

    def test_case_insensitive_severity_handling(self):
        """Test severity handling is case-insensitive"""
        vuln_upper = Vulnerability(
            name="test", severity="HIGH", title="", url="",
            vulnerable_versions="*", patched_versions=None
        )
        vuln_lower = Vulnerability(
            name="test", severity="high", title="", url="",
            vulnerable_versions="*", patched_versions=None
        )

        assert vuln_upper.severity_score == vuln_lower.severity_score

        result = ScanResult(vulnerabilities=[vuln_upper, vuln_lower])
        by_sev = result.by_severity

        # Both should be grouped together
        assert len(by_sev["high"]) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
