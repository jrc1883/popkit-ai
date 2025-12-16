# PopKit Documentation Website - Comprehensive Implementation Plan

**Version:** 1.0.0
**Date:** 2025-12-15
**Status:** Ready for Implementation
**Branch:** `claude/build-popkit-readme-UfKd9`

---

## Executive Summary

This plan designs a documentation website in `packages/docs/` that:
- Uses **Astro + Starlight** (docs framework) for consistency with landing page
- Consumes benchmark data from `packages/benchmarks/` to showcase PopKit's value
- Auto-generates API references from plugin content (`packages/plugin/`)
- Deploys independently to Cloudflare Pages (e.g., `docs.popkit.dev`)
- Works standalone: `git clone → npm install → npm run dev`

The design balances **simplicity for MVP** with **scalability for growth**, following a 5-phase implementation path.

---

## 1. Tech Stack Rationale

### Chosen: Astro + Starlight

**Why Astro:**
- Already used in `packages/landing/` - team familiarity
- Fast static site generation (perfect for docs)
- Component islands (can embed React/Vue for interactive benchmark charts)
- Excellent TypeScript support
- Built-in Markdown/MDX support with frontmatter

**Why Starlight:**
- Purpose-built docs framework on top of Astro
- Out-of-the-box features: search, navigation, dark mode, mobile responsive
- Auto-generates sidebar from file structure
- Excellent i18n support (future: multi-language docs)
- Active maintenance by Astro team
- Examples: Astro docs itself uses Starlight

**Alternatives Considered:**
- **Nextra (Next.js)**: Excellent, but adds React dependency; slower than Astro
- **Docusaurus**: React-heavy, opinionated, slower builds
- **VitePress**: Vue-based, great but different from existing stack
- **Custom Astro**: Starlight provides too much value to reinvent

### Visualization Stack for Benchmarks

- **Chart.js** or **Recharts**: Benchmark comparison charts
- **D3.js**: Custom visualizations (optional, future)
- **Mermaid**: Architecture diagrams (already supported by Starlight)

---

## 2. Directory Structure for `packages/docs/`

