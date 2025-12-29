/**
 * PopKit Benchmark Framework - Claude Code Runner
 *
 * Executes benchmarks using Claude Code CLI or API.
 */

import { spawn, type ChildProcess } from 'node:child_process';
import { mkdtemp, writeFile, readFile, rm, readdir, access } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

// ESM equivalent of __dirname
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
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
import { ConfigSwitcher, type ConfigSwitcherOptions } from './config-switcher.js';
import { BehaviorCaptureService } from '../behavior/capture.js';
import { BehaviorValidator } from '../validator/validator.js';
import { generateBehaviorReport } from '../validator/report.js';
import type { BehaviorExpectations } from '../validator/expectations.js';

/**
 * Parsed stream-json data from Claude CLI
 */
export interface StreamJsonData {
  sessionId: string;
  model: string;
  toolCalls: Array<{
    id: string;
    name: string;
    input: Record<string, unknown>;
    timestamp: string;
  }>;
  toolResults: Array<{
    toolUseId: string;
    type: string;
    filePath?: string;
    content?: string;
  }>;
  assistantMessages: string[];
  usage: {
    inputTokens: number;
    outputTokens: number;
    cacheReadTokens: number;
    cacheCreationTokens: number;
    costUsd: number;
  };
  durationMs: number;
  durationApiMs: number;
  numTurns: number;
  finalResult: string;
  initData: {
    tools: string[];
    plugins: Array<{ name: string; path: string }>;
    agents: string[];
    skills: string[];
    mcpServers: Array<{ name: string; status: string }>;
  } | null;
}

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
  /** Config switcher options for mode switching */
  configSwitcher?: ConfigSwitcherOptions;
  /** Whether to actually switch PopKit config (default: true) */
  enableConfigSwitching?: boolean;
}

/**
 * Claude Code benchmark runner
 */
export class ClaudeRunner implements ToolRunner {
  readonly name = 'claude' as const;
  readonly description = 'Claude Code CLI/API runner';

