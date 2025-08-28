import { useState } from 'react'
import { BarChart3, RefreshCw, Download, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { SystemHealthCard } from '@/components/dashboard/SystemHealthCard'
import { ProcessingMetricsChart } from '@/components/dashboard/ProcessingMetricsChart'
import { ModelPerformanceChart } from '@/components/dashboard/ModelPerformanceChart'
import { DatasetStatsTable } from '@/components/dashboard/DatasetStatsTable'
import { TimeRangeSelector } from '@/components/dashboard/TimeRangeSelector'
import { useDashboardSummary, useDashboardRefresh } from '@/hooks/useStats'
import type { StatsQuery } from '@/types/stats'

export function StatsDashboardPage() {
  const [query, setQuery] = useState<StatsQuery>({ 
    time_range: '24h' 
  })
  
  const { data: dashboardData, isLoading, error } = useDashboardSummary(query)
  const { refreshAll, getLastUpdated } = useDashboardRefresh()

  const handleViewDataset = (datasetId: string) => {
    console.log('Navigate to dataset:', datasetId)
    // TODO: Navigate to dataset detail page
  }

  const handleProcessDataset = (datasetId: string) => {
    console.log('Start processing dataset:', datasetId)
    // TODO: Navigate to jobs page with preselected dataset
  }

  const handleExportData = () => {
    if (!dashboardData) return
    
    const data = {
      ...dashboardData,
      exported_at: new Date().toISOString(),
      query_parameters: query,
    }
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { 
      type: 'application/json' 
    })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `modomo-dashboard-${new Date().toISOString().split('T')[0]}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center min-h-[400px]">
          {error && (
            <div className="text-center py-8">
              <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
              <p className="text-lg font-medium text-destructive mb-2">Failed to load statistics</p>
              <p className="text-muted-foreground">
                {error?.message || 'An error occurred while loading statistics'}
              </p>
            </div>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Analytics Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            System performance and dataset processing insights
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button variant="outline" onClick={refreshAll}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button variant="outline" onClick={handleExportData} disabled={!dashboardData}>
            <Download className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>
      </div>

      {/* Time Range Controls */}
      <div className="flex items-center justify-between">
        <TimeRangeSelector
          value={query}
          onChange={setQuery}
        />
        
        <div className="text-xs text-muted-foreground">
          Last updated: {getLastUpdated()}
        </div>
      </div>

      {/* Dashboard Grid */}
      {isLoading ? (
        <div className="space-y-8">
          <div className="h-96 bg-muted animate-pulse rounded-lg" />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="h-96 bg-muted animate-pulse rounded-lg" />
            <div className="h-96 bg-muted animate-pulse rounded-lg" />
          </div>
          <div className="h-96 bg-muted animate-pulse rounded-lg" />
        </div>
      ) : (
        <>
          {/* Top Row - System Health */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            <div className="lg:col-span-1">
              <SystemHealthCard query={query} />
            </div>
            
            <div className="lg:col-span-2">
              <ProcessingMetricsChart query={query} />
            </div>
          </div>

          {/* Middle Row - Model Performance */}
          <ModelPerformanceChart query={query} />

          {/* Bottom Row - Dataset Statistics */}
          <DatasetStatsTable
            query={query}
            onViewDataset={handleViewDataset}
            onProcessDataset={handleProcessDataset}
          />

          {/* Footer Summary */}
          {dashboardData && (
            <div className="bg-muted/50 rounded-lg p-6">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
                <div>
                  <div className="text-2xl font-bold text-blue-600">
                    {dashboardData.total_datasets || 0}
                  </div>
                  <div className="text-sm text-muted-foreground">Active Datasets</div>
                </div>
                
                <div>
                  <div className="text-2xl font-bold text-green-600">
                    {(dashboardData.total_scenes || 0).toLocaleString()}
                  </div>
                  <div className="text-sm text-muted-foreground">Total Scenes</div>
                </div>
                
                <div>
                  <div className="text-2xl font-bold text-purple-600">
                    {(dashboardData.total_objects || 0).toLocaleString()}
                  </div>
                  <div className="text-sm text-muted-foreground">Total Objects</div>
                </div>
                
                <div>
                  <div className="text-2xl font-bold text-orange-600">
                    {dashboardData.system_health_score || 0}%
                  </div>
                  <div className="text-sm text-muted-foreground">System Health</div>
                </div>
              </div>
              
              <div className="text-center mt-4 text-xs text-muted-foreground">
                Dashboard generated at {new Date().toLocaleString()}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}