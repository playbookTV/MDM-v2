import { formatDistanceToNow } from "date-fns";
import { ExternalLink, Calendar, Package } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { Dataset } from "@/types/dataset";

interface DatasetTableProps {
  datasets: Dataset[];
  loading?: boolean;
  highlightId?: string | null;
  onSelectDataset?: (dataset: Dataset) => void;
  onViewScenes?: (dataset: Dataset) => void;
  onProcessDataset?: (dataset: Dataset) => void;
}

export function DatasetTable({
  datasets,
  loading = false,
  highlightId,
  onSelectDataset,
  onViewScenes,
  onProcessDataset,
}: DatasetTableProps) {
  if (loading) {
    return (
      <div className="space-y-3" data-oid="7y1sc.1">
        {Array.from({ length: 3 }, (_, i) => (
          <div
            key={i}
            className="h-16 bg-muted animate-pulse rounded-md"
            data-oid="6k_1fql"
          />
        ))}
      </div>
    );
  }

  if (datasets.length === 0) {
    return (
      <div className="text-center py-12" data-oid="f:yg_ro">
        <Package
          className="mx-auto h-12 w-12 text-muted-foreground"
          data-oid="7wxwvti"
        />

        <h3
          className="mt-2 text-sm font-semibold text-gray-900"
          data-oid="32274hy"
        >
          No datasets
        </h3>
        <p className="mt-1 text-sm text-gray-500" data-oid="9li6bc_">
          Get started by uploading your first dataset.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-md border" data-oid="6rh4oll">
      <Table data-oid="crfrifi">
        <TableHeader data-oid="9d:o8-w">
          <TableRow data-oid="-53jrzh">
            <TableHead data-oid="d3uyoai">Name</TableHead>
            <TableHead data-oid="euh.iu1">Version</TableHead>
            <TableHead data-oid="0afq6fc">Source</TableHead>
            <TableHead data-oid="r-1d19g">License</TableHead>
            <TableHead data-oid="c99c_k2">Created</TableHead>
            <TableHead className="w-32" data-oid="ryu1pp9">
              Actions
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody data-oid="18jelu7">
          {datasets.map((dataset) => {
            const isHighlighted = highlightId === dataset.id;
            return (
              <TableRow
                key={dataset.id}
                className={`cursor-pointer transition-colors ${
                  isHighlighted
                    ? "bg-blue-50 border-blue-200 shadow-sm"
                    : "hover:bg-muted/50"
                }`}
                onClick={() => onSelectDataset?.(dataset)}
                data-oid="vw3ye39"
              >
                <TableCell className="font-medium" data-oid="-bxolvk">
                  <div
                    className="flex items-center space-x-2"
                    data-oid="35.0c3_"
                  >
                    <span data-oid="yw2-g2g">{dataset.name}</span>
                    {dataset.source_url && (
                      <ExternalLink
                        className="h-3 w-3 text-muted-foreground"
                        data-oid="m6wp_f9"
                      />
                    )}
                  </div>
                  {dataset.notes && (
                    <p
                      className="text-xs text-muted-foreground mt-1 truncate"
                      data-oid="wp9_j5e"
                    >
                      {dataset.notes}
                    </p>
                  )}
                </TableCell>
                <TableCell data-oid="ny_oxow">
                  <Badge variant="outline" data-oid="0wppg7o">
                    {dataset.version}
                  </Badge>
                </TableCell>
                <TableCell data-oid="7ak_u6l">
                  {dataset.source_url ? (
                    <div
                      className="flex items-center space-x-1"
                      data-oid="_p0jg4w"
                    >
                      <span className="text-xs" data-oid="12504sr">
                        HuggingFace
                      </span>
                      <Badge
                        variant="secondary"
                        className="text-xs"
                        data-oid="-y0msp9"
                      >
                        Remote
                      </Badge>
                    </div>
                  ) : (
                    <Badge
                      variant="outline"
                      className="text-xs"
                      data-oid="wkfml._"
                    >
                      Local
                    </Badge>
                  )}
                </TableCell>
                <TableCell data-oid="896r2-5">
                  {dataset.license ? (
                    <span className="text-sm" data-oid="3srcv19">
                      {dataset.license}
                    </span>
                  ) : (
                    <span
                      className="text-sm text-muted-foreground"
                      data-oid="e-1sos5"
                    >
                      —
                    </span>
                  )}
                </TableCell>
                <TableCell data-oid="219-6e7">
                  <div
                    className="flex items-center space-x-1"
                    data-oid="-hm9ufy"
                  >
                    <Calendar
                      className="h-3 w-3 text-muted-foreground"
                      data-oid="e3mc5nx"
                    />

                    <span className="text-xs" data-oid="gy_c391">
                      {formatDistanceToNow(new Date(dataset.created_at), {
                        addSuffix: true,
                      })}
                    </span>
                  </div>
                </TableCell>
                <TableCell data-oid="barjzt8">
                  <div
                    className="flex items-center space-x-1"
                    data-oid="7-mzjy6"
                  >
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onViewScenes?.(dataset);
                      }}
                      data-oid="afqagq."
                    >
                      View
                    </Button>
                    <Button
                      variant="default"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onProcessDataset?.(dataset);
                      }}
                      data-oid="upt._dq"
                    >
                      Process
                    </Button>
                  </div>
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
