import { formatDistanceToNow } from 'date-fns'
import { ExternalLink, Calendar, Package } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import type { Dataset } from '@/types/dataset'

interface DatasetTableProps {
  datasets: Dataset[]
  loading?: boolean
  onSelectDataset?: (dataset: Dataset) => void
  onViewScenes?: (dataset: Dataset) => void
  onProcessDataset?: (dataset: Dataset) => void
}

export function DatasetTable({
  datasets,
  loading = false,
  onSelectDataset,
  onViewScenes,
  onProcessDataset,
}: DatasetTableProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 3 }, (_, i) => (
          <div key={i} className="h-16 bg-muted animate-pulse rounded-md" />
        ))}
      </div>
    )
  }

  if (datasets.length === 0) {
    return (
      <div className="text-center py-12">
        <Package className="mx-auto h-12 w-12 text-muted-foreground" />
        <h3 className="mt-2 text-sm font-semibold text-gray-900">No datasets</h3>
        <p className="mt-1 text-sm text-gray-500">
          Get started by uploading your first dataset.
        </p>
      </div>
    )
  }

  return (
    <div className="rounded-md border">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Name</TableHead>
            <TableHead>Version</TableHead>
            <TableHead>Source</TableHead>
            <TableHead>License</TableHead>
            <TableHead>Created</TableHead>
            <TableHead className="w-32">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {datasets.map((dataset) => (
            <TableRow 
              key={dataset.id}
              className="cursor-pointer"
              onClick={() => onSelectDataset?.(dataset)}
            >
              <TableCell className="font-medium">
                <div className="flex items-center space-x-2">
                  <span>{dataset.name}</span>
                  {dataset.source_url && (
                    <ExternalLink className="h-3 w-3 text-muted-foreground" />
                  )}
                </div>
                {dataset.notes && (
                  <p className="text-xs text-muted-foreground mt-1 truncate">
                    {dataset.notes}
                  </p>
                )}
              </TableCell>
              <TableCell>
                <Badge variant="outline">{dataset.version}</Badge>
              </TableCell>
              <TableCell>
                {dataset.source_url ? (
                  <div className="flex items-center space-x-1">
                    <span className="text-xs">HuggingFace</span>
                    <Badge variant="secondary" className="text-xs">
                      Remote
                    </Badge>
                  </div>
                ) : (
                  <Badge variant="outline" className="text-xs">
                    Local
                  </Badge>
                )}
              </TableCell>
              <TableCell>
                {dataset.license ? (
                  <span className="text-sm">{dataset.license}</span>
                ) : (
                  <span className="text-sm text-muted-foreground">—</span>
                )}
              </TableCell>
              <TableCell>
                <div className="flex items-center space-x-1">
                  <Calendar className="h-3 w-3 text-muted-foreground" />
                  <span className="text-xs">
                    {formatDistanceToNow(new Date(dataset.created_at), { addSuffix: true })}
                  </span>
                </div>
              </TableCell>
              <TableCell>
                <div className="flex items-center space-x-1">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      onViewScenes?.(dataset)
                    }}
                  >
                    View
                  </Button>
                  <Button
                    variant="default"
                    size="sm"
                    onClick={(e) => {
                      e.stopPropagation()
                      onProcessDataset?.(dataset)
                    }}
                  >
                    Process
                  </Button>
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}