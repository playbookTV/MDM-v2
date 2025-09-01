import { useState, useEffect } from 'react'
import { 
  Eye, 
  Grid, 
  BarChart3,
  Filter,
  RefreshCw,
  ArrowLeft,
  Settings,
  Play,
  Pause
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { SceneGallery } from '@/components/review/SceneGallery'
import { SceneDetailView } from '@/components/review/SceneDetailView'
import { AnnotationTools } from '@/components/review/AnnotationTools'
import { AIAnalysisPanel } from '@/components/review/AIAnalysisPanel'
import { ReviewProgress } from '@/components/review/ReviewProgress'
import { BatchActions } from '@/components/review/BatchActions'
import { useScenePagination } from '@/hooks/useScenes'
import { useReviewSession } from '@/hooks/useReviews'
import { useDatasets } from '@/hooks/useDatasets'
import type { Scene, SceneObject } from '@/types/dataset'

type ViewMode = 'gallery' | 'detail'

export function SceneReviewPage() {
  const [viewMode, setViewMode] = useState<ViewMode>('gallery')
  const [selectedScenes, setSelectedScenes] = useState<Set<string>>(new Set())
  const [currentScene, setCurrentScene] = useState<Scene | null>(null)
  const [selectedObject, setSelectedObject] = useState<SceneObject | null>(null)
  const [datasetFilter, setDatasetFilter] = useState<string>('all')
  const [statusFilter, setStatusFilter] = useState<string>('pending')
  const [isSessionActive, setIsSessionActive] = useState(false)

  // Fetch datasets for filter
  const { data: datasetsData } = useDatasets({ limit: 100 })
  const datasets = datasetsData?.items || []

  // Fetch scenes with pagination
  const {
    scenes,
    isLoading,
    error,
    getNextScene,
    getPreviousScene,
    getSceneIndex
  } = useScenePagination({
    dataset_id: datasetFilter !== 'all' ? datasetFilter : undefined,
    review_status: statusFilter !== 'all' ? statusFilter : undefined,
    limit: 50
  })

  // Review session management
  const { startSession, endSession } = useReviewSession()

  // Start/end review session
  const handleToggleSession = async () => {
    if (isSessionActive) {
      // End current session
      const session = localStorage.getItem('currentReviewSession')
      if (session) {
        await endSession.mutateAsync(JSON.parse(session).id)
        localStorage.removeItem('currentReviewSession')
      }
      setIsSessionActive(false)
    } else {
      // Start new session
      const session = await startSession.mutateAsync({
        dataset_id: datasetFilter !== 'all' ? datasetFilter : undefined
      })
      localStorage.setItem('currentReviewSession', JSON.stringify(session))
      setIsSessionActive(true)
    }
  }

  // Check for active session on load
  useEffect(() => {
    const session = localStorage.getItem('currentReviewSession')
    setIsSessionActive(!!session)
  }, [])

  const handleSceneSelect = (scene: Scene) => {
    setCurrentScene(scene)
    setViewMode('detail')
    setSelectedObject(null)
  }

  const handleSceneToggle = (sceneId: string) => {
    setSelectedScenes(prev => {
      const newSet = new Set(prev)
      if (newSet.has(sceneId)) {
        newSet.delete(sceneId)
      } else {
        newSet.add(sceneId)
      }
      return newSet
    })
  }

  const handleBatchSelect = (scenes: Scene[]) => {
    setSelectedScenes(new Set(scenes.map(s => s.id)))
  }

  const handleClearSelection = () => {
    setSelectedScenes(new Set())
  }

  const handleNextScene = () => {
    if (!currentScene) return
    const nextScene = getNextScene(currentScene.id)
    if (nextScene) {
      setCurrentScene(nextScene)
      setSelectedObject(null)
    }
  }

  const handlePreviousScene = () => {
    if (!currentScene) return
    const prevScene = getPreviousScene(currentScene.id)
    if (prevScene) {
      setCurrentScene(prevScene)
      setSelectedObject(null)
    }
  }

  const handleCloseDetail = () => {
    setViewMode('gallery')
    setCurrentScene(null)
    setSelectedObject(null)
  }

  const getCurrentSceneIndex = () => {
    if (!currentScene) return -1
    return getSceneIndex(currentScene.id)
  }

  const getNextSceneId = () => {
    if (!currentScene) return undefined
    const nextScene = getNextScene(currentScene.id)
    return nextScene?.id
  }

  const getPreviousSceneId = () => {
    if (!currentScene) return undefined
    const prevScene = getPreviousScene(currentScene.id)
    return prevScene?.id
  }

  const selectedScenesList = scenes.filter(scene => selectedScenes.has(scene.id))

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <div className="border-b bg-card">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div>
                <h1 className="text-2xl font-bold tracking-tight">Scene Review</h1>
                <p className="text-sm text-muted-foreground">
                  Human-in-the-loop quality control for AI predictions
                </p>
              </div>
              
              {viewMode === 'detail' && currentScene && (
                <div className="flex items-center space-x-2">
                  <Button variant="ghost" size="sm" onClick={handleCloseDetail}>
                    <ArrowLeft className="h-4 w-4 mr-2" />
                    Back to Gallery
                  </Button>
                  <Badge variant="outline">
                    Scene {getCurrentSceneIndex() + 1} of {scenes.length}
                  </Badge>
                </div>
              )}
            </div>

            <div className="flex items-center space-x-2">
              {/* Session Control */}
              <Button
                variant={isSessionActive ? "destructive" : "default"}
                size="sm"
                onClick={handleToggleSession}
                disabled={startSession.isPending || endSession.isPending}
              >
                {isSessionActive ? (
                  <>
                    <Pause className="h-4 w-4 mr-2" />
                    End Session
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" />
                    Start Session
                  </>
                )}
              </Button>

              {/* Filters */}
              <Select value={datasetFilter} onValueChange={setDatasetFilter}>
                <SelectTrigger className="w-48">
                  <SelectValue placeholder="All Datasets" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Datasets</SelectItem>
                  {datasets.map(dataset => (
                    <SelectItem key={dataset.id} value={dataset.id}>
                      {dataset.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-40">
                  <SelectValue placeholder="Status" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="approved">Approved</SelectItem>
                  <SelectItem value="rejected">Rejected</SelectItem>
                  <SelectItem value="corrected">Corrected</SelectItem>
                </SelectContent>
              </Select>

              {/* View Mode */}
              <div className="flex border rounded-md">
                <Button
                  variant={viewMode === 'gallery' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => setViewMode('gallery')}
                  className="rounded-r-none"
                >
                  <Grid className="h-4 w-4" />
                </Button>
                <Button
                  variant={viewMode === 'detail' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => currentScene && setViewMode('detail')}
                  className="rounded-l-none"
                  disabled={!currentScene}
                >
                  <Eye className="h-4 w-4" />
                </Button>
              </div>

              <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
                <RefreshCw className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-6">
        {viewMode === 'gallery' ? (
          <div className="space-y-6">
            {/* Progress Overview */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <ReviewProgress
                  datasetId={datasetFilter !== 'all' ? datasetFilter : undefined}
                />
              </div>
              <div className="space-y-4">
                <div className="bg-card border rounded-lg p-4">
                  <h3 className="font-medium mb-2">Quick Stats</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span>Total Scenes:</span>
                      <span className="font-mono">{scenes.length}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Selected:</span>
                      <span className="font-mono">{selectedScenes.size}</span>
                    </div>
                    {isSessionActive && (
                      <div className="flex justify-between text-green-600">
                        <span>Session Active:</span>
                        <Badge variant="default" className="text-xs">
                          Recording
                        </Badge>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Batch Actions */}
            {selectedScenes.size > 0 && (
              <BatchActions
                selectedScenes={selectedScenesList}
                onClearSelection={handleClearSelection}
              />
            )}

            {/* Scene Gallery */}
            <SceneGallery
              datasetId={datasetFilter !== 'all' ? datasetFilter : undefined}
              selectedScenes={selectedScenes}
              onSceneSelect={handleSceneSelect}
              onSceneToggle={handleSceneToggle}
              onBatchSelect={handleBatchSelect}
            />
          </div>
        ) : (
          currentScene && (
            <div className="grid grid-cols-1 xl:grid-cols-5 gap-6">
              {/* Scene Detail View */}
              <div className="xl:col-span-3">
                <SceneDetailView
                  sceneId={currentScene.id}
                  onNext={handleNextScene}
                  onPrevious={handlePreviousScene}
                  onClose={handleCloseDetail}
                  selectedObject={selectedObject}
                  onObjectSelect={setSelectedObject}
                  nextSceneId={getNextSceneId()}
                  previousSceneId={getPreviousSceneId()}
                  className="h-[calc(100vh-200px)]"
                />
              </div>

              {/* AI Analysis Panel */}
              <div className="xl:col-span-1">
                <AIAnalysisPanel
                  scene={currentScene}
                  selectedObject={selectedObject}
                  onObjectSelect={setSelectedObject}
                  className="max-h-[calc(100vh-200px)] overflow-y-auto"
                />
              </div>

              {/* Annotation Tools Sidebar */}
              <div className="xl:col-span-1 space-y-4">
                <AnnotationTools
                  scene={currentScene}
                  selectedObject={selectedObject}
                  onObjectSelect={setSelectedObject}
                />

                {/* Mini Progress */}
                <div className="bg-card border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Progress</span>
                    <Badge variant="outline" className="text-xs">
                      {getCurrentSceneIndex() + 1} / {scenes.length}
                    </Badge>
                  </div>
                  <div className="w-full bg-muted rounded-full h-2">
                    <div 
                      className="bg-primary h-2 rounded-full transition-all"
                      style={{ 
                        width: `${((getCurrentSceneIndex() + 1) / scenes.length) * 100}%` 
                      }}
                    />
                  </div>
                  <div className="text-xs text-muted-foreground mt-1">
                    {Math.round(((getCurrentSceneIndex() + 1) / scenes.length) * 100)}% complete
                  </div>
                </div>

                {/* Navigation Help */}
                <div className="bg-muted/50 rounded-lg p-3">
                  <h4 className="text-xs font-medium mb-2">Keyboard Shortcuts</h4>
                  <div className="space-y-1 text-xs text-muted-foreground">
                    <div>← → Arrow keys: Navigate</div>
                    <div>A: Approve scene</div>
                    <div>R: Reject scene</div>
                    <div>Esc: Close detail view</div>
                    <div>Space: Next scene</div>
                  </div>
                </div>
              </div>
            </div>
          )
        )}
        {error && (
          <p className="text-sm text-muted-foreground">{error?.message || 'An error occurred'}</p>
        )}
      </div>
    </div>
  )
}