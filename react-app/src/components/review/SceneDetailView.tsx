import { useState, useCallback, useEffect } from "react";
import {
  ZoomIn,
  ZoomOut,
  RotateCw,
  Download,
  Maximize,
  ChevronLeft,
  ChevronRight,
  Eye,
  EyeOff,
  Layers,
  Info,
  AlertTriangle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useScene, useSceneImages, useScenePrefetch } from "@/hooks/useScenes";
import { useReviewKeyboard } from "@/hooks/useReviews";
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
  const [zoom, setZoom] = useState(1);
  const [panX, setPanX] = useState(0);
  const [panY, setPanY] = useState(0);
  const [showObjects, setShowObjects] = useState(true);
  const [showInfo, setShowInfo] = useState(true);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });

  const { data: scene, isLoading, error } = useScene(sceneId, true);
  const { prefetchScene } = useScenePrefetch();

  // Prefetch adjacent scenes for smooth navigation
  useEffect(() => {
    if (nextSceneId) prefetchScene(nextSceneId);
    if (previousSceneId) prefetchScene(previousSceneId);
  }, [nextSceneId, previousSceneId, prefetchScene]);

  const { originalUrl, depthUrl } = useSceneImages(scene || ({} as Scene));

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

  // Reset view when scene changes
  useEffect(() => {
    setZoom(1);
    setPanX(0);
    setPanY(0);
    onObjectSelect?.(null);
  }, [sceneId, onObjectSelect]);

  const handleWheel = useCallback(
    (e: React.WheelEvent) => {
      e.preventDefault();
      const delta = e.deltaY > 0 ? 0.9 : 1.1;
      const newZoom = Math.max(0.1, Math.min(5, zoom * delta));
      setZoom(newZoom);
    },
    [zoom],
  );

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (e.button === 0) {
        // Left click
        setIsDragging(true);
        setDragStart({ x: e.clientX - panX, y: e.clientY - panY });
      }
    },
    [panX, panY],
  );

  const handleMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (isDragging) {
        setPanX(e.clientX - dragStart.x);
        setPanY(e.clientY - dragStart.y);
      }
    },
    [isDragging, dragStart],
  );

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleObjectClick = (object: SceneObject, e: React.MouseEvent) => {
    e.stopPropagation();
    if (selectedObject?.id === object.id) {
      onObjectSelect?.(null);
    } else {
      onObjectSelect?.(object);
    }
  };

  const resetView = () => {
    setZoom(1);
    setPanX(0);
    setPanY(0);
  };

  const downloadImage = () => {
    if (!scene) return;
    const link = document.createElement("a");
    link.href = originalUrl;
    link.download = scene.source;
    link.click();
  };

  const getObjectColor = (objectId: string) => {
    const colors = [
      "#3b82f6",
      "#10b981",
      "#f59e0b",
      "#8b5cf6",
      "#ef4444",
      "#06b6d4",
      "#84cc16",
    ];
    const index = scene?.objects?.findIndex((obj) => obj.id === objectId) || 0;
    return colors[index % colors.length];
  };

  if (error) {
    return (
      <div
        className={`flex items-center justify-center min-h-96 bg-card border rounded-lg ${className}`}
        data-oid="x5zqld:"
      >
        <div className="text-center" data-oid="v1vbi4c">
          <AlertTriangle
            className="h-12 w-12 text-destructive mx-auto mb-4"
            data-oid="00ln:92"
          />
          <h3 className="text-lg font-semibold mb-2" data-oid="kn9yw7r">
            Failed to load scene
          </h3>
          <p className="text-sm text-muted-foreground" data-oid=":vdsv_5">
            {error?.message || "An error occurred"}
          </p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div
        className={`flex items-center justify-center min-h-96 bg-card border rounded-lg ${className}`}
        data-oid="fa.4x:g"
      >
        <div className="text-center" data-oid="wg95lwh">
          <div
            className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"
            data-oid="u51t1:m"
          />
          <p className="text-sm text-muted-foreground" data-oid="mctmfg9">
            Loading scene...
          </p>
        </div>
      </div>
    );
  }

  if (!scene) {
    return null;
  }

  return (
    <div
      className={`relative bg-card border rounded-lg overflow-hidden ${className}`}
      data-oid="hf4zo6w"
    >
      {/* Header */}
      <div
        className="absolute top-0 left-0 right-0 bg-background/95 backdrop-blur-sm border-b z-20 p-4"
        data-oid="gpc3a2g"
      >
        <div className="flex items-center justify-between" data-oid="f1yacf_">
          <div className="flex items-center space-x-3" data-oid=":rmdn08">
            <h3
              className="font-semibold truncate max-w-64"
              title={scene.source}
              data-oid="w.bp6.l"
            >
              {scene.source}
            </h3>
            <div className="flex items-center space-x-1" data-oid="zqnba95">
              {scene.scene_type && (
                <Badge variant="outline" data-oid="qga:m7k">
                  {scene.scene_type.replace("_", " ")}
                </Badge>
              )}
              {scene.scene_conf && (
                <Badge variant="secondary" data-oid=":nhm_5s">
                  {(scene.scene_conf * 100).toFixed(0)}% conf
                </Badge>
              )}
              {scene.review_status && (
                <Badge
                  variant={getReviewStatusVariant(scene.review_status)}
                  data-oid="n:3-yvq"
                >
                  {scene.review_status}
                </Badge>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-2" data-oid="kckcgw-">
            {/* View Controls */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowObjects(!showObjects)}
              data-oid=".m3yzt8"
            >
              {showObjects ? (
                <Eye className="h-4 w-4" data-oid="rqovqif" />
              ) : (
                <EyeOff className="h-4 w-4" data-oid="31s1qmg" />
              )}
              Objects
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowInfo(!showInfo)}
              data-oid="spyt4tu"
            >
              <Info className="h-4 w-4" data-oid="a2q16bn" />
            </Button>

            {/* Zoom Controls */}
            <div className="flex border rounded-md" data-oid="_vbi7sg">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setZoom(Math.max(0.1, zoom * 0.8))}
                className="rounded-r-none"
                data-oid="hfddmzf"
              >
                <ZoomOut className="h-4 w-4" data-oid="9vg3ru_" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={resetView}
                className="rounded-none border-x text-xs px-2"
                data-oid="yc2hwtw"
              >
                {Math.round(zoom * 100)}%
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setZoom(Math.min(5, zoom * 1.25))}
                className="rounded-l-none"
                data-oid="g4gavly"
              >
                <ZoomIn className="h-4 w-4" data-oid="4yb_.e8" />
              </Button>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={downloadImage}
              data-oid="mvda3yi"
            >
              <Download className="h-4 w-4" data-oid="_1d3yik" />
            </Button>

            {onClose && (
              <Button
                variant="outline"
                size="sm"
                onClick={onClose}
                data-oid="myb4ill"
              >
                <Maximize className="h-4 w-4" data-oid="sx:43l5" />
              </Button>
            )}
          </div>
        </div>
      </div>

      {/* Navigation */}
      {(onPrevious || onNext) && (
        <>
          {onPrevious && (
            <Button
              variant="outline"
              size="sm"
              onClick={onPrevious}
              className="absolute left-4 top-1/2 -translate-y-1/2 z-10"
              disabled={!previousSceneId}
              data-oid="zpzopll"
            >
              <ChevronLeft className="h-4 w-4" data-oid="f7am8iu" />
            </Button>
          )}

          {onNext && (
            <Button
              variant="outline"
              size="sm"
              onClick={onNext}
              className="absolute right-4 top-1/2 -translate-y-1/2 z-10"
              disabled={!nextSceneId}
              data-oid="7pp7osy"
            >
              <ChevronRight className="h-4 w-4" data-oid="nagpjsc" />
            </Button>
          )}
        </>
      )}

      {/* Image Container */}
      <div
        className="relative h-full min-h-96 overflow-hidden cursor-grab active:cursor-grabbing"
        onWheel={handleWheel}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        data-oid="a55z09."
      >
        <div
          className="relative transition-transform origin-center"
          style={{
            transform: `translate(${panX}px, ${panY}px) scale(${zoom})`,
            width: "100%",
            height: "100%",
            paddingTop: "80px", // Account for header
          }}
          data-oid="0p2fh3k"
        >
          {/* Main Image */}
          <img
            src={originalUrl}
            alt={scene.source}
            className="max-w-none h-auto mx-auto block"
            style={{
              width: "auto",
              height: "calc(100vh - 200px)",
              maxWidth: "none",
              objectFit: "contain",
            }}
            draggable={false}
            data-oid="az3:ork"
          />

          {/* Object Overlays */}
          {showObjects &&
            scene.objects &&
            scene.objects.map((object) => (
              <ObjectOverlay
                key={object.id}
                object={object}
                isSelected={selectedObject?.id === object.id}
                color={getObjectColor(object.id)}
                onClick={(e) => handleObjectClick(object, e)}
                imageWidth={scene.width}
                imageHeight={scene.height}
                data-oid="vdq-u1i"
              />
            ))}
        </div>
      </div>

      {/* Info Panel */}
      {showInfo && (
        <div
          className="absolute bottom-0 left-0 right-0 bg-background/95 backdrop-blur-sm border-t p-4 z-20"
          data-oid="uibqfo7"
        >
          <div
            className="flex items-center justify-between text-sm"
            data-oid="f.ys74d"
          >
            <div className="flex items-center space-x-4" data-oid="613apj.">
              <span data-oid="fq.15y6">
                {scene.width} × {scene.height}px
              </span>
              <span data-oid=":4kaxu8">
                {scene.objects?.length || 0} objects
              </span>
              {scene.dataset_name && (
                <span data-oid="b2amuck">Dataset: {scene.dataset_name}</span>
              )}
            </div>

            <div className="text-xs text-muted-foreground" data-oid="tuidghp">
              Use mouse wheel to zoom, drag to pan, arrow keys to navigate
            </div>
          </div>
        </div>
      )}

      {/* Object Info */}
      {selectedObject && (
        <div
          className="absolute top-20 right-4 bg-background/95 backdrop-blur-sm border rounded-lg p-3 z-20 max-w-64"
          data-oid="n17vz-v"
        >
          <div className="space-y-2" data-oid="bxh:cij">
            <div
              className="flex items-center justify-between"
              data-oid="8tw_mhy"
            >
              <Badge variant="secondary" data-oid="rf02ss7">
                {selectedObject.label}
              </Badge>
              <span className="text-xs font-mono" data-oid="ik71t6j">
                {(selectedObject.confidence * 100).toFixed(0)}%
              </span>
            </div>

            {selectedObject.material && (
              <div className="text-xs" data-oid="sb5_z.1">
                Material: {selectedObject.material} (
                {(selectedObject.material_conf || 0) * 100}%)
              </div>
            )}

            <div className="text-xs text-muted-foreground" data-oid="5nf1or:">
              {Math.round(selectedObject.bbox.width)}×
              {Math.round(selectedObject.bbox.height)} at (
              {Math.round(selectedObject.bbox.x)},{" "}
              {Math.round(selectedObject.bbox.y)})
            </div>

            {selectedObject.review_status && (
              <Badge variant="outline" className="text-xs" data-oid="7y46anm">
                {selectedObject.review_status}
              </Badge>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// Object overlay component
function ObjectOverlay({
  object,
  isSelected,
  color,
  onClick,
  imageWidth,
  imageHeight,
}: {
  object: SceneObject;
  isSelected: boolean;
  color: string;
  onClick: (e: React.MouseEvent) => void;
  imageWidth: number;
  imageHeight: number;
}) {
  const { bbox } = object;

  // Convert bbox coordinates to percentage
  const left = (bbox.x / imageWidth) * 100;
  const top = (bbox.y / imageHeight) * 100;
  const width = (bbox.width / imageWidth) * 100;
  const height = (bbox.height / imageHeight) * 100;

  return (
    <div
      className={`absolute border-2 cursor-pointer transition-all ${
        isSelected
          ? "border-primary bg-primary/20"
          : "border-white/60 hover:border-white/80"
      }`}
      style={{
        left: `${left}%`,
        top: `${top}%`,
        width: `${width}%`,
        height: `${height}%`,
        borderColor: isSelected ? color : "rgba(255, 255, 255, 0.6)",
      }}
      onClick={onClick}
      data-oid="ea_ehkh"
    >
      {/* Label */}
      <div
        className="absolute -top-6 left-0 px-1 py-0.5 text-xs font-medium rounded text-white"
        style={{ backgroundColor: color }}
        data-oid="n3zwlwr"
      >
        {object.label} ({(object.confidence * 100).toFixed(0)}%)
      </div>
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
