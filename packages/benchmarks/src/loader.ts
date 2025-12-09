/**
 * PopKit Benchmark Framework - Task Loader
 *
 * Utilities for loading and validating benchmark task definitions.
 */

import { readFileSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import type { BenchmarkTask } from './types.js';
import { validateTask, safeValidateTask } from './schemas.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

/**
 * Get the path to a task definition file
 */
export function getTaskPath(taskId: string): string {
  return join(__dirname, '..', 'tasks', `${taskId}.json`);
}

/**
 * Load a single benchmark task by ID
 * @throws If task file doesn't exist or validation fails
 */
export function loadTask(taskId: string): BenchmarkTask {
  const taskPath = getTaskPath(taskId);

  try {
    const content = readFileSync(taskPath, 'utf-8');
    const json = JSON.parse(content);
    return validateTask(json);
  } catch (error) {
    if (error instanceof Error) {
      if ('code' in error && error.code === 'ENOENT') {
        throw new Error(`Task not found: ${taskId}`);
      }
      throw new Error(`Failed to load task ${taskId}: ${error.message}`);
    }
    throw error;
  }
}

/**
 * Load a task without throwing on validation errors
 */
export function safeLoadTask(taskId: string): {
  success: boolean;
  task?: BenchmarkTask;
  error?: string;
} {
  try {
    const task = loadTask(taskId);
    return { success: true, task };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error),
    };
  }
}

/**
 * Load all available benchmark tasks
 */
export function loadAllTasks(): BenchmarkTask[] {
  const tasksDir = join(__dirname, '..', 'tasks');
  const files = readdirSync(tasksDir).filter((f) => f.endsWith('.json'));

  const tasks: BenchmarkTask[] = [];
  const errors: string[] = [];

  for (const file of files) {
    const taskId = file.replace('.json', '');
    const result = safeLoadTask(taskId);

    if (result.success && result.task) {
      tasks.push(result.task);
    } else {
      errors.push(`${taskId}: ${result.error}`);
    }
  }

  if (errors.length > 0) {
    console.warn(`Failed to load ${errors.length} tasks:`);
    for (const error of errors) {
      console.warn(`  - ${error}`);
    }
  }

  return tasks;
}

/**
 * Get list of available task IDs
 */
export function listTaskIds(): string[] {
  const tasksDir = join(__dirname, '..', 'tasks');
  return readdirSync(tasksDir)
    .filter((f) => f.endsWith('.json'))
    .map((f) => f.replace('.json', ''));
}

/**
 * Validate all tasks in the tasks directory
 */
export function validateAllTasks(): {
  valid: string[];
  invalid: { taskId: string; error: string }[];
} {
  const taskIds = listTaskIds();
  const valid: string[] = [];
  const invalid: { taskId: string; error: string }[] = [];

  for (const taskId of taskIds) {
    const result = safeLoadTask(taskId);
    if (result.success) {
      valid.push(taskId);
    } else {
      invalid.push({ taskId, error: result.error || 'Unknown error' });
    }
  }

  return { valid, invalid };
}
