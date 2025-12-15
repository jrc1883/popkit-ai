#!/usr/bin/env npx tsx
/**
 * Simple benchmark runner CLI
 *
 * Usage:
 *   npx tsx run-benchmark.ts bouncing-balls vanilla
 *   npx tsx run-benchmark.ts bouncing-balls popkit
 *   npx tsx run-benchmark.ts --list
 *   npx tsx run-benchmark.ts --status
 */

import { readdir, readFile } from 'node:fs/promises';
import { join } from 'node:path';
import {
  ClaudeRunner,
  isPopKitAvailable,
  type BenchmarkTask,
  type BenchmarkMode,
} from './src/index.js';

const TASKS_DIR = join(import.meta.dirname, 'tasks');

async function loadTask(taskId: string): Promise<BenchmarkTask> {
  // Try JSON first
  const jsonPath = join(TASKS_DIR, `${taskId}.json`);
  try {
    const content = await readFile(jsonPath, 'utf-8');
    return JSON.parse(content);
  } catch {
    // Not found, continue
  }

  // Try in subdirectories
  for (const subdir of ['standard', 'real-world', 'novel']) {
    const subdirPath = join(TASKS_DIR, subdir, `${taskId}.json`);
    try {
      const content = await readFile(subdirPath, 'utf-8');
      return JSON.parse(content);
    } catch {
      // Not found, continue
    }
  }

  throw new Error(`Task not found: ${taskId}`);
}

async function listTasks(): Promise<string[]> {
  const tasks: string[] = [];

  // Direct files
  try {
    const files = await readdir(TASKS_DIR);
    for (const file of files) {
      if (file.endsWith('.json')) {
        tasks.push(file.replace('.json', ''));
      }
    }
  } catch {
    // Ignore
  }

  // Subdirectories
  for (const subdir of ['standard', 'real-world', 'novel']) {
    try {
      const files = await readdir(join(TASKS_DIR, subdir));
      for (const file of files) {
        if (file.endsWith('.json')) {
          tasks.push(`${subdir}/${file.replace('.json', '')}`);
        }
      }
    } catch {
      // Ignore
    }
  }

  return tasks;
}

async function showStatus(): Promise<void> {
  console.log('='.repeat(60));
  console.log('PopKit Benchmark Status');
  console.log('='.repeat(60));

  // Check PopKit availability
  const popkitStatus = await isPopKitAvailable();
  console.log('\nPopKit Plugin Status:');
  console.log(`  Installed: ${popkitStatus.installed ? 'Yes' : 'No'}`);
  console.log(`  Enabled:   ${popkitStatus.enabled ? 'Yes' : 'No'}`);
  console.log(`  Pro:       ${popkitStatus.proConfigured ? 'Yes' : 'No'}`);

  // Check Claude CLI
  const runner = new ClaudeRunner();
  const claudeAvailable = await runner.isAvailable();
  console.log('\nClaude Code CLI:');
  console.log(`  Available: ${claudeAvailable ? 'Yes' : 'No'}`);

  // List tasks
  const tasks = await listTasks();
  console.log('\nAvailable Tasks:');
  for (const task of tasks) {
    console.log(`  - ${task}`);
  }

  console.log('\n' + '='.repeat(60));
}

