import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import type { 
  SceneReview,
  ObjectReview,
  ReviewSession,
  ReviewStatus,
  StyleClassification,
  APIError 
} from '@/types/dataset'

const API_BASE = '/api/v1'

// API functions
const submitSceneReview = async (review: {
  scene_id: string
  status: ReviewStatus
  corrected_scene_type?: string
  corrected_styles?: StyleClassification[]
  notes?: string
}): Promise<SceneReview> => {
  const response = await fetch(`${API_BASE}/reviews/scenes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(review),
  })
  
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

const submitObjectReview = async (review: {
  object_id: string
  status: ReviewStatus
  corrected_label?: string
  corrected_material?: string
  notes?: string
}): Promise<ObjectReview> => {
  const response = await fetch(`${API_BASE}/reviews/objects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(review),
  })
  
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

const submitBatchReviews = async (reviews: {
  scene_reviews?: Array<{
    scene_id: string
    status: ReviewStatus
    notes?: string
  }>
  object_reviews?: Array<{
    object_id: string
    status: ReviewStatus
    notes?: string
  }>
}): Promise<{ scenes_updated: number, objects_updated: number }> => {
  const response = await fetch(`${API_BASE}/reviews/batch`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(reviews),
  })
  
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

const startReviewSession = async (params: {
  dataset_id?: string
}): Promise<ReviewSession> => {
  const response = await fetch(`${API_BASE}/reviews/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  })
  
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

const endReviewSession = async (sessionId: string): Promise<ReviewSession> => {
  const response = await fetch(`${API_BASE}/reviews/sessions/${sessionId}/end`, {
    method: 'POST',
  })
  
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

const fetchReviewStats = async (params?: {
  dataset_id?: string
  reviewer_id?: string
  time_range?: string
}): Promise<{
  total_scenes: number
  reviewed_scenes: number
  pending_scenes: number
  approved_scenes: number
  rejected_scenes: number
  corrected_scenes: number
  review_rate: number
  avg_time_per_scene: number
}> => {
  const searchParams = new URLSearchParams()
  if (params?.dataset_id) searchParams.set('dataset_id', params.dataset_id)
  if (params?.reviewer_id) searchParams.set('reviewer_id', params.reviewer_id)
  if (params?.time_range) searchParams.set('time_range', params.time_range)
  
  const response = await fetch(`${API_BASE}/reviews/stats?${searchParams}`)
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

// React Query hooks
export const useSubmitSceneReview = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: submitSceneReview,
    onSuccess: (_, variables) => {
      // Invalidate and refetch scene data
      queryClient.invalidateQueries({ queryKey: ['scene', variables.scene_id] })
      queryClient.invalidateQueries({ queryKey: ['scenes'] })
      queryClient.invalidateQueries({ queryKey: ['reviewStats'] })
      
      console.log(`Scene review submitted: ${variables.scene_id} → ${variables.status}`)
    },
  })
}

export const useSubmitObjectReview = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: submitObjectReview,
    onSuccess: (_, variables) => {
      // Invalidate scene data to refresh object reviews
      queryClient.invalidateQueries({ queryKey: ['sceneObjects'] })
      queryClient.invalidateQueries({ queryKey: ['scenes'] })
      queryClient.invalidateQueries({ queryKey: ['reviewStats'] })
      
      console.log(`Object review submitted: ${variables.object_id} → ${variables.status}`)
    },
  })
}

export const useSubmitBatchReviews = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: submitBatchReviews,
    onSuccess: (result) => {
      // Invalidate all scene and review data
      queryClient.invalidateQueries({ queryKey: ['scenes'] })
      queryClient.invalidateQueries({ queryKey: ['reviewStats'] })
      
      console.log(`Batch reviews submitted: ${result.scenes_updated} scenes, ${result.objects_updated} objects`)
    },
  })
}

export const useReviewSession = () => {
  const queryClient = useQueryClient()
  
  const startSession = useMutation({
    mutationFn: startReviewSession,
    onSuccess: (session) => {
      // Store session in cache
      queryClient.setQueryData(['reviewSession'], session)
      console.log(`Review session started: ${session.id}`)
    },
  })
  
  const endSession = useMutation({
    mutationFn: endReviewSession,
    onSuccess: (session) => {
      // Update session in cache
      queryClient.setQueryData(['reviewSession'], session)
      queryClient.invalidateQueries({ queryKey: ['reviewStats'] })
      console.log(`Review session ended: ${session.id}`)
    },
  })
  
  return { startSession, endSession }
}

export const useReviewStats = (params?: {
  dataset_id?: string
  reviewer_id?: string
  time_range?: string
}) => {
  return useQuery({
    queryKey: ['reviewStats', params],
    queryFn: () => fetchReviewStats(params),
    refetchInterval: 30000, // Refresh every 30 seconds
  })
}

// Custom hook for managing review workflow
export const useReviewWorkflow = (sceneId?: string) => {
  const submitSceneReview = useSubmitSceneReview()
  const submitObjectReview = useSubmitObjectReview()
  
  const approveScene = (notes?: string) => {
    if (!sceneId) return
    return submitSceneReview.mutateAsync({
      scene_id: sceneId,
      status: 'approved',
      notes,
    })
  }
  
  const rejectScene = (notes?: string) => {
    if (!sceneId) return
    return submitSceneReview.mutateAsync({
      scene_id: sceneId,
      status: 'rejected',
      notes,
    })
  }
  
  const correctScene = (corrections: {
    scene_type?: string
    styles?: StyleClassification[]
    notes?: string
  }) => {
    if (!sceneId) return
    return submitSceneReview.mutateAsync({
      scene_id: sceneId,
      status: 'corrected',
      corrected_scene_type: corrections.scene_type,
      corrected_styles: corrections.styles,
      notes: corrections.notes,
    })
  }
  
  const approveObject = (objectId: string, notes?: string) => {
    return submitObjectReview.mutateAsync({
      object_id: objectId,
      status: 'approved',
      notes,
    })
  }
  
  const rejectObject = (objectId: string, notes?: string) => {
    return submitObjectReview.mutateAsync({
      object_id: objectId,
      status: 'rejected',
      notes,
    })
  }
  
  const correctObject = (objectId: string, corrections: {
    label?: string
    material?: string
    notes?: string
  }) => {
    return submitObjectReview.mutateAsync({
      object_id: objectId,
      status: 'corrected',
      corrected_label: corrections.label,
      corrected_material: corrections.material,
      notes: corrections.notes,
    })
  }
  
  return {
    approveScene,
    rejectScene,
    correctScene,
    approveObject,
    rejectObject,
    correctObject,
    isSubmitting: submitSceneReview.isPending || submitObjectReview.isPending,
  }
}

// Keyboard shortcuts for review workflow
export const useReviewKeyboard = (callbacks: {
  onApprove?: () => void
  onReject?: () => void
  onNext?: () => void
  onPrevious?: () => void
  onEscape?: () => void
}) => {
  const handleKeyPress = (event: KeyboardEvent) => {
    // Ignore if user is typing in an input
    if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
      return
    }
    
    switch (event.key) {
      case 'a':
      case 'A':
        event.preventDefault()
        callbacks.onApprove?.()
        break
      case 'r':
      case 'R':
        event.preventDefault()
        callbacks.onReject?.()
        break
      case 'ArrowRight':
      case ' ': // Spacebar
        event.preventDefault()
        callbacks.onNext?.()
        break
      case 'ArrowLeft':
        event.preventDefault()
        callbacks.onPrevious?.()
        break
      case 'Escape':
        event.preventDefault()
        callbacks.onEscape?.()
        break
    }
  }
  
  return { handleKeyPress }
}