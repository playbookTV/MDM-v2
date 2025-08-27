/**
 * Utility functions for image processing
 */

export interface ImageDimensions {
  width: number
  height: number
}

/**
 * Get image dimensions from a File object
 */
export const getImageDimensions = (file: File): Promise<ImageDimensions> => {
  return new Promise((resolve, reject) => {
    if (!file.type.startsWith('image/')) {
      reject(new Error('File is not an image'))
      return
    }

    const img = new Image()
    const url = URL.createObjectURL(file)

    img.onload = () => {
      URL.revokeObjectURL(url)
      resolve({
        width: img.naturalWidth,
        height: img.naturalHeight
      })
    }

    img.onerror = () => {
      URL.revokeObjectURL(url)
      reject(new Error('Failed to load image'))
    }

    img.src = url
  })
}

/**
 * Get dimensions for multiple image files
 */
export const getMultipleImageDimensions = async (
  files: File[]
): Promise<(ImageDimensions | null)[]> => {
  const dimensionPromises = files.map(async (file) => {
    try {
      return await getImageDimensions(file)
    } catch (error) {
      console.warn(`Failed to get dimensions for ${file.name}:`, error)
      return null
    }
  })

  return Promise.all(dimensionPromises)
}