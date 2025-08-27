import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, X, FileImage, AlertCircle, CheckCircle } from 'lucide-react'
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
import { Progress } from '@/components/ui/progress'
import { Badge } from '@/components/ui/badge'
import { useUploadDataset } from '@/hooks/useDatasets'
import type { DatasetCreate } from '@/types/dataset'

interface DatasetUploadModalProps {
  open: boolean
  onClose: () => void
}

interface FileWithStatus extends File {
  id: string
  status: 'pending' | 'uploading' | 'success' | 'error'
  error?: string
}

export function DatasetUploadModal({ open, onClose }: DatasetUploadModalProps) {
  const [files, setFiles] = useState<FileWithStatus[]>([])
  const [formData, setFormData] = useState<DatasetCreate>({
    name: '',
    version: 'v1.0',
    license: 'CC BY 4.0',
    notes: '',
  })
  
  const uploadMutation = useUploadDataset()

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: FileWithStatus[] = acceptedFiles.map(file => ({
      ...file,
      id: `${file.name}-${Date.now()}-${Math.random()}`,
      status: 'pending' as const,
    }))
    
    setFiles(prev => [...prev, ...newFiles])
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpg', '.jpeg', '.png', '.webp']
    },
    multiple: true,
  })

  const removeFile = (fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId))
  }

  const handleSubmit = async () => {
    if (!formData.name.trim() || files.length === 0) return
    
    try {
      // Update file statuses to uploading
      setFiles(prev => prev.map(f => ({ ...f, status: 'uploading' as const })))
      
      const actualFiles = files.map(f => {
        // Create a new File object without the extra properties
        return new File([f], f.name, { type: f.type, lastModified: f.lastModified })
      })
      
      await uploadMutation.mutateAsync({
        dataset: formData,
        files: actualFiles,
      })
      
      // Update file statuses to success
      setFiles(prev => prev.map(f => ({ ...f, status: 'success' as const })))
      
      // Close modal after short delay to show success
      setTimeout(() => {
        onClose()
        resetForm()
      }, 1000)
      
    } catch (error) {
      // Update file statuses to error
      setFiles(prev => prev.map(f => ({ 
        ...f, 
        status: 'error' as const,
        error: error instanceof Error ? error.message : 'Upload failed'
      })))
    }
  }

  const resetForm = () => {
    setFiles([])
    setFormData({
      name: '',
      version: 'v1.0',
      license: 'CC BY 4.0',
      notes: '',
    })
  }

  const handleClose = () => {
    if (uploadMutation.isPending) return // Prevent closing during upload
    onClose()
    resetForm()
  }

  const isUploading = uploadMutation.isPending
  const canSubmit = formData.name.trim() && files.length > 0 && !isUploading

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Upload Dataset</DialogTitle>
          <DialogDescription>
            Upload images from your local machine to create a new dataset.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Dataset Metadata Form */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="name">Dataset Name *</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Living Rooms v2"
                disabled={isUploading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="version">Version</Label>
              <Input
                id="version"
                value={formData.version}
                onChange={(e) => setFormData(prev => ({ ...prev, version: e.target.value }))}
                placeholder="v1.0"
                disabled={isUploading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="license">License</Label>
              <Input
                id="license"
                value={formData.license}
                onChange={(e) => setFormData(prev => ({ ...prev, license: e.target.value }))}
                placeholder="CC BY 4.0"
                disabled={isUploading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="notes">Notes (optional)</Label>
              <Input
                id="notes"
                value={formData.notes}
                onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
                placeholder="Internal test dataset"
                disabled={isUploading}
              />
            </div>
          </div>

          {/* File Upload Area */}
          <div className="space-y-4">
            <div
              {...getRootProps()}
              className={`
                border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
                transition-colors hover:bg-muted/50
                ${isDragActive ? 'border-primary bg-primary/10' : 'border-muted-foreground/25'}
                ${isUploading ? 'pointer-events-none opacity-50' : ''}
              `}
            >
              <input {...getInputProps()} />
              <Upload className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
              {isDragActive ? (
                <p className="text-lg font-medium">Drop the images here...</p>
              ) : (
                <>
                  <p className="text-lg font-medium mb-2">
                    Drag & drop images here, or click to select
                  </p>
                  <p className="text-sm text-muted-foreground">
                    Supports JPG, PNG, WebP formats
                  </p>
                </>
              )}
            </div>

            {/* File List */}
            {files.length > 0 && (
              <div className="space-y-2 max-h-48 overflow-y-auto">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">
                    {files.length} file{files.length !== 1 ? 's' : ''} selected
                  </span>
                  {isUploading && (
                    <Progress 
                      value={75} // Mock progress - in production, track actual progress
                      className="w-24"
                    />
                  )}
                </div>
                
                {files.map((file) => (
                  <div key={file.id} className="flex items-center space-x-3 p-2 bg-muted rounded-md">
                    <FileImage className="h-4 w-4 text-muted-foreground" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">{file.name}</p>
                      <p className="text-xs text-muted-foreground">
                        {(file.size / 1024 / 1024).toFixed(1)} MB
                      </p>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {file.status === 'pending' && (
                        <Badge variant="outline">Ready</Badge>
                      )}
                      {file.status === 'uploading' && (
                        <Badge variant="default">Uploading...</Badge>
                      )}
                      {file.status === 'success' && (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      )}
                      {file.status === 'error' && (
                        <AlertCircle className="h-4 w-4 text-red-500" />
                      )}
                      
                      {!isUploading && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeFile(file.id)}
                        >
                          <X className="h-3 w-3" />
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Error Display */}
          {uploadMutation.error && (
            <div className="bg-destructive/10 border border-destructive/20 rounded-md p-3">
              <div className="flex items-center space-x-2">
                <AlertCircle className="h-4 w-4 text-destructive" />
                <span className="text-sm text-destructive">
                  {uploadMutation.error.message}
                </span>
              </div>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleClose} disabled={isUploading}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={!canSubmit}>
            {isUploading ? 'Uploading...' : `Upload ${files.length} file${files.length !== 1 ? 's' : ''}`}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}