```
packages/docs/
├── package.json                    # Workspace package config
├── astro.config.mjs                # Astro + Starlight config
├── tsconfig.json                   # TypeScript config
├── wrangler.toml                   # Cloudflare Pages deploy config
├── .gitignore
├── README.md                       # Local dev instructions
│
├── public/                         # Static assets
│   ├── images/
│   │   ├── hero/                   # Hero images, screenshots
│   │   ├── benchmarks/             # Benchmark charts (if static)
│   │   └── architecture/           # Architecture diagrams
│   ├── videos/                     # Demo videos
│   └── downloads/                  # PDFs, examples
│
├── src/
│   ├── content/
│   │   ├── docs/                   # Main docs content
│   │   │   ├── index.mdx           # Docs home
│   │   │   ├── getting-started/
│   │   │   │   ├── installation.mdx
│   │   │   │   ├── quick-start.mdx
│   │   │   │   ├── first-command.mdx
│   │   │   │   └── configuration.mdx
│   │   │   ├── guides/
│   │   │   │   ├── issue-driven-dev.mdx
│   │   │   │   ├── feature-workflow.mdx
│   │   │   │   ├── daily-operations.mdx
│   │   │   │   ├── power-mode.mdx
│   │   │   │   └── debugging.mdx
│   │   │   ├── commands/
│   │   │   │   ├── index.mdx       # Commands overview
│   │   │   │   ├── issue.mdx       # Auto-generated
│   │   │   │   ├── git.mdx         # Auto-generated
│   │   │   │   └── ...             # One per command
│   │   │   ├── agents/
│   │   │   │   ├── index.mdx       # Agent system overview
│   │   │   │   ├── tier-1/
│   │   │   │   │   ├── code-reviewer.mdx
│   │   │   │   │   └── ...
│   │   │   │   └── tier-2/
│   │   │   │       └── ...
│   │   │   ├── skills/
│   │   │   │   ├── index.mdx       # Skills overview
│   │   │   │   ├── development/
│   │   │   │   ├── quality/
│   │   │   │   └── power-mode/
│   │   │   ├── hooks/
│   │   │   │   ├── index.mdx       # Hook system
│   │   │   │   ├── pre-tool-use.mdx
│   │   │   │   └── ...
│   │   │   ├── output-styles/
│   │   │   │   └── index.mdx       # Template reference
│   │   │   ├── benchmarks/
│   │   │   │   ├── index.mdx       # Benchmarks home
│   │   │   │   ├── overview.mdx    # Methodology
│   │   │   │   ├── bouncing-balls.mdx
│   │   │   │   ├── todo-app.mdx
│   │   │   │   ├── comparisons.mdx # Vanilla vs PopKit vs Power
│   │   │   │   └── historical.mdx  # Trends over time
│   │   │   ├── architecture/
│   │   │   │   ├── overview.mdx    # High-level architecture
│   │   │   │   ├── monorepo.mdx    # Monorepo structure
│   │   │   │   ├── tiered-agents.mdx
│   │   │   │   ├── power-mode.mdx  # Technical deep dive
│   │   │   │   ├── cloud-api.mdx   # PopKit Cloud
│   │   │   │   └── plugin-lifecycle.mdx
│   │   │   ├── contributing/
│   │   │   │   ├── index.mdx       # Contribution guide
│   │   │   │   ├── setup.mdx       # Dev environment
│   │   │   │   ├── testing.mdx     # Testing strategy
│   │   │   │   ├── adding-agents.mdx
│   │   │   │   ├── adding-skills.mdx
│   │   │   │   └── adding-commands.mdx
│   │   │   └── case-studies/
│   │   │       ├── index.mdx       # Case studies home
│   │   │       ├── 3x-faster-tokens.mdx
│   │   │       └── ...             # Generated from benchmarks
│   │   └── config.ts               # Content collection schema
│   │
│   ├── components/
│   │   ├── BenchmarkChart.astro    # Chart component
│   │   ├── BenchmarkComparison.astro
│   │   ├── CommandReference.astro  # Auto-generated command tables
│   │   ├── AgentCard.astro         # Agent display card
│   │   ├── SkillBrowser.astro      # Interactive skill explorer
│   │   ├── MetricsBadge.astro      # Token/success rate badges
│   │   └── VideoDemo.astro         # Embedded demos
│   │
│   ├── data/
│   │   ├── benchmarks.json         # Copied from packages/benchmarks/results
│   │   ├── commands.json           # Generated from plugin/commands/*.md
│   │   ├── agents.json             # Generated from plugin/agents/config.json
│   │   └── skills.json             # Generated from plugin/skills/*/SKILL.md
│   │
│   ├── scripts/
│   │   ├── sync-plugin-content.ts  # Auto-generate API reference
│   │   ├── sync-benchmarks.ts      # Copy benchmark results
│   │   ├── generate-case-studies.ts # Create case study pages
│   │   └── validate-links.ts       # Check for broken links
│   │
│   └── styles/
│       └── custom.css              # Theme overrides
│
└── scripts/                        # Build scripts
    ├── prebuild.sh                 # Runs before build
    └── deploy.sh                   # Cloudflare Pages deploy
```

---

## 3. Content Architecture & Information Architecture

### 3.1 Site Structure (Sidebar Navigation)

```
📘 Getting Started
  - Installation
  - Quick Start
  - First Command
  - Configuration

🛠️ Guides
  - Issue-Driven Development
  - Feature Workflow (7 Phases)
  - Daily Operations (Morning/Nightly)
  - Power Mode Deep Dive
  - Debugging Strategies

📚 API Reference
  - Commands (24)
    - Overview
    - /popkit:issue
    - /popkit:git
    - ... (alphabetical)
  - Agents (30)
    - Overview
    - Tier 1: Always Active
    - Tier 2: On-Demand
    - Feature Workflow
  - Skills (66+)
    - Overview
    - By Category
  - Hooks
  - Output Styles

📊 Benchmarks
  - Overview & Methodology
  - Task: Bouncing Balls
  - Task: Todo App
  - Task: API Client
  - Task: Binary Search Tree
  - Task: Bug Fix
  - Vanilla vs PopKit vs Power
  - Historical Trends

🏗️ Architecture
  - High-Level Overview
  - Monorepo Structure
  - Tiered Agent System
  - Power Mode Architecture
  - PopKit Cloud API
  - Plugin Lifecycle

🤝 Contributing
  - Getting Started
  - Development Setup
  - Testing Your Changes
  - Adding Agents
  - Adding Skills
  - Adding Commands
  - Code Style Guide

💼 Case Studies
  - 3x Faster Token Usage
  - 95% Success Rate with Power Mode
  - ... (generated from benchmarks)
```

