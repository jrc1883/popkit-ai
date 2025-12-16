/**
 * PopKit Self-Testing Framework - Behavior Validator (Issue #258)
 *
 * Validates captured behavior against expectations, generating violations
 * and calculating behavior scores. Core validation engine for self-testing.
 *
 * Design: docs/designs/self-testing-framework-design.md
 */

import { BehaviorCapture } from '../behavior/schema.js';
import {
  BehaviorExpectations,
  BehaviorViolation,
  ValidationResult,
  ViolationSeverity,
} from './expectations.js';

export class BehaviorValidator {
  private expectations: BehaviorExpectations;
  private capture: BehaviorCapture;
  private violations: BehaviorViolation[] = [];

  constructor(expectations: BehaviorExpectations, capture: BehaviorCapture) {
    this.expectations = expectations;
    this.capture = capture;
  }

  /**
   * Run all validations and return result
   */
  validate(): ValidationResult {
    this.violations = [];

    // Run all validation checks
    this.validateAgents();
    this.validateSkills();
    this.validateTools();
    this.validateRouting();
    this.validateWorkflows();
    this.validatePerformance();
    this.validateDecisions();

    // Calculate score and summary
    return this.buildResult();
  }

  private validateAgents(): void {
    if (!this.expectations.agents) return;

    // Check shouldInvoke agents
    if (this.expectations.agents.shouldInvoke) {
      for (const expectation of this.expectations.agents.shouldInvoke) {
        const invocations = this.capture.agents.invocations.filter((inv) =>
          expectation.agents.includes(inv.agent_name)
        );

        if (invocations.length === 0) {
          this.violations.push({
            category: 'agent',
            severity: expectation.required ? 'critical' : 'major',
            expected: `Agent(s) ${expectation.agents.join(', ')} should be invoked`,
            actual: 'Not invoked',
            reason: expectation.reason,
          });
        } else if (expectation.invocationCount) {
          this.validateInvocationCount(
            invocations.length,
            expectation.invocationCount,
            expectation.agents.join(', '),
            expectation.reason,
            expectation.required
          );
        }
      }
    }

    // Check shouldNotInvoke agents
    if (this.expectations.agents.shouldNotInvoke) {
      for (const expectation of this.expectations.agents.shouldNotInvoke) {
        const invocations = this.capture.agents.invocations.filter((inv) =>
          expectation.agents.includes(inv.agent_name)
        );

        if (invocations.length > 0) {
          this.violations.push({
            category: 'agent',
            severity: expectation.required ? 'critical' : 'major',
            expected: `Agent(s) ${expectation.agents.join(', ')} should NOT be invoked`,
            actual: `Invoked ${invocations.length} time(s)`,
            reason: expectation.reason,
          });
        }
      }
    }

    // Check exclusive invocation
    if (this.expectations.agents.exclusiveInvocation) {
      const { agents, reason } = this.expectations.agents.exclusiveInvocation;
      const otherInvocations = this.capture.agents.invocations.filter(
        (inv) => !agents.includes(inv.agent_name)
      );

      if (otherInvocations.length > 0) {
        this.violations.push({
          category: 'agent',
          severity: 'major',
          expected: `Only agent(s) ${agents.join(', ')} should be invoked`,
          actual: `Also invoked: ${otherInvocations.map((i) => i.agent_name).join(', ')}`,
          reason,
        });
      }
    }
  }

  private validateInvocationCount(
    actual: number,
    expected: { exact?: number; min?: number; max?: number },
    agentName: string,
    reason: string,
    critical: boolean
  ): void {
    if (expected.exact !== undefined && actual !== expected.exact) {
      this.violations.push({
        category: 'agent',
        severity: critical ? 'critical' : 'major',
        expected: `Agent ${agentName} invoked exactly ${expected.exact} time(s)`,
        actual: `Invoked ${actual} time(s)`,
        reason,
      });
    }
    if (expected.min !== undefined && actual < expected.min) {
      this.violations.push({
        category: 'agent',
        severity: critical ? 'critical' : 'major',
        expected: `Agent ${agentName} invoked at least ${expected.min} time(s)`,
        actual: `Invoked ${actual} time(s)`,
        reason,
      });
    }
    if (expected.max !== undefined && actual > expected.max) {
      this.violations.push({
        category: 'agent',
        severity: 'minor',
        expected: `Agent ${agentName} invoked at most ${expected.max} time(s)`,
        actual: `Invoked ${actual} time(s)`,
        reason,
      });
    }
  }

