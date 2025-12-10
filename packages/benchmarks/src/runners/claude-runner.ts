/**
 * PopKit Benchmark Framework - Claude Code Runner
 *
 * Executes benchmarks using Claude Code CLI or API.
 */

import { spawn, type ChildProcess } from 'node:child_process';
import { mkdtemp, writeFile, readFile, rm, readdir } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import type {
  ToolRunner,
  RunnerConfig,
  RunnerCapabilities,
  ExecutionResult,
  TestExecutionResult,
  QualityExecutionResult,
} from './interface.js';
import type {
  BenchmarkTask,
  BenchmarkMode,
  ConversationMessage,
} from '../types.js';

/**
 * Claude Code runner configuration
 */
export interface ClaudeRunnerConfig extends RunnerConfig {
  /** Path to Claude Code CLI (default: 'claude') */
  cliPath?: string;
  /** Use API instead of CLI */
  useApi?: boolean;
  /** Anthropic API key (for API mode) */
  anthropicApiKey?: string;
  /** Model to use (default: 'claude-sonnet-4-20250514') */
  model?: string;
}

/**
 * Claude Code benchmark runner
 */
export class ClaudeRunner implements ToolRunner {
  readonly name = 'claude' as const;
  readonly description = 'Claude Code CLI/API runner';

  private config: ClaudeRunnerConfig = {};
  private workDir: string | null = null;

  async isAvailable(): Promise<boolean> {
    try {
      // Check if claude CLI is available
      const result = await this.runCommand('claude', ['--version']);
      return result.exitCode === 0;
    } catch {
      // CLI not available, check for API key
      return !!process.env.ANTHROPIC_API_KEY || !!this.config.anthropicApiKey;
    }
  }

  async setup(config?: ClaudeRunnerConfig): Promise<void> {
    this.config = {
      cliPath: 'claude',
      useApi: false,
      model: 'claude-sonnet-4-20250514',
      timeoutMs: 300000, // 5 minutes
      maxRetries: 3,
      verbose: false,
      ...config,
    };

    // Create temporary working directory
    this.workDir = await mkdtemp(join(tmpdir(), 'popkit-benchmark-'));
  }

  async execute(
    task: BenchmarkTask,
    mode: BenchmarkMode
  ): Promise<ExecutionResult> {
    const startTime = Date.now();
    const logs: string[] = [];
    const conversation: ConversationMessage[] = [];

    if (!this.workDir) {
      throw new Error('Runner not set up. Call setup() first.');
    }

    logs.push(`[${new Date().toISOString()}] Starting benchmark: ${task.id}`);
    logs.push(`[${new Date().toISOString()}] Mode: ${mode}`);

    try {
      // Step 1: Create task workspace
      const taskDir = join(this.workDir, task.id);
      await this.setupTaskWorkspace(task, taskDir);
      logs.push(`[${new Date().toISOString()}] Workspace created: ${taskDir}`);

      // Step 2: Build the prompt based on mode
      const prompt = this.buildPrompt(task, mode);
      logs.push(`[${new Date().toISOString()}] Prompt built (${prompt.length} chars)`);

      // Step 3: Execute with Claude
      const claudeResult = await this.executeWithClaude(prompt, taskDir, mode);
      logs.push(`[${new Date().toISOString()}] Claude execution complete`);

      // Step 4: Collect output files
      const outputFiles = await this.collectOutputFiles(taskDir);
      logs.push(`[${new Date().toISOString()}] Collected ${Object.keys(outputFiles).length} output files`);

      // Step 5: Run tests
      const testResults = await this.runTests(task, taskDir);
      logs.push(`[${new Date().toISOString()}] Tests complete: ${testResults.filter(t => t.passed).length}/${testResults.length} passed`);

      // Step 6: Run quality checks
      const qualityResults = await this.runQualityChecks(task, taskDir);
      logs.push(`[${new Date().toISOString()}] Quality checks complete`);

      const durationSeconds = (Date.now() - startTime) / 1000;
      const success = testResults.every((t) => t.passed);

      return {
        success,
        outputFiles,
        conversation: claudeResult.conversation,
        tokens: claudeResult.tokens,
        toolCalls: claudeResult.toolCalls,
        durationSeconds,
        testResults,
        qualityResults,
        logs,
      };
    } catch (error) {
      const durationSeconds = (Date.now() - startTime) / 1000;
      logs.push(`[${new Date().toISOString()}] Error: ${error}`);

      return {
        success: false,
        outputFiles: {},
        conversation,
        tokens: { input: 0, output: 0, total: 0 },
        toolCalls: 0,
        durationSeconds,
        testResults: [],
        qualityResults: [],
        error: {
          message: error instanceof Error ? error.message : String(error),
          stack: error instanceof Error ? error.stack : undefined,
        },
        logs,
      };
    }
  }

