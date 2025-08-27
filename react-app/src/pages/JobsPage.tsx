import { useState } from 'react'
import { Play, RefreshCw, Filter, AlertCircle, CheckCircle, Clock, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { JobCard } from '@/components/jobs/JobCard'
import { JobLogsModal } from '@/components/jobs/JobLogsModal'
import { StartJobModal } from '@/components/jobs/StartJobModal'
import { useJobs, useJobStats, useJobMonitoring } from '@/hooks/useJobs'
import type { Job } from '@/types/dataset'

export function JobsPage() {
  const [statusFilter, setStatusFilter] = useState<string>('all')
  const [kindFilter, setKindFilter] = useState<string>('all')
  const [currentPage, setCurrentPage] = useState(1)
  const [selectedJob, setSelectedJob] = useState<Job | null>(null)
  const [showLogsModal, setShowLogsModal] = useState(false)
  const [showStartJobModal, setShowStartJobModal] = useState(false)

  // Enable real-time monitoring
  const { refreshJobs } = useJobMonitoring(true)

  const { data: jobsPage, isLoading, error } = useJobs({
    status: statusFilter !== 'all' ? statusFilter : undefined,
    kind: kindFilter !== 'all' ? kindFilter : undefined,
    page: currentPage,
    limit: 20,
  })

  const { data: jobStats } = useJobStats()

  const jobs = jobsPage?.items || []
  const totalPages = jobsPage ? Math.ceil(jobsPage.total / jobsPage.limit) : 0

  const handleViewLogs = (job: Job) => {
    setSelectedJob(job)
    setShowLogsModal(true)
  }

  const handleViewDataset = (job: Job) => {
    console.log('Navigate to dataset:', job.dataset_id)
    // TODO: Navigate to dataset detail page
  }

  const getStatusStats = () => {
    if (!jobStats) return null

    return [
      { 
        status: 'running', 
        count: jobStats.running_jobs, 
        label: 'Running',
        icon: Loader2,
        color: 'text-blue-500'
      },
      { 
        status: 'queued', 
        count: jobStats.queued_jobs, 
        label: 'Queued',
        icon: Clock,
        color: 'text-yellow-500'
      },
      { 
        status: 'succeeded', 
        count: jobStats.completed_jobs, 
        label: 'Completed',
        icon: CheckCircle,
        color: 'text-green-500'
      },
      { 
        status: 'failed', 
        count: jobStats.failed_jobs, 
        label: 'Failed',
        icon: AlertCircle,
        color: 'text-red-500'
      },
    ]
  }

  const statusStats = getStatusStats()

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-destructive mb-2">
              Failed to load jobs
            </h3>
            <p className="text-sm text-muted-foreground mb-4">
              {error.message}
            </p>
            <Button onClick={() => window.location.reload()}>
              Retry
            </Button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Processing Jobs</h1>
          <p className="text-muted-foreground mt-1">
            Monitor and manage dataset processing jobs
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={refreshJobs}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button onClick={() => setShowStartJobModal(true)}>
            <Play className="h-4 w-4 mr-2" />
            Start Job
          </Button>
        </div>
      </div>

      {/* Stats Dashboard */}
      {statusStats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {statusStats.map(({ status, count, label, icon: Icon, color }) => (
            <div key={status} className="bg-card border rounded-lg p-4">
              <div className="flex items-center space-x-2">
                <Icon className={`h-5 w-5 ${color}`} />
                <span className="text-sm font-medium text-muted-foreground">{label}</span>
              </div>
              <div className="text-2xl font-bold mt-2">{count.toLocaleString()}</div>
              {status === 'succeeded' && jobStats && (
                <div className="text-xs text-muted-foreground mt-1">
                  {jobStats.success_rate.toFixed(1)}% success rate
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center space-x-4 mb-6">
        <div className="flex items-center space-x-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-medium">Filters:</span>
        </div>
        
        <Select value={statusFilter} onValueChange={setStatusFilter}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Status" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Status</SelectItem>
            <SelectItem value="queued">Queued</SelectItem>
            <SelectItem value="running">Running</SelectItem>
            <SelectItem value="succeeded">Completed</SelectItem>
            <SelectItem value="failed">Failed</SelectItem>
          </SelectContent>
        </Select>

        <Select value={kindFilter} onValueChange={setKindFilter}>
          <SelectTrigger className="w-40">
            <SelectValue placeholder="Type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Types</SelectItem>
            <SelectItem value="ingest">Data Ingestion</SelectItem>
            <SelectItem value="process">AI Processing</SelectItem>
          </SelectContent>
        </Select>
        
        {jobsPage && (
          <div className="text-sm text-muted-foreground">
            Showing {jobs.length} of {jobsPage.total} job{jobsPage.total !== 1 ? 's' : ''}
          </div>
        )}
      </div>

      {/* Jobs List */}
      <div className="space-y-4">
        {isLoading && (
          <div className="space-y-4">
            {Array.from({ length: 3 }, (_, i) => (
              <div key={i} className="h-32 bg-muted animate-pulse rounded-lg" />
            ))}
          </div>
        )}

        {!isLoading && jobs.length === 0 && (
          <div className="text-center py-12">
            <Play className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No jobs found</h3>
            <p className="text-sm text-gray-500 mb-4">
              {statusFilter !== 'all' || kindFilter !== 'all'
                ? 'No jobs match your current filters.'
                : 'Start processing your datasets to see jobs here.'}
            </p>
            <Button onClick={() => setShowStartJobModal(true)}>
              <Play className="h-4 w-4 mr-2" />
              Start Your First Job
            </Button>
          </div>
        )}

        {!isLoading && jobs.map((job) => (
          <JobCard
            key={job.id}
            job={job}
            onViewLogs={handleViewLogs}
            onViewDataset={handleViewDataset}
          />
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-8">
          <div className="text-sm text-muted-foreground">
            Page {currentPage} of {totalPages}
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage <= 1 || isLoading}
            >
              Previous
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage >= totalPages || isLoading}
            >
              Next
            </Button>
          </div>
        </div>
      )}

      {/* Real-time Status Indicator */}
      {statusStats && statusStats.some(s => s.count > 0 && (s.status === 'running' || s.status === 'queued')) && (
        <div className="fixed bottom-4 right-4">
          <Badge variant="default" className="animate-pulse">
            <Loader2 className="h-3 w-3 mr-1 animate-spin" />
            Jobs Running
          </Badge>
        </div>
      )}

      {/* Modals */}
      <JobLogsModal
        job={selectedJob}
        open={showLogsModal}
        onClose={() => {
          setShowLogsModal(false)
          setSelectedJob(null)
        }}
      />
      
      <StartJobModal
        open={showStartJobModal}
        onClose={() => setShowStartJobModal(false)}
      />
    </div>
  )
}