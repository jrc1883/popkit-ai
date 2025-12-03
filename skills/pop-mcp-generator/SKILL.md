---
name: mcp-generator
description: "Use when setting up project-specific development tools or after analyzing a codebase - generates custom MCP server with semantic search, project-aware tools, and health monitoring capabilities. Do NOT use if generic popkit commands are sufficient or for small projects where MCP server overhead isn't justified - stick with built-in tools for simple workflows."
---

# MCP Server Generator

## Overview

Generate a custom MCP (Model Context Protocol) server tailored to the specific project's needs, including semantic search, project-specific tools, and contextual capabilities.

**Core principle:** Every project deserves tools that understand its unique architecture.

**Trigger:** `/generate-mcp` command after project analysis

## What Gets Generated

```
.claude/mcp-servers/[project-name]-dev/
├── package.json
├── tsconfig.json
├── src/
│   ├── index.ts              # MCP server entry point
│   ├── tools/
│   │   ├── project-tools.ts  # Project-specific tools
│   │   ├── health-check.ts   # Service health checks
│   │   └── search.ts         # Semantic search
│   └── resources/
│       └── project-context.ts # Project documentation
└── README.md
```

## Generation Process

### Step 1: Analyze Project

Gather project information:

```bash
# Detect tech stack
ls package.json Cargo.toml pyproject.toml go.mod 2>/dev/null

# Find main directories
ls -d src lib app components 2>/dev/null

# Detect test framework
grep -l "jest\|mocha\|vitest\|pytest" package.json pyproject.toml 2>/dev/null

# Find configuration files
ls .env* config/ *.config.* 2>/dev/null
```

### Step 2: Determine Tools to Generate

Based on project type, select tools:

**Node.js:**
- check_nextjs / check_vite / check_express
- run_typecheck
- run_lint
- run_tests
- npm_scripts

**Python:**
- run_pytest
- run_mypy
- check_virtualenv
- run_lint (ruff/black)

**Rust:**
- cargo_check
- cargo_test
- cargo_clippy

**Common:**
- git_status
- git_diff
- git_recent_commits
- morning_routine
- nightly_routine
- tool_search (semantic)

### Step 3: Generate package.json

```json
{
  "name": "[project]-dev-mcp",
  "version": "1.0.0",
  "description": "MCP server for [project] development",
  "type": "module",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "tsx src/index.ts"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "latest"
  },
  "devDependencies": {
    "typescript": "^5.0.0",
    "tsx": "^4.0.0"
  }
}
```

### Step 4: Generate Tool Implementations

For each tool, generate TypeScript implementation:

```typescript
// Example: health check tool
export const checkService = {
  name: "[project]__check_[service]",
  description: "Check if [service] is running on port [port]",
  inputSchema: {
    type: "object",
    properties: {},
    required: []
  },
  async execute() {
    const response = await fetch(`http://localhost:[port]/health`);
    return {
      running: response.ok,
      url: `http://localhost:[port]`,
      status: response.status
    };
  }
};
```

### Step 5: Generate Semantic Search

Create tool search with embeddings:

```typescript
// Tool search with semantic matching
export const toolSearch = {
  name: "[project]__tool_search",
  description: "Search for tools by description",
  inputSchema: {
    type: "object",
    properties: {
      query: { type: "string", description: "Natural language query" },
      top_k: { type: "number", default: 5 }
    },
    required: ["query"]
  },
  async execute({ query, top_k = 5 }) {
    // Match against tool descriptions
    const tools = getAllTools();
    return rankByRelevance(tools, query, top_k);
  }
};
```

### Step 6: Generate Index File

```typescript
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

// Import all tools
import { projectTools } from "./tools/project-tools.js";
import { healthChecks } from "./tools/health-check.js";
import { searchTools } from "./tools/search.js";

const server = new Server({
  name: "[project]-dev",
  version: "1.0.0"
}, {
  capabilities: {
    tools: {}
  }
});

// Register all tools
const allTools = [...projectTools, ...healthChecks, ...searchTools];

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: allTools.map(t => ({
    name: t.name,
    description: t.description,
    inputSchema: t.inputSchema
  }))
}));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const tool = allTools.find(t => t.name === request.params.name);
  if (!tool) throw new Error(`Unknown tool: ${request.params.name}`);
  return await tool.execute(request.params.arguments);
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

### Step 7: Register in Claude Settings

Add to `.claude/settings.json`:

```json
{
  "mcpServers": {
    "[project]-dev": {
      "command": "node",
      "args": [".claude/mcp-servers/[project]-dev/dist/index.js"]
    }
  }
}
```

## Post-Generation

After generating:

```
MCP server generated at .claude/mcp-servers/[project]-dev/

Tools created:
- [project]__check_[services]
- [project]__run_typecheck
- [project]__run_lint
- [project]__run_tests
- [project]__git_status
- [project]__tool_search

Next steps:
1. cd .claude/mcp-servers/[project]-dev
2. npm install
3. npm run build
4. Restart Claude Code to load MCP server

Would you like me to build and test it?
```

## Integration

**Requires:**
- Project analysis (via analyze-project skill)

**Enables:**
- Project-specific tools in Claude Code
- Semantic tool search
- Health monitoring
- Custom workflows
