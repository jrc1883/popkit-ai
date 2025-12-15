/**
 * PopKit Benchmark Framework - Raw Stream Analyzer
 *
 * Analyzes raw stream-json output from Claude Code CLI to understand
 * PopKit orchestration behavior, command expansions, and routing decisions.
 *
 * The stream-json format contains events like:
 * - tool_use: Tool invocations with input
 * - tool_result: Tool outputs
 * - text: Claude's text responses
 * - thinking: Extended thinking blocks
 * - command-message: Slash command expansions
 */

import { readFile } from 'node:fs/promises';
import { join } from 'node:path';

/**
 * Stream event types from Claude Code CLI
 */
export type StreamEventType =
  | 'tool_use'
  | 'tool_result'
  | 'text'
  | 'thinking'
  | 'command-message'
  | 'system'
  | 'user'
  | 'assistant';

/**
 * Parsed stream event
 */
export interface StreamEvent {
  type: StreamEventType;
  timestamp?: string;
  data: any;
}

/**
 * Command expansion event
 */
export interface CommandExpansion {
  command: string;
  expandedPrompt: string;
  timestamp: string;
  promptLength: number;
}

/**
 * Orchestration decision (routing, mode selection)
 */
export interface OrchestrationDecision {
  type: 'mode_selection' | 'routing' | 'workflow_phase';
  decision: string;
  reasoning?: string;
  timestamp: string;
  context: string;
}

/**
 * Tool call with timing
 */
export interface TimedToolCall {
  id: string;
  name: string;
  input: Record<string, any>;
  output?: string;
  timestamp: string;
  durationMs?: number;
}

/**
 * Analysis of raw stream data
 */
export interface StreamAnalysis {
  // Command expansions
  commandExpansions: CommandExpansion[];

  // Orchestration decisions
  orchestrationDecisions: OrchestrationDecision[];

  // Tool calls with timing
  timedToolCalls: TimedToolCall[];

  // Thinking blocks
  thinkingBlocks: Array<{
    content: string;
    timestamp: string;
    lengthChars: number;
  }>;

  // Text responses
  textResponses: Array<{
    content: string;
    timestamp: string;
  }>;

  // Statistics
  stats: {
    totalEvents: number;
    commandExpansionCount: number;
    orchestrationDecisionCount: number;
    thinkingBlockCount: number;
    totalThinkingChars: number;
    avgThinkingBlockLength: number;
  };
}

/**
 * Parse raw stream-json output
 */
export async function parseRawStream(streamPath: string): Promise<StreamEvent[]> {
  const content = await readFile(streamPath, 'utf-8');
  const lines = content.trim().split('\n');
  const events: StreamEvent[] = [];

  for (const line of lines) {
    if (!line.trim()) continue;

    try {
      const data = JSON.parse(line);
      // The data object IS the event, with type already set
      const event: StreamEvent = {
        type: data.type || 'unknown',
        timestamp: data.timestamp || new Date().toISOString(),
        data,
      };
      events.push(event);
    } catch (e) {
      // Skip malformed lines
      console.warn(`Skipping malformed JSON line: ${line.substring(0, 100)}...`);
    }
  }

  return events;
}

/**
 * Extract command expansions from stream events
 */
export function extractCommandExpansions(events: StreamEvent[]): CommandExpansion[] {
  const expansions: CommandExpansion[] = [];

  for (let i = 0; i < events.length; i++) {
    const event = events[i];

    // Look for assistant messages with SlashCommand tool use
    if (event.type === 'assistant' && event.data.message?.content) {
      const content = event.data.message.content;

      // Find SlashCommand tool_use
      for (const item of content) {
        if (item.type === 'tool_use' && item.name === 'SlashCommand') {
          const command = item.input?.command || '';

          // Find the corresponding command expansion in next user messages
          for (let j = i + 1; j < Math.min(i + 5, events.length); j++) {
            const nextEvent = events[j];

            if (nextEvent.type === 'user' && nextEvent.data.message?.content) {
              const userContent = nextEvent.data.message.content;

              // Check for command-message in content
              for (const userItem of userContent) {
                if (userItem.type === 'text' && userItem.text?.includes('<command-message>')) {
                  // Next event should have the full expansion
                  if (j + 1 < events.length) {
                    const expansionEvent = events[j + 1];
                    if (expansionEvent.type === 'user' && expansionEvent.data.message?.content) {
                      const expansionContent = expansionEvent.data.message.content;
                      for (const expItem of expansionContent) {
                        if (expItem.type === 'text' && expItem.text) {
                          expansions.push({
                            command,
                            expandedPrompt: expItem.text,
                            timestamp: event.timestamp || '',
                            promptLength: expItem.text.length,
                          });
                        }
                      }
                    }
                  }
                }
              }
            }
          }
        }
      }
    }
  }

  return expansions;
}

