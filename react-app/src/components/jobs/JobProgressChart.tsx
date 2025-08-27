import { useMemo } from 'react'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import type { JobProgress } from '@/types/dataset'

interface JobProgressChartProps {
  progress: JobProgress
  className?: string
}

export function JobProgressChart({ progress, className }: JobProgressChartProps) {
  const progressPercentage = useMemo(() => {
    if (progress.scenes_total === 0) return 0
    return Math.round((progress.scenes_done / progress.scenes_total) * 100)
  }, [progress.scenes_done, progress.scenes_total])

  const processingRate = useMemo(() => {
    return progress.processing_rate ? progress.processing_rate.toFixed(1) : '0.0'
  }, [progress.processing_rate])

  const etaDisplay = useMemo(() => {
    if (!progress.eta_seconds) return 'Unknown'
    
    const hours = Math.floor(progress.eta_seconds / 3600)
    const minutes = Math.floor((progress.eta_seconds % 3600) / 60)
    const seconds = progress.eta_seconds % 60
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`
    } else if (minutes > 0) {
      return `${minutes}m ${seconds}s`
    } else {
      return `${seconds}s`
    }
  }, [progress.eta_seconds])

  const averageConfidence = useMemo(() => {
    return progress.avg_conf ? (progress.avg_conf * 100).toFixed(1) : '0.0'
  }, [progress.avg_conf])

  return (
    <div className={className}>
      {/* Main Progress Bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between text-sm">
          <span className="font-medium">
            {progress.scenes_done.toLocaleString()} / {progress.scenes_total.toLocaleString()} scenes
          </span>
          <span className="text-muted-foreground">{progressPercentage}%</span>
        </div>
        
        <Progress 
          value={progressPercentage} 
          className="h-3"
        />
        
        {progress.current_scene && (
          <p className="text-xs text-muted-foreground truncate">
            Processing: {progress.current_scene}
          </p>
        )}
      </div>

      {/* Progress Stats Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4">
        <div className="bg-muted/50 rounded-md p-3">
          <div className="text-xs text-muted-foreground mb-1">Objects Detected</div>
          <div className="text-lg font-semibold">
            {progress.objects_detected.toLocaleString()}
          </div>
        </div>
        
        <div className="bg-muted/50 rounded-md p-3">
          <div className="text-xs text-muted-foreground mb-1">Avg Confidence</div>
          <div className="text-lg font-semibold">
            {averageConfidence}%
          </div>
        </div>
        
        <div className="bg-muted/50 rounded-md p-3">
          <div className="text-xs text-muted-foreground mb-1">Processing Rate</div>
          <div className="text-lg font-semibold">
            {processingRate} <span className="text-sm font-normal">scenes/min</span>
          </div>
        </div>
        
        <div className="bg-muted/50 rounded-md p-3">
          <div className="text-xs text-muted-foreground mb-1">ETA</div>
          <div className="text-lg font-semibold">
            {etaDisplay}
          </div>
        </div>
      </div>

      {/* Failure Badge */}
      {progress.failures > 0 && (
        <div className="mt-3 flex items-center space-x-2">
          <Badge variant="destructive">
            {progress.failures} failure{progress.failures !== 1 ? 's' : ''}
          </Badge>
          <span className="text-xs text-muted-foreground">
            {((progress.failures / (progress.scenes_done || 1)) * 100).toFixed(1)}% failure rate
          </span>
        </div>
      )}
    </div>
  )
}