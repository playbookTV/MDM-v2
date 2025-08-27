import { useState, useEffect } from 'react'
import { Play, Settings, Database, AlertCircle, Loader2 } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { useDatasets } from '@/hooks/useDatasets'
import { useCreateJob } from '@/hooks/useJobs'
import type { JobCreate, JobConfig, Dataset } from '@/types/dataset'

interface StartJobModalProps {
  open: boolean
  onClose: () => void
  preselectedDataset?: Dataset
}

const JOB_KINDS = [
  {
    value: 'ingest' as const,
    label: 'Data Ingestion',
    description: 'Download and prepare images from HuggingFace datasets'
  },
  {
    value: 'process' as const,
    label: 'AI Processing',
    description: 'Run scene analysis, object detection, and AI models on images'
  }
]

const DEFAULT_CONFIG: JobConfig = {
  scene_classifier_threshold: 0.5,
  style_classifier_threshold: 0.35,
  object_detector_threshold: 0.5,
  material_detector_threshold: 0.35,
  force_reprocess: false
}

export function StartJobModal({ open, onClose, preselectedDataset }: StartJobModalProps) {
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>('')
  const [jobKind, setJobKind] = useState<'ingest' | 'process'>('process')
  const [config, setConfig] = useState<JobConfig>(DEFAULT_CONFIG)
  const [showAdvanced, setShowAdvanced] = useState(false)

  const { data: datasetsPage } = useDatasets({ limit: 100 })
  const createJobMutation = useCreateJob()

  const datasets = datasetsPage?.items || []
  const selectedDataset = datasets.find(d => d.id === selectedDatasetId)

  // Set preselected dataset when modal opens
  useEffect(() => {
    if (preselectedDataset && open) {
      setSelectedDatasetId(preselectedDataset.id)
    }
  }, [preselectedDataset, open])

  const handleSubmit = async () => {
    if (!selectedDatasetId) return

    const jobData: JobCreate = {
      kind: jobKind,
      dataset_id: selectedDatasetId,
      config: showAdvanced ? config : undefined
    }

    try {
      await createJobMutation.mutateAsync(jobData)
      handleClose()
    } catch (error) {
      // Error handled by mutation
    }
  }

  const handleClose = () => {
    if (createJobMutation.isPending) return
    onClose()
    resetForm()
  }

  const resetForm = () => {
    setSelectedDatasetId(preselectedDataset?.id || '')
    setJobKind('process')
    setConfig(DEFAULT_CONFIG)
    setShowAdvanced(false)
  }

  const canSubmit = selectedDatasetId && !createJobMutation.isPending

  const getJobKindRecommendation = (dataset: Dataset) => {
    if (dataset.source_url) {
      return {
        recommended: 'ingest' as const,
        reason: 'HuggingFace dataset requires ingestion first'
      }
    }
    return {
      recommended: 'process' as const,
      reason: 'Local dataset ready for AI processing'
    }
  }

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Start Processing Job</DialogTitle>
          <DialogDescription>
            Configure and launch a dataset processing job.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Dataset Selection */}
          <div className="space-y-2">
            <Label htmlFor="dataset">Select Dataset *</Label>
            <Select 
              value={selectedDatasetId} 
              onValueChange={setSelectedDatasetId}
              disabled={createJobMutation.isPending}
            >
              <SelectTrigger>
                <SelectValue placeholder="Choose a dataset to process" />
              </SelectTrigger>
              <SelectContent>
                {datasets.map((dataset) => (
                  <SelectItem key={dataset.id} value={dataset.id}>
                    <div className="flex items-center justify-between w-full">
                      <div>
                        <div className="font-medium">{dataset.name}</div>
                        <div className="text-xs text-muted-foreground">
                          {dataset.source_url ? 'HuggingFace' : 'Local'} • {dataset.version}
                        </div>
                      </div>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            {selectedDataset && (
              <div className="text-sm text-muted-foreground">
                <Database className="inline h-3 w-3 mr-1" />
                {selectedDataset.source_url ? 'Remote dataset' : 'Local dataset'} • 
                Last updated {new Date(selectedDataset.created_at).toLocaleDateString()}
              </div>
            )}
          </div>

          {/* Job Type Selection */}
          <div className="space-y-3">
            <Label>Job Type *</Label>
            <div className="grid gap-3">
              {JOB_KINDS.map((kind) => {
                const isRecommended = selectedDataset && 
                  getJobKindRecommendation(selectedDataset).recommended === kind.value

                return (
                  <div
                    key={kind.value}
                    className={`relative rounded-lg border p-4 cursor-pointer transition-colors ${
                      jobKind === kind.value 
                        ? 'border-primary bg-primary/5' 
                        : 'border-border hover:bg-muted/50'
                    }`}
                    onClick={() => setJobKind(kind.value)}
                  >
                    <div className="flex items-start space-x-3">
                      <div className={`mt-0.5 rounded-full w-4 h-4 border-2 flex items-center justify-center ${
                        jobKind === kind.value 
                          ? 'border-primary bg-primary' 
                          : 'border-border'
                      }`}>
                        {jobKind === kind.value && (
                          <div className="w-2 h-2 rounded-full bg-background" />
                        )}
                      </div>
                      
                      <div className="flex-1">
                        <div className="flex items-center space-x-2">
                          <span className="font-medium">{kind.label}</span>
                          {isRecommended && (
                            <Badge variant="default" className="text-xs">
                              Recommended
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-muted-foreground mt-1">
                          {kind.description}
                        </p>
                        
                        {isRecommended && selectedDataset && (
                          <p className="text-xs text-primary mt-2">
                            {getJobKindRecommendation(selectedDataset).reason}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>

          {/* Advanced Configuration */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label>Advanced Configuration</Label>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowAdvanced(!showAdvanced)}
              >
                <Settings className="h-4 w-4 mr-1" />
                {showAdvanced ? 'Hide' : 'Show'} Advanced
              </Button>
            </div>

            {showAdvanced && jobKind === 'process' && (
              <div className="space-y-4 p-4 bg-muted/50 rounded-lg">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label className="text-sm">Scene Classifier Threshold</Label>
                    <Select
                      value={config.scene_classifier_threshold?.toString()}
                      onValueChange={(value) => 
                        setConfig(prev => ({ ...prev, scene_classifier_threshold: parseFloat(value) }))
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="0.3">0.3 (Permissive)</SelectItem>
                        <SelectItem value="0.5">0.5 (Balanced)</SelectItem>
                        <SelectItem value="0.7">0.7 (Conservative)</SelectItem>
                        <SelectItem value="0.9">0.9 (Strict)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label className="text-sm">Object Detector Threshold</Label>
                    <Select
                      value={config.object_detector_threshold?.toString()}
                      onValueChange={(value) => 
                        setConfig(prev => ({ ...prev, object_detector_threshold: parseFloat(value) }))
                      }
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="0.3">0.3 (Permissive)</SelectItem>
                        <SelectItem value="0.5">0.5 (Balanced)</SelectItem>
                        <SelectItem value="0.7">0.7 (Conservative)</SelectItem>
                        <SelectItem value="0.9">0.9 (Strict)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    id="force-reprocess"
                    checked={config.force_reprocess}
                    onChange={(e) => 
                      setConfig(prev => ({ ...prev, force_reprocess: e.target.checked }))
                    }
                    className="rounded border-border"
                  />
                  <Label htmlFor="force-reprocess" className="text-sm">
                    Force reprocess (override existing results)
                  </Label>
                </div>
              </div>
            )}
          </div>

          {/* Error Display */}
          {createJobMutation.error && (
            <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3">
              <div className="flex items-center space-x-2">
                <AlertCircle className="h-4 w-4 text-destructive" />
                <span className="text-sm text-destructive">
                  {createJobMutation.error.message}
                </span>
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={createJobMutation.isPending}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!canSubmit}>
            {createJobMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Starting Job...
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" />
                Start {JOB_KINDS.find(k => k.value === jobKind)?.label}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}