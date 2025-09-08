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
      <div className="space-y-3" data-oid="jnxla1m">
        {Array.from({ length: 3 }, (_, i) => (
          <div
            key={i}
            className="h-16 bg-muted animate-pulse rounded-md"
            data-oid="s1d9km9"
          />
        ))}
      </div>
    );
  }

  if (datasets.length === 0) {
    return (
      <div className="text-center py-12" data-oid="f1qm8pj">
        <Package
          className="mx-auto h-12 w-12 text-muted-foreground"
          data-oid="j3cawpx"
        />
        <h3
          className="mt-2 text-sm font-semibold text-gray-900"
          data-oid="eigyoef"
        >
          No datasets
        </h3>
        <p className="mt-1 text-sm text-gray-500" data-oid="zx1v8h3">
          Get started by uploading your first dataset.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-md border" data-oid="o3rls_u">
      <Table data-oid="v.9mv4.">
        <TableHeader data-oid="e73x8gx">
          <TableRow data-oid="hwdow6t">
            <TableHead data-oid="ah4dt61">Name</TableHead>
            <TableHead data-oid="me:26qb">Version</TableHead>
            <TableHead data-oid="5mfiexa">Source</TableHead>
            <TableHead data-oid="44tx.m6">License</TableHead>
            <TableHead data-oid="hlmnaj2">Created</TableHead>
            <TableHead className="w-32" data-oid="ntggw::">
              Actions
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody data-oid="e:uqw7i">
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
                data-oid="i681xa_"
              >
                <TableCell className="font-medium" data-oid="pgjypc-">
                  <div
                    className="flex items-center space-x-2"
                    data-oid="y9x31xg"
                  >
                    <span data-oid=":oa2fx:">{dataset.name}</span>
                    {dataset.source_url && (
                      <ExternalLink
                        className="h-3 w-3 text-muted-foreground"
                        data-oid="7cy-b34"
                      />
                    )}
                  </div>
                  {dataset.notes && (
                    <p
                      className="text-xs text-muted-foreground mt-1 truncate"
                      data-oid=".-urqah"
                    >
                      {dataset.notes}
                    </p>
                  )}
                </TableCell>
                <TableCell data-oid="uuhdnga">
                  <Badge variant="outline" data-oid="-x1dl7f">
                    {dataset.version}
                  </Badge>
                </TableCell>
                <TableCell data-oid="xo_.0jf">
                  {dataset.source_url ? (
                    <div
                      className="flex items-center space-x-1"
                      data-oid="0q79qnv"
                    >
                      <span className="text-xs" data-oid="_..980q">
                        HuggingFace
                      </span>
                      <Badge
                        variant="secondary"
                        className="text-xs"
                        data-oid="e47-dpo"
                      >
                        Remote
                      </Badge>
                    </div>
                  ) : (
                    <Badge
                      variant="outline"
                      className="text-xs"
                      data-oid="gjrdd9n"
                    >
                      Local
                    </Badge>
                  )}
                </TableCell>
                <TableCell data-oid="mkl8m:z">
                  {dataset.license ? (
                    <span className="text-sm" data-oid="75-oidl">
                      {dataset.license}
                    </span>
                  ) : (
                    <span
                      className="text-sm text-muted-foreground"
                      data-oid="i1rnejw"
                    >
                      —
                    </span>
                  )}
                </TableCell>
                <TableCell data-oid="_r09m6w">
                  <div
                    className="flex items-center space-x-1"
                    data-oid="4hbcd-l"
                  >
                    <Calendar
                      className="h-3 w-3 text-muted-foreground"
                      data-oid="b0806zc"
                    />
                    <span className="text-xs" data-oid="umps-c.">
                      {formatDistanceToNow(new Date(dataset.created_at), {
                        addSuffix: true,
                      })}
                    </span>
                  </div>
                </TableCell>
                <TableCell data-oid="out2vlk">
                  <div
                    className="flex items-center space-x-1"
                    data-oid="d60q5sx"
                  >
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={(e) => {
                        e.stopPropagation();
                        onViewScenes?.(dataset);
                      }}
                      data-oid="iustz1w"
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
                      data-oid="qq4tudx"
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
