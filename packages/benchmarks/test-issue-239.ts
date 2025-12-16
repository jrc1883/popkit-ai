#!/usr/bin/env npx tsx
/**
 * Manual test to reproduce Issue #254 - CLI never starts for github-issue-239-cache
 */

import { spawn } from 'node:child_process';
import { mkdtemp, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

async function testIssue239() {
  console.log('[Test] Reproducing Issue #254...\n');

  // Create temp workspace
  const tempDir = await mkdtemp(join(tmpdir(), 'bench-test-'));
  console.log(`[Test] Workspace: ${tempDir}\n`);

  // Write initial files
  await writeFile(join(tempDir, 'package.json'), '{"name": "test", "version": "1.0.0"}');
  await writeFile(join(tempDir, 'README.md'), '# Test\nSee REQUIREMENTS.md');
  await writeFile(join(tempDir, 'REQUIREMENTS.md'), `# Requirements

Implement a simple cache class with:
- get(key) -> value
- set(key, value)
- clear()

Use TypeScript.
`);

  // Build prompt (simplified version)
  const prompt = `Implement a simple cache class based on REQUIREMENTS.md.

Create cache.ts with:
- CacheClass with get(), set(), clear() methods
- TypeScript with type hints

Feel free to add features that would make this production-quality.`;

  console.log(`[Test] Prompt length: ${prompt.length} chars\n`);
  console.log(`[Test] Starting Claude CLI with stdin...\n`);

  // Spawn claude CLI exactly like the benchmark runner does (with fix)
  const proc = spawn('claude', ['--print', '--output-format', 'stream-json', '--verbose', '--permission-mode', 'acceptEdits'], {
    cwd: tempDir,
    stdio: ['pipe', 'pipe', 'pipe'],
    windowsHide: false,
    shell: process.platform === 'win32', // FIX: Use shell on Windows to find claude in PATH
  });

  let stdout = '';
  let stderr = '';
  let hasOutput = false;

  const timeout = setTimeout(() => {
    console.log('[Test] ❌ TIMEOUT after 60 seconds - CLI never started!');
    console.log(`[Test] Process still running: ${proc.pid}`);
    proc.kill();
  }, 60000);

  proc.stdout?.on('data', (data) => {
    hasOutput = true;
    stdout += data.toString();
    console.log('[Test] ✓ Got stdout:', data.toString().substring(0, 100));
  });

  proc.stderr?.on('data', (data) => {
    stderr += data.toString();
    console.log('[Test] Got stderr:', data.toString().substring(0, 100));
  });

  // Write prompt to stdin
  if (proc.stdin) {
    proc.stdin.write(prompt);
    if (!prompt.endsWith('\n')) {
      proc.stdin.write('\n');
    }
    proc.stdin.end();
    console.log('[Test] ✓ Wrote prompt to stdin\n');
  }

  proc.on('close', (code) => {
    clearTimeout(timeout);
    console.log(`\n[Test] Process closed with code: ${code}`);
    console.log(`[Test] Has output: ${hasOutput}`);
    console.log(`[Test] Stdout length: ${stdout.length}`);
    console.log(`[Test] Stderr length: ${stderr.length}`);

    if (!hasOutput) {
      console.log('\n❌ REPRODUCED: CLI never started producing output!');
    } else {
      console.log('\n✓ CLI produced output - issue NOT reproduced');
    }
  });

  proc.on('error', (error) => {
    clearTimeout(timeout);
    console.log(`\n[Test] ❌ Process error: ${error.message}`);
  });
}

testIssue239().catch(console.error);
