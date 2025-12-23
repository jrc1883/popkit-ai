/**
 * Tests for EmbeddingCache
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { EmbeddingCache } from './cache'

// Mock ioredis
vi.mock('ioredis', () => {
  return {
    default: class RedisMock {
      private store = new Map<string, { value: string; ttl: number }>()
      public status = 'ready'

      on = vi.fn()

      async get(key: string): Promise<string | null> {
        return this.store.get(key)?.value || null
      }

      async setex(key: string, ttl: number, value: string): Promise<void> {
        this.store.set(key, { value, ttl })
      }

      async mget(...keys: string[]): Promise<(string | null)[]> {
        return keys.map((key) => this.store.get(key)?.value || null)
      }

      pipeline() {
        const ops: Array<{
          command: string
          args: any[]
        }> = []

        return {
          setex: (key: string, ttl: number, value: string) => {
            ops.push({ command: 'setex', args: [key, ttl, value] })
            return this
          },
          exec: async () => {
            for (const op of ops) {
              if (op.command === 'setex') {
                await this.setex(...op.args)
              }
            }
            return ops.map(() => [null, 'OK'])
          },
        }
      }

      async keys(pattern: string): Promise<string[]> {
        if (pattern === 'embedding:*') {
          return Array.from(this.store.keys()).filter((key) =>
            key.startsWith('embedding:')
          )
        }
        return []
      }

      async del(...keys: string[]): Promise<number> {
        let count = 0
        for (const key of keys) {
          if (this.store.delete(key)) {
            count++
          }
        }
        return count
      }

      async quit(): Promise<void> {
        this.store.clear()
      }
    },
  }
})

describe('EmbeddingCache', () => {
  let cache: EmbeddingCache
  const config = {
    host: 'localhost',
    port: 6379,
    ttl: 3600,
  }

  beforeEach(() => {
    cache = new EmbeddingCache(config)
  })

  afterEach(async () => {
    await cache.close()
  })

  describe('constructor', () => {
    it('should create cache instance', () => {
      expect(cache).toBeInstanceOf(EmbeddingCache)
    })

    it('should use default TTL', () => {
      const cache = new EmbeddingCache({
        host: 'localhost',
        port: 6379,
      })
      expect(cache).toBeDefined()
    })
  })

  describe('get/set', () => {
    it('should store and retrieve embedding', async () => {
      const text = 'test text'
      const embedding = [0.1, 0.2, 0.3]
      const model = 'text-embedding-3-small'
      const dimensions = 1536

      await cache.set(text, embedding, model, dimensions)
      const result = await cache.get(text, model, dimensions)

      expect(result).toEqual(embedding)
    })

    it('should return null for non-existent key', async () => {
      const result = await cache.get('nonexistent', 'model', 1536)
      expect(result).toBeNull()
    })

    it('should track cache hits and misses', async () => {
      const text = 'test'
      const embedding = [0.1, 0.2]
      const model = 'test-model'
      const dimensions = 1536

      // Miss
      await cache.get(text, model, dimensions)
      let stats = cache.getStats()
      expect(stats.misses).toBe(1)
      expect(stats.hits).toBe(0)

      // Set
      await cache.set(text, embedding, model, dimensions)

      // Hit
      await cache.get(text, model, dimensions)
      stats = cache.getStats()
      expect(stats.hits).toBe(1)
      expect(stats.misses).toBe(1)
      expect(stats.hitRate).toBe(50)
    })
  })

  describe('getMany/setMany', () => {
    it('should get multiple embeddings', async () => {
      const texts = ['text1', 'text2', 'text3']
      const embeddings = [
        [0.1, 0.2],
        [0.3, 0.4],
        [0.5, 0.6],
      ]
      const model = 'test-model'
      const dimensions = 1536

      // Set some embeddings
      await cache.set(texts[0], embeddings[0], model, dimensions)
      await cache.set(texts[2], embeddings[2], model, dimensions)

      const results = await cache.getMany(texts, model, dimensions)

      expect(results.size).toBe(2)
      expect(results.get(texts[0])).toEqual(embeddings[0])
      expect(results.get(texts[2])).toEqual(embeddings[2])
      expect(results.has(texts[1])).toBe(false)
    })

    it('should set multiple embeddings', async () => {
      const entries = [
        { text: 'text1', embedding: [0.1, 0.2] },
        { text: 'text2', embedding: [0.3, 0.4] },
      ]
      const model = 'test-model'
      const dimensions = 1536

      await cache.setMany(entries, model, dimensions)

      const result1 = await cache.get(entries[0].text, model, dimensions)
      const result2 = await cache.get(entries[1].text, model, dimensions)

      expect(result1).toEqual(entries[0].embedding)
      expect(result2).toEqual(entries[1].embedding)
    })
  })

  describe('stats', () => {
    it('should calculate hit rate correctly', async () => {
      const text = 'test'
      const embedding = [0.1]
      const model = 'model'
      const dimensions = 1536

      await cache.set(text, embedding, model, dimensions)

      // 1 hit, 0 misses
      await cache.get(text, model, dimensions)
      expect(cache.getStats().hitRate).toBe(100)

      // 1 hit, 1 miss
      await cache.get('other', model, dimensions)
      expect(cache.getStats().hitRate).toBe(50)

      // 2 hits, 1 miss
      await cache.get(text, model, dimensions)
      expect(cache.getStats().hitRate).toBe(66.67)
    })

    it('should reset stats', async () => {
      await cache.get('test', 'model', 1536)
      expect(cache.getStats().misses).toBe(1)

      cache.resetStats()
      const stats = cache.getStats()
      expect(stats.hits).toBe(0)
      expect(stats.misses).toBe(0)
      expect(stats.hitRate).toBe(0)
    })
  })

  describe('clear', () => {
    it('should clear all embeddings', async () => {
      const model = 'model'
      const dimensions = 1536

      await cache.set('text1', [0.1], model, dimensions)
      await cache.set('text2', [0.2], model, dimensions)

      await cache.clear()

      const result1 = await cache.get('text1', model, dimensions)
      const result2 = await cache.get('text2', model, dimensions)

      expect(result1).toBeNull()
      expect(result2).toBeNull()
    })
  })

  describe('isConnected', () => {
    it('should return connection status', () => {
      expect(cache.isConnected()).toBe(true)
    })
  })
})
