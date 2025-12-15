#!/usr/bin/env npx tsx
/**
 * Analyze Raw Stream CLI
 *
 * Analyzes raw stream-json output from Claude Code CLI to understand
 * PopKit orchestration behavior, command expansions, and routing decisions.
 *
 * Usage:
 *   npx tsx analyze-stream.ts <results-dir>
 *
 * Example:
 *   npx tsx analyze-stream.ts results/bouncing-balls-popkit-1765801033560
 */

import { analyzeRawStream, generateStreamReport } from './src/reports/stream-analyzer.js';
import { join } from 'node:path';

const args = process.argv.slice(2);

if (args.length === 0 || args[0] === '--help') {
  console.log(`
Analyze Raw Stream CLI

Usage:
  npx tsx analyze-stream.ts <results-dir>

Example:
  npx tsx analyze-stream.ts results/bouncing-balls-popkit-1765801033560

This tool analyzes the raw stream-json output (stream-raw.jsonl) to show:
  - Command expansions (slash command → full prompts)
  - Orchestration decisions (mode selection, routing)
  - Thinking blocks and their sizes
  - Tool call timeline with timing

The raw stream contains the complete chain of thought including
expanded command documentation, Claude's reasoning, and all events.
`);
  process.exit(0);
}

const resultsDir = args[0];

// Make path absolute if it's relative
const resultsPath = resultsDir.startsWith('results/')
  ? join(import.meta.dirname, resultsDir)
  : resultsDir;

console.log(`Analyzing raw stream from: ${resultsPath}\n`);

try {
  const analysis = await analyzeRawStream(resultsPath);
  const report = generateStreamReport(analysis);

  console.log(report);

  // Save to file
  const { writeFile } = await import('node:fs/promises');
  const outputPath = join(resultsPath, 'stream-analysis.txt');
  await writeFile(outputPath, report);
  console.log(`\nReport saved to: ${outputPath}`);

  // Also save detailed JSON for further analysis
  const jsonPath = join(resultsPath, 'stream-analysis.json');
  await writeFile(jsonPath, JSON.stringify(analysis, null, 2));
  console.log(`Detailed JSON saved to: ${jsonPath}`);
} catch (error) {
  console.error('Error analyzing stream:', error);
  process.exit(1);
}