/**
 * Extract orchestration decisions from text responses
 */
export function extractOrchestrationDecisions(events: StreamEvent[]): OrchestrationDecision[] {
  const decisions: OrchestrationDecision[] = [];

  for (const event of events) {
    // Look at assistant messages for orchestration markers
    if (event.type === 'assistant' && event.data.message?.content) {
      const content = event.data.message.content;

      for (const item of content) {
        if (item.type === 'text' && item.text) {
          const text = item.text;

          // Check for mode selection markers
          const quickModeMatch = text.match(/\*\*\[QUICK MODE\]\*\*\s+(.+)/);
          if (quickModeMatch) {
            decisions.push({
              type: 'mode_selection',
              decision: 'Quick Mode',
              reasoning: quickModeMatch[1],
              timestamp: event.timestamp || '',
              context: text,
            });
          }

          const fullModeMatch = text.match(/\*\*\[FULL MODE\]\*\*\s+(.+)/);
          if (fullModeMatch) {
            decisions.push({
              type: 'mode_selection',
              decision: 'Full Mode',
              reasoning: fullModeMatch[1],
              timestamp: event.timestamp || '',
              context: text,
            });
          }

          // Check for routing decisions
          const routingMatch = text.match(/routing to (.+)/i);
          if (routingMatch) {
            decisions.push({
              type: 'routing',
              decision: routingMatch[1],
              timestamp: event.timestamp || '',
              context: text,
            });
          }

          // Check for workflow phase markers
          const phaseMatch = text.match(/\*\*Phase (\d+):\s+(.+?)\*\*/);
          if (phaseMatch) {
            decisions.push({
              type: 'workflow_phase',
              decision: `Phase ${phaseMatch[1]}: ${phaseMatch[2]}`,
              timestamp: event.timestamp || '',
              context: text,
            });
          }
        }
      }
    }
  }

  return decisions;
}

/**
 * Extract timed tool calls from stream events
 */
export function extractTimedToolCalls(events: StreamEvent[]): TimedToolCall[] {
  const calls: TimedToolCall[] = [];
  const pendingCalls = new Map<string, { call: TimedToolCall; startIndex: number }>();

  for (let i = 0; i < events.length; i++) {
    const event = events[i];

    // Tool use from assistant messages
    if (event.type === 'assistant' && event.data.message?.content) {
      const content = event.data.message.content;

      for (const item of content) {
        if (item.type === 'tool_use' && item.id && item.name) {
          const call: TimedToolCall = {
            id: item.id,
            name: item.name,
            input: item.input || {},
            timestamp: event.timestamp || '',
          };

          pendingCalls.set(call.id, { call, startIndex: i });
        }
      }
    }

    // Tool result from user messages
    if (event.type === 'user' && event.data.message?.content) {
      const content = event.data.message.content;

      for (const item of content) {
        if (item.type === 'tool_result' && item.tool_use_id) {
          const pending = pendingCalls.get(item.tool_use_id);
          if (pending) {
            pending.call.output = JSON.stringify(item.content || item);

            // Calculate duration based on event index (rough approximation)
            pending.call.durationMs = (i - pending.startIndex) * 100; // Assume ~100ms per event

            calls.push(pending.call);
            pendingCalls.delete(item.tool_use_id);
          }
        }
      }
    }
  }

  // Add any pending calls without results
  for (const [, { call }] of pendingCalls) {
    calls.push(call);
  }

  return calls;
}

/**
 * Extract thinking blocks from stream events
 */
export function extractThinkingBlocks(events: StreamEvent[]): Array<{
  content: string;
  timestamp: string;
  lengthChars: number;
}> {
  const blocks: Array<{ content: string; timestamp: string; lengthChars: number }> = [];

  for (const event of events) {
    if (event.type === 'assistant' && event.data.message?.content) {
      const content = event.data.message.content;

      for (const item of content) {
        if (item.type === 'thinking' && item.thinking) {
          blocks.push({
            content: item.thinking,
            timestamp: event.timestamp || '',
            lengthChars: item.thinking.length,
          });
        }
      }
    }
  }

  return blocks;
}

/**
 * Extract text responses from stream events
 */
export function extractTextResponses(events: StreamEvent[]): Array<{
  content: string;
  timestamp: string;
}> {
  const responses: Array<{ content: string; timestamp: string }> = [];

  for (const event of events) {
    if (event.type === 'assistant' && event.data.message?.content) {
      const content = event.data.message.content;

      for (const item of content) {
        if (item.type === 'text' && item.text && item.text.trim()) {
          responses.push({
            content: item.text,
            timestamp: event.timestamp || '',
          });
        }
      }
    }
  }

  return responses;
}

/**
 * Analyze raw stream data
 */
