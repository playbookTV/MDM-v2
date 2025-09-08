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
        data-oid="xuu6--l"
      >
        <div className="flex items-center space-x-2 mb-4" data-oid="73c006c">
          <AlertTriangle
            className="h-5 w-5 text-destructive"
            data-oid="m0dra:v"
          />
          <h3 className="text-lg font-semibold" data-oid="4zwie60">
            System Health
          </h3>
          <Badge variant="destructive" data-oid=".87g0k9">
            Error
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground" data-oid="qi_b072">
          Unable to fetch system health data
        </p>
      </div>
    );
  }

  if (isLoading || !health) {
    return (
      <div
        className={`bg-card border rounded-lg p-6 ${className}`}
        data-oid="cxci4mc"
      >
        <div className="flex items-center space-x-2 mb-4" data-oid="hmatg9h">
          <Activity className="h-5 w-5 animate-pulse" data-oid="bkscodv" />
          <h3 className="text-lg font-semibold" data-oid="8k96l7t">
            System Health
          </h3>
        </div>
        <div className="space-y-4" data-oid="6c3_nbn">
          {Array.from({ length: 4 }, (_, i) => (
            <div key={i} className="space-y-2" data-oid="zbniflb">
              <div
                className="h-4 bg-muted animate-pulse rounded"
                data-oid="nst08k4"
              />
              <div
                className="h-2 bg-muted animate-pulse rounded"
                data-oid="mobjy:2"
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
      data-oid="s.42g-a"
    >
      {/* Header */}
      <div
        className="flex items-center justify-between mb-6"
        data-oid="4jk:r9l"
      >
        <div className="flex items-center space-x-2" data-oid="tyxnx1t">
          <Activity className="h-5 w-5" data-oid="txhv1k9" />
          <h3 className="text-lg font-semibold" data-oid="cpnsmu3">
            System Health
          </h3>
        </div>

        <div className="flex items-center space-x-2" data-oid="2l_tzwr">
          {healthStatus.status === "healthy" && (
            <CheckCircle
              className="h-4 w-4 text-green-500"
              data-oid=".a-qpqi"
            />
          )}
          {healthStatus.status === "warning" && (
            <AlertTriangle
              className="h-4 w-4 text-yellow-500"
              data-oid="cid8i1."
            />
          )}
          {healthStatus.status === "critical" && (
            <AlertTriangle
              className="h-4 w-4 text-red-500"
              data-oid="g95csl5"
            />
          )}

          <Badge
            variant={
              healthStatus.status === "healthy" ? "secondary" : "destructive"
            }
            className={healthStatus.color}
            data-oid="oiduq-e"
          >
            {healthStatus.label}
          </Badge>
        </div>
      </div>

      {/* System Metrics */}
      <div className="space-y-6" data-oid="6_.42fs">
        {/* CPU Usage */}
        <div className="space-y-2" data-oid="pot4sel">
          <div className="flex items-center justify-between" data-oid="0id-jv_">
            <div className="flex items-center space-x-2" data-oid="j:.3udk">
              <Cpu className="h-4 w-4 text-blue-500" data-oid="iye0p7o" />
              <span className="text-sm font-medium" data-oid="5hqz3ma">
                CPU Usage
              </span>
            </div>
            <span className="text-sm text-muted-foreground" data-oid="3iomb4f">
              {(health.cpu_usage_percent || 0).toFixed(1)}%
            </span>
          </div>
          <Progress
            value={health.cpu_usage_percent || 0}
            className="h-2"
            data-oid="ieng:p9"
          />
        </div>

        {/* Memory Usage */}
        <div className="space-y-2" data-oid="rh.bi14">
          <div className="flex items-center justify-between" data-oid="usu.dia">
            <div className="flex items-center space-x-2" data-oid="l4.ogoe">
              <Memory className="h-4 w-4 text-green-500" data-oid="26i:yej" />
              <span className="text-sm font-medium" data-oid="v6---0y">
                Memory Usage
              </span>
            </div>
            <span className="text-sm text-muted-foreground" data-oid="mrufgbc">
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
            data-oid="cfopjuy"
          />
        </div>

        {/* Disk Usage */}
        <div className="space-y-2" data-oid="z1au8oq">
          <div className="flex items-center justify-between" data-oid=":.-7d.x">
            <div className="flex items-center space-x-2" data-oid="f.m6ss5">
              <HardDrive
                className="h-4 w-4 text-purple-500"
                data-oid="dov86z8"
              />
              <span className="text-sm font-medium" data-oid="eol260t">
                Disk Usage
              </span>
            </div>
            <span className="text-sm text-muted-foreground" data-oid=":jqy0a.">
              {(health.disk_usage_percent || 0).toFixed(1)}%
            </span>
          </div>
          <Progress
            value={health.disk_usage_percent || 0}
            className="h-2"
            data-oid="387yu8a"
          />
        </div>

        {/* Processing Stats Grid */}
        <div
          className="grid grid-cols-2 gap-4 pt-4 border-t"
          data-oid="bky30zi"
        >
          <div className="text-center" data-oid="ymotb1n">
            <div
              className="flex items-center justify-center space-x-1 mb-1"
              data-oid="h9ghlt1"
            >
              <Users
                className="h-4 w-4 text-muted-foreground"
                data-oid="t8_--18"
              />
              <span
                className="text-xs text-muted-foreground"
                data-oid="od4p4q6"
              >
                Workers
              </span>
            </div>
            <div className="text-xl font-semibold" data-oid="cr57l6r">
              {health.active_workers || 0}
            </div>
            <div className="text-xs text-muted-foreground" data-oid="tgj1ur6">
              Queue: {health.queue_depth || 0}
            </div>
          </div>

          <div className="text-center" data-oid="uosic64">
            <div
              className="flex items-center justify-center space-x-1 mb-1"
              data-oid="r2njw80"
            >
              <Activity
                className="h-4 w-4 text-muted-foreground"
                data-oid="hyce.dt"
              />
              <span
                className="text-xs text-muted-foreground"
                data-oid="oaq4fe:"
              >
                Processing Rate
              </span>
              {processingTrend.direction === "up" && (
                <TrendingUp
                  className="h-3 w-3 text-green-500"
                  data-oid="omtvvf."
                />
              )}
              {processingTrend.direction === "down" && (
                <TrendingDown
                  className="h-3 w-3 text-red-500"
                  data-oid="q6at1n-"
                />
              )}
            </div>
            <div className="text-xl font-semibold" data-oid="iq9e22j">
              {(health.processing_rate_per_minute || 0).toFixed(1)}
            </div>
            <div className="text-xs text-muted-foreground" data-oid="wumxxf0">
              scenes/min
            </div>
          </div>
        </div>

        {/* Uptime */}
        <div
          className="flex items-center justify-between pt-4 border-t"
          data-oid="_vre824"
        >
          <div className="flex items-center space-x-2" data-oid="vlsro:6">
            <Clock
              className="h-4 w-4 text-muted-foreground"
              data-oid="_bm6pf6"
            />
            <span className="text-sm text-muted-foreground" data-oid="ms2tbmp">
              Uptime
            </span>
          </div>
          <span className="text-sm font-medium" data-oid="lx4avc5">
            {formatUptime(health.uptime_seconds)}
          </span>
        </div>

        {/* Last Updated */}
        <div
          className="text-xs text-muted-foreground text-center"
          data-oid="r.2nkh1"
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
