/**
 * Search Module
 *
 * Provides semantic and hybrid search using Supabase pgvector
 * Extracted from Genesis app's search functionality
 */

import { createClient, SupabaseClient } from '@supabase/supabase-js'
import type { SearchResult, HybridSearchResult } from './types.js'

export class SearchClient {
  private supabase: SupabaseClient

  constructor(supabaseUrl: string, supabaseKey: string) {
    this.supabase = createClient(supabaseUrl, supabaseKey)
  }

  /**
   * Execute semantic search with pre-computed embedding
   */
  async searchWithEmbedding(
    _table: string,
    queryEmbedding: number[],
    options: {
      limit?: number
      threshold?: number
      filters?: Record<string, unknown>
    } = {}
  ): Promise<SearchResult[]> {
    const { limit = 20, filters = {} } = options

    // Call Supabase RPC function for semantic search
    const { data, error } = await this.supabase.rpc('search_verses_semantic', {
      p_query_embedding: `[${queryEmbedding.join(',')}]`,
      p_limit: limit,
      p_book_codes: (filters.books as string[]) || null,
      p_testament: (filters.testament as string) || null,
    })

    if (error) {
      throw new Error(`Semantic search failed: ${error.message}`)
    }

    return (
      data?.map((row: any) => ({
        id: row.verse_key,
        text: row.verse_text,
        similarity: row.similarity,
        metadata: {
          book_name: row.book_name,
          verse_key: row.verse_key,
        },
      })) || []
    )
  }

  /**
   * Hybrid search combining semantic and keyword search
   */
  async hybridSearch(
    queryText: string,
    queryEmbedding: number[],
    options: {
      limit?: number
      semanticWeight?: number
      keywordWeight?: number
      filters?: Record<string, unknown>
    } = {}
  ): Promise<HybridSearchResult[]> {
    const {
      limit = 20,
      semanticWeight = 0.7,
      keywordWeight = 0.3,
      filters = {},
    } = options

    // Validate weights
    if (Math.abs(semanticWeight + keywordWeight - 1.0) > 0.01) {
      throw new Error('Weights must sum to 1.0')
    }

    // Call Supabase RPC function for hybrid search
    const { data, error } = await this.supabase.rpc('search_verses_hybrid', {
      query_text: queryText,
      query_embedding: `[${queryEmbedding.join(',')}]`,
      semantic_weight: semanticWeight,
      keyword_weight: keywordWeight,
      match_count: limit,
      filter_books: (filters.books as string[]) || null,
      filter_testament: (filters.testament as string) || null,
    })

    if (error) {
      throw new Error(`Hybrid search failed: ${error.message}`)
    }

    return (
      data?.map((row: any) => ({
        id: row.verse_key,
        text: row.verse_text,
        similarity: row.hybrid_score,
        semantic_score: row.semantic_score,
        keyword_score: row.keyword_score,
        hybrid_score: row.hybrid_score,
        metadata: {
          book_code: row.book_code,
          book_name: row.book_name,
          chapter: row.chapter,
          verse: row.verse,
          verse_key: row.verse_key,
          translation_id: row.translation_id,
          testament: row.testament,
        },
      })) || []
    )
  }

  /**
   * Get raw Supabase client for custom queries
   */
  getClient(): SupabaseClient {
    return this.supabase
  }

  /**
   * Close connections (placeholder - Supabase client doesn't need explicit cleanup)
   */
  async close(): Promise<void> {
    // Supabase client doesn't require explicit cleanup
  }
}
