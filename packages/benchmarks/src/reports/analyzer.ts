/**
 * PopKit Benchmark Framework - Telemetry Analyzer
 *
 * Analyzes benchmark session data to understand tool usage patterns,
 * PopKit feature invocations, and behavioral differences between modes.
 *
 * Usage:
 *   import { analyzeBenchmarkSession, compareSessionsimport { analyzeBenchmarkSession, compareSessions } from './analyzer.js';
 */

import type { BenchmarkResult } from '../types.js';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';

/**
 * Detailed tool call information
 */
export interface ToolCallInfo {
  id: string;
  name: string;
  input: Record<string, any>;
  timestamp: string;
}

/**
 * Session telemetry data
 */
export interface SessionTelemetry {
  taskId: string;
  mode: string;
  success: boolean;
  durationSeconds: number;
  tokens: {
    input: number;
    output: number;
    total: number;
  };
  toolCalls: number;
  costUsd: number;

  // Tool usage breakdown
  toolUsage: Record<string, number>;

  // PopKit feature usage
  popkitFeatures: {
    skills: string[];
    agents: string[];
    commands: string[];
    hooks: string[];
  };

  // Detailed tool calls
  toolCallDetails: ToolCallInfo[];

  // Test results
  testsPassed: number;
  testsTotal: number;
  testResults: Array<{
    name: string;
    passed: boolean;
    error?: string;
  }>;
}

/**
 * Comparison result between two sessions
 */
export interface SessionComparison {
  vanilla: SessionTelemetry;
  popkit: SessionTelemetry;

  differences: {
    durationDiff: number;
    durationDiffPct: number;
    toolCallsDiff: number;
    tokensDiff: number;
    costDiff: number;

    // Tool usage differences
    toolsOnlyInVanilla: string[];
    toolsOnlyInPopkit: string[];
    toolFrequencyDiff: Record<string, { vanilla: number; popkit: number; diff: number }>;

    // PopKit features used
    popkitFeaturesUsed: string[];

    // Quality differences
    testResultsSame: boolean;
  };

  insights: string[];
}

/**
 * Load session data from results directory
 */
export async function loadSessionData(resultsDir: string): Promise<SessionTelemetry> {
  // Read session.json
  const sessionPath = join(resultsDir, 'session.json');
  const sessionData = JSON.parse(await readFile(sessionPath, 'utf-8'));

  // Read tool-calls.json
  const toolCallsPath = join(resultsDir, 'tool-calls.json');
  const toolCalls: ToolCallInfo[] = JSON.parse(await readFile(toolCallsPath, 'utf-8'));

  // Count tool usage
  const toolUsage: Record<string, number> = {};
  for (const call of toolCalls) {
    toolUsage[call.name] = (toolUsage[call.name] || 0) + 1;
  }

  // Detect PopKit features used
  const popkitFeatures = {
    skills: [] as string[],
    agents: [] as string[],
    commands: [] as string[],
    hooks: [] as string[],
  };

  // Check for Skill tool calls
  const skillCalls = toolCalls.filter(c => c.name === 'Skill');
  for (const call of skillCalls) {
    const skillName = call.input.skill || 'unknown';
    popkitFeatures.skills.push(skillName);
  }

  // Check for SlashCommand calls (PopKit commands start with /popkit:)
  const commandCalls = toolCalls.filter(c => c.name === 'SlashCommand');
  for (const call of commandCalls) {
    const command = call.input.command || '';
    if (command.startsWith('/popkit:')) {
      popkitFeatures.commands.push(command);
    }
  }

  // Check for Task tool calls (agent invocations)
  const taskCalls = toolCalls.filter(c => c.name === 'Task');
  for (const call of taskCalls) {
    const agentType = call.input.subagent_type || 'unknown';
    popkitFeatures.agents.push(agentType);
  }

  // Extract test results
  const testResults = sessionData.testResults || [];
  const testsPassed = testResults.filter((t: any) => t.passed).length;

  return {
    taskId: sessionData.taskId,
    mode: sessionData.mode,
    success: sessionData.success,
    durationSeconds: sessionData.durationSeconds,
    tokens: sessionData.tokens,
    toolCalls: sessionData.toolCalls,
    costUsd: sessionData.usageDetails?.costUsd || 0,
    toolUsage,
    popkitFeatures,
    toolCallDetails: toolCalls,
    testsPassed,
    testsTotal: testResults.length,
    testResults,
  };
}

