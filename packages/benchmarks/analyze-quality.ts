#!/usr/bin/env npx tsx
/**
 * Analyze Quality CLI
 *
 * Deep quality analysis of benchmark results to identify bugs, poor implementations,
 * and compare against vanilla results.
 *
 * Usage:
 *   npx tsx analyze-quality.ts <results-dir> [--compare vanilla-dir]
 *
 * Example:
 *   npx tsx analyze-quality.ts results/bouncing-balls-popkit-1765801033560
 *   npx tsx analyze-quality.ts results/bouncing-balls-popkit-1765801033560 --compare results/bouncing-balls-vanilla-1765775996133
 */

import { readFile, readdir } from 'node:fs/promises';
import { join } from 'node:path';

interface QualityIssue {
  severity: 'critical' | 'warning' | 'info';
  category: 'bug' | 'performance' | 'style' | 'physics' | 'correctness';
  description: string;
  file?: string;
  line?: number;
  code?: string;
}

const args = process.argv.slice(2);

if (args.length === 0 || args[0] === '--help') {
  console.log(`
Analyze Quality CLI

Usage:
  npx tsx analyze-quality.ts <results-dir> [--compare vanilla-dir]

Example:
  npx tsx analyze-quality.ts results/bouncing-balls-popkit-1765801033560
  npx tsx analyze-quality.ts results/bouncing-balls-popkit-1765801033560 \\
    --compare results/bouncing-balls-vanilla-1765775996133

This tool performs deep quality analysis:
  - Code quality issues
  - Physics simulation bugs
  - Performance problems
  - Comparison with vanilla if provided
`);
  process.exit(0);
}

const resultsDir = args[0];
const compareIndex = args.indexOf('--compare');
const compareDir = compareIndex !== -1 ? args[compareIndex + 1] : null;

// Make paths absolute if relative
const resultsPath = resultsDir.startsWith('results/')
  ? join(import.meta.dirname, resultsDir)
  : resultsDir;

const comparePath = compareDir
  ? compareDir.startsWith('results/')
    ? join(import.meta.dirname, compareDir)
    : compareDir
  : null;

/**
 * Analyze JavaScript code for quality issues
 */
async function analyzeCode(resultsPath: string): Promise<QualityIssue[]> {
  const issues: QualityIssue[] = [];

  // Find all JavaScript files
  const files = await readdir(resultsPath);
  const jsFiles = files.filter((f) => f.endsWith('.js'));

  for (const file of jsFiles) {
    const filePath = join(resultsPath, file);
    const code = await readFile(filePath, 'utf-8');
    const lines = code.split('\n');

    // Check for physics issues
    if (code.includes('DAMPING') || code.includes('FRICTION')) {
      const dampingMatch = code.match(/DAMPING\s*=\s*([\d.]+)/);
      const frictionMatch = code.match(/FRICTION\s*=\s*([\d.]+)/);
      const restitutionMatch = code.match(/RESTITUTION\s*=\s*([\d.]+)/);

      if (dampingMatch && parseFloat(dampingMatch[1]) < 1.0) {
        // Check if damping is applied every frame
        if (code.includes('this.vy *= DAMPING') || code.includes('this.vx *= DAMPING')) {
          issues.push({
            severity: 'critical',
            category: 'physics',
            description: `DAMPING (${dampingMatch[1]}) applied every frame causes balls to freeze`,
            file,
            code: dampingMatch[0],
          });
        }
      }

      if (frictionMatch && parseFloat(frictionMatch[1]) < 1.0) {
        // Check if friction is applied every frame
        if (code.includes('this.vx *= FRICTION') || code.includes('this.vy *= FRICTION')) {
          issues.push({
            severity: 'critical',
            category: 'physics',
            description: `FRICTION (${frictionMatch[1]}) applied every frame causes energy loss`,
            file,
            code: frictionMatch[0],
          });
        }
      }

      if (
        restitutionMatch &&
        parseFloat(restitutionMatch[1]) < 1.0 &&
        (dampingMatch || frictionMatch)
      ) {
        issues.push({
          severity: 'warning',
          category: 'physics',
          description: `RESTITUTION (${restitutionMatch[1]}) < 1.0 combined with damping/friction causes total energy loss`,
          file,
        });
      }
    }

    // Check for missing requestAnimationFrame
    if (!code.includes('requestAnimationFrame')) {
      issues.push({
        severity: 'critical',
        category: 'bug',
        description: 'Animation not using requestAnimationFrame',
        file,
      });
    }

    // Check for collision detection
    if (code.includes('ball') && !code.includes('collision') && !code.includes('distance')) {
      issues.push({
        severity: 'warning',
        category: 'correctness',
        description: 'No ball-to-ball collision detection found',
        file,
      });
    }

    // Check for gravity
    if (code.includes('ball') && !code.includes('GRAVITY') && !code.includes('gravity')) {
      issues.push({
        severity: 'warning',
        category: 'physics',
        description: 'No gravity constant found',
        file,
      });
    }
  }

  return issues;
}

/**
 * Compare two implementations
 */
