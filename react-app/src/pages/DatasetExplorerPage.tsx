import { useState } from 'react'
import { Plus, Download, Search } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { DatasetTable } from '@/components/datasets/DatasetTable'
import { DatasetUploadModal } from '@/components/datasets/DatasetUploadModal'
import { HFImportModal } from '@/components/datasets/HFImportModal'
import { useDatasets } from '@/hooks/useDatasets'
import type { Dataset } from '@/types/dataset'

export function DatasetExplorerPage() {
  const [searchQuery, setSearchQuery] = useState('')
  const [currentPage, setCurrentPage] = useState(1)
  const [showUploadModal, setShowUploadModal] = useState(false)
  const [showImportModal, setShowImportModal] = useState(false)
  
  const { data, isLoading, error } = useDatasets({
    q: searchQuery || undefined,
    page: currentPage,
    limit: 50,
  })

  const datasets = data?.items || []
  const totalPages = data ? Math.ceil(data.total / data.limit) : 0

  const handleSelectDataset = (dataset: Dataset) => {
    console.log('Selected dataset:', dataset)
    // TODO: Navigate to dataset detail view or show dataset info
  }

  const handleViewScenes = (dataset: Dataset) => {
    console.log('View scenes for dataset:', dataset)
    // TODO: Navigate to scenes view for this dataset
  }

  const handleProcessDataset = (dataset: Dataset) => {
    console.log('Process dataset:', dataset)
    // TODO: Start processing job for this dataset
  }

  const handleSearch = (query: string) => {
    setSearchQuery(query)
    setCurrentPage(1) // Reset to first page on new search
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <h3 className="text-lg font-semibold text-destructive mb-2">
            Failed to load datasets
          </h3>
          <p className="text-sm text-muted-foreground mb-4">
            {error.message}
          </p>
          <Button onClick={() => window.location.reload()}>
            Retry
          </Button>
        </div>
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