---

## 4. Benchmark Integration (Data Flow)

### 4.1 Benchmark Data Export

**packages/benchmarks/src/reports/json.ts** (new file):
```typescript
// Export benchmark results in standardized JSON format
export interface BenchmarkExport {
  version: string;
  generatedAt: string;
  tasks: {
    [taskId: string]: {
      name: string;
      description: string;
      results: {
        vanilla: MetricsSnapshot;
        popkit: MetricsSnapshot;
        power: MetricsSnapshot;
      };
      historical: MetricsSnapshot[]; // Over time
    };
  };
}

export function exportBenchmarks(): BenchmarkExport {
  // Query SQLite storage, aggregate results
}
```

### 4.2 Sync Script

**packages/docs/src/scripts/sync-benchmarks.ts**:
```typescript
import { execSync } from 'child_process';
import { readFileSync, writeFileSync } from 'fs';
import { join } from 'path';

// Run benchmark export script
execSync('npm run export --workspace=packages/benchmarks');

// Copy results to docs/src/data/
const benchmarksPath = '../../benchmarks/results/benchmarks.json';
const destPath = './src/data/benchmarks.json';
const data = readFileSync(benchmarksPath, 'utf-8');
writeFileSync(destPath, data);

console.log('✓ Benchmarks synced');
```

### 4.3 Real-time vs Static

**Two modes:**

1. **Build-time static** (default):
   - Benchmark results copied to `src/data/benchmarks.json`
   - Charts rendered at build time as static images or SVGs
   - Fast page loads, no runtime overhead

2. **Runtime dynamic** (future):
   - Fetch from PopKit Cloud API: `GET /api/benchmarks`
   - Live updates as new benchmark runs complete
   - Requires client-side JS for chart rendering

**Recommendation:** Start with build-time static, add runtime later for "live" dashboard.

---

## 5. File Naming Conventions & Frontmatter Schema

### 5.1 File Naming

- **Markdown files:** `kebab-case.mdx`
- **Components:** `PascalCase.astro`
- **Scripts:** `kebab-case.ts`
- **Data files:** `kebab-case.json`

### 5.2 Frontmatter Schema

**Content Collection Schema** (`src/content/config.ts`):
```typescript
import { defineCollection, z } from 'astro:content';

const docsCollection = defineCollection({
  type: 'content',
  schema: z.object({
    title: z.string(),
    description: z.string(),
    category: z.enum([
      'getting-started',
      'guides',
      'commands',
      'agents',
      'skills',
      'hooks',
      'benchmarks',
      'architecture',
      'contributing',
      'case-studies',
    ]),
    tags: z.array(z.string()).optional(),
    relatedCommands: z.array(z.string()).optional(),
    relatedAgents: z.array(z.string()).optional(),
    relatedSkills: z.array(z.string()).optional(),
    // For auto-generated pages
    autoGenerated: z.boolean().optional(),
    sourceFile: z.string().optional(), // Path to source in plugin/
    lastUpdated: z.date().optional(),
    // For benchmarks
    taskId: z.string().optional(),
    // For ordering
    order: z.number().optional(),
  }),
});

export const collections = {
  docs: docsCollection,
};
```

---

## 6. Build Pipeline (Content → Website)

### 6.1 Build Stages

```
1. Pre-build (npm run prebuild)
   ├─ sync-plugin-content.ts   → Extract commands/agents/skills
   ├─ sync-benchmarks.ts        → Copy benchmark results
   └─ generate-case-studies.ts  → Create case study pages

2. Build (npm run build)
   └─ Astro build               → Static site in dist/

3. Validate (npm run validate)
   └─ validate-links.ts         → Check internal/external links

4. Deploy (npm run deploy)
   └─ wrangler pages deploy     → Cloudflare Pages
```

### 6.2 Auto-generation Scripts

**sync-plugin-content.ts**:
```typescript
// Extract commands from packages/plugin/commands/*.md
import { readdirSync, readFileSync, writeFileSync } from 'fs';
import { join } from 'path';
import matter from 'gray-matter';

const PLUGIN_PATH = '../../plugin';
const COMMANDS_PATH = join(PLUGIN_PATH, 'commands');
const OUTPUT_PATH = './src/data/commands.json';

const commands = readdirSync(COMMANDS_PATH)
  .filter(f => f.endsWith('.md'))
  .map(file => {
    const content = readFileSync(join(COMMANDS_PATH, file), 'utf-8');
    const { data, content: markdown } = matter(content);
    return {
      id: file.replace('.md', ''),
      ...data,
      markdown,
    };
  });

writeFileSync(OUTPUT_PATH, JSON.stringify(commands, null, 2));
console.log(`✓ Synced ${commands.length} commands`);
```

