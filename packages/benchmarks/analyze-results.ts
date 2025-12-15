#!/usr/bin/env npx tsx
/**
 * Analyze Benchmark Results CLI
 *
 * Compares vanilla vs PopKit benchmark results to understand
 * tool usage patterns and PopKit feature invocations.
 *
 * Usage:
 *   npx tsx analyze-results.ts <vanilla-dir> <popkit-dir>
 *
 * Example:
 *   npx tsx analyze-results.ts \
 *     results/bouncing-balls-vanilla-1765775996133 \
 *     results/bouncing-balls-popkit-1765789176321
 */

import { analyzeBenchmarkSession, compareSessions, generateComparisonReport } from './src/reports/analyzer.js';
import { join } from 'node:path';

const args = process.argv.slice(2);

if (args.length < 2) {
  console.error(`
Usage: npx tsx analyze-results.ts <vanilla-dir> <popkit-dir>

Example:
  npx tsx analyze-results.ts \\
    results/bouncing-balls-vanilla-1765775996133 \\
    results/bouncing-balls-popkit-1765789176321
`);
  process.exit(1);
}

const [vanillaDir, popkitDir] = args;

// Make paths absolute if they're relative
const vanillaPath = vanillaDir.startsWith('results/')
  ? join(import.meta.dirname, vanillaDir)
  : vanillaDir;

const popkitPath = popkitDir.startsWith('results/')
  ? join(import.meta.dirname, popkitDir)
  : popkitDir;

console.log('Loading vanilla session data...');
const vanilla = await analyzeBenchmarkSession(vanillaPath);

console.log('Loading PopKit session data...');
const popkit = await analyzeBenchmarkSession(popkitPath);

console.log('Comparing sessions...\n');
const comparison = compareSessions(vanilla, popkit);

// Generate and print report
const report = generateComparisonReport(comparison);
console.log(report);

// Also save to file
const { writeFile } = await import('node:fs/promises');
const outputPath = join(import.meta.dirname, 'results', 'comparison-report.txt');
await writeFile(outputPath, report);
console.log(`\nReport saved to: ${outputPath}`);
