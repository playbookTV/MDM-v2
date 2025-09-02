import { useState } from 'react'
import { 
  Eye,
  Palette,
  Layers,
  BarChart3,
  ChevronDown,
  ChevronRight,
  Target,
  Settings,
  Mountain,
  Info
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { DepthMapViewer } from './DepthMapViewer'
import { AIProcessingTrigger } from './AIProcessingTrigger'
import type { Scene, SceneObject } from '@/types/dataset'

interface AIAnalysisPanelProps {
  scene: Scene
  selectedObject?: SceneObject | null
  onObjectSelect?: (object: SceneObject | null) => void
  onProcessingComplete?: () => void
  className?: string
}

export function AIAnalysisPanel({ 
  scene, 
  selectedObject, 
  onObjectSelect, 
  onProcessingComplete,
  className 
}: AIAnalysisPanelProps) {
  const [expandedSections, setExpandedSections] = useState({
    sceneAnalysis: true,
    objects: true,
    styles: false,
    colors: false,
    depth: false
  })
  const [showDepthMap, setShowDepthMap] = useState(false)

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }))
  }

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-green-600'
    if (confidence >= 0.6) return 'text-yellow-600'
    return 'text-red-600'
  }

  const getConfidenceVariant = (confidence: number) => {
    if (confidence >= 0.8) return 'default'
    if (confidence >= 0.6) return 'secondary'
    return 'destructive'
  }

  const formatConfidence = (confidence: number) => {
    return `${(confidence * 100).toFixed(0)}%`
  }

  return (
    <TooltipProvider>
      <div className={`space-y-4 ${className}`}>
        {/* AI Processing Trigger */}
        <AIProcessingTrigger
          scene={scene}
          onProcessingComplete={onProcessingComplete}
        />

        {/* Scene Analysis */}
        <Card>
          <Collapsible 
            open={expandedSections.sceneAnalysis} 
            onOpenChange={() => toggleSection('sceneAnalysis')}
          >
            <CollapsibleTrigger className="cursor-pointer hover:bg-muted/50 transition-colors pb-3">
              <CardHeader>
                <CardTitle className="flex items-center justify-between text-base">
                  <div className="flex items-center space-x-2">
                    <Eye className="h-4 w-4" />
                    <span>Scene Classification</span>
                  </div>
                  {expandedSections.sceneAnalysis ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </CardTitle>
              </CardHeader>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <CardContent className="pt-0">
                {scene.scene_type ? (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <Badge variant="secondary" className="text-sm">
                        {scene.scene_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                      </Badge>
                      <Badge 
                        variant={getConfidenceVariant(scene.scene_conf || 0)}
                        className="text-xs"
                      >
                        {formatConfidence(scene.scene_conf || 0)}
                      </Badge>
                    </div>
                    
                    {scene.scene_conf && (
                      <div className="space-y-1">
                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>Confidence</span>
                          <span className={getConfidenceColor(scene.scene_conf)}>
                            {formatConfidence(scene.scene_conf)}
                          </span>
                        </div>
                        <Progress value={scene.scene_conf * 100} className="h-2" />
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-4 text-muted-foreground">
                    <Target className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">No scene classification available</p>
                  </div>
                )}
              </CardContent>
            </CollapsibleContent>
          </Collapsible>
        </Card>

        {/* Objects */}
        <Card>
          <Collapsible 
            open={expandedSections.objects} 
            onOpenChange={() => toggleSection('objects')}
          >
            <CollapsibleTrigger className="cursor-pointer hover:bg-muted/50 transition-colors pb-3">
              <CardHeader>
                <CardTitle className="flex items-center justify-between text-base">
                  <div className="flex items-center space-x-2">
                    <Layers className="h-4 w-4" />
                    <span>Detected Objects</span>
                    <Badge variant="outline" className="text-xs">
                      {scene.objects?.length || 0}
                    </Badge>
                  </div>
                  {expandedSections.objects ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </CardTitle>
              </CardHeader>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <CardContent className="pt-0">
                {scene.objects && scene.objects.length > 0 ? (
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {scene.objects
                      .sort((a, b) => b.confidence - a.confidence)
                      .map((object) => (
                        <div
                          key={object.id}
                          className={`p-3 rounded-lg border cursor-pointer transition-all ${
                            selectedObject?.id === object.id 
                              ? 'bg-primary/10 border-primary' 
                              : 'hover:bg-muted/50'
                          }`}
                          onClick={() => onObjectSelect?.(
                            selectedObject?.id === object.id ? null : object
                          )}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium text-sm">
                              {object.label}
                            </span>
                            <Badge 
                              variant={getConfidenceVariant(object.confidence)}
                              className="text-xs"
                            >
                              {formatConfidence(object.confidence)}
                            </Badge>
                          </div>
                          
                          {object.material && (
                            <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                              <Settings className="h-3 w-3" />
                              <span>
                                {object.material}
                                {object.material_conf && (
                                  <span className="ml-1">
                                    ({formatConfidence(object.material_conf)})
                                  </span>
                                )}
                              </span>
                            </div>
                          )}
                          
                          <div className="text-xs text-muted-foreground mt-1">
                            {Math.round(object.bbox.width)}×{Math.round(object.bbox.height)} at 
                            ({Math.round(object.bbox.x)}, {Math.round(object.bbox.y)})
                          </div>
                        </div>
                      ))}
                  </div>
                ) : (
                  <div className="text-center py-4 text-muted-foreground">
                    <Layers className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">No objects detected</p>
                  </div>
                )}
              </CardContent>
            </CollapsibleContent>
          </Collapsible>
        </Card>

        {/* Style Analysis */}
        <Card>
          <Collapsible 
            open={expandedSections.styles} 
            onOpenChange={() => toggleSection('styles')}
          >
            <CollapsibleTrigger className="cursor-pointer hover:bg-muted/50 transition-colors pb-3">
              <CardHeader>
                <CardTitle className="flex items-center justify-between text-base">
                  <div className="flex items-center space-x-2">
                    <BarChart3 className="h-4 w-4" />
                    <span>Style Analysis</span>
                    <Badge variant="outline" className="text-xs">
                      {scene.styles?.length || 0}
                    </Badge>
                  </div>
                  {expandedSections.styles ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </CardTitle>
              </CardHeader>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <CardContent className="pt-0">
                {scene.styles && scene.styles.length > 0 ? (
                  <div className="space-y-3">
                    {scene.styles
                      .sort((a, b) => b.conf - a.conf)
                      .map((style) => (
                        <div key={style.code} className="space-y-1">
                          <div className="flex items-center justify-between">
                            <span className="text-sm font-medium capitalize">
                              {style.code.replace('_', ' ')}
                            </span>
                            <span className={`text-xs ${getConfidenceColor(style.conf)}`}>
                              {formatConfidence(style.conf)}
                            </span>
                          </div>
                          <Progress value={style.conf * 100} className="h-2" />
                        </div>
                      ))}
                  </div>
                ) : (
                  <div className="text-center py-4 text-muted-foreground">
                    <BarChart3 className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">No style analysis available</p>
                  </div>
                )}
              </CardContent>
            </CollapsibleContent>
          </Collapsible>
        </Card>

        {/* Color Palette */}
        <Card>
          <Collapsible 
            open={expandedSections.colors} 
            onOpenChange={() => toggleSection('colors')}
          >
            <CollapsibleTrigger className="cursor-pointer hover:bg-muted/50 transition-colors pb-3">
              <CardHeader>
                <CardTitle className="flex items-center justify-between text-base">
                  <div className="flex items-center space-x-2">
                    <Palette className="h-4 w-4" />
                    <span>Color Palette</span>
                    <Badge variant="outline" className="text-xs">
                      {scene.palette?.length || 0}
                    </Badge>
                  </div>
                  {expandedSections.colors ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </CardTitle>
              </CardHeader>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <CardContent className="pt-0">
                {scene.palette && scene.palette.length > 0 ? (
                  <div className="space-y-3">
                    <div className="grid grid-cols-5 gap-2">
                      {scene.palette.slice(0, 5).map((color, index) => (
                        <Tooltip key={index}>
                          <TooltipTrigger>
                            <div
                              className="h-10 rounded-md border-2 border-background shadow-sm cursor-pointer hover:scale-105 transition-transform"
                              style={{ backgroundColor: color.hex }}
                            />
                          </TooltipTrigger>
                          <TooltipContent>
                            <div className="text-center">
                              <div className="font-mono text-sm">{color.hex}</div>
                              <div className="text-xs text-muted-foreground">
                                {(color.p * 100).toFixed(1)}% coverage
                              </div>
                            </div>
                          </TooltipContent>
                        </Tooltip>
                      ))}
                    </div>
                    
                    <div className="space-y-2">
                      {scene.palette.slice(0, 3).map((color, index) => (
                        <div key={index} className="flex items-center space-x-3">
                          <div
                            className="w-4 h-4 rounded border"
                            style={{ backgroundColor: color.hex }}
                          />
                          <span className="font-mono text-xs">{color.hex}</span>
                          <span className="text-xs text-muted-foreground ml-auto">
                            {(color.p * 100).toFixed(1)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-4 text-muted-foreground">
                    <Palette className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">No color analysis available</p>
                  </div>
                )}
              </CardContent>
            </CollapsibleContent>
          </Collapsible>
        </Card>

        {/* Depth Analysis */}
        <Card>
          <Collapsible 
            open={expandedSections.depth} 
            onOpenChange={() => toggleSection('depth')}
          >
            <CollapsibleTrigger className="cursor-pointer hover:bg-muted/50 transition-colors pb-3">
              <CardHeader>
                <CardTitle className="flex items-center justify-between text-base">
                  <div className="flex items-center space-x-2">
                    <Mountain className="h-4 w-4" />
                    <span>Depth Analysis</span>
                    <Badge variant={scene.has_depth ? "default" : "secondary"} className="text-xs">
                      {scene.has_depth ? 'Available' : 'N/A'}
                    </Badge>
                  </div>
                  {expandedSections.depth ? (
                    <ChevronDown className="h-4 w-4" />
                  ) : (
                    <ChevronRight className="h-4 w-4" />
                  )}
                </CardTitle>
              </CardHeader>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <CardContent className="pt-0">
                {scene.has_depth ? (
                  <div className="space-y-3">
                    <div className="text-sm text-muted-foreground">
                      Depth mapping provides 3D spatial understanding of the scene, 
                      enabling advanced analysis of object relationships and room layout.
                    </div>
                    
                    <Button 
                      variant={showDepthMap ? "default" : "outline"} 
                      size="sm" 
                      className="w-full"
                      onClick={() => setShowDepthMap(!showDepthMap)}
                    >
                      <Mountain className="h-4 w-4 mr-2" />
                      {showDepthMap ? 'Hide' : 'View'} Depth Map
                    </Button>
                  </div>
                ) : (
                  <div className="text-center py-4 text-muted-foreground">
                    <Mountain className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">No depth analysis available</p>
                  </div>
                )}
              </CardContent>
            </CollapsibleContent>
          </Collapsible>
        </Card>

        {/* Depth Map Viewer */}
        {showDepthMap && scene.has_depth && (
          <DepthMapViewer
            scene={scene}
            isVisible={showDepthMap}
            onToggle={() => setShowDepthMap(!showDepthMap)}
          />
        )}

        {/* AI Processing Info */}
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-start space-x-3">
              <Info className="h-4 w-4 text-muted-foreground mt-0.5" />
              <div className="text-xs text-muted-foreground">
                <p className="mb-1">
                  AI analysis powered by YOLO, CLIP, SAM2, and Depth Anything V2 models 
                  running on RunPod GPU infrastructure.
                </p>
                <p>
                  Processing time: ~1.3s per image • Real-time inference
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </TooltipProvider>
  )
}