**Similar scripts for:**
- `sync-agents.ts`: Parse `packages/plugin/agents/config.json`
- `sync-skills.ts`: Extract from `packages/plugin/skills/*/SKILL.md`
- `sync-hooks.ts`: Parse `packages/plugin/hooks/hooks.json`

### 6.3 Package.json Scripts

**packages/docs/package.json**:
```json
{
  "name": "@popkit/docs",
  "version": "1.0.0",
  "private": true,
  "scripts": {
    "dev": "npm run prebuild && astro dev",
    "prebuild": "tsx src/scripts/sync-plugin-content.ts && tsx src/scripts/sync-benchmarks.ts",
    "build": "npm run prebuild && astro build",
    "validate": "tsx src/scripts/validate-links.ts",
    "preview": "astro preview",
    "deploy": "npm run build && wrangler pages deploy dist --project-name=popkit-docs"
  },
  "dependencies": {
    "@astrojs/starlight": "^0.15.0",
    "astro": "^4.16.0",
    "chart.js": "^4.4.0",
    "sharp": "^0.33.0"
  },
  "devDependencies": {
    "@types/node": "^20.10.0",
    "gray-matter": "^4.0.3",
    "tsx": "^4.7.0",
    "typescript": "^5.3.0"
  }
}
```

---

## 7. Deployment Strategy

### 7.1 Cloudflare Pages Configuration

**packages/docs/wrangler.toml**:
```toml
name = "popkit-docs"
compatibility_date = "2024-01-01"

# Build settings
[build]
command = "npm run build"
cwd = "."
watch_dirs = ["src", "public"]

[env.production]
vars = { SITE_URL = "https://docs.popkit.dev" }

[env.preview]
vars = { SITE_URL = "https://docs-preview.popkit.dev" }
```

### 7.2 Domain Setup

- **Production:** `docs.popkit.dev` (or `docs.thehouseofdeals.com`)
- **Preview:** Cloudflare auto-generates preview URLs per branch
- **Landing:** `popkit.dev` (separate deployment)

### 7.3 GitHub Actions Workflow

**.github/workflows/deploy-docs.yml**:
```yaml
name: Deploy Docs

on:
  push:
    branches: [main]
    paths:
      - 'packages/docs/**'
      - 'packages/plugin/**'
      - 'packages/benchmarks/results/**'
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Build docs
        run: npm run build --workspace=packages/docs

      - name: Deploy to Cloudflare Pages
        uses: cloudflare/wrangler-action@v3
        with:
          apiToken: ${{ secrets.CLOUDFLARE_API_TOKEN }}
          accountId: ${{ secrets.CLOUDFLARE_ACCOUNT_ID }}
          command: pages deploy packages/docs/dist --project-name=popkit-docs
```

---

## 8. Development Workflow

### 8.1 Local Development (Step-by-Step)

```bash
# 1. Clone repo
git clone https://github.com/jrc1883/popkit.git
cd popkit

# 2. Install dependencies (monorepo root)
npm install

# 3. Start docs dev server
npm run dev --workspace=packages/docs

# Opens http://localhost:4321
```

**Hot reload works for:**
- Content changes (`src/content/docs/`)
- Component changes (`src/components/`)
- Style changes (`src/styles/`)

**Manual sync needed for:**
- Plugin content changes (run `npm run prebuild -w packages/docs`)
- Benchmark results (run benchmarks, then `npm run prebuild -w packages/docs`)

### 8.2 Writing New Documentation

**Add a new guide:**
```bash
# 1. Create file
touch packages/docs/src/content/docs/guides/my-new-guide.mdx

# 2. Add frontmatter
---
title: My New Guide
description: How to do X
category: guides
tags: [feature, workflow]
order: 5
---

# 3. Write content (Starlight auto-adds to sidebar)
```

**Add a new case study:**
```bash
# Option 1: Manual
touch packages/docs/src/content/docs/case-studies/my-case-study.mdx

# Option 2: Auto-generated from benchmark
# Edit packages/docs/src/scripts/generate-case-studies.ts
```

