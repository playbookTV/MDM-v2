import { useState } from 'react'
import { ExternalLink, AlertCircle, CheckCircle, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useCreateDataset } from '@/hooks/useDatasets'
import type { DatasetCreate } from '@/types/dataset'

interface HFImportModalProps {
  open: boolean
  onClose: () => void
}

const HF_URL_PATTERN = /^https:\/\/huggingface\.co\/datasets\/[\w-]+\/[\w-]+(?:\/.*)?$/

export function HFImportModal({ open, onClose }: HFImportModalProps) {
  const [formData, setFormData] = useState<DatasetCreate & { source_url: string }>({
    name: '',
    version: 'v1.0',
    source_url: '',
    license: '',
    notes: '',
  })
  const [urlError, setUrlError] = useState<string | null>(null)
  const [isValidating, setIsValidating] = useState(false)
  
  const createMutation = useCreateDataset()

  const validateHuggingFaceUrl = async (url: string) => {
    if (!url) {
      setUrlError(null)
      return false
    }

    if (!HF_URL_PATTERN.test(url)) {
      setUrlError('Please enter a valid HuggingFace dataset URL')
      return false
    }

    setIsValidating(true)
    setUrlError(null)

    try {
      // Extract dataset name from URL for pre-filling form
      const urlMatch = url.match(/datasets\/([\w-]+)\/([\w-]+)/)
      if (urlMatch) {
        const [, org, datasetName] = urlMatch
        setFormData(prev => ({
          ...prev,
          name: prev.name || `${org}/${datasetName}`,
        }))
      }

      // In a real implementation, you might want to validate the URL
      // by checking if it exists or fetching metadata
      // For now, we'll just validate the URL format
      setIsValidating(false)
      return true
    } catch (error) {
      setUrlError('Failed to validate dataset URL')
      setIsValidating(false)
      return false
    }
  }

  const handleUrlChange = (url: string) => {
    setFormData(prev => ({ ...prev, source_url: url }))
    
    // Debounce URL validation
    const timeoutId = setTimeout(() => {
      validateHuggingFaceUrl(url)
    }, 500)

    return () => clearTimeout(timeoutId)
  }

  const handleSubmit = async () => {
    if (!formData.name.trim() || !formData.source_url.trim()) return
    
    const isValidUrl = await validateHuggingFaceUrl(formData.source_url)
    if (!isValidUrl) return

    try {
      await createMutation.mutateAsync({
        name: formData.name,
        version: formData.version,
        source_url: formData.source_url,
        license: formData.license || undefined,
        notes: formData.notes || undefined,
      })
      
      onClose()
      resetForm()
    } catch (error) {
      // Error is handled by the mutation
    }
  }

  const resetForm = () => {
    setFormData({
      name: '',
      version: 'v1.0',
      source_url: '',
      license: '',
      notes: '',
    })
    setUrlError(null)
    setIsValidating(false)
  }

  const handleClose = () => {
    if (createMutation.isPending) return
    onClose()
    resetForm()
  }

  const canSubmit = formData.name.trim() && 
                   formData.source_url.trim() && 
                   !urlError && 
                   !isValidating && 
                   !createMutation.isPending

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-lg">
        <div>
          <DialogHeader>
            <DialogTitle>Import from HuggingFace</DialogTitle>
            <DialogDescription>
              Import a dataset directly from HuggingFace Hub.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
          {/* HuggingFace URL */}
          <div className="space-y-2">
            <Label htmlFor="hf-url">HuggingFace Dataset URL *</Label>
            <div className="relative">
              <Input
                id="hf-url"
                value={formData.source_url}
                onChange={(e) => handleUrlChange(e.target.value)}
                placeholder="https://huggingface.co/datasets/username/dataset-name"
                disabled={createMutation.isPending}
                className={urlError ? 'border-destructive' : ''}
              />
              <div className="absolute right-3 top-1/2 -translate-y-1/2">
                {isValidating && <Loader2 className="h-4 w-4 animate-spin" />}
                {!isValidating && formData.source_url && !urlError && (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                )}
              </div>
            </div>
            {urlError && (
              <div className="flex items-center space-x-1 text-sm text-destructive">
                <AlertCircle className="h-3 w-3" />
                <span>{urlError}</span>
              </div>
            )}
            <p className="text-xs text-muted-foreground flex items-center space-x-1">
              <ExternalLink className="h-3 w-3" />
              <span>Browse datasets at huggingface.co/datasets</span>
            </p>
          </div>

          {/* Dataset Metadata */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name">Dataset Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="living-rooms-hf"
                disabled={createMutation.isPending}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="version">Version</Label>
              <Input
                id="version"
                value={formData.version}
                onChange={(e) => setFormData(prev => ({ ...prev, version: e.target.value }))}
                placeholder="v1.0"
                disabled={createMutation.isPending}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="license">License (optional)</Label>
            <Input
              id="license"
              value={formData.license}
              onChange={(e) => setFormData(prev => ({ ...prev, license: e.target.value }))}
              placeholder="Will be auto-detected from HuggingFace"
              disabled={createMutation.isPending}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="notes">Notes (optional)</Label>
            <Input
              id="notes"
              value={formData.notes}
              onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
              placeholder="Imported from HuggingFace"
              disabled={createMutation.isPending}
            />
          </div>

          {/* Info Box */}
          <div className="bg-muted p-3 rounded-md">
            <p className="text-sm text-muted-foreground">
              <strong>Note:</strong> After importing, you'll need to run a processing job 
              to download and analyze the images from HuggingFace.
            </p>
          </div>

          {/* Error Display */}
          {createMutation.error && (
            <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3">
              <div className="flex items-center space-x-2">
                <AlertCircle className="h-4 w-4 text-destructive" />
                <span className="text-sm text-destructive">
                  {(createMutation.error as Error)?.message || 'An error occurred during import'}
                </span>
              </div>
            </div>
          )}
        </div>

          <DialogFooter>
            <Button variant="outline" onClick={handleClose} disabled={createMutation.isPending}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} disabled={!canSubmit}>
              {createMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Importing...
                </>
              ) : (
                'Import Dataset'
              )}
            </Button>
          </DialogFooter>
        </div>
      </DialogContent>
    </Dialog>
  )
}