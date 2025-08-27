import { 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertTriangle, 
  Target, 
  TrendingUp,
  User,
  Calendar,
  Timer
} from 'lucide-react'
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { useReviewStats } from '@/hooks/useReviews'

interface ReviewProgressProps {
  datasetId?: string
  reviewerId?: string
  className?: string
}

export function ReviewProgress({ datasetId, reviewerId, className }: ReviewProgressProps) {
  const { data: stats, isLoading, error } = useReviewStats({
    dataset_id: datasetId,
    reviewer_id: reviewerId,
    time_range: '24h'
  })

  if (error) {
    return (
      <div className={`bg-card border rounded-lg p-6 ${className}`}>
        <div className="flex items-center space-x-2 mb-4">
          <AlertTriangle className="h-5 w-5 text-destructive" />
          <h3 className="text-lg font-semibold">Review Progress</h3>
          <Badge variant="destructive">Error</Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          Unable to load review progress
        </p>
      </div>
    )
  }

  if (isLoading || !stats) {
    return (
      <div className={`bg-card border rounded-lg p-6 ${className}`}>
        <div className="flex items-center space-x-2 mb-4">
          <Target className="h-5 w-5 animate-pulse" />
          <h3 className="text-lg font-semibold">Review Progress</h3>
        </div>
        <div className="space-y-4">
          {Array.from({ length: 4 }, (_, i) => (
            <div key={i} className="space-y-2">
              <div className="h-4 bg-muted animate-pulse rounded" />
              <div className="h-2 bg-muted animate-pulse rounded" />
            </div>
          ))}
        </div>
      </div>
    )
  }

  const completionPercentage = stats.total_scenes > 0 
    ? (stats.reviewed_scenes / stats.total_scenes) * 100 
    : 0

  const approvalRate = stats.reviewed_scenes > 0
    ? (stats.approved_scenes / stats.reviewed_scenes) * 100
    : 0

  const formatTime = (seconds: number) => {
    if (seconds < 60) {
      return `${seconds.toFixed(0)}s`
    } else if (seconds < 3600) {
      return `${(seconds / 60).toFixed(1)}m`
    } else {
      return `${(seconds / 3600).toFixed(1)}h`
    }
  }

  return (
    <div className={`bg-card border rounded-lg p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center space-x-2 mb-6">
        <Target className="h-5 w-5" />
        <h3 className="text-lg font-semibold">Review Progress</h3>
        <Badge variant="outline">
          {stats.reviewed_scenes} / {stats.total_scenes} scenes
        </Badge>
      </div>

      {/* Overall Progress Bar */}
      <div className="space-y-2 mb-6">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium">Completion Progress</span>
          <span className="text-sm text-muted-foreground">
            {completionPercentage.toFixed(1)}%
          </span>
        </div>
        <Progress value={completionPercentage} className="h-3" />
        <div className="text-xs text-muted-foreground">
          {stats.reviewed_scenes} of {stats.total_scenes} scenes reviewed
        </div>
      </div>

      {/* Review Status Breakdown */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="text-center p-3 bg-muted/50 rounded-md">
          <div className="flex items-center justify-center mb-2">
            <Clock className="h-4 w-4 text-gray-500" />
          </div>
          <div className="text-xl font-bold text-gray-600">
            {stats.pending_scenes}
          </div>
          <div className="text-xs text-muted-foreground">Pending</div>
        </div>
        
        <div className="text-center p-3 bg-muted/50 rounded-md">
          <div className="flex items-center justify-center mb-2">
            <CheckCircle className="h-4 w-4 text-green-500" />
          </div>
          <div className="text-xl font-bold text-green-600">
            {stats.approved_scenes}
          </div>
          <div className="text-xs text-muted-foreground">Approved</div>
        </div>
        
        <div className="text-center p-3 bg-muted/50 rounded-md">
          <div className="flex items-center justify-center mb-2">
            <XCircle className="h-4 w-4 text-red-500" />
          </div>
          <div className="text-xl font-bold text-red-600">
            {stats.rejected_scenes}
          </div>
          <div className="text-xs text-muted-foreground">Rejected</div>
        </div>
        
        <div className="text-center p-3 bg-muted/50 rounded-md">
          <div className="flex items-center justify-center mb-2">
            <AlertTriangle className="h-4 w-4 text-yellow-500" />
          </div>
          <div className="text-xl font-bold text-yellow-600">
            {stats.corrected_scenes}
          </div>
          <div className="text-xs text-muted-foreground">Corrected</div>
        </div>
      </div>

      {/* Review Quality Metrics */}
      <div className="space-y-4 mb-6">
        <h4 className="text-sm font-medium">Review Quality</h4>
        
        <div className="space-y-3">
          {/* Approval Rate */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <TrendingUp className="h-4 w-4 text-green-500" />
              <span className="text-sm">Approval Rate</span>
            </div>
            <div className="flex items-center space-x-2">
              <div className="text-sm font-medium">
                {approvalRate.toFixed(1)}%
              </div>
              <div className="w-16 h-2 bg-muted rounded-full overflow-hidden">
                <div 
                  className="h-full bg-green-500 transition-all"
                  style={{ width: `${approvalRate}%` }}
                />
              </div>
            </div>
          </div>

          {/* Review Rate */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Timer className="h-4 w-4 text-blue-500" />
              <span className="text-sm">Review Rate</span>
            </div>
            <div className="text-sm font-medium">
              {stats.review_rate.toFixed(1)} scenes/hour
            </div>
          </div>

          {/* Avg Time per Scene */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4 text-purple-500" />
              <span className="text-sm">Avg Time per Scene</span>
            </div>
            <div className="text-sm font-medium">
              {formatTime(stats.avg_time_per_scene)}
            </div>
          </div>
        </div>
      </div>

      {/* Session Info */}
      <div className="pt-4 border-t">
        <div className="grid grid-cols-2 gap-4 text-xs text-muted-foreground">
          <div className="flex items-center space-x-1">
            <User className="h-3 w-3" />
            <span>Reviewer: {reviewerId || 'Current User'}</span>
          </div>
          <div className="flex items-center space-x-1">
            <Calendar className="h-3 w-3" />
            <span>Last 24 hours</span>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      {stats.pending_scenes > 0 && (
        <div className="mt-4 pt-4 border-t">
          <div className="flex items-center justify-between">
            <div className="text-sm">
              <span className="font-medium">{stats.pending_scenes}</span> scenes remaining
            </div>
            <div className="text-xs text-muted-foreground">
              Estimated: {formatTime(stats.pending_scenes * stats.avg_time_per_scene)} remaining
            </div>
          </div>
        </div>
      )}

      {/* Completion Message */}
      {completionPercentage === 100 && (
        <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-md">
          <div className="flex items-center space-x-2">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <span className="text-sm font-medium text-green-800">
              All scenes reviewed!
            </span>
          </div>
        </div>
      )}
    </div>
  )
}