### 8.3 Editing Auto-generated Content

**Important:** Do not edit auto-generated files directly!

**To update command docs:**
1. Edit `packages/plugin/commands/{command}.md`
2. Run `npm run prebuild -w packages/docs`
3. Content re-syncs automatically

**To update agent docs:**
1. Edit `packages/plugin/agents/{tier}/{agent}/AGENT.md`
2. Run `npm run prebuild -w packages/docs`

---

## 9. Scalability Considerations

### 9.1 Performance

**Current scale:**
- 24 commands × ~1 page each = 24 pages
- 30 agents × ~1 page each = 30 pages
- 66 skills × ~1 page each = 66 pages
- Benchmarks: 5 tasks × 3 pages each = 15 pages
- Guides: ~15 pages
- Architecture: ~10 pages
- **Total: ~160 pages**

**Starlight performance:**
- Handles 1000+ pages easily
- Build time: ~1s per page (160 pages = ~3min)
- Search: Pagefind (auto-generated, fast)

**Optimization strategies:**
- Use Astro's partial hydration (islands)
- Lazy-load benchmark charts
- Compress images (Sharp integration)
- CDN via Cloudflare Pages

### 9.2 Content Growth

**As PopKit evolves:**
- v2.0: Multi-IDE support → Separate sections per IDE
- Skills grow to 100+: Paginate skill browser
- Benchmarks grow: Historical trends dashboard
- Case studies: Auto-generate from every benchmark run

**Scalable patterns:**
- **Collections:** Use Astro content collections for type-safe scaling
- **Dynamic routes:** `[...slug].astro` for programmatic pages
- **Pagination:** `import { getCollection } from 'astro:content'`

### 9.3 Search Strategy

**Starlight includes:**
- **Pagefind** (built-in): Static site search
- Indexes all page content at build time
- No server needed, works offline
- Fast fuzzy search

**Future enhancements:**
- **Algolia DocSearch** (free for OSS): Better relevance, analytics
- **Code search**: Search command/skill code snippets

---

## 10. MVP Implementation Checklist

### Phase 1: Foundation (Week 1)
- [ ] Create `packages/docs/` directory structure
- [ ] Install Astro + Starlight
- [ ] Configure `astro.config.mjs` with Starlight theme
- [ ] Set up `wrangler.toml` for Cloudflare Pages
- [ ] Create homepage (`src/content/docs/index.mdx`)
- [ ] Add basic sidebar navigation structure

### Phase 2: Content Migration (Week 2)
- [ ] Migrate existing README content to guides
- [ ] Create Getting Started section (installation, quick start)
- [ ] Write Guides section (issue-driven dev, feature workflow)
- [ ] Add Architecture section (overview, tiered agents)

### Phase 3: Auto-generation (Week 3)
- [ ] Write `sync-plugin-content.ts` (commands, agents, skills)
- [ ] Write `sync-benchmarks.ts` (benchmark results)
- [ ] Create data files (`commands.json`, `agents.json`, etc.)
- [ ] Generate API reference pages programmatically
- [ ] Add frontmatter schema validation

### Phase 4: Benchmark Visualization (Week 4)
- [ ] Create `BenchmarkChart.astro` component
- [ ] Create `BenchmarkComparison.astro` component
- [ ] Add benchmark task pages (bouncing-balls, todo-app, etc.)
- [ ] Create "Vanilla vs PopKit vs Power" comparison page
- [ ] Add historical trends charts

### Phase 5: Polish & Deploy (Week 5)
- [ ] Add search functionality (Starlight default)
- [ ] Create contributing guide
- [ ] Add case studies (auto-generated from benchmarks)
- [ ] Write deployment docs
- [ ] Set up GitHub Actions workflow
- [ ] Deploy to Cloudflare Pages
- [ ] Configure custom domain

---

## 11. Example Astro Config

