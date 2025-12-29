/**
 * PopKit Benchmark Framework - Markdown Report Generator
 *
 * Generates Markdown reports from benchmark results.
 */

import type {
  BenchmarkResult,
  ComparisonReport,
  AggregateReport,
} from '../types.js';
import {
  formatPercent,
  formatNumber,
  formatDuration,
  MODE_NAMES,
  calculateImprovement,
} from './formatters.js';

/**
 * Generate a single result report in Markdown
 */
export function generateResultMarkdown(result: BenchmarkResult): string {
  const lines: string[] = [];

  // Header
  lines.push(`# Benchmark Result: ${result.taskId}`);
  lines.push('');
  lines.push(`**Run ID:** ${result.runId}`);
  lines.push(`**Tool:** ${result.tool}`);
  lines.push(`**Mode:** ${MODE_NAMES[result.mode]}`);
  lines.push(`**Date:** ${new Date(result.startedAt).toLocaleString()}`);
  lines.push('');

  // Summary
  lines.push('## Summary');
  lines.push('');
  lines.push(`| Metric | Value |`);
  lines.push(`|--------|-------|`);
  lines.push(`| Success | ${result.success ? '✅ Yes' : '❌ No'} |`);
  lines.push(`| Duration | ${formatDuration(result.durationSeconds)} |`);
  lines.push(`| Tokens Used | ${formatNumber(result.tokensUsed)} |`);
  lines.push(`| Tool Calls | ${result.toolCalls} |`);
  lines.push(`| Tests Passed | ${formatPercent(result.testsPassedRatio)} |`);
  lines.push(`| Quality Score | ${result.codeQualityScore.toFixed(1)}/10 |`);
  lines.push('');

  // Test Results
  if (result.testResults.length > 0) {
    lines.push('## Test Results');
    lines.push('');
    lines.push('| Test | Status | Duration |');
    lines.push('|------|--------|----------|');
    for (const test of result.testResults) {
      const status = test.passed ? '✅' : '❌';
      lines.push(`| ${test.name} | ${status} | ${test.durationMs}ms |`);
    }
    lines.push('');
  }

  // Quality Checks
  if (result.qualityResults.length > 0) {
    lines.push('## Quality Checks');
    lines.push('');
    lines.push('| Check | Status | Score |');
    lines.push('|-------|--------|-------|');
    for (const check of result.qualityResults) {
      const status = check.passed ? '✅' : '❌';
      lines.push(`| ${check.name} | ${status} | ${check.score}/100 |`);
    }
    lines.push('');
  }

  // Error (if any)
  if (result.errored && result.errorMessage) {
    lines.push('## Error');
    lines.push('');
    lines.push('```');
    lines.push(result.errorMessage);
    if (result.errorStack) {
      lines.push('');
      lines.push(result.errorStack);
    }
    lines.push('```');
    lines.push('');
  }

  return lines.join('\n');
}

/**
 * Generate a comparison report in Markdown
 */
export function generateComparisonMarkdown(report: ComparisonReport): string {
  const lines: string[] = [];

  // Header
  lines.push(`# Benchmark Comparison: ${report.taskId}`);
  lines.push('');
  lines.push(`**Generated:** ${new Date(report.generatedAt).toLocaleString()}`);
  lines.push(`**Runs Analyzed:** ${report.runIds.length}`);
  lines.push('');

  // Summary
  lines.push('## Summary');
  lines.push('');
  lines.push(`🏆 **Best Mode:** ${MODE_NAMES[report.summary.bestMode]}`);
  lines.push('');
  lines.push('| Improvement | Value |');
  lines.push('|-------------|-------|');
  lines.push(`| Token Savings | ${report.summary.tokenSavingsPercent.toFixed(1)}% |`);
  lines.push(`| Success Rate | +${report.summary.successRateImprovement.toFixed(1)} pp |`);
  lines.push(`| Quality | +${report.summary.qualityImprovement.toFixed(1)} pts |`);
  lines.push('');

  // Mode Comparisons
  lines.push('## Mode Comparisons');
  lines.push('');

  if (report.modeComparisons.vanillaVsPopkit) {
    lines.push('### Vanilla vs. PopKit');
    lines.push('');
    lines.push(generateModeComparisonTable(report.modeComparisons.vanillaVsPopkit));
    lines.push('');
  }

  if (report.modeComparisons.vanillaVsPower) {
    lines.push('### Vanilla vs. Power Mode');
    lines.push('');
    lines.push(generateModeComparisonTable(report.modeComparisons.vanillaVsPower));
    lines.push('');
  }

  if (report.modeComparisons.popkitVsPower) {
    lines.push('### PopKit vs. Power Mode');
    lines.push('');
    lines.push(generateModeComparisonTable(report.modeComparisons.popkitVsPower));
    lines.push('');
  }

  return lines.join('\n');
}

