import { describe, it, expect, vi, beforeEach } from 'vitest'
import { getImageDimensions, getMultipleImageDimensions } from '../image-utils'

// Mock Image constructor
const mockImage = {
  onload: null as (() => void) | null,
  onerror: null as (() => void) | null,
  src: '',
  naturalWidth: 0,
  naturalHeight: 0,
}

global.Image = vi.fn(() => mockImage) as any

// Mock URL methods
global.URL.createObjectURL = vi.fn(() => 'blob:mock-url')
global.URL.revokeObjectURL = vi.fn()

describe('image-utils', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Reset mock image properties
    mockImage.onload = null
    mockImage.onerror = null
    mockImage.src = ''
    mockImage.naturalWidth = 0
    mockImage.naturalHeight = 0
  })

  describe('getImageDimensions', () => {
    it('should resolve with image dimensions', async () => {
      const mockFile = new File([''], 'test.jpg', { type: 'image/jpeg' })
      
      const dimensionsPromise = getImageDimensions(mockFile)
      
      // Simulate image loading
      mockImage.naturalWidth = 1920
      mockImage.naturalHeight = 1080
      mockImage.onload?.()
      
      const dimensions = await dimensionsPromise
      
      expect(dimensions).toEqual({ width: 1920, height: 1080 })
      expect(global.URL.createObjectURL).toHaveBeenCalledWith(mockFile)
      expect(global.URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-url')
    })

    it('should reject for non-image files', async () => {
      const mockFile = new File([''], 'test.txt', { type: 'text/plain' })
      
      await expect(getImageDimensions(mockFile)).rejects.toThrow('File is not an image')
    })

    it('should reject when image fails to load', async () => {
      const mockFile = new File([''], 'test.jpg', { type: 'image/jpeg' })
      
      const dimensionsPromise = getImageDimensions(mockFile)
      
      // Simulate image load error
      mockImage.onerror?.()
      
      await expect(dimensionsPromise).rejects.toThrow('Failed to load image')
      expect(global.URL.revokeObjectURL).toHaveBeenCalledWith('blob:mock-url')
    })
  })

  describe('getMultipleImageDimensions', () => {
    it('should handle multiple image files', async () => {
      const files = [
        new File([''], 'test1.jpg', { type: 'image/jpeg' }),
        new File([''], 'test2.png', { type: 'image/png' }),
      ]
      
      // Mock successful dimension detection for both files
      const dimensionsPromise1 = getImageDimensions(files[0])
      const dimensionsPromise2 = getImageDimensions(files[1])
      
      // Simulate first image loading
      mockImage.naturalWidth = 1920
      mockImage.naturalHeight = 1080
      mockImage.onload?.()
      
      setTimeout(() => {
        // Simulate second image loading
        mockImage.naturalWidth = 800
        mockImage.naturalHeight = 600
        mockImage.onload?.()
      }, 10)
      
      const results = await getMultipleImageDimensions(files)
      
      expect(results).toEqual([
        { width: 1920, height: 1080 },
        { width: 800, height: 600 },
      ])
    })

    it('should handle failures gracefully', async () => {
      const files = [
        new File([''], 'test1.jpg', { type: 'image/jpeg' }),
        new File([''], 'test2.txt', { type: 'text/plain' }),
      ]
      
      const results = await getMultipleImageDimensions(files)
      
      expect(results).toEqual([
        expect.objectContaining({ width: expect.any(Number), height: expect.any(Number) }),
        null, // Should be null for non-image file
      ])
    })

    it('should handle empty file array', async () => {
      const results = await getMultipleImageDimensions([])
      expect(results).toEqual([])
    })
  })
})