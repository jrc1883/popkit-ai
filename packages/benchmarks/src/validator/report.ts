/**
 * PopKit Self-Testing Framework - Report Generator (Issue #258)
 *
 * Generates markdown reports from validation results, providing human-readable
 * summaries of behavior violations, insights, and recommendations.
 *
 * Design: docs/designs/self-testing-framework-design.md
 */

import { BehaviorCapture } from '../behavior/schema.js';
import { BehaviorExpectations, ValidationResult, BehaviorViolation } from './expectations.js';

export class BehaviorReportGenerator {
  private result: ValidationResult;
  private expectations: BehaviorExpectations;
  private capture: BehaviorCapture;

  constructor(
    result: ValidationResult,
    expectations: BehaviorExpectations,
    capture: BehaviorCapture
  ) {
    this.result = result;
    this.expectations = expectations;
    this.capture = capture;
  }

  /**
   * Generate full markdown report
   */
  generateMarkdown(): string {
    const sections = [
      this.generateHeader(),
      this.generateExecutiveSummary(),
      this.generateScoreSection(),
      this.generateViolationsSection(),
      this.generateExpectedVsActualSection(),
      this.generateInsightsSection(),
      this.generateRecommendationsSection(),
      this.generateMetadataSection(),
    ];

    return sections.join('\n\n');
  }

  private generateHeader(): string {
    const passed = this.result.passed ? '✓ PASSED' : '✗ FAILED';
    const emoji = this.result.passed ? '✅' : '❌';

    return `# Behavior Validation Report

**Task:** ${this.expectations.taskId}
**Mode:** ${this.result.mode}
**Status:** ${passed} ${emoji}
**Score:** ${this.result.score}/100
**Date:** ${new Date(this.result.timestamp).toLocaleString()}`;
  }

  private generateExecutiveSummary(): string {
    const { summary } = this.result;
    const criticalIssue = summary.criticalCount > 0 ? ' **CRITICAL ISSUES DETECTED.**' : '';

    return `## Executive Summary

PopKit orchestration validation ${this.result.passed ? 'passed' : 'failed'} with a score of **${this.result.score}/100**.${criticalIssue}

- **Total Checks:** ${summary.totalChecks}
- **Passed:** ${summary.passedChecks} (${Math.round((summary.passedChecks / summary.totalChecks) * 100)}%)
- **Violations:** ${summary.totalViolations}
  - Critical: ${summary.criticalCount}
  - Major: ${summary.majorCount}
  - Minor: ${summary.minorCount}`;
  }

  private generateScoreSection(): string {
    const scoreBar = this.generateScoreBar(this.result.score);

    return `## Behavior Score

\`\`\`
${scoreBar}
${this.result.score}/100
\`\`\`

**Scoring:**
- Critical violations: -20 points each
- Major violations: -10 points each
- Minor violations: -5 points each
- Passing threshold: 80/100`;
  }

  private generateScoreBar(score: number): string {
    const filled = Math.floor(score / 5);
    const empty = 20 - filled;
    return '█'.repeat(filled) + '░'.repeat(empty);
  }

  private generateViolationsSection(): string {
    if (this.result.summary.totalViolations === 0) {
      return `## Violations

No violations detected. All expectations met! 🎉`;
    }

    const sections = [];

    if (this.result.violations.critical.length > 0) {
      sections.push('### Critical Violations\n');
      sections.push(this.formatViolationTable(this.result.violations.critical));
    }

    if (this.result.violations.major.length > 0) {
      sections.push('### Major Violations\n');
      sections.push(this.formatViolationTable(this.result.violations.major));
    }

    if (this.result.violations.minor.length > 0) {
      sections.push('### Minor Violations\n');
      sections.push(this.formatViolationTable(this.result.violations.minor));
    }

    return `## Violations\n\n${sections.join('\n\n')}`;
  }

  private formatViolationTable(violations: BehaviorViolation[]): string {
    const rows = violations.map((v, i) => {
      return `| ${i + 1} | ${v.category} | ${v.expected} | ${v.actual} | ${v.reason} |`;
    });

    return `| # | Category | Expected | Actual | Reason |
|---|----------|----------|--------|--------|
${rows.join('\n')}`;
  }

