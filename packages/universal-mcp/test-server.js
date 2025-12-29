/**
 * Simple test script for PopKit MCP Server
 *
 * Run with: node test-server.js
 */

import { spawn } from 'child_process';
import { dirname, join } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

// Start the MCP server
const server = spawn('node', [join(__dirname, 'dist', 'index.js')], {
  stdio: ['pipe', 'pipe', 'pipe']
});

let responseBuffer = '';

server.stdout.on('data', (data) => {
  responseBuffer += data.toString();

  // Try to parse JSON-RPC response
  try {
    const lines = responseBuffer.split('\n');
    for (const line of lines) {
      if (line.trim()) {
        const parsed = JSON.parse(line);
        console.log('\n=== Response ===');
        console.log(JSON.stringify(parsed, null, 2));
      }
    }
    responseBuffer = '';
  } catch {
    // Keep buffering
  }
});

server.stderr.on('data', (data) => {
  console.log('[Server]', data.toString().trim());
});

// Wait for server to start
await new Promise(resolve => setTimeout(resolve, 1000));

// Test 1: List tools
console.log('\n=== Test 1: List Tools ===');
const listToolsRequest = JSON.stringify({
  jsonrpc: '2.0',
  id: 1,
  method: 'tools/list'
}) + '\n';
server.stdin.write(listToolsRequest);

// Wait for response
await new Promise(resolve => setTimeout(resolve, 2000));

// Test 2: Call health status
console.log('\n=== Test 2: Call health_status ===');
const healthRequest = JSON.stringify({
  jsonrpc: '2.0',
  id: 2,
  method: 'tools/call',
  params: {
    name: 'popkit_health_status',
    arguments: {}
  }
}) + '\n';
server.stdin.write(healthRequest);

// Wait for response
await new Promise(resolve => setTimeout(resolve, 3000));

// Cleanup
console.log('\n=== Done ===');
server.kill();
process.exit(0);
