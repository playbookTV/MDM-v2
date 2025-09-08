import { useState, useCallback, useMemo, memo } from "react";
import {
  Grid,
  List,
  Search,
  Filter,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  Eye,
  ChevronLeft,
  ChevronRight,
  Loader2,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  useScenes,
  useSceneImages,
  REVIEW_STATUSES,
  SCENE_TYPES,
} from "@/hooks/useScenes";
import type { Scene } from "@/types/dataset";

interface SceneGalleryProps {
  datasetId?: string;
  selectedScenes?: Set<string>;
  onSceneSelect?: (scene: Scene) => void;
  onSceneToggle?: (sceneId: string) => void;
  onBatchSelect?: (scenes: Scene[]) => void;
  className?: string;
}

type ViewMode = "grid" | "list";

const REVIEW_STATUS_ICONS = {
  pending: Clock,
  approved: CheckCircle,
  rejected: XCircle,
  corrected: AlertTriangle,
};

const REVIEW_STATUS_COLORS = {
  pending: "text-gray-500",
  approved: "text-green-500",
  rejected: "text-red-500",
  corrected: "text-yellow-500",
};

// Utility function for confidence colors
const getConfidenceColor = (confidence?: number) => {
  if (!confidence) return "text-gray-400";
  if (confidence >= 0.8) return "text-green-500";
  if (confidence >= 0.6) return "text-yellow-500";
  return "text-red-500";
};

