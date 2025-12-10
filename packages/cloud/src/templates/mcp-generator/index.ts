/**
 * MCP Generator Templates
 *
 * Server-side template engine for generating custom MCP servers.
 * Part of Issue #152 (Server-Side Premium Skill Execution)
 *
 * Templates are rendered server-side and returned to the user.
 * No AI inference required - pure template substitution.
 */

import { indexTemplate } from './templates/index-template';
import { healthTemplate } from './templates/health-template';
import { gitTemplate } from './templates/git-template';
import { qualityTemplate } from './templates/quality-template';
import { routinesTemplate } from './templates/routines-template';
import { searchTemplate } from './templates/search-template';
import { packageJsonTemplate } from './templates/package-json-template';
import { tsconfigTemplate } from './templates/tsconfig-template';
import { readmeTemplate } from './templates/readme-template';

// Framework detection patterns
const FRAMEWORK_PATTERNS: Record<string, { files: string[]; defaultPort: number }> = {
  nextjs: { files: ['next.config.js', 'next.config.ts', 'next.config.mjs'], defaultPort: 3000 },
  vite: { files: ['vite.config.ts', 'vite.config.js'], defaultPort: 5173 },
  express: { files: ['app.js', 'server.js', 'index.js'], defaultPort: 3000 },
  fastify: { files: ['fastify.config.js'], defaultPort: 3000 },
  nest: { files: ['nest-cli.json'], defaultPort: 3000 },
  remix: { files: ['remix.config.js'], defaultPort: 3000 },
  nuxt: { files: ['nuxt.config.ts', 'nuxt.config.js'], defaultPort: 3000 },
  sveltekit: { files: ['svelte.config.js'], defaultPort: 5173 },
};

// Database detection patterns
const DATABASE_PATTERNS: Record<string, { files: string[]; defaultPort: number }> = {
  postgresql: { files: ['prisma/schema.prisma'], defaultPort: 5432 },
  mysql: { files: ['prisma/schema.prisma'], defaultPort: 3306 },
  mongodb: { files: ['prisma/schema.prisma'], defaultPort: 27017 },
  supabase: { files: ['.env.local', '.env'], defaultPort: 54322 },
  redis: { files: ['docker-compose.yml', '.env'], defaultPort: 6379 },
};

export interface MCPGeneratorContext {
  projectName: string;
  techStack: string[];
  services: string[];
  devPort?: number;
  dbPort?: number;
  framework?: string;
  database?: string;
  includeEmbeddings?: boolean;
  includeRoutines?: boolean;
}

export interface GeneratedFile {
  path: string;
  content: string;
}

export interface MCPGeneratorResult {
  files: GeneratedFile[];
  instructions: string;
  tools: string[];
}

/**
 * Detect framework from tech stack
 */
function detectFramework(techStack: string[]): { name: string; port: number } | null {
  for (const tech of techStack) {
    const lower = tech.toLowerCase();
    for (const [framework, config] of Object.entries(FRAMEWORK_PATTERNS)) {
      if (lower.includes(framework)) {
        return { name: framework, port: config.defaultPort };
      }
    }
  }
  return null;
}

/**
 * Detect database from tech stack
 */
function detectDatabase(techStack: string[]): { name: string; port: number } | null {
  for (const tech of techStack) {
    const lower = tech.toLowerCase();
    for (const [db, config] of Object.entries(DATABASE_PATTERNS)) {
      if (lower.includes(db) || lower.includes('prisma') || lower.includes('supabase')) {
        return { name: db, port: config.defaultPort };
      }
    }
  }
  return null;
}

/**
 * Generate MCP server files from context
 */
export function generateMCPServer(context: MCPGeneratorContext): MCPGeneratorResult {
  const framework = context.framework
    ? { name: context.framework, port: context.devPort || 3000 }
    : detectFramework(context.techStack);

  const database = context.database
    ? { name: context.database, port: context.dbPort || 5432 }
    : detectDatabase(context.techStack);

  const devPort = context.devPort || framework?.port || 3000;
  const dbPort = context.dbPort || database?.port || 5432;

  const vars = {
    PROJECT_NAME: context.projectName,
    DEV_PORT: String(devPort),
    DB_PORT: String(dbPort),
    FRAMEWORK: framework?.name || 'generic',
    DATABASE: database?.name || 'none',
  };

  const files: GeneratedFile[] = [];
  const tools: string[] = [];

  // Always include core files
  files.push({
    path: 'package.json',
    content: renderTemplate(packageJsonTemplate, vars),
  });

  files.push({
    path: 'tsconfig.json',
    content: renderTemplate(tsconfigTemplate, vars),
  });

  files.push({
    path: 'src/index.ts',
    content: renderTemplate(indexTemplate, vars),
  });

  files.push({
    path: 'README.md',
    content: renderTemplate(readmeTemplate, vars),
  });

  // Always include git tools
  files.push({
    path: 'src/tools/git.ts',
    content: renderTemplate(gitTemplate, vars),
  });
  tools.push('git_status', 'git_diff', 'git_recent_commits');

  // Include health checks
  files.push({
    path: 'src/tools/health.ts',
    content: renderTemplate(healthTemplate, vars),
  });
  tools.push('check_dev_server', 'check_database');

  // Include quality tools
  files.push({
    path: 'src/tools/quality.ts',
    content: renderTemplate(qualityTemplate, vars),
  });
  tools.push('run_typecheck', 'run_lint', 'run_tests');

  // Include routines if requested (default: true)
  if (context.includeRoutines !== false) {
    files.push({
      path: 'src/tools/routines.ts',
      content: renderTemplate(routinesTemplate, vars),
    });
    tools.push('morning_routine', 'nightly_routine');
  }

  // Include search if embeddings requested (default: true)
  if (context.includeEmbeddings !== false) {
    files.push({
      path: 'src/search/search.ts',
      content: renderTemplate(searchTemplate, vars),
    });
    tools.push('tool_search');
  }

  const instructions = `
## Generated MCP Server: ${context.projectName}-dev

### Setup Instructions

1. Copy files to your project:
   \`\`\`
   mkdir -p .claude/mcp-servers/${context.projectName}-dev
   # Copy generated files here
   \`\`\`

2. Install dependencies:
   \`\`\`
   cd .claude/mcp-servers/${context.projectName}-dev
   npm install
   \`\`\`

3. Build the server:
   \`\`\`
   npm run build
   \`\`\`

4. Add to Claude settings (.claude/settings.json):
   \`\`\`json
   {
     "mcpServers": {
       "${context.projectName}-dev": {
         "command": "node",
         "args": [".claude/mcp-servers/${context.projectName}-dev/dist/index.js"]
       }
     }
   }
   \`\`\`

5. Restart Claude Code to load the MCP server.

### Tools Generated (${tools.length})

${tools.map((t) => `- \`${t}\``).join('\n')}
`.trim();

  return { files, instructions, tools };
}

/**
 * Render template with variable substitution
 */
function renderTemplate(template: string, vars: Record<string, string>): string {
  let result = template;
  for (const [key, value] of Object.entries(vars)) {
    result = result.replace(new RegExp(`\\{\\{${key}\\}\\}`, 'g'), value);
  }
  return result;
}
