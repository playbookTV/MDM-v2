import { useMemo } from "react";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import type { JobProgress } from "@/types/dataset";

interface JobProgressChartProps {
  progress: JobProgress;
  className?: string;
}

export function JobProgressChart({
  progress,
  className,
}: JobProgressChartProps) {
  const progressPercentage = useMemo(() => {
    if (progress.scenes_total === 0) return 0;
    return Math.round((progress.scenes_done / progress.scenes_total) * 100);
  }, [progress.scenes_done, progress.scenes_total]);

  const processingRate = useMemo(() => {
    return progress.processing_rate
      ? progress.processing_rate.toFixed(1)
      : "0.0";
  }, [progress.processing_rate]);

  const etaDisplay = useMemo(() => {
    if (!progress.eta_seconds) return "Unknown";

    const hours = Math.floor(progress.eta_seconds / 3600);
    const minutes = Math.floor((progress.eta_seconds % 3600) / 60);
    const seconds = progress.eta_seconds % 60;

    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${seconds}s`;
    } else {
      return `${seconds}s`;
    }
  }, [progress.eta_seconds]);

  const averageConfidence = useMemo(() => {
    return progress.avg_conf ? (progress.avg_conf * 100).toFixed(1) : "0.0";
  }, [progress.avg_conf]);

  return (
    <div className={className} data-oid="0hnc2ji">
      {/* Main Progress Bar */}
      <div className="space-y-2" data-oid="yp2nn_u">
        <div
          className="flex items-center justify-between text-sm"
          data-oid="eta90.z"
        >
          <span className="font-medium" data-oid="21vb:4m">
            {progress.scenes_done.toLocaleString()} /{" "}
            {progress.scenes_total.toLocaleString()} scenes
          </span>
          <span className="text-muted-foreground" data-oid="gur4-0o">
            {progressPercentage}%
          </span>
        </div>

        <Progress
          value={progressPercentage}
          className="h-3"
          data-oid="_tnzj_x"
        />

        {progress.current_scene && (
          <p
            className="text-xs text-muted-foreground truncate"
            data-oid="868h54_"
          >
            Processing: {progress.current_scene}
          </p>
        )}
      </div>

      {/* Progress Stats Grid */}
      <div
        className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4"
        data-oid="lqn_w.:"
      >
        <div className="bg-muted/50 rounded-md p-3" data-oid="7pp_iy3">
          <div
            className="text-xs text-muted-foreground mb-1"
            data-oid="10x17bj"
          >
            Objects Detected
          </div>
          <div className="text-lg font-semibold" data-oid="vogsq3n">
            {progress.objects_detected.toLocaleString()}
          </div>
        </div>

        <div className="bg-muted/50 rounded-md p-3" data-oid="3vq94lp">
          <div
            className="text-xs text-muted-foreground mb-1"
            data-oid="di_pc6x"
          >
            Avg Confidence
          </div>
          <div className="text-lg font-semibold" data-oid="9zu87ud">
            {averageConfidence}%
          </div>
        </div>

        <div className="bg-muted/50 rounded-md p-3" data-oid=":4f:lwc">
          <div
            className="text-xs text-muted-foreground mb-1"
            data-oid="rp0y6a2"
          >
            Processing Rate
          </div>
          <div className="text-lg font-semibold" data-oid="o0_8dtx">
            {processingRate}{" "}
            <span className="text-sm font-normal" data-oid="-jrq::4">
              scenes/min
            </span>
          </div>
        </div>

        <div className="bg-muted/50 rounded-md p-3" data-oid="dubcv-y">
          <div
            className="text-xs text-muted-foreground mb-1"
            data-oid="_ssarym"
          >
            ETA
          </div>
          <div className="text-lg font-semibold" data-oid="1jrdjb2">
            {etaDisplay}
          </div>
        </div>
      </div>

      {/* Failure Badge */}
      {progress.failures > 0 && (
        <div className="mt-3 flex items-center space-x-2" data-oid="tv5khv3">
          <Badge variant="destructive" data-oid="4793sbz">
            {progress.failures} failure{progress.failures !== 1 ? "s" : ""}
          </Badge>
          <span className="text-xs text-muted-foreground" data-oid="ylvkwbt">
            {((progress.failures / (progress.scenes_done || 1)) * 100).toFixed(
              1,
            )}
            % failure rate
          </span>
        </div>
      )}
    </div>
  );
}
