import { useEffect, useRef, useState, useCallback } from "react";
import type { Scene, SceneObject } from "@/types/dataset";

interface SceneCanvasRendererProps {
  scene: Scene;
  imageUrl: string;
  objects: SceneObject[];
  showObjects: boolean;
  showMasks: boolean;
  selectedObject: SceneObject | undefined;
  onObjectClick: (object: SceneObject) => void;
  className?: string;
}

interface ViewTransform {
  x: number;
  y: number;
  scale: number;
}

export function SceneCanvasRenderer({
  scene,
  imageUrl,
  objects,
  showObjects,
  showMasks,
  selectedObject,
  onObjectClick,
  className = "",
}: SceneCanvasRendererProps) {
  // Add proxy parameter to image URL for CORS support
  const proxiedImageUrl = imageUrl.includes('?') 
    ? `${imageUrl}&proxy=true` 
    : `${imageUrl}?proxy=true`;
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const offscreenCanvasRef = useRef<OffscreenCanvas | null>(null);
  const contextRef = useRef<CanvasRenderingContext2D | null>(null);
  const imageRef = useRef<HTMLImageElement | null>(null);
  const maskImagesRef = useRef<Map<string, HTMLImageElement>>(new Map());
  const animationFrameRef = useRef<number | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [transform, setTransform] = useState<ViewTransform>({
    x: 0,
    y: 0,
    scale: 1,
  });

  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [hoveredObject, setHoveredObject] = useState<SceneObject | null>(null);

  // Color palette for objects
  const getObjectColor = useCallback((objectId: string): string => {
    const colors = [
      "#3b82f6",
      "#10b981",
      "#f59e0b",
      "#8b5cf6",
      "#ef4444",
      "#06b6d4",
      "#84cc16",
    ];
    const index = objects.findIndex((obj) => obj.id === objectId) || 0;
    return colors[index % colors.length];
  }, [objects]);

  // Load main image
  useEffect(() => {
    const img = new Image();
    
    // For API proxy URLs, don't set crossOrigin to avoid CORS issues
    // The API should handle CORS properly
    if (!imageUrl.startsWith('/api/')) {
      img.crossOrigin = "anonymous";
    }
    
    img.onload = () => {
      imageRef.current = img;
      setIsLoading(false);
      
      // Center image on initial load
      if (canvasRef.current) {
        const canvas = canvasRef.current;
        const centerX = (canvas.width - img.width) / 2;
        const centerY = (canvas.height - img.height) / 2;
        setTransform({ x: centerX, y: centerY, scale: 1 });
      }
    };

    img.onerror = (e) => {
      console.error("Failed to load image:", imageUrl, e);
      
      // Retry without crossOrigin if it was set
      if (img.crossOrigin) {
        console.log("Retrying without CORS...");
        const retryImg = new Image();
        retryImg.onload = () => {
          imageRef.current = retryImg;
          setIsLoading(false);
          
          if (canvasRef.current) {
            const canvas = canvasRef.current;
            const centerX = (canvas.width - retryImg.width) / 2;
            const centerY = (canvas.height - retryImg.height) / 2;
            setTransform({ x: centerX, y: centerY, scale: 1 });
          }
        };
        retryImg.onerror = () => {
          console.error("Image load failed after retry:", imageUrl);
          setIsLoading(false);
        };
        retryImg.src = imageUrl;
      } else {
        setIsLoading(false);
      }
    };

    img.src = proxiedImageUrl;
  }, [proxiedImageUrl]);

  // Load mask images
  useEffect(() => {
    if (!showMasks) return;

    const loadMasks = async () => {
      const newMaskImages = new Map<string, HTMLImageElement>();

      for (const obj of objects) {
        if (obj.mask_base64) {
          const maskImg = new Image();
          // Base64 data URLs don't need CORS
          
          await new Promise<void>((resolve) => {
            maskImg.onload = () => {
              newMaskImages.set(obj.id, maskImg);
              resolve();
            };
            maskImg.onerror = () => {
              console.error(`Failed to load mask for object ${obj.id}`);
              resolve();
            };
            maskImg.src = `data:image/png;base64,${obj.mask_base64}`;
          });
        }
      }

      maskImagesRef.current = newMaskImages;
    };

    loadMasks();
  }, [objects, showMasks]);

  // Initialize canvas context
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d", {
      alpha: true,
      desynchronized: true,
    });

    if (!ctx) {
      console.error("Failed to get canvas context");
      return;
    }

    contextRef.current = ctx;

    // Set canvas size to container size
    const resizeCanvas = () => {
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * window.devicePixelRatio;
      canvas.height = rect.height * window.devicePixelRatio;
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
      canvas.style.width = `${rect.width}px`;
      canvas.style.height = `${rect.height}px`;
    };

    resizeCanvas();
    window.addEventListener("resize", resizeCanvas);

    return () => {
      window.removeEventListener("resize", resizeCanvas);
    };
  }, []);

  // Main render function
  const render = useCallback(() => {
    const canvas = canvasRef.current;
    const ctx = contextRef.current;
    const image = imageRef.current;

    if (!canvas || !ctx || !image || isLoading) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width / window.devicePixelRatio, canvas.height / window.devicePixelRatio);

    // Save context state
    ctx.save();

    // Apply transformations
    ctx.translate(transform.x, transform.y);
    ctx.scale(transform.scale, transform.scale);

    // Draw main image
    ctx.drawImage(image, 0, 0, image.width, image.height);

    // Draw SAM2 masks if enabled
    if (showMasks) {
      objects.forEach((obj) => {
        const maskImg = maskImagesRef.current.get(obj.id);
        if (maskImg && obj.bbox) {
          const { x, y, width, height } = obj.bbox;
          
          // Apply color tinting to mask
          ctx.save();
          ctx.globalAlpha = selectedObject?.id === obj.id ? 0.7 : 0.4;
          ctx.globalCompositeOperation = "multiply";
          
          // Draw mask within bounding box
          ctx.drawImage(maskImg, x, y, width, height);
          
          // Apply color overlay
          ctx.globalCompositeOperation = "source-atop";
          ctx.fillStyle = getObjectColor(obj.id);
          ctx.fillRect(x, y, width, height);
          
          ctx.restore();
        }
      });
    }

    // Draw bounding boxes if enabled
    if (showObjects) {
      objects.forEach((obj) => {
        if (!obj.bbox) return;

        const { x, y, width, height } = obj.bbox;
        const color = getObjectColor(obj.id);
        const isSelected = selectedObject?.id === obj.id;
        const isHovered = hoveredObject?.id === obj.id;

        // Draw bounding box
        ctx.strokeStyle = color;
        ctx.lineWidth = isSelected ? 3 : 2;
        ctx.globalAlpha = isSelected ? 1 : isHovered ? 0.9 : 0.7;
        ctx.strokeRect(x, y, width, height);

        // Draw label
        ctx.fillStyle = color;
        ctx.globalAlpha = 1;
        const label = `${obj.label} (${Math.round(obj.confidence * 100)}%)`;
        const fontSize = 12 / transform.scale;
        ctx.font = `${fontSize}px Inter, system-ui, sans-serif`;
        
        // Measure text for background
        const textMetrics = ctx.measureText(label);
        const textHeight = fontSize * 1.2;
        const padding = 4 / transform.scale;

        // Draw label background
        ctx.fillStyle = color;
        ctx.fillRect(
          x,
          y - textHeight - padding,
          textMetrics.width + padding * 2,
          textHeight + padding
        );

        // Draw label text
        ctx.fillStyle = "white";
        ctx.fillText(label, x + padding, y - padding);
      });
    }

    // Restore context state
    ctx.restore();

    // Draw UI overlays (zoom level, etc.)
    ctx.fillStyle = "rgba(0, 0, 0, 0.5)";
    ctx.fillRect(10, 10, 100, 30);
    ctx.fillStyle = "white";
    ctx.font = "14px Inter, system-ui, sans-serif";
    ctx.fillText(`Zoom: ${Math.round(transform.scale * 100)}%`, 20, 30);
  }, [transform, objects, showObjects, showMasks, selectedObject, hoveredObject, isLoading, getObjectColor]);

  // Request animation frame for smooth rendering
  useEffect(() => {
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }

    animationFrameRef.current = requestAnimationFrame(render);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [render]);

  // Mouse wheel zoom
  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    const canvas = canvasRef.current;
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;

    const scaleDelta = e.deltaY > 0 ? 0.9 : 1.1;
    const newScale = Math.max(0.1, Math.min(10, transform.scale * scaleDelta));

    // Zoom towards mouse position
    const scaleChange = newScale - transform.scale;
    const offsetX = -(mouseX - transform.x) * (scaleChange / transform.scale);
    const offsetY = -(mouseY - transform.y) * (scaleChange / transform.scale);

    setTransform((prev) => ({
      x: prev.x + offsetX,
      y: prev.y + offsetY,
      scale: newScale,
    }));
  }, [transform]);

  // Register wheel handler with passive: false to allow preventDefault
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const handleWheelNative = (e: WheelEvent) => {
      e.preventDefault();
      
      const rect = canvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      const scaleDelta = e.deltaY > 0 ? 0.9 : 1.1;
      
      setTransform((prev) => {
        const newScale = Math.max(0.1, Math.min(10, prev.scale * scaleDelta));
        const scaleChange = newScale - prev.scale;
        const offsetX = -(mouseX - prev.x) * (scaleChange / prev.scale);
        const offsetY = -(mouseY - prev.y) * (scaleChange / prev.scale);

        return {
          x: prev.x + offsetX,
          y: prev.y + offsetY,
          scale: newScale,
        };
      });
    };

    canvas.addEventListener('wheel', handleWheelNative, { passive: false });
    
    return () => {
      canvas.removeEventListener('wheel', handleWheelNative);
    };
  }, []);

  // Mouse drag for panning
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.button === 0) {
      setIsDragging(true);
      setDragStart({ x: e.clientX - transform.x, y: e.clientY - transform.y });
    }
  }, [transform]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    const canvas = canvasRef.current;
    const image = imageRef.current;
    
    if (!canvas || !image) return;

    if (isDragging) {
      setTransform((prev) => ({
        ...prev,
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      }));
    } else {
      // Check for object hover
      const rect = canvas.getBoundingClientRect();
      const x = (e.clientX - rect.left - transform.x) / transform.scale;
      const y = (e.clientY - rect.top - transform.y) / transform.scale;

      const hoveredObj = objects.find((obj) => {
        if (!obj.bbox) return false;
        const { x: bx, y: by, width: bw, height: bh } = obj.bbox;
        return x >= bx && x <= bx + bw && y >= by && y <= by + bh;
      });

      setHoveredObject(hoveredObj || null);
      canvas.style.cursor = hoveredObj ? "pointer" : isDragging ? "grabbing" : "grab";
    }
  }, [isDragging, dragStart, transform, objects]);

  const handleMouseUp = useCallback((e: React.MouseEvent) => {
    if (!isDragging && hoveredObject) {
      onObjectClick(hoveredObject);
    }
    setIsDragging(false);
  }, [isDragging, hoveredObject, onObjectClick]);

  const handleMouseLeave = useCallback(() => {
    setIsDragging(false);
    setHoveredObject(null);
  }, []);

  // Reset view
  const resetView = useCallback(() => {
    const canvas = canvasRef.current;
    const image = imageRef.current;
    
    if (canvas && image) {
      const centerX = (canvas.width / window.devicePixelRatio - image.width) / 2;
      const centerY = (canvas.height / window.devicePixelRatio - image.height) / 2;
      setTransform({ x: centerX, y: centerY, scale: 1 });
    }
  }, []);

  // Zoom controls
  const zoomIn = useCallback(() => {
    setTransform((prev) => ({ ...prev, scale: Math.min(10, prev.scale * 1.25) }));
  }, []);

  const zoomOut = useCallback(() => {
    setTransform((prev) => ({ ...prev, scale: Math.max(0.1, prev.scale * 0.8) }));
  }, []);

  // Double click to reset view
  const handleDoubleClick = useCallback(() => {
    resetView();
  }, [resetView]);

  return (
    <div className={`relative w-full h-full ${className}`}>
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-background/50">
          <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      )}
      
      <canvas
        ref={canvasRef}
        className="w-full h-full"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseLeave}
        onDoubleClick={handleDoubleClick}
        style={{ cursor: isDragging ? "grabbing" : "grab" }}
      />

      {/* Export zoom controls for parent component */}
      <div className="absolute bottom-4 right-4 flex space-x-2">
        <button
          onClick={zoomOut}
          className="px-3 py-1 bg-background/90 border rounded-md hover:bg-background"
        >
          -
        </button>
        <button
          onClick={resetView}
          className="px-3 py-1 bg-background/90 border rounded-md hover:bg-background"
        >
          {Math.round(transform.scale * 100)}%
        </button>
        <button
          onClick={zoomIn}
          className="px-3 py-1 bg-background/90 border rounded-md hover:bg-background"
        >
          +
        </button>
      </div>
    </div>
  );
}