/**
 * PopKit Universal MCP Server Configuration
 *
 * Part of Issue #112 (Universal MCP Server)
 */

export interface PopKitConfig {
  /** PopKit Cloud API base URL */
  apiUrl: string;
  /** API key for authentication */
  apiKey?: string;
  /** Client identifier for analytics */
  clientId: string;
  /** Client version */
  clientVersion: string;
}

export function loadConfig(): PopKitConfig {
  return {
    apiUrl: process.env.POPKIT_API_URL || 'https://api.popkit.dev',
    apiKey: process.env.POPKIT_API_KEY,
    clientId: detectClient(),
    clientVersion: process.env.POPKIT_CLIENT_VERSION || '1.0.0',
  };
}

/**
 * Detect which MCP client is running this server.
 */
function detectClient(): string {
  // Check environment hints
  if (process.env.CURSOR_SESSION) return 'cursor';
  if (process.env.CONTINUE_SESSION) return 'continue';
  if (process.env.CLAUDE_CODE_SESSION) return 'claude-code';
  if (process.env.WINDSURF_SESSION) return 'windsurf';

  // Check parent process name hints
  const parentName = process.env._ || '';
  if (parentName.includes('cursor')) return 'cursor';
  if (parentName.includes('continue')) return 'continue';
  if (parentName.includes('claude')) return 'claude-code';

  // Check explicit override
  if (process.env.POPKIT_CLIENT) {
    return process.env.POPKIT_CLIENT;
  }

  return 'mcp-generic';
}

/**
 * Get HTTP headers for PopKit Cloud API requests.
 */
export function getApiHeaders(config: PopKitConfig): Record<string, string> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    'X-PopKit-Client': config.clientId,
    'X-PopKit-Client-Version': config.clientVersion,
    'X-PopKit-Plugin-Version': '1.0.0-beta.1',
  };

  if (config.apiKey) {
    headers['Authorization'] = `Bearer ${config.apiKey}`;
  }

  return headers;
}