  private config: ClaudeRunnerConfig = {};
  private workDir: string | null = null;
  private configSwitcher: ConfigSwitcher | null = null;

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
      enableConfigSwitching: true,
      ...config,
    };

    // Create temporary working directory
    this.workDir = await mkdtemp(join(tmpdir(), 'popkit-benchmark-'));

    // Initialize config switcher if enabled
    if (this.config.enableConfigSwitching) {
      this.configSwitcher = new ConfigSwitcher({
        ...this.config.configSwitcher,
        verbose: this.config.verbose,
      });
      // Save current state for restoration after benchmark
      await this.configSwitcher.saveSnapshot();
    }
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
      // Step 0: Switch PopKit configuration for this mode
      if (this.configSwitcher) {
        logs.push(`[${new Date().toISOString()}] Switching PopKit config to mode: ${mode}`);
        await this.configSwitcher.switchMode(mode);
        logs.push(`[${new Date().toISOString()}] PopKit config switched successfully`);
      }

      // Step 1: Create task workspace
      const taskDir = join(this.workDir, task.id);
      await this.setupTaskWorkspace(task, taskDir);
      logs.push(`[${new Date().toISOString()}] Workspace created: ${taskDir}`);

      // Step 2: Build the prompt based on mode
      const prompt = this.buildPrompt(task, mode);
      logs.push(`[${new Date().toISOString()}] Prompt built (${prompt.length} chars)`);

      // Step 3: Execute with Claude
      const claudeResult = await this.executeWithClaude(prompt, taskDir, mode, task);
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

      // Step 7: Run behavior validation (Issue #258)
      const behaviorValidation = await this.validateBehavior(task, claudeResult.behaviorCapture, logs);
      if (behaviorValidation) {
        logs.push(`[${new Date().toISOString()}] Behavior validation complete: ${behaviorValidation.result.score}/100`);
      }

      const durationSeconds = (Date.now() - startTime) / 1000;
      const success = testResults.every((t) => t.passed);
      const streamData = claudeResult.streamData;

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
        // Detailed tool call data from stream-json
        toolCallDetails: streamData?.toolCalls,
        // API usage details from stream-json
        usageDetails: streamData ? {
          costUsd: streamData.usage.costUsd,
          cacheReadTokens: streamData.usage.cacheReadTokens,
          cacheCreationTokens: streamData.usage.cacheCreationTokens,
          durationApiMs: streamData.durationApiMs,
          numTurns: streamData.numTurns,
          model: streamData.model,
          sessionId: streamData.sessionId,
        } : undefined,
        // Raw stream-json output for debugging
        rawStream: claudeResult.rawStream,
        // Behavior validation results (Issue #258)
        behaviorValidation: behaviorValidation?.result,
        behaviorCapture: claudeResult.behaviorCapture,
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
    // Restore original PopKit configuration
    if (this.configSwitcher) {
      try {
        await this.configSwitcher.restore();
      } catch (error) {
        console.error('[ClaudeRunner] Failed to restore PopKit config:', error);
      }
      this.configSwitcher = null;
    }

    // Clean up working directory
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
    for (const [filePath, content] of Object.entries(task.initialFiles)) {
      const fullPath = join(taskDir, filePath);
      const dir = dirname(fullPath);
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
    // For PopKit/Power modes with a workflow command, instruct Claude to invoke it
    // This encourages using the SlashCommand tool instead of just seeing it as text
    if (task.workflowCommand && (mode === 'popkit' || mode === 'power')) {
      return `Please invoke the command: ${task.workflowCommand}`;
    }

    // For vanilla or no workflow command, build traditional prompt
    let prompt = task.prompt;

    if (task.context) {
      prompt = `${task.context}\n\n${prompt}`;
    }

    // Add mode-specific instructions (legacy behavior)
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
    mode: BenchmarkMode,
    task: BenchmarkTask
  ): Promise<{
    conversation: ConversationMessage[];
    tokens: { input: number; output: number; total: number };
    toolCalls: number;
    streamData?: StreamJsonData;
    rawStream?: string;
    behaviorCapture?: import('../behavior/schema.js').BehaviorCapture;
  }> {
    // For now, use CLI execution
    // In the future, this could use the API directly for better metrics

    const conversation: ConversationMessage[] = [];

    // Add user message
    conversation.push({
      role: 'user',
      content: prompt,
      timestamp: new Date().toISOString(),
    });

    if (this.config.useApi) {
      // API-based execution (placeholder)
      throw new Error('API-based execution not yet implemented');
    }

    // Power Mode: Use coordinator for multi-agent coordination
    if (mode === 'power' && task.powerModeConfig) {
      const result = await this.runPowerModeCoordinator(task, workDir, prompt);
      const streamData = result.streamData;

      // Add assistant message
      conversation.push({
        role: 'assistant',
        content: result.output,
        timestamp: new Date().toISOString(),
        tokens: streamData?.usage.outputTokens || result.tokens,
      });

      return {
        conversation,
        tokens: {
          input: result.tokens,
          output: result.tokens,
          total: result.tokens * 2,
        },
        toolCalls: result.toolCalls,
        streamData,
        rawStream: result.rawStream,
        behaviorCapture: result.behaviorCapture,
      };
    }

    // CLI-based execution with stream-json output
    const result = await this.runClaudeCli(prompt, workDir, mode, task);
    const streamData = result.streamData;

    // Add assistant message
    conversation.push({
      role: 'assistant',
      content: result.output,
      timestamp: new Date().toISOString(),
      tokens: streamData?.usage.outputTokens || result.tokens,
    });

    // Use real token counts from streamData if available
    const totalTokens = streamData ? {
      input: streamData.usage.inputTokens,
      output: streamData.usage.outputTokens,
      total: streamData.usage.inputTokens + streamData.usage.outputTokens,
    } : {
      input: result.tokens,
      output: result.tokens,
      total: result.tokens * 2,
    };

    return {
      conversation,
      tokens: totalTokens,
      toolCalls: result.toolCalls,
      streamData,
      rawStream: result.rawStream,
      behaviorCapture: result.behaviorCapture,
    };
  }

  private async runClaudeCli(
    prompt: string,
    workDir: string,
    mode: BenchmarkMode,
    task: BenchmarkTask
  ): Promise<{
    output: string;
    tokens: number;
    toolCalls: number;
    streamData?: StreamJsonData;
    rawStream?: string;
    behaviorCapture?: import('../behavior/schema.js').BehaviorCapture;
  }> {
    const cliPath = this.config.cliPath || 'claude';

    // Use stream-json format for full tool call capture
    // This gives us: tool calls, tool results, model usage, costs, etc.
    const args = [
      '--print',
      '--output-format', 'stream-json',
      '--verbose',
      '--permission-mode', 'acceptEdits',
    ];

    // For PopKit/Power modes, allow SlashCommand tool for workflow invocation
    if ((mode === 'popkit' || mode === 'power') && task.workflowCommand) {
      args.push('--allowedTools', 'SlashCommand');
    }

    // Build environment with benchmark mode flags (Issue #237)
    const sessionId = `benchmark-${task.id}-${Date.now()}`;
    const env: Record<string, string | undefined> = {
      ...process.env,
      CI: 'true',
      // Enable behavior telemetry capture (Issue #258)
      TEST_MODE: 'true',
      TEST_SESSION_ID: sessionId,
    };

    // For popkit/power modes with workflow testing, set benchmark mode variables
    if ((mode === 'popkit' || mode === 'power') && task.workflowCommand) {
      env.POPKIT_BENCHMARK_MODE = 'true';

      // Create response file if benchmarkResponses are defined
      if (task.benchmarkResponses || task.standardAutoApprove || task.explicitDeclines) {
        const responseFile = await this.createBenchmarkResponseFile(task, workDir);
        env.POPKIT_BENCHMARK_RESPONSES = responseFile;
      }
    }

    // Initialize behavior capture service (Issue #258)
    const captureService = new BehaviorCaptureService(task.id, mode, sessionId);

    // Always use stdin for prompt (cross-platform compatible)
    const result = await this.runCommandWithStdin(cliPath, args, prompt, {
      cwd: workDir,
      timeout: this.config.timeoutMs,
      env: env as Record<string, string>,
      captureService, // Pass capture service to attach to subprocess
    });

    // Parse stream-json output
    const streamData = this.parseStreamJson(result.stdout);

    // Log summary if verbose
    if (this.config.verbose) {
      console.log(`[ClaudeRunner] Tool calls: ${streamData.toolCalls.length}`);
      console.log(`[ClaudeRunner] Tokens: input=${streamData.usage.inputTokens}, output=${streamData.usage.outputTokens}`);
      console.log(`[ClaudeRunner] Cost: $${streamData.usage.costUsd.toFixed(4)}`);
    }

    // Build behavior capture from telemetry events
    const behaviorCapture = captureService.buildBehaviorCapture();

    return {
      output: streamData.finalResult,
      tokens: streamData.usage.inputTokens + streamData.usage.outputTokens,
      toolCalls: streamData.toolCalls.length,
      streamData,
      rawStream: result.stdout, // Include raw stream-json output for debugging
      behaviorCapture,
    };
  }

  /**
   * Parse stream-json output from Claude CLI
   * Each line is a separate JSON object
   */
  private parseStreamJson(output: string): StreamJsonData {
    const lines = output.trim().split('\n').filter(line => line.trim());
    const data: StreamJsonData = {
      sessionId: '',
      model: '',
      toolCalls: [],
      toolResults: [],
      assistantMessages: [],
      usage: {
        inputTokens: 0,
        outputTokens: 0,
        cacheReadTokens: 0,
        cacheCreationTokens: 0,
        costUsd: 0,
      },
      durationMs: 0,
      durationApiMs: 0,
      numTurns: 0,
      finalResult: '',
      initData: null,
    };

    for (const line of lines) {
      try {
        const event = JSON.parse(line);

        switch (event.type) {
          case 'system':
            if (event.subtype === 'init') {
              data.sessionId = event.session_id;
              data.model = event.model;
              data.initData = {
                tools: event.tools || [],
                plugins: event.plugins || [],
                agents: event.agents || [],
                skills: event.skills || [],
                mcpServers: event.mcp_servers || [],
              };
            }
            break;

          case 'assistant':
            if (event.message?.content) {
              for (const block of event.message.content) {
                if (block.type === 'tool_use') {
                  data.toolCalls.push({
                    id: block.id,
                    name: block.name,
                    input: block.input,
                    timestamp: new Date().toISOString(),
                  });
                } else if (block.type === 'text') {
                  data.assistantMessages.push(block.text);
                }
              }
            }
            break;

          case 'user':
            if (event.tool_use_result) {
              data.toolResults.push({
                toolUseId: event.message?.content?.[0]?.tool_use_id,
                type: event.tool_use_result.type,
                filePath: event.tool_use_result.filePath,
                content: event.tool_use_result.content,
              });
            }
            break;

          case 'result':
            data.finalResult = event.result || '';
            data.durationMs = event.duration_ms || 0;
            data.durationApiMs = event.duration_api_ms || 0;
            data.numTurns = event.num_turns || 0;

            if (event.usage) {
              data.usage.inputTokens = event.usage.input_tokens || 0;
              data.usage.outputTokens = event.usage.output_tokens || 0;
              data.usage.cacheReadTokens = event.usage.cache_read_input_tokens || 0;
              data.usage.cacheCreationTokens = event.usage.cache_creation_input_tokens || 0;
            }
            if (event.total_cost_usd) {
              data.usage.costUsd = event.total_cost_usd;
            }
            break;
        }
      } catch {
        // Skip malformed JSON lines
        if (this.config.verbose) {
          console.log(`[ClaudeRunner] Skipping malformed JSON line: ${line.substring(0, 100)}...`);
        }
      }
    }

    return data;
  }

  /**
   * Create a benchmark response file for PopKit workflow testing (Issue #237)
   *
   * This file is read by PopKit skills when POPKIT_BENCHMARK_MODE is set,
   * allowing them to auto-answer AskUserQuestion prompts during benchmarks.
   */
  private async createBenchmarkResponseFile(
    task: BenchmarkTask,
    workDir: string
  ): Promise<string> {
    const responseData = {
      // Pre-defined responses for specific question headers
      responses: task.benchmarkResponses || {},

      // Patterns for prompts that auto-approve (select first/recommended option)
      // Default patterns cover common continuation prompts
      standardAutoApprove: task.standardAutoApprove || [
        'Continue.*',
        'Proceed.*',
        'Commit.*',
        'What.*next.*',
        'Should I.*',
        'Do you want.*continue',
        'Ready to.*',
      ],

      // Patterns for prompts that always decline (prevent side effects)
      // These prevent GitHub operations during benchmarks
      explicitDeclines: task.explicitDeclines || [
        'Create.*repo',
        'Create.*repository',
        'Push.*remote',
        'Push.*origin',
        'Create.*issue',
        'Create.*PR',
        'Create.*pull.*request',
        'gh.*create',
        'git.*push',
      ],
    };

    const responseFile = join(workDir, 'benchmark-responses.json');
    await writeFile(responseFile, JSON.stringify(responseData, null, 2));

    if (this.config.verbose) {
      console.log(`[ClaudeRunner] Created benchmark response file: ${responseFile}`);
      console.log(`[ClaudeRunner] Responses: ${Object.keys(responseData.responses).length}`);
      console.log(`[ClaudeRunner] Auto-approve patterns: ${responseData.standardAutoApprove.length}`);
      console.log(`[ClaudeRunner] Decline patterns: ${responseData.explicitDeclines.length}`);
    }

    return responseFile;
  }

  private runCommandWithStdin(
    command: string,
    args: string[],
    stdin: string,
    options: {
      cwd?: string;
      timeout?: number;
      env?: Record<string, string>;
      captureService?: BehaviorCaptureService;
    } = {}
  ): Promise<{
    exitCode: number;
    stdout: string;
    stderr: string;
  }> {
    return new Promise((resolve, reject) => {
      let stdout = '';
      let stderr = '';

      // Log command for debugging
      if (this.config.verbose) {
        console.log(`[ClaudeRunner] Running: ${command} ${args.join(' ')}`);
        console.log(`[ClaudeRunner] CWD: ${options.cwd}`);
        console.log(`[ClaudeRunner] Stdin length: ${stdin.length} chars`);
      }

      const proc: ChildProcess = spawn(command, args, {
        cwd: options.cwd,
        env: options.env || process.env,
        stdio: ['pipe', 'pipe', 'pipe'], // Explicit stdio piping for stream-json capture
        windowsHide: false,
        shell: process.platform === 'win32', // Fix #254: Use shell on Windows to find npm commands in PATH
      });

      const timeout = options.timeout || 30000;
      const timer = setTimeout(() => {
        if (process.platform === 'win32' && proc.pid) {
          spawn('taskkill', ['/pid', proc.pid.toString(), '/f', '/t'], { shell: true });
        } else {
          proc.kill();
        }
        reject(new Error(`Command timed out after ${timeout}ms`));
      }, timeout);

      // Write prompt to stdin (ensure it ends with newline)
      if (proc.stdin) {
        proc.stdin.write(stdin);
        if (!stdin.endsWith('\n')) {
          proc.stdin.write('\n');
        }
        proc.stdin.end();
      }

      proc.stdout?.on('data', (data) => {
        stdout += data.toString();
        // Stream output in verbose mode
        if (this.config.verbose) {
          process.stdout.write(data);
        }
      });

      proc.stderr?.on('data', (data) => {
        stderr += data.toString();
        // Capture telemetry events from stderr (Issue #258)
        if (options.captureService) {
          const lines = data.toString().split('\n');
          for (const line of lines) {
            if (line.trim()) {
              options.captureService.processLine(line);
            }
          }
        }
        if (this.config.verbose) {
          process.stderr.write(data);
        }
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

  /**
   * Run Power Mode coordinator for multi-agent collaboration
   * Issue #484: Use Python coordinator to properly distribute agent contexts
   */
  private async runPowerModeCoordinator(
    task: BenchmarkTask,
    workDir: string,
    prompt: string
  ): Promise<{
    output: string;
    tokens: number;
    toolCalls: number;
    streamData?: StreamJsonData;
    rawStream?: string;
    behaviorCapture?: import('../behavior/schema.js').BehaviorCapture;
  }> {
    const resultsDir = dirname(workDir);
    const taskConfigPath = join(resultsDir, 'task-config.json');

    // Write task config for coordinator
    await writeFile(taskConfigPath, JSON.stringify(task, null, 2));

    const coordinatorPath = join(
      dirname(dirname(dirname(__dirname))),
      'plugin/power-mode/benchmark_coordinator.py'
    );

    console.log('[PowerMode] Invoking coordinator...');
    console.log(`[PowerMode] Task: ${task.id}`);
    console.log(`[PowerMode] Agents: ${task.powerModeConfig?.numAgents}`);

    try {
      const result = await this.runCommand(
        'python',
        [
          coordinatorPath,
          '--task-config', taskConfigPath,
          '--results-dir', resultsDir,
          '--timeout', String(task.timeoutSeconds || 300)
        ],
        '',
        {
          cwd: workDir,
          timeout: (task.timeoutSeconds || 300) * 1000 + 10000, // Add 10s buffer
        }
      );

      // Read coordinator result
      const coordinatorResultPath = join(resultsDir, 'coordinator-result.json');
      let coordinatorResult: any = {};
      try {
        const resultData = await readFile(coordinatorResultPath, 'utf-8');
        coordinatorResult = JSON.parse(resultData);
      } catch {
        // Result file may not exist if coordinator failed early
      }

      console.log('[PowerMode] Coordination complete');
      console.log(`[PowerMode] Success: ${coordinatorResult.success}`);
      console.log(`[PowerMode] Messages: ${coordinatorResult.messageCount || 0}`);

      return {
        output: `Power Mode coordination completed.\nStream: ${coordinatorResult.streamKey || 'unknown'}\nMessages: ${coordinatorResult.messageCount || 0}\nDuration: ${coordinatorResult.duration || 0}s\nPuzzle Solved: ${coordinatorResult.puzzleSolved || false}`,
        tokens: 0, // Will be updated from agent transcripts later
        toolCalls: 0,
        streamData: undefined,
        rawStream: result.stdout,
      };
    } catch (error) {
      console.error('[PowerMode] Coordinator failed:', error);
      throw error;
    }
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
        // Run the command as a shell command (handles quotes properly)
        const result = await this.runCommand(test.command, [], {
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

    for (const check of task.qualityChecks || []) {
      const startTime = Date.now();
      try {
        // Run the command as a shell command (handles quotes properly)
        const result = await this.runCommand(check.command, [], {
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

      // Log command for debugging
      if (this.config.verbose) {
        console.log(`[ClaudeRunner] Running: ${command} ${args.join(' ')}`);
        console.log(`[ClaudeRunner] CWD: ${options.cwd}`);
      }

      const proc: ChildProcess = spawn(command, args, {
        cwd: options.cwd,
        env: options.env || process.env,
        shell: true, // Needed for shell commands with quotes/pipes in tests
        stdio: ['pipe', 'pipe', 'pipe'], // Explicit stdio piping (Issue #254)
        windowsHide: false,
      });

      const timeout = options.timeout || 30000;
      const timer = setTimeout(() => {
        // Use taskkill on Windows for more reliable process termination
        if (process.platform === 'win32' && proc.pid) {
          spawn('taskkill', ['/pid', proc.pid.toString(), '/f', '/t'], { shell: true });
        } else {
          proc.kill();
        }
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

  /**
   * Validate behavior against expectations (Issue #258)
   *
   * Loads expectation file for the task and runs validation if found.
   * Returns null if no expectation file exists.
   */
  private async validateBehavior(
    task: BenchmarkTask,
    behaviorCapture: import('../behavior/schema.js').BehaviorCapture | undefined,
    logs: string[]
  ): Promise<{
    result: import('../validator/expectations.js').ValidationResult;
    report: string;
  } | null> {
    if (!behaviorCapture) {
      logs.push(`[${new Date().toISOString()}] Behavior validation skipped: no behavior capture`);
      return null;
    }

    try {
      // Look for expectation file in tasks directory
      const expectationPath = join(
        process.cwd(),
        'packages/benchmarks/tasks',
        `${task.id}.expectations.json`
      );

      // Check if expectation file exists
      try {
        await access(expectationPath);
      } catch {
        // Expectation file doesn't exist - skip validation
        logs.push(`[${new Date().toISOString()}] Behavior validation skipped: no expectation file found`);
        return null;
      }

      // Load expectations
      const expectationContent = await readFile(expectationPath, 'utf-8');
      const expectations: BehaviorExpectations = JSON.parse(expectationContent);

      logs.push(`[${new Date().toISOString()}] Loaded expectations from ${expectationPath}`);

      // Run validation
      const validator = new BehaviorValidator(expectations, behaviorCapture);
      const result = validator.validate();

      // Generate report
      const report = generateBehaviorReport(result, expectations, behaviorCapture);

      // Save report to working directory (if available)
      if (this.workDir) {
        const reportPath = join(this.workDir, task.id, 'behavior-report.md');
        await writeFile(reportPath, report);
        logs.push(`[${new Date().toISOString()}] Behavior report saved: ${reportPath}`);
      }

      return { result, report };
    } catch (error) {
      logs.push(`[${new Date().toISOString()}] Behavior validation error: ${error instanceof Error ? error.message : String(error)}`);
      return null;
    }
  }
}
