/**
 * OpenAI Embeddings Module
 *
 * Handles embedding generation using OpenAI's API
 * Extracted from Genesis app's openai.ts
 */

import type { EmbeddingRequest, EmbeddingResponse, OpenAIError } from './types.js'

const OPENAI_API_BASE = 'https://api.openai.com/v1'
const DEFAULT_MODEL = 'text-embedding-3-small'
const DEFAULT_DIMENSIONS = 1536

// Pricing: text-embedding-3-small = $0.020 per 1M tokens
const PRICE_PER_1M_TOKENS = 0.02

export class EmbeddingsClient {
  private apiKey: string
  private model: string
  private dimensions: number

  constructor(config: { apiKey: string; model?: string; dimensions?: number }) {
    this.apiKey = config.apiKey
    this.model = config.model || DEFAULT_MODEL
    this.dimensions = config.dimensions || DEFAULT_DIMENSIONS

    if (!this.apiKey) {
      throw new Error('OpenAI API key is required')
    }
  }

  /**
   * Generate embeddings for text
   */
  async createEmbedding(
    input: string | string[],
    options?: {
      model?: string
      dimensions?: number
      user?: string
    }
  ): Promise<EmbeddingResponse> {
    const model = options?.model || this.model
    const dimensions = options?.dimensions || this.dimensions

    const requestBody: EmbeddingRequest = {
      input,
      model,
      encoding_format: 'float',
      dimensions,
      user: options?.user,
    }

    const response = await fetch(`${OPENAI_API_BASE}/embeddings`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify(requestBody),
    })

    if (!response.ok) {
      const error = (await response.json()) as OpenAIError
      throw new Error(`OpenAI API error: ${error.error.message} (${error.error.type})`)
    }

    return (await response.json()) as EmbeddingResponse
  }

  /**
   * Generate embedding for a single text
   */
  async embedText(text: string, options?: { model?: string; dimensions?: number }): Promise<number[]> {
    const response = await this.createEmbedding(text, options)
    return response.data[0].embedding
  }

  /**
   * Generate embeddings for multiple texts in batch
   */
  async embedBatch(texts: string[], options?: { model?: string; dimensions?: number }): Promise<number[][]> {
    const response = await this.createEmbedding(texts, options)
    return response.data.sort((a, b) => a.index - b.index).map((item) => item.embedding)
  }

  /**
   * Calculate estimated cost for embedding texts
   */
  estimateCost(texts: string[]): { tokens: number; cost_usd: number } {
    // Rough estimation: average ~4 characters per token
    const totalChars = texts.reduce((sum, text) => sum + text.length, 0)
    const estimatedTokens = Math.ceil(totalChars / 4)
    const cost = (estimatedTokens / 1_000_000) * PRICE_PER_1M_TOKENS

    return {
      tokens: estimatedTokens,
      cost_usd: parseFloat(cost.toFixed(4)),
    }
  }

  /**
   * Calculate actual cost from usage response
   */
  calculateCost(usage: { prompt_tokens: number; total_tokens: number }): number {
    return (usage.total_tokens / 1_000_000) * PRICE_PER_1M_TOKENS
  }

  /**
   * Process large batch with rate limiting and error handling
   */
  async embedBatchWithRetry(
    texts: string[],
    options?: {
      model?: string
      dimensions?: number
      batchSize?: number
      maxRetries?: number
      onProgress?: (progress: { current: number; total: number; percentage: number }) => void
    }
  ): Promise<{
    embeddings: number[][]
    successful: number
    failed: number
    totalCost: number
  }> {
    const batchSize = options?.batchSize || 100
    const maxRetries = options?.maxRetries || 3

    const embeddings: number[][] = []
    let successful = 0
    let failed = 0
    let totalCost = 0

    for (let i = 0; i < texts.length; i += batchSize) {
      const batch = texts.slice(i, i + batchSize)
      let retries = 0
      let batchSuccess = false

      while (retries < maxRetries && !batchSuccess) {
        try {
          const response = await this.createEmbedding(batch, {
            model: options?.model,
            dimensions: options?.dimensions,
          })

          const batchEmbeddings = response.data.sort((a, b) => a.index - b.index).map((item) => item.embedding)

          embeddings.push(...batchEmbeddings)
          successful += batch.length
          totalCost += this.calculateCost(response.usage)
          batchSuccess = true

          // Report progress
          if (options?.onProgress) {
            options.onProgress({
              current: i + batch.length,
              total: texts.length,
              percentage: Math.round(((i + batch.length) / texts.length) * 100),
            })
          }
        } catch (error) {
          retries++
          if (retries >= maxRetries) {
            // Add empty embeddings for failed batch
            embeddings.push(...Array(batch.length).fill([]))
            failed += batch.length
          } else {
            // Exponential backoff
            await new Promise((resolve) => setTimeout(resolve, Math.pow(2, retries) * 1000))
          }
        }
      }
    }

    return {
      embeddings,
      successful,
      failed,
      totalCost: parseFloat(totalCost.toFixed(4)),
    }
  }
}
