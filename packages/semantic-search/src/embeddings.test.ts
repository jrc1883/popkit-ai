/**
 * Tests for EmbeddingsClient
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { EmbeddingsClient } from './embeddings'

// Mock fetch globally
global.fetch = vi.fn()

describe('EmbeddingsClient', () => {
  let client: EmbeddingsClient
  const mockApiKey = 'test-api-key'

  beforeEach(() => {
    client = new EmbeddingsClient({ apiKey: mockApiKey })
    vi.clearAllMocks()
  })

  describe('constructor', () => {
    it('should create client with API key', () => {
      expect(client).toBeInstanceOf(EmbeddingsClient)
    })

    it('should throw error if API key is missing', () => {
      expect(() => new EmbeddingsClient({ apiKey: '' })).toThrow(
        'OpenAI API key is required'
      )
    })

    it('should use default model and dimensions', () => {
      const client = new EmbeddingsClient({ apiKey: mockApiKey })
      expect(client).toBeDefined()
    })

    it('should accept custom model and dimensions', () => {
      const client = new EmbeddingsClient({
        apiKey: mockApiKey,
        model: 'text-embedding-3-large',
        dimensions: 3072,
      })
      expect(client).toBeDefined()
    })
  })

  describe('createEmbedding', () => {
    it('should create embedding for single text', async () => {
      const mockResponse = {
        object: 'list',
        data: [
          {
            object: 'embedding',
            embedding: new Array(1536).fill(0.1),
            index: 0,
          },
        ],
        model: 'text-embedding-3-small',
        usage: {
          prompt_tokens: 10,
          total_tokens: 10,
        },
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await client.createEmbedding('test text')

      expect(global.fetch).toHaveBeenCalledWith(
        'https://api.openai.com/v1/embeddings',
        expect.objectContaining({
          method: 'POST',
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
            Authorization: `Bearer ${mockApiKey}`,
          }),
        })
      )
      expect(result).toEqual(mockResponse)
    })

    it('should create embeddings for multiple texts', async () => {
      const mockResponse = {
        object: 'list',
        data: [
          {
            object: 'embedding',
            embedding: new Array(1536).fill(0.1),
            index: 0,
          },
          {
            object: 'embedding',
            embedding: new Array(1536).fill(0.2),
            index: 1,
          },
        ],
        model: 'text-embedding-3-small',
        usage: {
          prompt_tokens: 20,
          total_tokens: 20,
        },
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await client.createEmbedding(['text 1', 'text 2'])
      expect(result.data).toHaveLength(2)
    })

    it('should handle API errors', async () => {
      const mockError = {
        error: {
          message: 'Invalid API key',
          type: 'invalid_request_error',
        },
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: false,
        json: async () => mockError,
      })

      await expect(client.createEmbedding('test')).rejects.toThrow(
        'OpenAI API error: Invalid API key'
      )
    })
  })

  describe('embedText', () => {
    it('should return embedding array for single text', async () => {
      const mockEmbedding = new Array(1536).fill(0.1)
      const mockResponse = {
        object: 'list',
        data: [
          {
            object: 'embedding',
            embedding: mockEmbedding,
            index: 0,
          },
        ],
        model: 'text-embedding-3-small',
        usage: {
          prompt_tokens: 10,
          total_tokens: 10,
        },
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await client.embedText('test text')
      expect(result).toEqual(mockEmbedding)
    })
  })

  describe('embedBatch', () => {
    it('should return array of embeddings', async () => {
      const mockResponse = {
        object: 'list',
        data: [
          {
            object: 'embedding',
            embedding: new Array(1536).fill(0.1),
            index: 0,
          },
          {
            object: 'embedding',
            embedding: new Array(1536).fill(0.2),
            index: 1,
          },
        ],
        model: 'text-embedding-3-small',
        usage: {
          prompt_tokens: 20,
          total_tokens: 20,
        },
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await client.embedBatch(['text 1', 'text 2'])
      expect(result).toHaveLength(2)
      expect(result[0]).toHaveLength(1536)
      expect(result[1]).toHaveLength(1536)
    })

    it('should sort results by index', async () => {
      const mockResponse = {
        object: 'list',
        data: [
          {
            object: 'embedding',
            embedding: new Array(1536).fill(0.2),
            index: 1,
          },
          {
            object: 'embedding',
            embedding: new Array(1536).fill(0.1),
            index: 0,
          },
        ],
        model: 'text-embedding-3-small',
        usage: {
          prompt_tokens: 20,
          total_tokens: 20,
        },
      }

      ;(global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      })

      const result = await client.embedBatch(['text 1', 'text 2'])
      expect(result[0][0]).toBe(0.1)
      expect(result[1][0]).toBe(0.2)
    })
  })

  describe('estimateCost', () => {
    it('should estimate tokens and cost', () => {
      const texts = [
        'Hello world this is a test',
        'This is another test with more content to estimate',
      ]
      const result = client.estimateCost(texts)

      expect(result.tokens).toBeGreaterThan(0)
      expect(result.cost_usd).toBeGreaterThanOrEqual(0)
      expect(typeof result.cost_usd).toBe('number')
    })

    it('should return zero for empty array', () => {
      const result = client.estimateCost([])
      expect(result.tokens).toBe(0)
      expect(result.cost_usd).toBe(0)
    })
  })

  describe('calculateCost', () => {
    it('should calculate cost from usage', () => {
      const usage = {
        prompt_tokens: 1000,
        total_tokens: 1000,
      }

      const cost = client.calculateCost(usage)
      expect(cost).toBeGreaterThan(0)
      expect(cost).toBe((1000 / 1_000_000) * 0.02)
    })
  })

  describe('embedBatchWithRetry', () => {
    it('should process batch with progress callback', async () => {
      const mockResponse = {
        object: 'list',
        data: [
          {
            object: 'embedding',
            embedding: new Array(1536).fill(0.1),
            index: 0,
          },
        ],
        model: 'text-embedding-3-small',
        usage: {
          prompt_tokens: 10,
          total_tokens: 10,
        },
      }

      ;(global.fetch as any).mockResolvedValue({
        ok: true,
        json: async () => mockResponse,
      })

      const onProgress = vi.fn()
      const result = await client.embedBatchWithRetry(['test'], {
        batchSize: 1,
        onProgress,
      })

      expect(result.successful).toBe(1)
      expect(result.failed).toBe(0)
      expect(result.embeddings).toHaveLength(1)
      expect(onProgress).toHaveBeenCalled()
    })

    it('should retry on failure', async () => {
      ;(global.fetch as any)
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            object: 'list',
            data: [
              {
                object: 'embedding',
                embedding: new Array(1536).fill(0.1),
                index: 0,
              },
            ],
            model: 'text-embedding-3-small',
            usage: {
              prompt_tokens: 10,
              total_tokens: 10,
            },
          }),
        })

      const result = await client.embedBatchWithRetry(['test'], {
        batchSize: 1,
        maxRetries: 3,
      })

      expect(result.successful).toBe(1)
      expect(result.failed).toBe(0)
    })

    it('should mark as failed after max retries', async () => {
      ;(global.fetch as any).mockRejectedValue(new Error('Network error'))

      const result = await client.embedBatchWithRetry(['test'], {
        batchSize: 1,
        maxRetries: 2,
      })

      expect(result.successful).toBe(0)
      expect(result.failed).toBe(1)
      expect(result.embeddings[0]).toEqual([])
    })
  })
})