  private validateSkills(): void {
    if (!this.expectations.skills) return;

    // Check shouldInvoke skills
    if (this.expectations.skills.shouldInvoke) {
      for (const expectation of this.expectations.skills.shouldInvoke) {
        const executions = this.capture.skills.executions.filter((exec) =>
          expectation.skills.includes(exec.skill_name)
        );

        if (executions.length === 0) {
          this.violations.push({
            category: 'skill',
            severity: expectation.required ? 'critical' : 'major',
            expected: `Skill(s) ${expectation.skills.join(', ')} should be executed`,
            actual: 'Not executed',
            reason: expectation.reason,
          });
        }
      }
    }

    // Check shouldNotInvoke skills
    if (this.expectations.skills.shouldNotInvoke) {
      for (const expectation of this.expectations.skills.shouldNotInvoke) {
        const executions = this.capture.skills.executions.filter((exec) =>
          expectation.skills.includes(exec.skill_name)
        );

        if (executions.length > 0) {
          this.violations.push({
            category: 'skill',
            severity: expectation.required ? 'critical' : 'major',
            expected: `Skill(s) ${expectation.skills.join(', ')} should NOT be executed`,
            actual: `Executed ${executions.length} time(s)`,
            reason: expectation.reason,
          });
        }
      }
    }
  }

  private validateTools(): void {
    if (!this.expectations.tools) return;

    // Check expected patterns
    if (this.expectations.tools.expectedPatterns) {
      for (const expectation of this.expectations.tools.expectedPatterns) {
        const matches = this.capture.tools.calls.filter((call) =>
          this.matchesToolPattern(call.tool_name, expectation.pattern)
        );

        if (expectation.minOccurrences && matches.length < expectation.minOccurrences) {
          this.violations.push({
            category: 'tool',
            severity: expectation.severity,
            expected: `Tool ${expectation.pattern} called at least ${expectation.minOccurrences} time(s)`,
            actual: `Called ${matches.length} time(s)`,
            reason: expectation.reason,
          });
        }
      }
    }

    // Check forbidden patterns
    if (this.expectations.tools.forbiddenPatterns) {
      for (const expectation of this.expectations.tools.forbiddenPatterns) {
        const matches = this.capture.tools.calls.filter((call) =>
          this.matchesToolPattern(call.tool_name, expectation.pattern)
        );

        if (matches.length > 0) {
          this.violations.push({
            category: 'tool',
            severity: expectation.severity,
            expected: `Tool ${expectation.pattern} should NOT be called`,
            actual: `Called ${matches.length} time(s)`,
            reason: expectation.reason,
          });
        }
      }
    }

    // Check sequences
    if (this.expectations.tools.sequences?.antiPatterns) {
      this.validateToolSequences();
    }
  }

  private matchesToolPattern(toolName: string, pattern: string): boolean {
    // Support exact match or glob-like pattern (e.g., "Glob:*.tsx")
    if (pattern.includes(':')) {
      const [tool, arg] = pattern.split(':', 2);
      return toolName === tool;
    }
    return toolName === pattern;
  }

  private validateToolSequences(): void {
    if (!this.expectations.tools?.sequences?.antiPatterns) return;

    const toolNames = this.capture.tools.calls.map((c) => c.tool_name);

    for (const antiPattern of this.expectations.tools.sequences.antiPatterns) {
      const occurrences = this.countSequenceOccurrences(toolNames, antiPattern.sequence);

      if (occurrences > 0) {
        this.violations.push({
          category: 'tool',
          severity: antiPattern.severity,
          expected: `Anti-pattern ${antiPattern.sequence.join(' → ')} should NOT occur`,
          actual: `Occurred ${occurrences} time(s)`,
          reason: antiPattern.reason,
        });
      }
    }
  }

  private countSequenceOccurrences(tools: string[], sequence: string[]): number {
    let count = 0;
    for (let i = 0; i <= tools.length - sequence.length; i++) {
      if (sequence.every((tool, j) => tools[i + j] === tool)) {
        count++;
      }
    }
    return count;
  }

