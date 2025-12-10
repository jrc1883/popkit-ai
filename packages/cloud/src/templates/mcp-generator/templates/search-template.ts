/**
 * Search Tools Template (Semantic + Keyword)
 */

export const searchTemplate = `/**
 * Tool search with semantic and keyword matching
 */

interface Tool {
  name: string;
  description: string;
  inputSchema: Record<string, unknown>;
  handler: (args: Record<string, unknown>, workspacePath: string) => Promise<unknown>;
}

interface SearchResult {
  tool: Tool;
  score: number;
  method: 'keyword';
}

export function createToolSearch(tools: Tool[]) {
  // Pre-process tool descriptions into keywords
  const toolKeywords = tools.map((tool) => ({
    tool,
    keywords: extractKeywords(tool.name + ' ' + tool.description),
  }));

  return {
    /**
     * Search for tools matching a query using keyword matching
     */
    search(query: string, topK: number = 5): Promise<SearchResult[]> {
      const queryKeywords = extractKeywords(query);

      // Score each tool based on keyword overlap
      const scored = toolKeywords.map(({ tool, keywords }) => {
        const score = calculateScore(queryKeywords, keywords);
        return { tool, score, method: 'keyword' as const };
      });

      // Sort by score and return top K
      return Promise.resolve(
        scored
          .sort((a, b) => b.score - a.score)
          .slice(0, topK)
          .filter((r) => r.score > 0)
      );
    },

    /**
     * Get search configuration info
     */
    getInfo(): { toolsCount: number } {
      return { toolsCount: tools.length };
    },
  };
}

function extractKeywords(text: string): Set<string> {
  return new Set(
    text
      .toLowerCase()
      .replace(/[^a-z0-9\\s]/g, ' ')
      .split(/\\s+/)
      .filter((word) => word.length > 2)
  );
}

function calculateScore(queryKeywords: Set<string>, toolKeywords: Set<string>): number {
  let matches = 0;
  for (const keyword of queryKeywords) {
    if (toolKeywords.has(keyword)) {
      matches++;
    } else {
      // Partial match
      for (const toolKeyword of toolKeywords) {
        if (toolKeyword.includes(keyword) || keyword.includes(toolKeyword)) {
          matches += 0.5;
          break;
        }
      }
    }
  }
  return matches / Math.max(queryKeywords.size, 1);
}
`;