  async cleanup(): Promise<void> {
    if (this.workDir) {
      try {
        await rm(this.workDir, { recursive: true, force: true });
      } catch {
        // Ignore cleanup errors
      }
      this.workDir = null;
    }
  }

  getCapabilities(): RunnerCapabilities {
    return {
      modes: ['vanilla', 'popkit', 'power'],
      languages: ['typescript', 'javascript', 'python', 'rust', 'go', 'java'],
      streaming: true,
      concurrent: false, // One execution at a time for now
      ciCompatible: true,
    };
  }

  // Private helper methods

  private async setupTaskWorkspace(
    task: BenchmarkTask,
    taskDir: string
  ): Promise<void> {
    // Create directory structure
    const { mkdir } = await import('node:fs/promises');
    await mkdir(taskDir, { recursive: true });

    // Write initial files
    for (const [path, content] of Object.entries(task.initialFiles)) {
      const fullPath = join(taskDir, path);
      const dir = fullPath.substring(0, fullPath.lastIndexOf('/'));
      if (dir !== taskDir) {
        await mkdir(dir, { recursive: true });
      }
      await writeFile(fullPath, content);
    }

    // Run setup commands
    if (task.setupCommands) {
      for (const cmd of task.setupCommands) {
        const [command, ...args] = cmd.split(' ');
        await this.runCommand(command, args, { cwd: taskDir });
      }
    }
  }

  private buildPrompt(task: BenchmarkTask, mode: BenchmarkMode): string {
    let prompt = task.prompt;

    if (task.context) {
      prompt = `${task.context}\n\n${prompt}`;
    }

    // Add mode-specific instructions
    switch (mode) {
      case 'vanilla':
        // No additional instructions for vanilla mode
        break;
      case 'popkit':
        prompt = `[Using PopKit workflows for enhanced development]\n\n${prompt}`;
        break;
      case 'power':
        prompt = `[Using PopKit Power Mode for multi-agent collaboration]\n\n${prompt}`;
        break;
    }

    return prompt;
  }

  private async executeWithClaude(
    prompt: string,
    workDir: string,
    _mode: BenchmarkMode
  ): Promise<{
    conversation: ConversationMessage[];
    tokens: { input: number; output: number; total: number };
    toolCalls: number;
  }> {
    // For now, use CLI execution
    // In the future, this could use the API directly for better metrics

    const conversation: ConversationMessage[] = [];
    let totalTokens = { input: 0, output: 0, total: 0 };
    let toolCalls = 0;

    // Add user message
    conversation.push({
      role: 'user',
      content: prompt,
      timestamp: new Date().toISOString(),
    });

    if (this.config.useApi) {
      // API-based execution (placeholder)
      throw new Error('API-based execution not yet implemented');
    } else {
      // CLI-based execution
      const result = await this.runClaudeCli(prompt, workDir);

      conversation.push({
        role: 'assistant',
        content: result.output,
        timestamp: new Date().toISOString(),
        tokens: result.tokens,
      });

      totalTokens = {
        input: result.tokens,
        output: result.tokens * 2, // Estimate
        total: result.tokens * 3,
      };
      toolCalls = result.toolCalls;
    }

    return {
      conversation,
      tokens: totalTokens,
      toolCalls,
    };
  }

  private async runClaudeCli(
    prompt: string,
    workDir: string
  ): Promise<{
    output: string;
    tokens: number;
    toolCalls: number;
  }> {
    const cliPath = this.config.cliPath || 'claude';

    // Write prompt to temp file
    const promptFile = join(workDir, '.benchmark-prompt.txt');
    await writeFile(promptFile, prompt);

    // Run Claude CLI
    const result = await this.runCommand(
      cliPath,
      ['-p', prompt, '--yes'],
      {
        cwd: workDir,
        timeout: this.config.timeoutMs,
        env: {
          ...process.env,
          // Disable interactive features
          CI: 'true',
        },
      }
    );

    // Parse output for metrics (simplified - real implementation would parse JSON)
    const output = result.stdout;
    const tokens = Math.ceil(output.length / 4); // Rough estimate
    const toolCalls = (output.match(/Tool call:/g) || []).length;

    return {
      output,
      tokens,
      toolCalls,
    };
  }

  private async collectOutputFiles(
    taskDir: string
  ): Promise<Record<string, string>> {
    const files: Record<string, string> = {};

    const collectRecursive = async (dir: string, prefix: string = '') => {
      const entries = await readdir(dir, { withFileTypes: true });
      for (const entry of entries) {
        const fullPath = join(dir, entry.name);
        const relativePath = prefix ? `${prefix}/${entry.name}` : entry.name;

        if (entry.isDirectory()) {
          // Skip node_modules and hidden directories
          if (entry.name !== 'node_modules' && !entry.name.startsWith('.')) {
            await collectRecursive(fullPath, relativePath);
          }
        } else if (entry.isFile()) {
          // Skip hidden files and binaries
          if (!entry.name.startsWith('.') && !this.isBinaryFile(entry.name)) {
            try {
              files[relativePath] = await readFile(fullPath, 'utf-8');
            } catch {
              // Skip files that can't be read
            }
          }
        }
      }
    };

    await collectRecursive(taskDir);
    return files;
  }

