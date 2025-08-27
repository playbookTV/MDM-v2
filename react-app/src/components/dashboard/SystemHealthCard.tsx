import { 
  Cpu, 
  HardDrive, 
  MemoryStick, 
  Users, 
  Clock, 
  Activity,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  TrendingDown
} from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { useSystemHealth, useSystemTrends } from '@/hooks/useStats'
import type { StatsQuery } from '@/types/stats'

interface SystemHealthCardProps {
  query?: StatsQuery
  className?: string
}

export function SystemHealthCard({ query, className }: SystemHealthCardProps) {
  const { data: health, isLoading, error } = useSystemHealth()
  const { data: trends } = useSystemTrends({ time_range: '1h', granularity: 'minute' })

  const getHealthStatus = () => {
    if (!health) return { status: 'unknown', label: 'Unknown', color: 'text-gray-500' }
    
    const criticalThreshold = 90
    const warningThreshold = 75
    
    const maxUsage = Math.max(health.cpu_usage_percent, health.memory_usage_percent, health.disk_usage_percent)
    
    if (maxUsage >= criticalThreshold) {
      return { status: 'critical', label: 'Critical', color: 'text-red-500' }
    } else if (maxUsage >= warningThreshold) {
      return { status: 'warning', label: 'Warning', color: 'text-yellow-500' }
    } else {
      return { status: 'healthy', label: 'Healthy', color: 'text-green-500' }
    }
  }

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / (24 * 3600))
    const hours = Math.floor((seconds % (24 * 3600)) / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    
    if (days > 0) {
      return `${days}d ${hours}h ${minutes}m`
    } else if (hours > 0) {
      return `${hours}h ${minutes}m`
    } else {
      return `${minutes}m`
    }
  }

  const getProcessingTrend = () => {
    if (!trends || trends.length < 2) return { direction: 'stable', change: 0 }
    
    const latest = trends[trends.length - 1]
    const previous = trends[trends.length - 2]
    
    const change = latest.processing_rate - previous.processing_rate
    const direction = change > 0 ? 'up' : change < 0 ? 'down' : 'stable'
    
    return { direction, change: Math.abs(change) }
  }

  const healthStatus = getHealthStatus()
  const processingTrend = getProcessingTrend()

  if (error) {
    return (
      <div className={`bg-card border rounded-lg p-6 ${className}`}>
        <div className="flex items-center space-x-2 mb-4">
          <AlertTriangle className="h-5 w-5 text-destructive" />
          <h3 className="text-lg font-semibold">System Health</h3>
          <Badge variant="destructive">Error</Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          Unable to fetch system health data
        </p>
      </div>
    )
  }

  if (isLoading || !health) {
    return (
      <div className={`bg-card border rounded-lg p-6 ${className}`}>
        <div className="flex items-center space-x-2 mb-4">
          <Activity className="h-5 w-5 animate-pulse" />
          <h3 className="text-lg font-semibold">System Health</h3>
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

  return (
    <div className={`bg-card border rounded-lg p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <Activity className="h-5 w-5" />
          <h3 className="text-lg font-semibold">System Health</h3>
        </div>
        
        <div className="flex items-center space-x-2">
          {healthStatus.status === 'healthy' && <CheckCircle className="h-4 w-4 text-green-500" />}
          {healthStatus.status === 'warning' && <AlertTriangle className="h-4 w-4 text-yellow-500" />}
          {healthStatus.status === 'critical' && <AlertTriangle className="h-4 w-4 text-red-500" />}
          
          <Badge 
            variant={healthStatus.status === 'healthy' ? 'secondary' : 'destructive'}
            className={healthStatus.color}
          >
            {healthStatus.label}
          </Badge>
        </div>
      </div>

      {/* System Metrics */}
      <div className="space-y-6">
        {/* CPU Usage */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Cpu className="h-4 w-4 text-blue-500" />
              <span className="text-sm font-medium">CPU Usage</span>
            </div>
            <span className="text-sm text-muted-foreground">
              {health.cpu_usage_percent.toFixed(1)}%
            </span>
          </div>
          <Progress value={health.cpu_usage_percent} className="h-2" />
        </div>

        {/* Memory Usage */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <MemoryStick className="h-4 w-4 text-green-500" />
              <span className="text-sm font-medium">Memory Usage</span>
            </div>
            <span className="text-sm text-muted-foreground">
              {health.memory_usage_percent.toFixed(1)}%
            </span>
          </div>
          <Progress value={health.memory_usage_percent} className="h-2" />
        </div>

        {/* Disk Usage */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <HardDrive className="h-4 w-4 text-purple-500" />
              <span className="text-sm font-medium">Disk Usage</span>
            </div>
            <span className="text-sm text-muted-foreground">
              {health.disk_usage_percent.toFixed(1)}%
            </span>
          </div>
          <Progress value={health.disk_usage_percent} className="h-2" />
        </div>

        {/* Processing Stats Grid */}
        <div className="grid grid-cols-2 gap-4 pt-4 border-t">
          <div className="text-center">
            <div className="flex items-center justify-center space-x-1 mb-1">
              <Users className="h-4 w-4 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">Workers</span>
            </div>
            <div className="text-xl font-semibold">{health.active_workers}</div>
            <div className="text-xs text-muted-foreground">
              Queue: {health.queue_depth}
            </div>
          </div>
          
          <div className="text-center">
            <div className="flex items-center justify-center space-x-1 mb-1">
              <Activity className="h-4 w-4 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">Processing Rate</span>
              {processingTrend.direction === 'up' && (
                <TrendingUp className="h-3 w-3 text-green-500" />
              )}
              {processingTrend.direction === 'down' && (
                <TrendingDown className="h-3 w-3 text-red-500" />
              )}
            </div>
            <div className="text-xl font-semibold">
              {health.processing_rate_per_minute.toFixed(1)}
            </div>
            <div className="text-xs text-muted-foreground">scenes/min</div>
          </div>
        </div>

        {/* Uptime */}
        <div className="flex items-center justify-between pt-4 border-t">
          <div className="flex items-center space-x-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">Uptime</span>
          </div>
          <span className="text-sm font-medium">
            {formatUptime(health.uptime_seconds)}
          </span>
        </div>

        {/* Last Updated */}
        <div className="text-xs text-muted-foreground text-center">
          Last updated: {new Date(health.last_updated).toLocaleTimeString()}
        </div>
      </div>
    </div>
  )
}