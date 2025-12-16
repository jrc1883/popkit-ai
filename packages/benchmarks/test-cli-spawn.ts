import { spawn } from 'node:child_process';

const testPrompt = "Say hello in one word";

console.log('Testing CLI spawn with stdin...');
console.log('Prompt:', testPrompt);
console.log('');

const proc = spawn('claude', ['--print', '--output-format', 'stream-json', '--verbose', '--permission-mode', 'acceptEdits'], {
  cwd: process.cwd(),
  shell: true,
  windowsHide: false,
});

let stdout = '';
let stderr = '';

proc.stdout?.on('data', (data) => {
  stdout += data.toString();
  console.log('[STDOUT]', data.toString());
});

proc.stderr?.on('data', (data) => {
  stderr += data.toString();
  console.log('[STDERR]', data.toString());
});

setTimeout(() => {
  console.log('\nWriting to stdin...');
  if (proc.stdin) {
    proc.stdin.write(testPrompt + '\n');
    proc.stdin.end();
    console.log('Stdin written and closed');
  } else {
    console.log('ERROR: stdin is null!');
  }
}, 1000);

proc.on('close', (code) => {
  console.log('\nProcess closed with code:', code);
  console.log('Stdout length:', stdout.length);
  console.log('Stderr length:', stderr.length);
  process.exit(code || 0);
});

proc.on('error', (error) => {
  console.error('Process error:', error);
  process.exit(1);
});

setTimeout(() => {
  console.log('\nTimeout - killing process');
  proc.kill();
  process.exit(1);
}, 30000);