  private validateRouting(): void {
    if (!this.expectations.routing) return;

    // Check expected triggers
    if (this.expectations.routing.expectedTriggers) {
      for (const expected of this.expectations.routing.expectedTriggers) {
        const found = this.capture.routing.decisions.some(
          (decision) =>
            decision.trigger.type === expected.type && decision.trigger.value === expected.value
        );

        if (!found) {
          this.violations.push({
            category: 'routing',
            severity: 'major',
            expected: `Routing trigger ${expected.type}:${expected.value}`,
            actual: 'Not triggered',
            reason: 'Expected routing decision not made',
          });
        }
      }
    }

    // Check agent selection
    if (this.expectations.routing.agentSelection) {
      const { shouldConsider, shouldNotConsider } = this.expectations.routing.agentSelection;

      if (shouldConsider) {
        const considered = new Set(this.capture.routing.agents_considered.map((a) => a.agent));
        for (const agent of shouldConsider) {
          if (!considered.has(agent)) {
            this.violations.push({
              category: 'routing',
              severity: 'major',
              expected: `Agent ${agent} should be considered`,
              actual: 'Not considered',
              reason: 'Routing should evaluate this agent',
            });
          }
        }
      }

      if (shouldNotConsider) {
        const considered = new Set(this.capture.routing.agents_considered.map((a) => a.agent));
        for (const agent of shouldNotConsider) {
          if (considered.has(agent)) {
            this.violations.push({
              category: 'routing',
              severity: 'minor',
              expected: `Agent ${agent} should NOT be considered`,
              actual: 'Was considered',
              reason: 'Routing should not evaluate irrelevant agents',
            });
          }
        }
      }
    }
  }

  private validateWorkflows(): void {
    if (!this.expectations.workflows) return;

    // Check workflow type
    if (this.expectations.workflows.workflowType) {
      const activeWorkflows = this.capture.workflows.active_workflows;
      const matchingWorkflows = activeWorkflows.filter(
        (wf) => wf.workflow_type === this.expectations.workflows!.workflowType
      );

      if (matchingWorkflows.length === 0 && activeWorkflows.length > 0) {
        this.violations.push({
          category: 'workflow',
          severity: 'major',
          expected: `Workflow type: ${this.expectations.workflows.workflowType}`,
          actual: activeWorkflows.length > 0 ? activeWorkflows[0].workflow_type : 'none',
          reason: 'Wrong workflow type used',
        });
      }
    }

    // Check phases
    if (this.expectations.workflows.phases) {
      const transitions = this.capture.workflows.phase_transitions;
      const actualPhases = new Set(transitions.map((t) => t.to_phase));

      if (this.expectations.workflows.phases.expectedPhases) {
        for (const phase of this.expectations.workflows.phases.expectedPhases) {
          if (!actualPhases.has(phase)) {
            this.violations.push({
              category: 'workflow',
              severity: 'major',
              expected: `Workflow should include phase: ${phase}`,
              actual: `Phase not reached`,
              reason: 'Expected workflow phase missing',
            });
          }
        }
      }
    }
  }

  private validatePerformance(): void {
    if (!this.expectations.performance) return;

    const perf = this.capture.performance;

    if (this.expectations.performance.maxRoutingTimeMs !== undefined) {
      if (perf.routing_time_ms > this.expectations.performance.maxRoutingTimeMs) {
        this.violations.push({
          category: 'performance',
          severity: 'minor',
          expected: `Routing time ≤ ${this.expectations.performance.maxRoutingTimeMs}ms`,
          actual: `${perf.routing_time_ms}ms`,
          reason: 'Routing took too long',
        });
      }
    }

    if (this.expectations.performance.maxToolCalls !== undefined) {
      if (perf.tool_call_count > this.expectations.performance.maxToolCalls) {
        this.violations.push({
          category: 'performance',
          severity: 'minor',
          expected: `Tool calls ≤ ${this.expectations.performance.maxToolCalls}`,
          actual: `${perf.tool_call_count}`,
          reason: 'Too many tool calls (inefficient)',
        });
      }
    }

    if (this.expectations.performance.maxAgentInvocations !== undefined) {
      if (perf.agent_invocation_count > this.expectations.performance.maxAgentInvocations) {
        this.violations.push({
          category: 'performance',
          severity: 'minor',
          expected: `Agent invocations ≤ ${this.expectations.performance.maxAgentInvocations}`,
          actual: `${perf.agent_invocation_count}`,
          reason: 'Too many agent invocations',
        });
      }
    }
  }

