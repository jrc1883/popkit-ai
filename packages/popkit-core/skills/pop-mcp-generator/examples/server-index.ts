// Example: MCP Server Entry Point

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
