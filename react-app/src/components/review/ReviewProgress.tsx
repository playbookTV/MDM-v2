import {
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Target,
  TrendingUp,
  User,
  Calendar,
  Timer,
} from "lucide-react";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { useReviewStats } from "@/hooks/useReviews";

interface ReviewProgressProps {
  datasetId?: string;
  reviewerId?: string;
  className?: string;
}

export function ReviewProgress({
  datasetId,
  reviewerId,
  className,
}: ReviewProgressProps) {
  const {
    data: stats,
    isLoading,
    error,
  } = useReviewStats({
    dataset_id: datasetId,
    reviewer_id: reviewerId,
    time_range: "24h",
  });

  if (error) {
    return (
      <div
        className={`bg-card border rounded-lg p-6 ${className}`}
        data-oid="00ne36n"
      >
        <div className="flex items-center space-x-2 mb-4" data-oid="32gpknu">
          <AlertTriangle
            className="h-5 w-5 text-destructive"
            data-oid="9vezy8i"
          />

          <h3 className="text-lg font-semibold" data-oid="pry9nce">
            Review Progress
          </h3>
          <Badge variant="destructive" data-oid="jzlteu_">
            Error
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground" data-oid="l9j6i_6">
          Unable to load review progress
        </p>
      </div>
    );
  }

  if (isLoading || !stats) {
    return (
      <div
        className={`bg-card border rounded-lg p-6 ${className}`}
        data-oid="xme4itm"
      >
        <div className="flex items-center space-x-2 mb-4" data-oid="aaspirp">
          <Target className="h-5 w-5 animate-pulse" data-oid="cf0_ako" />
          <h3 className="text-lg font-semibold" data-oid="dydf8bm">
            Review Progress
          </h3>
        </div>
        <div className="space-y-4" data-oid="37.c:vb">
          {Array.from({ length: 4 }, (_, i) => (
            <div key={i} className="space-y-2" data-oid="jxennga">
              <div
                className="h-4 bg-muted animate-pulse rounded"
                data-oid="-zugxo2"
              />

              <div
                className="h-2 bg-muted animate-pulse rounded"
                data-oid="h1halx."
              />
            </div>
          ))}
        </div>
      </div>
    );
  }

  const completionPercentage =
    stats.total_scenes > 0
      ? (stats.reviewed_scenes / stats.total_scenes) * 100
      : 0;

  const approvalRate =
    stats.reviewed_scenes > 0
      ? (stats.approved_scenes / stats.reviewed_scenes) * 100
      : 0;

  const formatTime = (seconds: number) => {
    if (seconds < 60) {
      return `${seconds.toFixed(0)}s`;
    } else if (seconds < 3600) {
      return `${(seconds / 60).toFixed(1)}m`;
    } else {
      return `${(seconds / 3600).toFixed(1)}h`;
    }
  };

  return (
    <div
      className={`bg-card border rounded-lg p-6 ${className}`}
      data-oid="asue_v2"
    >
      {/* Header */}
      <div className="flex items-center space-x-2 mb-6" data-oid="dr:f6qu">
        <Target className="h-5 w-5" data-oid="924yc7h" />
        <h3 className="text-lg font-semibold" data-oid=".bbml4r">
          Review Progress
        </h3>
        <Badge variant="outline" data-oid="lccgf5y">
          {stats.reviewed_scenes} / {stats.total_scenes} scenes
        </Badge>
      </div>

      {/* Overall Progress Bar */}
      <div className="space-y-2 mb-6" data-oid="lv0__6e">
        <div className="flex items-center justify-between" data-oid="0ng:y_t">
          <span className="text-sm font-medium" data-oid="_823ja9">
            Completion Progress
          </span>
          <span className="text-sm text-muted-foreground" data-oid="k72-imy">
            {completionPercentage.toFixed(1)}%
          </span>
        </div>
        <Progress
          value={completionPercentage}
          className="h-3"
          data-oid="zsuqrju"
        />

        <div className="text-xs text-muted-foreground" data-oid="z2._39h">
          {stats.reviewed_scenes} of {stats.total_scenes} scenes reviewed
        </div>
      </div>

      {/* Review Status Breakdown */}
      <div
        className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6"
        data-oid="oyy:lsl"
      >
        <div
          className="text-center p-3 bg-muted/50 rounded-md"
          data-oid="grfe3r8"
        >
          <div
            className="flex items-center justify-center mb-2"
            data-oid="3m8f4gh"
          >
            <Clock className="h-4 w-4 text-gray-500" data-oid="7f1mdoy" />
          </div>
          <div className="text-xl font-bold text-gray-600" data-oid="wh__f:d">
            {stats.pending_scenes}
          </div>
          <div className="text-xs text-muted-foreground" data-oid="wa1i.ca">
            Pending
          </div>
        </div>

        <div
          className="text-center p-3 bg-muted/50 rounded-md"
          data-oid="pe:w1zb"
        >
          <div
            className="flex items-center justify-center mb-2"
            data-oid=":8lsjzb"
          >
            <CheckCircle
              className="h-4 w-4 text-green-500"
              data-oid="6o8o-gj"
            />
          </div>
          <div className="text-xl font-bold text-green-600" data-oid="cyqntub">
            {stats.approved_scenes}
          </div>
          <div className="text-xs text-muted-foreground" data-oid="45xwhsj">
            Approved
          </div>
        </div>

        <div
          className="text-center p-3 bg-muted/50 rounded-md"
          data-oid="8659srf"
        >
          <div
            className="flex items-center justify-center mb-2"
            data-oid="uf5h40:"
          >
            <XCircle className="h-4 w-4 text-red-500" data-oid="l79-u-t" />
          </div>
          <div className="text-xl font-bold text-red-600" data-oid="kvle24u">
            {stats.rejected_scenes}
          </div>
          <div className="text-xs text-muted-foreground" data-oid="ueo7ew_">
            Rejected
          </div>
        </div>

        <div
          className="text-center p-3 bg-muted/50 rounded-md"
          data-oid="q4h4ub1"
        >
          <div
            className="flex items-center justify-center mb-2"
            data-oid="tcw3age"
          >
            <AlertTriangle
              className="h-4 w-4 text-yellow-500"
              data-oid="wkaa5vm"
            />
          </div>
          <div className="text-xl font-bold text-yellow-600" data-oid="95haa2z">
            {stats.corrected_scenes}
          </div>
          <div className="text-xs text-muted-foreground" data-oid="aw8gqaz">
            Corrected
          </div>
        </div>
      </div>

      {/* Review Quality Metrics */}
      <div className="space-y-4 mb-6" data-oid="nnjn007">
        <h4 className="text-sm font-medium" data-oid="vnjkc34">
          Review Quality
        </h4>

        <div className="space-y-3" data-oid="j.0lm1a">
          {/* Approval Rate */}
          <div className="flex items-center justify-between" data-oid="g5upls:">
            <div className="flex items-center space-x-2" data-oid="4rzqeyj">
              <TrendingUp
                className="h-4 w-4 text-green-500"
                data-oid=".:9_qu7"
              />

              <span className="text-sm" data-oid="w_6c7vd">
                Approval Rate
              </span>
            </div>
            <div className="flex items-center space-x-2" data-oid="1eubhd_">
              <div className="text-sm font-medium" data-oid="n6793qo">
                {approvalRate.toFixed(1)}%
              </div>
              <div
                className="w-16 h-2 bg-muted rounded-full overflow-hidden"
                data-oid="yrgdcbd"
              >
                <div
                  className="h-full bg-green-500 transition-all"
                  style={{ width: `${approvalRate}%` }}
                  data-oid="8_2ka:b"
                />
              </div>
            </div>
          </div>

          {/* Review Rate */}
          <div className="flex items-center justify-between" data-oid="-yf2-j5">
            <div className="flex items-center space-x-2" data-oid="2c4v9_5">
              <Timer className="h-4 w-4 text-blue-500" data-oid=".ky6o5." />
              <span className="text-sm" data-oid="n3oornl">
                Review Rate
              </span>
            </div>
            <div className="text-sm font-medium" data-oid="4lwu.0f">
              {stats.review_rate.toFixed(1)} scenes/hour
            </div>
          </div>

          {/* Avg Time per Scene */}
          <div className="flex items-center justify-between" data-oid="tr-7xs5">
            <div className="flex items-center space-x-2" data-oid="m_ys7ac">
              <Clock className="h-4 w-4 text-purple-500" data-oid="j_6jxa9" />
              <span className="text-sm" data-oid="vptpk2s">
                Avg Time per Scene
              </span>
            </div>
            <div className="text-sm font-medium" data-oid="61ep5y3">
              {formatTime(stats.avg_time_per_scene)}
            </div>
          </div>
        </div>
      </div>

      {/* Session Info */}
      <div className="pt-4 border-t" data-oid="_e29otx">
        <div
          className="grid grid-cols-2 gap-4 text-xs text-muted-foreground"
          data-oid="5_p-b.5"
        >
          <div className="flex items-center space-x-1" data-oid="9lx4bs1">
            <User className="h-3 w-3" data-oid="gz.kucb" />
            <span data-oid="xe7dds9">
              Reviewer: {reviewerId || "Current User"}
            </span>
          </div>
          <div className="flex items-center space-x-1" data-oid="1-dd1nf">
            <Calendar className="h-3 w-3" data-oid="_zyysdj" />
            <span data-oid="2r1d0y3">Last 24 hours</span>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      {stats.pending_scenes > 0 && (
        <div className="mt-4 pt-4 border-t" data-oid=".nz5vxu">
          <div className="flex items-center justify-between" data-oid="wynygc2">
            <div className="text-sm" data-oid="c_:oitl">
              <span className="font-medium" data-oid="cd7q935">
                {stats.pending_scenes}
              </span>{" "}
              scenes remaining
            </div>
            <div className="text-xs text-muted-foreground" data-oid="24v-__8">
              Estimated:{" "}
              {formatTime(stats.pending_scenes * stats.avg_time_per_scene)}{" "}
              remaining
            </div>
          </div>
        </div>
      )}

      {/* Completion Message */}
      {completionPercentage === 100 && (
        <div
          className="mt-4 p-3 bg-green-50 border border-green-200 rounded-md"
          data-oid="nfn-lz4"
        >
          <div className="flex items-center space-x-2" data-oid="n1p51y8">
            <CheckCircle
              className="h-4 w-4 text-green-600"
              data-oid="52gth6j"
            />

            <span
              className="text-sm font-medium text-green-800"
              data-oid="dd_-y91"
            >
              All scenes reviewed!
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
