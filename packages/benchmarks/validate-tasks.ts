#!/usr/bin/env npx tsx
/**
 * Quick validator for benchmark task JSON files
 */

import { readFile } from 'node:fs/promises';
import { join } from 'node:path';

const TASKS_DIR = join(import.meta.dirname, 'tasks');

async function validateTask(taskId: string): Promise<boolean> {
  const filePath = join(TASKS_DIR, `${taskId}.json`);

  try {
    const content = await readFile(filePath, 'utf-8');
    const task = JSON.parse(content);

    // Check required fields
    const requiredFields = ['id', 'name', 'description', 'category', 'language', 'version', 'prompt', 'tests'];
    const missing = requiredFields.filter(field => !task[field]);

    if (missing.length > 0) {
      console.error(`❌ ${taskId}: Missing fields: ${missing.join(', ')}`);
      return false;
    }

    // Check GitHub issue fields if category is 'github-issue'
    if (task.category === 'github-issue') {
      if (!task.githubIssue || !task.githubIssue.repo || !task.githubIssue.number) {
        console.error(`❌ ${taskId}: Missing githubIssue metadata`);
        return false;
      }
    }

    // Check tests array
    if (!Array.isArray(task.tests) || task.tests.length === 0) {
      console.error(`❌ ${taskId}: No tests defined`);
      return false;
    }

    console.log(`✅ ${taskId}: Valid (${task.tests.length} tests, ${task.qualityChecks?.length || 0} quality checks)`);
    return true;

  } catch (error) {
    console.error(`❌ ${taskId}: ${error instanceof Error ? error.message : String(error)}`);
    return false;
  }
}

async function main() {
  const tasks = [
    'github-issue-238-ip-scanner',
    'github-issue-237-workflow',
    'github-issue-239-cache'
  ];

  console.log('Validating GitHub Issue Benchmark Tasks...\n');

  const results = await Promise.all(tasks.map(validateTask));
  const allValid = results.every(r => r);

  console.log(`\nValidation ${allValid ? '✅ PASSED' : '❌ FAILED'}`);
  process.exit(allValid ? 0 : 1);
}

main();
