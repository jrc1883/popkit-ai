/**
 * Redis Cache Module
 *
 * Provides caching layer for embeddings to reduce OpenAI API costs
 * Extracted from Genesis app's redis integration
 */

import Redis from 'ioredis'
import type { RedisConfig } from './types.js'

export interface CacheStats {
  hits: number
  misses: number
  hitRate: number
}

export class EmbeddingCache {
  private redis: Redis
  private ttl: number
  private stats: { hits: number; misses: number }

  constructor(config: RedisConfig & { ttl?: number }) {
    this.redis = new Redis({
      host: config.host,
      port: config.port,
      password: config.password,
      db: config.db || 0,
      retryStrategy(times) {
        const delay = Math.min(times * 50, 2000)
        return delay
      },
      maxRetriesPerRequest: 3,
    })

    this.ttl = config.ttl || 86400 // Default 24 hours
    this.stats = { hits: 0, misses: 0 }

    // Handle connection errors gracefully
    this.redis.on('error', (err) => {
      console.error('Redis connection error:', err)
    })
  }

  /**
   * Generate cache key from text using hash
   */
  private getCacheKey(text: string, model: string, dimensions: number): string {
    // Simple hash for cache key
    const hash = Buffer.from(text).toString('base64').slice(0, 32)
    return `embedding:${model}:${dimensions}:${hash}`
  }

  /**
   * Get cached embedding for text
   */
  async get(text: string, model: string, dimensions: number): Promise<number[] | null> {
    try {
      const key = this.getCacheKey(text, model, dimensions)
      const cached = await this.redis.get(key)

      if (cached) {
        this.stats.hits++
        return JSON.parse(cached)
      }

      this.stats.misses++
      return null
    } catch (error) {
      console.error('Cache get error:', error)
      this.stats.misses++
      return null
    }
  }

  /**
   * Set cached embedding for text
   */
  async set(
    text: string,
    embedding: number[],
    model: string,
    dimensions: number
  ): Promise<void> {
    try {
      const key = this.getCacheKey(text, model, dimensions)
      await this.redis.setex(key, this.ttl, JSON.stringify(embedding))
    } catch (error) {
      console.error('Cache set error:', error)
      // Don't throw - caching is optional
    }
  }

  /**
   * Get multiple cached embeddings
   */
  async getMany(
    texts: string[],
    model: string,
    dimensions: number
  ): Promise<Map<string, number[]>> {
    const results = new Map<string, number[]>()

    try {
      const keys = texts.map((text) => this.getCacheKey(text, model, dimensions))
      const values = await this.redis.mget(...keys)

      values.forEach((value, index) => {
        if (value) {
          results.set(texts[index], JSON.parse(value))
          this.stats.hits++
        } else {
          this.stats.misses++
        }
      })
    } catch (error) {
      console.error('Cache getMany error:', error)
      this.stats.misses += texts.length
    }

    return results
  }

  /**
   * Set multiple cached embeddings
   */
  async setMany(
    entries: Array<{ text: string; embedding: number[] }>,
    model: string,
    dimensions: number
  ): Promise<void> {
    try {
      const pipeline = this.redis.pipeline()

      entries.forEach(({ text, embedding }) => {
        const key = this.getCacheKey(text, model, dimensions)
        pipeline.setex(key, this.ttl, JSON.stringify(embedding))
      })

      await pipeline.exec()
    } catch (error) {
      console.error('Cache setMany error:', error)
      // Don't throw - caching is optional
    }
  }

  /**
   * Get cache statistics
   */
  getStats(): CacheStats {
    const total = this.stats.hits + this.stats.misses
    const hitRate = total > 0 ? (this.stats.hits / total) * 100 : 0

    return {
      hits: this.stats.hits,
      misses: this.stats.misses,
      hitRate: parseFloat(hitRate.toFixed(2)),
    }
  }

  /**
   * Reset cache statistics
   */
  resetStats(): void {
    this.stats = { hits: 0, misses: 0 }
  }

  /**
   * Clear all cached embeddings
   */
  async clear(): Promise<void> {
    try {
      const keys = await this.redis.keys('embedding:*')
      if (keys.length > 0) {
        await this.redis.del(...keys)
      }
    } catch (error) {
      console.error('Cache clear error:', error)
      throw error
    }
  }

  /**
   * Close Redis connection
   */
  async close(): Promise<void> {
    await this.redis.quit()
  }

  /**
   * Check if Redis is connected
   */
  isConnected(): boolean {
    return this.redis.status === 'ready'
  }
}
