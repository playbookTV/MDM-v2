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
        data-oid="6dgdzfe"
      >
        <div className="flex items-center space-x-2 mb-4" data-oid="u2hqlvq">
          <AlertTriangle
            className="h-5 w-5 text-destructive"
            data-oid="gzcewhj"
          />
          <h3 className="text-lg font-semibold" data-oid="534_4ir">
            Review Progress
          </h3>
          <Badge variant="destructive" data-oid="pjrogx0">
            Error
          </Badge>
        </div>
        <p className="text-sm text-muted-foreground" data-oid="n:7:cmc">
          Unable to load review progress
        </p>
      </div>
    );
  }

  if (isLoading || !stats) {
    return (
      <div
        className={`bg-card border rounded-lg p-6 ${className}`}
        data-oid="uj2fgz:"
      >
        <div className="flex items-center space-x-2 mb-4" data-oid="s05.i4j">
          <Target className="h-5 w-5 animate-pulse" data-oid="74qwciu" />
          <h3 className="text-lg font-semibold" data-oid="az1v7f7">
            Review Progress
          </h3>
        </div>
        <div className="space-y-4" data-oid=":--1yq-">
          {Array.from({ length: 4 }, (_, i) => (
            <div key={i} className="space-y-2" data-oid="61cjyta">
              <div
                className="h-4 bg-muted animate-pulse rounded"
                data-oid="g41e8h:"
              />
              <div
                className="h-2 bg-muted animate-pulse rounded"
                data-oid="-t8l-m2"
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
      data-oid="fd.pxya"
    >
      {/* Header */}
      <div className="flex items-center space-x-2 mb-6" data-oid="bzhlq51">
        <Target className="h-5 w-5" data-oid="4s3xtvp" />
        <h3 className="text-lg font-semibold" data-oid="epiqw50">
          Review Progress
        </h3>
        <Badge variant="outline" data-oid="h4as-7t">
          {stats.reviewed_scenes} / {stats.total_scenes} scenes
        </Badge>
      </div>

      {/* Overall Progress Bar */}
      <div className="space-y-2 mb-6" data-oid="d_fnmo.">
        <div className="flex items-center justify-between" data-oid="1wg4kcp">
          <span className="text-sm font-medium" data-oid="sv1uprr">
            Completion Progress
          </span>
          <span className="text-sm text-muted-foreground" data-oid="7vt096e">
            {completionPercentage.toFixed(1)}%
          </span>
        </div>
        <Progress
          value={completionPercentage}
          className="h-3"
          data-oid="01hvpr."
        />
        <div className="text-xs text-muted-foreground" data-oid="1tdmh6k">
          {stats.reviewed_scenes} of {stats.total_scenes} scenes reviewed
        </div>
      </div>

      {/* Review Status Breakdown */}
      <div
        className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6"
        data-oid="tp:4.4l"
      >
        <div
          className="text-center p-3 bg-muted/50 rounded-md"
          data-oid="tn.b_m5"
        >
          <div
            className="flex items-center justify-center mb-2"
            data-oid="si5db._"
          >
            <Clock className="h-4 w-4 text-gray-500" data-oid=".a1byo_" />
          </div>
          <div className="text-xl font-bold text-gray-600" data-oid=":ou.ny.">
            {stats.pending_scenes}
          </div>
          <div className="text-xs text-muted-foreground" data-oid="n64jv43">
            Pending
          </div>
        </div>

        <div
          className="text-center p-3 bg-muted/50 rounded-md"
          data-oid="3ng60jz"
        >
          <div
            className="flex items-center justify-center mb-2"
            data-oid="8q..md-"
          >
            <CheckCircle
              className="h-4 w-4 text-green-500"
              data-oid="l8su1-8"
            />
          </div>
          <div className="text-xl font-bold text-green-600" data-oid="er_rxey">
            {stats.approved_scenes}
          </div>
          <div className="text-xs text-muted-foreground" data-oid="0jq:880">
            Approved
          </div>
        </div>

        <div
          className="text-center p-3 bg-muted/50 rounded-md"
          data-oid="0cvc36m"
        >
          <div
            className="flex items-center justify-center mb-2"
            data-oid="avpq19q"
          >
            <XCircle className="h-4 w-4 text-red-500" data-oid="et0dlxr" />
          </div>
          <div className="text-xl font-bold text-red-600" data-oid="15y_-9n">
            {stats.rejected_scenes}
          </div>
          <div className="text-xs text-muted-foreground" data-oid="1aomj58">
            Rejected
          </div>
        </div>

        <div
          className="text-center p-3 bg-muted/50 rounded-md"
          data-oid="5it2zr3"
        >
          <div
            className="flex items-center justify-center mb-2"
            data-oid="_6g26w:"
          >
            <AlertTriangle
              className="h-4 w-4 text-yellow-500"
              data-oid="t:-il_6"
            />
          </div>
          <div className="text-xl font-bold text-yellow-600" data-oid="7kszl08">
            {stats.corrected_scenes}
          </div>
          <div className="text-xs text-muted-foreground" data-oid="gerr.:a">
            Corrected
          </div>
        </div>
      </div>

      {/* Review Quality Metrics */}
      <div className="space-y-4 mb-6" data-oid="q4obkm7">
        <h4 className="text-sm font-medium" data-oid="z6-l0hb">
          Review Quality
        </h4>

        <div className="space-y-3" data-oid="u73gx-w">
          {/* Approval Rate */}
          <div className="flex items-center justify-between" data-oid="..jxuq8">
            <div className="flex items-center space-x-2" data-oid="jr5tplv">
              <TrendingUp
                className="h-4 w-4 text-green-500"
                data-oid="q82yt9i"
              />
              <span className="text-sm" data-oid="p-64c:1">
                Approval Rate
              </span>
            </div>
            <div className="flex items-center space-x-2" data-oid="0fbihxn">
              <div className="text-sm font-medium" data-oid="kd1y7kz">
                {approvalRate.toFixed(1)}%
              </div>
              <div
                className="w-16 h-2 bg-muted rounded-full overflow-hidden"
                data-oid="3-eyjj_"
              >
                <div
                  className="h-full bg-green-500 transition-all"
                  style={{ width: `${approvalRate}%` }}
                  data-oid="-jt9crv"
                />
              </div>
            </div>
          </div>

          {/* Review Rate */}
          <div className="flex items-center justify-between" data-oid="tbxoymj">
            <div className="flex items-center space-x-2" data-oid="5v2g8l6">
              <Timer className="h-4 w-4 text-blue-500" data-oid="k56iqpk" />
              <span className="text-sm" data-oid="u-6zfq5">
                Review Rate
              </span>
            </div>
            <div className="text-sm font-medium" data-oid="h5_5veo">
              {stats.review_rate.toFixed(1)} scenes/hour
            </div>
          </div>

          {/* Avg Time per Scene */}
          <div className="flex items-center justify-between" data-oid="mq4206p">
            <div className="flex items-center space-x-2" data-oid="1uarbh1">
              <Clock className="h-4 w-4 text-purple-500" data-oid="q7bt_cn" />
              <span className="text-sm" data-oid="p-9wrew">
                Avg Time per Scene
              </span>
            </div>
            <div className="text-sm font-medium" data-oid="fjx8mms">
              {formatTime(stats.avg_time_per_scene)}
            </div>
          </div>
        </div>
      </div>

      {/* Session Info */}
      <div className="pt-4 border-t" data-oid=":zheoon">
        <div
          className="grid grid-cols-2 gap-4 text-xs text-muted-foreground"
          data-oid="ozgv5q0"
        >
          <div className="flex items-center space-x-1" data-oid="3xmnmxc">
            <User className="h-3 w-3" data-oid="dtvse-o" />
            <span data-oid="hvabe2i">
              Reviewer: {reviewerId || "Current User"}
            </span>
          </div>
          <div className="flex items-center space-x-1" data-oid="4lq9a01">
            <Calendar className="h-3 w-3" data-oid="uzpc6d6" />
            <span data-oid="lm_sxy7">Last 24 hours</span>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      {stats.pending_scenes > 0 && (
        <div className="mt-4 pt-4 border-t" data-oid="qhd3kwk">
          <div className="flex items-center justify-between" data-oid="nfk97il">
            <div className="text-sm" data-oid="1::b.v-">
              <span className="font-medium" data-oid="mhz46j0">
                {stats.pending_scenes}
              </span>{" "}
              scenes remaining
            </div>
            <div className="text-xs text-muted-foreground" data-oid="l7ny5ss">
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
          data-oid="ou:-46f"
        >
          <div className="flex items-center space-x-2" data-oid="fzt-u2p">
            <CheckCircle
              className="h-4 w-4 text-green-600"
              data-oid="5n5uefi"
            />
            <span
              className="text-sm font-medium text-green-800"
              data-oid="5oncsk0"
            >
              All scenes reviewed!
            </span>
          </div>
        </div>
      )}
    </div>
  );
}
