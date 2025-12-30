#!/usr/bin/env node
/**
 * PopKit Universal MCP Server
 *
 * Part of Issue #112 (Universal MCP Server)
 *
 * A universal MCP server that works with any MCP-compatible AI tool:
 * - Cursor
 * - Continue.dev
 * - Claude Code
 * - Windsurf (when MCP is supported)
 * - Any other MCP client
 *
 * Provides access to PopKit's:
 * - Pattern search (collective learning)
 * - Workflow tracking (durable state)
 * - Memory recall (cross-project learnings)
 * - Agent coordination (Power Mode lite)
 * - Quality checks (code validation)
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema } from '@modelcontextprotocol/sdk/types.js';

import { loadConfig, type PopKitConfig } from './config.js';
import { patternTools } from './tools/patterns.js';
import { workflowTools } from './tools/workflows.js';
import { memoryTools } from './tools/memory.js';
import { agentTools } from './tools/agents.js';
import { qualityTools } from './tools/quality.js';

// Tool interface
interface Tool {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
  handler: (args: Record<string, unknown>, config: PopKitConfig) => Promise<unknown>;
}

class PopKitMCPServer {
  private server: Server;
  private config: PopKitConfig;
  private allTools: Tool[];

  constructor() {
    this.config = loadConfig();

    this.server = new Server(
      {
        name: 'popkit-universal',
        version: '1.0.0-beta.1',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    // Combine all tools
    this.allTools = [
      ...patternTools,
      ...workflowTools,
      ...memoryTools,
      ...agentTools,
      ...qualityTools,
    ];

    // Setup handlers
    this.setupToolHandlers();

    // Error handling
    this.server.onerror = (error) => console.error('[PopKit MCP Error]', error);
    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  private setupToolHandlers() {
    // List tools handler
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: this.allTools.map((tool) => ({
        name: tool.name,
        description: tool.description,
        inputSchema: tool.inputSchema,
      })),
    }));

    // Call tool handler
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      const tool = this.allTools.find((t) => t.name === name);
      if (!tool) {
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                error: true,
                message: `Tool not found: ${name}`,
                availableTools: this.allTools.map((t) => t.name),
              }, null, 2),
            },
          ],
          isError: true,
        };
      }

      try {
        const result = await tool.handler((args as Record<string, unknown>) || {}, this.config);

        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      } catch (error) {
        return {
          content: [
            {
              type: 'text',
              text: JSON.stringify({
                error: true,
                message: error instanceof Error ? error.message : String(error),
                tool: name,
              }, null, 2),
            },
          ],
          isError: true,
        };
      }
    });
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error(`PopKit Universal MCP Server running`);
    console.error(`  Client: ${this.config.clientId}`);
    console.error(`  API: ${this.config.apiUrl}`);
    console.error(`  Auth: ${this.config.apiKey ? 'configured' : 'anonymous'}`);
    console.error(`  Tools: ${this.allTools.length}`);
  }
}

// Main entry point
const server = new PopKitMCPServer();
server.run().catch(console.error);
