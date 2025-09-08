import { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import {
  TrendingUp,
  BarChart3,
  PieChart as PieChartIcon,
  Activity,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useProcessingTrends } from "@/hooks/useStats";
import type { StatsQuery } from "@/types/stats";

interface ProcessingMetricsChartProps {
  query?: StatsQuery;
  className?: string;
}

type ChartType = "line" | "bar" | "pie";

export function ProcessingMetricsChart({
  query,
  className,
}: ProcessingMetricsChartProps) {
  const [chartType, setChartType] = useState<ChartType>("line");

  const { data: trends, isLoading, error } = useProcessingTrends(query);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const timeRange = query?.time_range || "24h";

    if (timeRange === "1h" || timeRange === "6h") {
      return date.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
      });
    } else if (timeRange === "24h") {
      return date.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
      });
    } else {
      return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
      });
    }
  };

  const getChartData = () => {
    if (!trends) return [];

    return trends.map((trend) => ({
      date: trend.date,
      dateFormatted: formatDate(trend.date),
      jobsCompleted: trend.jobs_completed,
      jobsFailed: trend.jobs_failed,
      successRate: trend.success_rate * 100,
      processingRate: trend.processing_rate,
      averageConfidence: trend.average_confidence * 100,
    }));
  };

  const getPieData = () => {
    if (!trends) return [];

    const totalCompleted = trends.reduce((sum, t) => sum + t.jobs_completed, 0);
    const totalFailed = trends.reduce((sum, t) => sum + t.jobs_failed, 0);

    return [
      { name: "Completed", value: totalCompleted, color: "#10b981" },
      { name: "Failed", value: totalFailed, color: "#ef4444" },
    ];
  };

  const getSummaryStats = () => {
    if (!trends || trends.length === 0) return null;

    const totalCompleted = trends.reduce((sum, t) => sum + t.jobs_completed, 0);
    const totalFailed = trends.reduce((sum, t) => sum + t.jobs_failed, 0);
    const avgSuccessRate =
      trends.reduce((sum, t) => sum + t.success_rate, 0) / trends.length;
    const avgProcessingRate =
      trends.reduce((sum, t) => sum + t.processing_rate, 0) / trends.length;
    const avgConfidence =
      trends.reduce((sum, t) => sum + t.average_confidence, 0) / trends.length;

    return {
      totalCompleted,
      totalFailed,
      totalJobs: totalCompleted + totalFailed,
      avgSuccessRate: avgSuccessRate * 100,
      avgProcessingRate,
      avgConfidence: avgConfidence * 100,
    };
  };

  const chartData = getChartData();
  const pieData = getPieData();
  const summaryStats = getSummaryStats();

  if (error) {
    return (
      <div
        className={`bg-card border rounded-lg p-6 ${className}`}
        data-oid="_yyzxbh"
      >
        <div className="flex items-center space-x-2 mb-4" data-oid="9x-m:i-">
          <Activity className="h-5 w-5 text-destructive" data-oid="x_de038" />
          <h3 className="text-lg font-semibold" data-oid="x5q7-5q">
            Processing Metrics
          </h3>
          <Badge variant="destructive" data-oid="_-ko-1:">
            Error
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground" data-oid="qyftth.">
          Unable to load processing metrics
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div
        className={`bg-card border rounded-lg p-6 ${className}`}
        data-oid="kbjk-77"
      >
        <div className="flex items-center space-x-2 mb-4" data-oid=".hu6_op">
          <Activity className="h-5 w-5 animate-pulse" data-oid="z0ly482" />
          <h3 className="text-lg font-semibold" data-oid="xbs2mjh">
            Processing Metrics
          </h3>
        </div>
        <div
          className="h-80 bg-muted animate-pulse rounded"
          data-oid=":.abuuw"
        />
      </div>
    );
  }

  return (
    <div
      className={`bg-card border rounded-lg p-6 ${className}`}
      data-oid=".bdlm_6"
    >
      {/* Header */}
      <div
        className="flex items-center justify-between mb-6"
        data-oid="61a:hwp"
      >
        <div className="flex items-center space-x-2" data-oid="jolzfq:">
          <Activity className="h-5 w-5" data-oid="qx5-ont" />
          <h3 className="text-lg font-semibold" data-oid="b1_6rwg">
            Processing Metrics
          </h3>
        </div>

        <div className="flex items-center space-x-2" data-oid="o-68k09">
          <Button
            variant={chartType === "line" ? "default" : "outline"}
            size="sm"
            onClick={() => setChartType("line")}
            data-oid="z24osy3"
          >
            <TrendingUp className="h-4 w-4" data-oid="mgpdjw0" />
          </Button>
          <Button
            variant={chartType === "bar" ? "default" : "outline"}
            size="sm"
            onClick={() => setChartType("bar")}
            data-oid="7dymroh"
          >
            <BarChart3 className="h-4 w-4" data-oid="d9p2qmk" />
          </Button>
          <Button
            variant={chartType === "pie" ? "default" : "outline"}
            size="sm"
            onClick={() => setChartType("pie")}
            data-oid="4yc-0d:"
          >
            <PieChartIcon className="h-4 w-4" data-oid="_.uaejm" />
          </Button>
        </div>
      </div>

      {/* Summary Stats */}
      {summaryStats && (
        <div
          className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6"
          data-oid="xkah_9k"
        >
          <div
            className="text-center p-3 bg-muted/50 rounded-md"
            data-oid="1gixsa4"
          >
            <div
              className="text-2xl font-bold text-green-600"
              data-oid="p1obsjt"
            >
              {summaryStats.totalCompleted.toLocaleString()}
            </div>
            <div className="text-xs text-muted-foreground" data-oid="zvlhuy1">
              Jobs Completed
            </div>
          </div>

          <div
            className="text-center p-3 bg-muted/50 rounded-md"
            data-oid="1z03-56"
          >
            <div className="text-2xl font-bold text-red-600" data-oid="jhq-cyh">
              {summaryStats.totalFailed.toLocaleString()}
            </div>
            <div className="text-xs text-muted-foreground" data-oid="7ndpl7-">
              Jobs Failed
            </div>
          </div>

          <div
            className="text-center p-3 bg-muted/50 rounded-md"
            data-oid="ayb0hyi"
          >
            <div
              className="text-2xl font-bold text-blue-600"
              data-oid="liny.0z"
            >
              {summaryStats.avgSuccessRate.toFixed(1)}%
            </div>
            <div className="text-xs text-muted-foreground" data-oid="uz4h:ul">
              Avg Success Rate
            </div>
          </div>

          <div
            className="text-center p-3 bg-muted/50 rounded-md"
            data-oid="sryf1__"
          >
            <div
              className="text-2xl font-bold text-purple-600"
              data-oid=".byi2ea"
            >
              {summaryStats.avgProcessingRate.toFixed(1)}
            </div>
            <div className="text-xs text-muted-foreground" data-oid="p.l58z8">
              Scenes/min
            </div>
          </div>
        </div>
      )}

      {/* Chart Area */}
      <div className="h-80" data-oid="o_mh2d2">
        {chartData.length === 0 ? (
          <div
            className="flex items-center justify-center h-full text-muted-foreground"
            data-oid="0so6iyj"
          >
            No data available for the selected time range
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%" data-oid="8out7c9">
            {chartType === "line" && (
              <LineChart data={chartData} data-oid="at_9io:">
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#374151"
                  opacity={0.3}
                  data-oid="cdjobp3"
                />

                <XAxis
                  dataKey="dateFormatted"
                  tick={{ fontSize: 12 }}
                  stroke="#6b7280"
                  data-oid="m99_mxi"
                />

                <YAxis
                  tick={{ fontSize: 12 }}
                  stroke="#6b7280"
                  data-oid="v73rkrl"
                />

                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1f2937",
                    border: "1px solid #374151",
                    borderRadius: "8px",
                  }}
                  labelStyle={{ color: "#f9fafb" }}
                  data-oid=".q-twxd"
                />

                <Legend data-oid="jzf5m68" />

                <Line
                  type="monotone"
                  dataKey="jobsCompleted"
                  stroke="#10b981"
                  strokeWidth={2}
                  name="Completed Jobs"
                  dot={{ fill: "#10b981", strokeWidth: 2, r: 4 }}
                  data-oid="tah4-kl"
                />

                <Line
                  type="monotone"
                  dataKey="jobsFailed"
                  stroke="#ef4444"
                  strokeWidth={2}
                  name="Failed Jobs"
                  dot={{ fill: "#ef4444", strokeWidth: 2, r: 4 }}
                  data-oid="koo:dlq"
                />

                <Line
                  type="monotone"
                  dataKey="successRate"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name="Success Rate (%)"
                  dot={{ fill: "#3b82f6", strokeWidth: 2, r: 4 }}
                  data-oid="9m15plz"
                />
              </LineChart>
            )}

            {chartType === "bar" && (
              <BarChart data={chartData} data-oid="ciyudc4">
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#374151"
                  opacity={0.3}
                  data-oid="dk9mo8l"
                />

                <XAxis
                  dataKey="dateFormatted"
                  tick={{ fontSize: 12 }}
                  stroke="#6b7280"
                  data-oid="m.a_d1u"
                />

                <YAxis
                  tick={{ fontSize: 12 }}
                  stroke="#6b7280"
                  data-oid="y2b-gu."
                />

                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1f2937",
                    border: "1px solid #374151",
                    borderRadius: "8px",
                  }}
                  data-oid="s.uc.t7"
                />

                <Legend data-oid="j667v2l" />

                <Bar
                  dataKey="jobsCompleted"
                  fill="#10b981"
                  name="Completed"
                  data-oid="syaah:t"
                />

                <Bar
                  dataKey="jobsFailed"
                  fill="#ef4444"
                  name="Failed"
                  data-oid="69xptuv"
                />
              </BarChart>
            )}

            {chartType === "pie" && (
              <PieChart data-oid="isjqti4">
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={120}
                  paddingAngle={5}
                  dataKey="value"
                  label={(entry) => `${entry.name}: ${entry.value}`}
                  data-oid="9-tnfq5"
                >
                  {pieData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.color}
                      data-oid="g4ijqy-"
                    />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1f2937",
                    border: "1px solid #374151",
                    borderRadius: "8px",
                  }}
                  data-oid="-.uezv:"
                />

                <Legend data-oid="e7kojcs" />
              </PieChart>
            )}
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
