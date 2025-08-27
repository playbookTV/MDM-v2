import { useState, useRef, useEffect } from 'react'
import { 
  Download, 
  Trash2, 
  Filter, 
  Search, 
  ChevronDown,
  Bug,
  Info,
  AlertTriangle,
  XCircle,
  Loader2,
  Eye,
  EyeOff
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useJobLogsStream } from '@/hooks/useJobLogs'
import type { Job, JobLogEntry } from '@/types/dataset'

interface JobLogsModalProps {
  job: Job | null
  open: boolean
  onClose: () => void
}

const LOG_LEVEL_CONFIG = {
  DEBUG: { 
    icon: Bug, 
    color: 'text-gray-500', 
    bg: 'bg-gray-50', 
    badge: 'outline' as const,
    label: 'Debug'
  },
  INFO: { 
    icon: Info, 
    color: 'text-blue-500', 
    bg: 'bg-blue-50', 
    badge: 'default' as const,
    label: 'Info'
  },
  WARNING: { 
    icon: AlertTriangle, 
    color: 'text-yellow-500', 
    bg: 'bg-yellow-50', 
    badge: 'secondary' as const,
    label: 'Warning'
  },
  ERROR: { 
    icon: XCircle, 
    color: 'text-red-500', 
    bg: 'bg-red-50', 
    badge: 'destructive' as const,
    label: 'Error'
  }
}

export function JobLogsModal({ job, open, onClose }: JobLogsModalProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [levelFilter, setLevelFilter] = useState<string[]>([])
  const [autoScroll, setAutoScroll] = useState(true)
  const [showContext, setShowContext] = useState(false)
  const logsEndRef = useRef<HTMLDivElement>(null)
  
  const {
    logs,
    isLoading,
    error,
    clearLogs,
    downloadLogs,
    getLogsByLevel,
    getLogStats,
    hasNewLogs
  } = useJobLogsStream(job?.id || '', {
    maxLogs: 1000,
    autoScroll,
    levelFilter: levelFilter.length > 0 ? levelFilter : undefined
  })

  // Scroll to bottom when new logs arrive (if auto-scroll is enabled)
  useEffect(() => {
    if (autoScroll && hasNewLogs && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [hasNewLogs, autoScroll])

  const filteredLogs = logs.filter(log => {
    if (searchQuery) {
      return log.message.toLowerCase().includes(searchQuery.toLowerCase())
    }
    return true
  })

  const logStats = getLogStats()

  const handleLevelFilterChange = (level: string) => {
    setLevelFilter(prev => {
      if (prev.includes(level)) {
        return prev.filter(l => l !== level)
      } else {
        return [...prev, level]
      }
    })
  }

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString()
  }

  const renderLogEntry = (log: JobLogEntry, index: number) => {
    const config = LOG_LEVEL_CONFIG[log.level]
    const Icon = config.icon

    return (
      <div 
        key={`${log.timestamp}-${index}`}
        className={`flex items-start space-x-3 p-3 rounded-md border-l-2 border-l-${config.color.split('-')[1]}-500 ${config.bg}`}
      >
        <Icon className={`h-4 w-4 mt-0.5 ${config.color} flex-shrink-0`} />
        
        <div className="flex-1 min-w-0 space-y-1">
          <div className="flex items-center space-x-2">
            <Badge variant={config.badge} className="text-xs">
              {config.label}
            </Badge>
            <span className="text-xs text-muted-foreground font-mono">
              {formatTimestamp(log.timestamp)}
            </span>
          </div>
          
          <p className="text-sm font-mono break-words leading-relaxed">
            {log.message}
          </p>
          
          {showContext && log.context && Object.keys(log.context).length > 0 && (
            <details className="mt-2">
              <summary className="text-xs text-muted-foreground cursor-pointer hover:text-foreground">
                Context ({Object.keys(log.context).length} fields)
              </summary>
              <pre className="text-xs bg-muted p-2 rounded mt-1 overflow-x-auto">
                {JSON.stringify(log.context, null, 2)}
              </pre>
            </details>
          )}
        </div>
      </div>
    )
  }

  if (!job) return null

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-5xl max-h-[80vh] flex flex-col">
        <DialogHeader className="flex-shrink-0">
          <DialogTitle>Job Logs - {job.dataset_name || job.dataset_id}</DialogTitle>
          <DialogDescription>
            Real-time logs for job #{job.id.slice(-8)} • {logs.length} entries
          </DialogDescription>
        </DialogHeader>

        {/* Controls Bar */}
        <div className="flex-shrink-0 flex items-center justify-between gap-4 py-3 border-b">
          {/* Search */}
          <div className="relative flex-1 max-w-sm">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search logs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>

          {/* Level Filter */}
          <div className="flex items-center space-x-2">
            {Object.entries(LOG_LEVEL_CONFIG).map(([level, config]) => (
              <Button
                key={level}
                variant={levelFilter.includes(level) ? "default" : "outline"}
                size="sm"
                onClick={() => handleLevelFilterChange(level)}
                className="text-xs"
              >
                <config.icon className="h-3 w-3 mr-1" />
                {config.label} ({logStats[level.toLowerCase() as keyof typeof logStats]})
              </Button>
            ))}
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowContext(!showContext)}
            >
              {showContext ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => setAutoScroll(!autoScroll)}
            >
              <ChevronDown className={`h-4 w-4 ${autoScroll ? 'text-green-500' : ''}`} />
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={downloadLogs}
              disabled={logs.length === 0}
            >
              <Download className="h-4 w-4" />
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={clearLogs}
              disabled={logs.length === 0}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Logs Content */}
        <div 
          className="flex-1 overflow-y-auto space-y-2 p-1"
          data-logs-container
        >
          {isLoading && logs.length === 0 && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-6 w-6 animate-spin mr-2" />
              <span className="text-muted-foreground">Loading logs...</span>
            </div>
          )}

          {error && (
            <div className="bg-destructive/10 border border-destructive/20 rounded-md p-4">
              <div className="flex items-center space-x-2">
                <XCircle className="h-4 w-4 text-destructive" />
                <span className="text-destructive font-medium">Failed to load logs</span>
              </div>
              <p className="text-sm text-destructive/80 mt-1">{error?.message || 'An error occurred'}</p>
            </div>
          )}

          {!isLoading && !error && logs.length === 0 && (
            <div className="text-center py-8 text-muted-foreground">
              <Info className="h-8 w-8 mx-auto mb-2" />
              <p>No logs available for this job</p>
            </div>
          )}

          {!isLoading && !error && filteredLogs.length === 0 && logs.length > 0 && (
            <div className="text-center py-8 text-muted-foreground">
              <Search className="h-8 w-8 mx-auto mb-2" />
              <p>No logs match your search criteria</p>
            </div>
          )}

          {filteredLogs.map(renderLogEntry)}
          
          <div ref={logsEndRef} />
        </div>

        {/* Status Bar */}
        <div className="flex-shrink-0 flex items-center justify-between text-xs text-muted-foreground py-2 border-t">
          <div className="flex items-center space-x-4">
            <span>{filteredLogs.length} of {logs.length} logs shown</span>
            {searchQuery && <Badge variant="outline">Searching: {searchQuery}</Badge>}
            {levelFilter.length > 0 && (
              <Badge variant="outline">
                Filtered: {levelFilter.join(', ')}
              </Badge>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            {autoScroll && <Badge variant="outline">Auto-scroll ON</Badge>}
            {hasNewLogs && <Badge variant="default">New logs available</Badge>}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}