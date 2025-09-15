import { useState, useCallback, useEffect, useRef } from "react";
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
  const containerRef = useRef<HTMLDivElement>(null);

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

  // Register non-passive wheel listener to allow preventDefault
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const onWheel = (e: WheelEvent) => {
      e.preventDefault();
      const delta = e.deltaY > 0 ? 0.9 : 1.1;
      setZoom((z) => Math.max(0.1, Math.min(5, z * delta)));
    };
    el.addEventListener("wheel", onWheel, { passive: false });
    return () => {
      el.removeEventListener("wheel", onWheel as EventListener);
    };
  }, []);

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

  // Normalize objects to ensure bbox is present when DB fields are returned
  const normalizedObjects: SceneObject[] = (scene?.objects || []).map((obj: any) => {
    if (obj && !obj.bbox) {
      // From DB-style columns
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
        } as SceneObject
      }
      // From array format [x1,y1,x2,y2]
      if (Array.isArray(obj.bbox) && obj.bbox.length === 4) {
        const [x1, y1, x2, y2] = obj.bbox
        return {
          ...obj,
          bbox: {
            x: x1,
            y: y1,
            width: x2 - x1,
            height: y2 - y1,
          },
        } as SceneObject
      }
    }
    return obj as SceneObject
  })

  if (error) {
    return (
      <div
        className={`flex items-center justify-center min-h-96 bg-card border rounded-lg ${className}`}
        data-oid="a08uv3r"
      >
        <div className="text-center" data-oid="p_ia0kt">
          <AlertTriangle
            className="h-12 w-12 text-destructive mx-auto mb-4"
            data-oid=":s0ungw"
          />

          <h3 className="text-lg font-semibold mb-2" data-oid="pn7esmx">
            Failed to load scene
          </h3>
          <p className="text-sm text-muted-foreground" data-oid="m0u651w">
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
        data-oid="4ctyfd9"
      >
        <div className="text-center" data-oid="6le0vx_">
          <div
            className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin mx-auto mb-4"
            data-oid="23tego0"
          />

          <p className="text-sm text-muted-foreground" data-oid="7q883dm">
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
      data-oid="vy.xxcj"
    >
      {/* Header */}
      <div
        className="absolute top-0 left-0 right-0 bg-background/95 backdrop-blur-sm border-b z-20 p-4"
        data-oid="9at:puk"
      >
        <div className="flex items-center justify-between" data-oid="k788zfr">
          <div className="flex items-center space-x-3" data-oid="_8fs243">
            <h3
              className="font-semibold truncate max-w-64"
              title={scene.source}
              data-oid="9nlcnc:"
            >
              {scene.source}
            </h3>
            <div className="flex items-center space-x-1" data-oid="37-o78_">
              {scene.scene_type && (
                <Badge variant="outline" data-oid="50xa1-n">
                  {scene.scene_type.replace("_", " ")}
                </Badge>
              )}
              {scene.scene_conf && (
                <Badge variant="secondary" data-oid=".0:a_rv">
                  {(scene.scene_conf * 100).toFixed(0)}% conf
                </Badge>
              )}
              {scene.review_status && (
                <Badge
                  variant={getReviewStatusVariant(scene.review_status)}
                  data-oid="p3piq0i"
                >
                  {scene.review_status}
                </Badge>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-2" data-oid="prdrwm_">
            {/* View Controls */}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowObjects(!showObjects)}
              data-oid="9l6_ksm"
            >
              {showObjects ? (
                <Eye className="h-4 w-4" data-oid="z35swrb" />
              ) : (
                <EyeOff className="h-4 w-4" data-oid="1abviih" />
              )}
              Objects
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowInfo(!showInfo)}
              data-oid="j298zv5"
            >
              <Info className="h-4 w-4" data-oid="hyfn7kg" />
            </Button>

            {/* Zoom Controls */}
            <div className="flex border rounded-md" data-oid="x1hx3f:">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setZoom(Math.max(0.1, zoom * 0.8))}
                className="rounded-r-none"
                data-oid="yx2lsuw"
              >
                <ZoomOut className="h-4 w-4" data-oid="49nh71c" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={resetView}
                className="rounded-none border-x text-xs px-2"
                data-oid="3.zn1vf"
              >
                {Math.round(zoom * 100)}%
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setZoom(Math.min(5, zoom * 1.25))}
                className="rounded-l-none"
                data-oid="o18gwy_"
              >
                <ZoomIn className="h-4 w-4" data-oid="aiv1l_9" />
              </Button>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={downloadImage}
              data-oid="elfpstz"
            >
              <Download className="h-4 w-4" data-oid="tw29j.p" />
            </Button>

            {onClose && (
              <Button
                variant="outline"
                size="sm"
                onClick={onClose}
                data-oid="z-z0atp"
              >
                <Maximize className="h-4 w-4" data-oid="pvvvy7c" />
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
              data-oid="l4eufhe"
            >
              <ChevronLeft className="h-4 w-4" data-oid=".:9.fb5" />
            </Button>
          )}

          {onNext && (
            <Button
              variant="outline"
              size="sm"
              onClick={onNext}
              className="absolute right-4 top-1/2 -translate-y-1/2 z-10"
              disabled={!nextSceneId}
              data-oid="q:dn3o8"
            >
              <ChevronRight className="h-4 w-4" data-oid="xx53:dc" />
            </Button>
          )}
        </>
      )}

      {/* Image Container */}
      <div
        className="relative h-full min-h-96 overflow-hidden cursor-grab active:cursor-grabbing"
        ref={containerRef}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        data-oid="ugw-j2j"
      >
        <div
          className="relative transition-transform origin-center"
          style={{
            transform: `translate(${panX}px, ${panY}px) scale(${zoom})`,
            width: "100%",
            height: "100%",
            paddingTop: "80px", // Account for header
          }}
          data-oid="uuxx_e-"
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
            data-oid="f..vnk6"
          />

          {/* Object Overlays */}
          {showObjects &&
            normalizedObjects &&
            normalizedObjects.map((object) => (
              <ObjectOverlay
                key={object.id}
                object={object}
                isSelected={selectedObject?.id === object.id}
                color={getObjectColor(object.id)}
                onClick={(e) => handleObjectClick(object, e)}
                imageWidth={scene.width}
                imageHeight={scene.height}
                data-oid="lyruzec"
              />
            ))}
        </div>
      </div>

      {/* Info Panel */}
      {showInfo && (
        <div
          className="absolute bottom-0 left-0 right-0 bg-background/95 backdrop-blur-sm border-t p-4 z-20"
          data-oid="-2xpgjp"
        >
          <div
            className="flex items-center justify-between text-sm"
            data-oid="62wcr0u"
          >
            <div className="flex items-center space-x-4" data-oid="ei1had0">
              <span data-oid="7lvcnk7">
                {scene.width} × {scene.height}px
              </span>
              <span data-oid="wef5v92">
              {normalizedObjects?.length || 0} objects
              </span>
              {scene.dataset_name && (
                <span data-oid="vms9ok3">Dataset: {scene.dataset_name}</span>
              )}
            </div>

            <div className="text-xs text-muted-foreground" data-oid="e60ie3v">
              Use mouse wheel to zoom, drag to pan, arrow keys to navigate
            </div>
          </div>
        </div>
      )}

      {/* Object Info */}
      {selectedObject && (
        <div
          className="absolute top-20 right-4 bg-background/95 backdrop-blur-sm border rounded-lg p-3 z-20 max-w-64"
          data-oid="tkoc:ux"
        >
          <div className="space-y-2" data-oid="sc:247s">
            <div
              className="flex items-center justify-between"
              data-oid=":jie40c"
            >
              <Badge variant="secondary" data-oid="qu0gngl">
                {selectedObject.label}
              </Badge>
              <span className="text-xs font-mono" data-oid="5_5ypka">
                {(selectedObject.confidence * 100).toFixed(0)}%
              </span>
            </div>

            {/* Enhanced material display */}
            {selectedObject.materials && selectedObject.materials.length > 0 ? (
              <div className="space-y-1" data-oid="qg3pl96">
                <div className="text-xs font-medium">Materials:</div>
                {selectedObject.materials.slice(0, 3).map((mat, idx) => (
                  <div key={idx} className="text-xs flex items-center justify-between">
                    <span className="text-muted-foreground">{mat.material}</span>
                    <span className="font-mono">
                      {(mat.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                ))}
              </div>
            ) : selectedObject.material ? (
              // Fallback to legacy single material
              <div className="text-xs" data-oid="qg3pl96">
                Material: {selectedObject.material} (
                {(selectedObject.material_conf || 0) * 100}%)
              </div>
            ) : null}

            {(selectedObject.bbox &&
              typeof selectedObject.bbox.x === "number" &&
              typeof selectedObject.bbox.y === "number" &&
              typeof selectedObject.bbox.width === "number" &&
              typeof selectedObject.bbox.height === "number") ? (
              <div className="text-xs text-muted-foreground" data-oid=".ojmm.v">
                {Math.round(selectedObject.bbox.width)}×
                {Math.round(selectedObject.bbox.height)} at (
                {Math.round(selectedObject.bbox.x)},{" "}
                {Math.round(selectedObject.bbox.y)})
              </div>
            ) : (
              <div className="text-xs text-muted-foreground" data-oid=".ojmm.v">
                Bounding box: N/A
              </div>
            )}

            {selectedObject.review_status && (
              <Badge variant="outline" className="text-xs" data-oid="98_3l0a">
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

  // Guard against undefined bbox
  if (
    !bbox ||
    typeof bbox.x !== "number" ||
    typeof bbox.y !== "number" ||
    typeof bbox.width !== "number" ||
    typeof bbox.height !== "number"
  ) {
    console.debug("ObjectOverlay: Invalid bbox data", { objectId: object?.id, bbox });
    return null;
  }

  // Convert bbox coordinates to percentage
  if (!imageWidth || !imageHeight) return null;
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
      data-oid="heq5ywk"
    >
      {/* Label */}
      <div
        className="absolute -top-6 left-0 px-1 py-0.5 text-xs font-medium rounded text-white"
        style={{ backgroundColor: color }}
        data-oid="4zw6-.s"
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