  private generateExpectedVsActualSection(): string {
    const sections = [];

    // Agents
    if (this.expectations.agents) {
      sections.push(this.generateAgentsComparison());
    }

    // Skills
    if (this.expectations.skills) {
      sections.push(this.generateSkillsComparison());
    }

    // Performance
    if (this.expectations.performance) {
      sections.push(this.generatePerformanceComparison());
    }

    return `## Expected vs Actual\n\n${sections.join('\n\n')}`;
  }

  private generateAgentsComparison(): string {
    const expected = this.expectations.agents?.shouldInvoke?.map((e) => e.agents).flat() || [];
    const actual = this.capture.agents.invocations.map((inv) => inv.agent_name);

    return `### Agents

**Expected:**
${expected.length > 0 ? expected.map((a) => `- ${a}`).join('\n') : '- (none specified)'}

**Actual:**
${actual.length > 0 ? actual.map((a) => `- ${a}`).join('\n') : '- (none invoked)'}`;
  }

  private generateSkillsComparison(): string {
    const expected = this.expectations.skills?.shouldInvoke?.map((e) => e.skills).flat() || [];
    const actual = this.capture.skills.executions.map((exec) => exec.skill_name);

    return `### Skills

**Expected:**
${expected.length > 0 ? expected.map((s) => `- ${s}`).join('\n') : '- (none specified)'}

**Actual:**
${actual.length > 0 ? actual.map((s) => `- ${s}`).join('\n') : '- (none executed)'}`;
  }

  private generatePerformanceComparison(): string {
    const exp = this.expectations.performance;
    const act = this.capture.performance;

    const rows = [];

    if (exp?.maxToolCalls !== undefined) {
      const status = act.tool_call_count <= exp.maxToolCalls ? '✓' : '✗';
      rows.push(`| Tool Calls | ≤ ${exp.maxToolCalls} | ${act.tool_call_count} | ${status} |`);
    }

    if (exp?.maxAgentInvocations !== undefined) {
      const status = act.agent_invocation_count <= exp.maxAgentInvocations ? '✓' : '✗';
      rows.push(
        `| Agent Invocations | ≤ ${exp.maxAgentInvocations} | ${act.agent_invocation_count} | ${status} |`
      );
    }

    if (exp?.maxRoutingTimeMs !== undefined) {
      const status = act.routing_time_ms <= exp.maxRoutingTimeMs ? '✓' : '✗';
      rows.push(`| Routing Time | ≤ ${exp.maxRoutingTimeMs}ms | ${act.routing_time_ms}ms | ${status} |`);
    }

    if (rows.length === 0) return '';

    return `### Performance

| Metric | Expected | Actual | Status |
|--------|----------|--------|--------|
${rows.join('\n')}`;
  }

  private generateInsightsSection(): string {
    if (this.result.insights.length === 0) return '';

    return `## Insights

${this.result.insights.map((insight) => `- ${insight}`).join('\n')}`;
  }

  private generateRecommendationsSection(): string {
    if (this.result.recommendations.length === 0) return '';

    return `## Recommendations

${this.result.recommendations.map((rec) => `- ${rec}`).join('\n')}`;
  }

  private generateMetadataSection(): string {
    return `## Metadata

**Capture:**
- Session ID: ${this.capture.metadata.session_id}
- Capture Version: ${this.capture.metadata.capture_version}
- Test Mode: ${this.capture.metadata.test_mode}

**Expectations:**
- Version: ${this.expectations.metadata?.version || 'unspecified'}
- Created: ${this.expectations.metadata?.created || 'unknown'}

**Execution:**
- Total Duration: ${this.capture.performance.total_duration_ms}ms
- Tool Calls: ${this.capture.performance.tool_call_count}
- Agent Invocations: ${this.capture.performance.agent_invocation_count}
- Skill Invocations: ${this.capture.performance.skill_invocation_count}`;
  }
}

/**
 * Helper function to generate report from validation result
 */
export function generateBehaviorReport(
  result: ValidationResult,
  expectations: BehaviorExpectations,
  capture: BehaviorCapture
): string {
  const generator = new BehaviorReportGenerator(result, expectations, capture);
  return generator.generateMarkdown();
}
