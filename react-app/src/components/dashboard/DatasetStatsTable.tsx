import { useState, useMemo, useCallback, memo } from 'react'
import { 
  Database,
  Search,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Eye,
  Play,
  CheckCircle,
  XCircle,
  Clock,
} from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { useDatasetStats } from '@/hooks/useStats'
import type { StatsQuery } from '@/types/stats'

interface DatasetStatsTableProps {
  query?: StatsQuery
  onViewDataset?: (datasetId: string) => void
  onProcessDataset?: (datasetId: string) => void
  className?: string
}

type SortField = 'name' | 'scenes' | 'progress' | 'objects' | 'confidence' | 'last_processed'
type SortDirection = 'asc' | 'desc'

export function DatasetStatsTable({ 
  query, 
  onViewDataset, 
  onProcessDataset, 
  className 
}: DatasetStatsTableProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [sortField, setSortField] = useState<SortField>('last_processed')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')
  
  const { data: datasetStats, isLoading, error } = useDatasetStats(query)

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('desc')
    }
  }

  const getSortedAndFilteredData = useMemo(() => {
    if (!datasetStats) return []
    
    // Filter by search query
    let filtered = datasetStats.filter(dataset =>
      dataset.dataset_name.toLowerCase().includes(searchQuery.toLowerCase())
    )
    
    // Sort data
    filtered.sort((a, b) => {
      let aVal: any, bVal: any
      
      switch (sortField) {
        case 'name':
          aVal = a.dataset_name.toLowerCase()
          bVal = b.dataset_name.toLowerCase()
          break
        case 'scenes':
          aVal = a.total_scenes
          bVal = b.total_scenes
          break
        case 'progress':
          aVal = a.processing_progress
          bVal = b.processing_progress
          break
        case 'objects':
          aVal = a.objects_detected
          bVal = b.objects_detected
          break
        case 'confidence':
          aVal = a.average_confidence
          bVal = b.average_confidence
          break
        case 'last_processed':
          aVal = new Date(a.last_processed).getTime()
          bVal = new Date(b.last_processed).getTime()
          break
        default:
          return 0
      }
      
      if (sortDirection === 'asc') {
        return aVal > bVal ? 1 : -1
      } else {
        return aVal < bVal ? 1 : -1
      }
    })
    
    return filtered
  }, [datasetStats, searchQuery, sortField, sortDirection])

  const formatLastProcessed = useCallback((dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffHours / 24)
    
    if (diffDays > 0) {
      return `${diffDays}d ago`
    } else if (diffHours > 0) {
      return `${diffHours}h ago`
    } else {
      return 'Recently'
    }
  }, [])

  const getProcessingStatus = useCallback((dataset: any) => {
    if (dataset.failed_scenes > 0 && dataset.processing_progress < 100) {
      return { status: 'partial', icon: XCircle, color: 'text-yellow-500' }
    } else if (dataset.processing_progress === 100) {
      return { status: 'complete', icon: CheckCircle, color: 'text-green-500' }
    } else if (dataset.processing_progress > 0) {
      return { status: 'processing', icon: Clock, color: 'text-blue-500' }
    } else {
      return { status: 'pending', icon: Clock, color: 'text-gray-500' }
    }
  }, [])

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return <ArrowUpDown className="h-4 w-4 opacity-50" />
    }
    return sortDirection === 'asc' 
      ? <ArrowUp className="h-4 w-4" />
      : <ArrowDown className="h-4 w-4" />
  }

  const filteredData = getSortedAndFilteredData

  if (error) {
    return (
      <div className={`bg-card border rounded-lg p-6 ${className}`}>
        <div className="flex items-center space-x-2 mb-4">
          <Database className="h-5 w-5 text-destructive" />
          <h3 className="text-lg font-semibold">Dataset Statistics</h3>
          <Badge variant="destructive">Error</Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          Unable to load dataset statistics
        </p>
      </div>
    )
  }

  return (
    <div className={`bg-card border rounded-lg p-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <Database className="h-5 w-5" />
          <h3 className="text-lg font-semibold">Dataset Statistics</h3>
          {datasetStats && (
            <Badge variant="outline">
              {filteredData.length} of {datasetStats.length}
            </Badge>
          )}
        </div>
        
        {/* Search */}
        <div className="relative w-64">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search datasets..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }, (_, i) => (
            <div key={i} className="h-16 bg-muted animate-pulse rounded" />
          ))}
        </div>
      ) : filteredData.length === 0 ? (
        <div className="text-center py-12">
          <Database className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No datasets found</h3>
          <p className="text-sm text-muted-foreground">
            {searchQuery ? 'No datasets match your search criteria.' : 'No datasets available.'}
          </p>
        </div>
      ) : (
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>
                  <Button 
                    variant="ghost" 
                    className="h-auto p-0 font-medium"
                    onClick={() => handleSort('name')}
                  >
                    Dataset <SortIcon field="name" />
                  </Button>
                </TableHead>
                <TableHead>
                  <Button 
                    variant="ghost" 
                    className="h-auto p-0 font-medium"
                    onClick={() => handleSort('scenes')}
                  >
                    Scenes <SortIcon field="scenes" />
                  </Button>
                </TableHead>
                <TableHead>
                  <Button 
                    variant="ghost" 
                    className="h-auto p-0 font-medium"
                    onClick={() => handleSort('progress')}
                  >
                    Progress <SortIcon field="progress" />
                  </Button>
                </TableHead>
                <TableHead>
                  <Button 
                    variant="ghost" 
                    className="h-auto p-0 font-medium"
                    onClick={() => handleSort('objects')}
                  >
                    Objects <SortIcon field="objects" />
                  </Button>
                </TableHead>
                <TableHead>
                  <Button 
                    variant="ghost" 
                    className="h-auto p-0 font-medium"
                    onClick={() => handleSort('confidence')}
                  >
                    Confidence <SortIcon field="confidence" />
                  </Button>
                </TableHead>
                <TableHead>
                  <Button 
                    variant="ghost" 
                    className="h-auto p-0 font-medium"
                    onClick={() => handleSort('last_processed')}
                  >
                    Last Processed <SortIcon field="last_processed" />
                  </Button>
                </TableHead>
                <TableHead className="w-32">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredData.map((dataset) => {
                const status = getProcessingStatus(dataset)
                const StatusIcon = status.icon
                
                return (
                  <TableRow key={dataset.dataset_id}>
                    <TableCell>
                      <div>
                        <div className="font-medium">{dataset.dataset_name}</div>
                        <div className="text-xs text-muted-foreground">
                          {dataset.unique_object_types} object types
                        </div>
                        {/* Scene Types */}
                        <div className="flex flex-wrap gap-1 mt-1">
                          {dataset.scene_types.slice(0, 3).map((sceneType) => (
                            <Badge key={sceneType.scene_type} variant="outline" className="text-xs">
                              {sceneType.scene_type} ({sceneType.count})
                            </Badge>
                          ))}
                          {dataset.scene_types.length > 3 && (
                            <Badge variant="outline" className="text-xs">
                              +{dataset.scene_types.length - 3} more
                            </Badge>
                          )}
                        </div>
                      </div>
                    </TableCell>
                    
                    <TableCell>
                      <div className="text-center">
                        <div className="text-lg font-semibold">
                          {dataset.total_scenes.toLocaleString()}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {dataset.processed_scenes} processed
                        </div>
                        {dataset.failed_scenes > 0 && (
                          <div className="text-xs text-red-500">
                            {dataset.failed_scenes} failed
                          </div>
                        )}
                      </div>
                    </TableCell>
                    
                    <TableCell>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <StatusIcon className={`h-4 w-4 ${status.color}`} />
                          <span className="text-sm">{dataset.processing_progress.toFixed(1)}%</span>
                        </div>
                        <Progress value={dataset.processing_progress} className="h-2" />
                      </div>
                    </TableCell>
                    
                    <TableCell>
                      <div className="text-center">
                        <div className="text-lg font-semibold">
                          {dataset.objects_detected.toLocaleString()}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {dataset.unique_object_types} types
                        </div>
                      </div>
                    </TableCell>
                    
                    <TableCell>
                      <div className="text-center">
                        <div className="text-lg font-semibold">
                          {(dataset.average_confidence * 100).toFixed(1)}%
                        </div>
                        <div className="text-xs text-muted-foreground">
                          avg confidence
                        </div>
                      </div>
                    </TableCell>
                    
                    <TableCell>
                      <div className="text-sm">
                        {formatLastProcessed(dataset.last_processed)}
                      </div>
                    </TableCell>
                    
                    <TableCell>
                      <div className="flex items-center space-x-1">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => onViewDataset?.(dataset.dataset_id)}
                        >
                          <Eye className="h-3 w-3" />
                        </Button>
                        {dataset.processing_progress < 100 && (
                          <Button
                            variant="default"
                            size="sm"
                            onClick={() => onProcessDataset?.(dataset.dataset_id)}
                          >
                            <Play className="h-3 w-3" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  )
}