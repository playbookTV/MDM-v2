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
        data-oid="jb_6cx7"
      >
        <div className="flex items-center space-x-2 mb-4" data-oid="04v56pl">
          <Activity className="h-5 w-5 text-destructive" data-oid="5eht_ld" />
          <h3 className="text-lg font-semibold" data-oid="vwyom2g">
            Model Performance
          </h3>
          <Badge variant="destructive" data-oid="2i.kdtd">
            Error
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground" data-oid="82rflrz">
          Unable to load model performance data
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div
        className={`bg-card border rounded-lg p-6 ${className}`}
        data-oid="5q5.ete"
      >
        <div className="flex items-center space-x-2 mb-4" data-oid="nz8sgrr">
          <Activity className="h-5 w-5 animate-pulse" data-oid="69lkxoa" />
          <h3 className="text-lg font-semibold" data-oid="mu.h_d:">
            Model Performance
          </h3>
        </div>
        <div
          className="h-80 bg-muted animate-pulse rounded"
          data-oid="h320_fu"
        />
      </div>
    );
  }

  return (
    <div
      className={`bg-card border rounded-lg p-6 ${className}`}
      data-oid="t0b60al"
    >
      {/* Header */}
      <div
        className="flex items-center justify-between mb-6"
        data-oid="5avv6:q"
      >
        <div className="flex items-center space-x-2" data-oid="6_ixnk3">
          <Activity className="h-5 w-5" data-oid="djo5:86" />
          <h3 className="text-lg font-semibold" data-oid="8tsruo_">
            Model Performance
          </h3>
        </div>

        <div className="flex items-center space-x-2" data-oid="dda4ym5">
          <Select
            value={selectedModel}
            onValueChange={setSelectedModel}
            data-oid="si.eyc4"
          >
            <SelectTrigger className="w-40" data-oid="0eikwcw">
              <SelectValue data-oid="357wdgt" />
            </SelectTrigger>
            <SelectContent data-oid="d3i_7bb">
              <SelectItem value="all" data-oid="tuw9drm">
                All Models
              </SelectItem>
              <SelectItem value="scene_classifier" data-oid="f79deo7">
                Scene Classifier
              </SelectItem>
              <SelectItem value="style_classifier" data-oid="zhscg2p">
                Style Classifier
              </SelectItem>
              <SelectItem value="object_detector" data-oid="oqjq:d3">
                Object Detector
              </SelectItem>
              <SelectItem value="material_detector" data-oid=".w9ov33">
                Material Detector
              </SelectItem>
            </SelectContent>
          </Select>

          <div className="flex space-x-1" data-oid="2t4lykt">
            <Button
              variant={chartType === "confidence" ? "default" : "outline"}
              size="sm"
              onClick={() => setChartType("confidence")}
              data-oid="33:-g8b"
            >
              <TrendingUp className="h-4 w-4" data-oid="q4p58st" />
            </Button>
            <Button
              variant={chartType === "accuracy" ? "default" : "outline"}
              size="sm"
              onClick={() => setChartType("accuracy")}
              data-oid=".a5j8x2"
            >
              <Target className="h-4 w-4" data-oid="e3nxzej" />
            </Button>
            <Button
              variant={chartType === "radar" ? "default" : "outline"}
              size="sm"
              onClick={() => setChartType("radar")}
              data-oid="lpt9-zn"
            >
              <Eye className="h-4 w-4" data-oid="u.557wj" />
            </Button>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      {summary && (
        <div className="grid grid-cols-3 gap-4 mb-6" data-oid="vwz2e5t">
          <div
            className="text-center p-3 bg-muted/50 rounded-md"
            data-oid="-2ezn87"
          >
            <div
              className="text-2xl font-bold text-blue-600"
              data-oid="rd:pk82"
            >
              {summary.totalModels}
            </div>
            <div className="text-xs text-muted-foreground" data-oid="3mn3_u7">
              Active Models
            </div>
          </div>

          <div
            className="text-center p-3 bg-muted/50 rounded-md"
            data-oid="od7hztj"
          >
            <div
              className="text-2xl font-bold text-green-600"
              data-oid="kpd2od."
            >
              {summary.totalPredictions.toLocaleString()}
            </div>
            <div className="text-xs text-muted-foreground" data-oid="84nxnl9">
              Total Predictions
            </div>
          </div>

          <div
            className="text-center p-3 bg-muted/50 rounded-md"
            data-oid="7my_xd3"
          >
            <div
              className="text-2xl font-bold text-purple-600"
              data-oid="1b9hqc5"
            >
              {summary.avgConfidence.toFixed(1)}%
            </div>
            <div className="text-xs text-muted-foreground" data-oid="b-3sm8z">
              Avg Confidence
            </div>
          </div>
        </div>
      )}

      {/* Chart Area */}
      <div className="h-80" data-oid="mssx2s8">
        {!modelPerformance || modelPerformance.length === 0 ? (
          <div
            className="flex items-center justify-center h-full text-muted-foreground"
            data-oid="9mj_mqz"
          >
            No model performance data available
          </div>
        ) : (
          <ResponsiveContainer width="100%" height="100%" data-oid="tcbuga7">
            {(() => {
              if (chartType === "confidence") {
                return (
                  <BarChart data={confidenceData} data-oid="0g6m8:v">
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="#374151"
                      opacity={0.3}
                      data-oid="zc0li.6"
                    />
                    <XAxis
                      dataKey="name"
                      tick={{ fontSize: 12 }}
                      stroke="#6b7280"
                      angle={-45}
                      textAnchor="end"
                      height={60}
                      data-oid="9cq5pv3"
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
                      data-oid="4d-i:br"
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
                      data-oid="3_dpar9"
                    />

                    <Bar
                      dataKey="avgConfidence"
                      fill="#3b82f6"
                      name="Average Confidence"
                      radius={[4, 4, 0, 0]}
                      data-oid="zy7wlc_"
                    />
                  </BarChart>
                );
              }

              if (chartType === "accuracy" && accuracyData.length > 0) {
                return (
                  <BarChart data={accuracyData.slice(0, 10)} data-oid="2vua4f7">
                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="#374151"
                      opacity={0.3}
                      data-oid="jrr7c_v"
                    />
                    <XAxis
                      dataKey="className"
                      tick={{ fontSize: 12 }}
                      stroke="#6b7280"
                      angle={-45}
                      textAnchor="end"
                      height={80}
                      data-oid="sh1z47w"
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
                      data-oid="9h7qw1p"
                    />

                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1f2937",
                        border: "1px solid #374151",
                        borderRadius: "8px",
                      }}
                      formatter={(value: number) => [`${value.toFixed(1)}%`]}
                      data-oid="b:bg-jc"
                    />

                    <Legend data-oid="15csx5b" />

                    <Bar
                      dataKey="precision"
                      fill="#10b981"
                      name="Precision"
                      data-oid="ac.yz-:"
                    />
                    <Bar
                      dataKey="recall"
                      fill="#f59e0b"
                      name="Recall"
                      data-oid="k77bz48"
                    />
                    <Bar
                      dataKey="f1Score"
                      fill="#8b5cf6"
                      name="F1 Score"
                      data-oid="m7mm-z5"
                    />
                  </BarChart>
                );
              }

              if (chartType === "radar") {
                return (
                  <RadarChart data={radarData} data-oid="3klkz8e">
                    <PolarGrid stroke="#374151" data-oid="js10bcn" />
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
                      data-oid="2z.tsuk"
                    />

                    <PolarRadiusAxis
                      tick={{ fontSize: 10, fill: "#6b7280" }}
                      domain={[0, 100]}
                      tickCount={5}
                      data-oid="cl9f09y"
                    />

                    <Tooltip
                      contentStyle={{
                        backgroundColor: "#1f2937",
                        border: "1px solid #374151",
                        borderRadius: "8px",
                      }}
                      data-oid="v_o5969"
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
                        data-oid="xfhjw8g"
                      />
                    ))}
                    <Legend data-oid="sd9anl9" />
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
        <div className="mt-4 pt-4 border-t" data-oid="pt-ge.f">
          {modelPerformance
            .filter((model) => model.model_type === selectedModel)
            .map((model) => (
              <div
                key={model.model_name}
                className="text-sm"
                data-oid="c_.868c"
              >
                <div
                  className="flex justify-between items-center"
                  data-oid="6cvrv4z"
                >
                  <span className="font-medium" data-oid="-v.v532">
                    {model.model_name}
                  </span>
                  <Badge variant="outline" data-oid="z8h:-ki">
                    {model.total_predictions.toLocaleString()} predictions
                  </Badge>
                </div>
                <div
                  className="text-xs text-muted-foreground mt-1"
                  data-oid="upz.sbv"
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
