export interface Dataset {
  id: string
  name: string
  version: string
  source_url?: string
  license?: string
  notes?: string
  created_at: string
}

export interface DatasetCreate {
  name: string
  version: string
  source_url?: string
  license?: string
  notes?: string
}

export interface Scene {
  id: string
  dataset_id: string
  dataset_name?: string
  source: string
  r2_key_original: string
  r2_key_thumbnail?: string
  r2_key_depth?: string
  width: number
  height: number
  scene_type?: string
  scene_conf?: number
  styles?: StyleClassification[]
  palette?: ColorPalette[]
  has_depth: boolean
  objects_count: number
  objects?: SceneObject[]
  review_status?: ReviewStatus
  review_notes?: string
  reviewed_by?: string
  reviewed_at?: string
  created_at: string
  updated_at?: string
}

export interface SceneObject {
  id: string
  scene_id: string
  label: string
  confidence: number
  bbox: BoundingBox
  r2_key_mask?: string
  material?: string  // Legacy single material
  material_conf?: number  // Legacy material confidence
  materials?: MaterialDetection[]  // Enhanced: multiple materials with confidence
  primary_material?: string  // Enhanced: top material
  material_confidence?: number  // Enhanced: top material confidence
  review_status?: ReviewStatus
  corrected_label?: string
  review_notes?: string
}

export interface MaterialDetection {
  material: string
  confidence: number
}

export interface BoundingBox {
  x: number
  y: number
  width: number
  height: number
}

export type ReviewStatus = 'pending' | 'approved' | 'rejected' | 'corrected'

export interface SceneReview {
  scene_id: string
  reviewer_id: string
  status: ReviewStatus
  corrected_scene_type?: string
  corrected_styles?: StyleClassification[]
  notes?: string
  created_at: string
}

export interface ObjectReview {
  object_id: string
  reviewer_id: string
  status: ReviewStatus
  corrected_label?: string
  corrected_material?: string
  notes?: string
  created_at: string
}

export interface ReviewSession {
  id: string
  reviewer_id: string
  dataset_id?: string
  scenes_reviewed: number
  time_spent_seconds: number
  started_at: string
  ended_at?: string
}

export interface StyleClassification {
  code: string
  conf: number
}

export interface ColorPalette {
  hex: string
  p: number
}

export interface Job {
  id: string
  kind: 'ingest' | 'process'
  status: 'queued' | 'running' | 'succeeded' | 'failed' | 'skipped'
  dataset_id: string
  dataset_name?: string
  started_at?: string
  finished_at?: string
  progress?: JobProgress
  error_message?: string
  error_trace?: string
  created_at: string
  updated_at: string
}

export interface JobProgress {
  scenes_total: number
  scenes_done: number
  objects_detected: number
  avg_conf: number
  failures: number
  current_scene?: string
  eta_seconds?: number
  processing_rate?: number
}

export interface JobCreate {
  kind: 'ingest' | 'process'
  dataset_id: string
  config?: JobConfig
}

export interface JobConfig {
  scene_classifier_threshold?: number
  style_classifier_threshold?: number
  object_detector_threshold?: number
  material_detector_threshold?: number
  force_reprocess?: boolean
}

export interface JobLogEntry {
  timestamp: string
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR'
  message: string
  context?: Record<string, any>
}

export interface JobStats {
  total_jobs: number
  queued_jobs: number
  running_jobs: number
  completed_jobs: number
  failed_jobs: number
  average_processing_time: number
  success_rate: number
}

export interface PresignRequest {
  files: PresignFile[]
}

export interface PresignFile {
  filename: string
  content_type: string
}

export interface PresignResponse {
  uploads: PresignUpload[]
  expires_in_seconds: number
}

export interface PresignUpload {
  filename: string
  key: string
  url: string
  headers: Record<string, string>
}

export interface RegisterScenesRequest {
  scenes: SceneRegistration[]
}

export interface SceneRegistration {
  source: string
  r2_key_original: string
  width: number
  height: number
}

export interface RegisterScenesResponse {
  created: number
  scene_ids: string[]
}

export interface Page<T> {
  items: T[]
  page: number
  limit: number
  total: number
}

export interface APIError {
  error: {
    code: string
    message: string
    trace_id: string
  }
}

// Roboflow API types
export interface ProcessRoboflowRequest {
  roboflow_url: string
  api_key: string
  export_format?: string
  max_images?: number
}

export interface ProcessRoboflowResponse {
  job_id: string
  status: string
}

export interface RoboflowDatasetInfo {
  workspace: string
  project: string
  version: string
  dataset_id: string
  description: string
  tags: string[]
  license: string
  format: string
}