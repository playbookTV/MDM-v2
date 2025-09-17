import { useState, useCallback, useEffect } from "react";
import {
  Download,
  ChevronLeft,
  ChevronRight,
  Eye,
  EyeOff,
  Layers,
  X,
  AlertTriangle,
  ImageIcon,
  TagIcon,
  Palette,
  Ruler,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { useScene, useSceneImages, useScenePrefetch } from "@/hooks/useScenes";
import { useReviewKeyboard } from "@/hooks/useReviews";
import { SceneCanvasRenderer } from "./SceneCanvasRenderer";
import type { Scene, SceneObject } from "@/types/dataset";

interface SceneDetailViewProps {
  sceneId: string;
  onNext?: () => void;
  onPrevious?: () => void;
  onClose?: () => void;
  selectedObject?: SceneObject;
  onObjectSelect?: (object: SceneObject | null) => void;
  nextSceneId?: string;
  previousSceneId?: string;
  className?: string;
}

export function SceneDetailView({
  sceneId,
  onNext,
  onPrevious,
  onClose,
  selectedObject,
  onObjectSelect,
  nextSceneId,
  previousSceneId,
  className,
}: SceneDetailViewProps) {
  const [showObjects, setShowObjects] = useState(true);
  const [showMasks, setShowMasks] = useState(false);
  const [sidebarVisible, setSidebarVisible] = useState(true);

  const { data: scene, isLoading, error } = useScene(sceneId, true);
  const { prefetchScene } = useScenePrefetch();

  // Prefetch adjacent scenes for smooth navigation
  useEffect(() => {
    if (nextSceneId) prefetchScene(nextSceneId);
    if (previousSceneId) prefetchScene(previousSceneId);
  }, [nextSceneId, previousSceneId, prefetchScene]);

  const { originalUrl } = useSceneImages(scene || ({} as Scene));

  // Keyboard shortcuts
  const { handleKeyPress } = useReviewKeyboard({
    onNext,
    onPrevious,
    onEscape: onClose,
  });

  useEffect(() => {
    document.addEventListener("keydown", handleKeyPress);
    return () => document.removeEventListener("keydown", handleKeyPress);
  }, [handleKeyPress]);

  // Reset selection when scene changes
  useEffect(() => {
    onObjectSelect?.(null);
  }, [sceneId, onObjectSelect]);

  const handleObjectClick = useCallback((object: SceneObject) => {
    const newSelection = selectedObject?.id === object.id ? null : object;
    onObjectSelect?.(newSelection);
  }, [selectedObject, onObjectSelect]);

  const downloadImage = () => {
    if (!scene) return;
    const link = document.createElement("a");
    link.href = originalUrl;
    link.download = scene.source;
    link.click();
  };

  const getObjectColor = (objectId: string) => {
    const colors = [
      "#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", 
      "#ef4444", "#06b6d4", "#84cc16"
    ];
    const index = scene?.objects?.findIndex((obj) => obj.id === objectId) || 0;
    return colors[index % colors.length];
  };

  // Normalize objects to ensure bbox is present
  const normalizedObjects: SceneObject[] = (scene?.objects || []).map((obj: any) => {
    if (obj && !obj.bbox) {
      if (
        typeof obj.bbox_x === "number" &&
        typeof obj.bbox_y === "number" &&
        typeof obj.bbox_w === "number" &&
        typeof obj.bbox_h === "number"
      ) {
        return {
          ...obj,
          bbox: {
            x: obj.bbox_x,
            y: obj.bbox_y,
            width: obj.bbox_w,
            height: obj.bbox_h,
          },
        } as SceneObject;
      }
      if (Array.isArray(obj.bbox) && obj.bbox.length === 4) {
        const [x1, y1, x2, y2] = obj.bbox;
        return {
          ...obj,
          bbox: {
            x: x1,
            y: y1,
            width: x2 - x1,
            height: y2 - y1,
          },
        } as SceneObject;
      }
    }
    return obj as SceneObject;
  });

  if (error) {
    return (
      <Card className={`w-full h-96 flex items-center justify-center ${className}`}>
        <CardContent className="text-center">
          <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">Failed to load scene</h3>
          <p className="text-sm text-muted-foreground">
            {error?.message || "An error occurred"}
          </p>
        </CardContent>
      </Card>
    );
  }

  if (isLoading) {
    return (
      <Card className={`w-full h-96 flex items-center justify-center ${className}`}>
        <CardContent className="text-center">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-sm text-muted-foreground">Loading scene...</p>
        </CardContent>
      </Card>
    );
  }

  if (!scene) {
    return null;
  }

  return (
    <div className={`flex h-full bg-background ${className}`}>
      {/* Main Content Area */}
      <div className="flex-1 flex flex-col">
        {/* Top Toolbar */}
        <div className="flex items-center justify-between p-4 border-b bg-card">
          <div className="flex items-center space-x-4">
            {/* Navigation */}
            {onPrevious && (
              <Button
                variant="outline"
                size="sm"
                onClick={onPrevious}
                disabled={!previousSceneId}
              >
                <ChevronLeft className="h-4 w-4" />
                Previous
              </Button>
            )}

            {onNext && (
              <Button
                variant="outline"
                size="sm"
                onClick={onNext}
                disabled={!nextSceneId}
              >
                Next
                <ChevronRight className="h-4 w-4" />
              </Button>
            )}

            <Separator orientation="vertical" className="h-6" />

            {/* Scene Info */}
            <div className="flex items-center space-x-2">
              <ImageIcon className="h-4 w-4 text-muted-foreground" />
              <span className="font-medium truncate max-w-48" title={scene.source}>
                {scene.source}
              </span>
              {scene.scene_type && (
                <Badge variant="outline">
                  {scene.scene_type.replace("_", " ")}
                </Badge>
              )}
              {scene.scene_conf && (
                <Badge variant="secondary">
                  {(scene.scene_conf * 100).toFixed(0)}% conf
                </Badge>
              )}
              {scene.review_status && (
                <Badge variant={getReviewStatusVariant(scene.review_status)}>
                  {scene.review_status}
                </Badge>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-2">
            {/* View Controls */}
            <Button
              variant={showObjects ? "default" : "outline"}
              size="sm"
              onClick={() => setShowObjects(!showObjects)}
            >
              <Eye className="h-4 w-4 mr-1" />
              Objects
            </Button>

            <Button
              variant={showMasks ? "default" : "outline"}
              size="sm"
              onClick={() => setShowMasks(!showMasks)}
            >
              <Layers className="h-4 w-4 mr-1" />
              Masks
            </Button>

            <Separator orientation="vertical" className="h-6" />

            <Button
              variant="outline"
              size="sm"
              onClick={() => setSidebarVisible(!sidebarVisible)}
            >
              <TagIcon className="h-4 w-4 mr-1" />
              Details
            </Button>

            <Button variant="outline" size="sm" onClick={downloadImage}>
              <Download className="h-4 w-4" />
            </Button>

            {onClose && (
              <Button variant="outline" size="sm" onClick={onClose}>
                <X className="h-4 w-4" />
              </Button>
            )}
          </div>
        </div>

        {/* Canvas Area */}
        <div className="flex-1 bg-muted/20">
          <SceneCanvasRenderer
            scene={scene}
            imageUrl={originalUrl}
            objects={normalizedObjects}
            showObjects={showObjects}
            showMasks={showMasks}
            selectedObject={selectedObject}
            onObjectClick={handleObjectClick}
            className="w-full h-full"
          />
        </div>

        {/* Bottom Status Bar */}
        <div className="flex items-center justify-between p-2 border-t bg-card text-sm text-muted-foreground">
          <div className="flex items-center space-x-4">
            <span>{scene.width} × {scene.height}px</span>
            <span>{normalizedObjects?.length || 0} objects detected</span>
            {scene.dataset_name && <span>Dataset: {scene.dataset_name}</span>}
          </div>
          <div className="text-xs">
            Mouse wheel: zoom • Drag: pan • Click objects to select
          </div>
        </div>
      </div>

      {/* Right Sidebar */}
      {sidebarVisible && (
        <div className="w-80 border-l bg-card flex flex-col">
          {/* Scene Details */}
          <Card className="m-4 mb-2">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center">
                <ImageIcon className="h-4 w-4 mr-2" />
                Scene Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid grid-cols-2 gap-2 text-sm">
                <div>
                  <span className="text-muted-foreground">Type:</span>
                  <div className="font-medium">
                    {scene.scene_type?.replace("_", " ") || "Unknown"}
                  </div>
                </div>
                <div>
                  <span className="text-muted-foreground">Confidence:</span>
                  <div className="font-medium">
                    {scene.scene_conf ? `${(scene.scene_conf * 100).toFixed(0)}%` : "N/A"}
                  </div>
                </div>
                <div>
                  <span className="text-muted-foreground">Objects:</span>
                  <div className="font-medium">{normalizedObjects?.length || 0}</div>
                </div>
                <div>
                  <span className="text-muted-foreground">Status:</span>
                  <div className="font-medium">
                    <Badge variant={getReviewStatusVariant(scene.review_status || "pending")}>
                      {scene.review_status || "pending"}
                    </Badge>
                  </div>
                </div>
              </div>

              {/* Style Information */}
              {scene.styles && scene.styles.length > 0 && (
                <div>
                  <div className="text-muted-foreground text-sm mb-1 flex items-center">
                    <Palette className="h-3 w-3 mr-1" />
                    Design Styles
                  </div>
                  <div className="flex flex-wrap gap-1">
                    {scene.styles.slice(0, 3).map((style, idx) => (
                      <Badge key={idx} variant="outline" className="text-xs">
                        {style.code} ({(style.conf * 100).toFixed(0)}%)
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Color Palette */}
              {scene.palette && scene.palette.length > 0 && (
                <div>
                  <div className="text-muted-foreground text-sm mb-1">Color Palette</div>
                  <div className="flex space-x-1">
                    {scene.palette.slice(0, 6).map((color, idx) => (
                      <div
                        key={idx}
                        className="w-6 h-6 rounded border border-border"
                        style={{ backgroundColor: color.hex }}
                        title={`${color.hex} (${(color.p * 100).toFixed(1)}%)`}
                      />
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Selected Object Details */}
          {selectedObject && (
            <Card className="m-4 mt-0 flex-1 overflow-auto">
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center">
                  <TagIcon className="h-4 w-4 mr-2" />
                  Object Details
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-between">
                  <Badge 
                    variant="secondary" 
                    className="text-sm"
                    style={{ backgroundColor: `${getObjectColor(selectedObject.id)}20`, color: getObjectColor(selectedObject.id) }}
                  >
                    {selectedObject.label}
                  </Badge>
                  <span className="text-sm font-mono">
                    {(selectedObject.confidence * 100).toFixed(0)}% conf
                  </span>
                </div>

                {/* Materials */}
                {selectedObject.materials && selectedObject.materials.length > 0 ? (
                  <div>
                    <div className="text-sm font-medium mb-2">Materials</div>
                    <div className="space-y-1">
                      {selectedObject.materials.slice(0, 3).map((mat, idx) => (
                        <div key={idx} className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">{mat.material}</span>
                          <span className="font-mono">{(mat.confidence * 100).toFixed(0)}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ) : selectedObject.material ? (
                  <div>
                    <div className="text-sm font-medium mb-1">Material</div>
                    <div className="text-sm">
                      {selectedObject.material} ({(selectedObject.material_conf || 0) * 100}%)
                    </div>
                  </div>
                ) : null}

                {/* Bounding Box */}
                {selectedObject.bbox && (
                  <div>
                    <div className="text-sm font-medium mb-2 flex items-center">
                      <Ruler className="h-3 w-3 mr-1" />
                      Dimensions
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-sm">
                      <div>
                        <span className="text-muted-foreground">Size:</span>
                        <div className="font-mono">
                          {Math.round(selectedObject.bbox.width)} × {Math.round(selectedObject.bbox.height)}px
                        </div>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Position:</span>
                        <div className="font-mono">
                          ({Math.round(selectedObject.bbox.x)}, {Math.round(selectedObject.bbox.y)})
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Segmentation Info */}
                {selectedObject.has_mask && (
                  <div>
                    <div className="text-sm font-medium mb-2">Segmentation</div>
                    <div className="space-y-1 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Mask Area:</span>
                        <span className="font-mono">
                          {selectedObject.mask_area?.toLocaleString()} px
                        </span>
                      </div>
                      {selectedObject.mask_coverage && (
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">Coverage:</span>
                          <span className="font-mono">
                            {(selectedObject.mask_coverage * 100).toFixed(1)}%
                          </span>
                        </div>
                      )}
                      {selectedObject.segmentation_confidence && (
                        <div className="flex justify-between">
                          <span className="text-muted-foreground">SAM2 Score:</span>
                          <span className="font-mono">
                            {(selectedObject.segmentation_confidence * 100).toFixed(0)}%
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Review Status */}
                {selectedObject.review_status && (
                  <div>
                    <div className="text-sm font-medium mb-1">Review Status</div>
                    <Badge variant={getReviewStatusVariant(selectedObject.review_status)}>
                      {selectedObject.review_status}
                    </Badge>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Objects List when no selection */}
          {!selectedObject && normalizedObjects.length > 0 && (
            <Card className="m-4 mt-0 flex-1 overflow-auto">
              <CardHeader className="pb-3">
                <CardTitle className="text-base">
                  Detected Objects ({normalizedObjects.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {normalizedObjects.map((obj, idx) => (
                  <div
                    key={obj.id}
                    className="flex items-center justify-between p-2 rounded border hover:bg-muted/50 cursor-pointer"
                    onClick={() => handleObjectClick(obj)}
                  >
                    <div className="flex items-center space-x-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: getObjectColor(obj.id) }}
                      />
                      <span className="text-sm font-medium">{obj.label}</span>
                    </div>
                    <span className="text-xs font-mono text-muted-foreground">
                      {(obj.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}

// Utility function
function getReviewStatusVariant(status: string) {
  switch (status) {
    case "approved":
      return "secondary" as const;
    case "rejected":
      return "destructive" as const;
    case "corrected":
      return "default" as const;
    default:
      return "outline" as const;
  }
}