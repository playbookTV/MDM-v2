import { formatDistanceToNow } from "date-fns";
import {
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
      data-oid="h744z.e"
    >
      {/* Header */}
      <div className="flex items-start justify-between mb-4" data-oid="xi86f4m">
        <div className="flex items-center space-x-3" data-oid="9bwjmut">
          <div className={`p-2 rounded-full bg-background`} data-oid="w_ku:0.">
            <StatusIcon
              className={`h-5 w-5 ${statusConfig.color} ${
                job.status === "running" ? "animate-spin" : ""
              }`}
              data-oid="fp-4:i3"
            />
          </div>

          <div data-oid="p-7ux3p">
            <div className="flex items-center space-x-2" data-oid=":zh6clf">
              <h3 className="font-semibold text-lg" data-oid="sbu8p_v">
                {KIND_LABELS[job.kind]}
              </h3>
              <Badge variant={statusConfig.badge} data-oid="gzsq32e">
                {statusConfig.label}
              </Badge>
            </div>

            <div
              className="flex items-center space-x-2 mt-1 text-sm text-muted-foreground"
              data-oid="gn1ynfl"
            >
              <Database className="h-3 w-3" data-oid="mnbilaf" />
              <span data-oid="0s2bi47">
                {job.dataset_name || job.dataset_id}
              </span>
              <span data-oid="m79mo_r">•</span>
              <span data-oid="jx-8u5j">Job #{job.id.slice(-8)}</span>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center space-x-2" data-oid="fbhuerr">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onViewLogs?.(job)}
            data-oid="2f:-yoe"
          >
            <FileText className="h-4 w-4 mr-1" data-oid="ums21vt" />
            Logs
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => onViewDataset?.(job)}
            data-oid="5:kejba"
          >
            <Database className="h-4 w-4 mr-1" data-oid="ac.bgan" />
            Dataset
          </Button>

          {canCancel && (
            <Button
              variant="destructive"
              size="sm"
              onClick={handleCancel}
              disabled={cancelMutation.isPending}
              data-oid=":8nbsxm"
            >
              <Square className="h-4 w-4 mr-1" data-oid="zqmnq-m" />
              Cancel
            </Button>
          )}

          {canRetry && (
            <Button
              variant="default"
              size="sm"
              onClick={handleRetry}
              disabled={retryMutation.isPending}
              data-oid="s_2yo_d"
            >
              <RotateCcw className="h-4 w-4 mr-1" data-oid="2249ypy" />
              Retry
            </Button>
          )}
        </div>
      </div>

      {/* Progress Section */}
      {job.progress && (
        <div className="mb-4" data-oid="q9l845o">
          <JobProgressChart progress={job.progress} data-oid="6oe6qoh" />
        </div>
      )}

      {/* Error Message */}
      {job.status === "failed" && job.error_message && (
        <div
          className="mb-4 p-3 bg-destructive/10 border border-destructive/20 rounded-md"
          data-oid="qe1zsp0"
        >
          <div className="flex items-center space-x-2 mb-2" data-oid="l01gv22">
            <AlertTriangle
              className="h-4 w-4 text-destructive"
              data-oid="smfgfgv"
            />

            <span className="font-medium text-destructive" data-oid="m44ok8l">
              Error Details
            </span>
          </div>
          <p className="text-sm text-destructive/80" data-oid="y5fdbrv">
            {job.error_message}
          </p>
        </div>
      )}

      {/* Footer with Timestamps */}
      <div
        className="flex items-center justify-between text-xs text-muted-foreground pt-3 border-t border-background"
        data-oid="wjx93gb"
      >
        <div className="flex items-center space-x-4" data-oid="c:0_rbm">
          <span data-oid="xsd2zql">
            Created{" "}
            {formatDistanceToNow(new Date(job.created_at), { addSuffix: true })}
          </span>

          {job.started_at && (
            <span data-oid="wge-8m4">
              Started{" "}
              {formatDistanceToNow(new Date(job.started_at), {
                addSuffix: true,
              })}
            </span>
          )}

          {job.finished_at && (
            <span data-oid="m7q4kmq">
              Finished{" "}
              {formatDistanceToNow(new Date(job.finished_at), {
                addSuffix: true,
              })}
            </span>
          )}
        </div>

        {getDuration() && (
          <div className="flex items-center space-x-1" data-oid="zrtux_z">
            <Clock className="h-3 w-3" data-oid="i_9b8cs" />
            <span data-oid="edru07c">Duration: {getDuration()}</span>
          </div>
        )}
      </div>
    </div>
  );
}
