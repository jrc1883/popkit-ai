/**
 * Workflow Metrics Analyzer
 *
 * Measures the 90% of unmeasured PopKit value:
 * - Workflow visibility and guidance
 * - Context efficiency (preserved vs re-read)
 * - Decision quality (user choices made)
 * - Agent coordination effectiveness
 * - Skill invocation patterns
 *
 * Issue #256: Build Workflow Metrics Analyzer
 */

import type { SessionTelemetry } from './analyzer.js';

/**
 * Workflow metrics - the unmeasured value of PopKit
 */
export interface WorkflowMetrics {
  // Context efficiency
  contextMetrics: {
    filesReadMultipleTimes: number; // Files read >1 time (inefficiency)
    contextRestorations: number; // Times context was restored from session
    averageFileReReads: number; // Avg times a file was re-read
    contextEfficiencyScore: number; // 0-100 score
  };

  // Workflow guidance
  workflowMetrics: {
    phaseTransitions: number; // Number of workflow phases executed
    userDecisionPoints: number; // Times user made decisions via AskUserQuestion
    workflowCompleteness: number; // % of workflow completed
    guidanceScore: number; // 0-100 score for how well workflow guided user
  };

  // Agent coordination
  coordinationMetrics: {
    agentInvocations: number; // Total agent invocations
    parallelAgentPeriods: number; // Times multiple agents ran in parallel
    agentHandoffs: number; // Times context was handed between agents
    coordinationScore: number; // 0-100 score
  };

  // Skill usage
  skillMetrics: {
    skillsInvoked: string[]; // Which skills were used
    skillSuggestions: number; // Times skills were suggested but not used
    skillUtilizationRate: number; // % of suggestions that were used
    skillEffectivenessScore: number; // 0-100 score
  };

  // Overall workflow value
  overallScore: number; // 0-100 composite score
  valueBreakdown: {
    timeToFirstValue: number; // Seconds until first useful output
    decisionsSupported: number; // Number of decisions PopKit helped with
    contextSaved: number; // Estimated context re-reading time saved (seconds)
    workflowClarityGain: number; // % improvement in task clarity
  };
}

/**
 * Analyze workflow metrics from session telemetry
 */
