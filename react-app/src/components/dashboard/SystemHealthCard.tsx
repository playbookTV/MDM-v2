import {
  Cpu,
  HardDrive,
  Database as Memory,
  Users,
  Clock,
  Activity,
  AlertTriangle,
  CheckCircle,
  TrendingUp,
  TrendingDown,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useSystemHealth, useSystemTrends } from "@/hooks/useStats";
import type { StatsQuery } from "@/types/stats";

interface SystemHealthCardProps {
  query?: StatsQuery;
  className?: string;
}

export function SystemHealthCard({ className }: SystemHealthCardProps) {
  const { data: health, isLoading, error } = useSystemHealth();
  const { data: trends } = useSystemTrends({
    time_range: "1h",
    granularity: "minute",
  });

  const getHealthStatus = () => {
    if (!health)
      return { status: "unknown", label: "Unknown", color: "text-gray-500" };

    const criticalThreshold = 90;
    const warningThreshold = 75;

    const cpuUsage = health.cpu_usage_percent || 0;
    const memoryUsage =
      health.memory_usage_percent ||
      (health.memory_usage_mb
        ? Math.min((health.memory_usage_mb / 8192) * 100, 100)
        : 0);
    const diskUsage = health.disk_usage_percent || 0;
    const maxUsage = Math.max(cpuUsage, memoryUsage, diskUsage);

    if (maxUsage >= criticalThreshold) {
      return { status: "critical", label: "Critical", color: "text-red-500" };
    } else if (maxUsage >= warningThreshold) {
      return { status: "warning", label: "Warning", color: "text-yellow-500" };
    } else {
      return { status: "healthy", label: "Healthy", color: "text-green-500" };
    }
  };

  const formatUptime = (seconds: number) => {
    const days = Math.floor(seconds / (24 * 3600));
    const hours = Math.floor((seconds % (24 * 3600)) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);

    if (days > 0) {
      return `${days}d ${hours}h ${minutes}m`;
    } else if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  };

  const getProcessingTrend = () => {
    if (!trends || trends.length < 2) return { direction: "stable", change: 0 };

    const latest = trends[trends.length - 1];
    const previous = trends[trends.length - 2];

    const change = latest.processing_rate - previous.processing_rate;
    const direction = change > 0 ? "up" : change < 0 ? "down" : "stable";

    return { direction, change: Math.abs(change) };
  };

  const healthStatus = getHealthStatus();
  const processingTrend = getProcessingTrend();

  if (error) {
    return (
      <div
        className={`bg-card border rounded-lg p-6 ${className}`}
        data-oid=":s_gcvr"
      >
        <div className="flex items-center space-x-2 mb-4" data-oid="crj9g81">
          <AlertTriangle
            className="h-5 w-5 text-destructive"
            data-oid="w3w82oq"
          />

          <h3 className="text-lg font-semibold" data-oid="0vl0m45">
            System Health
          </h3>
          <Badge variant="destructive" data-oid="s69qo9.">
            Error
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground" data-oid="rgjthfw">
          Unable to fetch system health data
        </p>
      </div>
    );
  }

  if (isLoading || !health) {
    return (
      <div
        className={`bg-card border rounded-lg p-6 ${className}`}
        data-oid="l35aat."
      >
        <div className="flex items-center space-x-2 mb-4" data-oid="wbigh8j">
          <Activity className="h-5 w-5 animate-pulse" data-oid="h69is8a" />
          <h3 className="text-lg font-semibold" data-oid="_e:tdnv">
            System Health
          </h3>
        </div>
        <div className="space-y-4" data-oid="3.4h33k">
          {Array.from({ length: 4 }, (_, i) => (
            <div key={i} className="space-y-2" data-oid="9u9h3wv">
              <div
                className="h-4 bg-muted animate-pulse rounded"
                data-oid="rnciw9u"
              />

              <div
                className="h-2 bg-muted animate-pulse rounded"
                data-oid="1--il99"
              />
            </div>
          ))}
        </div>
      </div>
    );
  }

  return (
    <div
      className={`bg-card border rounded-lg p-6 ${className}`}
      data-oid="6zzsm-t"
    >
      {/* Header */}
      <div
        className="flex items-center justify-between mb-6"
        data-oid="vsro7rw"
      >
        <div className="flex items-center space-x-2" data-oid="3v2jmg4">
          <Activity className="h-5 w-5" data-oid="qi5p18_" />
          <h3 className="text-lg font-semibold" data-oid=".z230wf">
            System Health
          </h3>
        </div>

        <div className="flex items-center space-x-2" data-oid="3_xz76_">
          {healthStatus.status === "healthy" && (
            <CheckCircle
              className="h-4 w-4 text-green-500"
              data-oid="e_fnrzo"
            />
          )}
          {healthStatus.status === "warning" && (
            <AlertTriangle
              className="h-4 w-4 text-yellow-500"
              data-oid="_93_iki"
            />
          )}
          {healthStatus.status === "critical" && (
            <AlertTriangle
              className="h-4 w-4 text-red-500"
              data-oid="bum6wz:"
            />
          )}

          <Badge
            variant={
              healthStatus.status === "healthy" ? "secondary" : "destructive"
            }
            className={healthStatus.color}
            data-oid="2isy-lb"
          >
            {healthStatus.label}
          </Badge>
        </div>
      </div>

      {/* System Metrics */}
      <div className="space-y-6" data-oid="4o34f3p">
        {/* CPU Usage */}
        <div className="space-y-2" data-oid="q-0thc6">
          <div className="flex items-center justify-between" data-oid="gy2xx0u">
            <div className="flex items-center space-x-2" data-oid="9:41we.">
              <Cpu className="h-4 w-4 text-blue-500" data-oid="bybcstj" />
              <span className="text-sm font-medium" data-oid="ll6kinb">
                CPU Usage
              </span>
            </div>
            <span className="text-sm text-muted-foreground" data-oid="rgtdhyn">
              {(health.cpu_usage_percent || 0).toFixed(1)}%
            </span>
          </div>
          <Progress
            value={health.cpu_usage_percent || 0}
            className="h-2"
            data-oid="8ifkxg8"
          />
        </div>

        {/* Memory Usage */}
        <div className="space-y-2" data-oid="qp2c.b8">
          <div className="flex items-center justify-between" data-oid="yhz7ent">
            <div className="flex items-center space-x-2" data-oid="ivz6ir1">
              <Memory className="h-4 w-4 text-green-500" data-oid="tm6j369" />
              <span className="text-sm font-medium" data-oid="xus2zav">
                Memory Usage
              </span>
            </div>
            <span className="text-sm text-muted-foreground" data-oid="uix2ftq">
              {(
                health.memory_usage_percent ||
                (health.memory_usage_mb
                  ? Math.min((health.memory_usage_mb / 8192) * 100, 100)
                  : 0)
              ).toFixed(1)}
              %
            </span>
          </div>
          <Progress
            value={
              health.memory_usage_percent ||
              (health.memory_usage_mb
                ? Math.min((health.memory_usage_mb / 8192) * 100, 100)
                : 0)
            }
            className="h-2"
            data-oid="-zv2qxg"
          />
        </div>

        {/* Disk Usage */}
        <div className="space-y-2" data-oid="t0yquj6">
          <div className="flex items-center justify-between" data-oid="vp58jdc">
            <div className="flex items-center space-x-2" data-oid="g3np_kx">
              <HardDrive
                className="h-4 w-4 text-purple-500"
                data-oid="jnbr35j"
              />

              <span className="text-sm font-medium" data-oid="exf38gj">
                Disk Usage
              </span>
            </div>
            <span className="text-sm text-muted-foreground" data-oid="3-qmhpx">
              {(health.disk_usage_percent || 0).toFixed(1)}%
            </span>
          </div>
          <Progress
            value={health.disk_usage_percent || 0}
            className="h-2"
            data-oid="h0bako2"
          />
        </div>

        {/* Processing Stats Grid */}
        <div
          className="grid grid-cols-2 gap-4 pt-4 border-t"
          data-oid="armr40t"
        >
          <div className="text-center" data-oid=".r7h47s">
            <div
              className="flex items-center justify-center space-x-1 mb-1"
              data-oid="2-k5pfv"
            >
              <Users
                className="h-4 w-4 text-muted-foreground"
                data-oid=":3c99.g"
              />

              <span
                className="text-xs text-muted-foreground"
                data-oid=":821pwe"
              >
                Workers
              </span>
            </div>
            <div className="text-xl font-semibold" data-oid="zac-cpz">
              {health.active_workers || 0}
            </div>
            <div className="text-xs text-muted-foreground" data-oid="23srbyx">
              Queue: {health.queue_depth || 0}
            </div>
          </div>

          <div className="text-center" data-oid=":hhe0pr">
            <div
              className="flex items-center justify-center space-x-1 mb-1"
              data-oid="-aneco3"
            >
              <Activity
                className="h-4 w-4 text-muted-foreground"
                data-oid="nf31.q4"
              />

              <span
                className="text-xs text-muted-foreground"
                data-oid="-fj39qa"
              >
                Processing Rate
              </span>
              {processingTrend.direction === "up" && (
                <TrendingUp
                  className="h-3 w-3 text-green-500"
                  data-oid="lyl6mfn"
                />
              )}
              {processingTrend.direction === "down" && (
                <TrendingDown
                  className="h-3 w-3 text-red-500"
                  data-oid=":8j8h.c"
                />
              )}
            </div>
            <div className="text-xl font-semibold" data-oid="cfdz:sz">
              {(health.processing_rate_per_minute || 0).toFixed(1)}
            </div>
            <div className="text-xs text-muted-foreground" data-oid="hs8co5z">
              scenes/min
            </div>
          </div>
        </div>

        {/* Uptime */}
        <div
          className="flex items-center justify-between pt-4 border-t"
          data-oid="yuu40g9"
        >
          <div className="flex items-center space-x-2" data-oid="85oe364">
            <Clock
              className="h-4 w-4 text-muted-foreground"
              data-oid="xmtvnwp"
            />

            <span className="text-sm text-muted-foreground" data-oid="022g4qp">
              Uptime
            </span>
          </div>
          <span className="text-sm font-medium" data-oid="vgmsc3u">
            {formatUptime(health.uptime_seconds)}
          </span>
        </div>

        {/* Last Updated */}
        <div
          className="text-xs text-muted-foreground text-center"
          data-oid="n9nslrh"
        >
          Last updated:{" "}
          {health.last_updated
            ? new Date(health.last_updated).toLocaleTimeString()
            : "Unknown"}
        </div>
      </div>
    </div>
  );
}
