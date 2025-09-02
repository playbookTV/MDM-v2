import { useQuery } from '@tanstack/react-query'
import { useState, useEffect, useCallback } from 'react'
import type { JobLogEntry, APIError } from '@/types/dataset'

const API_BASE = '/api/v1'

// API functions
const fetchJobLogs = async (
  jobId: string, 
  params?: { 
    level?: string
    limit?: number
    offset?: number 
  }
): Promise<{ logs: JobLogEntry[], total: number, has_more: boolean }> => {
  const searchParams = new URLSearchParams()
  if (params?.level) searchParams.set('level', params.level)
  if (params?.limit) searchParams.set('limit', params.limit.toString())
  if (params?.offset) searchParams.set('offset', params.offset.toString())
  
  const response = await fetch(`${API_BASE}/jobs/${jobId}/logs?${searchParams}`)
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

// React Query hooks
export const useJobLogs = (
  jobId: string,
  params?: { 
    level?: string
    limit?: number
    offset?: number
    autoRefresh?: boolean
  }
) => {
  const { autoRefresh = true, ...queryParams } = params || {}
  
  return useQuery({
    queryKey: ['jobLogs', jobId, queryParams],
    queryFn: () => fetchJobLogs(jobId, queryParams),
    enabled: !!jobId,
    refetchInterval: autoRefresh ? 2000 : false, // Refresh logs every 2 seconds
    refetchIntervalInBackground: false,
  })
}

// Custom hook for real-time log streaming with accumulation
export const useJobLogsStream = (jobId: string, options?: {
  maxLogs?: number
  autoScroll?: boolean
  levelFilter?: string[]
}) => {
  const { maxLogs = 1000, autoScroll = true, levelFilter } = options || {}
  const [accumulatedLogs, setAccumulatedLogs] = useState<JobLogEntry[]>([])
  const [lastFetchTime, setLastFetchTime] = useState<string | null>(null)
  
  // Query to fetch new logs since last fetch
  const { data: newLogsData, error, isLoading } = useQuery({
    queryKey: ['jobLogsStream', jobId, lastFetchTime],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (lastFetchTime) {
        params.set('since', lastFetchTime)
      }
      params.set('limit', '100') // Fetch in smaller chunks for streaming
      
      const response = await fetch(`${API_BASE}/jobs/${jobId}/logs?${params}`)
      if (!response.ok) {
        const error: APIError = await response.json()
        throw new Error(error.error.message)
      }
      return response.json() as Promise<{ logs: JobLogEntry[], total: number, has_more: boolean }>
    },
    enabled: !!jobId,
    refetchInterval: 1500, // Fast refresh for real-time feel
    refetchIntervalInBackground: false,
  })

  // Extract logs from the response
  const newLogs = newLogsData?.logs || []

  // Accumulate new logs
  useEffect(() => {
    if (newLogs && newLogs.length > 0) {
      setAccumulatedLogs(prev => {
        // Filter logs by level if specified
        const filteredNewLogs = levelFilter 
          ? newLogs.filter(log => levelFilter.includes(log.level))
          : newLogs

        // Combine with existing logs and remove duplicates by timestamp
        const combined = [...prev, ...filteredNewLogs]
        const unique = combined.filter((log, index, array) => 
          array.findIndex(l => l.timestamp === log.timestamp && l.message === log.message) === index
        )
        
        // Sort by timestamp and limit total logs
        const sorted = unique
          .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
          .slice(-maxLogs)
        
        return sorted
      })
      
      // Update last fetch time to newest log timestamp
      const latestTimestamp = Math.max(
        ...newLogs.map(log => new Date(log.timestamp).getTime())
      )
      setLastFetchTime(new Date(latestTimestamp).toISOString())
    }
  }, [newLogs, maxLogs, levelFilter])

  // Auto scroll functionality
  useEffect(() => {
    if (autoScroll && newLogs && newLogs.length > 0) {
      // Small delay to ensure DOM is updated
      setTimeout(() => {
        const logsContainer = document.querySelector('[data-logs-container]')
        if (logsContainer) {
          logsContainer.scrollTop = logsContainer.scrollHeight
        }
      }, 50)
    }
  }, [autoScroll, newLogs])

  // Utility functions
  const clearLogs = useCallback(() => {
    setAccumulatedLogs([])
    setLastFetchTime(null)
  }, [])

  const downloadLogs = useCallback(() => {
    const logsText = accumulatedLogs
      .map(log => `[${log.timestamp}] ${log.level}: ${log.message}`)
      .join('\n')
    
    const blob = new Blob([logsText], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `job-${jobId}-logs.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }, [accumulatedLogs, jobId])

  const getLogsByLevel = useCallback((level: string) => {
    return accumulatedLogs.filter(log => log.level === level)
  }, [accumulatedLogs])

  const getLogStats = useCallback(() => {
    const stats = {
      total: accumulatedLogs.length,
      debug: 0,
      info: 0,
      warning: 0,
      error: 0,
    }
    
    accumulatedLogs.forEach(log => {
      stats[log.level.toLowerCase() as keyof typeof stats]++
    })
    
    return stats
  }, [accumulatedLogs])

  return {
    logs: accumulatedLogs,
    isLoading,
    error,
    clearLogs,
    downloadLogs,
    getLogsByLevel,
    getLogStats,
    hasNewLogs: newLogs && newLogs.length > 0,
  }
}