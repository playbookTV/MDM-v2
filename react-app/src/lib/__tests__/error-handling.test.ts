import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { APIError, ValidationError, NetworkError, apiRequest, withRetry } from '../error-handling'

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('Error Classes', () => {
  it('should create APIError with correct properties', () => {
    const error = new APIError('API failed', 500, 'INTERNAL_ERROR', { details: 'test' })
    
    expect(error.name).toBe('APIError')
    expect(error.message).toBe('API failed')
    expect(error.statusCode).toBe(500)
    expect(error.code).toBe('INTERNAL_ERROR')
    expect(error.context).toEqual({ details: 'test' })
  })

  it('should create ValidationError with correct properties', () => {
    const error = new ValidationError('Invalid input', { field: 'email' })
    
    expect(error.name).toBe('ValidationError')
    expect(error.message).toBe('Invalid input')
    expect(error.statusCode).toBe(400)
    expect(error.code).toBe('VALIDATION_ERROR')
    expect(error.context).toEqual({ field: 'email' })
  })

  it('should create NetworkError with correct properties', () => {
    const error = new NetworkError('Connection failed', { url: '/api/test' })
    
    expect(error.name).toBe('NetworkError')
    expect(error.message).toBe('Connection failed')
    expect(error.statusCode).toBe(0)
    expect(error.code).toBe('NETWORK_ERROR')
    expect(error.context).toEqual({ url: '/api/test' })
  })
})

describe('apiRequest', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.clearAllTimers()
  })

  it('should make successful API request', async () => {
    const mockData = { id: 1, name: 'test' }
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: vi.fn().mockResolvedValueOnce(mockData)
    })

    const result = await apiRequest('/api/test')
    
    expect(result).toEqual(mockData)
    expect(mockFetch).toHaveBeenCalledWith('/api/test', expect.objectContaining({
      signal: expect.any(AbortSignal)
    }))
  })

  it('should throw APIError for HTTP errors', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: 'Not Found',
      json: vi.fn().mockResolvedValueOnce({
        error: { message: 'Resource not found', code: 'NOT_FOUND' }
      })
    })

    await expect(apiRequest('/api/test')).rejects.toThrow(APIError)
  })

  it('should handle timeout', async () => {
    // Mock AbortSignal timeout behavior
    const abortError = new DOMException('The user aborted a request.', 'AbortError')
    mockFetch.mockRejectedValueOnce(abortError)

    await expect(apiRequest('/api/test', { timeout: 100 })).rejects.toThrow(NetworkError)
  })

  it('should handle network errors', async () => {
    mockFetch.mockRejectedValueOnce(new TypeError('Failed to fetch'))

    await expect(apiRequest('/api/test')).rejects.toThrow(NetworkError)
  })
})

describe('withRetry', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  it('should retry failed operations', async () => {
    const mockOperation = vi.fn()
      .mockRejectedValueOnce(new NetworkError('Network failed'))
      .mockRejectedValueOnce(new NetworkError('Network failed'))
      .mockResolvedValueOnce('success')

    const resultPromise = withRetry(mockOperation, { maxAttempts: 3, delayMs: 10 })
    
    // Fast forward through retry delays
    await vi.runAllTimersAsync()
    
    const result = await resultPromise
    
    expect(result).toBe('success')
    expect(mockOperation).toHaveBeenCalledTimes(3)
  }, 10000)

  it('should not retry non-retryable errors', async () => {
    const mockOperation = vi.fn()
      .mockRejectedValueOnce(new ValidationError('Invalid input'))

    await expect(
      withRetry(mockOperation, { maxAttempts: 3 })
    ).rejects.toThrow(ValidationError)
    
    expect(mockOperation).toHaveBeenCalledTimes(1)
  })

  it('should respect maxAttempts limit', async () => {
    const mockOperation = vi.fn()
      .mockRejectedValue(new NetworkError('Always fails'))

    const resultPromise = withRetry(mockOperation, { maxAttempts: 2, delayMs: 10 })
    
    // Fast forward through retry delays
    await vi.runAllTimersAsync()
    
    await expect(resultPromise).rejects.toThrow(NetworkError)
    expect(mockOperation).toHaveBeenCalledTimes(2)
  }, 10000)
})