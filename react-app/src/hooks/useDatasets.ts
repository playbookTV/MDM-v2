import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { getMultipleImageDimensions } from '@/lib/image-utils'
import type { 
  Dataset, 
  DatasetCreate, 
  Page, 
  PresignRequest, 
  PresignResponse,
  RegisterScenesRequest,
  RegisterScenesResponse,
  APIError 
} from '@/types/dataset'

const API_BASE = '/api/v1'

// API functions
const fetchDatasets = async (params?: { 
  q?: string
  page?: number
  limit?: number 
}): Promise<Page<Dataset>> => {
  const searchParams = new URLSearchParams()
  if (params?.q) searchParams.set('q', params.q)
  if (params?.page) searchParams.set('page', params.page.toString())
  if (params?.limit) searchParams.set('limit', params.limit.toString())
  
  const response = await fetch(`${API_BASE}/datasets?${searchParams}`)
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

const createDataset = async (dataset: DatasetCreate): Promise<Dataset> => {
  const response = await fetch(`${API_BASE}/datasets`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dataset),
  })
  
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

const getPresignedUrls = async (
  datasetId: string, 
  request: PresignRequest
): Promise<PresignResponse> => {
  const response = await fetch(`${API_BASE}/datasets/${datasetId}/presign`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

const uploadFileToR2 = async (file: File, presignedUrl: string, headers: Record<string, string>) => {
  const response = await fetch(presignedUrl, {
    method: 'PUT',
    headers,
    body: file,
  })
  
  if (!response.ok) {
    throw new Error(`Failed to upload ${file.name}: ${response.statusText}`)
  }
}

const registerScenes = async (
  datasetId: string,
  request: RegisterScenesRequest
): Promise<RegisterScenesResponse> => {
  const response = await fetch(`${API_BASE}/datasets/${datasetId}/register-scenes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  })
  
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

// React Query hooks
export const useDatasets = (params?: { 
  q?: string
  page?: number
  limit?: number 
}) => {
  return useQuery({
    queryKey: ['datasets', params],
    queryFn: () => fetchDatasets(params),
  })
}

export const useCreateDataset = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: createDataset,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
    },
  })
}

export const useUploadDataset = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: async ({
      dataset,
      files
    }: {
      dataset: DatasetCreate
      files: File[]
    }) => {
      console.log(`Starting upload: ${dataset.name} with ${files.length} files`)
      
      // Step 1: Create dataset
      const createdDataset = await createDataset(dataset)
      console.log(`Dataset created: ${createdDataset.id}`)
      
      // Step 2: Get presigned URLs
      const presignRequest: PresignRequest = {
        files: files.map(file => ({
          filename: file.name,
          content_type: file.type,
        }))
      }
      
      const presignResponse = await getPresignedUrls(createdDataset.id, presignRequest)
      console.log(`Got ${presignResponse.uploads.length} presigned URLs`)
      
      // Step 3: Upload files to R2
      const uploadPromises = files.map(async (file, index) => {
        const upload = presignResponse.uploads[index]
        try {
          await uploadFileToR2(file, upload.url, upload.headers)
          console.log(`Uploaded: ${file.name}`)
          return {
            file,
            upload,
            success: true,
          }
        } catch (error) {
          console.error(`Failed to upload ${file.name}:`, error)
          return {
            file,
            upload,
            success: false,
            error: error instanceof Error ? error.message : 'Unknown error'
          }
        }
      })
      
      const uploadResults = await Promise.all(uploadPromises)
      const successfulUploads = uploadResults.filter(result => result.success)
      
      if (successfulUploads.length === 0) {
        throw new Error('No files were uploaded successfully')
      }
      
      // Step 4: Get image dimensions for successful uploads
      const successfulFiles = successfulUploads.map(result => result.file)
      const imageDimensions = await getMultipleImageDimensions(successfulFiles)
      
      // Step 5: Register successful uploads as scenes
      const registerRequest: RegisterScenesRequest = {
        scenes: successfulUploads.map((result, index) => {
          const dimensions = imageDimensions[index]
          return {
            source: result.file.name,
            r2_key_original: result.upload.key,
            width: dimensions?.width || 1920, // fallback for non-images or processing errors
            height: dimensions?.height || 1080, // fallback for non-images or processing errors
          }
        })
      }
      
      const registerResponse = await registerScenes(createdDataset.id, registerRequest)
      console.log(`Registered ${registerResponse.created} scenes`)
      
      return {
        dataset: createdDataset,
        uploadResults,
        registeredScenes: registerResponse,
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
    },
  })
}