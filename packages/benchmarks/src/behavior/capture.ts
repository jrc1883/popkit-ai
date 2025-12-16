import { Readable } from 'stream';
import { BehaviorCapture } from './schema.js';

interface TelemetryEvent {
  type: string;
  timestamp: string;
  session_id: string;
  data: Record<string, unknown>;
}

export class BehaviorCaptureService {
  private taskId: string;
  private mode: 'vanilla' | 'popkit' | 'power';
  private sessionId: string;
  private events: TelemetryEvent[] = [];
  private startTime: number;

  constructor(taskId: string, mode: 'vanilla' | 'popkit' | 'power', sessionId: string) {
    this.taskId = taskId;
    this.mode = mode;
    this.sessionId = sessionId;
    this.startTime = Date.now();
  }

  attachToProcess(stdout: Readable): void {
    let buffer = '';
    stdout.on('data', (chunk: Buffer) => {
      buffer += chunk.toString();
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';
      for (const line of lines) {
        this.processLine(line);
      }
    });
    stdout.on('end', () => {
      if (buffer.trim()) this.processLine(buffer);
    });
  }

  processLine(line: string): void {
    const trimmed = line.trim();
    if (!trimmed.startsWith('TELEMETRY:')) return;
    try {
      const jsonStr = trimmed.substring(10);
      const event = JSON.parse(jsonStr) as TelemetryEvent;
      this.events.push(event);
    } catch (error) {
      console.error('Failed to parse telemetry');
    }
  }

  buildBehaviorCapture(): BehaviorCapture {
    return {
      metadata: {
        task_id: this.taskId,
        mode: this.mode,
        capture_version: '1.0.0',
        timestamp: new Date().toISOString(),
        session_id: this.sessionId,
        test_mode: true,
      },
      routing: { decisions: [], agents_considered: [], agents_selected: [], routing_strategy: 'manual' },
      agents: { invocations: [], total_invoked: 0, agents_by_category: {}, parallel_groups: [] },
      skills: { executions: [], total_executed: 0, skills_by_type: {} },
      workflows: { active_workflows: [], phase_transitions: [], total_workflows: 0 },
      tools: { calls: [], total_calls: 0, calls_by_tool: {}, patterns: [], sequence_analysis: { common_sequences: [], anti_patterns: [], efficiency_score: 100, insights: [] } },
      decisions: { user_decisions: [], total_decisions: 0 },
      performance: {
        total_duration_ms: Date.now() - this.startTime,
        routing_time_ms: 0,
        agent_execution_time_ms: 0,
        skill_execution_time_ms: 0,
        tool_call_count: 0,
        agent_invocation_count: 0,
        skill_invocation_count: 0,
      },
      insights: [`Captured ${this.events.length} events`],
      warnings: [],
    };
  }
}
