/**
 * Routine Generator Templates
 *
 * Server-side template engine for generating custom morning/nightly routines.
 * Part of Issue #152 (Server-Side Premium Skill Execution)
 *
 * Templates are rendered server-side and returned to the user.
 * No AI inference required - pure template substitution.
 */

import { morningCommandTemplate, morningMcpTemplate } from './templates/morning-template';
import { nightlyCommandTemplate, nightlyMcpTemplate } from './templates/nightly-template';

// Framework detection patterns
const FRAMEWORK_PATTERNS: Record<string, { port: number; buildDir: string; cacheDir: string }> = {
  nextjs: { port: 3000, buildDir: '.next', cacheDir: 'node_modules/.cache' },
  vite: { port: 5173, buildDir: 'dist', cacheDir: 'node_modules/.cache' },
  cra: { port: 3000, buildDir: 'build', cacheDir: 'node_modules/.cache' },
  express: { port: 3000, buildDir: 'dist', cacheDir: 'node_modules/.cache' },
  fastify: { port: 3000, buildDir: 'dist', cacheDir: 'node_modules/.cache' },
  nest: { port: 3000, buildDir: 'dist', cacheDir: 'node_modules/.cache' },
  remix: { port: 3000, buildDir: 'build', cacheDir: 'node_modules/.cache' },
  nuxt: { port: 3000, buildDir: '.nuxt', cacheDir: 'node_modules/.cache' },
  sveltekit: { port: 5173, buildDir: '.svelte-kit', cacheDir: 'node_modules/.cache' },
};

// Database detection patterns
const DATABASE_PATTERNS: Record<string, { port: number; checkCommand: string }> = {
  postgresql: { port: 5432, checkCommand: 'pg_isready -h localhost' },
  mysql: { port: 3306, checkCommand: 'mysqladmin ping' },
  mongodb: { port: 27017, checkCommand: 'mongosh --eval "db.adminCommand(\'ping\')"' },
  supabase: { port: 54321, checkCommand: 'curl -s localhost:54321/health' },
  redis: { port: 6379, checkCommand: 'redis-cli ping' },
};

// Language-specific cleanup patterns
const LANGUAGE_CLEANUP: Record<string, { dirs: string[]; files: string[] }> = {
  typescript: { dirs: ['dist', 'coverage'], files: ['.tsbuildinfo', '.eslintcache'] },
  javascript: { dirs: ['node_modules/.cache', 'coverage'], files: ['.eslintcache'] },
  python: { dirs: ['__pycache__', '.pytest_cache', '.mypy_cache', 'dist', 'build'], files: ['*.pyc'] },
  rust: { dirs: ['target/debug'], files: [] },
  go: { dirs: [], files: [] },
};

export interface RoutineGeneratorContext {
  projectName: string;
  projectPrefix: string;
  techStack: string[];
  services: string[];
  devPort?: number;
  dbPort?: number;
  framework?: string;
  database?: string;
  language?: string;
  hasMcp?: boolean;
  mcpServerName?: string;
}

export interface GeneratedFile {
  path: string;
  content: string;
}

export interface RoutineGeneratorResult {
  files: GeneratedFile[];
  instructions: string;
  detectedStack: {
    framework: string | null;
    database: string | null;
    language: string | null;
    services: string[];
  };
  checksIncluded: string[];
  cleanupTargets?: string[];
}

/**
 * Detect framework from tech stack
 */
function detectFramework(techStack: string[]): { name: string; config: typeof FRAMEWORK_PATTERNS[string] } | null {
  for (const tech of techStack) {
    const lower = tech.toLowerCase();
    for (const [framework, config] of Object.entries(FRAMEWORK_PATTERNS)) {
      if (lower.includes(framework) || lower.includes(framework.replace('js', ''))) {
        return { name: framework, config };
      }
    }
  }
  return null;
}

/**
 * Detect database from tech stack
 */
