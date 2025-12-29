/**
 * PopKit Benchmark Framework - Report Module
 *
 * Exports report generation utilities for Markdown and HTML formats.
 */

// Formatters
export {
  type FormatOptions,
  progressBar,
  formatPercent,
  formatNumber,
  formatDuration,
  calculateImprovement,
  MODE_NAMES,
  getColor,
  RESET_COLOR,
  formatResultSummary,
  createTable,
  createComparisonBox,
} from './formatters.js';

// Markdown reports
export {
  generateResultMarkdown,
  generateComparisonMarkdown,
  generateAggregateMarkdown,
} from './markdown.js';

// HTML reports
export {
  generateResultHtml,
  generateComparisonHtml,
  generateAggregateHtml,
} from './html.js';
