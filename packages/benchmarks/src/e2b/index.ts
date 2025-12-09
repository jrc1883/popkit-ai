/**
 * E2B Integration Module
 *
 * Optional E2B.dev integration for sandboxed benchmark execution.
 *
 * Note: Requires @e2b/code-interpreter package and E2B_API_KEY env var.
 * This module is optional - benchmarks can run without E2B using Docker fallback.
 */

// Re-export POC for testing
// Note: These are only available if @e2b/code-interpreter is installed

/**
 * Check if E2B is available
 */
export async function isE2BAvailable(): Promise<boolean> {
  try {
    await import('@e2b/code-interpreter');
    return !!process.env.E2B_API_KEY;
  } catch {
    return false;
  }
}

/**
 * E2B configuration
 */
export interface E2BConfig {
  /** Sandbox timeout in seconds (default: 300) */
  timeout?: number;
  /** Custom template name */
  template?: string;
  /** Environment variables */
  envs?: Record<string, string>;
}

/**
 * Default E2B configuration
 */
export const defaultE2BConfig: E2BConfig = {
  timeout: 300,
};

// Future exports:
// export { E2BRunner } from './runner.js';
// export { createBenchmarkSandbox } from './sandbox.js';
