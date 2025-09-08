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
        data-oid="bukx02l"
      >
        <div className="text-center" data-oid="a.g.f7f">
          <XCircle
            className="h-12 w-12 text-destructive mx-auto mb-4"
            data-oid="rh1t8xx"
          />
          <h3 className="text-lg font-semibold mb-2" data-oid=".xx:eof">
            Failed to load scenes
          </h3>
          {error && (
            <p className="text-sm text-muted-foreground" data-oid="inskdh-">
              {error?.message || "An error occurred"}
            </p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={className} data-oid="m3irnb2">
      {/* Header Controls */}
      <div
        className="flex items-center justify-between mb-6"
        data-oid="rqyxat4"
      >
        <div className="flex items-center space-x-4" data-oid="2efkel4">
          {/* Search */}
          <div className="relative w-64" data-oid="iq9fmyp">
            <Search
              className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"
              data-oid="yghxn5i"
            />
            <Input
              placeholder="Search scenes..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
              data-oid="evfxbsx"
            />
          </div>

          {/* Filters */}
          <Select
            value={reviewStatusFilter}
            onValueChange={setReviewStatusFilter}
            data-oid="k-04pjj"
          >
            <SelectTrigger className="w-40" data-oid="8ywqp38">
              <SelectValue placeholder="Status" data-oid="rpkd6xo" />
            </SelectTrigger>
            <SelectContent data-oid=":elkjvl">
              <SelectItem value="all" data-oid="l4cwna8">
                All Status
              </SelectItem>
              {REVIEW_STATUSES.map((status) => (
                <SelectItem
                  key={status.value}
                  value={status.value}
                  data-oid="d_apvx9"
                >
                  {status.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Select
            value={sceneTypeFilter}
            onValueChange={setSceneTypeFilter}
            data-oid="z5878va"
          >
            <SelectTrigger className="w-40" data-oid="pd776h7">
              <SelectValue placeholder="Scene Type" data-oid="t:w.271" />
            </SelectTrigger>
            <SelectContent data-oid="wf67on5">
              <SelectItem value="all" data-oid="m_4sbkr">
                All Types
              </SelectItem>
              {SCENE_TYPES.map((type) => (
                <SelectItem key={type} value={type} data-oid="4qgninf">
                  {type.replace("_", " ")}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* View Controls */}
        <div className="flex items-center space-x-2" data-oid="b_q2ngw">
          {data && (
            <div className="text-sm text-muted-foreground" data-oid="mpo4tf.">
              {filteredScenes.length} of {data.total} scenes
            </div>
          )}

          {filteredScenes.length > 0 && (
            <Button
              variant="outline"
              size="sm"
              onClick={handleSelectAll}
              data-oid="sabojzs"
            >
              {selectedScenes.size === filteredScenes.length
                ? "Deselect All"
                : "Select All"}
            </Button>
          )}

          <div className="flex border rounded-md" data-oid="r8dqwv-">
            <Button
              variant={viewMode === "grid" ? "default" : "ghost"}
              size="sm"
              onClick={() => setViewMode("grid")}
              className="rounded-r-none"
              data-oid="bj170m8"
            >
              <Grid className="h-4 w-4" data-oid="3s-nxqo" />
            </Button>
            <Button
              variant={viewMode === "list" ? "default" : "ghost"}
              size="sm"
              onClick={() => setViewMode("list")}
              className="rounded-l-none"
              data-oid="s3tgj2e"
            >
              <List className="h-4 w-4" data-oid="dkrkyt_" />
            </Button>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div
          className="flex items-center justify-center p-12"
          data-oid="z0knjfx"
        >
          <Loader2 className="h-8 w-8 animate-spin" data-oid="aogywws" />
        </div>
      )}

      {/* Empty State */}
      {!isLoading && filteredScenes.length === 0 && (
        <div className="text-center p-12" data-oid="b8__454">
          <Eye
            className="mx-auto h-12 w-12 text-muted-foreground mb-4"
            data-oid="qx:b8jf"
          />
          <h3 className="text-lg font-semibold mb-2" data-oid="w013u-m">
            No scenes found
          </h3>
          <p className="text-sm text-muted-foreground" data-oid="7gaix1d">
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
              data-oid="z0sf7o1"
            />
          ) : (
            <SceneList
              scenes={filteredScenes}
              selectedScenes={selectedScenes}
              onSceneSelect={onSceneSelect}
              onSceneToggle={onSceneToggle}
              data-oid="64-2da7"
            />
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div
              className="flex items-center justify-between mt-8"
              data-oid="n6.7qex"
            >
              <div className="text-sm text-muted-foreground" data-oid="kfvm:7:">
                Page {currentPage} of {totalPages}
              </div>

              <div className="flex items-center space-x-2" data-oid="xz_pwf3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  disabled={currentPage <= 1}
                  data-oid="1tffmt-"
                >
                  <ChevronLeft className="h-4 w-4" data-oid="wa38ix." />
                  Previous
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    setCurrentPage((p) => Math.min(totalPages, p + 1))
                  }
                  disabled={currentPage >= totalPages}
                  data-oid="if6xl2_"
                >
                  Next
                  <ChevronRight className="h-4 w-4" data-oid="uvksx.0" />
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
      data-oid="4m8v:a3"
    >
      {scenes.map((scene) => (
        <SceneCard
          key={scene.id}
          scene={scene}
          isSelected={selectedScenes.has(scene.id)}
          onSceneSelect={onSceneSelect}
          onSceneToggle={onSceneToggle}
          data-oid="ivjkr65"
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
    <div className="space-y-2" data-oid="9m:sj5a">
      {scenes.map((scene) => (
        <SceneListItem
          key={scene.id}
          scene={scene}
          isSelected={selectedScenes.has(scene.id)}
          onSceneSelect={onSceneSelect}
          onSceneToggle={onSceneToggle}
          data-oid="2etwboi"
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
      data-oid="88x4dy6"
    >
      {/* Selection Checkbox */}
      <div className="absolute top-2 left-2 z-10" data-oid="6d.ufxa">
        <button
          onClick={handleToggle}
          className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
            isSelected
              ? "bg-primary border-primary text-primary-foreground"
              : "bg-background border-muted-foreground"
          }`}
          data-oid="i5_6a5n"
        >
          {isSelected && <CheckCircle className="h-3 w-3" data-oid="2ajz:rf" />}
        </button>
      </div>

      {/* Status Icon */}
      <div className="absolute top-2 right-2 z-10" data-oid="lpxauti">
        <StatusIcon className={`h-4 w-4 ${statusColor}`} data-oid="fzk.-8r" />
      </div>

      {/* Image */}
      <div
        className="aspect-[4/3] rounded-t-lg overflow-hidden bg-muted"
        data-oid="l93qx1."
      >
        <img
          src={thumbnailUrl}
          alt={scene.source}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform"
          loading="lazy"
          data-oid="lvp2560"
        />
      </div>

      {/* Info */}
      <div className="p-3 space-y-2" data-oid="xm8v1b4">
        <div
          className="text-sm font-medium truncate"
          title={scene.source}
          data-oid="1136io."
        >
          {scene.source}
        </div>

        <div className="flex items-center justify-between" data-oid="j-:gp2.">
          {scene.scene_type && (
            <Badge variant="outline" className="text-xs" data-oid="d565tw-">
              {scene.scene_type.replace("_", " ")}
            </Badge>
          )}

          {scene.scene_conf && (
            <span
              className={`text-xs font-mono ${getConfidenceColor(scene.scene_conf)}`}
              data-oid="qm.-taz"
            >
              {(scene.scene_conf * 100).toFixed(0)}%
            </span>
          )}
        </div>

        <div className="text-xs text-muted-foreground" data-oid="-8v5l2w">
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
      data-oid="jvcstfw"
    >
      {/* Selection */}
      <button
        onClick={handleToggle}
        className={`w-5 h-5 rounded border-2 flex items-center justify-center ${
          isSelected
            ? "bg-primary border-primary text-primary-foreground"
            : "bg-background border-muted-foreground"
        }`}
        data-oid="r6n0z75"
      >
        {isSelected && <CheckCircle className="h-3 w-3" data-oid="wft-3vq" />}
      </button>

      {/* Thumbnail */}
      <div
        className="w-16 h-12 rounded overflow-hidden bg-muted flex-shrink-0"
        data-oid="4vqu:f:"
      >
        <img
          src={thumbnailUrl}
          alt={scene.source}
          className="w-full h-full object-cover"
          loading="lazy"
          data-oid="st_.7.y"
        />
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0" data-oid=":3wuvrx">
        <div className="font-medium truncate" data-oid="0nrlwhp">
          {scene.source}
        </div>
        <div className="text-sm text-muted-foreground" data-oid="f67-62e">
          {scene.dataset_name} • {scene.objects_count} objects • {scene.width}×
          {scene.height}
        </div>
      </div>

      {/* Status & Confidence */}
      <div className="flex items-center space-x-4" data-oid="h2_b04g">
        {scene.scene_type && (
          <Badge variant="outline" data-oid="g0c7zf0">
            {scene.scene_type.replace("_", " ")}
          </Badge>
        )}

        {scene.scene_conf && (
          <span
            className={`text-sm font-mono ${getConfidenceColor(scene.scene_conf)}`}
            data-oid="gj8ya4u"
          >
            {(scene.scene_conf * 100).toFixed(0)}%
          </span>
        )}

        <StatusIcon className={`h-4 w-4 ${statusColor}`} data-oid="z_u.7si" />
      </div>
    </div>
  );
});
