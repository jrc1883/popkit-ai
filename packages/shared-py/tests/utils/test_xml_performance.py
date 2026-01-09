#!/usr/bin/env python3
"""
Performance test suite for PopKit XML operations

Tests performance benchmarks for XML generation, parsing, and validation.
Ensures operations meet sub-millisecond targets.
"""

import sys
import time
import pytest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from popkit_shared.utils.xml_generator import (
    generate_problem_xml,
    generate_project_context_xml,
    generate_findings_xml
)
from popkit_shared.utils.xml_parser import (
    parse_problem_context,
    parse_project_context,
    parse_findings
)
from popkit_shared.utils.xml_validator import (
    validate_problem_xml,
    validate_project_xml,
    validate_findings_xml,
    is_well_formed_xml
)


class TestGenerationPerformance:
    """Test XML generation performance"""

    def test_problem_generation_benchmark(self):
        """Test problem XML generation speed (<1ms target)"""
        iterations = 100
        start = time.perf_counter()

        for _ in range(iterations):
            generate_problem_xml("Fix the authentication bug in production")

        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        avg_time = elapsed / iterations

        # Target: <1ms per generation
        assert avg_time < 1.0, f"Average generation time {avg_time:.3f}ms exceeds 1ms target"

    def test_project_generation_benchmark(self):
        """Test project XML generation speed (<1ms target)"""
        context = {
            "name": "test-project",
            "stack": ["Python", "TypeScript", "React"],
            "infrastructure": {"redis": True, "postgres": True, "docker": True}
        }

        iterations = 100
        start = time.perf_counter()

        for _ in range(iterations):
            generate_project_context_xml(context)

        elapsed = (time.perf_counter() - start) * 1000
        avg_time = elapsed / iterations

        assert avg_time < 1.0, f"Average generation time {avg_time:.3f}ms exceeds 1ms target"

    def test_findings_generation_benchmark(self):
        """Test findings XML generation speed (<1ms target)"""
        findings = {
            "tool": "Write",
            "status": "success",
            "quality_score": 0.85,
            "issues": ["Issue 1", "Issue 2"],
            "suggestions": ["Suggestion 1", "Suggestion 2"]
        }

        iterations = 100
        start = time.perf_counter()

        for _ in range(iterations):
            generate_findings_xml(findings)

        elapsed = (time.perf_counter() - start) * 1000
        avg_time = elapsed / iterations

        assert avg_time < 1.0, f"Average generation time {avg_time:.3f}ms exceeds 1ms target"


class TestParsingPerformance:
    """Test XML parsing performance"""

    def test_problem_parsing_benchmark(self):
        """Test problem XML parsing speed (<0.5ms target)"""
        xml = '''
        <problem-context version="1.0">
            <category>bug</category>
            <description>Authentication fails intermittently</description>
            <severity>high</severity>
        </problem-context>
        '''

        iterations = 100
        start = time.perf_counter()

        for _ in range(iterations):
            parse_problem_context(xml)

        elapsed = (time.perf_counter() - start) * 1000
        avg_time = elapsed / iterations

        # Target: <0.5ms per parse
        assert avg_time < 0.5, f"Average parsing time {avg_time:.3f}ms exceeds 0.5ms target"

    def test_project_parsing_benchmark(self):
        """Test project XML parsing speed (<0.5ms target)"""
        xml = '''
        <project version="1.0">
            <name>popkit-claude</name>
            <stack>
                <technology>Python</technology>
                <technology>TypeScript</technology>
            </stack>
            <infrastructure>
                <redis>false</redis>
                <postgres>true</postgres>
            </infrastructure>
        </project>
        '''

        iterations = 100
        start = time.perf_counter()

        for _ in range(iterations):
            parse_project_context(xml)

        elapsed = (time.perf_counter() - start) * 1000
        avg_time = elapsed / iterations

        assert avg_time < 0.5, f"Average parsing time {avg_time:.3f}ms exceeds 0.5ms target"

    def test_findings_parsing_benchmark(self):
        """Test findings XML parsing speed (<0.5ms target)"""
        xml = '''
        <findings version="1.0">
            <tool>Write</tool>
            <status>success</status>
            <quality_score>0.85</quality_score>
            <issues>
                <issue>Issue 1</issue>
                <issue>Issue 2</issue>
            </issues>
        </findings>
        '''

        iterations = 100
        start = time.perf_counter()

        for _ in range(iterations):
            parse_findings(xml)

        elapsed = (time.perf_counter() - start) * 1000
        avg_time = elapsed / iterations

        assert avg_time < 0.5, f"Average parsing time {avg_time:.3f}ms exceeds 0.5ms target"


