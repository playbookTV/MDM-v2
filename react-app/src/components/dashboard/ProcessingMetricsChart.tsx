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
        data-oid="ctacjaj"
      >
        <div className="flex items-center space-x-2 mb-4" data-oid="h6o_amt">
          <Activity className="h-5 w-5 text-destructive" data-oid="u6dsw:x" />
          <h3 className="text-lg font-semibold" data-oid="57nhn46">
            Processing Metrics
          </h3>
          <Badge variant="destructive" data-oid="pki68qb">
            Error
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground" data-oid="i4z7jqv">
          Unable to load processing metrics
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div
        className={`bg-card border rounded-lg p-6 ${className}`}
        data-oid="1rswyt."
      >
        <div className="flex items-center space-x-2 mb-4" data-oid="x3._266">
          <Activity className="h-5 w-5 animate-pulse" data-oid="y-7ytzv" />
          <h3 className="text-lg font-semibold" data-oid="rgec-8_">
            Processing Metrics
          </h3>
        </div>
        <div
          className="h-80 bg-muted animate-pulse rounded"
          data-oid="pvrc16p"
        />
      </div>
    );
  }

  return (
    <div
      className={`bg-card border rounded-lg p-6 ${className}`}
      data-oid="lkrl1fv"
    >
      {/* Header */}
      <div
        className="flex items-center justify-between mb-6"
        data-oid="oskqb6n"
      >
        <div className="flex items-center space-x-2" data-oid="a83b-30">
          <Activity className="h-5 w-5" data-oid="eocatka" />
          <h3 className="text-lg font-semibold" data-oid="mpl8wnk">
            Processing Metrics
          </h3>
        </div>

        <div className="flex items-center space-x-2" data-oid="fj-8z5o">
          <Button
            variant={chartType === "line" ? "default" : "outline"}
            size="sm"
            onClick={() => setChartType("line")}
            data-oid="bg1ttr_"
          >
            <TrendingUp className="h-4 w-4" data-oid="t7uuaj7" />
          </Button>
          <Button
            variant={chartType === "bar" ? "default" : "outline"}
            size="sm"
            onClick={() => setChartType("bar")}
            data-oid="n6o9_7e"
          >
            <BarChart3 className="h-4 w-4" data-oid="stz6-:5" />
          </Button>
          <Button
            variant={chartType === "pie" ? "default" : "outline"}
            size="sm"
            onClick={() => setChartType("pie")}
            data-oid="ug00myy"
          >
            <PieChartIcon className="h-4 w-4" data-oid="uu_4aeh" />
          </Button>
        </div>
      </div>

      {/* Summary Stats */}
      {summaryStats && (
        <div
          className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6"
          data-oid="tv5rp-9"
        >
          <div
            className="text-center p-3 bg-muted/50 rounded-md"
            data-oid="45x4:xz"
          >
            <div
              className="text-2xl font-bold text-green-600"
              data-oid="w7k33fm"
            >
              {summaryStats.totalCompleted.toLocaleString()}
            </div>
            <div className="text-xs text-muted-foreground" data-oid="j7ado7v">
              Jobs Completed
            </div>
          </div>

          <div
            className="text-center p-3 bg-muted/50 rounded-md"
            data-oid=".lgo36v"
          >
            <div className="text-2xl font-bold text-red-600" data-oid="af4.h96">
              {summaryStats.totalFailed.toLocaleString()}
            </div>
            <div className="text-xs text-muted-foreground" data-oid="drd-eee">
              Jobs Failed
            </div>
          </div>

          <div
            className="text-center p-3 bg-muted/50 rounded-md"
            data-oid="46j_qq2"
          >
            <div
              className="text-2xl font-bold text-blue-600"
              data-oid="pmz8ygc"
            >
              {summaryStats.avgSuccessRate.toFixed(1)}%
            </div>
            <div className="text-xs text-muted-foreground" data-oid="5zeebqw">
              Avg Success Rate
            </div>
          </div>

          <div
            className="text-center p-3 bg-muted/50 rounded-md"
            data-oid="r801k2o"
          >
            <div
              className="text-2xl font-bold text-purple-600"
              data-oid="ur-colg"
            >
              {summaryStats.avgProcessingRate.toFixed(1)}
            </div>
            <div className="text-xs text-muted-foreground" data-oid="xdy.caj">
              Scenes/min
            </div>
          </div>
        </div>
      )}

      {/* Chart Area */}
      <div className="h-80" data-oid="izm8gw_">
        {chartData.length === 0 ? (
          <div
            className="flex items-center justify-center h-full text-muted-foreground"
            data-oid="80jlc4q"
          >
            No data available for the selected time range
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%" data-oid="3hba9an">
            {chartType === "line" && (
              <LineChart data={chartData} data-oid="kr_m2nk">
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#374151"
                  opacity={0.3}
                  data-oid="48.24:4"
                />
                <XAxis
                  dataKey="dateFormatted"
                  tick={{ fontSize: 12 }}
                  stroke="#6b7280"
                  data-oid="hbzqtgj"
                />

                <YAxis
                  tick={{ fontSize: 12 }}
                  stroke="#6b7280"
                  data-oid=".:kth9s"
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1f2937",
                    border: "1px solid #374151",
                    borderRadius: "8px",
                  }}
                  labelStyle={{ color: "#f9fafb" }}
                  data-oid="5s_m:eb"
                />

                <Legend data-oid="2c57kew" />

                <Line
                  type="monotone"
                  dataKey="jobsCompleted"
                  stroke="#10b981"
                  strokeWidth={2}
                  name="Completed Jobs"
                  dot={{ fill: "#10b981", strokeWidth: 2, r: 4 }}
                  data-oid="9tqfr.e"
                />

                <Line
                  type="monotone"
                  dataKey="jobsFailed"
                  stroke="#ef4444"
                  strokeWidth={2}
                  name="Failed Jobs"
                  dot={{ fill: "#ef4444", strokeWidth: 2, r: 4 }}
                  data-oid="2cfj2:7"
                />

                <Line
                  type="monotone"
                  dataKey="successRate"
                  stroke="#3b82f6"
                  strokeWidth={2}
                  name="Success Rate (%)"
                  dot={{ fill: "#3b82f6", strokeWidth: 2, r: 4 }}
                  data-oid="ff.x3s3"
                />
              </LineChart>
            )}

            {chartType === "bar" && (
              <BarChart data={chartData} data-oid="7gmmpc7">
                <CartesianGrid
                  strokeDasharray="3 3"
                  stroke="#374151"
                  opacity={0.3}
                  data-oid="zvpxnsi"
                />
                <XAxis
                  dataKey="dateFormatted"
                  tick={{ fontSize: 12 }}
                  stroke="#6b7280"
                  data-oid="-7sx2ow"
                />

                <YAxis
                  tick={{ fontSize: 12 }}
                  stroke="#6b7280"
                  data-oid="eex_2ve"
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1f2937",
                    border: "1px solid #374151",
                    borderRadius: "8px",
                  }}
                  data-oid="_up96su"
                />

                <Legend data-oid=".q0-8p0" />

                <Bar
                  dataKey="jobsCompleted"
                  fill="#10b981"
                  name="Completed"
                  data-oid="7km4_p_"
                />
                <Bar
                  dataKey="jobsFailed"
                  fill="#ef4444"
                  name="Failed"
                  data-oid="ync490f"
                />
              </BarChart>
            )}

            {chartType === "pie" && (
              <PieChart data-oid="rxnv99.">
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={120}
                  paddingAngle={5}
                  dataKey="value"
                  label={(entry) => `${entry.name}: ${entry.value}`}
                  data-oid="ww9m41z"
                >
                  {pieData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.color}
                      data-oid="w3t1cq_"
                    />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    backgroundColor: "#1f2937",
                    border: "1px solid #374151",
                    borderRadius: "8px",
                  }}
                  data-oid="6qz7yaz"
                />

                <Legend data-oid="zqcgggo" />
              </PieChart>
            )}
          </ResponsiveContainer>
        )}
      </div>
    </div>
  );
}
