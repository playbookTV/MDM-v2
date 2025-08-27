export interface SystemHealth {
  cpu_usage_percent: number
  memory_usage_percent: number
  disk_usage_percent: number
  queue_depth: number
  active_workers: number
  processing_rate_per_minute: number
  uptime_seconds: number
  last_updated: string
}

export interface ProcessingMetrics {
  period_start: string
  period_end: string
  jobs_completed: number
  jobs_failed: number
  jobs_cancelled: number
  scenes_processed: number
  objects_detected: number
  average_processing_time_seconds: number
  success_rate: number
}

export interface ModelPerformanceMetrics {
  model_name: string
  model_type: 'scene_classifier' | 'style_classifier' | 'object_detector' | 'material_detector'
  total_predictions: number
  average_confidence: number
  confidence_distribution: ConfidenceBucket[]
  accuracy_by_class?: ClassAccuracy[]
  last_updated: string
}

export interface ConfidenceBucket {
  min_confidence: number
  max_confidence: number
  count: number
  percentage: number
}

export interface ClassAccuracy {
  class_name: string
  precision: number
  recall: number
  f1_score: number
  support: number
}

export interface DatasetStats {
  dataset_id: string
  dataset_name: string
  total_scenes: number
  processed_scenes: number
  failed_scenes: number
  processing_progress: number
  objects_detected: number
  unique_object_types: number
  scene_types: SceneTypeBreakdown[]
  styles: StyleBreakdown[]
  average_confidence: number
  last_processed: string
}

export interface SceneTypeBreakdown {
  scene_type: string
  count: number
  percentage: number
  average_confidence: number
}

export interface StyleBreakdown {
  style_code: string
  style_name: string
  count: number
  percentage: number
  average_confidence: number
}

export interface TimeSeriesPoint {
  timestamp: string
  value: number
  label?: string
}

export interface ProcessingTrend {
  date: string
  jobs_completed: number
  jobs_failed: number
  success_rate: number
  processing_rate: number
  average_confidence: number
}

export interface SystemMetricsTrend {
  timestamp: string
  cpu_usage: number
  memory_usage: number
  queue_depth: number
  processing_rate: number
}

export interface ErrorAnalysis {
  error_type: string
  error_message: string
  occurrence_count: number
  first_seen: string
  last_seen: string
  affected_datasets: string[]
  resolution_suggestions?: string[]
}

export interface TopPerformingDatasets {
  dataset_id: string
  dataset_name: string
  success_rate: number
  processing_speed: number
  quality_score: number
  scenes_processed: number
}

export type TimeRange = 
  | '1h' 
  | '6h' 
  | '24h' 
  | '7d' 
  | '30d' 
  | 'custom'

export interface TimeRangeConfig {
  label: string
  value: TimeRange
  hours: number
}

export interface StatsQuery {
  time_range?: TimeRange
  start_date?: string
  end_date?: string
  dataset_ids?: string[]
  granularity?: 'minute' | 'hour' | 'day'
}

export interface DashboardSummary {
  system_health: SystemHealth
  processing_metrics: ProcessingMetrics
  model_performance: ModelPerformanceMetrics[]
  dataset_stats: DatasetStats[]
  recent_trends: ProcessingTrend[]
  error_analysis: ErrorAnalysis[]
  top_datasets: TopPerformingDatasets[]
  generated_at: string
}