/**
 * Compare two benchmark sessions (vanilla vs popkit)
 */
export function compareSessions(
  vanilla: SessionTelemetry,
  popkit: SessionTelemetry
): SessionComparison {
  // Calculate basic differences
  const durationDiff = popkit.durationSeconds - vanilla.durationSeconds;
  const durationDiffPct = (durationDiff / vanilla.durationSeconds) * 100;
  const toolCallsDiff = popkit.toolCalls - vanilla.toolCalls;
  const tokensDiff = popkit.tokens.total - vanilla.tokens.total;
  const costDiff = popkit.costUsd - vanilla.costUsd;

  // Find tool usage differences
  const allTools = new Set([
    ...Object.keys(vanilla.toolUsage),
    ...Object.keys(popkit.toolUsage),
  ]);

  const toolsOnlyInVanilla: string[] = [];
  const toolsOnlyInPopkit: string[] = [];
  const toolFrequencyDiff: Record<string, { vanilla: number; popkit: number; diff: number }> = {};

  for (const tool of allTools) {
    const vanillaCount = vanilla.toolUsage[tool] || 0;
    const popkitCount = popkit.toolUsage[tool] || 0;

    if (vanillaCount > 0 && popkitCount === 0) {
      toolsOnlyInVanilla.push(tool);
    } else if (vanillaCount === 0 && popkitCount > 0) {
      toolsOnlyInPopkit.push(tool);
    }

    if (vanillaCount !== popkitCount) {
      toolFrequencyDiff[tool] = {
        vanilla: vanillaCount,
        popkit: popkitCount,
        diff: popkitCount - vanillaCount,
      };
    }
  }

  // Check PopKit features
  const popkitFeaturesUsed = [
    ...popkit.popkitFeatures.skills.map(s => `skill:${s}`),
    ...popkit.popkitFeatures.agents.map(a => `agent:${a}`),
    ...popkit.popkitFeatures.commands.map(c => c),
  ];

  // Test results comparison
  const testResultsSame =
    vanilla.testsPassed === popkit.testsPassed &&
    vanilla.testsTotal === popkit.testsTotal;

  // Generate insights
  const insights: string[] = [];

  // Duration insight
  if (durationDiffPct > 50) {
    insights.push(`PopKit was ${durationDiffPct.toFixed(0)}% slower (${durationDiff.toFixed(1)}s)`);
  } else if (durationDiffPct < -20) {
    insights.push(`PopKit was ${Math.abs(durationDiffPct).toFixed(0)}% faster (${Math.abs(durationDiff).toFixed(1)}s)`);
  }

  // Tool usage insight
  if (toolCallsDiff > 0) {
    insights.push(`PopKit made ${toolCallsDiff} more tool calls`);
  }

  // TodoWrite specific insight
  const vanillaTodoWrite = vanilla.toolUsage.TodoWrite || 0;
  const popkitTodoWrite = popkit.toolUsage.TodoWrite || 0;
  if (popkitTodoWrite > vanillaTodoWrite) {
    insights.push(`PopKit used TodoWrite ${popkitTodoWrite}x (vanilla: ${vanillaTodoWrite}x) - NOT a PopKit feature!`);
  }

  // PopKit features insight
  if (popkitFeaturesUsed.length === 0) {
    insights.push('⚠️ NO PopKit features (skills/agents/commands) were actually invoked');
  } else {
    insights.push(`PopKit features used: ${popkitFeaturesUsed.join(', ')}`);
  }

  // Cost insight
  if (costDiff > 0.05) {
    insights.push(`PopKit cost $${costDiff.toFixed(2)} more`);
  }

  // Test results insight
  if (testResultsSame) {
    insights.push('Both modes passed all tests');
  } else {
    insights.push(`Test results differ: vanilla ${vanilla.testsPassed}/${vanilla.testsTotal}, popkit ${popkit.testsPassed}/${popkit.testsTotal}`);
  }

  return {
    vanilla,
    popkit,
    differences: {
      durationDiff,
      durationDiffPct,
      toolCallsDiff,
      tokensDiff,
      costDiff,
      toolsOnlyInVanilla,
      toolsOnlyInPopkit,
      toolFrequencyDiff,
      popkitFeaturesUsed,
      testResultsSame,
    },
    insights,
  };
}