  private isBinaryFile(filename: string): boolean {
    const binaryExtensions = [
      '.png', '.jpg', '.jpeg', '.gif', '.ico',
      '.woff', '.woff2', '.ttf', '.eot',
      '.zip', '.tar', '.gz',
      '.exe', '.dll', '.so', '.dylib',
    ];
    return binaryExtensions.some((ext) => filename.endsWith(ext));
  }

  private async runTests(
    task: BenchmarkTask,
    taskDir: string
  ): Promise<TestExecutionResult[]> {
    const results: TestExecutionResult[] = [];

    for (const test of task.tests) {
      const startTime = Date.now();
      try {
        const [cmd, ...args] = test.command.split(' ');
        const result = await this.runCommand(cmd, args, {
          cwd: taskDir,
          timeout: (test.timeoutSeconds || 30) * 1000,
        });

        const passed = this.evaluateTestResult(test, result);

        results.push({
          testId: test.id,
          name: test.name,
          passed,
          exitCode: result.exitCode,
          output: result.stdout,
          error: result.stderr || undefined,
          durationMs: Date.now() - startTime,
        });
      } catch (error) {
        results.push({
          testId: test.id,
          name: test.name,
          passed: false,
          exitCode: -1,
          output: '',
          error: error instanceof Error ? error.message : String(error),
          durationMs: Date.now() - startTime,
        });
      }
    }

    return results;
  }

  private evaluateTestResult(
    test: BenchmarkTask['tests'][0],
    result: { exitCode: number; stdout: string; stderr: string }
  ): boolean {
    // Check exit code
    if (test.expectedExitCode !== undefined) {
      if (result.exitCode !== test.expectedExitCode) {
        return false;
      }
    }

    // Check success pattern
    if (test.successPattern) {
      const regex = new RegExp(test.successPattern);
      if (!regex.test(result.stdout)) {
        return false;
      }
    }

    // Check failure pattern
    if (test.failurePattern) {
      const regex = new RegExp(test.failurePattern);
      if (regex.test(result.stdout) || regex.test(result.stderr)) {
        return false;
      }
    }

    // Default: success if exit code is 0
    return result.exitCode === 0;
  }

  private async runQualityChecks(
    task: BenchmarkTask,
    taskDir: string
  ): Promise<QualityExecutionResult[]> {
    const results: QualityExecutionResult[] = [];

    for (const check of task.qualityChecks) {
      const startTime = Date.now();
      try {
        const [cmd, ...args] = check.command.split(' ');
        const result = await this.runCommand(cmd, args, {
          cwd: taskDir,
          timeout: 60000, // 1 minute for quality checks
        });

        // Simple pass/fail based on exit code
        const passed = result.exitCode === 0;
        const score = passed ? 100 : 0;

        results.push({
          checkId: check.id,
          name: check.name,
          passed,
          score,
          findings: result.stdout.split('\n').filter((l) => l.trim()),
          durationMs: Date.now() - startTime,
        });
      } catch (error) {
        results.push({
          checkId: check.id,
          name: check.name,
          passed: false,
          score: 0,
          findings: [error instanceof Error ? error.message : String(error)],
          durationMs: Date.now() - startTime,
        });
      }
    }

    return results;
  }

  private runCommand(
    command: string,
    args: string[],
    options: {
      cwd?: string;
      timeout?: number;
      env?: Record<string, string>;
    } = {}
  ): Promise<{
    exitCode: number;
    stdout: string;
    stderr: string;
  }> {
    return new Promise((resolve, reject) => {
      let stdout = '';
      let stderr = '';

      const proc: ChildProcess = spawn(command, args, {
        cwd: options.cwd,
        env: options.env || process.env,
        shell: true,
      });

      const timeout = options.timeout || 30000;
      const timer = setTimeout(() => {
        proc.kill('SIGTERM');
        reject(new Error(`Command timed out after ${timeout}ms`));
      }, timeout);

      proc.stdout?.on('data', (data) => {
        stdout += data.toString();
      });

      proc.stderr?.on('data', (data) => {
        stderr += data.toString();
      });

      proc.on('close', (code) => {
        clearTimeout(timer);
        resolve({
          exitCode: code ?? -1,
          stdout,
          stderr,
        });
      });

      proc.on('error', (error) => {
        clearTimeout(timer);
        reject(error);
      });
    });
  }
}