async function compareImplementations(path1: string, path2: string): Promise<string> {
  const issues1 = await analyzeCode(path1);
  const issues2 = await analyzeCode(path2);

  const lines: string[] = [];

  lines.push('');
  lines.push('='.repeat(80));
  lines.push('IMPLEMENTATION COMPARISON');
  lines.push('='.repeat(80));
  lines.push('');

  lines.push(`PopKit: ${path1.split('/').pop()}`);
  lines.push(`Vanilla: ${path2.split('/').pop()}`);
  lines.push('');

  // Quality scores
  const popkitScore = calculateQualityScore(issues1);
  const vanillaScore = calculateQualityScore(issues2);

  lines.push('QUALITY SCORES');
  lines.push('-'.repeat(80));
  lines.push(`PopKit:  ${popkitScore}/10`);
  lines.push(`Vanilla: ${vanillaScore}/10`);
  lines.push('');

  // Issue comparison
  lines.push('ISSUES COMPARISON');
  lines.push('-'.repeat(80));
  lines.push(`PopKit:  ${issues1.length} issues`);
  lines.push(`Vanilla: ${issues2.length} issues`);
  lines.push('');

  // Critical issues
  const popkitCritical = issues1.filter((i) => i.severity === 'critical');
  const vanillaCritical = issues2.filter((i) => i.severity === 'critical');

  if (popkitCritical.length > 0 || vanillaCritical.length > 0) {
    lines.push('CRITICAL ISSUES');
    lines.push('-'.repeat(80));

    if (popkitCritical.length > 0) {
      lines.push(`\nPopKit (${popkitCritical.length}):`);
      for (const issue of popkitCritical) {
        lines.push(`  [${issue.category}] ${issue.description}`);
        if (issue.code) {
          lines.push(`    Code: ${issue.code}`);
        }
      }
    }

    if (vanillaCritical.length > 0) {
      lines.push(`\nVanilla (${vanillaCritical.length}):`);
      for (const issue of vanillaCritical) {
        lines.push(`  [${issue.category}] ${issue.description}`);
        if (issue.code) {
          lines.push(`    Code: ${issue.code}`);
        }
      }
    }
    lines.push('');
  }

  // Winner
  lines.push('VERDICT');
  lines.push('-'.repeat(80));
  if (popkitScore > vanillaScore) {
    lines.push(`✓ PopKit is BETTER (${popkitScore} vs ${vanillaScore})`);
  } else if (popkitScore < vanillaScore) {
    lines.push(`✗ Vanilla is BETTER (${vanillaScore} vs ${popkitScore})`);
  } else {
    lines.push(`= Both have SAME quality (${popkitScore}/10)`);
  }
  lines.push('');

  lines.push('='.repeat(80));

  return lines.join('\n');
}

/**
 * Calculate quality score from issues
 */
function calculateQualityScore(issues: QualityIssue[]): number {
  let score = 10;

  for (const issue of issues) {
    if (issue.severity === 'critical') {
      score -= 3;
    } else if (issue.severity === 'warning') {
      score -= 1;
    } else if (issue.severity === 'info') {
      score -= 0.5;
    }
  }

  return Math.max(0, score);
}

/**
 * Generate quality report
 */
function generateQualityReport(issues: QualityIssue[], resultsPath: string): string {
  const lines: string[] = [];

  lines.push('='.repeat(80));
  lines.push('QUALITY ANALYSIS REPORT');
  lines.push('='.repeat(80));
  lines.push('');

  lines.push(`Results: ${resultsPath.split('/').pop()}`);
  lines.push('');

  // Summary
  const score = calculateQualityScore(issues);
  lines.push('SUMMARY');
  lines.push('-'.repeat(80));
  lines.push(`Quality Score:  ${score}/10`);
  lines.push(`Total Issues:   ${issues.length}`);

  const bySeverity = {
    critical: issues.filter((i) => i.severity === 'critical').length,
    warning: issues.filter((i) => i.severity === 'warning').length,
    info: issues.filter((i) => i.severity === 'info').length,
  };

  lines.push(`  Critical:     ${bySeverity.critical}`);
  lines.push(`  Warnings:     ${bySeverity.warning}`);
  lines.push(`  Info:         ${bySeverity.info}`);
  lines.push('');

  // Issues by category
  const byCategory = issues.reduce(
    (acc, issue) => {
      acc[issue.category] = (acc[issue.category] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  if (Object.keys(byCategory).length > 0) {
    lines.push('ISSUES BY CATEGORY');
    lines.push('-'.repeat(80));
    for (const [category, count] of Object.entries(byCategory)) {
      lines.push(`${category.padEnd(20)} ${count}`);
    }
    lines.push('');
  }

  // Detailed issues
  if (issues.length > 0) {
    lines.push('DETAILED ISSUES');
    lines.push('-'.repeat(80));

    for (const issue of issues) {
      const severity = issue.severity.toUpperCase();
      const category = issue.category.toUpperCase();

      lines.push(`[${severity}] [${category}] ${issue.description}`);
      if (issue.file) {
        lines.push(`  File: ${issue.file}${issue.line ? `:${issue.line}` : ''}`);
      }
      if (issue.code) {
        lines.push(`  Code: ${issue.code}`);
      }
      lines.push('');
    }
  }

  lines.push('='.repeat(80));

  return lines.join('\n');
}

// Main
console.log('Analyzing code quality...\n');

const issues = await analyzeCode(resultsPath);
const report = generateQualityReport(issues, resultsPath);

console.log(report);

// Save report
const { writeFile } = await import('node:fs/promises');
const outputPath = join(resultsPath, 'quality-analysis.txt');
await writeFile(outputPath, report);
console.log(`\nReport saved to: ${outputPath}`);

// Compare if requested
if (comparePath) {
  console.log('\n');
  const comparison = await compareImplementations(resultsPath, comparePath);
  console.log(comparison);

  const comparisonPath = join(resultsPath, 'quality-comparison.txt');
  await writeFile(comparisonPath, comparison);
  console.log(`Comparison saved to: ${comparisonPath}`);
}
