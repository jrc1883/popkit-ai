/**
 * TypeScript types for semantic search package
 */

// ============================================================================
// Configuration
// ============================================================================

export interface RedisConfig {
  host: string
  port: number
  password?: string
  db?: number
}

export interface CacheConfig {
  enabled: boolean
  ttl: number // Time to live in seconds
  redis: RedisConfig
}

export interface SemanticSearchConfig {
  openaiKey: string
  supabaseUrl: string
  supabaseKey: string
  embeddingModel?: string
  embeddingDimensions?: number
  cache?: CacheConfig
  rateLimit?: {
    requestsPerMinute: number
  }
}

// ============================================================================
// Embeddings
// ============================================================================

export interface EmbeddingRequest {
  input: string | string[]
  model?: string
  encoding_format?: 'float' | 'base64'
  dimensions?: number
  user?: string
}

export interface EmbeddingResponse {
  object: 'list'
  data: Array<{
    object: 'embedding'
    embedding: number[]
    index: number
  }>
  model: string
  usage: {
    prompt_tokens: number
    total_tokens: number
  }
}

export interface OpenAIError {
  error: {
    message: string
    type: string
    param?: string
    code?: string
  }
}

// ============================================================================
// Search
// ============================================================================

export interface SemanticSearchOptions {
  text: string
  table: string
  embeddingColumn?: string
  textColumn?: string
  limit?: number
  threshold?: number
  filters?: Record<string, unknown>
}

export interface HybridSearchOptions extends SemanticSearchOptions {
  keywordColumns: string[]
  weights?: {
    semantic: number
    keyword: number
  }
}

export interface SearchResult {
  id: string
  text: string
  similarity: number
  metadata?: Record<string, unknown>
}

export interface HybridSearchResult extends SearchResult {
  semantic_score: number
  keyword_score: number
  hybrid_score: number
}

// ============================================================================
// Batch Operations
// ============================================================================

export interface BatchEmbeddingOptions {
  table: string
  textColumn: string
  embeddingColumn: string
  batchSize?: number
  filters?: Record<string, unknown>
  onProgress?: (progress: BatchProgress) => void
}

export interface BatchProgress {
  current: number
  total: number
  percentage: number
  successful: number
  failed: number
  estimatedTimeRemaining?: number
}

export interface BatchResult {
  total: number
  successful: number
  failed: number
  duration: number
  cost: number
}

// ============================================================================
// Client Interface
// ============================================================================

export interface SemanticSearchClient {
  /**
   * Generate embedding for a single text
   */
  generateEmbedding(text: string): Promise<number[]>

  /**
   * Generate embeddings for multiple texts
   */
  generateEmbeddings(texts: string[]): Promise<number[][]>

  /**
   * Search using semantic similarity
   */
  query(options: SemanticSearchOptions): Promise<SearchResult[]>

  /**
   * Hybrid search (semantic + keyword)
   */
  hybrid(options: HybridSearchOptions): Promise<HybridSearchResult[]>

  /**
   * Batch generate embeddings for database table
   */
  batchEmbed(options: BatchEmbeddingOptions): Promise<BatchResult>

  /**
   * Close connections (Redis, Supabase)
   */
  close(): Promise<void>
}
