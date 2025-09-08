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
    <div className={className} data-oid="3cbwl9a">
      {/* Main Progress Bar */}
      <div className="space-y-2" data-oid="5uxpnys">
        <div
          className="flex items-center justify-between text-sm"
          data-oid="a1:clh2"
        >
          <span className="font-medium" data-oid="sms8uh0">
            {progress.scenes_done.toLocaleString()} /{" "}
            {progress.scenes_total.toLocaleString()} scenes
          </span>
          <span className="text-muted-foreground" data-oid="zd.btqt">
            {progressPercentage}%
          </span>
        </div>

        <Progress
          value={progressPercentage}
          className="h-3"
          data-oid="0mnb4op"
        />

        {progress.current_scene && (
          <p
            className="text-xs text-muted-foreground truncate"
            data-oid="5i-2ac8"
          >
            Processing: {progress.current_scene}
          </p>
        )}
      </div>

      {/* Progress Stats Grid */}
      <div
        className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4"
        data-oid="1ry6r-m"
      >
        <div className="bg-muted/50 rounded-md p-3" data-oid="9q7s4jd">
          <div
            className="text-xs text-muted-foreground mb-1"
            data-oid=".93a0vl"
          >
            Objects Detected
          </div>
          <div className="text-lg font-semibold" data-oid="d39wr6g">
            {progress.objects_detected.toLocaleString()}
          </div>
        </div>

        <div className="bg-muted/50 rounded-md p-3" data-oid="e2q3k2u">
          <div
            className="text-xs text-muted-foreground mb-1"
            data-oid="shpj1xt"
          >
            Avg Confidence
          </div>
          <div className="text-lg font-semibold" data-oid="yqnqsb0">
            {averageConfidence}%
          </div>
        </div>

        <div className="bg-muted/50 rounded-md p-3" data-oid="jj888go">
          <div
            className="text-xs text-muted-foreground mb-1"
            data-oid="a-xrjjp"
          >
            Processing Rate
          </div>
          <div className="text-lg font-semibold" data-oid="3q3cx27">
            {processingRate}{" "}
            <span className="text-sm font-normal" data-oid="f6_l5b2">
              scenes/min
            </span>
          </div>
        </div>

        <div className="bg-muted/50 rounded-md p-3" data-oid="bq17:hg">
          <div
            className="text-xs text-muted-foreground mb-1"
            data-oid=".bunmd."
          >
            ETA
          </div>
          <div className="text-lg font-semibold" data-oid="awdt714">
            {etaDisplay}
          </div>
        </div>
      </div>

      {/* Failure Badge */}
      {progress.failures > 0 && (
        <div className="mt-3 flex items-center space-x-2" data-oid="tu-qacc">
          <Badge variant="destructive" data-oid="p5pxi95">
            {progress.failures} failure{progress.failures !== 1 ? "s" : ""}
          </Badge>
          <span className="text-xs text-muted-foreground" data-oid="h6krxqa">
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