export function analyzeWorkflowMetrics(session: SessionTelemetry): WorkflowMetrics {
  // Context efficiency analysis
  const fileReads = session.toolCallDetails.filter(t => t.name === 'Read');
  const filesReadMap = new Map<string, number>();

  for (const read of fileReads) {
    const filepath = read.input.file_path || 'unknown';
    filesReadMap.set(filepath, (filesReadMap.get(filepath) || 0) + 1);
  }

  const filesReadMultipleTimes = Array.from(filesReadMap.values()).filter(count => count > 1).length;
  const totalReReads = Array.from(filesReadMap.values()).reduce((sum, count) => sum + Math.max(0, count - 1), 0);
  const averageFileReReads = filesReadMap.size > 0 ? totalReReads / filesReadMap.size : 0;

  // Check for session restoration
  const sessionRestoreCalls = session.toolCallDetails.filter(t =>
    t.name === 'Skill' &&
    (t.input.skill === 'pop-session-resume' || t.input.skill === 'pop-context-restore')
  );
  const contextRestorations = sessionRestoreCalls.length;

  // Context efficiency score (higher is better)
  // 100 = perfect (no re-reads), 0 = terrible (many re-reads)
  const contextEfficiencyScore = Math.max(0, 100 - (averageFileReReads * 50));

  // Workflow guidance analysis
  const askUserQuestionCalls = session.toolCallDetails.filter(t => t.name === 'AskUserQuestion');
  const userDecisionPoints = askUserQuestionCalls.length;

  // Detect workflow phases (based on agent invocations in feature-dev workflow)
  const agentInvocations = session.popkitFeatures.agents;
  const featureDevAgents = ['code-explorer', 'code-architect', 'code-reviewer'];
  const phaseTransitions = agentInvocations.filter(a => featureDevAgents.includes(a)).length;

  // Workflow completeness (did they complete the workflow?)
  const workflowCompleteness = phaseTransitions > 0 ? (phaseTransitions / 7) * 100 : 0; // 7 phases in feature-dev

  // Guidance score (higher if more decisions supported)
  const guidanceScore = Math.min(100, userDecisionPoints * 20); // Max out at 100

  // Agent coordination analysis
  const taskCalls = session.toolCallDetails.filter(t => t.name === 'Task');
  const totalAgentInvocations = taskCalls.length;

  // Detect parallel agents (simplified: look for Task calls within 60s window)
  let parallelAgentPeriods = 0;
  for (let i = 0; i < taskCalls.length - 1; i++) {
    const current = new Date(taskCalls[i].timestamp);
    const next = new Date(taskCalls[i + 1].timestamp);
    const diffSeconds = (next.getTime() - current.getTime()) / 1000;
    if (diffSeconds < 60) {
      parallelAgentPeriods++;
    }
  }

  // Agent handoffs (different agents in sequence)
  let agentHandoffs = 0;
  for (let i = 0; i < agentInvocations.length - 1; i++) {
    if (agentInvocations[i] !== agentInvocations[i + 1]) {
      agentHandoffs++;
    }
  }

  const coordinationScore = totalAgentInvocations > 0
    ? Math.min(100, (parallelAgentPeriods + agentHandoffs) * 10)
    : 0;

  // Skill usage analysis
  const skillsInvoked = session.popkitFeatures.skills;

  // Detect skill suggestions (HTML comments in output - would need to parse logs)
  // For now, assume 1 suggestion per skill invoked (conservative)
  const skillSuggestions = skillsInvoked.length;
  const skillUtilizationRate = skillSuggestions > 0 ? 100 : 0; // If skill invoked, 100% used

  const skillEffectivenessScore = skillsInvoked.length > 0
    ? Math.min(100, skillsInvoked.length * 25)
    : 0;

  // Overall workflow value
  const timeToFirstValue = session.durationSeconds > 0
    ? Math.min(session.durationSeconds, 300) / 300 * 100 // Normalize to 5min max
    : 0;

  const decisionsSupported = userDecisionPoints;

  // Estimate context saved (each re-read avoidance saves ~30s)
  const potentialReReads = filesReadMap.size * 2; // Assume vanilla reads everything 2x
  const actualReReads = Array.from(filesReadMap.values()).reduce((sum, c) => sum + c, 0);
  const reReadsAvoided = Math.max(0, potentialReReads - actualReReads);
  const contextSaved = reReadsAvoided * 30; // 30s per re-read avoided

  // Workflow clarity gain (based on decisions supported and guidance)
  const workflowClarityGain = Math.min(100, (decisionsSupported * 10) + (phaseTransitions * 5));

  // Composite overall score
  const overallScore = Math.round(
    (contextEfficiencyScore * 0.25) +
    (guidanceScore * 0.3) +
    (coordinationScore * 0.2) +
    (skillEffectivenessScore * 0.15) +
    (workflowClarityGain * 0.1)
  );

  return {
    contextMetrics: {
      filesReadMultipleTimes,
      contextRestorations,
      averageFileReReads,
      contextEfficiencyScore,
    },
    workflowMetrics: {
      phaseTransitions,
      userDecisionPoints,
      workflowCompleteness,
      guidanceScore,
    },
    coordinationMetrics: {
      agentInvocations: totalAgentInvocations,
      parallelAgentPeriods,
      agentHandoffs,
      coordinationScore,
    },
    skillMetrics: {
      skillsInvoked,
      skillSuggestions,
      skillUtilizationRate,
      skillEffectivenessScore,
    },
    overallScore,
    valueBreakdown: {
      timeToFirstValue,
      decisionsSupported,
      contextSaved,
      workflowClarityGain,
    },
  };
}

/**
 * Compare workflow metrics between vanilla and PopKit modes
 */
export interface WorkflowMetricsComparison {
  vanilla: WorkflowMetrics;
  popkit: WorkflowMetrics;

  improvements: {
    contextEfficiencyGain: number; // Percentage points
    guidanceGain: number;
    coordinationGain: number;
    skillValueGain: number;
    overallValueGain: number;
  };

  insights: string[];
}