export function SceneGallery({
  datasetId,
  selectedScenes = new Set(),
  onSceneSelect,
  onSceneToggle,
  onBatchSelect,
  className,
}: SceneGalleryProps) {
  const [viewMode, setViewMode] = useState<ViewMode>("grid");
  const [searchQuery, setSearchQuery] = useState("");
  const [reviewStatusFilter, setReviewStatusFilter] = useState<string>("all");
  const [sceneTypeFilter, setSceneTypeFilter] = useState<string>("all");
  const [currentPage, setCurrentPage] = useState(1);

  const { data, isLoading, error } = useScenes({
    dataset_id: datasetId,
    review_status:
      reviewStatusFilter !== "all" ? reviewStatusFilter : undefined,
    scene_type: sceneTypeFilter !== "all" ? sceneTypeFilter : undefined,
    page: currentPage,
    limit: 24, // 4x6 grid
  });

  const scenes = data?.items || [];
  const totalPages = data ? Math.ceil(data.total / data.limit) : 0;

  const filteredScenes = useMemo(
    () =>
      scenes.filter((scene) => {
        if (searchQuery) {
          return (
            scene.source.toLowerCase().includes(searchQuery.toLowerCase()) ||
            scene.scene_type
              ?.toLowerCase()
              .includes(searchQuery.toLowerCase()) ||
            scene.dataset_name
              ?.toLowerCase()
              .includes(searchQuery.toLowerCase())
          );
        }
        return true;
      }),
    [scenes, searchQuery],
  );

  const handleSelectAll = useCallback(() => {
    if (selectedScenes.size === filteredScenes.length) {
      // Deselect all
      onBatchSelect?.([]);
    } else {
      // Select all
      onBatchSelect?.(filteredScenes);
    }
  }, [
    selectedScenes.size,
    filteredScenes.length,
    filteredScenes,
    onBatchSelect,
  ]);

  if (error) {
    return (
      <div
        className={`flex items-center justify-center p-12 ${className}`}
        data-oid="p9owxt6"
      >
        <div className="text-center" data-oid="kve26s1">
          <XCircle
            className="h-12 w-12 text-destructive mx-auto mb-4"
            data-oid=":zby5hh"
          />

          <h3 className="text-lg font-semibold mb-2" data-oid="jf1jwzc">
            Failed to load scenes
          </h3>
          {error && (
            <p className="text-sm text-muted-foreground" data-oid="5.efzgh">
              {error?.message || "An error occurred"}
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={className} data-oid="4p_yg:q">
      {/* Header Controls */}
      <div
        className="flex items-center justify-between mb-6"
        data-oid="u277_gz"
      >
        <div className="flex items-center space-x-4" data-oid="k26y4sd">
          {/* Search */}
          <div className="relative w-64" data-oid="w6kahst">
            <Search
              className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"
              data-oid="lzszh7j"
            />

            <Input
              placeholder="Search scenes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
              data-oid="9u52cqh"
            />
          </div>

          {/* Filters */}
          <Select
            value={reviewStatusFilter}
            onValueChange={setReviewStatusFilter}
            data-oid="mktyz6m"
          >
            <SelectTrigger className="w-40" data-oid="64u_mwe">
              <SelectValue placeholder="Status" data-oid="_s8uy44" />
            </SelectTrigger>
            <SelectContent data-oid="5vg8dye">
              <SelectItem value="all" data-oid="3ag7ecg">
                All Status
              </SelectItem>
              {REVIEW_STATUSES.map((status) => (
                <SelectItem
                  key={status.value}
                  value={status.value}
                  data-oid="7923vqy"
                >
                  {status.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={sceneTypeFilter}
            onValueChange={setSceneTypeFilter}
            data-oid="92-8vpl"
          >
            <SelectTrigger className="w-40" data-oid="u5dm4.:">
              <SelectValue placeholder="Scene Type" data-oid="tgboj8g" />
            </SelectTrigger>
            <SelectContent data-oid="8-va3e3">
              <SelectItem value="all" data-oid="8x-uhjs">
                All Types
              </SelectItem>
              {SCENE_TYPES.map((type) => (
                <SelectItem key={type} value={type} data-oid="2xj.euf">
                  {type.replace("_", " ")}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* View Controls */}
        <div className="flex items-center space-x-2" data-oid="c6-dx10">
          {data && (
            <div className="text-sm text-muted-foreground" data-oid="6d_besa">
              {filteredScenes.length} of {data.total} scenes
            </div>
          )}

          {filteredScenes.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleSelectAll}
              data-oid="lu.rnx9"
            >
              {selectedScenes.size === filteredScenes.length
                ? "Deselect All"
                : "Select All"}
            </Button>
          )}

          <div className="flex border rounded-md" data-oid="2d0xh0c">
            <Button
              variant={viewMode === "grid" ? "default" : "ghost"}
              size="sm"
              onClick={() => setViewMode("grid")}
              className="rounded-r-none"
              data-oid="v-.-w:i"
            >
              <Grid className="h-4 w-4" data-oid="-b5syze" />
            </Button>
            <Button
              variant={viewMode === "list" ? "default" : "ghost"}
              size="sm"
              onClick={() => setViewMode("list")}
              className="rounded-l-none"
              data-oid="jzz4y9z"
            >
              <List className="h-4 w-4" data-oid="z-o:vpf" />
            </Button>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div
          className="flex items-center justify-center p-12"
          data-oid="aed9hui"
        >
          <Loader2 className="h-8 w-8 animate-spin" data-oid="91rt:-o" />
        </div>
      )}

      {/* Empty State */}
      {!isLoading && filteredScenes.length === 0 && (
        <div className="text-center p-12" data-oid="mmxyu:x">
          <Eye
            className="mx-auto h-12 w-12 text-muted-foreground mb-4"
            data-oid=".5dvn8t"
          />

          <h3 className="text-lg font-semibold mb-2" data-oid="x2_-x8s">
            No scenes found
          </h3>
          <p className="text-sm text-muted-foreground" data-oid="1t9gzkq">
            {searchQuery ||
            reviewStatusFilter !== "all" ||
            sceneTypeFilter !== "all"
              ? "Try adjusting your search criteria."
              : "No scenes available for review."}
          </p>
        </div>
      )}

      {/* Scene Grid */}
      {!isLoading && filteredScenes.length > 0 && (
        <>
          {viewMode === "grid" ? (
            <SceneGrid
              scenes={filteredScenes}
              selectedScenes={selectedScenes}
              onSceneSelect={onSceneSelect}
              onSceneToggle={onSceneToggle}
              data-oid="c5zn-hv"
            />
          ) : (
            <SceneList
              scenes={filteredScenes}
              selectedScenes={selectedScenes}
              onSceneSelect={onSceneSelect}
              onSceneToggle={onSceneToggle}
              data-oid="9s3jkuu"
            />
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div
              className="flex items-center justify-between mt-8"
              data-oid="o1778bp"
            >
              <div className="text-sm text-muted-foreground" data-oid="l8vjd_k">
                Page {currentPage} of {totalPages}
              </div>

              <div className="flex items-center space-x-2" data-oid="b:1nxne">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage <= 1}
                  data-oid="5gh.e7a"
                >
                  <ChevronLeft className="h-4 w-4" data-oid="gl5ofdb" />
                  Previous
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    setCurrentPage((p) => Math.min(totalPages, p + 1))
                  }
                  disabled={currentPage >= totalPages}
                  data-oid="6fii0va"
                >
                  Next
                  <ChevronRight className="h-4 w-4" data-oid="q.bu8ix" />
                </Button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

// Grid View Component
const SceneGrid = memo(function SceneGrid({
  scenes,
  selectedScenes,
  onSceneSelect,
  onSceneToggle,
}: {
  scenes: Scene[];
  selectedScenes: Set<string>;
  onSceneSelect?: (scene: Scene) => void;
  onSceneToggle?: (sceneId: string) => void;
}) {
  return (
    <div
      className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4"
      data-oid="7_zsxjy"
    >
      {scenes.map((scene) => (
        <SceneCard
          key={scene.id}
          scene={scene}
          isSelected={selectedScenes.has(scene.id)}
          onSceneSelect={onSceneSelect}
          onSceneToggle={onSceneToggle}
          data-oid="csul0z4"
        />
      ))}
    </div>
  );
});

// List View Component
const SceneList = memo(function SceneList({
  scenes,
  selectedScenes,
  onSceneSelect,
  onSceneToggle,
}: {
  scenes: Scene[];
  selectedScenes: Set<string>;
  onSceneSelect?: (scene: Scene) => void;
  onSceneToggle?: (sceneId: string) => void;
}) {
  return (
    <div className="space-y-2" data-oid="w-40ndp">
      {scenes.map((scene) => (
        <SceneListItem
          key={scene.id}
          scene={scene}
          isSelected={selectedScenes.has(scene.id)}
          onSceneSelect={onSceneSelect}
          onSceneToggle={onSceneToggle}
          data-oid="qj56p03"
        />
      ))}
    </div>
  );
});

// Scene Card Component
const SceneCard = memo(function SceneCard({
  scene,
  isSelected,
  onSceneSelect,
  onSceneToggle,
}: {
  scene: Scene;
  isSelected: boolean;
  onSceneSelect?: (scene: Scene) => void;
  onSceneToggle?: (sceneId: string) => void;
}) {
  const { thumbnailUrl } = useSceneImages(scene);
  const StatusIcon =
    REVIEW_STATUS_ICONS[
      scene.review_status as keyof typeof REVIEW_STATUS_ICONS
    ] || Clock;
  const statusColor =
    REVIEW_STATUS_COLORS[
      scene.review_status as keyof typeof REVIEW_STATUS_COLORS
    ] || "text-gray-500";

  const handleSelect = useCallback(() => {
    onSceneSelect?.(scene);
  }, [onSceneSelect, scene]);

  const handleToggle = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      onSceneToggle?.(scene.id);
    },
    [onSceneToggle, scene.id],
  );

  return (
    <div
      className={`relative group rounded-lg border-2 transition-colors cursor-pointer ${
        isSelected
          ? "border-primary"
          : "border-transparent hover:border-muted-foreground"
      }`}
      onClick={handleSelect}
      data-oid="jl5wr0d"
    >
      {/* Selection Checkbox */}
      <div className="absolute top-2 left-2 z-10" data-oid="sc1600-">
        <button
          onClick={handleToggle}
          className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
            isSelected
              ? "bg-primary border-primary text-primary-foreground"
              : "bg-background border-muted-foreground"
          }`}
          data-oid="qnc8_b3"
        >
          {isSelected && <CheckCircle className="h-3 w-3" data-oid="tv9r5.y" />}
        </button>
      </div>

      {/* Status Icon */}
      <div className="absolute top-2 right-2 z-10" data-oid="bn99d_8">
        <StatusIcon className={`h-4 w-4 ${statusColor}`} data-oid="s8.as9b" />
      </div>

      {/* Image */}
      <div
        className="aspect-[4/3] rounded-t-lg overflow-hidden bg-muted"
        data-oid="zyhv_15"
      >
        <img
          src={thumbnailUrl}
          alt={scene.source}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform"
          loading="lazy"
          data-oid="e6edhca"
        />
      </div>

      {/* Info */}
      <div className="p-3 space-y-2" data-oid="v5055q-">
        <div
          className="text-sm font-medium truncate"
          title={scene.source}
          data-oid="e9kg.pd"
        >
          {scene.source}
        </div>

        <div className="flex items-center justify-between" data-oid="tjscmps">
          {scene.scene_type && (
            <Badge variant="outline" className="text-xs" data-oid="z3d_mmq">
              {scene.scene_type.replace("_", " ")}
            </Badge>
          )}

          {scene.scene_conf && (
            <span
              className={`text-xs font-mono ${getConfidenceColor(scene.scene_conf)}`}
              data-oid="horvezr"
            >
              {(scene.scene_conf * 100).toFixed(0)}%
            </span>
          )}
        </div>

        <div className="text-xs text-muted-foreground" data-oid="a-eofu6">
          {scene.objects_count} objects
        </div>
      </div>
    </div>
  );
});

// Scene List Item Component
const SceneListItem = memo(function SceneListItem({
  scene,
  isSelected,
  onSceneSelect,
  onSceneToggle,
}: {
  scene: Scene;
  isSelected: boolean;
  onSceneSelect?: (scene: Scene) => void;
  onSceneToggle?: (sceneId: string) => void;
}) {
  const { thumbnailUrl } = useSceneImages(scene);
  const StatusIcon =
    REVIEW_STATUS_ICONS[
      scene.review_status as keyof typeof REVIEW_STATUS_ICONS
    ] || Clock;
  const statusColor =
    REVIEW_STATUS_COLORS[
      scene.review_status as keyof typeof REVIEW_STATUS_COLORS
    ] || "text-gray-500";

  const handleSelect = useCallback(() => {
    onSceneSelect?.(scene);
  }, [onSceneSelect, scene]);

  const handleToggle = useCallback(
    (e: React.MouseEvent) => {
      e.stopPropagation();
      onSceneToggle?.(scene.id);
    },
    [onSceneToggle, scene.id],
  );

  return (
    <div
      className={`flex items-center space-x-4 p-4 rounded-lg border cursor-pointer transition-colors ${
        isSelected
          ? "border-primary bg-primary/5"
          : "border-border hover:bg-muted/50"
      }`}
      onClick={handleSelect}
      data-oid="mf.q-3_"
    >
      {/* Selection */}
      <button
        onClick={handleToggle}
        className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
          isSelected
            ? "bg-primary border-primary text-primary-foreground"
            : "bg-background border-muted-foreground"
        }`}
        data-oid="ivigmtu"
      >
        {isSelected && <CheckCircle className="h-3 w-3" data-oid="s:-lqgr" />}
      </button>

      {/* Thumbnail */}
      <div
        className="w-16 h-12 rounded overflow-hidden bg-muted flex-shrink-0"
        data-oid="85g2od7"
      >
        <img
          src={thumbnailUrl}
          alt={scene.source}
          className="w-full h-full object-cover"
          loading="lazy"
          data-oid="yd6_nkf"
        />
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0" data-oid="uychv7p">
        <div className="font-medium truncate" data-oid=":fmnp44">
          {scene.source}
        </div>
        <div className="text-sm text-muted-foreground" data-oid="5a.hs_9">
          {scene.dataset_name} • {scene.objects_count} objects • {scene.width}×
          {scene.height}
        </div>
      </div>

      {/* Status & Confidence */}
      <div className="flex items-center space-x-4" data-oid="0q_gy7m">
        {scene.scene_type && (
          <Badge variant="outline" data-oid="61utmac">
            {scene.scene_type.replace("_", " ")}
          </Badge>
        )}

        {scene.scene_conf && (
          <span
            className={`text-sm font-mono ${getConfidenceColor(scene.scene_conf)}`}
            data-oid="a:s7.4h"
          >
            {(scene.scene_conf * 100).toFixed(0)}%
          </span>
        )}

        <StatusIcon className={`h-4 w-4 ${statusColor}`} data-oid="0mp8y-k" />
      </div>
    </div>
  );
});
