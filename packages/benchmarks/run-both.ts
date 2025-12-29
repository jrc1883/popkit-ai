#!/usr/bin/env npx tsx
/**
 * Run both vanilla and popkit benchmarks in parallel
 *
 * Usage:
 *   npx tsx run-both.ts bouncing-balls
 *   npx tsx run-both.ts bouncing-balls --visible
 */

import { spawn } from 'node:child_process';
import { join } from 'node:path';

const args = process.argv.slice(2);

if (args.length === 0 || args[0] === '--help') {
  console.log(`
Run Both Benchmarks (Vanilla + PopKit)

Usage:
  npx tsx run-both.ts <task-id> [--visible]

Options:
  --visible    Run in visible terminal windows (Windows only)
  --no-timeout Remove timeout (let it run forever)

Example:
  npx tsx run-both.ts bouncing-balls
  npx tsx run-both.ts bouncing-balls --visible
`);
  process.exit(0);
}

const taskId = args[0];
const visible = args.includes('--visible');
const noTimeout = args.includes('--no-timeout');

const runnerScript = join(import.meta.dirname, 'run-benchmark.ts');

console.log('='.repeat(80));
console.log(`Running Parallel Benchmarks: ${taskId}`);
console.log('='.repeat(80));
console.log('');
console.log(`Task:       ${taskId}`);
console.log(`Mode:       ${visible ? 'Visible Windows' : 'Background'}`);
console.log(`Timeout:    ${noTimeout ? 'None (infinite)' : '300s'}`);
console.log('');
console.log('Starting vanilla benchmark...');

// Run vanilla in background
const vanilla = spawn(
  'npx',
  ['tsx', runnerScript, taskId, 'vanilla'],
  {
    cwd: import.meta.dirname,
    stdio: 'pipe',
    shell: visible ? true : false,
    ...(visible && process.platform === 'win32'
      ? {
          detached: true,
          windowsHide: false,
        }
      : {}),
  }
);

vanilla.stdout?.on('data', (data) => {
  console.log(`[VANILLA] ${data.toString().trim()}`);
});

vanilla.stderr?.on('data', (data) => {
  console.error(`[VANILLA ERROR] ${data.toString().trim()}`);
});

console.log('Starting popkit benchmark...');

// Run popkit in background
const popkit = spawn(
  'npx',
  ['tsx', runnerScript, taskId, 'popkit'],
  {
    cwd: import.meta.dirname,
    stdio: 'pipe',
    shell: visible ? true : false,
    ...(visible && process.platform === 'win32'
      ? {
          detached: true,
          windowsHide: false,
        }
      : {}),
  }
);

popkit.stdout?.on('data', (data) => {
  console.log(`[POPKIT] ${data.toString().trim()}`);
});

popkit.stderr?.on('data', (data) => {
  console.error(`[POPKIT ERROR] ${data.toString().trim()}`);
});

console.log('');
console.log('='.repeat(80));
console.log('Both benchmarks running...');
console.log('='.repeat(80));
console.log('');
console.log('You can monitor progress in separate terminal windows or check');
console.log('the results/ directory for output.');
console.log('');

// Wait for both to complete
Promise.all([
  new Promise<number>((resolve) => {
    vanilla.on('exit', (code) => {
      console.log(`\n[VANILLA] Completed with exit code: ${code}`);
      resolve(code || 0);
    });
  }),
  new Promise<number>((resolve) => {
    popkit.on('exit', (code) => {
      console.log(`[POPKIT] Completed with exit code: ${code}`);
      resolve(code || 0);
    });
  }),
]).then(([vanillaCode, popkitCode]) => {
  console.log('');
  console.log('='.repeat(80));
  console.log('BOTH BENCHMARKS COMPLETE');
  console.log('='.repeat(80));
  console.log(`Vanilla: ${vanillaCode === 0 ? 'SUCCESS' : 'FAILED'}`);
  console.log(`PopKit:  ${popkitCode === 0 ? 'SUCCESS' : 'FAILED'}`);
  console.log('');
  console.log('Run analysis:');
  console.log('  npx tsx analyze-results.ts <vanilla-dir> <popkit-dir>');
  console.log('  npx tsx analyze-quality.ts <popkit-dir> --compare <vanilla-dir>');
  console.log('  npx tsx analyze-stream.ts <popkit-dir>');
  console.log('');

  process.exit(vanillaCode === 0 && popkitCode === 0 ? 0 : 1);
});

// Handle process termination
process.on('SIGINT', () => {
  console.log('\n\nTerminating both benchmarks...');
  vanilla.kill();
  popkit.kill();
  process.exit(130);
});
