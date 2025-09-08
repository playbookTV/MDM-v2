import { formatDistanceToNow } from "date-fns";
import {
  Play,
  Pause,
  Square,
  RotateCcw,
  FileText,
  Clock,
  AlertTriangle,
  CheckCircle,
  Loader2,
  Database,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { JobProgressChart } from "./JobProgressChart";
import { useCancelJob, useRetryJob } from "@/hooks/useJobs";
import type { Job } from "@/types/dataset";

interface JobCardProps {
  job: Job;
  onViewLogs?: (job: Job) => void;
  onViewDataset?: (job: Job) => void;
  className?: string;
}

const STATUS_CONFIG = {
  queued: {
    icon: Clock,
    color: "text-yellow-500",
    bgColor: "bg-yellow-50 border-yellow-200",
    badge: "default" as const,
    label: "Queued",
  },
  running: {
    icon: Loader2,
    color: "text-blue-500",
    bgColor: "bg-blue-50 border-blue-200",
    badge: "default" as const,
    label: "Running",
  },
  succeeded: {
    icon: CheckCircle,
    color: "text-green-500",
    bgColor: "bg-green-50 border-green-200",
    badge: "secondary" as const,
    label: "Completed",
  },
  failed: {
    icon: AlertTriangle,
    color: "text-red-500",
    bgColor: "bg-red-50 border-red-200",
    badge: "destructive" as const,
    label: "Failed",
  },
  skipped: {
    icon: Pause,
    color: "text-gray-500",
    bgColor: "bg-gray-50 border-gray-200",
    badge: "outline" as const,
    label: "Skipped",
  },
};

const KIND_LABELS = {
  ingest: "Data Ingestion",
  process: "AI Processing",
};

export function JobCard({
  job,
  onViewLogs,
  onViewDataset,
  className,
}: JobCardProps) {
  const cancelMutation = useCancelJob();
  const retryMutation = useRetryJob();

  const statusConfig = STATUS_CONFIG[job.status];
  const StatusIcon = statusConfig.icon;
  const isActive = job.status === "running" || job.status === "queued";
  const canCancel = job.status === "running" || job.status === "queued";
  const canRetry = job.status === "failed";

  const handleCancel = async () => {
    if (confirm("Are you sure you want to cancel this job?")) {
      try {
        await cancelMutation.mutateAsync(job.id);
      } catch (error) {
        console.error("Failed to cancel job:", error);
      }
    }
  };

  const handleRetry = async () => {
    try {
      await retryMutation.mutateAsync(job.id);
    } catch (error) {
      console.error("Failed to retry job:", error);
    }
  };

  const getDuration = () => {
    if (!job.started_at) return null;

    const startTime = new Date(job.started_at);
    const endTime = job.finished_at ? new Date(job.finished_at) : new Date();
    const durationMs = endTime.getTime() - startTime.getTime();

    const hours = Math.floor(durationMs / (1000 * 60 * 60));
    const minutes = Math.floor((durationMs % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((durationMs % (1000 * 60)) / 1000);

    if (hours > 0) {
      return `${hours}h ${minutes}m ${seconds}s`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    } else {
      return `${seconds}s`;
    }
  };

  return (
    <div
      className={`border rounded-lg p-6 ${statusConfig.bgColor} ${className}`}
      data-oid="1hte36x"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4" data-oid="n3vu3k5">
        <div className="flex items-center space-x-3" data-oid="3ulk6ob">
          <div className={`p-2 rounded-full bg-background`} data-oid="kuyc4.u">
            <StatusIcon
              className={`h-5 w-5 ${statusConfig.color} ${
                job.status === "running" ? "animate-spin" : ""
              }`}
              data-oid="c7jv5-l"
            />
          </div>

          <div data-oid="l0x0gky">
            <div className="flex items-center space-x-2" data-oid="6gvipkw">
              <h3 className="font-semibold text-lg" data-oid="58.ox2b">
                {KIND_LABELS[job.kind]}
              </h3>
              <Badge variant={statusConfig.badge} data-oid="2e3n-r0">
                {statusConfig.label}
              </Badge>
            </div>

            <div
              className="flex items-center space-x-2 mt-1 text-sm text-muted-foreground"
              data-oid="6:fj9_g"
            >
              <Database className="h-3 w-3" data-oid="o2t4suy" />
              <span data-oid="c7ll4:6">
                {job.dataset_name || job.dataset_id}
              </span>
              <span data-oid="58towdx">•</span>
              <span data-oid="6v-5q2g">Job #{job.id.slice(-8)}</span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-2" data-oid="0:131gy">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onViewLogs?.(job)}
            data-oid="q2uvsmn"
          >
            <FileText className="h-4 w-4 mr-1" data-oid="nzforj_" />
            Logs
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => onViewDataset?.(job)}
            data-oid="-w5sxfq"
          >
            <Database className="h-4 w-4 mr-1" data-oid="qozp2gi" />
            Dataset
          </Button>

          {canCancel && (
            <Button
              variant="destructive"
              size="sm"
              onClick={handleCancel}
              disabled={cancelMutation.isPending}
              data-oid="9ihb40y"
            >
              <Square className="h-4 w-4 mr-1" data-oid="drgj8bb" />
              Cancel
            </Button>
          )}

          {canRetry && (
            <Button
              variant="default"
              size="sm"
              onClick={handleRetry}
              disabled={retryMutation.isPending}
              data-oid="m8:odsd"
            >
              <RotateCcw className="h-4 w-4 mr-1" data-oid="t_49f0f" />
              Retry
            </Button>
          )}
        </div>
      </div>

      {/* Progress Section */}
      {job.progress && (
        <div className="mb-4" data-oid="ekg2hts">
          <JobProgressChart progress={job.progress} data-oid="u_pjaxs" />
        </div>
      )}

      {/* Error Message */}
      {job.status === "failed" && job.error_message && (
        <div
          className="mb-4 p-3 bg-destructive/10 border border-destructive/20 rounded-md"
          data-oid="2x-eroa"
        >
          <div className="flex items-center space-x-2 mb-2" data-oid="wrv2o6.">
            <AlertTriangle
              className="h-4 w-4 text-destructive"
              data-oid="bikixb9"
            />
            <span className="font-medium text-destructive" data-oid="8bcjndr">
              Error Details
            </span>
          </div>
          <p className="text-sm text-destructive/80" data-oid="jg2ml:q">
            {job.error_message}
          </p>
        </div>
      )}

      {/* Footer with Timestamps */}
      <div
        className="flex items-center justify-between text-xs text-muted-foreground pt-3 border-t border-background"
        data-oid="f_wqjeq"
      >
        <div className="flex items-center space-x-4" data-oid="fwsa8n4">
          <span data-oid="8r4n_v0">
            Created{" "}
            {formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}
          </span>

          {job.started_at && (
            <span data-oid="yv8:pac">
              Started{" "}
              {formatDistanceToNow(new Date(job.started_at), {
                addSuffix: true,
              })}
            </span>
          )}

          {job.finished_at && (
            <span data-oid="8g_72so">
              Finished{" "}
              {formatDistanceToNow(new Date(job.finished_at), {
                addSuffix: true,
              })}
            </span>
          )}
        </div>

        {getDuration() && (
          <div className="flex items-center space-x-1" data-oid="8m-vx_b">
            <Clock className="h-3 w-3" data-oid="ztlgsvw" />
            <span data-oid="9.dt3oq">Duration: {getDuration()}</span>
          </div>
        )}
      </div>
    </div>
  );
}
