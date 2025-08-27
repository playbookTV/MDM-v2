import { formatDistanceToNow } from 'date-fns'
import { 
  Play, 
  Pause, 
  Square, 
  RotateCcw, 
  FileText, 
  Clock, 
  AlertTriangle,
  CheckCircle,
  Loader2,
  Database
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { JobProgressChart } from './JobProgressChart'
import { useCancelJob, useRetryJob } from '@/hooks/useJobs'
import type { Job } from '@/types/dataset'

interface JobCardProps {
  job: Job
  onViewLogs?: (job: Job) => void
  onViewDataset?: (job: Job) => void
  className?: string
}

const STATUS_CONFIG = {
  queued: {
    icon: Clock,
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-50 border-yellow-200',
    badge: 'default' as const,
    label: 'Queued'
  },
  running: {
    icon: Loader2,
    color: 'text-blue-500',
    bgColor: 'bg-blue-50 border-blue-200',
    badge: 'default' as const,
    label: 'Running'
  },
  succeeded: {
    icon: CheckCircle,
    color: 'text-green-500',
    bgColor: 'bg-green-50 border-green-200',
    badge: 'secondary' as const,
    label: 'Completed'
  },
  failed: {
    icon: AlertTriangle,
    color: 'text-red-500',
    bgColor: 'bg-red-50 border-red-200',
    badge: 'destructive' as const,
    label: 'Failed'
  },
  skipped: {
    icon: Pause,
    color: 'text-gray-500',
    bgColor: 'bg-gray-50 border-gray-200',
    badge: 'outline' as const,
    label: 'Skipped'
  }
}

const KIND_LABELS = {
  ingest: 'Data Ingestion',
  process: 'AI Processing'
}

export function JobCard({ job, onViewLogs, onViewDataset, className }: JobCardProps) {
  const cancelMutation = useCancelJob()
  const retryMutation = useRetryJob()
  
  const statusConfig = STATUS_CONFIG[job.status]
  const StatusIcon = statusConfig.icon
  const isActive = job.status === 'running' || job.status === 'queued'
  const canCancel = job.status === 'running' || job.status === 'queued'
  const canRetry = job.status === 'failed'

  const handleCancel = async () => {
    if (confirm('Are you sure you want to cancel this job?')) {
      try {
        await cancelMutation.mutateAsync(job.id)
      } catch (error) {
        console.error('Failed to cancel job:', error)
      }
    }
  }

  const handleRetry = async () => {
    try {
      await retryMutation.mutateAsync(job.id)
    } catch (error) {
      console.error('Failed to retry job:', error)
    }
  }

  const getDuration = () => {
    if (!job.started_at) return null
    
    const startTime = new Date(job.started_at)
    const endTime = job.finished_at ? new Date(job.finished_at) : new Date()
    const durationMs = endTime.getTime() - startTime.getTime()
    
    const hours = Math.floor(durationMs / (1000 * 60 * 60))
    const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60))
    const seconds = Math.floor((durationMs % (1000 * 60)) / 1000)
    
    if (hours > 0) {
      return `${hours}h ${minutes}m ${seconds}s`
    } else if (minutes > 0) {
      return `${minutes}m ${seconds}s`
    } else {
      return `${seconds}s`
    }
  }

  return (
    <div className={`border rounded-lg p-6 ${statusConfig.bgColor} ${className}`}>
      {/* Header */}
      <div className="flex items-start justify-between mb-4">
        <div className="flex items-center space-x-3">
          <div className={`p-2 rounded-full bg-background`}>
            <StatusIcon 
              className={`h-5 w-5 ${statusConfig.color} ${
                job.status === 'running' ? 'animate-spin' : ''
              }`} 
            />
          </div>
          
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="font-semibold text-lg">
                {KIND_LABELS[job.kind]}
              </h3>
              <Badge variant={statusConfig.badge}>
                {statusConfig.label}
              </Badge>
            </div>
            
            <div className="flex items-center space-x-2 mt-1 text-sm text-muted-foreground">
              <Database className="h-3 w-3" />
              <span>{job.dataset_name || job.dataset_id}</span>
              <span>•</span>
              <span>Job #{job.id.slice(-8)}</span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onViewLogs?.(job)}
          >
            <FileText className="h-4 w-4 mr-1" />
            Logs
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => onViewDataset?.(job)}
          >
            <Database className="h-4 w-4 mr-1" />
            Dataset
          </Button>
          
          {canCancel && (
            <Button
              variant="destructive"
              size="sm"
              onClick={handleCancel}
              disabled={cancelMutation.isPending}
            >
              <Square className="h-4 w-4 mr-1" />
              Cancel
            </Button>
          )}
          
          {canRetry && (
            <Button
              variant="default"
              size="sm"
              onClick={handleRetry}
              disabled={retryMutation.isPending}
            >
              <RotateCcw className="h-4 w-4 mr-1" />
              Retry
            </Button>
          )}
        </div>
      </div>

      {/* Progress Section */}
      {job.progress && (
        <div className="mb-4">
          <JobProgressChart progress={job.progress} />
        </div>
      )}

      {/* Error Message */}
      {job.status === 'failed' && job.error_message && (
        <div className="mb-4 p-3 bg-destructive/10 border border-destructive/20 rounded-md">
          <div className="flex items-center space-x-2 mb-2">
            <AlertTriangle className="h-4 w-4 text-destructive" />
            <span className="font-medium text-destructive">Error Details</span>
          </div>
          <p className="text-sm text-destructive/80">{job.error_message}</p>
        </div>
      )}

      {/* Footer with Timestamps */}
      <div className="flex items-center justify-between text-xs text-muted-foreground pt-3 border-t border-background">
        <div className="flex items-center space-x-4">
          <span>Created {formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}</span>
          
          {job.started_at && (
            <span>Started {formatDistanceToNow(new Date(job.started_at), { addSuffix: true })}</span>
          )}
          
          {job.finished_at && (
            <span>Finished {formatDistanceToNow(new Date(job.finished_at), { addSuffix: true })}</span>
          )}
        </div>
        
        {getDuration() && (
          <div className="flex items-center space-x-1">
            <Clock className="h-3 w-3" />
            <span>Duration: {getDuration()}</span>
          </div>
        )}
      </div>
    </div>
  )
}