import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useEffect } from 'react'
import type { 
  Job, 
  JobCreate, 
  JobStats,
  Page, 
  APIError 
} from '@/types/dataset'

const API_BASE = '/api/v1'

// API functions
const fetchJobs = async (params?: { 
  status?: string
  kind?: string
  dataset_id?: string
  page?: number
  limit?: number 
}): Promise<Page<Job>> => {
  const searchParams = new URLSearchParams()
  if (params?.status) searchParams.set('status', params.status)
  if (params?.kind) searchParams.set('kind', params.kind)
  if (params?.dataset_id) searchParams.set('dataset_id', params.dataset_id)
  if (params?.page) searchParams.set('page', params.page.toString())
  if (params?.limit) searchParams.set('limit', params.limit.toString())
  
  const response = await fetch(`${API_BASE}/jobs?${searchParams}`)
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

const fetchJob = async (jobId: string): Promise<Job> => {
  const response = await fetch(`${API_BASE}/jobs/${jobId}`)
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

const createJob = async (job: JobCreate): Promise<Job> => {
  const response = await fetch(`${API_BASE}/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(job),
  })
  
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

const cancelJob = async (jobId: string): Promise<void> => {
  const response = await fetch(`${API_BASE}/jobs/${jobId}/cancel`, {
    method: 'POST',
  })
  
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
}

const retryJob = async (jobId: string): Promise<Job> => {
  const response = await fetch(`${API_BASE}/jobs/${jobId}/retry`, {
    method: 'POST',
  })
  
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

const fetchJobStats = async (): Promise<JobStats> => {
  const response = await fetch(`${API_BASE}/jobs/stats`)
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

// React Query hooks
export const useJobs = (params?: { 
  status?: string
  kind?: string
  dataset_id?: string
  page?: number
  limit?: number 
}) => {
  const query = useQuery({
    queryKey: ['jobs', params],
    queryFn: () => fetchJobs(params),
    refetchInterval: (data) => {
      // Auto-refresh every 2 seconds if there are running jobs
      const hasRunningJobs = data?.items.some(job => 
        job.status === 'running' || job.status === 'queued'
      )
      return hasRunningJobs ? 2000 : false
    },
  })

  return query
}

export const useJob = (jobId: string) => {
  return useQuery({
    queryKey: ['job', jobId],
    queryFn: () => fetchJob(jobId),
    enabled: !!jobId,
    refetchInterval: (data) => {
      // Auto-refresh every 2 seconds for active jobs
      return data && (data.status === 'running' || data.status === 'queued') ? 2000 : false
    },
  })
}

export const useJobStats = () => {
  return useQuery({
    queryKey: ['jobStats'],
    queryFn: fetchJobStats,
    refetchInterval: 5000, // Refresh stats every 5 seconds
  })
}

export const useCreateJob = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: createJob,
    onSuccess: (newJob) => {
      // Update jobs list
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
      queryClient.invalidateQueries({ queryKey: ['jobStats'] })
      
      // Set the new job data in cache for immediate access
      queryClient.setQueryData(['job', newJob.id], newJob)
      
      console.log(`Job created: ${newJob.id} (${newJob.kind})`)
    },
  })
}

export const useCancelJob = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: cancelJob,
    onSuccess: (_, jobId) => {
      // Invalidate queries to refresh job status
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
      queryClient.invalidateQueries({ queryKey: ['job', jobId] })
      queryClient.invalidateQueries({ queryKey: ['jobStats'] })
      
      console.log(`Job cancelled: ${jobId}`)
    },
  })
}

export const useRetryJob = () => {
  const queryClient = useQueryClient()
  
  return useMutation({
    mutationFn: retryJob,
    onSuccess: (retriedJob) => {
      // Update queries with new job data
      queryClient.invalidateQueries({ queryKey: ['jobs'] })
      queryClient.invalidateQueries({ queryKey: ['jobStats'] })
      queryClient.setQueryData(['job', retriedJob.id], retriedJob)
      
      console.log(`Job retried: ${retriedJob.id}`)
    },
  })
}

// Custom hook for managing real-time job monitoring
export const useJobMonitoring = (enableRealTime: boolean = true) => {
  const queryClient = useQueryClient()

  useEffect(() => {
    if (!enableRealTime) return

    // Set up periodic invalidation for active job monitoring
    const interval = setInterval(() => {
      queryClient.invalidateQueries({ 
        queryKey: ['jobs'],
        refetchType: 'active'
      })
    }, 3000)

    return () => clearInterval(interval)
  }, [enableRealTime, queryClient])

  // Return utility functions for manual refresh
  return {
    refreshJobs: () => queryClient.invalidateQueries({ queryKey: ['jobs'] }),
    refreshJob: (jobId: string) => queryClient.invalidateQueries({ queryKey: ['job', jobId] }),
    refreshStats: () => queryClient.invalidateQueries({ queryKey: ['jobStats'] }),
  }
}