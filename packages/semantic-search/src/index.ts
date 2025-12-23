/**
 * @elshaddai/semantic-search
 *
 * Semantic search package using OpenAI embeddings and pgvector
 */

// Main client
export { SemanticSearchClient, createSemanticSearch } from './client.js'

// Individual modules (for advanced usage)
export { EmbeddingsClient } from './embeddings.js'
export { EmbeddingCache } from './cache.js'
export { SearchClient } from './search.js'

// Types
export type {
  // Configuration
  RedisConfig,
  CacheConfig,
  SemanticSearchConfig,
  // Embeddings
  EmbeddingRequest,
  EmbeddingResponse,
  OpenAIError,
  // Search
  SemanticSearchOptions,
  HybridSearchOptions,
  SearchResult,
  HybridSearchResult,
  // Batch operations
  BatchEmbeddingOptions,
  BatchProgress,
  BatchResult,
  // Client interface
  SemanticSearchClient as ISemanticSearchClient,
} from './types.js'
