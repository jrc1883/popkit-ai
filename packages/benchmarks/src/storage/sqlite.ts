/**
 * PopKit Benchmark Framework - SQLite Storage Adapter
 *
 * Local SQLite storage for benchmark results.
 */

import Database from 'better-sqlite3';
import type {
  StorageAdapter,
  ResultFilters,
} from './interface.js';
import type {
  BenchmarkResult,
  ComparisonReport,
  AggregateReport,
  ComparisonMetric,
  BenchmarkMode,
} from '../types.js';

/**
 * SQLite storage adapter for benchmark results
 */
export class SQLiteAdapter implements StorageAdapter {
  private db: Database.Database;

  constructor(dbPath: string = ':memory:') {
    this.db = new Database(dbPath);
    this.db.pragma('journal_mode = WAL');
  }

  async initialize(): Promise<void> {
    // Create results table
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS benchmark_results (
        run_id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL,
        tool TEXT NOT NULL,
        mode TEXT NOT NULL,
        started_at TEXT NOT NULL,
        completed_at TEXT NOT NULL,
        duration_seconds REAL NOT NULL,
        tokens_used INTEGER NOT NULL,
        input_tokens INTEGER NOT NULL,
        output_tokens INTEGER NOT NULL,
        tool_calls INTEGER NOT NULL,
        success INTEGER NOT NULL,
        tests_passed_ratio REAL NOT NULL,
        code_quality_score REAL NOT NULL,
        security_issues INTEGER NOT NULL,
        context_precision REAL NOT NULL,
        first_attempt_success INTEGER NOT NULL,
        iterations_needed INTEGER NOT NULL,
        errored INTEGER NOT NULL,
        error_message TEXT,
        error_stack TEXT,
        raw_data TEXT NOT NULL,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
      );

      CREATE INDEX IF NOT EXISTS idx_task_id ON benchmark_results(task_id);
      CREATE INDEX IF NOT EXISTS idx_tool ON benchmark_results(tool);
      CREATE INDEX IF NOT EXISTS idx_mode ON benchmark_results(mode);
      CREATE INDEX IF NOT EXISTS idx_success ON benchmark_results(success);
    `);
  }

  async close(): Promise<void> {
    this.db.close();
  }

  async saveResult(result: BenchmarkResult): Promise<void> {
    const stmt = this.db.prepare(`
      INSERT OR REPLACE INTO benchmark_results (
        run_id, task_id, tool, mode,
        started_at, completed_at, duration_seconds,
        tokens_used, input_tokens, output_tokens, tool_calls,
        success, tests_passed_ratio, code_quality_score, security_issues,
        context_precision, first_attempt_success, iterations_needed,
        errored, error_message, error_stack, raw_data
      ) VALUES (
        @runId, @taskId, @tool, @mode,
        @startedAt, @completedAt, @durationSeconds,
        @tokensUsed, @inputTokens, @outputTokens, @toolCalls,
        @success, @testsPassedRatio, @codeQualityScore, @securityIssues,
        @contextPrecision, @firstAttemptSuccess, @iterationsNeeded,
        @errored, @errorMessage, @errorStack, @rawData
      )
    `);

    stmt.run({
      runId: result.runId,
      taskId: result.taskId,
      tool: result.tool,
      mode: result.mode,
      startedAt: result.startedAt,
      completedAt: result.completedAt,
      durationSeconds: result.durationSeconds,
      tokensUsed: result.tokensUsed,
      inputTokens: result.inputTokens,
      outputTokens: result.outputTokens,
      toolCalls: result.toolCalls,
      success: result.success ? 1 : 0,
      testsPassedRatio: result.testsPassedRatio,
      codeQualityScore: result.codeQualityScore,
      securityIssues: result.securityIssues,
      contextPrecision: result.contextPrecision,
      firstAttemptSuccess: result.firstAttemptSuccess ? 1 : 0,
      iterationsNeeded: result.iterationsNeeded,
      errored: result.errored ? 1 : 0,
      errorMessage: result.errorMessage || null,
      errorStack: result.errorStack || null,
      rawData: JSON.stringify({
        conversation: result.conversation,
        outputFiles: result.outputFiles,
        testResults: result.testResults,
        qualityResults: result.qualityResults,
        logs: result.logs,
      }),
    });
  }

  async getResult(runId: string): Promise<BenchmarkResult | null> {
    const stmt = this.db.prepare('SELECT * FROM benchmark_results WHERE run_id = ?');
    const row = stmt.get(runId) as DatabaseRow | undefined;
    return row ? this.rowToResult(row) : null;
  }

  async getResultsByTask(taskId: string): Promise<BenchmarkResult[]> {
    const stmt = this.db.prepare('SELECT * FROM benchmark_results WHERE task_id = ? ORDER BY started_at DESC');
    const rows = stmt.all(taskId) as DatabaseRow[];
    return rows.map((row) => this.rowToResult(row));
  }

  async queryResults(filters: ResultFilters): Promise<BenchmarkResult[]> {
    const conditions: string[] = [];
    const params: Record<string, unknown> = {};

    if (filters.taskId) {
      conditions.push('task_id = @taskId');
      params.taskId = filters.taskId;
    }
    if (filters.tool) {
      conditions.push('tool = @tool');
      params.tool = filters.tool;
    }
    if (filters.mode) {
      conditions.push('mode = @mode');
      params.mode = filters.mode;
    }
    if (filters.success !== undefined) {
      conditions.push('success = @success');
      params.success = filters.success ? 1 : 0;
    }
    if (filters.minDate) {
      conditions.push('started_at >= @minDate');
      params.minDate = filters.minDate.toISOString();
    }
    if (filters.maxDate) {
      conditions.push('started_at <= @maxDate');
      params.maxDate = filters.maxDate.toISOString();
    }

    let sql = 'SELECT * FROM benchmark_results';
    if (conditions.length > 0) {
      sql += ' WHERE ' + conditions.join(' AND ');
    }
    sql += ' ORDER BY started_at DESC';

    if (filters.limit) {
      sql += ` LIMIT ${filters.limit}`;
    }
    if (filters.offset) {
      sql += ` OFFSET ${filters.offset}`;
    }

    const stmt = this.db.prepare(sql);
    const rows = stmt.all(params) as DatabaseRow[];
    return rows.map((row) => this.rowToResult(row));
  }

  async deleteResult(runId: string): Promise<boolean> {
    const stmt = this.db.prepare('DELETE FROM benchmark_results WHERE run_id = ?');
    const result = stmt.run(runId);
    return result.changes > 0;
  }

  async deleteResultsByTask(taskId: string): Promise<number> {
    const stmt = this.db.prepare('DELETE FROM benchmark_results WHERE task_id = ?');
    const result = stmt.run(taskId);
    return result.changes;
  }

  async getComparison(taskId: string): Promise<ComparisonReport | null> {
    const results = await this.getResultsByTask(taskId);
    if (results.length === 0) return null;

    // Group by mode
    const byMode: Record<string, BenchmarkResult[]> = {
      vanilla: [],
      popkit: [],
      power: [],
    };

    for (const result of results) {
      if (result.mode in byMode) {
        byMode[result.mode].push(result);
      }
    }

    // Calculate averages per mode
    const modeStats = Object.fromEntries(
      Object.entries(byMode).map(([mode, runs]) => [
        mode,
        runs.length > 0 ? this.calculateAverages(runs) : null,
      ])
    ) as Record<string, ModeStats | null>;

    // Build comparisons
    const modeComparisons: ComparisonReport['modeComparisons'] = {};

    if (modeStats.vanilla && modeStats.popkit) {
      modeComparisons.vanillaVsPopkit = this.compareStats(
        modeStats.vanilla,
        modeStats.popkit
      );
    }
    if (modeStats.vanilla && modeStats.power) {
      modeComparisons.vanillaVsPower = this.compareStats(
        modeStats.vanilla,
        modeStats.power
      );
    }
    if (modeStats.popkit && modeStats.power) {
      modeComparisons.popkitVsPower = this.compareStats(
        modeStats.popkit,
        modeStats.power
      );
    }

    // Determine best mode
    let bestMode: BenchmarkMode = 'vanilla';
    let bestScore = -Infinity;
    for (const [mode, stats] of Object.entries(modeStats)) {
      if (stats) {
        // Score = success rate - normalized token usage
        const score = stats.successRate * 100 - stats.avgTokens / 1000;
        if (score > bestScore) {
          bestScore = score;
          bestMode = mode as BenchmarkMode;
        }
      }
    }

    // Calculate savings
    const vanillaStats = modeStats.vanilla;
    const popkitStats = modeStats.popkit;
    const powerStats = modeStats.power;
    const bestStats = modeStats[bestMode];

    return {
      taskId,
      generatedAt: new Date().toISOString(),
      runIds: results.map((r) => r.runId),
      modeComparisons,
      summary: {
        bestMode,
        tokenSavingsPercent: vanillaStats && bestStats
          ? ((vanillaStats.avgTokens - bestStats.avgTokens) / vanillaStats.avgTokens) * 100
          : 0,
        successRateImprovement: vanillaStats && bestStats
          ? (bestStats.successRate - vanillaStats.successRate) * 100
          : 0,
        qualityImprovement: vanillaStats && bestStats
          ? bestStats.avgQuality - vanillaStats.avgQuality
          : 0,
      },
    };
  }

  async getAggregateReport(): Promise<AggregateReport> {
    const tasks = await this.listTasks();
    const taskReports: AggregateReport['tasks'] = [];
    let totalTokenReduction = 0;
    let totalSuccessImprovement = 0;
    let totalQualityImprovement = 0;
    let totalTimeSavings = 0;
    let validTasks = 0;

    for (const taskId of tasks) {
      const comparison = await this.getComparison(taskId);
      if (comparison) {
        const results = await this.getResultsByTask(taskId);
        const taskName = results[0]?.taskId || taskId;

        taskReports.push({
          taskId,
          taskName,
          comparison,
        });

        totalTokenReduction += comparison.summary.tokenSavingsPercent;
        totalSuccessImprovement += comparison.summary.successRateImprovement;
        totalQualityImprovement += comparison.summary.qualityImprovement;
        validTasks++;
      }
    }

    const runCount = await this.getResultCount();

    return {
      title: 'PopKit Benchmark Aggregate Report',
      generatedAt: new Date().toISOString(),
      taskCount: tasks.length,
      runCount,
      averages: {
        tokenReduction: validTasks > 0 ? totalTokenReduction / validTasks : 0,
        successRateImprovement: validTasks > 0 ? totalSuccessImprovement / validTasks : 0,
        qualityImprovement: validTasks > 0 ? totalQualityImprovement / validTasks : 0,
        timeSavings: validTasks > 0 ? totalTimeSavings / validTasks : 0,
      },
      tasks: taskReports,
      confidence: {
        sufficientSamples: runCount >= 30,
        pValue: undefined, // Would need statistical library
        confidenceInterval: undefined,
      },
    };
  }

  async listTasks(): Promise<string[]> {
    const stmt = this.db.prepare('SELECT DISTINCT task_id FROM benchmark_results ORDER BY task_id');
    const rows = stmt.all() as { task_id: string }[];
    return rows.map((row) => row.task_id);
  }

  async getResultCount(filters?: ResultFilters): Promise<number> {
    if (!filters || Object.keys(filters).length === 0) {
      const stmt = this.db.prepare('SELECT COUNT(*) as count FROM benchmark_results');
      const row = stmt.get() as { count: number };
      return row.count;
    }

    const conditions: string[] = [];
    const params: Record<string, unknown> = {};

    if (filters.taskId) {
      conditions.push('task_id = @taskId');
      params.taskId = filters.taskId;
    }
    if (filters.tool) {
      conditions.push('tool = @tool');
      params.tool = filters.tool;
    }
    if (filters.mode) {
      conditions.push('mode = @mode');
      params.mode = filters.mode;
    }

    let sql = 'SELECT COUNT(*) as count FROM benchmark_results';
    if (conditions.length > 0) {
      sql += ' WHERE ' + conditions.join(' AND ');
    }

    const stmt = this.db.prepare(sql);
    const row = stmt.get(params) as { count: number };
    return row.count;
  }

  // Helper methods

  private rowToResult(row: DatabaseRow): BenchmarkResult {
    const rawData = JSON.parse(row.raw_data as string);
    return {
      runId: row.run_id,
      taskId: row.task_id,
      tool: row.tool as BenchmarkResult['tool'],
      mode: row.mode as BenchmarkResult['mode'],
      startedAt: row.started_at,
      completedAt: row.completed_at,
      durationSeconds: row.duration_seconds,
      tokensUsed: row.tokens_used,
      inputTokens: row.input_tokens,
      outputTokens: row.output_tokens,
      toolCalls: row.tool_calls,
      success: row.success === 1,
      testsPassedRatio: row.tests_passed_ratio,
      codeQualityScore: row.code_quality_score,
      securityIssues: row.security_issues,
      contextPrecision: row.context_precision,
      firstAttemptSuccess: row.first_attempt_success === 1,
      iterationsNeeded: row.iterations_needed,
      conversation: rawData.conversation || [],
      outputFiles: rawData.outputFiles || {},
      testResults: rawData.testResults || [],
      qualityResults: rawData.qualityResults || [],
      logs: rawData.logs || [],
      errored: row.errored === 1,
      errorMessage: row.error_message || undefined,
      errorStack: row.error_stack || undefined,
    };
  }

  private calculateAverages(results: BenchmarkResult[]): ModeStats {
    const n = results.length;
    return {
      count: n,
      avgTokens: results.reduce((sum, r) => sum + r.tokensUsed, 0) / n,
      avgToolCalls: results.reduce((sum, r) => sum + r.toolCalls, 0) / n,
      successRate: results.filter((r) => r.success).length / n,
      avgQuality: results.reduce((sum, r) => sum + r.codeQualityScore, 0) / n,
      avgTime: results.reduce((sum, r) => sum + r.durationSeconds, 0) / n,
    };
  }

  private compareStats(
    baseline: ModeStats,
    compared: ModeStats
  ): {
    tokens: ComparisonMetric;
    toolCalls: ComparisonMetric;
    successRate: ComparisonMetric;
    quality: ComparisonMetric;
    time: ComparisonMetric;
  } {
    return {
      tokens: this.createMetric(baseline.avgTokens, compared.avgTokens, true),
      toolCalls: this.createMetric(baseline.avgToolCalls, compared.avgToolCalls, true),
      successRate: this.createMetric(baseline.successRate, compared.successRate, false),
      quality: this.createMetric(baseline.avgQuality, compared.avgQuality, false),
      time: this.createMetric(baseline.avgTime, compared.avgTime, true),
    };
  }

  private createMetric(
    baseline: number,
    compared: number,
    lowerIsBetter: boolean
  ): ComparisonMetric {
    const difference = compared - baseline;
    const percentChange = baseline !== 0 ? (difference / baseline) * 100 : 0;
    const improved = lowerIsBetter ? compared < baseline : compared > baseline;

    return {
      baseline,
      compared,
      difference,
      percentChange,
      improved,
    };
  }
}

// Type for database row
interface DatabaseRow {
  run_id: string;
  task_id: string;
  tool: string;
  mode: string;
  started_at: string;
  completed_at: string;
  duration_seconds: number;
  tokens_used: number;
  input_tokens: number;
  output_tokens: number;
  tool_calls: number;
  success: number;
  tests_passed_ratio: number;
  code_quality_score: number;
  security_issues: number;
  context_precision: number;
  first_attempt_success: number;
  iterations_needed: number;
  errored: number;
  error_message: string | null;
  error_stack: string | null;
  raw_data: string;
}

// Type for mode statistics
interface ModeStats {
  count: number;
  avgTokens: number;
  avgToolCalls: number;
  successRate: number;
  avgQuality: number;
  avgTime: number;
}
