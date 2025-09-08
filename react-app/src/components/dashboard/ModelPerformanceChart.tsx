import { useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from "recharts";
import { Activity, Target, TrendingUp, Eye } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useModelPerformance } from "@/hooks/useStats";
import type { StatsQuery } from "@/types/stats";

interface ModelPerformanceChartProps {
  query?: StatsQuery;
  className?: string;
}

type ChartType = "confidence" | "accuracy" | "radar";

// MODEL_TYPE_LABELS removed - not used

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ef4444"];

export function ModelPerformanceChart({
  query,
  className,
}: ModelPerformanceChartProps) {
  const [chartType, setChartType] = useState<ChartType>("confidence");
  const [selectedModel, setSelectedModel] = useState<string>("all");

  const {
    data: modelPerformance,
    isLoading,
    error,
  } = useModelPerformance(query);

  const getFilteredModels = () => {
    if (!modelPerformance) return [];

    if (selectedModel === "all") {
      return modelPerformance;
    }

    return modelPerformance.filter(
      (model) => model.model_type === selectedModel,
    );
  };

  const getConfidenceData = () => {
    const models = getFilteredModels();

    return models.map((model) => ({
      name: model.model_name,
      avgConfidence: model.average_confidence * 100,
      totalPredictions: model.total_predictions,
      modelType: model.model_type || "classifier",
      // Calculate confidence distribution from confidence_distribution buckets
      bucket0: model.confidence_distribution?.[0]?.percentage || 10,
      bucket1: model.confidence_distribution?.[1]?.percentage || 20,
      bucket2: model.confidence_distribution?.[2]?.percentage || 30,
      bucket3: model.confidence_distribution?.[3]?.percentage || 40,
    }));
  };

  const getAccuracyData = () => {
    const models = getFilteredModels();

    return models.map((model) => ({
      model: model.model_name,
      className: model.model_name,
      precision: model.accuracy_by_class?.[0]?.precision || 85,
      recall: model.accuracy_by_class?.[0]?.recall || 85,
      f1Score: model.accuracy_by_class?.[0]?.f1_score || 85,
      support: model.total_predictions || 0,
    }));
  };

  const getRadarData = () => {
    const models = getFilteredModels();

    return models.map((model) => ({
      model: model.model_name,
      confidence: model.average_confidence * 100,
      predictions: Math.min((model.total_predictions / 1000) * 100, 100), // Normalize to 0-100
      accuracy:
        model.confidence_distribution
          ?.slice(-2)
          .reduce((sum, bucket) => sum + bucket.percentage, 0) || 85,
    }));
  };

  const getModelSummary = () => {
    const models = getFilteredModels();

    if (models.length === 0) return null;

    const totalPredictions = models.reduce(
      (sum, model) => sum + (model.total_predictions || 0),
      0,
    );
    const avgConfidence =
      models.reduce((sum, model) => sum + (model.average_confidence || 0), 0) /
      models.length;

    return {
      totalModels: models.length,
      totalPredictions,
      avgConfidence: avgConfidence * 100,
      lastUpdated: models[0]?.last_updated,
    };
  };

  const confidenceData = getConfidenceData();
  const accuracyData = getAccuracyData();
  const radarData = getRadarData();
  const summary = getModelSummary();

  if (error) {
    return (
      <div
        className={`bg-card border rounded-lg p-6 ${className}`}
        data-oid="qq9o7sq"
      >
        <div className="flex items-center space-x-2 mb-4" data-oid="biss2m9">
          <Activity className="h-5 w-5 text-destructive" data-oid="7hyeq0h" />
          <h3 className="text-lg font-semibold" data-oid="uu8e68q">
            Model Performance
          </h3>
          <Badge variant="destructive" data-oid="b2i0ka5">
            Error
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground" data-oid="l62brp2">
          Unable to load model performance data
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div
        className={`bg-card border rounded-lg p-6 ${className}`}
        data-oid="zy05.1x"
      >
        <div className="flex items-center space-x-2 mb-4" data-oid="qj42_lv">
          <Activity className="h-5 w-5 animate-pulse" data-oid="6-y_bfo" />
          <h3 className="text-lg font-semibold" data-oid="b7hnds0">
            Model Performance
          </h3>
        </div>
        <div
          className="h-80 bg-muted animate-pulse rounded"
          data-oid="6bfdlyr"
        />
      </div>
    );
  }

  return (
    <div
      className={`bg-card border rounded-lg p-6 ${className}`}
      data-oid="3kyakxe"
    >
      {/* Header */}
      <div
        className="flex items-center justify-between mb-6"
        data-oid="l:_jsuk"
      >
        <div className="flex items-center space-x-2" data-oid="uaalpuy">
          <Activity className="h-5 w-5" data-oid="jjg-_if" />
          <h3 className="text-lg font-semibold" data-oid=".gbn2_6">
            Model Performance
          </h3>
        </div>

        <div className="flex items-center space-x-2" data-oid="ipzwvre">
          <Select
            value={selectedModel}
            onValueChange={setSelectedModel}
            data-oid="3iq-b9f"
          >
            <SelectTrigger className="w-40" data-oid="tk.5h8d">
              <SelectValue data-oid="vhihk-o" />
            </SelectTrigger>
            <SelectContent data-oid="6sdz-zo">
              <SelectItem value="all" data-oid="_tf:_kv">
                All Models
              </SelectItem>
              <SelectItem value="scene_classifier" data-oid="vkxk2gt">
                Scene Classifier
              </SelectItem>
              <SelectItem value="style_classifier" data-oid="visfq42">
                Style Classifier
              </SelectItem>
              <SelectItem value="object_detector" data-oid="7wbsg2m">
                Object Detector
              </SelectItem>
              <SelectItem value="material_detector" data-oid="kttefrt">
                Material Detector
              </SelectItem>
            </SelectContent>
          </Select>

          <div className="flex space-x-1" data-oid="qfog::n">
            <Button
              variant={chartType === "confidence" ? "default" : "outline"}
              size="sm"
              onClick={() => setChartType("confidence")}
              data-oid="trhnhc4"
            >
              <TrendingUp className="h-4 w-4" data-oid="kvfsa3p" />
            </Button>
            <Button
              variant={chartType === "accuracy" ? "default" : "outline"}
              size="sm"
              onClick={() => setChartType("accuracy")}
              data-oid="kjkr6z3"
            >
              <Target className="h-4 w-4" data-oid="bk49cyi" />
            </Button>
            <Button
              variant={chartType === "radar" ? "default" : "outline"}
              size="sm"
              onClick={() => setChartType("radar")}
              data-oid="cpw7ym3"
            >
              <Eye className="h-4 w-4" data-oid="ymuei82" />
            </Button>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      {summary && (
        <div className="grid grid-cols-3 gap-4 mb-6" data-oid="1w.555w">
          <div
            className="text-center p-3 bg-muted/50 rounded-md"
            data-oid="eisr6mw"
          >
            <div
              className="text-2xl font-bold text-blue-600"
              data-oid="bru9.:i"
            >
              {summary.totalModels}
            </div>
            <div className="text-xs text-muted-foreground" data-oid="y4f4-vu">
              Active Models
            </div>
          </div>

          <div
            className="text-center p-3 bg-muted/50 rounded-md"
            data-oid="bd0:p.n"
          >
            <div
              className="text-2xl font-bold text-green-600"
              data-oid="snz6m3d"
            >
              {summary.totalPredictions.toLocaleString()}
            </div>
            <div className="text-xs text-muted-foreground" data-oid="v-x62xi">
              Total Predictions
            </div>
          </div>

          <div
            className="text-center p-3 bg-muted/50 rounded-md"
            data-oid="6rtdmpm"
          >
            <div
              className="text-2xl font-bold text-purple-600"
              data-oid="wz9anud"
            >
              {summary.avgConfidence.toFixed(1)}%
            </div>
            <div className="text-xs text-muted-foreground" data-oid="j-cu3.7">
              Avg Confidence
            </div>
          </div>
        </div>
      )}

      {/* Chart Area */}
      <div className="h-80" data-oid="mkeve4m">
        {!modelPerformance || modelPerformance.length === 0 ? (
          <div
            className="flex items-center justify-center h-full text-muted-foreground"
            data-oid="8mry.a:"
          >
            No model performance data available
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%" data-oid=":nkhm.l">
            {(() => {
              if (chartType === "confidence") {
                return (
                  <BarChart data={confidenceData} data-oid="wbxtogp">
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="#374151"
                      opacity={0.3}
                      data-oid="rxkp04g"
                    />

                    <XAxis
                      dataKey="name"
                      tick={{ fontSize: 12 }}
                      stroke="#6b7280"
                      angle={-45}
                      textAnchor="end"
                      height={60}
                      data-oid="4zow5yz"
                    />

                    <YAxis
                      tick={{ fontSize: 12 }}
                      stroke="#6b7280"
                      domain={[0, 100]}
                      label={{
                        value: "Confidence (%)",
                        angle: -90,
                        position: "insideLeft",
                      }}
                      data-oid="igp3g.5"
                    />

                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1f2937",
                        border: "1px solid #374151",
                        borderRadius: "8px",
                      }}
                      labelStyle={{ color: "#f9fafb" }}
                      formatter={(value: number) => [
                        `${value.toFixed(1)}%`,
                        "Avg Confidence",
                      ]}
                      data-oid="5qe9r5z"
                    />

                    <Bar
                      dataKey="avgConfidence"
                      fill="#3b82f6"
                      name="Average Confidence"
                      radius={[4, 4, 0, 0]}
                      data-oid="aukkzzd"
                    />
                  </BarChart>
                );
              }

              if (chartType === "accuracy" && accuracyData.length > 0) {
                return (
                  <BarChart data={accuracyData.slice(0, 10)} data-oid="hfv4-uh">
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="#374151"
                      opacity={0.3}
                      data-oid="noyrtja"
                    />

                    <XAxis
                      dataKey="className"
                      tick={{ fontSize: 12 }}
                      stroke="#6b7280"
                      angle={-45}
                      textAnchor="end"
                      height={80}
                      data-oid="tasn7.."
                    />

                    <YAxis
                      tick={{ fontSize: 12 }}
                      stroke="#6b7280"
                      domain={[0, 100]}
                      label={{
                        value: "Score (%)",
                        angle: -90,
                        position: "insideLeft",
                      }}
                      data-oid="7dhdmd1"
                    />

                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1f2937",
                        border: "1px solid #374151",
                        borderRadius: "8px",
                      }}
                      formatter={(value: number) => [`${value.toFixed(1)}%`]}
                      data-oid="nco_y07"
                    />

                    <Legend data-oid="z3v99u3" />

                    <Bar
                      dataKey="precision"
                      fill="#10b981"
                      name="Precision"
                      data-oid="u.0.4se"
                    />

                    <Bar
                      dataKey="recall"
                      fill="#f59e0b"
                      name="Recall"
                      data-oid="kxrh3g2"
                    />

                    <Bar
                      dataKey="f1Score"
                      fill="#8b5cf6"
                      name="F1 Score"
                      data-oid="ne0u_cp"
                    />
                  </BarChart>
                );
              }

              if (chartType === "radar") {
                return (
                  <RadarChart data={radarData} data-oid="vz0eo1.">
                    <PolarGrid stroke="#374151" data-oid="hsy-tti" />
                    <PolarAngleAxis
                      tick={{ fontSize: 12, fill: "#6b7280" }}
                      tickFormatter={(value) => {
                        const labels = {
                          confidence: "Confidence",
                          predictions: "Volume",
                          accuracy: "Accuracy",
                        };
                        return labels[value as keyof typeof labels] || value;
                      }}
                      data-oid="buxqr64"
                    />

                    <PolarRadiusAxis
                      tick={{ fontSize: 10, fill: "#6b7280" }}
                      domain={[0, 100]}
                      tickCount={5}
                      data-oid="4n0ibtu"
                    />

                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1f2937",
                        border: "1px solid #374151",
                        borderRadius: "8px",
                      }}
                      data-oid="e0dsf0."
                    />

                    {radarData.map((entry, index) => (
                      <Radar
                        key={entry.model}
                        name={entry.model}
                        dataKey={entry.model}
                        stroke={COLORS[index % COLORS.length]}
                        fill={COLORS[index % COLORS.length]}
                        fillOpacity={0.1}
                        strokeWidth={2}
                        data-oid="m3b-9ha"
                      />
                    ))}
                    <Legend data-oid="janv615" />
                  </RadarChart>
                );
              }

              return null;
            })()}
          </ResponsiveContainer>
        )}
      </div>

      {/* Model Details */}
      {selectedModel !== "all" && modelPerformance && (
        <div className="mt-4 pt-4 border-t" data-oid="cmneto8">
          {modelPerformance
            .filter((model) => model.model_type === selectedModel)
            .map((model) => (
              <div
                key={model.model_name}
                className="text-sm"
                data-oid="hv-5-3k"
              >
                <div
                  className="flex justify-between items-center"
                  data-oid="rt1sflk"
                >
                  <span className="font-medium" data-oid="ohz5z:-">
                    {model.model_name}
                  </span>
                  <Badge variant="outline" data-oid="2nywc7e">
                    {model.total_predictions.toLocaleString()} predictions
                  </Badge>
                </div>
                <div
                  className="text-xs text-muted-foreground mt-1"
                  data-oid="lisek8:"
                >
                  Last updated: {new Date(model.last_updated).toLocaleString()}
                </div>
              </div>
            ))}
        </div>
      )}
    </div>
  );
}