  private validateDecisions(): void {
    if (!this.expectations.decisions) return;

    const decisionCount = this.capture.decisions.total_decisions;

    if (this.expectations.decisions.minimumDecisions !== undefined) {
      if (decisionCount < this.expectations.decisions.minimumDecisions) {
        this.violations.push({
          category: 'decision',
          severity: 'major',
          expected: `At least ${this.expectations.decisions.minimumDecisions} user decisions`,
          actual: `${decisionCount} decisions`,
          reason: 'Task should involve user input',
        });
      }
    }

    if (this.expectations.decisions.maximumDecisions !== undefined) {
      if (decisionCount > this.expectations.decisions.maximumDecisions) {
        this.violations.push({
          category: 'decision',
          severity: 'minor',
          expected: `At most ${this.expectations.decisions.maximumDecisions} user decisions`,
          actual: `${decisionCount} decisions`,
          reason: 'Too many user interruptions',
        });
      }
    }
  }

  private buildResult(): ValidationResult {
    const critical = this.violations.filter((v) => v.severity === 'critical');
    const major = this.violations.filter((v) => v.severity === 'major');
    const minor = this.violations.filter((v) => v.severity === 'minor');

    // Score calculation: 100 - (critical*20 + major*10 + minor*5)
    const score = Math.max(
      0,
      100 - (critical.length * 20 + major.length * 10 + minor.length * 5)
    );

    // Generate insights and recommendations
    const insights = this.generateInsights();
    const recommendations = this.generateRecommendations();

    return {
      taskId: this.expectations.taskId,
      mode: this.expectations.mode,
      timestamp: new Date().toISOString(),
      score,
      passed: score >= 80,
      violations: { critical, major, minor },
      summary: {
        totalViolations: this.violations.length,
        criticalCount: critical.length,
        majorCount: major.length,
        minorCount: minor.length,
        passedChecks: this.countPassedChecks(),
        totalChecks: this.countTotalChecks(),
      },
      insights,
      recommendations,
    };
  }

  private countPassedChecks(): number {
    let total = this.countTotalChecks();
    return total - this.violations.length;
  }

  private countTotalChecks(): number {
    let count = 0;
    if (this.expectations.agents?.shouldInvoke) count += this.expectations.agents.shouldInvoke.length;
    if (this.expectations.agents?.shouldNotInvoke) count += this.expectations.agents.shouldNotInvoke.length;
    if (this.expectations.skills?.shouldInvoke) count += this.expectations.skills.shouldInvoke.length;
    if (this.expectations.skills?.shouldNotInvoke) count += this.expectations.skills.shouldNotInvoke.length;
    if (this.expectations.tools?.expectedPatterns) count += this.expectations.tools.expectedPatterns.length;
    if (this.expectations.tools?.forbiddenPatterns) count += this.expectations.tools.forbiddenPatterns.length;
    if (this.expectations.routing?.expectedTriggers) count += this.expectations.routing.expectedTriggers.length;
    if (this.expectations.workflows?.phases?.expectedPhases) count += this.expectations.workflows.phases.expectedPhases.length;
    if (this.expectations.performance) count += Object.keys(this.expectations.performance).length;
    if (this.expectations.decisions?.minimumDecisions) count++;
    if (this.expectations.decisions?.maximumDecisions) count++;
    return count;
  }

  private generateInsights(): string[] {
    const insights: string[] = [];

    if (this.violations.length === 0) {
      insights.push('Perfect behavior! All expectations met.');
    }

    if (this.capture.agents.total_invoked === 0) {
      insights.push('No agents were invoked - task completed without orchestration');
    }

    if (this.capture.performance.tool_call_count > 50) {
      insights.push('High tool call count - consider optimizing task efficiency');
    }

    return insights;
  }

  private generateRecommendations(): string[] {
    const recommendations: string[] = [];

    const critical = this.violations.filter((v) => v.severity === 'critical');
    if (critical.length > 0) {
      recommendations.push(`Fix ${critical.length} critical violation(s) before proceeding`);
    }

    const agentViolations = this.violations.filter((v) => v.category === 'agent');
    if (agentViolations.length > 0) {
      recommendations.push('Review agent routing configuration in agents/config.json');
    }

    return recommendations;
  }
}
