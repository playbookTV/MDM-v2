import { useState } from 'react'
import { 
  Mountain, 
  Eye, 
  EyeOff, 
  RotateCw,
  Layers,
  Settings,
  Info
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'
import { useSceneImages } from '@/hooks/useScenes'
import type { Scene } from '@/types/dataset'

interface DepthMapViewerProps {
  scene: Scene
  isVisible: boolean
  onToggle: () => void
  className?: string
}

export function DepthMapViewer({ 
  scene, 
  isVisible, 
  onToggle, 
  className 
}: DepthMapViewerProps) {
  const [opacity, setOpacity] = useState([0.7])
  const [colorMode, setColorMode] = useState<'grayscale' | 'heatmap'>('heatmap')
  const [showOriginal, setShowOriginal] = useState(true)

  const { originalUrl, depthUrl } = useSceneImages(scene)

  if (!scene.has_depth) {
    return (
      <Card className={className}>
        <CardContent className="pt-6">
          <div className="text-center py-8 text-muted-foreground">
            <Mountain className="h-12 w-12 mx-auto mb-4 opacity-50" />
            <h3 className="text-lg font-semibold mb-2">No Depth Data</h3>
            <p className="text-sm">
              This scene doesn't have depth map data available.
            </p>
          </div>
        </CardContent>
      </Card>
    )
  }

  const toggleColorMode = () => {
    setColorMode(current => current === 'grayscale' ? 'heatmap' : 'grayscale')
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Mountain className="h-5 w-5" />
            <span>Depth Map Analysis</span>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant="secondary" className="text-xs">
              3D Spatial
            </Badge>
            <Button
              variant="ghost"
              size="sm"
              onClick={onToggle}
            >
              {isVisible ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </Button>
          </div>
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {isVisible && (
          <>
            {/* Depth Map Display */}
            <div className="relative rounded-lg overflow-hidden border">
              <div className="relative">
                {/* Original Image (Background) */}
                {showOriginal && (
                  <img
                    src={originalUrl}
                    alt="Original scene"
                    className="w-full h-auto"
                  />
                )}
                
                {/* Depth Map Overlay */}
                {depthUrl && (
                  <img
                    src={depthUrl}
                    alt="Depth map"
                    className={`absolute top-0 left-0 w-full h-full object-cover transition-opacity ${
                      colorMode === 'heatmap' ? 'depth-heatmap' : 'depth-grayscale'
                    }`}
                    style={{ 
                      opacity: opacity[0],
                      mixBlendMode: showOriginal ? 'multiply' : 'normal'
                    }}
                  />
                )}
                
                {/* Depth Legend */}
                <div className="absolute top-2 right-2 bg-background/90 backdrop-blur-sm rounded-lg p-2">
                  <div className="text-xs font-medium mb-1">Depth</div>
                  <div className="flex items-center space-x-2 text-xs">
                    <div className="flex items-center space-x-1">
                      <div className="w-3 h-3 bg-blue-600 rounded-sm" />
                      <span>Near</span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <div className="w-3 h-3 bg-red-600 rounded-sm" />
                      <span>Far</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Controls */}
            <div className="space-y-4">
              {/* Opacity Control */}
              <div className="space-y-2">
                <Label className="text-xs font-medium flex items-center">
                  <Layers className="h-3 w-3 mr-1" />
                  Depth Map Opacity
                </Label>
                <Slider
                  value={opacity}
                  onValueChange={setOpacity}
                  max={1}
                  min={0}
                  step={0.1}
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Transparent</span>
                  <span>{Math.round(opacity[0] * 100)}%</span>
                  <span>Opaque</span>
                </div>
              </div>

              {/* Display Options */}
              <div className="grid grid-cols-2 gap-3">
                <div className="flex items-center space-x-2">
                  <Switch
                    id="show-original"
                    checked={showOriginal}
                    onCheckedChange={setShowOriginal}
                  />
                  <Label htmlFor="show-original" className="text-xs">
                    Show Original
                  </Label>
                </div>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={toggleColorMode}
                  className="text-xs"
                >
                  <RotateCw className="h-3 w-3 mr-1" />
                  {colorMode === 'heatmap' ? 'Heatmap' : 'Grayscale'}
                </Button>
              </div>
            </div>

            {/* Depth Statistics */}
            <div className="bg-muted/50 rounded-lg p-3 space-y-2">
              <div className="flex items-center space-x-2 mb-2">
                <Info className="h-4 w-4 text-muted-foreground" />
                <span className="text-xs font-medium">Depth Analysis</span>
              </div>
              
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Resolution:</span>
                  <span className="font-mono">{scene.width}×{scene.height}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Model:</span>
                  <span className="font-mono">Depth Anything V2</span>
                </div>
              </div>
              
              <div className="text-xs text-muted-foreground mt-2">
                Depth maps provide spatial understanding for object relationships, 
                occlusion analysis, and 3D scene reconstruction.
              </div>
            </div>
          </>
        )}
        
        {!isVisible && (
          <div className="text-center py-6 text-muted-foreground">
            <Mountain className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">Click the eye icon to view depth analysis</p>
          </div>
        )}
      </CardContent>

      {/* CSS for depth map styling */}
      <style jsx>{`
        .depth-heatmap {
          filter: hue-rotate(240deg) saturate(1.5) contrast(1.2);
        }
        
        .depth-grayscale {
          filter: grayscale(1) contrast(1.3);
        }
      `}</style>
    </Card>
  )
}