class TestValidationPerformance:
    """Test XML validation performance"""

    def test_well_formedness_check_benchmark(self):
        """Test well-formedness checking speed (<0.1ms target)"""
        xml = '<problem-context><category>bug</category><description>Test</description><severity>high</severity></problem-context>'

        iterations = 1000
        start = time.perf_counter()

        for _ in range(iterations):
            is_well_formed_xml(xml)

        elapsed = (time.perf_counter() - start) * 1000
        avg_time = elapsed / iterations

        # Target: <0.1ms per check
        assert avg_time < 0.1, f"Average validation time {avg_time:.3f}ms exceeds 0.1ms target"

    def test_schema_validation_benchmark(self):
        """Test schema validation speed (baseline measurement)"""
        xml = '''
        <problem-context version="1.0">
            <category>bug</category>
            <description>Test description</description>
            <severity>high</severity>
        </problem-context>
        '''

        iterations = 50
        start = time.perf_counter()

        for _ in range(iterations):
            validate_problem_xml(xml)

        elapsed = (time.perf_counter() - start) * 1000
        avg_time = elapsed / iterations

        # Just measure and log, don't enforce strict limit (depends on lxml availability)
        print(f"\nSchema validation average time: {avg_time:.3f}ms")
        assert avg_time < 10.0, f"Schema validation time {avg_time:.3f}ms unreasonably slow"


class TestLargePayloadPerformance:
    """Test performance with large XML payloads"""

    def test_large_findings_list(self):
        """Test performance with large findings lists"""
        findings = {
            "tool": "Test",
            "status": "success",
            "quality_score": 0.5,
            "issues": [f"Issue {i}" for i in range(100)],
            "suggestions": [f"Suggestion {i}" for i in range(100)]
        }

        start = time.perf_counter()
        xml = generate_findings_xml(findings)
        gen_time = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        parsed = parse_findings(xml)
        parse_time = (time.perf_counter() - start) * 1000

        # Large payloads allowed more time but should still be reasonable
        assert gen_time < 5.0, f"Large XML generation {gen_time:.3f}ms too slow"
        assert parse_time < 5.0, f"Large XML parsing {parse_time:.3f}ms too slow"
        assert len(parsed['issues']) == 100
        assert len(parsed['suggestions']) == 100

    def test_large_project_stack(self):
        """Test performance with large technology stacks"""
        context = {
            "name": "mega-project",
            "stack": [f"Technology-{i}" for i in range(50)]
        }

        start = time.perf_counter()
        xml = generate_project_context_xml(context)
        gen_time = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        parsed = parse_project_context(xml)
        parse_time = (time.perf_counter() - start) * 1000

        assert gen_time < 5.0, f"Large project generation {gen_time:.3f}ms too slow"
        assert parse_time < 5.0, f"Large project parsing {parse_time:.3f}ms too slow"
        assert len(parsed['stack']) == 50


class TestRoundTripPerformance:
    """Test complete round-trip performance"""

    def test_problem_roundtrip_benchmark(self):
        """Test complete generate->parse cycle for problem context"""
        iterations = 50
        start = time.perf_counter()

        for _ in range(iterations):
            xml = generate_problem_xml("Fix authentication bug")
            parsed = parse_problem_context(xml)
            assert parsed is not None

        elapsed = (time.perf_counter() - start) * 1000
        avg_time = elapsed / iterations

        # Target: <2ms for complete roundtrip
        assert avg_time < 2.0, f"Average roundtrip time {avg_time:.3f}ms exceeds 2ms target"

    def test_concurrent_operations(self):
        """Test performance under concurrent-like load"""
        # Simulate 100 operations in quick succession
        operations = []
        start = time.perf_counter()

        for i in range(100):
            xml = generate_problem_xml(f"Task {i}")
            parsed = parse_problem_context(xml)
            operations.append(parsed)

        elapsed = (time.perf_counter() - start) * 1000

        # Should complete 100 operations in under 200ms
        assert elapsed < 200.0, f"100 operations took {elapsed:.1f}ms (target <200ms)"
        assert len(operations) == 100


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
