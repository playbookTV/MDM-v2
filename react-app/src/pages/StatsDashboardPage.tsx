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
      <div className="container mx-auto px-4 py-8" data-oid=".nchtqx">
        <div
          className="flex items-center justify-center min-h-[400px]"
          data-oid="u0lxgq6"
        >
          {error && (
            <div className="text-center py-8" data-oid="k5iji9c">
              <AlertCircle
                className="h-12 w-12 text-destructive mx-auto mb-4"
                data-oid="5kmv_ex"
              />

              <p
                className="text-lg font-medium text-destructive mb-2"
                data-oid="_6cc1wp"
              >
                Failed to load statistics
              </p>
              <p className="text-muted-foreground" data-oid="o2x:axw">
                {(error as Error)?.message || "An error occurred while loading statistics"}
              </p>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8 space-y-8" data-oid="07jo34k">
      {/* Header */}
      <div className="flex items-center justify-between" data-oid=".3ylrw5">
        <div data-oid="uct7gda">
          <h1 className="text-3xl font-bold tracking-tight" data-oid="d1aeizs">
            Analytics Dashboard
          </h1>
          <p className="text-muted-foreground mt-1" data-oid="0_un8l_">
            System performance and dataset processing insights
          </p>
        </div>

        <div className="flex items-center space-x-2" data-oid="p8nr3po">
          <Button variant="outline" onClick={refreshAll} data-oid="caqeojj">
            <RefreshCw className="h-4 w-4 mr-2" data-oid="cewjcqs" />
            Refresh
          </Button>
          <Button
            variant="outline"
            onClick={handleExportData}
            disabled={!dashboardData}
            data-oid="n49k-s7"
          >
            <Download className="h-4 w-4 mr-2" data-oid="dh5::qm" />
            Export
          </Button>
        </div>
      </div>

      {/* Time Range Controls */}
      <div className="flex items-center justify-between" data-oid="dvl7ct2">
        <TimeRangeSelector
          value={query}
          onChange={setQuery}
          data-oid="jquqtdv"
        />

        <div className="text-xs text-muted-foreground" data-oid="vbzjs1n">
          Last updated: {getLastUpdated()}
        </div>
      </div>

      {/* Dashboard Grid */}
      {isLoading ? (
        <div className="space-y-8" data-oid="q6agwk4">
          <div
            className="h-96 bg-muted animate-pulse rounded-lg"
            data-oid="6zw.nwx"
          />

          <div
            className="grid grid-cols-1 lg:grid-cols-2 gap-8"
            data-oid="abpnnsa"
          >
            <div
              className="h-96 bg-muted animate-pulse rounded-lg"
              data-oid="-o.ayod"
            />

            <div
              className="h-96 bg-muted animate-pulse rounded-lg"
              data-oid="khc.6.4"
            />
          </div>
          <div
            className="h-96 bg-muted animate-pulse rounded-lg"
            data-oid="8k-uwfc"
          />
        </div>
      ) : (
        <>
          {/* Top Row - System Health */}
          <div
            className="grid grid-cols-1 lg:grid-cols-3 gap-8"
            data-oid="6x83t96"
          >
            <div className="lg:col-span-1" data-oid="-jq:7z.">
              <SystemHealthCard query={query} data-oid="s0cnnrf" />
            </div>

            <div className="lg:col-span-2" data-oid="9lgyr21">
              <ProcessingMetricsChart query={query} data-oid="3nbrxl7" />
            </div>
          </div>

          {/* Middle Row - Model Performance */}
          <ModelPerformanceChart query={query} data-oid="fz6tc34" />

          {/* Bottom Row - Dataset Statistics */}
          <DatasetStatsTable
            query={query}
            onViewDataset={handleViewDataset}
            onProcessDataset={handleProcessDataset}
            data-oid="azan556"
          />

          {/* Footer Summary */}
          {dashboardData && (
            <div className="bg-muted/50 rounded-lg p-6" data-oid="fkh1.8m">
              <div
                className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center"
                data-oid="7mg-wig"
              >
                <div data-oid="0jp_0st">
                  <div
                    className="text-2xl font-bold text-blue-600"
                    data-oid="yg46p7i"
                  >
                    {dashboardData.total_datasets || 0}
                  </div>
                  <div
                    className="text-sm text-muted-foreground"
                    data-oid="o1qt9if"
                  >
                    Active Datasets
                  </div>
                </div>

                <div data-oid="gp2wxhe">
                  <div
                    className="text-2xl font-bold text-green-600"
                    data-oid="zls09se"
                  >
                    {(dashboardData.total_scenes || 0).toLocaleString()}
                  </div>
                  <div
                    className="text-sm text-muted-foreground"
                    data-oid="2ocjoce"
                  >
                    Total Scenes
                  </div>
                </div>

                <div data-oid="htwbc8.">
                  <div
                    className="text-2xl font-bold text-purple-600"
                    data-oid="bmiw0r5"
                  >
                    {(dashboardData.total_objects || 0).toLocaleString()}
                  </div>
                  <div
                    className="text-sm text-muted-foreground"
                    data-oid="3u3zuqj"
                  >
                    Total Objects
                  </div>
                </div>

                <div data-oid="z8maks_">
                  <div
                    className="text-2xl font-bold text-orange-600"
                    data-oid="cs:jx0t"
                  >
                    {dashboardData.system_health_score || 0}%
                  </div>
                  <div
                    className="text-sm text-muted-foreground"
                    data-oid="h8k3il1"
                  >
                    System Health
                  </div>
                </div>
              </div>

              <div
                className="text-center mt-4 text-xs text-muted-foreground"
                data-oid="tuyhc8a"
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
