import { useState, useCallback, useEffect } from "react";
import {
  Download,
  ChevronLeft,
  ChevronRight,
  Eye,
  Layers,
  X,
  AlertTriangle,
  ImageIcon,
  TagIcon,
  Palette,
  Ruler,
  Check,
  XCircle,
  Edit3,
  BarChart3,
  Activity,
  Save,
  RotateCcw,
  Plus,
  Minus,
  ChevronDown,
  RefreshCw,
  Zap,
  Play,
  CheckCircle,
  Users,
  Target,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Progress } from "@/components/ui/progress";
import { useToast } from "@/components/ui/use-toast";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import { useScene, useSceneImages, useScenePrefetch } from "@/hooks/useScenes";
import { useReviewKeyboard, useReviewWorkflow, useSubmitObjectReview, useSubmitBatchReviews } from "@/hooks/useReviews";
import { SceneCanvasRenderer } from "./SceneCanvasRenderer";
import type { Scene, SceneObject, StyleClassification } from "@/types/dataset";

// Constants for editing
const SCENE_TYPES = [
  { value: "living_room", label: "Living Room" },
  { value: "bedroom", label: "Bedroom" },
  { value: "kitchen", label: "Kitchen" },
  { value: "dining_room", label: "Dining Room" },
  { value: "bathroom", label: "Bathroom" },
  { value: "office", label: "Office" },
] as const;

const STYLE_CODES = [
  { code: "contemporary", name: "Contemporary" },
  { code: "traditional", name: "Traditional" },
  { code: "modern", name: "Modern" },
  { code: "rustic", name: "Rustic" },
  { code: "industrial", name: "Industrial" },
  { code: "minimalist", name: "Minimalist" },
  { code: "bohemian", name: "Bohemian" },
  { code: "scandinavian", name: "Scandinavian" },
] as const;