**packages/docs/astro.config.mjs**:
```javascript
import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';

export default defineConfig({
  site: process.env.SITE_URL || 'https://docs.popkit.dev',
  integrations: [
    starlight({
      title: 'PopKit Docs',
      logo: {
        src: './src/assets/logo.svg',
      },
      social: {
        github: 'https://github.com/jrc1883/popkit',
      },
      sidebar: [
        {
          label: 'Getting Started',
          autogenerate: { directory: 'getting-started' },
        },
        {
          label: 'Guides',
          autogenerate: { directory: 'guides' },
        },
        {
          label: 'Commands',
          autogenerate: { directory: 'commands' },
        },
        {
          label: 'Agents',
          items: [
            { label: 'Overview', link: '/agents/' },
            {
              label: 'Tier 1: Always Active',
              autogenerate: { directory: 'agents/tier-1' },
            },
            {
              label: 'Tier 2: On-Demand',
              autogenerate: { directory: 'agents/tier-2' },
            },
          ],
        },
        {
          label: 'Benchmarks',
          autogenerate: { directory: 'benchmarks' },
        },
        {
          label: 'Architecture',
          autogenerate: { directory: 'architecture' },
        },
        {
          label: 'Contributing',
          autogenerate: { directory: 'contributing' },
        },
        {
          label: 'Case Studies',
          autogenerate: { directory: 'case-studies' },
        },
      ],
      customCss: [
        './src/styles/custom.css',
      ],
      components: {
        // Override default components if needed
        Head: './src/components/Head.astro',
      },
    }),
  ],
});
```

---

## 12. Example Benchmark Component

**packages/docs/src/components/BenchmarkComparison.astro**:
```astro
---
import { getEntry } from 'astro:content';
import benchmarks from '../data/benchmarks.json';

const { taskId } = Astro.props;
const task = benchmarks.tasks[taskId];

const modes = ['vanilla', 'popkit', 'power'];
const metrics = [
  { key: 'tokenEstimate', label: 'Tokens', format: (v) => v.toLocaleString() },
  { key: 'successRate', label: 'Success Rate', format: (v) => `${(v * 100).toFixed(0)}%` },
  { key: 'timeEstimate', label: 'Time (s)', format: (v) => v },
];
---

<div class="benchmark-comparison">
  <h3>Benchmark Results: {task.name}</h3>

  <table>
    <thead>
      <tr>
        <th>Mode</th>
        {metrics.map(m => <th>{m.label}</th>)}
      </tr>
    </thead>
    <tbody>
      {modes.map(mode => (
        <tr>
          <td class="mode-label">{mode}</td>
          {metrics.map(m => (
            <td>{m.format(task.results[mode][m.key])}</td>
          ))}
        </tr>
      ))}
    </tbody>
  </table>

  <div class="chart-container">
    <canvas id={`chart-${taskId}`}></canvas>
  </div>
</div>

<script>
  import Chart from 'chart.js/auto';

  const taskId = document.currentScript.dataset.taskId;
  const ctx = document.getElementById(`chart-${taskId}`);

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Vanilla', 'PopKit', 'Power'],
      datasets: [{
        label: 'Tokens',
        data: [15000, 10000, 8000], // From benchmarks.json
        backgroundColor: ['#ff6b6b', '#4ecdc4', '#45b7d1'],
      }],
    },
    options: {
      responsive: true,
      plugins: {
        title: { display: true, text: 'Token Usage Comparison' },
      },
    },
  });
</script>

<style>
  .benchmark-comparison {
    margin: 2rem 0;
    padding: 1.5rem;
    border: 1px solid var(--sl-color-gray-5);
    border-radius: 8px;
  }

  table {
    width: 100%;
    margin-bottom: 1.5rem;
    border-collapse: collapse;
  }

  th, td {
    padding: 0.75rem;
    text-align: left;
    border-bottom: 1px solid var(--sl-color-gray-5);
  }

  .mode-label {
    font-weight: 600;
    text-transform: capitalize;
  }

  .chart-container {
    max-width: 600px;
    margin: 0 auto;
  }
</style>
```

---

## 13. SEO Strategy

### 13.1 Meta Tags

**Per-page SEO** (via frontmatter):
```yaml
---
title: PopKit Commands Reference
description: Complete guide to all PopKit commands for Claude Code
keywords: [popkit, claude code, commands, cli, workflow]
ogImage: /images/og/commands.png
---
```

### 13.2 Target Keywords

- "Claude Code plugin"
- "AI development workflow"
- "Claude Code automation"
- "PopKit benchmarks"
- "Claude Code Power Mode"

---

## 14. Evolution Path Roadmap

### v1.0: MVP (Current Plan)
- ✅ Basic content structure
- ✅ Auto-generated API reference
- ✅ Benchmark visualization
- ✅ Cloudflare Pages deployment