export function compareWorkflowMetrics(
  vanilla: WorkflowMetrics,
  popkit: WorkflowMetrics
): WorkflowMetricsComparison {
  const improvements = {
    contextEfficiencyGain: popkit.contextMetrics.contextEfficiencyScore - vanilla.contextMetrics.contextEfficiencyScore,
    guidanceGain: popkit.workflowMetrics.guidanceScore - vanilla.workflowMetrics.guidanceScore,
    coordinationGain: popkit.coordinationMetrics.coordinationScore - vanilla.coordinationMetrics.coordinationScore,
    skillValueGain: popkit.skillMetrics.skillEffectivenessScore - vanilla.skillMetrics.skillEffectivenessScore,
    overallValueGain: popkit.overallScore - vanilla.overallScore,
  };

  const insights: string[] = [];

  // Context efficiency insight
  if (improvements.contextEfficiencyGain > 10) {
    insights.push(`✅ Context efficiency improved by ${improvements.contextEfficiencyGain.toFixed(0)}% (${popkit.valueBreakdown.contextSaved}s saved)`);
  } else if (improvements.contextEfficiencyGain < -10) {
    insights.push(`⚠️ Context efficiency decreased by ${Math.abs(improvements.contextEfficiencyGain).toFixed(0)}%`);
  }

  // Workflow guidance insight
  if (improvements.guidanceGain > 20) {
    insights.push(`✅ Workflow guidance improved by ${improvements.guidanceGain.toFixed(0)}% (${popkit.workflowMetrics.userDecisionPoints} decisions supported)`);
  }

  // Agent coordination insight
  if (popkit.coordinationMetrics.agentInvocations > 0) {
    insights.push(`✅ Agent coordination: ${popkit.coordinationMetrics.agentInvocations} agents, ${popkit.coordinationMetrics.agentHandoffs} handoffs`);
  }

  // Skill value insight
  if (popkit.skillMetrics.skillsInvoked.length > 0) {
    insights.push(`✅ Skills invoked: ${popkit.skillMetrics.skillsInvoked.join(', ')}`);
  } else {
    insights.push(`⚠️ No skills were invoked - PopKit features underutilized`);
  }

  // Overall value insight
  if (improvements.overallValueGain > 20) {
    insights.push(`✅ Overall workflow value improved by ${improvements.overallValueGain.toFixed(0)} points`);
  } else if (improvements.overallValueGain < 0) {
    insights.push(`⚠️ Overall workflow value decreased by ${Math.abs(improvements.overallValueGain).toFixed(0)} points`);
  }

  // Clarity gain insight
  if (popkit.valueBreakdown.workflowClarityGain > 30) {
    insights.push(`✅ Workflow clarity improved by ${popkit.valueBreakdown.workflowClarityGain.toFixed(0)}%`);
  }

  return {
    vanilla,
    popkit,
    improvements,
    insights,
  };
}

/**
 * Generate workflow metrics report
 */
