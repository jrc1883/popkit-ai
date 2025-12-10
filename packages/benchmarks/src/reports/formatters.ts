/**
 * PopKit Benchmark Framework - Report Formatters
 *
 * Utilities for formatting benchmark data into various output formats.
 */

import type {
  BenchmarkResult,
  ComparisonReport,
  AggregateReport,
  BenchmarkMode,
} from '../types.js';

/**
 * Format options for reports
 */
export interface FormatOptions {
  /** Include raw data in output */
  includeRawData?: boolean;
  /** Include timestamps */
  includeTimestamps?: boolean;
  /** Color output (for terminal) */
  color?: boolean;
  /** Compact output */
  compact?: boolean;
}

/**
 * Create a progress bar string
 */
export function progressBar(
  value: number,
  max: number,
  width: number = 20,
  filled: string = '█',
  empty: string = '░'
): string {
  const percentage = Math.min(value / max, 1);
  const filledCount = Math.round(percentage * width);
  const emptyCount = width - filledCount;
  return filled.repeat(filledCount) + empty.repeat(emptyCount);
}

/**
 * Format a number as a percentage
 */
export function formatPercent(value: number, decimals: number = 1): string {
  return `${(value * 100).toFixed(decimals)}%`;
}

/**
 * Format a number with K/M suffixes
 */
export function formatNumber(value: number): string {
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M`;
  }
  if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}K`;
  }
  return value.toFixed(0);
}

/**
 * Format duration in seconds to human readable
 */
export function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${seconds.toFixed(1)}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remaining = seconds % 60;
  return `${minutes}m ${remaining.toFixed(0)}s`;
}

/**
 * Calculate improvement percentage
 */
export function calculateImprovement(
  baseline: number,
  compared: number,
  lowerIsBetter: boolean = false
): { value: number; improved: boolean } {
  const diff = compared - baseline;
  const percentChange = baseline !== 0 ? (diff / baseline) * 100 : 0;
  const improved = lowerIsBetter ? compared < baseline : compared > baseline;
  return { value: Math.abs(percentChange), improved };
}

/**
 * Mode display names
 */
export const MODE_NAMES: Record<BenchmarkMode, string> = {
  vanilla: 'Vanilla',
  popkit: 'PopKit',
  power: 'Power Mode',
};

/**
 * Get color code for terminal output
 */
export function getColor(
  type: 'success' | 'error' | 'warning' | 'info' | 'dim'
): string {
  const colors = {
    success: '\x1b[32m',
    error: '\x1b[31m',
    warning: '\x1b[33m',
    info: '\x1b[36m',
    dim: '\x1b[90m',
  };
  return colors[type];
}

/**
 * Reset terminal color
 */
export const RESET_COLOR = '\x1b[0m';

/**
 * Format a single benchmark result as a summary line
 */
export function formatResultSummary(
  result: BenchmarkResult,
  options: FormatOptions = {}
): string {
  const status = result.success ? '✓' : '✗';
  const statusColor = options.color
    ? result.success
      ? getColor('success')
      : getColor('error')
    : '';
  const reset = options.color ? RESET_COLOR : '';

  return [
    `${statusColor}${status}${reset}`,
    result.taskId,
    `[${result.tool}/${result.mode}]`,
    `${formatNumber(result.tokensUsed)} tokens`,
    `${result.toolCalls} calls`,
    formatDuration(result.durationSeconds),
  ].join(' ');
}

/**
 * Create ASCII table from data
 */
export function createTable(
  headers: string[],
  rows: string[][],
  options: { minWidth?: number; align?: ('left' | 'right' | 'center')[] } = {}
): string {
  const { minWidth = 8 } = options;

  // Calculate column widths
  const widths = headers.map((h, i) => {
    const maxRowWidth = Math.max(...rows.map((r) => (r[i] || '').length));
    return Math.max(h.length, maxRowWidth, minWidth);
  });

  // Create separator
  const separator = '├' + widths.map((w) => '─'.repeat(w + 2)).join('┼') + '┤';
  const topBorder = '┌' + widths.map((w) => '─'.repeat(w + 2)).join('┬') + '┐';
  const bottomBorder = '└' + widths.map((w) => '─'.repeat(w + 2)).join('┴') + '┘';

  // Format row
  const formatRow = (cells: string[]) => {
    const formatted = cells.map((cell, i) => {
      const align = options.align?.[i] || 'left';
      const width = widths[i];
      if (align === 'right') {
        return cell.padStart(width);
      } else if (align === 'center') {
        const padding = width - cell.length;
        const left = Math.floor(padding / 2);
        return ' '.repeat(left) + cell + ' '.repeat(padding - left);
      }
      return cell.padEnd(width);
    });
    return '│ ' + formatted.join(' │ ') + ' │';
  };

  const lines = [
    topBorder,
    formatRow(headers),
    separator,
    ...rows.map(formatRow),
    bottomBorder,
  ];

  return lines.join('\n');
}

/**
 * Create a comparison box for terminal display
 */
export function createComparisonBox(
  title: string,
  comparisons: { label: string; value: number; max: number; unit?: string }[],
  width: number = 60
): string {
  const lines: string[] = [];

  // Top border with title
  const titlePadding = Math.floor((width - title.length - 2) / 2);
  lines.push('┌' + '─'.repeat(titlePadding) + ' ' + title + ' ' + '─'.repeat(width - titlePadding - title.length - 2) + '┐');

  // Content
  const barWidth = 30;
  const maxValue = Math.max(...comparisons.map((c) => c.max));

  for (const comp of comparisons) {
    const bar = progressBar(comp.value, maxValue, barWidth);
    const valueStr = comp.unit ? `${comp.value}${comp.unit}` : comp.value.toString();
    const line = ` ${comp.label.padEnd(12)} ${bar} ${valueStr}`;
    lines.push('│' + line.padEnd(width - 2) + '│');
  }

  // Bottom border
  lines.push('└' + '─'.repeat(width - 2) + '┘');

  return lines.join('\n');
}
