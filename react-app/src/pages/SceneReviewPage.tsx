import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
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
    <div className="min-h-screen bg-background" data-oid="2yumk3n">
      {/* Header */}
      <div className="border-b bg-card" data-oid="0xeeba0">
        <div className="container mx-auto px-4 py-4" data-oid="cy60cwg">
          <div className="flex items-center justify-between" data-oid="_2a_ks-">
            <div className="flex items-center space-x-4" data-oid="zenm:36">
              <div data-oid="aoftif8">
                <h1
                  className="text-2xl font-bold tracking-tight"
                  data-oid="vvgd_k-"
                >
                  Scene Review
                </h1>
                <p className="text-sm text-muted-foreground" data-oid="e6898or">
                  Human-in-the-loop quality control for AI predictions
                </p>
              </div>

              {viewMode === "detail" && currentScene && (
                <div className="flex items-center space-x-2" data-oid="28a9a6t">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleCloseDetail}
                    data-oid="n-3.03d"
                  >
                    <ArrowLeft className="h-4 w-4 mr-2" data-oid="gg00fwi" />
                    Back to Gallery
                  </Button>
                  <Badge variant="outline" data-oid="k-:1zjn">
                    Scene {getCurrentSceneIndex() + 1} of {scenes.length}
                  </Badge>
                </div>
              )}
            </div>

            <div className="flex items-center space-x-2" data-oid="gcoi3.p">
              {/* Session Control */}
              <Button
                variant={isSessionActive ? "destructive" : "default"}
                size="sm"
                onClick={handleToggleSession}
                disabled={startSession.isPending || endSession.isPending}
                data-oid="lq-d_qv"
              >
                {isSessionActive ? (
                  <>
                    <Pause className="h-4 w-4 mr-2" data-oid="vq0o87o" />
                    End Session
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4 mr-2" data-oid="vcqv6v0" />
                    Start Session
                  </>
                )}
              </Button>

              {/* Filters */}
              <Select
                value={datasetFilter}
                onValueChange={setDatasetFilter}
                data-oid="ji.ds37"
              >
                <SelectTrigger className="w-48" data-oid="wjpi01x">
                  <SelectValue placeholder="All Datasets" data-oid="_:8wuwa" />
                </SelectTrigger>
                <SelectContent data-oid="b0gc3qd">
                  <SelectItem value="all" data-oid="eeob3lp">
                    All Datasets
                  </SelectItem>
                  {datasets.map((dataset) => (
                    <SelectItem
                      key={dataset.id}
                      value={dataset.id}
                      data-oid="-lid_wh"
                    >
                      {dataset.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>

              <Select
                value={statusFilter}
                onValueChange={setStatusFilter}
                data-oid="7sg61j:"
              >
                <SelectTrigger className="w-40" data-oid="mmlai7h">
                  <SelectValue placeholder="Status" data-oid="dloqhe." />
                </SelectTrigger>
                <SelectContent data-oid="y:qcwhe">
                  <SelectItem value="all" data-oid="uuywk37">
                    All Status
                  </SelectItem>
                  <SelectItem value="pending" data-oid="9sgr3-b">
                    Pending
                  </SelectItem>
                  <SelectItem value="approved" data-oid="6rs07f3">
                    Approved
                  </SelectItem>
                  <SelectItem value="rejected" data-oid="a3djcpk">
                    Rejected
                  </SelectItem>
                  <SelectItem value="corrected" data-oid="-44p-sy">
                    Corrected
                  </SelectItem>
                </SelectContent>
              </Select>

              {/* View Mode */}
              <div className="flex border rounded-md" data-oid=".ez_lxn">
                <Button
                  variant={viewMode === "gallery" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setViewMode("gallery")}
                  className="rounded-r-none"
                  data-oid="c83lpr3"
                >
                  <Grid className="h-4 w-4" data-oid="i:yi:rv" />
                </Button>
                <Button
                  variant={viewMode === "detail" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => currentScene && setViewMode("detail")}
                  className="rounded-l-none"
                  disabled={!currentScene}
                  data-oid="rvjyr55"
                >
                  <Eye className="h-4 w-4" data-oid="n8w4:ej" />
                </Button>
              </div>

              <Button
                variant="outline"
                size="sm"
                onClick={() => window.location.reload()}
                data-oid="u5w694:"
              >
                <RefreshCw className="h-4 w-4" data-oid="2.3rv-h" />
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="container mx-auto px-4 py-6" data-oid="2f7-l_6">
        {viewMode === "gallery" ? (
          <div className="space-y-6" data-oid="q.5:do_">
            {/* Progress Overview */}
            <div
              className="grid grid-cols-1 lg:grid-cols-3 gap-6"
              data-oid="z-5ykwv"
            >
              <div className="lg:col-span-2" data-oid="oou-7ru">
                <ReviewProgress
                  datasetId={
                    datasetFilter !== "all" ? datasetFilter : undefined
                  }
                  data-oid="k2feiba"
                />
              </div>
              <div className="space-y-4" data-oid="::ji2um">
                <div
                  className="bg-card border rounded-lg p-4"
                  data-oid="6giqh8x"
                >
                  <h3 className="font-medium mb-2" data-oid="oal:u:o">
                    Quick Stats
                  </h3>
                  <div className="space-y-2 text-sm" data-oid="9x26lru">
                    <div className="flex justify-between" data-oid="__0ykqu">
                      <span data-oid="dg9hnar">Total Scenes:</span>
                      <span className="font-mono" data-oid="yc06p5b">
                        {scenes.length}
                      </span>
                    </div>
                    <div className="flex justify-between" data-oid="fxmeyxr">
                      <span data-oid="bfoo_8p">Selected:</span>
                      <span className="font-mono" data-oid="wfpq:sb">
                        {selectedScenes.size}
                      </span>
                    </div>
                    {isSessionActive && (
                      <div
                        className="flex justify-between text-green-600"
                        data-oid="35dd6q8"
                      >
                        <span data-oid="kfee2y8">Session Active:</span>
                        <Badge
                          variant="default"
                          className="text-xs"
                          data-oid="vae.ous"
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
                data-oid="db-myz6"
              />
            )}

            {/* Scene Gallery */}
            <SceneGallery
              datasetId={datasetFilter !== "all" ? datasetFilter : undefined}
              selectedScenes={selectedScenes}
              onSceneSelect={handleSceneSelect}
              onSceneToggle={handleSceneToggle}
              onBatchSelect={handleBatchSelect}
              data-oid="qkt2qiu"
            />
          </div>
        ) : (
          currentScene && (
            <div
              className="grid grid-cols-1 xl:grid-cols-5 gap-6"
              data-oid="8ug6pmg"
            >
              {/* Scene Detail View */}
              <div className="xl:col-span-3" data-oid="4y5-blm">
                <SceneDetailView
                  sceneId={currentScene.id}
                  onNext={handleNextScene}
                  onPrevious={handlePreviousScene}
                  onClose={handleCloseDetail}
                  selectedObject={selectedObject}
                  onObjectSelect={setSelectedObject}
                  nextSceneId={getNextSceneId()}
                  previousSceneId={getPreviousSceneId()}
                  className="h-[calc(100vh-200px)]"
                  data-oid="9d4zbpt"
                />
              </div>

              {/* AI Analysis Panel */}
              <div className="xl:col-span-1" data-oid="h6jmqzm">
                <AIAnalysisPanel
                  scene={currentScene}
                  selectedObject={selectedObject}
                  onObjectSelect={setSelectedObject}
                  className="max-h-[calc(100vh-200px)] overflow-y-auto"
                  data-oid="osxo:h:"
                />
              </div>

              {/* Annotation Tools Sidebar */}
              <div className="xl:col-span-1 space-y-4" data-oid="t83rjs:">
                <AnnotationTools
                  scene={currentScene}
                  selectedObject={selectedObject}
                  onObjectSelect={setSelectedObject}
                  data-oid="lm.oi45"
                />

                {/* Mini Progress */}
                <div
                  className="bg-card border rounded-lg p-4"
                  data-oid="n.rt98l"
                >
                  <div
                    className="flex items-center justify-between mb-2"
                    data-oid="dypt8rp"
                  >
                    <span className="text-sm font-medium" data-oid="onj4yfk">
                      Progress
                    </span>
                    <Badge
                      variant="outline"
                      className="text-xs"
                      data-oid="yzprj23"
                    >
                      {getCurrentSceneIndex() + 1} / {scenes.length}
                    </Badge>
                  </div>
                  <div
                    className="w-full bg-muted rounded-full h-2"
                    data-oid="hknc8__"
                  >
                    <div
                      className="bg-primary h-2 rounded-full transition-all"
                      style={{
                        width: `${((getCurrentSceneIndex() + 1) / scenes.length) * 100}%`,
                      }}
                      data-oid="w.r.:o1"
                    />
                  </div>
                  <div
                    className="text-xs text-muted-foreground mt-1"
                    data-oid="cs21weu"
                  >
                    {Math.round(
                      ((getCurrentSceneIndex() + 1) / scenes.length) * 100,
                    )}
                    % complete
                  </div>
                </div>

                {/* Navigation Help */}
                <div className="bg-muted/50 rounded-lg p-3" data-oid="qtt.ab7">
                  <h4 className="text-xs font-medium mb-2" data-oid="0455im6">
                    Keyboard Shortcuts
                  </h4>
                  <div
                    className="space-y-1 text-xs text-muted-foreground"
                    data-oid="a6kjieo"
                  >
                    <div data-oid="_fpwku3">← → Arrow keys: Navigate</div>
                    <div data-oid="g.i.3c3">A: Approve scene</div>
                    <div data-oid="hwmx:os">R: Reject scene</div>
                    <div data-oid="mhy3pg9">Esc: Close detail view</div>
                    <div data-oid="adm9eqp">Space: Next scene</div>
                  </div>
                </div>
              </div>
            </div>
          )
        )}
        {error && (
          <p className="text-sm text-muted-foreground" data-oid="qx7:k1_">
            {error?.message || "An error occurred"}
          </p>
        )}
      </div>
    </div>
  );
}
