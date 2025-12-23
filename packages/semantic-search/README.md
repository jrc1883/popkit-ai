# @elshaddai/semantic-search

Semantic search package using OpenAI embeddings and PostgreSQL pgvector, extracted from the Genesis app.

## Features

- **OpenAI Embeddings**: Generate vector embeddings using text-embedding-3-small
- **pgvector Search**: Semantic similarity search using PostgreSQL pgvector extension
- **Redis Caching**: 50-70% cost reduction through intelligent embedding caching
- **Hybrid Search**: Combine semantic similarity with keyword matching
- **Batch Operations**: Efficient batch embedding generation with retry logic
- **TypeScript**: Full TypeScript support with strict mode
- **Tested**: 27 comprehensive tests covering all functionality

## Installation

```bash
pnpm add @elshaddai/semantic-search
```

### Dependencies

- **OpenAI API Key**: For embedding generation
- **Supabase**: PostgreSQL database with pgvector extension
- **Redis** (optional): For embedding caching

### Database Setup

Your Supabase/PostgreSQL database must have:

1. **pgvector extension** installed:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

2. **Embeddings table** with vector column:
```sql
CREATE TABLE bible_verse_embeddings (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  verse_key VARCHAR(20) NOT NULL UNIQUE,
  verse_text TEXT NOT NULL,
  embedding vector(1536) NOT NULL,
  -- ... other columns
);

-- Create IVFFlat index for fast similarity search
CREATE INDEX ON bible_verse_embeddings
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
```

3. **Search functions** (see Genesis migrations for full implementation):
```sql
-- Semantic search function
CREATE FUNCTION search_verses_semantic(
  p_query_embedding vector(1536),
  p_limit INTEGER DEFAULT 20,
  p_book_codes TEXT[] DEFAULT NULL,
  p_testament VARCHAR(2) DEFAULT NULL
) RETURNS TABLE (...);

-- Hybrid search function
CREATE FUNCTION search_verses_hybrid(
  query_text TEXT,
  query_embedding vector(1536),
  semantic_weight FLOAT DEFAULT 0.7,
  keyword_weight FLOAT DEFAULT 0.3,
  match_count INTEGER DEFAULT 20
) RETURNS TABLE (...);
```

## Quick Start

### Basic Usage

```typescript
import { createSemanticSearch } from '@elshaddai/semantic-search'

const searchClient = createSemanticSearch({
  openaiKey: process.env.OPENAI_API_KEY!,
  supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL!,
  supabaseKey: process.env.SUPABASE_SERVICE_ROLE_KEY!,
  embeddingModel: 'text-embedding-3-small',
  embeddingDimensions: 1536,
})

// Semantic search
const results = await searchClient.query({
  text: 'faith and works',
  table: 'bible_verse_embeddings',
  limit: 20,
})

console.log(results)
// [
//   {
//     id: 'JAS.2.26',
//     text: 'For as the body without the spirit is dead...',
//     similarity: 0.85,
//     metadata: { book_name: 'James', verse_key: 'JAS.2.26' }
//   }
// ]
```

### With Redis Caching

```typescript
const searchClient = createSemanticSearch({
  openaiKey: process.env.OPENAI_API_KEY!,
  supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL!,
  supabaseKey: process.env.SUPABASE_SERVICE_ROLE_KEY!,
  cache: {
    enabled: true,
    ttl: 86400, // 24 hours
    redis: {
      host: process.env.REDIS_HOST || 'localhost',
      port: parseInt(process.env.REDIS_PORT || '6379'),
      password: process.env.REDIS_PASSWORD,
    },
  },
})

// Check cache stats
const stats = searchClient.getCacheStats()
console.log(`Cache hit rate: ${stats?.hitRate}%`)
```

### Hybrid Search

```typescript
const results = await searchClient.hybrid({
  text: 'love thy neighbor',
  table: 'bible_verse_embeddings',
  keywordColumns: ['verse_text'],
  weights: {
    semantic: 0.7,
    keyword: 0.3,
  },
  limit: 20,
})

console.log(results)
// [
//   {
//     id: 'LEV.19.18',
//     text: '...thou shalt love thy neighbour as thyself...',
//     similarity: 0.82,
//     semantic_score: 0.85,
//     keyword_score: 0.75,
//     hybrid_score: 0.82,
//     metadata: { ... }
//   }
// ]
```

## API Reference

### SemanticSearchClient

Main client for semantic search operations.

#### `createSemanticSearch(config: SemanticSearchConfig): SemanticSearchClient`

Factory function to create a client instance.

**Config Options:**
```typescript
interface SemanticSearchConfig {
  openaiKey: string              // OpenAI API key
  supabaseUrl: string            // Supabase project URL
  supabaseKey: string            // Supabase service role key
  embeddingModel?: string        // Default: 'text-embedding-3-small'
  embeddingDimensions?: number   // Default: 1536
  cache?: CacheConfig            // Optional Redis caching
  rateLimit?: {
    requestsPerMinute: number
  }
}

interface CacheConfig {
  enabled: boolean
  ttl: number                    // Cache TTL in seconds
  redis: RedisConfig
}
```

#### `generateEmbedding(text: string): Promise<number[]>`

Generate embedding for a single text.