async function runBenchmark(taskId: string, mode: BenchmarkMode): Promise<void> {
  console.log('='.repeat(60));
  console.log(`Running Benchmark: ${taskId} (${mode} mode)`);
  console.log('='.repeat(60));

  // Load task
  console.log('\nLoading task...');
  const task = await loadTask(taskId);
  console.log(`  Name: ${task.name}`);
  console.log(`  Category: ${task.category}`);
  console.log(`  Language: ${task.language}`);

  // Setup runner
  console.log('\nSetting up runner...');
  const runner = new ClaudeRunner();

  if (!(await runner.isAvailable())) {
    console.error('Error: Claude Code CLI not available');
    process.exit(1);
  }

  await runner.setup({
    verbose: true,
    enableConfigSwitching: true,
    timeoutMs: task.timeoutSeconds * 1000,
  });

  // Create output directory for artifacts
  const { mkdir, cp } = await import('node:fs/promises');
  const { join } = await import('node:path');
  const outputDir = join(import.meta.dirname, 'results', `${taskId}-${mode}-${Date.now()}`);
  await mkdir(outputDir, { recursive: true });

  try {
    // Execute
    console.log(`\nExecuting benchmark in ${mode} mode...`);
    console.log('(This may take several minutes)\n');

    const result = await runner.execute(task, mode);

    // Save output files to results directory
    const { writeFile } = await import('node:fs/promises');
    for (const [filename, content] of Object.entries(result.outputFiles)) {
      const filePath = join(outputDir, filename);
      await mkdir(join(outputDir, filename.split('/').slice(0, -1).join('/')), { recursive: true }).catch(() => {});
      await writeFile(filePath, content);
    }

    // Save full session data for analysis
    const sessionData = {
      taskId: task.id,
      mode,
      timestamp: new Date().toISOString(),
      success: result.success,
      durationSeconds: result.durationSeconds,
      tokens: result.tokens,
      toolCalls: result.toolCalls,
      testResults: result.testResults,
      qualityResults: result.qualityResults,
      conversation: result.conversation,
      logs: result.logs,
      error: result.error ? { message: result.error.message } : null,
      outputFileNames: Object.keys(result.outputFiles),
      // New detailed data from stream-json
      toolCallDetails: result.toolCallDetails || [],
      usageDetails: result.usageDetails || null,
    };
    await writeFile(join(outputDir, 'session.json'), JSON.stringify(sessionData, null, 2));

    // Save detailed tool calls as separate file for easy analysis
    if (result.toolCallDetails && result.toolCallDetails.length > 0) {
      await writeFile(
        join(outputDir, 'tool-calls.json'),
        JSON.stringify(result.toolCallDetails, null, 2)
      );
    }

    // Save raw stream-json output for debugging (includes thinking blocks, command expansions, etc.)
    if (result.rawStream) {
      await writeFile(join(outputDir, 'stream-raw.jsonl'), result.rawStream);
    }

    // Save raw transcript for transcript_parser.py analysis
    const transcriptLines = result.conversation.map(msg =>
      `[${msg.role}] ${msg.timestamp || ''}\n${msg.content}\n`
    ).join('\n---\n');
    await writeFile(join(outputDir, 'transcript.txt'), transcriptLines);

    // Save logs
    if (result.logs.length > 0) {
      await writeFile(join(outputDir, 'logs.txt'), result.logs.join('\n'));
    }

    console.log(`\nOutput files saved to: ${outputDir}`);
    console.log(`Session data saved to: ${outputDir}/session.json`);

    // Show results
    console.log('\n' + '='.repeat(60));
    console.log('RESULTS');
    console.log('='.repeat(60));
    console.log(`Success: ${result.success ? 'Yes' : 'No'}`);
    console.log(`Duration: ${result.durationSeconds.toFixed(1)}s`);
    console.log(`Tool Calls: ${result.toolCalls}`);
    console.log(`Tokens: ${result.tokens.total}`);
    console.log(`Tests Passed: ${result.testResults.filter(t => t.passed).length}/${result.testResults.length}`);

    // Show test details
    if (result.testResults.length > 0) {
      console.log('\nTest Results:');
      for (const test of result.testResults) {
        const status = test.passed ? '[PASS]' : '[FAIL]';
        console.log(`  ${status} ${test.name}`);
        if (!test.passed && test.error) {
          console.log(`         Error: ${test.error}`);
        }
      }
    }

    // Show errors
    if (result.error) {
      console.log('\nError:');
      console.log(`  ${result.error.message}`);
    }

    // Show output files
    console.log(`\nOutput Files: ${Object.keys(result.outputFiles).length}`);
    for (const file of Object.keys(result.outputFiles).slice(0, 10)) {
      console.log(`  - ${file}`);
    }

  } finally {
    await runner.cleanup();
  }

  console.log('\n' + '='.repeat(60));
}

// Main
const args = process.argv.slice(2);

if (args.length === 0 || args[0] === '--help') {
  console.log(`
PopKit Benchmark Runner

Usage:
  npx tsx run-benchmark.ts <task-id> <mode>
  npx tsx run-benchmark.ts --list
  npx tsx run-benchmark.ts --status

Arguments:
  task-id   Task identifier (e.g., bouncing-balls, todo-app)
  mode      Benchmark mode: vanilla, popkit, or power

Examples:
  npx tsx run-benchmark.ts bouncing-balls vanilla
  npx tsx run-benchmark.ts todo-app popkit
  npx tsx run-benchmark.ts --status
`);
  process.exit(0);
}

if (args[0] === '--list') {
  const tasks = await listTasks();
  console.log('Available Tasks:');
  for (const task of tasks) {
    console.log(`  - ${task}`);
  }
  process.exit(0);
}

if (args[0] === '--status') {
  await showStatus();
  process.exit(0);
}

const taskId = args[0];
const mode = (args[1] || 'vanilla') as BenchmarkMode;

if (!['vanilla', 'popkit', 'power'].includes(mode)) {
  console.error(`Invalid mode: ${mode}. Must be vanilla, popkit, or power`);
  process.exit(1);
}

await runBenchmark(taskId, mode);
