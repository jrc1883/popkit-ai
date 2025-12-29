# @popkit/benchmarks

Benchmark framework for measuring PopKit's value proposition by comparing Claude Code performance across configurations.

## Overview

This package provides tools to run reproducible benchmarks comparing:
- **Vanilla**: Claude Code without PopKit installed
- **PopKit**: Claude Code with PopKit plugin (free tier)
- **Power**: Claude Code with PopKit plugin + pro credentials (Power Mode)

## Quick Start

```bash
# Check status
npx tsx run-benchmark.ts --status

# List available tasks
npx tsx run-benchmark.ts --list

# Run a benchmark
npx tsx run-benchmark.ts bouncing-balls vanilla
npx tsx run-benchmark.ts bouncing-balls popkit
npx tsx run-benchmark.ts bouncing-balls power
```

## Current Status

| Component | Status | Notes |
|-----------|--------|-------|
| Task Definitions | 5 tasks | bouncing-balls, todo-app, api-client, binary-search-tree, bug-fix |
| Claude Runner | Working | Windows + Unix support, config switching |
| ConfigSwitcher | Working | Enables/disables PopKit for A/B testing |
| SQLite Storage | Implemented | Not yet integrated with runner |
| Report Generation | Implemented | Markdown + HTML formatters |
| E2B Integration | Scaffolded | API available, not fully integrated |

## Architecture

```
packages/benchmarks/
├── run-benchmark.ts      # CLI entry point
├── src/
│   ├── types.ts          # Type definitions
│   ├── schemas.ts        # Zod validation schemas
│   ├── loader.ts         # Task loading utilities
│   ├── collector.ts      # Metrics collection
│   ├── runners/
│   │   ├── interface.ts      # Runner interface
│   │   ├── claude-runner.ts  # Claude Code CLI runner
│   │   ├── config-switcher.ts # PopKit enable/disable
│   │   └── executor.ts       # Orchestrates comparisons
│   ├── storage/
│   │   ├── interface.ts  # Storage interface
│   │   └── sqlite.ts     # SQLite adapter
│   ├── reports/
│   │   ├── formatters.ts # Display utilities
│   │   ├── markdown.ts   # Markdown reports
│   │   └── html.ts       # HTML reports
│   └── e2b/
│       ├── index.ts      # E2B utilities
│       └── poc.ts        # Proof of concept
├── tasks/                # Benchmark task definitions (JSON)
│   ├── bouncing-balls.json
│   ├── todo-app.json
│   ├── api-client.json
│   ├── binary-search-tree.json
│   └── bug-fix.json
└── results/              # Benchmark output
    ├── sessions/         # Raw session data
    └── comparisons/      # Comparison reports
```

## Task Definition Format

Tasks are defined in JSON with the following structure:

```json
{
  "id": "bouncing-balls",
  "name": "Bouncing Balls Canvas Animation",
  "description": "Create an HTML canvas with physics-based bouncing balls.",
  "category": "standard",
  "language": "javascript",
  "version": "1.0.0",

  "initialFiles": {
    "index.html": "<!DOCTYPE html>...",
    "balls.js": "// TODO: Implement bouncing balls animation"
  },
  "dependencies": [],
  "setupCommands": [],

  "prompt": "Create a web page with a canvas showing 5 balls bouncing...",
  "context": "This is a vanilla JavaScript task.",
  "maxTokens": 50000,
  "timeoutSeconds": 300,

  "tests": [
    {
      "id": "file-exists",
      "name": "balls.js file exists and has content",
      "type": "unit",
      "command": "node -e \"const fs=require('fs'); ...\"",
      "successPattern": "PASS"
    }
  ],

  "baseline": {
    "vanilla": { "tokenEstimate": 15000, "successRate": 0.6 },
    "popkit": { "tokenEstimate": 10000, "successRate": 0.85 },
    "power": { "tokenEstimate": 8000, "successRate": 0.95 }
  }
}
```

## How ConfigSwitcher Works

The `ConfigSwitcher` enables true A/B testing by modifying Claude Code's configuration:

```typescript
// Switches between modes by:
// 1. vanilla: Renames ~/.popkit-claude/ to ~/.popkit-claude/.disabled
// 2. popkit: Restores plugin, removes pro credentials
// 3. power: Restores plugin + pro credentials

const switcher = new ConfigSwitcher();
await switcher.saveSnapshot();           // Save current state
await switcher.switchMode('vanilla');    // Disable PopKit
// ... run benchmark ...
await switcher.restore();                // Restore original state
```

## Known Limitations

### Metrics Collection
- **Tool calls**: Currently shows 0 - needs to parse Claude's output for actual tool usage
- **Token count**: Only captures visible output tokens, not full API usage
- **Process stream**: Not yet capturing real-time tool call events

### PopKit Mode Testing
- **Workflow testing**: Simply enabling PopKit doesn't test `/popkit:dev`, `/popkit:project init`, etc.
- **Interactive prompts**: `AskUserQuestion` prompts need automated answers for benchmarking
- **Design decision**: Need to decide between "PopKit-lite" (hooks/agents) vs full workflow testing

### Platform Compatibility
- Windows: Uses stdin piping for prompts (avoids quote escaping issues)
- Unix: Uses command substitution `"$(cat promptfile)"`
- Tests: Use cross-platform Node.js one-liners instead of Unix utilities

## Results

Benchmark outputs are saved to `results/<task>-<mode>-<timestamp>/`:
- Generated source files (e.g., `balls.js`, `index.html`)
- Can be opened in browser to verify visual output

## Running Comparisons

Use the `BenchmarkExecutor` for automated comparisons:

```typescript
import { createExecutor } from './src/runners/executor.js';

const executor = createExecutor({
  modes: ['vanilla', 'popkit', 'power'],
  iterations: 5,
  storage: sqliteAdapter,
});

const report = await executor.runComparison('bouncing-balls');
```

## Related Documentation

- [Benchmarking Strategy](../docs/research/BENCHMARKING_STRATEGY.md) - Vision and roadmap
- [E2B Integration](./src/e2b/README.md) - Cloud sandbox execution

## Development

```bash
# Build
pnpm build

# Type check
pnpm typecheck

# Run tests
pnpm test
```

## Next Steps

1. **Fix metrics collection**: Capture actual tool calls and token usage from Claude's JSON output
2. **Process stream capture**: Add real-time event logging during benchmark execution
3. **PopKit workflow testing**: Design approach for testing full PopKit workflows
4. **E2B integration**: Run benchmarks in isolated cloud sandboxes
5. **Comparison reports**: Generate markdown/HTML reports comparing modes