export async function analyzeRawStream(resultsDir: string): Promise<StreamAnalysis> {
  const streamPath = join(resultsDir, 'stream-raw.jsonl');

  // Parse events
  const events = await parseRawStream(streamPath);

  // Extract components
  const commandExpansions = extractCommandExpansions(events);
  const orchestrationDecisions = extractOrchestrationDecisions(events);
  const timedToolCalls = extractTimedToolCalls(events);
  const thinkingBlocks = extractThinkingBlocks(events);
  const textResponses = extractTextResponses(events);

  // Calculate statistics
  const totalThinkingChars = thinkingBlocks.reduce((sum, block) => sum + block.lengthChars, 0);
  const avgThinkingBlockLength =
    thinkingBlocks.length > 0 ? totalThinkingChars / thinkingBlocks.length : 0;

  return {
    commandExpansions,
    orchestrationDecisions,
    timedToolCalls,
    thinkingBlocks,
    textResponses,
    stats: {
      totalEvents: events.length,
      commandExpansionCount: commandExpansions.length,
      orchestrationDecisionCount: orchestrationDecisions.length,
      thinkingBlockCount: thinkingBlocks.length,
      totalThinkingChars,
      avgThinkingBlockLength,
    },
  };
}

/**
 * Generate a report from stream analysis
 */
export function generateStreamReport(analysis: StreamAnalysis): string {
  const lines: string[] = [];

  lines.push('='.repeat(80));
  lines.push('RAW STREAM ANALYSIS REPORT');
  lines.push('='.repeat(80));
  lines.push('');

  // Statistics
  lines.push('STATISTICS');
  lines.push('-'.repeat(80));
  lines.push(`Total Events:              ${analysis.stats.totalEvents}`);
  lines.push(`Command Expansions:        ${analysis.stats.commandExpansionCount}`);
  lines.push(`Orchestration Decisions:   ${analysis.stats.orchestrationDecisionCount}`);
  lines.push(`Thinking Blocks:           ${analysis.stats.thinkingBlockCount}`);
  lines.push(`Total Thinking Chars:      ${analysis.stats.totalThinkingChars}`);
  lines.push(`Avg Thinking Block Length: ${analysis.stats.avgThinkingBlockLength.toFixed(0)} chars`);
  lines.push('');

  // Command expansions
  if (analysis.commandExpansions.length > 0) {
    lines.push('COMMAND EXPANSIONS');
    lines.push('-'.repeat(80));
    for (const expansion of analysis.commandExpansions) {
      lines.push(`Command:      ${expansion.command}`);
      lines.push(`Timestamp:    ${expansion.timestamp}`);
      lines.push(`Prompt Size:  ${expansion.promptLength.toLocaleString()} chars`);
      lines.push(`Preview:      ${expansion.expandedPrompt.substring(0, 200)}...`);
      lines.push('');
    }
  }

  // Orchestration decisions
  if (analysis.orchestrationDecisions.length > 0) {
    lines.push('ORCHESTRATION DECISIONS');
    lines.push('-'.repeat(80));
    for (const decision of analysis.orchestrationDecisions) {
      lines.push(`Type:      ${decision.type}`);
      lines.push(`Decision:  ${decision.decision}`);
      if (decision.reasoning) {
        lines.push(`Reasoning: ${decision.reasoning}`);
      }
      lines.push(`Timestamp: ${decision.timestamp}`);
      lines.push('');
    }
  }

  // Tool call summary
  lines.push('TOOL CALL TIMELINE');
  lines.push('-'.repeat(80));
  const toolCounts: Record<string, number> = {};
  for (const call of analysis.timedToolCalls) {
    toolCounts[call.name] = (toolCounts[call.name] || 0) + 1;
  }
  for (const [tool, count] of Object.entries(toolCounts).sort((a, b) => b[1] - a[1])) {
    lines.push(`${tool.padEnd(20)} ${count}x`);
  }
  lines.push('');

  // Thinking blocks summary
  if (analysis.thinkingBlocks.length > 0) {
    lines.push('THINKING BLOCKS');
    lines.push('-'.repeat(80));
    lines.push(`Total blocks: ${analysis.thinkingBlocks.length}`);
    lines.push(`Total chars:  ${analysis.stats.totalThinkingChars.toLocaleString()}`);
    lines.push(`Average size: ${analysis.stats.avgThinkingBlockLength.toFixed(0)} chars`);
    lines.push('');

    // Show first thinking block preview
    if (analysis.thinkingBlocks.length > 0) {
      const firstBlock = analysis.thinkingBlocks[0];
      lines.push('First Thinking Block Preview:');
      lines.push(firstBlock.content.substring(0, 300) + '...');
      lines.push('');
    }
  }

  lines.push('='.repeat(80));

  return lines.join('\n');
}