function detectDatabase(techStack: string[]): { name: string; config: typeof DATABASE_PATTERNS[string] } | null {
  for (const tech of techStack) {
    const lower = tech.toLowerCase();
    for (const [db, config] of Object.entries(DATABASE_PATTERNS)) {
      if (lower.includes(db) || lower.includes(db.replace('sql', ''))) {
        return { name: db, config };
      }
    }
  }
  return null;
}

/**
 * Detect primary language from tech stack
 */
function detectLanguage(techStack: string[]): string {
  const languageMap: Record<string, string[]> = {
    typescript: ['typescript', 'ts', 'nextjs', 'nest', 'angular'],
    javascript: ['javascript', 'js', 'react', 'vue', 'express', 'node'],
    python: ['python', 'py', 'django', 'fastapi', 'flask'],
    rust: ['rust', 'rs', 'cargo'],
    go: ['go', 'golang'],
  };

  for (const tech of techStack) {
    const lower = tech.toLowerCase();
    for (const [lang, patterns] of Object.entries(languageMap)) {
      if (patterns.some(p => lower.includes(p))) {
        return lang;
      }
    }
  }
  return 'javascript'; // default
}

/**
 * Generate morning routine command
 */
export function generateMorningRoutine(context: RoutineGeneratorContext): RoutineGeneratorResult {
  const framework = context.framework
    ? { name: context.framework, config: FRAMEWORK_PATTERNS[context.framework] || FRAMEWORK_PATTERNS.express }
    : detectFramework(context.techStack);

  const database = context.database
    ? { name: context.database, config: DATABASE_PATTERNS[context.database] || DATABASE_PATTERNS.postgresql }
    : detectDatabase(context.techStack);

  const language = context.language || detectLanguage(context.techStack);
  const devPort = context.devPort || framework?.config.port || 3000;
  const dbPort = context.dbPort || database?.config.port || 5432;

  const vars = {
    PROJECT_NAME: context.projectName,
    PROJECT_PREFIX: context.projectPrefix,
    DEV_PORT: String(devPort),
    DB_PORT: String(dbPort),
    FRAMEWORK: framework?.name || 'generic',
    DATABASE: database?.name || 'none',
    DB_CHECK_COMMAND: database?.config.checkCommand || 'echo "No database configured"',
    LANGUAGE: language,
  };

  const files: GeneratedFile[] = [];
  const checksIncluded: string[] = [];

  // Generate appropriate template based on MCP presence
  if (context.hasMcp && context.mcpServerName) {
    const mcpVars = { ...vars, MCP_SERVER_NAME: context.mcpServerName };
    files.push({
      path: `.claude/commands/${context.projectPrefix}:morning.md`,
      content: renderTemplate(morningMcpTemplate, mcpVars),
    });
    checksIncluded.push('MCP morning_routine', 'MCP check_database', 'MCP check_api');
  } else {
    files.push({
      path: `.claude/commands/${context.projectPrefix}:morning.md`,
      content: renderTemplate(morningCommandTemplate, vars),
    });

    // Add checks based on detected stack
    checksIncluded.push('Git status');
    if (framework) checksIncluded.push(`${framework.name} dev server (port ${devPort})`);
    if (database) checksIncluded.push(`${database.name} connection (port ${dbPort})`);
    if (language === 'typescript') checksIncluded.push('TypeScript validation');
    checksIncluded.push('Test suite');
  }

  const instructions = `
## Generated Morning Routine: ${context.projectPrefix}:morning

### Setup Instructions

1. The command file has been generated at:
   \`.claude/commands/${context.projectPrefix}:morning.md\`

2. Restart Claude Code to load the new command.

3. Run your new morning routine:
   \`\`\`
   /${context.projectPrefix}:morning
   /${context.projectPrefix}:morning quick
   \`\`\`

### Detected Stack
- **Framework:** ${framework?.name || 'Not detected'}
- **Database:** ${database?.name || 'Not detected'}
- **Language:** ${language}

### Health Checks Included (${checksIncluded.length})
${checksIncluded.map(c => `- ${c}`).join('\n')}
`.trim();

  return {
    files,
    instructions,
    detectedStack: {
      framework: framework?.name || null,
      database: database?.name || null,
      language,
      services: context.services,
    },
    checksIncluded,
  };
}

