import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import {
  Eye,
  Grid,
  BarChart3,
  Filter,
  RefreshCw,
  ArrowLeft,
  Settings,
  Play,
  Pause,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SceneGallery } from "@/components/review/SceneGallery";
import { SceneDetailView } from "@/components/review/SceneDetailView";
import { AnnotationTools } from "@/components/review/AnnotationTools";
import { AIAnalysisPanel } from "@/components/review/AIAnalysisPanel";
import { ReviewProgress } from "@/components/review/ReviewProgress";
import { BatchActions } from "@/components/review/BatchActions";
import { useScenePagination } from "@/hooks/useScenes";
import { useReviewSession } from "@/hooks/useReviews";
import { useDatasets } from "@/hooks/useDatasets";
import type { Scene, SceneObject } from "@/types/dataset";

type ViewMode = "gallery" | "detail";

export function SceneReviewPage() {
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();
  const [viewMode, setViewMode] = useState<ViewMode>("gallery");
  const [selectedScenes, setSelectedScenes] = useState<Set<string>>(new Set());
  const [currentScene, setCurrentScene] = useState<Scene | null>(null);
  const [selectedObject, setSelectedObject] = useState<SceneObject | null>(
    null,
  );
  const [datasetFilter, setDatasetFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("pending");
  const [isSessionActive, setIsSessionActive] = useState(false);

  // Read dataset filter from URL parameters
  useEffect(() => {
    const datasetParam = searchParams.get("dataset");
    if (datasetParam) {
      setDatasetFilter(datasetParam);
    }
  }, [searchParams]);

  // Fetch datasets for filter
  const { data: datasetsData } = useDatasets({ limit: 100 });
  const datasets = datasetsData?.items || [];

  // Fetch scenes with pagination
  const {
    scenes,
    isLoading,
    error,
    getNextScene,
    getPreviousScene,
    getSceneIndex,
  } = useScenePagination({
    dataset_id: datasetFilter !== "all" ? datasetFilter : undefined,
    review_status: statusFilter !== "all" ? statusFilter : undefined,
    limit: 50,
  });

  // Review session management
  const { startSession, endSession } = useReviewSession();

  // Start/end review session
  const handleToggleSession = async () => {
    if (isSessionActive) {
      // End current session
      const session = localStorage.getItem("currentReviewSession");
      if (session) {
        await endSession.mutateAsync(JSON.parse(session).id);
        localStorage.removeItem("currentReviewSession");
      }
      setIsSessionActive(false);
    } else {
      // Start new session
      const session = await startSession.mutateAsync({
        dataset_id: datasetFilter !== "all" ? datasetFilter : undefined,
      });
      localStorage.setItem("currentReviewSession", JSON.stringify(session));
      setIsSessionActive(true);
    }
  };

  // Check for active session on load
  useEffect(() => {
    const session = localStorage.getItem("currentReviewSession");
    setIsSessionActive(!!session);
  }, []);

  const handleSceneSelect = (scene: Scene) => {
    setCurrentScene(scene);
    setViewMode("detail");
    setSelectedObject(null);
  };

  const handleSceneToggle = (sceneId: string) => {
    setSelectedScenes((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(sceneId)) {
        newSet.delete(sceneId);
      } else {
        newSet.add(sceneId);
      }
      return newSet;
    });
  };

  const handleBatchSelect = (scenes: Scene[]) => {
    setSelectedScenes(new Set(scenes.map((s) => s.id)));
  };

  const handleClearSelection = () => {
    setSelectedScenes(new Set());
  };

  const handleProcessingComplete = () => {
    // Force immediate refetch of scene data after AI processing
    queryClient.invalidateQueries({ queryKey: ["scenes"] });
    queryClient.refetchQueries({ queryKey: ["scenes"] });
    
    if (currentScene) {
      queryClient.invalidateQueries({ queryKey: ["scene", currentScene.id] });
      queryClient.invalidateQueries({
        queryKey: ["sceneObjects", currentScene.id],
      });
      
      // Force immediate refetch of the current scene data
      queryClient.refetchQueries({ queryKey: ["scene", currentScene.id] });
      queryClient.refetchQueries({
        queryKey: ["sceneObjects", currentScene.id],
      });
    }
  };

  const handleNextScene = () => {
    if (!currentScene) return;
    const nextScene = getNextScene(currentScene.id);
    if (nextScene) {
      setCurrentScene(nextScene);
      setSelectedObject(null);
    }
  };

  const handlePreviousScene = () => {
    if (!currentScene) return;
    const prevScene = getPreviousScene(currentScene.id);
    if (prevScene) {
      setCurrentScene(prevScene);
      setSelectedObject(null);
    }
  };

  const handleCloseDetail = () => {
    setViewMode("gallery");
    setCurrentScene(null);
    setSelectedObject(null);
  };

  const getCurrentSceneIndex = () => {
    if (!currentScene) return -1;
    return getSceneIndex(currentScene.id);
  };

  const getNextSceneId = () => {
    if (!currentScene) return undefined;
    const nextScene = getNextScene(currentScene.id);
    return nextScene?.id;
  };

  const getPreviousSceneId = () => {
    if (!currentScene) return undefined;
    const prevScene = getPreviousScene(currentScene.id);
    return prevScene?.id;
  };

  const selectedScenesList = scenes.filter((scene) =>
    selectedScenes.has(scene.id),
  );

  return (
    <div className="min-h-screen bg-background" data-oid="-keqib4">
      {/* Header */}
      <div className="border-b bg-card" data-oid="rhib7r_">
        <div className="container mx-auto px-4 py-4" data-oid="zzqt_c:">
          <div className="flex items-center justify-between" data-oid="b6561dd">
            <div className="flex items-center space-x-4" data-oid="imz_6f5">
              <div data-oid="7-u:0kh">
                <h1
                  className="text-2xl font-bold tracking-tight"
                  data-oid="xb6js-8"
                >
                  Scene Review
                </h1>
                <p className="text-sm text-muted-foreground" data-oid="_u_792v">
                  Human-in-the-loop quality control for AI predictions
                </p>
              </div>

              {viewMode === "detail" && currentScene && (
                <div className="flex items-center space-x-2" data-oid="elcnw5l">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleCloseDetail}
                    data-oid=".gs6l34"
                  >
                    <ArrowLeft className="h-4 w-4 mr-2" data-oid=".6pww7n" />
                    Back to Gallery
                  </Button>
                  <Badge variant="outline" data-oid="5-k.swl">
                    Scene {getCurrentSceneIndex() + 1} of {scenes.length}
                  </Badge>
                </div>
              )}
            </div>

            <div className="flex items-center space-x-2" data-oid="fqd-tzd">
              {/* Session Control */}
              <Button
                variant={isSessionActive ? "destructive" : "default"}
                size="sm"
                onClick={handleToggleSession}
                disabled={startSession.isPending || endSession.isPending}
                data-oid="r6y1ntl"
              >
                {isSessionActive ? (
                  <>
                    <Pause className="h-4 w-4 mr-2" data-oid="syc:8h_" />
                    End Session
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" data-oid="kaxcg2:" />
                    Start Session
                  </>
                )}
              </Button>

              {/* Filters */}
              <Select
                value={datasetFilter}
                onValueChange={setDatasetFilter}
                data-oid="j5zya4_"
              >
                <SelectTrigger className="w-48" data-oid="kp85krk">
                  <SelectValue placeholder="All Datasets" data-oid="hn-u.w_" />
                </SelectTrigger>
                <SelectContent data-oid="-r009i_">
                  <SelectItem value="all" data-oid=".sv51ke">
                    All Datasets
                  </SelectItem>
                  {datasets.map((dataset) => (
                    <SelectItem
                      key={dataset.id}
                      value={dataset.id}
                      data-oid="jqds5.7"
                    >
                      {dataset.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select
                value={statusFilter}
                onValueChange={setStatusFilter}
                data-oid="cq5eop2"
              >
                <SelectTrigger className="w-40" data-oid="coqenmn">
                  <SelectValue placeholder="Status" data-oid="hv4ikt4" />
                </SelectTrigger>
                <SelectContent data-oid="5t4n6i8">
                  <SelectItem value="all" data-oid="t..xwvb">
                    All Status
                  </SelectItem>
                  <SelectItem value="pending" data-oid="98z-om6">
                    Pending
                  </SelectItem>
                  <SelectItem value="approved" data-oid="zno_m9:">
                    Approved
                  </SelectItem>
                  <SelectItem value="rejected" data-oid="-30oq7d">
                    Rejected
                  </SelectItem>
                  <SelectItem value="corrected" data-oid="wplmrr0">
                    Corrected
                  </SelectItem>
                </SelectContent>
              </Select>

              {/* View Mode */}
              <div className="flex border rounded-md" data-oid="-5nb4sq">
                <Button
                  variant={viewMode === "gallery" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setViewMode("gallery")}
                  className="rounded-r-none"
                  data-oid="7tfim_5"
                >
                  <Grid className="h-4 w-4" data-oid="1nuvhka" />
                </Button>
                <Button
                  variant={viewMode === "detail" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => currentScene && setViewMode("detail")}
                  className="rounded-l-none"
                  disabled={!currentScene}
                  data-oid="fq:1nc8"
                >
                  <Eye className="h-4 w-4" data-oid="5xfdk5u" />
                </Button>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={() => window.location.reload()}
                data-oid="uo:5v.g"
              >
                <RefreshCw className="h-4 w-4" data-oid="q4x94do" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-6" data-oid="l8gzyhp">
        {viewMode === "gallery" ? (
          <div className="space-y-6" data-oid="w1.u8tp">
            {/* Progress Overview */}
            <div
              className="grid grid-cols-1 lg:grid-cols-3 gap-6"
              data-oid="o1p6kps"
            >
              <div className="lg:col-span-2" data-oid="_.9tyf7">
                <ReviewProgress
                  datasetId={
                    datasetFilter !== "all" ? datasetFilter : undefined
                  }
                  data-oid="46j8pdd"
                />
              </div>
              <div className="space-y-4" data-oid="r_0p7t6">
                <div
                  className="bg-card border rounded-lg p-4"
                  data-oid=".7-2ze4"
                >
                  <h3 className="font-medium mb-2" data-oid="abymprc">
                    Quick Stats
                  </h3>
                  <div className="space-y-2 text-sm" data-oid="912lrll">
                    <div className="flex justify-between" data-oid="qqkakun">
                      <span data-oid="c9kwrua">Total Scenes:</span>
                      <span className="font-mono" data-oid="3h1vy1k">
                        {scenes.length}
                      </span>
                    </div>
                    <div className="flex justify-between" data-oid="ippa._m">
                      <span data-oid="cd9cdzo">Selected:</span>
                      <span className="font-mono" data-oid="dhrfqzl">
                        {selectedScenes.size}
                      </span>
                    </div>
                    {isSessionActive && (
                      <div
                        className="flex justify-between text-green-600"
                        data-oid="9z66l82"
                      >
                        <span data-oid=":.1ni83">Session Active:</span>
                        <Badge
                          variant="default"
                          className="text-xs"
                          data-oid="xdkib77"
                        >
                          Recording
                        </Badge>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Batch Actions */}
            {selectedScenes.size > 0 && (
              <BatchActions
                selectedScenes={selectedScenesList}
                onClearSelection={handleClearSelection}
                data-oid="xs6hp4l"
              />
            )}

            {/* Scene Gallery */}
            <SceneGallery
              datasetId={datasetFilter !== "all" ? datasetFilter : undefined}
              selectedScenes={selectedScenes}
              onSceneSelect={handleSceneSelect}
              onSceneToggle={handleSceneToggle}
              onBatchSelect={handleBatchSelect}
              data-oid="tg5q946"
            />
          </div>
        ) : (
          currentScene && (
            <div className="h-[calc(100vh-120px)]">
              <SceneDetailView
                sceneId={currentScene.id}
                onNext={handleNextScene}
                onPrevious={handlePreviousScene}
                onClose={handleCloseDetail}
                selectedObject={selectedObject}
                onObjectSelect={setSelectedObject}
                nextSceneId={getNextSceneId()}
                previousSceneId={getPreviousSceneId()}
                currentIndex={getCurrentSceneIndex()}
                totalScenes={scenes.length}
                className="w-full h-full"
              />
            </div>
          )
        )}
        {error && (
          <p className="text-sm text-muted-foreground" data-oid="t21k.ps">
            {(error as Error)?.message || "An error occurred"}
          </p>
        )}
      </div>
    </div>
  );
}