```typescript
const embedding = await client.generateEmbedding('faith and hope')
// [0.123, -0.456, 0.789, ...]
```

#### `generateEmbeddings(texts: string[]): Promise<number[][]>`

Generate embeddings for multiple texts (batch).

```typescript
const embeddings = await client.generateEmbeddings([
  'faith',
  'hope',
  'love',
])
// [[0.123, ...], [0.456, ...], [0.789, ...]]
```

#### `query(options: SemanticSearchOptions): Promise<SearchResult[]>`

Perform semantic similarity search.

```typescript
const results = await client.query({
  text: 'forgiveness and mercy',
  table: 'bible_verse_embeddings',
  limit: 20,
  threshold: 0.7,
  filters: {
    books: ['MAT', 'LUK'],
    testament: 'NT',
  },
})
```

#### `hybrid(options: HybridSearchOptions): Promise<HybridSearchResult[]>`

Perform hybrid search (semantic + keyword).

```typescript
const results = await client.hybrid({
  text: 'peace and joy',
  table: 'bible_verse_embeddings',
  keywordColumns: ['verse_text'],
  weights: {
    semantic: 0.7,
    keyword: 0.3,
  },
  limit: 20,
})
```

#### `batchEmbed(options: BatchEmbeddingOptions): Promise<BatchResult>`

Generate embeddings for entire database table with progress tracking.

```typescript
const result = await client.batchEmbed({
  table: 'bible_verse_embeddings',
  textColumn: 'verse_text',
  embeddingColumn: 'embedding',
  batchSize: 100,
  onProgress: (progress) => {
    console.log(`${progress.percentage}% complete`)
    console.log(`${progress.successful} successful, ${progress.failed} failed`)
  },
})

console.log(`Total: ${result.total}`)
console.log(`Cost: $${result.cost}`)
console.log(`Duration: ${result.duration}ms`)
```

### Advanced Usage

#### Direct Module Access

For advanced usage, you can import individual modules:

```typescript
import {
  EmbeddingsClient,
  EmbeddingCache,
  SearchClient,
} from '@elshaddai/semantic-search'

// Embeddings only
const embeddings = new EmbeddingsClient({
  apiKey: process.env.OPENAI_API_KEY!,
  model: 'text-embedding-3-small',
  dimensions: 1536,
})

const embedding = await embeddings.embedText('test')

// Cache only
const cache = new EmbeddingCache({
  host: 'localhost',
  port: 6379,
  ttl: 86400,
})

await cache.set('text', embedding, 'model', 1536)
const cached = await cache.get('text', 'model', 1536)

// Search only
const search = new SearchClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

const results = await search.searchWithEmbedding(
  'bible_verse_embeddings',
  embedding,
  { limit: 20 }
)
```

## Cost Optimization

### Embedding Costs

OpenAI text-embedding-3-small pricing: **$0.020 per 1M tokens**

```typescript
// Estimate cost before embedding
const client = new EmbeddingsClient({ apiKey: '...' })
const texts = [...] // 1000 texts
const estimate = client.estimateCost(texts)

console.log(`Estimated tokens: ${estimate.tokens}`)
console.log(`Estimated cost: $${estimate.cost_usd}`)
```

### Redis Caching Benefits

With Redis caching enabled, you can achieve **50-70% cost reduction** on repeated queries:

- First query: Generate embedding ($0.02 per 1M tokens)
- Cached queries: Redis lookup (free)
- Cache TTL: 24 hours default

```typescript
// Enable caching for cost savings
const searchClient = createSemanticSearch({
  // ...config
  cache: {
    enabled: true,
    ttl: 86400, // 24 hours
    redis: { host: 'localhost', port: 6379 },
  },
})

// Monitor cache efficiency
const stats = searchClient.getCacheStats()
console.log(`Hit rate: ${stats?.hitRate}%`)
console.log(`Hits: ${stats?.hits}, Misses: ${stats?.misses}`)
```

## Testing

Run the test suite:

```bash
pnpm test
```

Test coverage:
- ✅ 27 tests passing
- ✅ Embeddings client (16 tests)
- ✅ Redis caching (11 tests)
- ✅ Error handling
- ✅ Batch operations
- ✅ Cost estimation

## Migration Guide

### From Genesis App

If you're migrating from the Genesis app's embedded semantic search:

**Before:**
```typescript
import { getSemanticSearchClient } from '@/lib/semantic-search'

const client = getSemanticSearchClient()
const embedding = await client.generateEmbedding(query)
```

**After:**
```typescript
import { createSemanticSearch } from '@elshaddai/semantic-search'

const client = createSemanticSearch({
  openaiKey: process.env.OPENAI_API_KEY!,
  supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL!,
  supabaseKey: process.env.SUPABASE_SERVICE_ROLE_KEY!,
  cache: {
    enabled: true,
    ttl: 86400,
    redis: { host: 'localhost', port: 6379 },
  },
})

const embedding = await client.generateEmbedding(query)
```

## License

MIT

## Contributing

This package is part of the ElShaddai monorepo. Issues and pull requests should be submitted to the main repository.

## Related Packages

- `@elshaddai/ui` - Shared React components
- `@elshaddai/api-client` - Shared API client
- `@elshaddai/hooks` - Shared React hooks
