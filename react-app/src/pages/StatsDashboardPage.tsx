import { useState } from "react";
import { BarChart3, RefreshCw, Download, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { SystemHealthCard } from "@/components/dashboard/SystemHealthCard";
import { ProcessingMetricsChart } from "@/components/dashboard/ProcessingMetricsChart";
import { ModelPerformanceChart } from "@/components/dashboard/ModelPerformanceChart";
import { DatasetStatsTable } from "@/components/dashboard/DatasetStatsTable";
import { TimeRangeSelector } from "@/components/dashboard/TimeRangeSelector";
import { useDashboardSummary, useDashboardRefresh } from "@/hooks/useStats";
import type { StatsQuery } from "@/types/stats";

export function StatsDashboardPage() {
  const [query, setQuery] = useState<StatsQuery>({
    time_range: "24h",
  });

  const { data: dashboardData, isLoading, error } = useDashboardSummary(query);
  const { refreshAll, getLastUpdated } = useDashboardRefresh();

  const handleViewDataset = (datasetId: string) => {
    console.log("Navigate to dataset:", datasetId);
    // TODO: Navigate to dataset detail page
  };

  const handleProcessDataset = (datasetId: string) => {
    console.log("Start processing dataset:", datasetId);
    // TODO: Navigate to jobs page with preselected dataset
  };

  const handleExportData = () => {
    if (!dashboardData) return;

    const data = {
      ...dashboardData,
      exported_at: new Date().toISOString(),
      query_parameters: query,
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `modomo-dashboard-${new Date().toISOString().split("T")[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8" data-oid="i3rxpga">
        <div
          className="flex items-center justify-center min-h-[400px]"
          data-oid=":bdx:7i"
        >
          {error && (
            <div className="text-center py-8" data-oid="a5v608.">
              <AlertCircle
                className="h-12 w-12 text-destructive mx-auto mb-4"
                data-oid="b1z0b6d"
              />
              <p
                className="text-lg font-medium text-destructive mb-2"
                data-oid="xjk6oar"
              >
                Failed to load statistics
              </p>
              <p className="text-muted-foreground" data-oid="qzxmhpz">
                {error?.message || "An error occurred while loading statistics"}
              </p>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 space-y-8" data-oid="u021ug_">
      {/* Header */}
      <div className="flex items-center justify-between" data-oid="m2vbbxg">
        <div data-oid="kw.943k">
          <h1 className="text-3xl font-bold tracking-tight" data-oid="kb8ql8-">
            Analytics Dashboard
          </h1>
          <p className="text-muted-foreground mt-1" data-oid="jwqx6dt">
            System performance and dataset processing insights
          </p>
        </div>

        <div className="flex items-center space-x-2" data-oid=".rr8e62">
          <Button variant="outline" onClick={refreshAll} data-oid="y4sp.x.">
            <RefreshCw className="h-4 w-4 mr-2" data-oid="1bbi2kb" />
            Refresh
          </Button>
          <Button
            variant="outline"
            onClick={handleExportData}
            disabled={!dashboardData}
            data-oid="szh8.o1"
          >
            <Download className="h-4 w-4 mr-2" data-oid="-i3g2il" />
            Export
          </Button>
        </div>
      </div>

      {/* Time Range Controls */}
      <div className="flex items-center justify-between" data-oid="o2uf82o">
        <TimeRangeSelector
          value={query}
          onChange={setQuery}
          data-oid="p4wutcz"
        />

        <div className="text-xs text-muted-foreground" data-oid="ho_cj7b">
          Last updated: {getLastUpdated()}
        </div>
      </div>

      {/* Dashboard Grid */}
      {isLoading ? (
        <div className="space-y-8" data-oid="ekfxdif">
          <div
            className="h-96 bg-muted animate-pulse rounded-lg"
            data-oid="6q9qwvr"
          />
          <div
            className="grid grid-cols-1 lg:grid-cols-2 gap-8"
            data-oid="68cua8w"
          >
            <div
              className="h-96 bg-muted animate-pulse rounded-lg"
              data-oid="3xy05p7"
            />
            <div
              className="h-96 bg-muted animate-pulse rounded-lg"
              data-oid="uqz-l45"
            />
          </div>
          <div
            className="h-96 bg-muted animate-pulse rounded-lg"
            data-oid="nj9he-z"
          />
        </div>
      ) : (
        <>
          {/* Top Row - System Health */}
          <div
            className="grid grid-cols-1 lg:grid-cols-3 gap-8"
            data-oid="lkwelbv"
          >
            <div className="lg:col-span-1" data-oid="2m8-7vj">
              <SystemHealthCard query={query} data-oid="kl.9-6h" />
            </div>

            <div className="lg:col-span-2" data-oid="inm.yjv">
              <ProcessingMetricsChart query={query} data-oid="j8lrjsr" />
            </div>
          </div>

          {/* Middle Row - Model Performance */}
          <ModelPerformanceChart query={query} data-oid="trbcn6m" />

          {/* Bottom Row - Dataset Statistics */}
          <DatasetStatsTable
            query={query}
            onViewDataset={handleViewDataset}
            onProcessDataset={handleProcessDataset}
            data-oid="ucz6_1t"
          />

          {/* Footer Summary */}
          {dashboardData && (
            <div className="bg-muted/50 rounded-lg p-6" data-oid="lwed5u1">
              <div
                className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center"
                data-oid="wk33vvy"
              >
                <div data-oid="_0j_yrj">
                  <div
                    className="text-2xl font-bold text-blue-600"
                    data-oid="pd.9vgl"
                  >
                    {dashboardData.total_datasets || 0}
                  </div>
                  <div
                    className="text-sm text-muted-foreground"
                    data-oid="x7a5:2a"
                  >
                    Active Datasets
                  </div>
                </div>

                <div data-oid="2qs0isd">
                  <div
                    className="text-2xl font-bold text-green-600"
                    data-oid="9e61o6j"
                  >
                    {(dashboardData.total_scenes || 0).toLocaleString()}
                  </div>
                  <div
                    className="text-sm text-muted-foreground"
                    data-oid="-v6yugy"
                  >
                    Total Scenes
                  </div>
                </div>

                <div data-oid="ns6pdto">
                  <div
                    className="text-2xl font-bold text-purple-600"
                    data-oid="1slxefh"
                  >
                    {(dashboardData.total_objects || 0).toLocaleString()}
                  </div>
                  <div
                    className="text-sm text-muted-foreground"
                    data-oid="_wo7b:7"
                  >
                    Total Objects
                  </div>
                </div>

                <div data-oid="ca5bzrk">
                  <div
                    className="text-2xl font-bold text-orange-600"
                    data-oid="6nhvwig"
                  >
                    {dashboardData.system_health_score || 0}%
                  </div>
                  <div
                    className="text-sm text-muted-foreground"
                    data-oid="zj2zoz8"
                  >
                    System Health
                  </div>
                </div>
              </div>

              <div
                className="text-center mt-4 text-xs text-muted-foreground"
                data-oid="r03dsf5"
              >
                Dashboard generated at {new Date().toLocaleString()}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
