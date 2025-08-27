import { useQuery } from '@tanstack/react-query'
import type { 
  SystemHealth,
  ProcessingMetrics,
  ModelPerformanceMetrics,
  DatasetStats,
  ProcessingTrend,
  SystemMetricsTrend,
  ErrorAnalysis,
  TopPerformingDatasets,
  DashboardSummary,
  StatsQuery,
  TimeRange,
  APIError 
} from '@/types/stats'

const API_BASE = '/api/v1'

// API functions
const fetchSystemHealth = async (): Promise<SystemHealth> => {
  const response = await fetch(`${API_BASE}/stats/system-health`)
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

const fetchProcessingMetrics = async (query: StatsQuery = {}): Promise<ProcessingMetrics> => {
  const searchParams = new URLSearchParams()
  if (query.time_range) searchParams.set('time_range', query.time_range)
  if (query.start_date) searchParams.set('start_date', query.start_date)
  if (query.end_date) searchParams.set('end_date', query.end_date)
  if (query.dataset_ids) searchParams.set('dataset_ids', query.dataset_ids.join(','))

  const response = await fetch(`${API_BASE}/stats/processing-metrics?${searchParams}`)
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

const fetchModelPerformance = async (query: StatsQuery = {}): Promise<ModelPerformanceMetrics[]> => {
  const searchParams = new URLSearchParams()
  if (query.time_range) searchParams.set('time_range', query.time_range)
  if (query.start_date) searchParams.set('start_date', query.start_date)
  if (query.end_date) searchParams.set('end_date', query.end_date)

  const response = await fetch(`${API_BASE}/stats/model-performance?${searchParams}`)
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

const fetchDatasetStats = async (query: StatsQuery = {}): Promise<DatasetStats[]> => {
  const searchParams = new URLSearchParams()
  if (query.dataset_ids) searchParams.set('dataset_ids', query.dataset_ids.join(','))

  const response = await fetch(`${API_BASE}/stats/dataset-stats?${searchParams}`)
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

const fetchProcessingTrends = async (query: StatsQuery = {}): Promise<ProcessingTrend[]> => {
  const searchParams = new URLSearchParams()
  if (query.time_range) searchParams.set('time_range', query.time_range)
  if (query.start_date) searchParams.set('start_date', query.start_date)
  if (query.end_date) searchParams.set('end_date', query.end_date)
  if (query.granularity) searchParams.set('granularity', query.granularity)

  const response = await fetch(`${API_BASE}/stats/processing-trends?${searchParams}`)
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

const fetchSystemTrends = async (query: StatsQuery = {}): Promise<SystemMetricsTrend[]> => {
  const searchParams = new URLSearchParams()
  if (query.time_range) searchParams.set('time_range', query.time_range)
  if (query.granularity) searchParams.set('granularity', query.granularity)

  const response = await fetch(`${API_BASE}/stats/system-trends?${searchParams}`)
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

const fetchErrorAnalysis = async (query: StatsQuery = {}): Promise<ErrorAnalysis[]> => {
  const searchParams = new URLSearchParams()
  if (query.time_range) searchParams.set('time_range', query.time_range)
  if (query.start_date) searchParams.set('start_date', query.start_date)
  if (query.end_date) searchParams.set('end_date', query.end_date)

  const response = await fetch(`${API_BASE}/stats/error-analysis?${searchParams}`)
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

const fetchTopPerformingDatasets = async (query: StatsQuery = {}): Promise<TopPerformingDatasets[]> => {
  const searchParams = new URLSearchParams()
  if (query.time_range) searchParams.set('time_range', query.time_range)
  searchParams.set('limit', '10')

  const response = await fetch(`${API_BASE}/stats/top-datasets?${searchParams}`)
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

const fetchDashboardSummary = async (query: StatsQuery = {}): Promise<DashboardSummary> => {
  const searchParams = new URLSearchParams()
  if (query.time_range) searchParams.set('time_range', query.time_range)
  if (query.start_date) searchParams.set('start_date', query.start_date)
  if (query.end_date) searchParams.set('end_date', query.end_date)

  const response = await fetch(`${API_BASE}/stats/dashboard-summary?${searchParams}`)
  if (!response.ok) {
    const error: APIError = await response.json()
    throw new Error(error.error.message)
  }
  return response.json()
}

// React Query hooks
export const useSystemHealth = () => {
  return useQuery({
    queryKey: ['systemHealth'],
    queryFn: fetchSystemHealth,
    refetchInterval: 5000, // Refresh every 5 seconds for real-time health monitoring
    refetchIntervalInBackground: false,
  })
}

export const useProcessingMetrics = (query: StatsQuery = {}) => {
  return useQuery({
    queryKey: ['processingMetrics', query],
    queryFn: () => fetchProcessingMetrics(query),
    refetchInterval: 10000, // Refresh every 10 seconds
  })
}

export const useModelPerformance = (query: StatsQuery = {}) => {
  return useQuery({
    queryKey: ['modelPerformance', query],
    queryFn: () => fetchModelPerformance(query),
    refetchInterval: 30000, // Refresh every 30 seconds
  })
}

export const useDatasetStats = (query: StatsQuery = {}) => {
  return useQuery({
    queryKey: ['datasetStats', query],
    queryFn: () => fetchDatasetStats(query),
    refetchInterval: 15000, // Refresh every 15 seconds
  })
}

export const useProcessingTrends = (query: StatsQuery = {}) => {
  return useQuery({
    queryKey: ['processingTrends', query],
    queryFn: () => fetchProcessingTrends(query),
    staleTime: 60000, // Cache for 1 minute since trends don't change rapidly
  })
}

export const useSystemTrends = (query: StatsQuery = {}) => {
  return useQuery({
    queryKey: ['systemTrends', query],
    queryFn: () => fetchSystemTrends(query),
    refetchInterval: 10000, // Real-time system monitoring
  })
}

export const useErrorAnalysis = (query: StatsQuery = {}) => {
  return useQuery({
    queryKey: ['errorAnalysis', query],
    queryFn: () => fetchErrorAnalysis(query),
    staleTime: 120000, // Cache for 2 minutes
  })
}

export const useTopPerformingDatasets = (query: StatsQuery = {}) => {
  return useQuery({
    queryKey: ['topPerformingDatasets', query],
    queryFn: () => fetchTopPerformingDatasets(query),
    staleTime: 300000, // Cache for 5 minutes
  })
}

export const useDashboardSummary = (query: StatsQuery = {}) => {
  return useQuery({
    queryKey: ['dashboardSummary', query],
    queryFn: () => fetchDashboardSummary(query),
    refetchInterval: 30000, // Refresh every 30 seconds
  })
}

// Utility hook for coordinated refresh across all dashboard components
export const useDashboardRefresh = () => {
  return {
    refreshAll: () => {
      // Force refresh all dashboard queries
      window.location.reload() // Simple approach for coordinated refresh
    },
    getLastUpdated: () => {
      return new Date().toLocaleTimeString()
    }
  }
}

// Time range utilities
export const TIME_RANGES = [
  { label: 'Last Hour', value: '1h' as TimeRange, hours: 1 },
  { label: 'Last 6 Hours', value: '6h' as TimeRange, hours: 6 },
  { label: 'Last 24 Hours', value: '24h' as TimeRange, hours: 24 },
  { label: 'Last 7 Days', value: '7d' as TimeRange, hours: 168 },
  { label: 'Last 30 Days', value: '30d' as TimeRange, hours: 720 },
] as const

export const getTimeRangeLabel = (timeRange: TimeRange): string => {
  const range = TIME_RANGES.find(r => r.value === timeRange)
  return range?.label || timeRange
}