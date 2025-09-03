import { useState } from 'react'
import { 
  Activity,
  Play,
  Clock,
  CheckCircle,
  AlertCircle,
  RefreshCw,
  Zap
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { useToast } from '@/components/ui/use-toast'
import type { Scene } from '@/types/dataset'

interface AIProcessingTriggerProps {
  scene: Scene
  onProcessingComplete?: (sceneId: string) => void
  className?: string
}

type ProcessingStatus = 'idle' | 'processing' | 'completed' | 'error'

export function AIProcessingTrigger({ 
  scene, 
  onProcessingComplete, 
  className 
}: AIProcessingTriggerProps) {
  const [status, setStatus] = useState<ProcessingStatus>('idle')
  const [progress, setProgress] = useState(0)
  const [processingTime, setProcessingTime] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)
  
  const { toast } = useToast()

  // Check if scene needs AI processing
  const needsProcessing = !scene.scene_type || 
                         !scene.objects || 
                         scene.objects.length === 0 || 
                         !scene.styles || 
                         scene.styles.length === 0

  const triggerAIProcessing = async () => {
    setStatus('processing')
    setProgress(0)
    setError(null)
    const startTime = Date.now()

    try {
      // Start the processing job
      const processResponse = await fetch(`/api/v1/scenes/${scene.id}/process`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          force_reprocess: true
        }),
      })

      if (!processResponse.ok) {
        throw new Error(`Processing failed: ${processResponse.statusText}`)
      }

      const processResult = await processResponse.json()
      const jobId = processResult.job_id

      if (!jobId) {
        throw new Error('No job ID returned from processing request')
      }

      // Poll for progress updates
      const pollProgress = async (): Promise<void> => {
        const statusResponse = await fetch(`/api/v1/scenes/${scene.id}/process-status`)
        
        if (!statusResponse.ok) {
          throw new Error('Failed to get processing status')
        }

        const statusData = await statusResponse.json()
        
        // Update progress from real job status
        setProgress(statusData.progress || 0)
        
        if (statusData.status === 'succeeded') {
          setProgress(100)
          const endTime = Date.now()
          setProcessingTime((endTime - startTime) / 1000)
          setStatus('completed')

          // Show success toast
          toast({
            title: "AI Processing Complete!",
            description: `Scene analyzed in ${((endTime - startTime) / 1000).toFixed(1)}s`,
            duration: 5000,
          })

          // Notify parent component
          onProcessingComplete?.(scene.id)

          // Auto-reset after 3 seconds
          setTimeout(() => {
            setStatus('idle')
            setProgress(0)
            setProcessingTime(null)
          }, 3000)
          
        } else if (statusData.status === 'failed') {
          throw new Error(statusData.error || 'Processing failed')
        } else if (statusData.status === 'running' || statusData.status === 'pending') {
          // Continue polling
          setTimeout(pollProgress, 1000)
        }
      }

      // Start polling for progress
      setTimeout(pollProgress, 1000)

    } catch (err) {
      setStatus('error')
      setError(err instanceof Error ? err.message : 'Processing failed')
      
      toast({
        title: "Processing Failed",
        description: "Failed to process scene with AI models",
        variant: "destructive",
        duration: 5000,
      })
    }
  }

  const getStatusIcon = () => {
    switch (status) {
      case 'processing':
        return <RefreshCw className="h-4 w-4 animate-spin" />
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-600" />
      case 'error':
        return <AlertCircle className="h-4 w-4 text-red-600" />
      default:
        return <Activity className="h-4 w-4" />
    }
  }

  const getStatusBadge = () => {
    switch (status) {
      case 'processing':
        return <Badge variant="default" className="animate-pulse">Processing</Badge>
      case 'completed':
        return <Badge variant="secondary">Completed</Badge>
      case 'error':
        return <Badge variant="destructive">Failed</Badge>
      default:
        return needsProcessing 
          ? <Badge variant="outline">Needs Processing</Badge>
          : <Badge variant="secondary">Processed</Badge>
    }
  }

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center justify-between text-base">
          <div className="flex items-center space-x-2">
            {getStatusIcon()}
            <span>AI Processing</span>
          </div>
          {getStatusBadge()}
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {status === 'idle' && (
          <>
            {needsProcessing ? (
              <div className="space-y-3">
                <Alert>
                  <Zap className="h-4 w-4" />
                  <AlertDescription>
                    This scene needs AI analysis to extract comprehensive metadata.
                  </AlertDescription>
                </Alert>

                <Button 
                  onClick={triggerAIProcessing}
                  className="w-full"
                  size="sm"
                >
                  <Play className="h-4 w-4 mr-2" />
                  Run AI Analysis
                </Button>

                <div className="text-xs text-muted-foreground">
                  <p>Will analyze:</p>
                  <ul className="mt-1 space-y-1 list-disc list-inside">
                    <li>Scene type classification</li>
                    <li>Object detection & segmentation</li>
                    <li>Interior design style analysis</li>
                    <li>Material identification</li>
                    <li>Color palette extraction</li>
                    <li>Depth map generation</li>
                  </ul>
                </div>
              </div>
            ) : (
              <div className="text-center py-4">
                <CheckCircle className="h-8 w-8 mx-auto mb-2 text-green-600" />
                <p className="text-sm font-medium">Scene Already Processed</p>
                <p className="text-xs text-muted-foreground mt-1">
                  All AI analysis completed
                </p>
                
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={triggerAIProcessing}
                  className="mt-2"
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Reprocess
                </Button>
              </div>
            )}
          </>
        )}

        {status === 'processing' && (
          <div className="space-y-3">
            <div className="text-center">
              <div className="w-12 h-12 mx-auto mb-3 relative">
                <Activity className="h-12 w-12 text-primary animate-pulse" />
              </div>
              <p className="text-sm font-medium">Processing Scene...</p>
              <p className="text-xs text-muted-foreground">
                Running AI models on RunPod GPU
              </p>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span>Progress</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <Progress value={progress} className="w-full" />
            </div>

            <div className="text-xs text-muted-foreground text-center">
              Expected time: ~2-3 seconds
            </div>
          </div>
        )}

        {status === 'completed' && processingTime && (
          <div className="text-center space-y-2">
            <CheckCircle className="h-8 w-8 mx-auto text-green-600" />
            <div>
              <p className="text-sm font-medium text-green-600">Processing Complete!</p>
              <p className="text-xs text-muted-foreground">
                Completed in {processingTime.toFixed(1)}s
              </p>
            </div>
            <Badge variant="secondary" className="text-xs">
              <Clock className="h-3 w-3 mr-1" />
              Fast Processing
            </Badge>
          </div>
        )}

        {status === 'error' && error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription className="text-sm">
              {error}
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  )
}