/**
 * Generate nightly routine command
 */
export function generateNightlyRoutine(context: RoutineGeneratorContext): RoutineGeneratorResult {
  const framework = context.framework
    ? { name: context.framework, config: FRAMEWORK_PATTERNS[context.framework] || FRAMEWORK_PATTERNS.express }
    : detectFramework(context.techStack);

  const database = context.database
    ? { name: context.database, config: DATABASE_PATTERNS[context.database] || DATABASE_PATTERNS.postgresql }
    : detectDatabase(context.techStack);

  const language = context.language || detectLanguage(context.techStack);
  const cleanup = LANGUAGE_CLEANUP[language] || LANGUAGE_CLEANUP.javascript;

  const cleanupDirs = [...cleanup.dirs];
  const cleanupFiles = [...cleanup.files];

  // Add framework-specific cleanup
  if (framework) {
    cleanupDirs.push(framework.config.buildDir);
    cleanupDirs.push(framework.config.cacheDir);
  }

  const vars = {
    PROJECT_NAME: context.projectName,
    PROJECT_PREFIX: context.projectPrefix,
    FRAMEWORK: framework?.name || 'generic',
    DATABASE: database?.name || 'none',
    LANGUAGE: language,
    CLEANUP_DIRS: cleanupDirs.join(', '),
    CLEANUP_FILES: cleanupFiles.join(', '),
    BUILD_DIR: framework?.config.buildDir || 'dist',
    CACHE_DIR: framework?.config.cacheDir || 'node_modules/.cache',
  };

  const files: GeneratedFile[] = [];
  const cleanupTargets: string[] = [];

  // Generate appropriate template based on MCP presence
  if (context.hasMcp && context.mcpServerName) {
    const mcpVars = { ...vars, MCP_SERVER_NAME: context.mcpServerName };
    files.push({
      path: `.claude/commands/${context.projectPrefix}:nightly.md`,
      content: renderTemplate(nightlyMcpTemplate, mcpVars),
    });
    cleanupTargets.push('MCP nightly_routine', 'MCP cleanup_caches');
  } else {
    files.push({
      path: `.claude/commands/${context.projectPrefix}:nightly.md`,
      content: renderTemplate(nightlyCommandTemplate, vars),
    });

    // Add cleanup targets based on detected stack
    cleanupDirs.forEach(dir => cleanupTargets.push(`${dir}/`));
    cleanupFiles.forEach(file => cleanupTargets.push(file));
    cleanupTargets.push('Old log files (7+ days)');
  }

  const instructions = `
## Generated Nightly Routine: ${context.projectPrefix}:nightly

### Setup Instructions

1. The command file has been generated at:
   \`.claude/commands/${context.projectPrefix}:nightly.md\`

2. Restart Claude Code to load the new command.

3. Run your new nightly routine:
   \`\`\`
   /${context.projectPrefix}:nightly
   /${context.projectPrefix}:nightly quick
   \`\`\`

### Detected Stack
- **Framework:** ${framework?.name || 'Not detected'}
- **Database:** ${database?.name || 'Not detected'}
- **Language:** ${language}

### Cleanup Targets Configured (${cleanupTargets.length})
${cleanupTargets.map(c => `- ${c}`).join('\n')}

### Maintenance Tasks
- Git gc and prune
- npm/pip audit
- Branch cleanup
- Session state capture
`.trim();

  return {
    files,
    instructions,
    detectedStack: {
      framework: framework?.name || null,
      database: database?.name || null,
      language,
      services: context.services,
    },
    checksIncluded: ['Git maintenance', 'Security audit', 'Session capture'],
    cleanupTargets,
  };
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
