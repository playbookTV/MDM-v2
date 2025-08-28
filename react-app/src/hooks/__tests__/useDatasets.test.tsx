import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import React, { ReactNode } from 'react'
import { useDatasets, useCreateDataset, useUploadDataset } from '../useDatasets'
import { mockFetchResponse, mockFetchError, createMockDataset } from '@/test/utils'

// Mock the image utils
vi.mock('@/lib/image-utils', () => ({
  getMultipleImageDimensions: vi.fn(),
}))

// Mock the error handling
vi.mock('@/lib/error-handling', () => ({
  apiRequest: vi.fn(),
  withRetry: vi.fn(),
  ValidationError: class ValidationError extends Error {
    constructor(message: string) {
      super(message)
      this.name = 'ValidationError'
    }
  },
}))

const mockApiRequest = vi.mocked(await import('@/lib/error-handling')).apiRequest
const mockWithRetry = vi.mocked(await import('@/lib/error-handling')).withRetry
const mockGetMultipleImageDimensions = vi.mocked(await import('@/lib/image-utils')).getMultipleImageDimensions

describe('useDatasets hook', () => {
  let queryClient: QueryClient

  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    vi.clearAllMocks()
  })

  describe('useDatasets', () => {
    it('should fetch datasets successfully', async () => {
      const mockDatasets = {
        items: [createMockDataset()],
        total: 1,
        page: 1,
        limit: 10,
        pages: 1,
      }

      mockWithRetry.mockResolvedValueOnce(mockDatasets)

      const { result } = renderHook(() => useDatasets(), { wrapper })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
        expect(result.current.data).toEqual(mockDatasets)
      })
    })

    it('should handle fetch error', async () => {
      mockWithRetry.mockRejectedValueOnce(new Error('Network error'))

      const { result } = renderHook(() => useDatasets(), { wrapper })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
        expect(result.current.error).toBeInstanceOf(Error)
      })
    })

    it('should pass query parameters correctly', async () => {
      const params = { q: 'test', page: 2, limit: 20 }
      mockWithRetry.mockResolvedValueOnce({ items: [], total: 0, page: 2, limit: 20, pages: 0 })

      renderHook(() => useDatasets(params), { wrapper })

      await waitFor(() => {
        expect(mockWithRetry).toHaveBeenCalledWith(expect.any(Function))
      })
    })
  })

  describe('useCreateDataset', () => {
    it('should create dataset successfully', async () => {
      const newDataset = { name: 'New Dataset', description: 'Test dataset' }
      const createdDataset = createMockDataset(newDataset)

      mockApiRequest.mockResolvedValueOnce(createdDataset)

      const { result } = renderHook(() => useCreateDataset(), { wrapper })

      result.current.mutate(newDataset)

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
        expect(result.current.data).toEqual(createdDataset)
      })
    })

    it('should validate dataset name', async () => {
      const { result } = renderHook(() => useCreateDataset(), { wrapper })

      result.current.mutate({ name: '', description: 'Test' })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
        expect(result.current.error?.message).toBe('Dataset name is required')
      })
    })
  })

  describe('useUploadDataset', () => {
    beforeEach(() => {
      // Mock successful API calls
      mockApiRequest.mockResolvedValue({})
      mockWithRetry.mockResolvedValue(undefined)
      mockGetMultipleImageDimensions.mockResolvedValue([
        { width: 1920, height: 1080 },
        { width: 800, height: 600 },
      ])
    })

    it('should upload dataset with files successfully', async () => {
      const dataset = { name: 'Upload Dataset', description: 'Test upload' }
      const files = [
        new File([''], 'image1.jpg', { type: 'image/jpeg' }),
        new File([''], 'image2.jpg', { type: 'image/jpeg' }),
      ]

      const createdDataset = createMockDataset(dataset)
      const presignResponse = {
        uploads: [
          { key: 'image1.jpg', url: 'https://upload1.com', headers: {} },
          { key: 'image2.jpg', url: 'https://upload2.com', headers: {} },
        ]
      }
      const registerResponse = { created: 2 }

      // Mock the sequential API calls
      mockApiRequest
        .mockResolvedValueOnce(createdDataset) // create dataset
        .mockResolvedValueOnce(presignResponse) // get presigned URLs
        .mockResolvedValueOnce(registerResponse) // register scenes

      const { result } = renderHook(() => useUploadDataset(), { wrapper })

      result.current.mutate({ dataset, files })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
        expect(result.current.data?.dataset).toEqual(createdDataset)
        expect(result.current.data?.registeredScenes).toEqual(registerResponse)
      })

      // Verify all API calls were made
      expect(mockApiRequest).toHaveBeenCalledTimes(3)
      expect(mockWithRetry).toHaveBeenCalledTimes(2) // 2 file uploads
      expect(mockGetMultipleImageDimensions).toHaveBeenCalledWith(files)
    })

    it('should handle upload failures gracefully', async () => {
      const dataset = { name: 'Upload Dataset', description: 'Test upload' }
      const files = [
        new File([''], 'image1.jpg', { type: 'image/jpeg' }),
        new File([''], 'image2.jpg', { type: 'image/jpeg' }),
      ]

      const createdDataset = createMockDataset(dataset)
      const presignResponse = {
        uploads: [
          { key: 'image1.jpg', url: 'https://upload1.com', headers: {} },
          { key: 'image2.jpg', url: 'https://upload2.com', headers: {} },
        ]
      }

      mockApiRequest
        .mockResolvedValueOnce(createdDataset) // create dataset
        .mockResolvedValueOnce(presignResponse) // get presigned URLs

      // Mock one successful upload and one failure
      mockWithRetry
        .mockResolvedValueOnce(undefined) // first upload succeeds
        .mockRejectedValueOnce(new Error('Upload failed')) // second upload fails

      const { result } = renderHook(() => useUploadDataset(), { wrapper })

      result.current.mutate({ dataset, files })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
        // Should still register the successful upload
        expect(mockApiRequest).toHaveBeenCalledTimes(3) // create + presign + register
      })
    })

    it('should handle zero successful uploads', async () => {
      const dataset = { name: 'Upload Dataset', description: 'Test upload' }
      const files = [new File([''], 'image1.jpg', { type: 'image/jpeg' })]

      const createdDataset = createMockDataset(dataset)
      const presignResponse = {
        uploads: [{ key: 'image1.jpg', url: 'https://upload1.com', headers: {} }]
      }

      mockApiRequest
        .mockResolvedValueOnce(createdDataset)
        .mockResolvedValueOnce(presignResponse)

      // Mock upload failure
      mockWithRetry.mockRejectedValueOnce(new Error('Upload failed'))

      const { result } = renderHook(() => useUploadDataset(), { wrapper })

      result.current.mutate({ dataset, files })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
        expect(result.current.error?.message).toBe('No files were uploaded successfully')
      })
    })

    it('should use fallback dimensions for failed image processing', async () => {
      const dataset = { name: 'Upload Dataset', description: 'Test upload' }
      const files = [new File([''], 'image1.jpg', { type: 'image/jpeg' })]

      // Mock failed image dimension detection
      mockGetMultipleImageDimensions.mockResolvedValue([null])

      const createdDataset = createMockDataset(dataset)
      const presignResponse = {
        uploads: [{ key: 'image1.jpg', url: 'https://upload1.com', headers: {} }]
      }
      const registerResponse = { created: 1 }

      mockApiRequest
        .mockResolvedValueOnce(createdDataset)
        .mockResolvedValueOnce(presignResponse)
        .mockResolvedValueOnce(registerResponse)

      const { result } = renderHook(() => useUploadDataset(), { wrapper })

      result.current.mutate({ dataset, files })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      // Verify fallback dimensions were used (1920x1080)
      const registerCall = mockApiRequest.mock.calls[2][1]
      const requestBody = JSON.parse(registerCall.body)
      expect(requestBody.scenes[0].width).toBe(1920)
      expect(requestBody.scenes[0].height).toBe(1080)
    })
  })
})