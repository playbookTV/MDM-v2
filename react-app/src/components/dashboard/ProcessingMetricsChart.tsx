import { useState } from 'react'
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell
} from 'recharts'
import { TrendingUp, BarChart3, PieChart as PieChartIcon, Activity } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { useProcessingTrends } from '@/hooks/useStats'
import type { StatsQuery } from '@/types/stats'

interface ProcessingMetricsChartProps {
  query?: StatsQuery
  className?: string
}

type ChartType = 'line' | 'bar' | 'pie'


export function ProcessingMetricsChart({ query, className }: ProcessingMetricsChartProps) {
  const [chartType, setChartType] = useState<ChartType>('line')
  
  const { data: trends, isLoading, error } = useProcessingTrends(query)

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const timeRange = query?.time_range || '24h'
    
    if (timeRange === '1h' || timeRange === '6h') {
      return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    } else if (timeRange === '24h') {
      return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    }
  }

  const getChartData = () => {
    if (!trends) return []
    
    return trends.map(trend => ({
      date: trend.date,
      dateFormatted: formatDate(trend.date),
      jobsCompleted: trend.jobs_completed,
      jobsFailed: trend.jobs_failed,
      successRate: trend.success_rate * 100,
      processingRate: trend.processing_rate,
      averageConfidence: trend.average_confidence * 100,
    }))
  }

  const getPieData = () => {
    if (!trends) return []
    
    const totalCompleted = trends.reduce((sum, t) => sum + t.jobs_completed, 0)
    const totalFailed = trends.reduce((sum, t) => sum + t.jobs_failed, 0)
    
    return [
      { name: 'Completed', value: totalCompleted, color: '#10b981' },
      { name: 'Failed', value: totalFailed, color: '#ef4444' },
    ]
  }

  const getSummaryStats = () => {
    if (!trends || trends.length === 0) return null
    
    const totalCompleted = trends.reduce((sum, t) => sum + t.jobs_completed, 0)
    const totalFailed = trends.reduce((sum, t) => sum + t.jobs_failed, 0)
    const avgSuccessRate = trends.reduce((sum, t) => sum + t.success_rate, 0) / trends.length
    const avgProcessingRate = trends.reduce((sum, t) => sum + t.processing_rate, 0) / trends.length
    const avgConfidence = trends.reduce((sum, t) => sum + t.average_confidence, 0) / trends.length
    
    return {
      totalCompleted,
      totalFailed,
      totalJobs: totalCompleted + totalFailed,
      avgSuccessRate: avgSuccessRate * 100,
      avgProcessingRate,
      avgConfidence: avgConfidence * 100,
    }
  }

  const chartData = getChartData()
  const pieData = getPieData()
  const summaryStats = getSummaryStats()

  if (error) {
    return (
      <div className={`bg-card border rounded-lg p-6 ${className}`}>
        <div className="flex items-center space-x-2 mb-4">
          <Activity className="h-5 w-5 text-destructive" />
          <h3 className="text-lg font-semibold">Processing Metrics</h3>
          <Badge variant="destructive">Error</Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          Unable to load processing metrics
        </p>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className={`bg-card border rounded-lg p-6 ${className}`}>
        <div className="flex items-center space-x-2 mb-4">
          <Activity className="h-5 w-5 animate-pulse" />
          <h3 className="text-lg font-semibold">Processing Metrics</h3>
        </div>
        <div className="h-80 bg-muted animate-pulse rounded" />
      </div>
    )
  }

  return (
    <div className={`bg-card border rounded-lg p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <Activity className="h-5 w-5" />
          <h3 className="text-lg font-semibold">Processing Metrics</h3>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button
            variant={chartType === 'line' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setChartType('line')}
          >
            <TrendingUp className="h-4 w-4" />
          </Button>
          <Button
            variant={chartType === 'bar' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setChartType('bar')}
          >
            <BarChart3 className="h-4 w-4" />
          </Button>
          <Button
            variant={chartType === 'pie' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setChartType('pie')}
          >
            <PieChartIcon className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Summary Stats */}
      {summaryStats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="text-center p-3 bg-muted/50 rounded-md">
            <div className="text-2xl font-bold text-green-600">
              {summaryStats.totalCompleted.toLocaleString()}
            </div>
            <div className="text-xs text-muted-foreground">Jobs Completed</div>
          </div>
          
          <div className="text-center p-3 bg-muted/50 rounded-md">
            <div className="text-2xl font-bold text-red-600">
              {summaryStats.totalFailed.toLocaleString()}
            </div>
            <div className="text-xs text-muted-foreground">Jobs Failed</div>
          </div>
          
          <div className="text-center p-3 bg-muted/50 rounded-md">
            <div className="text-2xl font-bold text-blue-600">
              {summaryStats.avgSuccessRate.toFixed(1)}%
            </div>
            <div className="text-xs text-muted-foreground">Avg Success Rate</div>
          </div>
          
          <div className="text-center p-3 bg-muted/50 rounded-md">
            <div className="text-2xl font-bold text-purple-600">
              {summaryStats.avgProcessingRate.toFixed(1)}
            </div>
            <div className="text-xs text-muted-foreground">Scenes/min</div>
          </div>
        </div>
      )}

      {/* Chart Area */}
      <div className="h-80">
        {chartData.length === 0 ? (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            No data available for the selected time range
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            {chartType === 'line' && (
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                <XAxis 
                  dataKey="dateFormatted" 
                  tick={{ fontSize: 12 }}
                  stroke="#6b7280"
                />
                <YAxis tick={{ fontSize: 12 }} stroke="#6b7280" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                  }}
                  labelStyle={{ color: '#f9fafb' }}
                />
                <Legend />
                
                <Line
                  type="monotone"
                  dataKey="jobsCompleted"
                  stroke="#10b981"
                  strokeWidth={2}
                  name="Completed Jobs"
                  dot={{ fill: '#10b981', strokeWidth: 2, r: 4 }}
                />
                
                <Line
                  type="monotone"
                  dataKey="jobsFailed"
                  stroke="#ef4444"
                  strokeWidth={2}
                  name="Failed Jobs"
                  dot={{ fill: '#ef4444', strokeWidth: 2, r: 4 }}
                />
                
                <Line
                  type="monotone"
                  dataKey="successRate"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name="Success Rate (%)"
                  dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                />
              </LineChart>
            )}
            
            {chartType === 'bar' && (
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#374151" opacity={0.3} />
                <XAxis 
                  dataKey="dateFormatted" 
                  tick={{ fontSize: 12 }}
                  stroke="#6b7280"
                />
                <YAxis tick={{ fontSize: 12 }} stroke="#6b7280" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
                
                <Bar dataKey="jobsCompleted" fill="#10b981" name="Completed" />
                <Bar dataKey="jobsFailed" fill="#ef4444" name="Failed" />
              </BarChart>
            )}
            
            {chartType === 'pie' && (
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={120}
                  paddingAngle={5}
                  dataKey="value"
                  label={(entry) => `${entry.name}: ${entry.value}`}
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#1f2937',
                    border: '1px solid #374151',
                    borderRadius: '8px',
                  }}
                />
                <Legend />
              </PieChart>
            )}
          </ResponsiveContainer>
        )}
      </div>
    </div>
  )
}