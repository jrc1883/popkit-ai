/**
 * Semantic Search Client
 *
 * Main client combining embeddings, caching, and search
 */

import { EmbeddingsClient } from './embeddings.js'
import { EmbeddingCache } from './cache.js'
import { SearchClient } from './search.js'
import type {
  SemanticSearchConfig,
  SemanticSearchClient as ISemanticSearchClient,
  SemanticSearchOptions,
  HybridSearchOptions,
  SearchResult,
  HybridSearchResult,
  BatchEmbeddingOptions,
  BatchResult,
} from './types.js'

export class SemanticSearchClient implements ISemanticSearchClient {
  private embeddings: EmbeddingsClient
  private cache?: EmbeddingCache
  private search: SearchClient
  private config: SemanticSearchConfig

  constructor(config: SemanticSearchConfig) {
    this.config = config

    // Initialize embeddings client
    this.embeddings = new EmbeddingsClient({
      apiKey: config.openaiKey,
      model: config.embeddingModel,
      dimensions: config.embeddingDimensions,
    })

    // Initialize cache if enabled
    if (config.cache?.enabled) {
      this.cache = new EmbeddingCache({
        ...config.cache.redis,
        ttl: config.cache.ttl,
      })
    }

    // Initialize search client
    this.search = new SearchClient(config.supabaseUrl, config.supabaseKey)
  }

  /**
   * Generate embedding for a single text
   */
  async generateEmbedding(text: string): Promise<number[]> {
    const model = this.config.embeddingModel || 'text-embedding-3-small'
    const dimensions = this.config.embeddingDimensions || 1536

    // Check cache first
    if (this.cache) {
      const cached = await this.cache.get(text, model, dimensions)
      if (cached) {
        return cached
      }
    }

    // Generate embedding
    const embedding = await this.embeddings.embedText(text, {
      model,
      dimensions,
    })

    // Cache result
    if (this.cache) {
      await this.cache.set(text, embedding, model, dimensions)
    }

    return embedding
  }

  /**
   * Generate embeddings for multiple texts
   */
  async generateEmbeddings(texts: string[]): Promise<number[][]> {
    const model = this.config.embeddingModel || 'text-embedding-3-small'
    const dimensions = this.config.embeddingDimensions || 1536

    // Check cache for all texts
    let cachedResults: Map<string, number[]> | undefined
    if (this.cache) {
      cachedResults = await this.cache.getMany(texts, model, dimensions)
    }

    // Determine which texts need embedding
    const textsToEmbed = cachedResults
      ? texts.filter((text) => !cachedResults!.has(text))
      : texts

    // Generate embeddings for uncached texts
    let newEmbeddings: number[][] = []
    if (textsToEmbed.length > 0) {
      newEmbeddings = await this.embeddings.embedBatch(textsToEmbed, {
        model,
        dimensions,
      })

      // Cache new embeddings
      if (this.cache) {
        await this.cache.setMany(
          textsToEmbed.map((text, i) => ({
            text,
            embedding: newEmbeddings[i],
          })),
          model,
          dimensions
        )
      }
    }

    // Combine cached and new results in original order
    const results: number[][] = []
    let newIndex = 0

    for (const text of texts) {
      if (cachedResults?.has(text)) {
        results.push(cachedResults.get(text)!)
      } else {
        results.push(newEmbeddings[newIndex])
        newIndex++
      }
    }

    return results
  }

  /**
   * Search using semantic similarity
   */
  async query(options: SemanticSearchOptions): Promise<SearchResult[]> {
    // Generate embedding for query
    const embedding = await this.generateEmbedding(options.text)

    // Execute search
    return this.search.searchWithEmbedding(options.table, embedding, {
      limit: options.limit,
      threshold: options.threshold,
      filters: options.filters,
    })
  }

  /**
   * Hybrid search (semantic + keyword)
   */
  async hybrid(options: HybridSearchOptions): Promise<HybridSearchResult[]> {
    // Generate embedding for query
    const embedding = await this.generateEmbedding(options.text)

    // Execute hybrid search
    return this.search.hybridSearch(options.text, embedding, {
      limit: options.limit,
      semanticWeight: options.weights?.semantic || 0.7,
      keywordWeight: options.weights?.keyword || 0.3,
      filters: options.filters,
    })
  }

  /**
   * Batch generate embeddings for database table
   */
  async batchEmbed(options: BatchEmbeddingOptions): Promise<BatchResult> {
    const startTime = Date.now()
    const batchSize = options.batchSize || 100

    // Get texts from database
    const supabase = this.search.getClient()
    const { data: rows, error } = await supabase
      .from(options.table)
      .select(`id, ${options.textColumn}`)
      .is(options.embeddingColumn, null) // Only process rows without embeddings
      .limit(10000) // Safety limit

    if (error) {
      throw new Error(`Failed to fetch texts: ${error.message}`)
    }

    if (!rows || rows.length === 0) {
      return {
        total: 0,
        successful: 0,
        failed: 0,
        duration: Date.now() - startTime,
        cost: 0,
      }
    }

    // Extract texts
    const texts = rows.map((row) => (row as any)[options.textColumn] as string)

    // Generate embeddings with retry
    const result = await this.embeddings.embedBatchWithRetry(texts, {
      model: this.config.embeddingModel,
      dimensions: this.config.embeddingDimensions,
      batchSize,
      onProgress: options.onProgress
        ? (progress) => {
            options.onProgress!({
              ...progress,
              successful: 0,
              failed: 0,
            })
          }
        : undefined,
    })

    // Update database with embeddings
    let successful = 0
    let failed = 0

    for (let i = 0; i < rows.length; i++) {
      const embedding = result.embeddings[i]
      if (embedding && embedding.length > 0) {
        const { error: updateError } = await supabase
          .from(options.table)
          .update({ [options.embeddingColumn]: embedding })
          .eq('id', (rows[i] as any).id)

        if (updateError) {
          failed++
        } else {
          successful++
        }
      } else {
        failed++
      }
    }

    return {
      total: rows.length,
      successful,
      failed,
      duration: Date.now() - startTime,
      cost: result.totalCost,
    }
  }

  /**
   * Get cache statistics (if caching enabled)
   */
  getCacheStats() {
    return this.cache?.getStats()
  }

  /**
   * Reset cache statistics
   */
  resetCacheStats(): void {
    this.cache?.resetStats()
  }

  /**
   * Close connections (Redis, Supabase)
   */
  async close(): Promise<void> {
    if (this.cache) {
      await this.cache.close()
    }
    await this.search.close()
  }
}

/**
 * Factory function to create a SemanticSearchClient
 */
export function createSemanticSearch(
  config: SemanticSearchConfig
): SemanticSearchClient {
  return new SemanticSearchClient(config)
}
