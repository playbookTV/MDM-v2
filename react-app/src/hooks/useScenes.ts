import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { 
  Scene,
  SceneObject, 
  Page,
  APIError 
} from '@/types/dataset'

const API_BASE = '/api/v1'

// API functions
const fetchScenes = async (params?: { 
  dataset_id?: string
  review_status?: string
  scene_type?: string
  page?: number
  limit?: number
  include_objects?: boolean
}): Promise<Page<Scene>> => {
  const searchParams = new URLSearchParams()
  if (params?.dataset_id) searchParams.set('dataset_id', params.dataset_id)
  if (params?.review_status) searchParams.set('review_status', params.review_status)
  if (params?.scene_type) searchParams.set('scene_type', params.scene_type)
  if (params?.page) searchParams.set('page', params.page.toString())
  if (params?.limit) searchParams.set('limit', params.limit.toString())
  if (params?.include_objects) searchParams.set('include_objects', 'true')
  
  const response = await fetch(`${API_BASE}/scenes?${searchParams}`)
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

const fetchScene = async (sceneId: string, includeObjects = true): Promise<Scene> => {
  const searchParams = new URLSearchParams()
  if (includeObjects) searchParams.set('include_objects', 'true')
  
  const response = await fetch(`${API_BASE}/scenes/${sceneId}?${searchParams}`)
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

const fetchSceneObjects = async (sceneId: string): Promise<SceneObject[]> => {
  const response = await fetch(`${API_BASE}/scenes/${sceneId}/objects`)
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

const getImageUrl = (sceneId: string, type: 'original' | 'thumbnail' | 'depth' = 'original') => {
  // Use scene ID to get image via backend API
  const baseUrl = '/api/v1/images/scenes'
  return `${baseUrl}/${sceneId}.jpg?type=${type}`
}

// React Query hooks
export const useScenes = (params?: { 
  dataset_id?: string
  review_status?: string
  scene_type?: string
  page?: number
  limit?: number
  include_objects?: boolean
}) => {
  return useQuery({
    queryKey: ['scenes', params],
    queryFn: () => fetchScenes(params),
    staleTime: 30000, // Cache for 30 seconds since scene data doesn't change rapidly
  })
}

export const useScene = (sceneId: string, includeObjects = true) => {
  return useQuery({
    queryKey: ['scene', sceneId, includeObjects],
    queryFn: () => fetchScene(sceneId, includeObjects),
    enabled: !!sceneId,
    staleTime: 60000, // Cache individual scenes for 1 minute
  })
}

export const useSceneObjects = (sceneId: string) => {
  return useQuery({
    queryKey: ['sceneObjects', sceneId],
    queryFn: () => fetchSceneObjects(sceneId),
    enabled: !!sceneId,
    staleTime: 60000,
  })
}

// Pagination hook for smooth scene browsing
export const useScenePagination = (params?: { 
  dataset_id?: string
  review_status?: string
  scene_type?: string
  limit?: number
}) => {
  const { data, isLoading, error } = useScenes({ ...params, limit: params?.limit || 50 })
  
  const scenes = data?.items || []
  const totalPages = data ? Math.ceil(data.total / data.limit) : 0
  const currentPage = data?.page || 1
  
  const getSceneIndex = (sceneId: string) => {
    return scenes.findIndex(scene => scene.id === sceneId)
  }
  
  const getNextScene = (currentSceneId: string): Scene | null => {
    const currentIndex = getSceneIndex(currentSceneId)
    if (currentIndex === -1 || currentIndex >= scenes.length - 1) {
      return null
    }
    return scenes[currentIndex + 1]
  }
  
  const getPreviousScene = (currentSceneId: string): Scene | null => {
    const currentIndex = getSceneIndex(currentSceneId)
    if (currentIndex <= 0) {
      return null
    }
    return scenes[currentIndex - 1]
  }
  
  return {
    scenes,
    totalPages,
    currentPage,
    isLoading,
    error,
    getNextScene,
    getPreviousScene,
    getSceneIndex,
  }
}

// Utility hook for image URLs
export const useSceneImages = (scene: Scene) => {
  return {
    originalUrl: getImageUrl(scene.id, 'original'),
    thumbnailUrl: getImageUrl(scene.id, 'thumbnail'),
    depthUrl: scene.has_depth ? getImageUrl(scene.id, 'depth') : null,
  }
}

// Prefetching hook for smooth navigation
export const useScenePrefetch = () => {
  const queryClient = useQueryClient()
  
  const prefetchScene = (sceneId: string) => {
    queryClient.prefetchQuery({
      queryKey: ['scene', sceneId, true],
      queryFn: () => fetchScene(sceneId, true),
      staleTime: 60000,
    })
  }
  
  const prefetchScenes = (sceneIds: string[]) => {
    sceneIds.forEach(id => prefetchScene(id))
  }
  
  return { prefetchScene, prefetchScenes }
}

// Scene filtering utilities
export const SCENE_TYPES = [
  'bedroom',
  'living_room', 
  'kitchen',
  'bathroom',
  'dining_room',
  'office',
  'outdoor',
  'other'
] as const

export const REVIEW_STATUSES = [
  { value: 'pending', label: 'Pending Review' },
  { value: 'approved', label: 'Approved' },
  { value: 'rejected', label: 'Rejected' },
  { value: 'corrected', label: 'Corrected' },
] as const

export const getReviewStatusColor = (status?: string) => {
  switch (status) {
    case 'approved': return 'text-green-500'
    case 'rejected': return 'text-red-500'
    case 'corrected': return 'text-yellow-500'
    default: return 'text-gray-500'
  }
}

export const getReviewStatusBadge = (status?: string) => {
  switch (status) {
    case 'approved': return 'secondary'
    case 'rejected': return 'destructive'
    case 'corrected': return 'default'
    default: return 'outline'
  }
}