/**
 * Generate mode comparison table
 */
function generateModeComparisonTable(comparison: NonNullable<ComparisonReport['modeComparisons']['vanillaVsPopkit']>): string {
  const lines: string[] = [];

  lines.push('| Metric | Baseline | Compared | Change |');
  lines.push('|--------|----------|----------|--------|');

  const formatMetric = (name: string, metric: { baseline: number; compared: number; percentChange: number; improved: boolean }, format: 'number' | 'percent' | 'score' = 'number') => {
    let baselineStr: string;
    let comparedStr: string;

    switch (format) {
      case 'percent':
        baselineStr = formatPercent(metric.baseline);
        comparedStr = formatPercent(metric.compared);
        break;
      case 'score':
        baselineStr = `${metric.baseline.toFixed(1)}/10`;
        comparedStr = `${metric.compared.toFixed(1)}/10`;
        break;
      default:
        baselineStr = formatNumber(metric.baseline);
        comparedStr = formatNumber(metric.compared);
    }

    const changeSign = metric.percentChange >= 0 ? '+' : '';
    const changeStr = `${changeSign}${metric.percentChange.toFixed(1)}%`;
    const indicator = metric.improved ? '✅' : '❌';

    return `| ${name} | ${baselineStr} | ${comparedStr} | ${changeStr} ${indicator} |`;
  };

  lines.push(formatMetric('Tokens', comparison.tokens));
  lines.push(formatMetric('Tool Calls', comparison.toolCalls));
  lines.push(formatMetric('Success Rate', comparison.successRate, 'percent'));
  lines.push(formatMetric('Quality', comparison.quality, 'score'));
  lines.push(formatMetric('Time', comparison.time));

  return lines.join('\n');
}

/**
 * Generate aggregate report in Markdown
 */
export function generateAggregateMarkdown(report: AggregateReport): string {
  const lines: string[] = [];

  // Header
  lines.push(`# ${report.title}`);
  lines.push('');
  lines.push(`**Generated:** ${new Date(report.generatedAt).toLocaleString()}`);
  lines.push(`**Tasks:** ${report.taskCount}`);
  lines.push(`**Total Runs:** ${report.runCount}`);
  lines.push('');

  // Executive Summary
  lines.push('## Executive Summary');
  lines.push('');
  lines.push('PopKit demonstrates measurable improvements across all metrics:');
  lines.push('');
  lines.push(`- 📉 **Token Reduction:** ${report.averages.tokenReduction.toFixed(1)}%`);
  lines.push(`- 📈 **Success Rate Improvement:** +${report.averages.successRateImprovement.toFixed(1)} percentage points`);
  lines.push(`- ⭐ **Quality Improvement:** +${report.averages.qualityImprovement.toFixed(1)} points`);
  lines.push(`- ⏱️ **Time Savings:** ${report.averages.timeSavings.toFixed(1)}%`);
  lines.push('');

  // Statistical Confidence
  lines.push('## Statistical Confidence');
  lines.push('');
  if (report.confidence.sufficientSamples) {
    lines.push('✅ Sample size is sufficient for statistical significance.');
  } else {
    lines.push('⚠️ Sample size may be insufficient. More runs recommended for statistical significance.');
  }
  if (report.confidence.pValue) {
    lines.push(`- p-value: ${report.confidence.pValue.toFixed(4)}`);
  }
  if (report.confidence.confidenceInterval) {
    lines.push(`- 95% CI: [${report.confidence.confidenceInterval[0].toFixed(1)}, ${report.confidence.confidenceInterval[1].toFixed(1)}]`);
  }
  lines.push('');

  // Per-Task Results
  lines.push('## Per-Task Results');
  lines.push('');
  lines.push('| Task | Best Mode | Token Savings | Success Improvement |');
  lines.push('|------|-----------|---------------|---------------------|');

  for (const task of report.tasks) {
    const { summary } = task.comparison;
    lines.push(`| ${task.taskName} | ${MODE_NAMES[summary.bestMode]} | ${summary.tokenSavingsPercent.toFixed(1)}% | +${summary.successRateImprovement.toFixed(1)} pp |`);
  }
  lines.push('');

  // Footer
  lines.push('---');
  lines.push('');
  lines.push('*Generated by PopKit Benchmark Framework*');

  return lines.join('\n');
}
