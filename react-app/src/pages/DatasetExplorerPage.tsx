import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Plus, Download, Search, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { DatasetTable } from '@/components/datasets/DatasetTable'
import { DatasetUploadModal } from '@/components/datasets/DatasetUploadModal'
import { HFImportModal } from '@/components/datasets/HFImportModal'
import { useDatasets, useProcessHuggingFaceDataset } from '@/hooks/useDatasets'
import { useToast } from '@/components/ui/use-toast'
import type { Dataset } from '@/types/dataset'

export function DatasetExplorerPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [showImportModal, setShowImportModal] = useState(false)
  const [highlightDatasetId, setHighlightDatasetId] = useState<string | null>(null)
  
  const [searchParams, setSearchParams] = useSearchParams()
  
  const { data, isLoading, error } = useDatasets({
    q: searchQuery || undefined,
    page: currentPage,
    limit: 50,
  })

  const processHuggingFace = useProcessHuggingFaceDataset()
  const navigate = useNavigate()
  const { toast } = useToast()

  const datasets = data?.items || []
  const totalPages = data ? Math.ceil(data.total / data.limit) : 0

  // Handle dataset highlighting from URL parameters
  useEffect(() => {
    const datasetId = searchParams.get('dataset')
    if (datasetId) {
      setHighlightDatasetId(datasetId)
      // Clear the URL parameter after highlighting
      const newSearchParams = new URLSearchParams(searchParams)
      newSearchParams.delete('dataset')
      setSearchParams(newSearchParams, { replace: true })
      
      // Clear highlight after 3 seconds
      const timer = setTimeout(() => {
        setHighlightDatasetId(null)
      }, 3000)
      
      return () => clearTimeout(timer)
    }
  }, [searchParams, setSearchParams])

  const handleSelectDataset = (dataset: Dataset) => {
    console.log('Selected dataset:', dataset)
    // TODO: Navigate to dataset detail view or show dataset info
  }

  const handleViewScenes = (dataset: Dataset) => {
    console.log('View scenes for dataset:', dataset)
    // TODO: Navigate to scenes view for this dataset
  }

  const handleProcessDataset = async (dataset: Dataset) => {
    console.log('Process dataset:', dataset)
    
    if (!dataset.source_url) {
      toast({
        title: "Processing Failed",
        description: "Dataset has no source URL to process",
        variant: "destructive"
      })
      return
    }
    
    try {
      const result = await processHuggingFace.mutateAsync({
        datasetId: dataset.id,
        hfUrl: dataset.source_url,
        options: {
          split: 'train',
          image_column: 'image',
          max_images: 100 // Optional limit for testing
        }
      })
      
      console.log(`Processing started successfully. Job ID: ${result.job_id}`)
      
      toast({
        title: "Processing Started",
        description: `Dataset processing job ${result.job_id} started successfully`,
        variant: "default"
      })
      
      // Navigate to job monitoring page
      navigate('/jobs')
      
    } catch (error) {
      console.error('Failed to start dataset processing:', error)
      
      toast({
        title: "Processing Failed",
        description: error instanceof Error ? error.message : "Failed to start dataset processing",
        variant: "destructive"
      })
    }
  }

  const handleSearch = (query: string) => {
    setSearchQuery(query)
    setCurrentPage(1) // Reset to first page on new search
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        {error && (
          <div className="text-center py-8">
            <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
            <p className="text-lg font-medium text-destructive mb-2">Failed to load datasets</p>
            <p className="text-muted-foreground">
              {error?.message || 'An error occurred while loading datasets'}
            </p>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dataset Explorer</h1>
          <p className="text-muted-foreground mt-1">
            Manage and process your interior scene datasets
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button 
            variant="outline" 
            onClick={() => setShowImportModal(true)}
          >
            <Download className="h-4 w-4 mr-2" />
            Import from HF
          </Button>
          <Button onClick={() => setShowUploadModal(true)}>
            <Plus className="h-4 w-4 mr-2" />
            Upload Dataset
          </Button>
        </div>
      </div>

      {/* Search and Filters */}
      <div className="flex items-center space-x-4 mb-6">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search datasets..."
            value={searchQuery}
            onChange={(e) => handleSearch(e.target.value)}
            className="pl-9"
          />
        </div>
        
        {data && (
          <div className="text-sm text-muted-foreground">
            Showing {data.items.length} of {data.total} dataset{data.total !== 1 ? 's' : ''}
          </div>
        )}
      </div>

      {/* Dataset Table */}
      <DatasetTable
        datasets={datasets}
        loading={isLoading}
        highlightId={highlightDatasetId}
        onSelectDataset={handleSelectDataset}
        onViewScenes={handleViewScenes}
        onProcessDataset={handleProcessDataset}
      />

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-6">
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

      {/* Modals */}
      <DatasetUploadModal
        open={showUploadModal}
        onClose={() => setShowUploadModal(false)}
      />
      
      <HFImportModal
        open={showImportModal}
        onClose={() => setShowImportModal(false)}
      />
    </div>
  )
}