interface SceneDetailViewProps {
  sceneId: string;
  onNext?: () => void;
  onPrevious?: () => void;
  onClose?: () => void;
  selectedObject?: SceneObject | null;
  onObjectSelect?: (object: SceneObject | null) => void;
  nextSceneId?: string;
  previousSceneId?: string;
  currentIndex?: number;
  totalScenes?: number;
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
  currentIndex = 0,
  totalScenes = 0,
  className,
}: SceneDetailViewProps) {
  const [showObjects, setShowObjects] = useState(true);
  const [showMasks, setShowMasks] = useState(false);
  const [sidebarVisible, setSidebarVisible] = useState(true);
  
  // Editing state
  const [isEditing, setIsEditing] = useState(false);
  const [editedSceneType, setEditedSceneType] = useState("");
  const [editedStyles, setEditedStyles] = useState<StyleClassification[]>([]);
  const [notes, setNotes] = useState("");
  const [expandedSections, setExpandedSections] = useState({
    aiAnalysis: false,
    editing: false,
  });
  
  // Processing state
  const [processingStatus, setProcessingStatus] = useState<"idle" | "processing" | "completed" | "error">("idle");
  const [processingProgress, setProcessingProgress] = useState(0);
  
  // Object review state
  const [reviewingObjectId, setReviewingObjectId] = useState<string | null>(null);
  const [bulkReviewInProgress, setBulkReviewInProgress] = useState(false);

  const { data: scene, isLoading, error } = useScene(sceneId, true);
  const { prefetchScene } = useScenePrefetch();
  const reviewWorkflow = useReviewWorkflow(sceneId);
  const { toast } = useToast();
  const submitObjectReview = useSubmitObjectReview();
  const submitBatchReviews = useSubmitBatchReviews();

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

  // Initialize editing values when scene changes
  useEffect(() => {
    if (scene) {
      setEditedSceneType(scene.scene_type || "");
      setEditedStyles(scene.styles || []);
      setNotes("");
    }
  }, [scene]);

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

  // Editing functions
  const handleSaveCorrections = async () => {
    if (!scene) return;
    try {
      await reviewWorkflow.correctScene({
        scene_type: editedSceneType !== scene.scene_type ? editedSceneType : undefined,
        styles: JSON.stringify(editedStyles) !== JSON.stringify(scene.styles || [])
          ? editedStyles : undefined,
        notes: notes || undefined,
      });
      setIsEditing(false);
      setNotes("");
    } catch (error) {
      // Error handled by mutation
    }
  };

  const handleResetEdits = () => {
    if (scene) {
      setEditedSceneType(scene.scene_type || "");
      setEditedStyles(scene.styles || []);
      setNotes("");
    }
  };

  const addStyle = (styleCode: string) => {
    if (!editedStyles.find((s) => s.code === styleCode)) {
      setEditedStyles([...editedStyles, { code: styleCode, conf: 0.5 }]);
    }
  };

  const removeStyle = (styleCode: string) => {
    setEditedStyles(editedStyles.filter((s) => s.code !== styleCode));
  };

  const toggleSection = (section: keyof typeof expandedSections) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const hasChanges = scene ? (
    editedSceneType !== scene.scene_type ||
    JSON.stringify(editedStyles) !== JSON.stringify(scene.styles || [])
  ) : false;

  // AI Processing function
  const triggerAIProcessing = async () => {
    if (!scene) return;

    setProcessingStatus("processing");
    setProcessingProgress(0);
    
    try {
      // Start the processing job
      const processResponse = await fetch(
        `/api/v1/scenes/${scene.id}/process`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            force_reprocess: true,
          }),
        },
      );

      if (!processResponse.ok) {
        throw new Error(`Processing failed: ${processResponse.statusText}`);
      }

      const processResult = await processResponse.json();
      const jobId = processResult.job_id;

      if (!jobId) {
        throw new Error("No job ID returned from processing request");
      }

      // Poll for progress updates
      const pollProgress = async (): Promise<void> => {
        const statusResponse = await fetch(
          `/api/v1/scenes/${scene.id}/process-status`,
        );

        if (!statusResponse.ok) {
          throw new Error("Failed to get processing status");
        }

        const statusData = await statusResponse.json();
        setProcessingProgress(Math.min(statusData.progress || 0, 100));

        if (statusData.status === "succeeded") {
          setProcessingStatus("completed");
          toast({
            title: "Processing Complete",
            description: "Scene has been successfully reanalyzed with AI.",
          });
          
          // Refresh the scene data
          window.location.reload(); // Simple refresh for now
          return;
        } else if (statusData.status === "failed") {
          throw new Error(statusData.error || "Processing failed");
        } else if (statusData.status === "processing") {
          // Continue polling
          setTimeout(pollProgress, 2000);
        }
      };

      // Start polling
      setTimeout(pollProgress, 1000);

    } catch (error) {
      setProcessingStatus("error");
      toast({
        title: "Processing Failed", 
        description: error instanceof Error ? error.message : "An error occurred",
        variant: "destructive",
      });
    }
  };

  // Check if scene needs processing
  const needsProcessing = scene ? (
    !scene.scene_type ||
    !scene.objects ||
    scene.objects.length === 0 ||
    !scene.styles ||
    scene.styles.length === 0
  ) : false;

  // Object review functions
  const handleObjectApprove = async (objectId: string) => {
    setReviewingObjectId(objectId);
    try {
      await submitObjectReview.mutateAsync({
        object_id: objectId,
        status: "approved",
      });
      toast({
        title: "Object Approved",
        description: "Object has been successfully approved.",
      });
    } catch (error) {
      toast({
        title: "Approval Failed",
        description: error instanceof Error ? error.message : "An error occurred",
        variant: "destructive",
      });
    } finally {
      setReviewingObjectId(null);
    }
  };

  const handleObjectReject = async (objectId: string) => {
    setReviewingObjectId(objectId);
    try {
      await submitObjectReview.mutateAsync({
        object_id: objectId,
        status: "rejected",
      });
      toast({
        title: "Object Rejected",
        description: "Object has been rejected.",
      });
    } catch (error) {
      toast({
        title: "Rejection Failed",
        description: error instanceof Error ? error.message : "An error occurred",
        variant: "destructive",
      });
    } finally {
      setReviewingObjectId(null);
    }
  };

  const handleBulkApproveObjects = async () => {
    if (!normalizedObjects.length) return;
    
    setBulkReviewInProgress(true);
    try {
      const result = await submitBatchReviews.mutateAsync({
        scene_reviews: [], // API requires this field even if empty
        object_reviews: normalizedObjects.map(obj => ({
          object_id: obj.id,
          status: "approved" as const,
        }))
      });
      
      console.log('Batch reviews result:', result);
      
      // Check if result is valid
      if (!result) {
        throw new Error('No response received from server');
      }
      
      toast({
        title: "Bulk Approval Complete",
        description: `Successfully approved ${result.objects_updated || normalizedObjects.length} objects.`,
      });
    } catch (error) {
      console.error('Batch approval error:', error);
      
      let errorMessage = "An error occurred";
      if (error instanceof Error) {
        errorMessage = error.message;
      } else if (typeof error === 'string') {
        errorMessage = error;
      } else if (error && typeof error === 'object' && 'message' in error) {
        errorMessage = String(error.message);
      }
      
      toast({
        title: "Bulk Approval Failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setBulkReviewInProgress(false);
    }
  };

  // Normalize objects to ensure bbox is present and map mask fields
  const normalizedObjects: SceneObject[] = (scene?.objects || []).map((obj: any) => {
    let normalizedObj = { ...obj };
    
    // Map mask_key to r2_key_mask for compatibility
    if (obj.mask_key && !obj.r2_key_mask) {
      normalizedObj.r2_key_mask = obj.mask_key;
    }
    
    // Also ensure canvas renderer can find it as mask_key
    if (obj.r2_key_mask && !obj.mask_key) {
      normalizedObj.mask_key = obj.r2_key_mask;
    }
    
    if (obj && !obj.bbox) {
      if (
        typeof obj.bbox_x === "number" &&
        typeof obj.bbox_y === "number" &&
        typeof obj.bbox_w === "number" &&
        typeof obj.bbox_h === "number"
      ) {
        return {
          ...normalizedObj,
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
          ...normalizedObj,
          bbox: {
            x: x1,
            y: y1,
            width: x2 - x1,
            height: y2 - y1,
          },
        } as SceneObject;
      }
    }
    return normalizedObj as SceneObject;
  });

  if (error) {
    return (
      <Card className={`w-full h-96 flex items-center justify-center ${className}`}>
        <CardContent className="text-center">
          <AlertTriangle className="h-12 w-12 text-destructive mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2">Failed to load scene</h3>
          <p className="text-sm text-muted-foreground">
            {(error as any)?.message || "An error occurred"}
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
              onClick={() => {
                const hasAnyMasks = normalizedObjects.some(obj => obj.has_mask || obj.mask_base64 || obj.mask_url);
                if (!hasAnyMasks && !showMasks) {
                  toast({
                    title: "No Masks Available",
                    description: "This scene doesn't have SAM2 segmentation masks. Click 'Reanalyze Scene' in the sidebar to generate masks.",
                    variant: "destructive",
                  });
                  // Open sidebar to show reanalyze button
                  setSidebarVisible(true);
                  return; // Don't toggle if no masks available
                }
                setShowMasks(!showMasks);
              }}
              disabled={normalizedObjects.length === 0}
            >
              <Layers className="h-4 w-4 mr-1" />
              Masks
              {normalizedObjects.some(obj => obj.has_mask || obj.mask_base64 || obj.mask_url) && (
                <span className="ml-1 text-xs bg-green-500 text-white rounded-full px-1">
                  {normalizedObjects.filter(obj => obj.has_mask || obj.mask_base64 || obj.mask_url).length}
                </span>
              )}
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
            reviewingObjectId={reviewingObjectId}
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

          {/* Review Actions */}
          <Card className="m-4 my-2">
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center">
                <Check className="h-4 w-4 mr-2" />
                Review Actions
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="space-y-2">
                <div className="text-sm font-medium">Scene Review</div>
                <div className="flex space-x-2">
                  <Button
                    size="sm"
                    onClick={() => reviewWorkflow.approveScene()}
                    disabled={reviewWorkflow.isSubmitting}
                    className="flex-1"
                  >
                    <Check className="h-4 w-4 mr-1" />
                    Approve Scene
                  </Button>
                  <Button
                    size="sm"
                    variant="destructive"
                    onClick={() => reviewWorkflow.rejectScene()}
                    disabled={reviewWorkflow.isSubmitting}
                    className="flex-1"
                  >
                    <XCircle className="h-4 w-4 mr-1" />
                    Reject Scene
                  </Button>
                </div>
              </div>

              {/* Bulk Object Actions */}
              {normalizedObjects.length > 0 && (
                <div className="space-y-2 pt-2 border-t">
                  <div className="text-sm font-medium">Object Review</div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleBulkApproveObjects}
                    disabled={bulkReviewInProgress || submitBatchReviews.isPending}
                    className="w-full"
                  >
                    {bulkReviewInProgress ? (
                      <>
                        <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                        Approving {normalizedObjects.length} objects...
                      </>
                    ) : (
                      <>
                        <Users className="h-4 w-4 mr-2" />
                        Bulk Approve All Objects ({normalizedObjects.length})
                      </>
                    )}
                  </Button>
                </div>
              )}
              
              {/* Progress Information */}
              <div className="pt-2 border-t">
                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="text-muted-foreground">Session Progress</span>
                  <Badge variant="outline" className="text-xs">
                    {currentIndex + 1} of {totalScenes}
                  </Badge>
                </div>
                <div className="text-xs text-muted-foreground space-y-1">
                  <div>• A: Approve scene</div>
                  <div>• R: Reject scene</div>
                  <div>• ← → Navigate scenes</div>
                  <div>• Esc: Close view</div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* AI Analysis Panel */}
          <Card className="m-4 my-2">
            <Collapsible
              open={expandedSections.aiAnalysis}
              onOpenChange={() => toggleSection('aiAnalysis')}
            >
              <CollapsibleTrigger>
                <CardHeader className="pb-3 cursor-pointer hover:bg-muted/50">
                  <CardTitle className="text-base flex items-center justify-between">
                    <div className="flex items-center">
                      <Activity className="h-4 w-4 mr-2" />
                      AI Analysis
                    </div>
                    {expandedSections.aiAnalysis ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                  </CardTitle>
                </CardHeader>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <CardContent className="space-y-4">
                  {/* Scene Classification Details */}
                  <div>
                    <div className="text-sm font-medium mb-2">Scene Classification</div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm">{scene.scene_type?.replace("_", " ")}</span>
                        <Badge variant="outline" className="text-xs">
                          {scene.scene_conf ? `${(scene.scene_conf * 100).toFixed(0)}%` : "N/A"}
                        </Badge>
                      </div>
                      
                      {/* Object Detection Summary */}
                      <div>
                        <div className="text-sm text-muted-foreground mb-1">Object Detection</div>
                        <div className="text-sm">
                          {normalizedObjects.length} objects detected
                          {normalizedObjects.length > 0 && (
                            <span className="text-muted-foreground ml-1">
                              (avg conf: {(normalizedObjects.reduce((acc, obj) => acc + obj.confidence, 0) / normalizedObjects.length * 100).toFixed(0)}%)
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Processing Status */}
                      <div className="pt-2 border-t">
                        <div className="text-sm text-muted-foreground mb-3">
                          Status: {scene.review_status || "pending"}
                        </div>
                        
                        {/* Reanalyze Button */}
                        <div className="space-y-2">
                          {needsProcessing && (
                            <div className="text-xs text-amber-600 bg-amber-50 p-2 rounded border">
                              ⚠️ Scene needs AI analysis
                            </div>
                          )}
                          
                          <Button
                            size="sm"
                            variant={needsProcessing ? "default" : "outline"}
                            onClick={triggerAIProcessing}
                            disabled={processingStatus === "processing"}
                            className="w-full"
                          >
                            {processingStatus === "processing" ? (
                              <>
                                <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                                Processing...
                              </>
                            ) : (
                              <>
                                <Zap className="h-4 w-4 mr-2" />
                                Reanalyze Scene
                              </>
                            )}
                          </Button>
                          
                          {processingStatus === "processing" && (
                            <div className="space-y-2">
                              <Progress value={processingProgress} className="h-2" />
                              <div className="text-xs text-center text-muted-foreground">
                                {processingProgress}% complete
                              </div>
                            </div>
                          )}
                          
                          {processingStatus === "completed" && (
                            <div className="text-xs text-green-600 bg-green-50 p-2 rounded border">
                              ✅ Analysis completed successfully
                            </div>
                          )}
                          
                          {processingStatus === "error" && (
                            <div className="text-xs text-red-600 bg-red-50 p-2 rounded border">
                              ❌ Analysis failed - check console for details
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </CollapsibleContent>
            </Collapsible>
          </Card>

          {/* Edit Scene Panel */}
          <Card className="m-4 my-2">
            <Collapsible
              open={expandedSections.editing}
              onOpenChange={() => toggleSection('editing')}
            >
              <CollapsibleTrigger>
                <CardHeader className="pb-3 cursor-pointer hover:bg-muted/50">
                  <CardTitle className="text-base flex items-center justify-between">
                    <div className="flex items-center">
                      <Edit3 className="h-4 w-4 mr-2" />
                      Edit Scene
                    </div>
                    {expandedSections.editing ? (
                      <ChevronDown className="h-4 w-4" />
                    ) : (
                      <ChevronRight className="h-4 w-4" />
                    )}
                  </CardTitle>
                </CardHeader>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <CardContent className="space-y-4">
                  {/* Scene Type Editing */}
                  <div>
                    <Label htmlFor="scene-type" className="text-sm font-medium">
                      Scene Type
                    </Label>
                    <Select
                      value={editedSceneType}
                      onValueChange={setEditedSceneType}
                    >
                      <SelectTrigger className="mt-1">
                        <SelectValue placeholder="Select scene type" />
                      </SelectTrigger>
                      <SelectContent>
                        {SCENE_TYPES.map((type) => (
                          <SelectItem key={type.value} value={type.value}>
                            {type.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Style Editing */}
                  <div>
                    <Label className="text-sm font-medium">Styles</Label>
                    <div className="mt-2 space-y-2">
                      {editedStyles.map((style) => (
                        <div key={style.code} className="flex items-center justify-between">
                          <Badge variant="outline">{style.code}</Badge>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => removeStyle(style.code)}
                          >
                            <Minus className="h-3 w-3" />
                          </Button>
                        </div>
                      ))}
                      
                      <Select onValueChange={addStyle}>
                        <SelectTrigger>
                          <SelectValue placeholder="Add style" />
                        </SelectTrigger>
                        <SelectContent>
                          {STYLE_CODES.filter(style => 
                            !editedStyles.find(s => s.code === style.code)
                          ).map((style) => (
                            <SelectItem key={style.code} value={style.code}>
                              {style.name}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  {/* Notes */}
                  <div>
                    <Label htmlFor="notes" className="text-sm font-medium">
                      Correction Notes
                    </Label>
                    <Textarea
                      id="notes"
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                      placeholder="Add notes about corrections..."
                      className="mt-1"
                      rows={3}
                    />
                  </div>

                  {/* Action Buttons */}
                  <div className="flex space-x-2 pt-2">
                    <Button
                      size="sm"
                      onClick={handleSaveCorrections}
                      disabled={!hasChanges || reviewWorkflow.isSubmitting}
                      className="flex-1"
                    >
                      <Save className="h-4 w-4 mr-1" />
                      Save Changes
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={handleResetEdits}
                      disabled={!hasChanges}
                    >
                      <RotateCcw className="h-4 w-4 mr-1" />
                      Reset
                    </Button>
                  </div>
                </CardContent>
              </CollapsibleContent>
            </Collapsible>
          </Card>

          {/* Selected Object Details */}
          {selectedObject && (
            <Card className={`m-4 mt-0 flex-1 overflow-auto ${
              reviewingObjectId === selectedObject.id ? 'ring-2 ring-blue-500 ring-opacity-50' : ''
            }`}>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center justify-between">
                  <div className="flex items-center">
                    <TagIcon className="h-4 w-4 mr-2" />
                    Object Details
                    {reviewingObjectId === selectedObject.id && (
                      <Target className="h-4 w-4 ml-2 text-blue-500 animate-pulse" />
                    )}
                  </div>
                  <div className="flex space-x-1">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleObjectApprove(selectedObject.id)}
                      disabled={reviewingObjectId !== null || submitObjectReview.isPending}
                      className="text-green-600 hover:text-green-700"
                    >
                      <CheckCircle className="h-3 w-3" />
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleObjectReject(selectedObject.id)}
                      disabled={reviewingObjectId !== null || submitObjectReview.isPending}
                      className="text-red-600 hover:text-red-700"
                    >
                      <XCircle className="h-3 w-3" />
                    </Button>
                  </div>
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

                {/* Review Status */}
                {reviewingObjectId === selectedObject.id && (
                  <div className="text-xs text-blue-600 bg-blue-50 p-2 rounded border animate-pulse">
                    🎯 Reviewing this object...
                  </div>
                )}

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
                {normalizedObjects.map((obj) => (
                  <div
                    key={obj.id}
                    className={`flex items-center justify-between p-2 rounded border hover:bg-muted/50 ${
                      reviewingObjectId === obj.id ? 'ring-2 ring-blue-500 ring-opacity-50 bg-blue-50' : ''
                    }`}
                  >
                    <div 
                      className="flex items-center space-x-2 flex-1 cursor-pointer"
                      onClick={() => handleObjectClick(obj)}
                    >
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: getObjectColor(obj.id) }}
                      />
                      <span className="text-sm font-medium">{obj.label}</span>
                      {reviewingObjectId === obj.id && (
                        <Target className="h-3 w-3 text-blue-500 animate-pulse" />
                      )}
                    </div>
                    <div className="flex items-center space-x-2">
                      <span className="text-xs font-mono text-muted-foreground">
                        {(obj.confidence * 100).toFixed(0)}%
                      </span>
                      <div className="flex space-x-1">
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleObjectApprove(obj.id);
                          }}
                          disabled={reviewingObjectId !== null || submitObjectReview.isPending}
                          className="h-6 w-6 p-0 text-green-600 hover:text-green-700 hover:bg-green-50"
                        >
                          <CheckCircle className="h-3 w-3" />
                        </Button>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleObjectReject(obj.id);
                          }}
                          disabled={reviewingObjectId !== null || submitObjectReview.isPending}
                          className="h-6 w-6 p-0 text-red-600 hover:text-red-700 hover:bg-red-50"
                        >
                          <XCircle className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
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