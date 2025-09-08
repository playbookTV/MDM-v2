import { useState, useMemo, useCallback } from "react";
import {
  Database,
  Search,
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Eye,
  Play,
  CheckCircle,
  XCircle,
  Clock,
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useDatasetStats } from "@/hooks/useStats";
import type { StatsQuery } from "@/types/stats";

interface DatasetStatsTableProps {
  query?: StatsQuery;
  onViewDataset?: (datasetId: string) => void;
  onProcessDataset?: (datasetId: string) => void;
  className?: string;
}

type SortField =
  | "name"
  | "scenes"
  | "progress"
  | "objects"
  | "confidence"
  | "last_processed";
type SortDirection = "asc" | "desc";

export function DatasetStatsTable({
  query,
  onViewDataset,
  onProcessDataset,
  className,
}: DatasetStatsTableProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [sortField, setSortField] = useState<SortField>("last_processed");
  const [sortDirection, setSortDirection] = useState<SortDirection>("desc");

  const { data: datasetStats, isLoading, error } = useDatasetStats(query);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("desc");
    }
  };

  const getSortedAndFilteredData = useMemo(() => {
    if (!datasetStats) return [];

    // Filter by search query
    let filtered = datasetStats.filter((dataset) =>
      dataset.dataset_name.toLowerCase().includes(searchQuery.toLowerCase()),
    );

    // Sort data
    filtered.sort((a, b) => {
      let aVal: any, bVal: any;

      switch (sortField) {
        case "name":
          aVal = a.dataset_name.toLowerCase();
          bVal = b.dataset_name.toLowerCase();
          break;
        case "scenes":
          aVal = a.total_scenes;
          bVal = b.total_scenes;
          break;
        case "progress":
          aVal = a.processing_progress || a.completion_rate || 0;
          bVal = b.processing_progress || b.completion_rate || 0;
          break;
        case "objects":
          aVal = a.objects_detected || a.total_objects || 0;
          bVal = b.objects_detected || b.total_objects || 0;
          break;
        case "confidence":
          aVal = a.average_confidence || 0.85;
          bVal = b.average_confidence || 0.85;
          break;
        case "last_processed":
          aVal = a.last_processed ? new Date(a.last_processed).getTime() : 0;
          bVal = b.last_processed ? new Date(b.last_processed).getTime() : 0;
          break;
        default:
          return 0;
      }

      if (sortDirection === "asc") {
        return aVal > bVal ? 1 : -1;
      } else {
        return aVal < bVal ? 1 : -1;
      }
    });

    return filtered;
  }, [datasetStats, searchQuery, sortField, sortDirection]);

  const formatLastProcessed = useCallback((dateString: string | undefined) => {
    if (!dateString) return "Never";
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) {
      return `${diffDays}d ago`;
    } else if (diffHours > 0) {
      return `${diffHours}h ago`;
    } else {
      return "Recently";
    }
  }, []);

  const getProcessingStatus = useCallback((dataset: any) => {
    const failedScenes = dataset.failed_scenes || 0;
    const processingProgress =
      dataset.processing_progress || dataset.completion_rate || 0;

    if (failedScenes > 0 && processingProgress < 100) {
      return { status: "partial", icon: XCircle, color: "text-yellow-500" };
    } else if (processingProgress === 100) {
      return { status: "complete", icon: CheckCircle, color: "text-green-500" };
    } else if (processingProgress > 0) {
      return { status: "processing", icon: Clock, color: "text-blue-500" };
    } else {
      return { status: "pending", icon: Clock, color: "text-gray-500" };
    }
  }, []);

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return <ArrowUpDown className="h-4 w-4 opacity-50" data-oid="ihm3v3c" />;
    }
    return sortDirection === "asc" ? (
      <ArrowUp className="h-4 w-4" data-oid="gr8cpd0" />
    ) : (
      <ArrowDown className="h-4 w-4" data-oid="ur:qxmm" />
    );
  };

  const filteredData = getSortedAndFilteredData;

  if (error) {
    return (
      <div
        className={`bg-card border rounded-lg p-6 ${className}`}
        data-oid="eorpe_4"
      >
        <div className="flex items-center space-x-2 mb-4" data-oid="0mo0ged">
          <Database className="h-5 w-5 text-destructive" data-oid="rgegb8l" />
          <h3 className="text-lg font-semibold" data-oid="t_h_xz9">
            Dataset Statistics
          </h3>
          <Badge variant="destructive" data-oid="uudhwy4">
            Error
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground" data-oid="s9_v1s2">
          Unable to load dataset statistics
        </p>
      </div>
    );
  }

  return (
    <div
      className={`bg-card border rounded-lg p-6 ${className}`}
      data-oid="5x8:ou:"
    >
      {/* Header */}
      <div
        className="flex items-center justify-between mb-6"
        data-oid=".fhm_mp"
      >
        <div className="flex items-center space-x-2" data-oid="psqpc07">
          <Database className="h-5 w-5" data-oid="pfbu-4v" />
          <h3 className="text-lg font-semibold" data-oid="ci1i5x0">
            Dataset Statistics
          </h3>
          {datasetStats && (
            <Badge variant="outline" data-oid="x:vc0im">
              {filteredData.length} of {datasetStats.length}
            </Badge>
          )}
        </div>

        {/* Search */}
        <div className="relative w-64" data-oid="b_owfu-">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"
            data-oid="depppnf"
          />
          <Input
            placeholder="Search datasets..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
            data-oid="6y1p3qf"
          />
        </div>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="space-y-3" data-oid="sze2:2h">
          {Array.from({ length: 5 }, (_, i) => (
            <div
              key={i}
              className="h-16 bg-muted animate-pulse rounded"
              data-oid="g1wuqwj"
            />
          ))}
        </div>
      ) : filteredData.length === 0 ? (
        <div className="text-center py-12" data-oid="4neiska">
          <Database
            className="mx-auto h-12 w-12 text-muted-foreground mb-4"
            data-oid="kz1i55r"
          />
          <h3 className="text-lg font-semibold mb-2" data-oid="f9k8_bd">
            No datasets found
          </h3>
          <p className="text-sm text-muted-foreground" data-oid="yc:gpj-">
            {searchQuery
              ? "No datasets match your search criteria."
              : "No datasets available."}
          </p>
        </div>
      ) : (
        <div className="rounded-md border" data-oid="hf5b_.8">
          <Table data-oid="8ix0cub">
            <TableHeader data-oid="_3lxnv:">
              <TableRow data-oid="-7xttbc">
                <TableHead data-oid="vb7752s">
                  <Button
                    variant="ghost"
                    className="h-auto p-0 font-medium"
                    onClick={() => handleSort("name")}
                    data-oid="ay9.9ik"
                  >
                    Dataset <SortIcon field="name" data-oid="ziuw98o" />
                  </Button>
                </TableHead>
                <TableHead data-oid="d7jhnj5">
                  <Button
                    variant="ghost"
                    className="h-auto p-0 font-medium"
                    onClick={() => handleSort("scenes")}
                    data-oid="adi:e7t"
                  >
                    Scenes <SortIcon field="scenes" data-oid="-.5wu.m" />
                  </Button>
                </TableHead>
                <TableHead data-oid="9m8zs1p">
                  <Button
                    variant="ghost"
                    className="h-auto p-0 font-medium"
                    onClick={() => handleSort("progress")}
                    data-oid="ga_x8hm"
                  >
                    Progress <SortIcon field="progress" data-oid="9w0z_0a" />
                  </Button>
                </TableHead>
                <TableHead data-oid="aq7e_wx">
                  <Button
                    variant="ghost"
                    className="h-auto p-0 font-medium"
                    onClick={() => handleSort("objects")}
                    data-oid="-t.7dqm"
                  >
                    Objects <SortIcon field="objects" data-oid="pog21-." />
                  </Button>
                </TableHead>
                <TableHead data-oid="l4qi7z:">
                  <Button
                    variant="ghost"
                    className="h-auto p-0 font-medium"
                    onClick={() => handleSort("confidence")}
                    data-oid="efxbp0m"
                  >
                    Confidence{" "}
                    <SortIcon field="confidence" data-oid="jxe7g61" />
                  </Button>
                </TableHead>
                <TableHead data-oid="-qws8iv">
                  <Button
                    variant="ghost"
                    className="h-auto p-0 font-medium"
                    onClick={() => handleSort("last_processed")}
                    data-oid="d95hi.8"
                  >
                    Last Processed{" "}
                    <SortIcon field="last_processed" data-oid="upq1lps" />
                  </Button>
                </TableHead>
                <TableHead className="w-32" data-oid="e.6xg7g">
                  Actions
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody data-oid=".q5v692">
              {filteredData.map((dataset) => {
                const status = getProcessingStatus(dataset);
                const StatusIcon = status.icon;

                return (
                  <TableRow key={dataset.dataset_id} data-oid="58wc.j9">
                    <TableCell data-oid="_rmhfv3">
                      <div data-oid="eaiyop0">
                        <div className="font-medium" data-oid="7c3.t84">
                          {dataset.dataset_name}
                        </div>
                        <div
                          className="text-xs text-muted-foreground"
                          data-oid="rjz33.m"
                        >
                          {dataset.unique_object_types || 0} object types
                        </div>
                        {/* Scene Types */}
                        <div
                          className="flex flex-wrap gap-1 mt-1"
                          data-oid="9qtyzwe"
                        >
                          {(dataset.scene_types || [])
                            .slice(0, 3)
                            .map((sceneType) => (
                              <Badge
                                key={sceneType.scene_type}
                                variant="outline"
                                className="text-xs"
                                data-oid="cy2tr1j"
                              >
                                {sceneType.scene_type} ({sceneType.count})
                              </Badge>
                            ))}
                          {(dataset.scene_types || []).length > 3 && (
                            <Badge
                              variant="outline"
                              className="text-xs"
                              data-oid="8bylo5z"
                            >
                              +{(dataset.scene_types || []).length - 3} more
                            </Badge>
                          )}
                        </div>
                      </div>
                    </TableCell>

                    <TableCell data-oid="0-bke.4">
                      <div className="text-center" data-oid="9phgg-f">
                        <div
                          className="text-lg font-semibold"
                          data-oid="x_2legt"
                        >
                          {dataset.total_scenes.toLocaleString()}
                        </div>
                        <div
                          className="text-xs text-muted-foreground"
                          data-oid="grumlee"
                        >
                          {dataset.processed_scenes} processed
                        </div>
                        {(dataset.failed_scenes || 0) > 0 && (
                          <div
                            className="text-xs text-red-500"
                            data-oid="wqz.w0i"
                          >
                            {dataset.failed_scenes || 0} failed
                          </div>
                        )}
                      </div>
                    </TableCell>

                    <TableCell data-oid="mzty5np">
                      <div className="space-y-2" data-oid=".ewplp7">
                        <div
                          className="flex items-center justify-between"
                          data-oid="49uio0d"
                        >
                          <StatusIcon
                            className={`h-4 w-4 ${status.color}`}
                            data-oid="4sc9qwe"
                          />
                          <span className="text-sm" data-oid="gd2-v4j">
                            {(
                              dataset.processing_progress ||
                              dataset.completion_rate ||
                              0
                            ).toFixed(1)}
                            %
                          </span>
                        </div>
                        <Progress
                          value={
                            dataset.processing_progress ||
                            dataset.completion_rate ||
                            0
                          }
                          className="h-2"
                          data-oid="y32vloe"
                        />
                      </div>
                    </TableCell>

                    <TableCell data-oid="59t0zr1">
                      <div className="text-center" data-oid="lyow.cr">
                        <div
                          className="text-lg font-semibold"
                          data-oid="jhmj3g:"
                        >
                          {(
                            dataset.objects_detected ||
                            dataset.total_objects ||
                            0
                          ).toLocaleString()}
                        </div>
                        <div
                          className="text-xs text-muted-foreground"
                          data-oid="m:w2ix."
                        >
                          {dataset.unique_object_types || 0} types
                        </div>
                      </div>
                    </TableCell>

                    <TableCell data-oid="s._wjxz">
                      <div className="text-center" data-oid="dy-ey2-">
                        <div
                          className="text-lg font-semibold"
                          data-oid="g3l47ke"
                        >
                          {((dataset.average_confidence || 0.85) * 100).toFixed(
                            1,
                          )}
                          %
                        </div>
                        <div
                          className="text-xs text-muted-foreground"
                          data-oid="rjbme5j"
                        >
                          avg confidence
                        </div>
                      </div>
                    </TableCell>

                    <TableCell data-oid="2i4n6ps">
                      <div className="text-sm" data-oid="tsiwh:o">
                        {formatLastProcessed(dataset.last_processed)}
                      </div>
                    </TableCell>

                    <TableCell data-oid="pd8:acx">
                      <div
                        className="flex items-center space-x-1"
                        data-oid="n6bb26_"
                      >
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => onViewDataset?.(dataset.dataset_id)}
                          data-oid="pw7:9of"
                        >
                          <Eye className="h-3 w-3" data-oid="kmr.u:h" />
                        </Button>
                        {(dataset.processing_progress ||
                          dataset.completion_rate ||
                          0) < 100 && (
                          <Button
                            variant="default"
                            size="sm"
                            onClick={() =>
                              onProcessDataset?.(dataset.dataset_id)
                            }
                            data-oid="jj6732e"
                          >
                            <Play className="h-3 w-3" data-oid="h_gx5zy" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
