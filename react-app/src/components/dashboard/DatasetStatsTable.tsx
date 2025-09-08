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
      return <ArrowUpDown className="h-4 w-4 opacity-50" data-oid="z7toggi" />;
    }
    return sortDirection === "asc" ? (
      <ArrowUp className="h-4 w-4" data-oid="tvl:1j0" />
    ) : (
      <ArrowDown className="h-4 w-4" data-oid=":xm62p0" />
    );
  };

  const filteredData = getSortedAndFilteredData;

  if (error) {
    return (
      <div
        className={`bg-card border rounded-lg p-6 ${className}`}
        data-oid="2isp5rv"
      >
        <div className="flex items-center space-x-2 mb-4" data-oid="uudf.c7">
          <Database className="h-5 w-5 text-destructive" data-oid="fxnwgn2" />
          <h3 className="text-lg font-semibold" data-oid="5_bx4ua">
            Dataset Statistics
          </h3>
          <Badge variant="destructive" data-oid="mtwhztp">
            Error
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground" data-oid="y.wx4wx">
          Unable to load dataset statistics
        </p>
      </div>
    );
  }

  return (
    <div
      className={`bg-card border rounded-lg p-6 ${className}`}
      data-oid="e:fk5jk"
    >
      {/* Header */}
      <div
        className="flex items-center justify-between mb-6"
        data-oid="b_7f-3r"
      >
        <div className="flex items-center space-x-2" data-oid="wskpkpn">
          <Database className="h-5 w-5" data-oid="zp6.b:8" />
          <h3 className="text-lg font-semibold" data-oid="_ssk9ss">
            Dataset Statistics
          </h3>
          {datasetStats && (
            <Badge variant="outline" data-oid="y:b7k18">
              {filteredData.length} of {datasetStats.length}
            </Badge>
          )}
        </div>

        {/* Search */}
        <div className="relative w-64" data-oid="h5abh3i">
          <Search
            className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"
            data-oid="k5zhs9g"
          />

          <Input
            placeholder="Search datasets..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
            data-oid="o4:uj79"
          />
        </div>
      </div>

      {/* Table */}
      {isLoading ? (
        <div className="space-y-3" data-oid="xrvotu8">
          {Array.from({ length: 5 }, (_, i) => (
            <div
              key={i}
              className="h-16 bg-muted animate-pulse rounded"
              data-oid="7khfp48"
            />
          ))}
        </div>
      ) : filteredData.length === 0 ? (
        <div className="text-center py-12" data-oid="15wxp_s">
          <Database
            className="mx-auto h-12 w-12 text-muted-foreground mb-4"
            data-oid="j7kj6p3"
          />

          <h3 className="text-lg font-semibold mb-2" data-oid="w54nyty">
            No datasets found
          </h3>
          <p className="text-sm text-muted-foreground" data-oid="4g5il3r">
            {searchQuery
              ? "No datasets match your search criteria."
              : "No datasets available."}
          </p>
        </div>
      ) : (
        <div className="rounded-md border" data-oid="w1:9_g3">
          <Table data-oid="oqjbjc7">
            <TableHeader data-oid="bl7vqws">
              <TableRow data-oid="fa.6nra">
                <TableHead data-oid="_v9ymba">
                  <Button
                    variant="ghost"
                    className="h-auto p-0 font-medium"
                    onClick={() => handleSort("name")}
                    data-oid="av5-:1p"
                  >
                    Dataset <SortIcon field="name" data-oid="iw2vhiq" />
                  </Button>
                </TableHead>
                <TableHead data-oid="eknk7w3">
                  <Button
                    variant="ghost"
                    className="h-auto p-0 font-medium"
                    onClick={() => handleSort("scenes")}
                    data-oid="vxrrivh"
                  >
                    Scenes <SortIcon field="scenes" data-oid="hx.ym9-" />
                  </Button>
                </TableHead>
                <TableHead data-oid="kaz7jiy">
                  <Button
                    variant="ghost"
                    className="h-auto p-0 font-medium"
                    onClick={() => handleSort("progress")}
                    data-oid="t6.e4mh"
                  >
                    Progress <SortIcon field="progress" data-oid="1:b9ctk" />
                  </Button>
                </TableHead>
                <TableHead data-oid="q3wco5f">
                  <Button
                    variant="ghost"
                    className="h-auto p-0 font-medium"
                    onClick={() => handleSort("objects")}
                    data-oid=".a36z8x"
                  >
                    Objects <SortIcon field="objects" data-oid="ql8zu1t" />
                  </Button>
                </TableHead>
                <TableHead data-oid="qtwtelw">
                  <Button
                    variant="ghost"
                    className="h-auto p-0 font-medium"
                    onClick={() => handleSort("confidence")}
                    data-oid="qovz6ct"
                  >
                    Confidence{" "}
                    <SortIcon field="confidence" data-oid="r8hkeyd" />
                  </Button>
                </TableHead>
                <TableHead data-oid="0bxh.0a">
                  <Button
                    variant="ghost"
                    className="h-auto p-0 font-medium"
                    onClick={() => handleSort("last_processed")}
                    data-oid="32d246f"
                  >
                    Last Processed{" "}
                    <SortIcon field="last_processed" data-oid="6uikszp" />
                  </Button>
                </TableHead>
                <TableHead className="w-32" data-oid="ookgu1v">
                  Actions
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody data-oid=".b1xtbr">
              {filteredData.map((dataset) => {
                const status = getProcessingStatus(dataset);
                const StatusIcon = status.icon;

                return (
                  <TableRow key={dataset.dataset_id} data-oid="ipspmxa">
                    <TableCell data-oid="ybgqr.x">
                      <div data-oid="87jt7-a">
                        <div className="font-medium" data-oid="v8yhp5f">
                          {dataset.dataset_name}
                        </div>
                        <div
                          className="text-xs text-muted-foreground"
                          data-oid="9jh5_7l"
                        >
                          {dataset.unique_object_types || 0} object types
                        </div>
                        {/* Scene Types */}
                        <div
                          className="flex flex-wrap gap-1 mt-1"
                          data-oid="tv5nz3-"
                        >
                          {(dataset.scene_types || [])
                            .slice(0, 3)
                            .map((sceneType) => (
                              <Badge
                                key={sceneType.scene_type}
                                variant="outline"
                                className="text-xs"
                                data-oid="vfy.x9-"
                              >
                                {sceneType.scene_type} ({sceneType.count})
                              </Badge>
                            ))}
                          {(dataset.scene_types || []).length > 3 && (
                            <Badge
                              variant="outline"
                              className="text-xs"
                              data-oid="sta-1xo"
                            >
                              +{(dataset.scene_types || []).length - 3} more
                            </Badge>
                          )}
                        </div>
                      </div>
                    </TableCell>

                    <TableCell data-oid="udph4_g">
                      <div className="text-center" data-oid="gd45f3e">
                        <div
                          className="text-lg font-semibold"
                          data-oid="0-s5e6z"
                        >
                          {dataset.total_scenes.toLocaleString()}
                        </div>
                        <div
                          className="text-xs text-muted-foreground"
                          data-oid="7thn1-d"
                        >
                          {dataset.processed_scenes} processed
                        </div>
                        {(dataset.failed_scenes || 0) > 0 && (
                          <div
                            className="text-xs text-red-500"
                            data-oid="cetyceg"
                          >
                            {dataset.failed_scenes || 0} failed
                          </div>
                        )}
                      </div>
                    </TableCell>

                    <TableCell data-oid="mo6aokz">
                      <div className="space-y-2" data-oid="lngqvcm">
                        <div
                          className="flex items-center justify-between"
                          data-oid="cydqo_x"
                        >
                          <StatusIcon
                            className={`h-4 w-4 ${status.color}`}
                            data-oid="0as4fm8"
                          />

                          <span className="text-sm" data-oid="ca3i2mq">
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
                          data-oid="fsy_iw7"
                        />
                      </div>
                    </TableCell>

                    <TableCell data-oid="ce:ra7.">
                      <div className="text-center" data-oid="ccf9ma6">
                        <div
                          className="text-lg font-semibold"
                          data-oid="2ja429w"
                        >
                          {(
                            dataset.objects_detected ||
                            dataset.total_objects ||
                            0
                          ).toLocaleString()}
                        </div>
                        <div
                          className="text-xs text-muted-foreground"
                          data-oid="qnf:_ko"
                        >
                          {dataset.unique_object_types || 0} types
                        </div>
                      </div>
                    </TableCell>

                    <TableCell data-oid="q2d:9cn">
                      <div className="text-center" data-oid="s2d92xz">
                        <div
                          className="text-lg font-semibold"
                          data-oid="av4-e0x"
                        >
                          {((dataset.average_confidence || 0.85) * 100).toFixed(
                            1,
                          )}
                          %
                        </div>
                        <div
                          className="text-xs text-muted-foreground"
                          data-oid="dn2_y70"
                        >
                          avg confidence
                        </div>
                      </div>
                    </TableCell>

                    <TableCell data-oid=":ypx64q">
                      <div className="text-sm" data-oid=":vq1chb">
                        {formatLastProcessed(dataset.last_processed)}
                      </div>
                    </TableCell>

                    <TableCell data-oid="vqz96_4">
                      <div
                        className="flex items-center space-x-1"
                        data-oid="nukt.mq"
                      >
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => onViewDataset?.(dataset.dataset_id)}
                          data-oid="nz0r8lv"
                        >
                          <Eye className="h-3 w-3" data-oid="1vjv6bm" />
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
                            data-oid="14x7l-o"
                          >
                            <Play className="h-3 w-3" data-oid="smw3o3g" />
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
