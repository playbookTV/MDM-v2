import { useState } from 'react'
import { 
  Grid, 
  List, 
  Search, 
  Filter,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  Eye,
  ChevronLeft,
  ChevronRight,
  Loader2
} from 'lucide-react'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useScenes, useSceneImages, REVIEW_STATUSES, SCENE_TYPES } from '@/hooks/useScenes'
import type { Scene } from '@/types/dataset'

interface SceneGalleryProps {
  datasetId?: string
  selectedScenes?: Set<string>
  onSceneSelect?: (scene: Scene) => void
  onSceneToggle?: (sceneId: string) => void
  onBatchSelect?: (scenes: Scene[]) => void
  className?: string
}

type ViewMode = 'grid' | 'list'

const REVIEW_STATUS_ICONS = {
  pending: Clock,
  approved: CheckCircle,
  rejected: XCircle,
  corrected: AlertTriangle,
}

const REVIEW_STATUS_COLORS = {
  pending: 'text-gray-500',
  approved: 'text-green-500',
  rejected: 'text-red-500',
  corrected: 'text-yellow-500',
}

export function SceneGallery({
  datasetId,
  selectedScenes = new Set(),
  onSceneSelect,
  onSceneToggle,
  onBatchSelect,
  className
}: SceneGalleryProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('grid')
  const [searchQuery, setSearchQuery] = useState('')
  const [reviewStatusFilter, setReviewStatusFilter] = useState<string>('all')
  const [sceneTypeFilter, setSceneTypeFilter] = useState<string>('all')
  const [currentPage, setCurrentPage] = useState(1)
  
  const { data, isLoading, error } = useScenes({
    dataset_id: datasetId,
    review_status: reviewStatusFilter !== 'all' ? reviewStatusFilter : undefined,
    scene_type: sceneTypeFilter !== 'all' ? sceneTypeFilter : undefined,
    page: currentPage,
    limit: 24, // 4x6 grid
  })

  const scenes = data?.items || []
  const totalPages = data ? Math.ceil(data.total / data.limit) : 0

  const filteredScenes = scenes.filter(scene => {
    if (searchQuery) {
      return scene.source.toLowerCase().includes(searchQuery.toLowerCase()) ||
             scene.scene_type?.toLowerCase().includes(searchQuery.toLowerCase()) ||
             scene.dataset_name?.toLowerCase().includes(searchQuery.toLowerCase())
    }
    return true
  })

  const handleSelectAll = () => {
    if (selectedScenes.size === filteredScenes.length) {
      // Deselect all
      onBatchSelect?.([])
    } else {
      // Select all
      onBatchSelect?.(filteredScenes)
    }
  }

  const getConfidenceColor = (confidence?: number) => {
    if (!confidence) return 'text-gray-400'
    if (confidence >= 0.8) return 'text-green-500'
    if (confidence >= 0.6) return 'text-yellow-500'
    return 'text-red-500'
  }

  if (error) {
    return (
      <div className={`flex items-center justify-center p-12 ${className}`}>
        <div className="text-center">
          <XCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">Failed to load scenes</h3>
          {error && (
            <p className="text-sm text-muted-foreground">{error?.message || 'An error occurred'}</p>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className={className}>
      {/* Header Controls */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-4">
          {/* Search */}
          <div className="relative w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search scenes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
            />
          </div>

          {/* Filters */}
          <Select value={reviewStatusFilter} onValueChange={setReviewStatusFilter}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Status" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Status</SelectItem>
              {REVIEW_STATUSES.map(status => (
                <SelectItem key={status.value} value={status.value}>
                  {status.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select value={sceneTypeFilter} onValueChange={setSceneTypeFilter}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Scene Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              {SCENE_TYPES.map(type => (
                <SelectItem key={type} value={type}>
                  {type.replace('_', ' ')}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* View Controls */}
        <div className="flex items-center space-x-2">
          {data && (
            <div className="text-sm text-muted-foreground">
              {filteredScenes.length} of {data.total} scenes
            </div>
          )}
          
          {filteredScenes.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleSelectAll}
            >
              {selectedScenes.size === filteredScenes.length ? 'Deselect All' : 'Select All'}
            </Button>
          )}
          
          <div className="flex border rounded-md">
            <Button
              variant={viewMode === 'grid' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('grid')}
              className="rounded-r-none"
            >
              <Grid className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === 'list' ? 'default' : 'ghost'}
              size="sm"
              onClick={() => setViewMode('list')}
              className="rounded-l-none"
            >
              <List className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center p-12">
          <Loader2 className="h-8 w-8 animate-spin" />
        </div>
      )}

      {/* Empty State */}
      {!isLoading && filteredScenes.length === 0 && (
        <div className="text-center p-12">
          <Eye className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-lg font-semibold mb-2">No scenes found</h3>
          <p className="text-sm text-muted-foreground">
            {searchQuery || reviewStatusFilter !== 'all' || sceneTypeFilter !== 'all'
              ? 'Try adjusting your search criteria.'
              : 'No scenes available for review.'}
          </p>
        </div>
      )}

      {/* Scene Grid */}
      {!isLoading && filteredScenes.length > 0 && (
        <>
          {viewMode === 'grid' ? (
            <SceneGrid
              scenes={filteredScenes}
              selectedScenes={selectedScenes}
              onSceneSelect={onSceneSelect}
              onSceneToggle={onSceneToggle}
            />
          ) : (
            <SceneList
              scenes={filteredScenes}
              selectedScenes={selectedScenes}
              onSceneSelect={onSceneSelect}
              onSceneToggle={onSceneToggle}
            />
          )}

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
                  disabled={currentPage <= 1}
                >
                  <ChevronLeft className="h-4 w-4" />
                  Previous
                </Button>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage >= totalPages}
                >
                  Next
                  <ChevronRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

// Grid View Component
function SceneGrid({ 
  scenes, 
  selectedScenes, 
  onSceneSelect, 
  onSceneToggle 
}: {
  scenes: Scene[]
  selectedScenes: Set<string>
  onSceneSelect?: (scene: Scene) => void
  onSceneToggle?: (sceneId: string) => void
}) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4">
      {scenes.map((scene) => (
        <SceneCard
          key={scene.id}
          scene={scene}
          isSelected={selectedScenes.has(scene.id)}
          onSelect={() => onSceneSelect?.(scene)}
          onToggle={() => onSceneToggle?.(scene.id)}
        />
      ))}
    </div>
  )
}

// List View Component
function SceneList({ 
  scenes, 
  selectedScenes, 
  onSceneSelect, 
  onSceneToggle 
}: {
  scenes: Scene[]
  selectedScenes: Set<string>
  onSceneSelect?: (scene: Scene) => void
  onSceneToggle?: (sceneId: string) => void
}) {
  return (
    <div className="space-y-2">
      {scenes.map((scene) => (
        <SceneListItem
          key={scene.id}
          scene={scene}
          isSelected={selectedScenes.has(scene.id)}
          onSelect={() => onSceneSelect?.(scene)}
          onToggle={() => onSceneToggle?.(scene.id)}
        />
      ))}
    </div>
  )
}

// Scene Card Component
function SceneCard({ 
  scene, 
  isSelected, 
  onSelect, 
  onToggle 
}: {
  scene: Scene
  isSelected: boolean
  onSelect: () => void
  onToggle: () => void
}) {
  const { thumbnailUrl } = useSceneImages(scene)
  const StatusIcon = REVIEW_STATUS_ICONS[scene.review_status as keyof typeof REVIEW_STATUS_ICONS] || Clock
  const statusColor = REVIEW_STATUS_COLORS[scene.review_status as keyof typeof REVIEW_STATUS_COLORS] || 'text-gray-500'

  return (
    <div 
      className={`relative group rounded-lg border-2 transition-colors cursor-pointer ${
        isSelected ? 'border-primary' : 'border-transparent hover:border-muted-foreground'
      }`}
      onClick={onSelect}
    >
      {/* Selection Checkbox */}
      <div className="absolute top-2 left-2 z-10">
        <button
          onClick={(e) => {
            e.stopPropagation()
            onToggle()
          }}
          className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
            isSelected 
              ? 'bg-primary border-primary text-primary-foreground' 
              : 'bg-background border-muted-foreground'
          }`}
        >
          {isSelected && <CheckCircle className="h-3 w-3" />}
        </button>
      </div>

      {/* Status Icon */}
      <div className="absolute top-2 right-2 z-10">
        <StatusIcon className={`h-4 w-4 ${statusColor}`} />
      </div>

      {/* Image */}
      <div className="aspect-[4/3] rounded-t-lg overflow-hidden bg-muted">
        <img
          src={thumbnailUrl}
          alt={scene.source}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform"
          loading="lazy"
        />
      </div>

      {/* Info */}
      <div className="p-3 space-y-2">
        <div className="text-sm font-medium truncate" title={scene.source}>
          {scene.source}
        </div>
        
        <div className="flex items-center justify-between">
          {scene.scene_type && (
            <Badge variant="outline" className="text-xs">
              {scene.scene_type.replace('_', ' ')}
            </Badge>
          )}
          
          {scene.scene_conf && (
            <span className={`text-xs font-mono ${getConfidenceColor(scene.scene_conf)}`}>
              {(scene.scene_conf * 100).toFixed(0)}%
            </span>
          )}
        </div>

        <div className="text-xs text-muted-foreground">
          {scene.objects_count} objects
        </div>
      </div>
    </div>
  )
}

// Scene List Item Component
function SceneListItem({ 
  scene, 
  isSelected, 
  onSelect, 
  onToggle 
}: {
  scene: Scene
  isSelected: boolean
  onSelect: () => void
  onToggle: () => void
}) {
  const { thumbnailUrl } = useSceneImages(scene)
  const StatusIcon = REVIEW_STATUS_ICONS[scene.review_status as keyof typeof REVIEW_STATUS_ICONS] || Clock
  const statusColor = REVIEW_STATUS_COLORS[scene.review_status as keyof typeof REVIEW_STATUS_COLORS] || 'text-gray-500'

  return (
    <div 
      className={`flex items-center space-x-4 p-4 rounded-lg border cursor-pointer transition-colors ${
        isSelected ? 'border-primary bg-primary/5' : 'border-border hover:bg-muted/50'
      }`}
      onClick={onSelect}
    >
      {/* Selection */}
      <button
        onClick={(e) => {
          e.stopPropagation()
          onToggle()
        }}
        className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
          isSelected 
            ? 'bg-primary border-primary text-primary-foreground' 
            : 'bg-background border-muted-foreground'
        }`}
      >
        {isSelected && <CheckCircle className="h-3 w-3" />}
      </button>

      {/* Thumbnail */}
      <div className="w-16 h-12 rounded overflow-hidden bg-muted flex-shrink-0">
        <img
          src={thumbnailUrl}
          alt={scene.source}
          className="w-full h-full object-cover"
          loading="lazy"
        />
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="font-medium truncate">{scene.source}</div>
        <div className="text-sm text-muted-foreground">
          {scene.dataset_name} • {scene.objects_count} objects • {scene.width}×{scene.height}
        </div>
      </div>

      {/* Status & Confidence */}
      <div className="flex items-center space-x-4">
        {scene.scene_type && (
          <Badge variant="outline">
            {scene.scene_type.replace('_', ' ')}
          </Badge>
        )}
        
        {scene.scene_conf && (
          <span className={`text-sm font-mono ${getConfidenceColor(scene.scene_conf)}`}>
            {(scene.scene_conf * 100).toFixed(0)}%
          </span>
        )}

        <StatusIcon className={`h-4 w-4 ${statusColor}`} />
      </div>
    </div>
  )
}

// Utility function for confidence colors
function getConfidenceColor(confidence?: number) {
  if (!confidence) return 'text-gray-400'
  if (confidence >= 0.8) return 'text-green-500'
  if (confidence >= 0.6) return 'text-yellow-500'
  return 'text-red-500'
}