/**
 * Generate a summary report of the comparison
 */
export function generateComparisonReport(comparison: SessionComparison): string {
  const lines: string[] = [];

  lines.push('='.repeat(80));
  lines.push('BENCHMARK COMPARISON REPORT');
  lines.push('='.repeat(80));
  lines.push('');

  // Basic info
  lines.push(`Task: ${comparison.vanilla.taskId}`);
  lines.push(`Modes: ${comparison.vanilla.mode} vs ${comparison.popkit.mode}`);
  lines.push('');

  // Summary table
  lines.push('SUMMARY');
  lines.push('-'.repeat(80));
  lines.push(`Metric                 Vanilla          PopKit           Difference`);
  lines.push('-'.repeat(80));
  lines.push(
    `Duration               ${comparison.vanilla.durationSeconds.toFixed(1)}s           ` +
    `${comparison.popkit.durationSeconds.toFixed(1)}s           ` +
    `${comparison.differences.durationDiff > 0 ? '+' : ''}${comparison.differences.durationDiff.toFixed(1)}s (${comparison.differences.durationDiffPct > 0 ? '+' : ''}${comparison.differences.durationDiffPct.toFixed(0)}%)`
  );
  lines.push(
    `Tool Calls             ${comparison.vanilla.toolCalls}                ` +
    `${comparison.popkit.toolCalls}                ` +
    `${comparison.differences.toolCallsDiff > 0 ? '+' : ''}${comparison.differences.toolCallsDiff}`
  );
  lines.push(
    `Tokens                 ${comparison.vanilla.tokens.total}              ` +
    `${comparison.popkit.tokens.total}             ` +
    `${comparison.differences.tokensDiff > 0 ? '+' : ''}${comparison.differences.tokensDiff}`
  );
  lines.push(
    `Cost                   $${comparison.vanilla.costUsd.toFixed(2)}           ` +
    `$${comparison.popkit.costUsd.toFixed(2)}          ` +
    `$${comparison.differences.costDiff > 0 ? '+' : ''}${comparison.differences.costDiff.toFixed(2)}`
  );
  lines.push(
    `Tests Passed           ${comparison.vanilla.testsPassed}/${comparison.vanilla.testsTotal}              ` +
    `${comparison.popkit.testsPassed}/${comparison.popkit.testsTotal}              ` +
    `${comparison.differences.testResultsSame ? 'Same' : 'Different'}`
  );
  lines.push('');

  // Tool usage breakdown
  lines.push('TOOL USAGE');
  lines.push('-'.repeat(80));

  const allTools = new Set([
    ...Object.keys(comparison.vanilla.toolUsage),
    ...Object.keys(comparison.popkit.toolUsage),
  ]);

  for (const tool of Array.from(allTools).sort()) {
    const vanillaCount = comparison.vanilla.toolUsage[tool] || 0;
    const popkitCount = comparison.popkit.toolUsage[tool] || 0;
    const diff = popkitCount - vanillaCount;

    lines.push(
      `${tool.padEnd(20)} ` +
      `${vanillaCount.toString().padStart(8)} ` +
      `${popkitCount.toString().padStart(8)} ` +
      `${(diff > 0 ? '+' : '') + diff.toString().padStart(8)}`
    );
  }
  lines.push('');

  // PopKit features
  if (comparison.differences.popkitFeaturesUsed.length > 0) {
    lines.push('POPKIT FEATURES USED');
    lines.push('-'.repeat(80));
    for (const feature of comparison.differences.popkitFeaturesUsed) {
      lines.push(`  • ${feature}`);
    }
    lines.push('');
  } else {
    lines.push('⚠️ NO POPKIT FEATURES USED');
    lines.push('-'.repeat(80));
    lines.push('PopKit mode did not invoke any skills, agents, or commands.');
    lines.push('This suggests the benchmark task did not trigger PopKit features.');
    lines.push('');
  }

  // Key insights
  lines.push('KEY INSIGHTS');
  lines.push('-'.repeat(80));
  for (const insight of comparison.insights) {
    lines.push(`  • ${insight}`);
  }
  lines.push('');

  lines.push('='.repeat(80));

  return lines.join('\n');
}

/**
 * Analyze a benchmark session and return telemetry
 */
export async function analyzeBenchmarkSession(resultsDir: string): Promise<SessionTelemetry> {
  return await loadSessionData(resultsDir);
}