### v1.1: Enhanced Search
- [ ] Algolia DocSearch integration
- [ ] Code snippet search
- [ ] Advanced filtering (by tag, category)

### v1.2: Interactive Features
- [ ] Live benchmark dashboard (real-time)
- [ ] Interactive skill browser
- [ ] Command builder (form → generates command)

### v1.3: Multi-IDE Support
- [ ] VS Code section
- [ ] Cursor section
- [ ] Windsurf section
- [ ] IDE comparison matrix

### v2.0: Community Features
- [ ] User-submitted case studies
- [ ] Community showcase (best workflows)
- [ ] Integration gallery (MCP servers, skills)
- [ ] Video tutorials

---

## 15. Next Steps for Implementation

1. **Initialize package:**
   ```bash
   cd packages/docs
   npm init -y
   npm install astro @astrojs/starlight sharp
   ```

2. **Create directory structure:**
   ```bash
   mkdir -p src/{content/docs,components,scripts,data,styles} public/images
   ```

3. **Create `astro.config.mjs`** (use example from Section 11)

4. **Write sync scripts** (Section 6.2)

5. **Migrate README content** to `src/content/docs/`

6. **Create benchmark components** (Section 12)

7. **Test locally:**
   ```bash
   npm run dev
   ```

8. **Set up Cloudflare Pages:**
   ```bash
   npm run deploy
   ```

9. **Configure GitHub Actions** (Section 9.3)

10. **Launch and iterate!**

---

## 16. Key Files Summary

### Files You'll Create/Edit

**Configuration Files:**
- `packages/docs/package.json` - Package manifest
- `packages/docs/astro.config.mjs` - Astro configuration
- `packages/docs/tsconfig.json` - TypeScript configuration
- `packages/docs/wrangler.toml` - Cloudflare config
- `packages/docs/src/content/config.ts` - Content schema

**Build Scripts:**
- `packages/docs/src/scripts/sync-plugin-content.ts` - Auto-generate API refs
- `packages/docs/src/scripts/sync-benchmarks.ts` - Copy benchmark data
- `packages/docs/src/scripts/generate-case-studies.ts` - Create case studies

**Components:**
- `packages/docs/src/components/BenchmarkChart.astro`
- `packages/docs/src/components/BenchmarkComparison.astro`
- `packages/docs/src/components/CommandReference.astro`

**Content (Auto-generated):**
- `packages/docs/src/data/commands.json`
- `packages/docs/src/data/agents.json`
- `packages/docs/src/data/benchmarks.json`

**Content (Manual):**
- `packages/docs/src/content/docs/index.mdx` - Home page
- `packages/docs/src/content/docs/getting-started/*.mdx` - Getting started
- `packages/docs/src/content/docs/guides/*.mdx` - Guides
- `packages/docs/src/content/docs/benchmarks/*.mdx` - Benchmark pages
- `packages/docs/src/content/docs/architecture/*.mdx` - Architecture docs

---

## 17. Timeline Summary

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| 1: Foundation | 1 week | Working Astro + Starlight setup |
| 2: Content | 1 week | README migrated, basic guides |
| 3: Auto-gen | 1 week | API references, sync scripts |
| 4: Benchmarks | 1 week | Chart components, benchmark pages |
| 5: Deploy | 1 week | Live docs site, GitHub Actions |
| **Total** | **5 weeks** | **Production-ready docs site** |

---

## 18. Success Metrics

Once the docs site launches, track these metrics:

- **Traffic:** Page views, session duration, bounce rate
- **Search:** Most-searched terms, search success rate
- **Benchmarks:** Views per benchmark, engagement time on charts
- **Developer Experience:** Time to find answers, guide completion rate
- **SEO:** Google ranking for target keywords

---

## Final Notes

This design is **comprehensive yet pragmatic**:
- **MVP-first**: Start with content structure, add features incrementally
- **Scalable**: Design supports growth from 160 → 1000+ pages
- **Maintainable**: Auto-generation keeps docs in sync with code
- **User-focused**: Benchmarks are the star, everything else supports them

The docs site will be your **proof of concept** for PopKit's value. When your benchmarks show that PopKit is 3x faster with 95% success rates, this docs site will be where developers come to learn **why**.

Good luck! 🚀

---

**Document Version:** 1.0.0
**Last Updated:** 2025-12-15
**Status:** Ready for Implementation