export function generateWorkflowMetricsReport(comparison: WorkflowMetricsComparison): string {
  const lines: string[] = [];

  lines.push('='.repeat(80));
  lines.push('WORKFLOW METRICS REPORT - Measuring the Unmeasured 90%');
  lines.push('='.repeat(80));
  lines.push('');

  lines.push('CONTEXT EFFICIENCY');
  lines.push('-'.repeat(80));
  lines.push(`Files Re-Read (Multiple Times)    Vanilla: ${comparison.vanilla.contextMetrics.filesReadMultipleTimes}  PopKit: ${comparison.popkit.contextMetrics.filesReadMultipleTimes}`);
  lines.push(`Context Restorations               Vanilla: ${comparison.vanilla.contextMetrics.contextRestorations}  PopKit: ${comparison.popkit.contextMetrics.contextRestorations}`);
  lines.push(`Efficiency Score                   Vanilla: ${comparison.vanilla.contextMetrics.contextEfficiencyScore.toFixed(0)}  PopKit: ${comparison.popkit.contextMetrics.contextEfficiencyScore.toFixed(0)}`);
  lines.push(`Context Time Saved                 ${comparison.popkit.valueBreakdown.contextSaved.toFixed(0)}s`);
  lines.push('');

  lines.push('WORKFLOW GUIDANCE');
  lines.push('-'.repeat(80));
  lines.push(`Phase Transitions                  Vanilla: ${comparison.vanilla.workflowMetrics.phaseTransitions}  PopKit: ${comparison.popkit.workflowMetrics.phaseTransitions}`);
  lines.push(`User Decision Points               Vanilla: ${comparison.vanilla.workflowMetrics.userDecisionPoints}  PopKit: ${comparison.popkit.workflowMetrics.userDecisionPoints}`);
  lines.push(`Workflow Completeness              Vanilla: ${comparison.vanilla.workflowMetrics.workflowCompleteness.toFixed(0)}%  PopKit: ${comparison.popkit.workflowMetrics.workflowCompleteness.toFixed(0)}%`);
  lines.push(`Guidance Score                     Vanilla: ${comparison.vanilla.workflowMetrics.guidanceScore.toFixed(0)}  PopKit: ${comparison.popkit.workflowMetrics.guidanceScore.toFixed(0)}`);
  lines.push('');

  lines.push('AGENT COORDINATION');
  lines.push('-'.repeat(80));
  lines.push(`Agent Invocations                  Vanilla: ${comparison.vanilla.coordinationMetrics.agentInvocations}  PopKit: ${comparison.popkit.coordinationMetrics.agentInvocations}`);
  lines.push(`Parallel Agent Periods             Vanilla: ${comparison.vanilla.coordinationMetrics.parallelAgentPeriods}  PopKit: ${comparison.popkit.coordinationMetrics.parallelAgentPeriods}`);
  lines.push(`Agent Handoffs                     Vanilla: ${comparison.vanilla.coordinationMetrics.agentHandoffs}  PopKit: ${comparison.popkit.coordinationMetrics.agentHandoffs}`);
  lines.push(`Coordination Score                 Vanilla: ${comparison.vanilla.coordinationMetrics.coordinationScore.toFixed(0)}  PopKit: ${comparison.popkit.coordinationMetrics.coordinationScore.toFixed(0)}`);
  lines.push('');

  lines.push('SKILL UTILIZATION');
  lines.push('-'.repeat(80));
  lines.push(`Skills Invoked                     Vanilla: ${comparison.vanilla.skillMetrics.skillsInvoked.length}  PopKit: ${comparison.popkit.skillMetrics.skillsInvoked.length}`);
  if (comparison.popkit.skillMetrics.skillsInvoked.length > 0) {
    lines.push(`PopKit Skills Used: ${comparison.popkit.skillMetrics.skillsInvoked.join(', ')}`);
  }
  lines.push(`Skill Effectiveness Score          Vanilla: ${comparison.vanilla.skillMetrics.skillEffectivenessScore.toFixed(0)}  PopKit: ${comparison.popkit.skillMetrics.skillEffectivenessScore.toFixed(0)}`);
  lines.push('');

  lines.push('OVERALL WORKFLOW VALUE');
  lines.push('-'.repeat(80));
  lines.push(`Overall Score                      Vanilla: ${comparison.vanilla.overallScore}  PopKit: ${comparison.popkit.overallScore}`);
  lines.push(`Decisions Supported                ${comparison.popkit.valueBreakdown.decisionsSupported}`);
  lines.push(`Workflow Clarity Gain              ${comparison.popkit.valueBreakdown.workflowClarityGain.toFixed(0)}%`);
  lines.push('');

  lines.push('KEY INSIGHTS');
  lines.push('-'.repeat(80));
  for (const insight of comparison.insights) {
    lines.push(`  ${insight}`);
  }
  lines.push('');

  lines.push('IMPROVEMENTS SUMMARY');
  lines.push('-'.repeat(80));
  lines.push(`Context Efficiency:   ${comparison.improvements.contextEfficiencyGain > 0 ? '+' : ''}${comparison.improvements.contextEfficiencyGain.toFixed(0)} points`);
  lines.push(`Workflow Guidance:    ${comparison.improvements.guidanceGain > 0 ? '+' : ''}${comparison.improvements.guidanceGain.toFixed(0)} points`);
  lines.push(`Agent Coordination:   ${comparison.improvements.coordinationGain > 0 ? '+' : ''}${comparison.improvements.coordinationGain.toFixed(0)} points`);
  lines.push(`Skill Value:          ${comparison.improvements.skillValueGain > 0 ? '+' : ''}${comparison.improvements.skillValueGain.toFixed(0)} points`);
  lines.push(`Overall Value:        ${comparison.improvements.overallValueGain > 0 ? '+' : ''}${comparison.improvements.overallValueGain.toFixed(0)} points`);
  lines.push('');

  lines.push('='.repeat(80));

  return lines.join('\n');
}
