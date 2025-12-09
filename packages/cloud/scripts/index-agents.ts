/**
 * Agent Indexing Script
 *
 * Part of Issue #101 (Upstash Vector Integration)
 *
 * Reads all AGENT.md files from the plugin package and indexes them in Upstash Vector.
 * Run once during setup, then whenever agents are added or modified.
 *
 * Usage:
 *   UPSTASH_VECTOR_REST_URL=... UPSTASH_VECTOR_REST_TOKEN=... npx tsx scripts/index-agents.ts
 *
 * Prerequisites:
 *   npm install @upstash/vector yaml tsx
 */

import { Index } from '@upstash/vector';
import * as fs from 'fs';
import * as path from 'path';

// =============================================================================
// CONFIGURATION
// =============================================================================

const PLUGIN_ROOT = path.join(__dirname, '../../plugin');
const TIERS = ['tier-1-always-active', 'tier-2-on-demand', 'feature-workflow'] as const;

type Tier = (typeof TIERS)[number];

interface AgentMetadata {
  name: string;
  tier: Tier;
  keywords: string[];
  description: string;
}

// =============================================================================
// YAML FRONTMATTER PARSER (simple, no external dependency)
// =============================================================================

function extractFrontmatter(content: string): Record<string, string> {
  if (!content.startsWith('---')) return {};
  const end = content.indexOf('---', 3);
  if (end < 0) return {};

  const yamlContent = content.slice(3, end);
  const result: Record<string, string> = {};

  for (const line of yamlContent.split('\n')) {
    const colonIndex = line.indexOf(':');
    if (colonIndex > 0) {
      const key = line.slice(0, colonIndex).trim();
      let value = line.slice(colonIndex + 1).trim();
      // Remove quotes if present
      if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
        value = value.slice(1, -1);
      }
      result[key] = value;
    }
  }

  return result;
}

// =============================================================================
// KEYWORD EXTRACTION
// =============================================================================

function extractKeywordsForAgent(agentName: string, configPath: string): string[] {
  const keywords: string[] = [];

  try {
    const config = JSON.parse(fs.readFileSync(configPath, 'utf-8'));
    const routing = config.routing?.keywords || {};

    for (const [keyword, agents] of Object.entries(routing)) {
      if (Array.isArray(agents) && agents.includes(agentName)) {
        keywords.push(keyword);
      }
    }
  } catch (e) {
    console.warn(`Could not read config.json: ${e}`);
  }

  return keywords;
}

// =============================================================================
// MAIN
// =============================================================================

async function main() {
  // Check environment
  const url = process.env.UPSTASH_VECTOR_REST_URL;
  const token = process.env.UPSTASH_VECTOR_REST_TOKEN;

  if (!url || !token) {
    console.error('Error: UPSTASH_VECTOR_REST_URL and UPSTASH_VECTOR_REST_TOKEN are required');
    console.error('');
    console.error('Usage:');
    console.error('  UPSTASH_VECTOR_REST_URL=... UPSTASH_VECTOR_REST_TOKEN=... npx tsx scripts/index-agents.ts');
    process.exit(1);
  }

  const index = new Index<AgentMetadata>({
    url,
    token,
  });

  const configPath = path.join(PLUGIN_ROOT, 'agents/config.json');

  // Collect all agents
  const agents: Array<{
    id: string;
    data: string; // Description for auto-embedding
    metadata: AgentMetadata;
  }> = [];

  console.log('Scanning agent directories...\n');

  for (const tier of TIERS) {
    const tierPath = path.join(PLUGIN_ROOT, 'agents', tier);

    if (!fs.existsSync(tierPath)) {
      console.log(`  [skip] ${tier} - directory not found`);
      continue;
    }

    const agentDirs = fs.readdirSync(tierPath);

    for (const agentDir of agentDirs) {
      const agentFile = path.join(tierPath, agentDir, 'AGENT.md');

      if (!fs.existsSync(agentFile)) {
        continue;
      }

      const content = fs.readFileSync(agentFile, 'utf-8');
      const frontmatter = extractFrontmatter(content);

      if (!frontmatter.description) {
        console.warn(`  [warn] ${agentDir}: no description in frontmatter`);
        continue;
      }

      const keywords = extractKeywordsForAgent(agentDir, configPath);

      agents.push({
        id: agentDir,
        data: frontmatter.description, // Auto-embedded by Upstash
        metadata: {
          name: agentDir,
          tier: tier,
          keywords,
          description: frontmatter.description,
        },
      });

      console.log(`  [found] ${agentDir} (${tier})`);
    }
  }

  console.log(`\nFound ${agents.length} agents to index\n`);

  if (agents.length === 0) {
    console.log('No agents found. Check that PLUGIN_ROOT is correct.');
    process.exit(1);
  }

  // Upsert in batches of 10 (Upstash recommends batching)
  const batchSize = 10;
  let indexed = 0;

  console.log('Indexing agents...\n');

  for (let i = 0; i < agents.length; i += batchSize) {
    const batch = agents.slice(i, i + batchSize);

    try {
      await index.upsert(batch);
      indexed += batch.length;
      console.log(`  [indexed] ${indexed}/${agents.length}`);
    } catch (error) {
      console.error(`  [error] Failed to index batch: ${error}`);
    }
  }

  console.log('\n=== Indexing Complete ===');
  console.log(`  Total agents: ${agents.length}`);
  console.log(`  Successfully indexed: ${indexed}`);

  // Verify by listing
  console.log('\nVerifying index...');
  try {
    const result = await index.range({
      cursor: '0',
      limit: 100,
      includeMetadata: true,
    });
    console.log(`  Vectors in index: ${result.vectors.length}`);

    // Group by tier
    const byTier: Record<string, number> = {};
    for (const v of result.vectors) {
      const tier = (v.metadata as AgentMetadata)?.tier || 'unknown';
      byTier[tier] = (byTier[tier] || 0) + 1;
    }

    console.log('\n  By tier:');
    for (const [tier, count] of Object.entries(byTier)) {
      console.log(`    ${tier}: ${count}`);
    }
  } catch (error) {
    console.warn(`  Could not verify: ${error}`);
  }

  console.log('\nDone!');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});
