import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Play,
  RefreshCw,
  Filter,
  AlertCircle,
  CheckCircle,
  Clock,
  Loader2,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { JobCard } from "@/components/jobs/JobCard";
import { JobLogsModal } from "@/components/jobs/JobLogsModal";
import { StartJobModal } from "@/components/jobs/StartJobModal";
import { useJobs, useJobStats, useJobMonitoring } from "@/hooks/useJobs";
import type { Job } from "@/types/dataset";

export function JobsPage() {
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [kindFilter, setKindFilter] = useState<string>("all");
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [showLogsModal, setShowLogsModal] = useState(false);
  const [showStartJobModal, setShowStartJobModal] = useState(false);

  // Enable real-time monitoring
  const { refreshJobs } = useJobMonitoring(true);
  const navigate = useNavigate();

  const {
    data: jobsPage,
    isLoading,
    error,
  } = useJobs({
    status: statusFilter !== "all" ? statusFilter : undefined,
    kind: kindFilter !== "all" ? kindFilter : undefined,
    page: currentPage,
    limit: 20,
  });

  const { data: jobStats } = useJobStats();

  const jobs = jobsPage?.items || [];
  const totalPages = jobsPage ? Math.ceil(jobsPage.total / jobsPage.limit) : 0;

  const handleViewLogs = (job: Job) => {
    setSelectedJob(job);
    setShowLogsModal(true);
  };

  const handleViewDataset = (job: Job) => {
    console.log("Navigate to dataset:", job.dataset_id);
    // Navigate to datasets page with the specific dataset ID highlighted
    navigate(`/datasets?dataset=${job.dataset_id}`);
  };

  const getStatusStats = () => {
    if (!jobStats) return null;

    return [
      {
        status: "running",
        count: jobStats.running_jobs,
        label: "Running",
        icon: Loader2,
        color: "text-blue-500",
      },
      {
        status: "queued",
        count: jobStats.queued_jobs,
        label: "Queued",
        icon: Clock,
        color: "text-yellow-500",
      },
      {
        status: "succeeded",
        count: jobStats.completed_jobs,
        label: "Completed",
        icon: CheckCircle,
        color: "text-green-500",
      },
      {
        status: "failed",
        count: jobStats.failed_jobs,
        label: "Failed",
        icon: AlertCircle,
        color: "text-red-500",
      },
    ];
  };

  const statusStats = getStatusStats();

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8" data-oid="_is4a:r">
        <div
          className="flex items-center justify-center min-h-[400px]"
          data-oid="m5uqizc"
        >
          {error && (
            <div className="text-center py-8" data-oid="52w8bql">
              <AlertCircle
                className="h-12 w-12 text-destructive mx-auto mb-4"
                data-oid="a_9udz:"
              />
              <p
                className="text-lg font-medium text-destructive mb-2"
                data-oid="abe3iu8"
              >
                Failed to load jobs
              </p>
              <p className="text-muted-foreground" data-oid=".7j3od4">
                {error?.message || "An error occurred while loading jobs"}
              </p>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8" data-oid="ye0:osk">
      {/* Header */}
      <div
        className="flex items-center justify-between mb-8"
        data-oid="xxa3978"
      >
        <div data-oid="ae9e_.8">
          <h1 className="text-3xl font-bold tracking-tight" data-oid="_pu-hpj">
            Processing Jobs
          </h1>
          <p className="text-muted-foreground mt-1" data-oid="m7zao61">
            Monitor and manage dataset processing jobs
          </p>
        </div>

        <div className="flex items-center space-x-2" data-oid="a_uih_c">
          <Button variant="outline" onClick={refreshJobs} data-oid="u_t7tny">
            <RefreshCw className="h-4 w-4 mr-2" data-oid="v0-0pph" />
            Refresh
          </Button>
          <Button onClick={() => setShowStartJobModal(true)} data-oid="3f-whpx">
            <Play className="h-4 w-4 mr-2" data-oid="vzbec0a" />
            Start Job
          </Button>
        </div>
      </div>

      {/* Stats Dashboard */}
      {statusStats && (
        <div
          className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
          data-oid="-5k8ti:"
        >
          {statusStats.map(({ status, count, label, icon: Icon, color }) => (
            <div
              key={status}
              className="bg-card border rounded-lg p-4"
              data-oid="75z_:lk"
            >
              <div className="flex items-center space-x-2" data-oid="hf9e35v">
                <Icon className={`h-5 w-5 ${color}`} data-oid="t..n2w5" />
                <span
                  className="text-sm font-medium text-muted-foreground"
                  data-oid="_51gv3m"
                >
                  {label}
                </span>
              </div>
              <div className="text-2xl font-bold mt-2" data-oid="v0_n_tv">
                {count.toLocaleString()}
              </div>
              {status === "succeeded" && jobStats && (
                <div
                  className="text-xs text-muted-foreground mt-1"
                  data-oid="1y_fxw7"
                >
                  {jobStats.success_rate.toFixed(1)}% success rate
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center space-x-4 mb-6" data-oid="1_yjpk4">
        <div className="flex items-center space-x-2" data-oid="_w:03_w">
          <Filter
            className="h-4 w-4 text-muted-foreground"
            data-oid="s84hy.7"
          />
          <span className="text-sm font-medium" data-oid="qu.6ezv">
            Filters:
          </span>
        </div>

        <Select
          value={statusFilter}
          onValueChange={setStatusFilter}
          data-oid="1q.2vzu"
        >
          <SelectTrigger className="w-40" data-oid="h5h_t6t">
            <SelectValue placeholder="Status" data-oid="l7g3ue_" />
          </SelectTrigger>
          <SelectContent data-oid="1dfk3ev">
            <SelectItem value="all" data-oid="g5ftun2">
              All Status
            </SelectItem>
            <SelectItem value="queued" data-oid="c34145d">
              Queued
            </SelectItem>
            <SelectItem value="running" data-oid="mv3xe_3">
              Running
            </SelectItem>
            <SelectItem value="succeeded" data-oid="li.zxyq">
              Completed
            </SelectItem>
            <SelectItem value="failed" data-oid="nlb5qxu">
              Failed
            </SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={kindFilter}
          onValueChange={setKindFilter}
          data-oid="9jx.0ad"
        >
          <SelectTrigger className="w-40" data-oid="9v25-:.">
            <SelectValue placeholder="Type" data-oid="pbxfiy1" />
          </SelectTrigger>
          <SelectContent data-oid="23d55y5">
            <SelectItem value="all" data-oid="xg6u91b">
              All Types
            </SelectItem>
            <SelectItem value="ingest" data-oid="b_y37pt">
              Data Ingestion
            </SelectItem>
            <SelectItem value="process" data-oid="651-i1f">
              AI Processing
            </SelectItem>
          </SelectContent>
        </Select>

        {jobsPage && (
          <div className="text-sm text-muted-foreground" data-oid="65f5z4y">
            Showing {jobs.length} of {jobsPage.total} job
            {jobsPage.total !== 1 ? "s" : ""}
          </div>
        )}
      </div>

      {/* Jobs List */}
      <div className="space-y-4" data-oid="dy4fu0j">
        {isLoading && (
          <div className="space-y-4" data-oid="rvm8lve">
            {Array.from({ length: 3 }, (_, i) => (
              <div
                key={i}
                className="h-32 bg-muted animate-pulse rounded-lg"
                data-oid="mrdszs2"
              />
            ))}
          </div>
        )}

        {!isLoading && jobs.length === 0 && (
          <div className="text-center py-12" data-oid="1_ric46">
            <Play
              className="mx-auto h-12 w-12 text-muted-foreground mb-4"
              data-oid="jv.zp.j"
            />
            <h3
              className="text-lg font-semibold text-gray-900 mb-2"
              data-oid="yxfjhnh"
            >
              No jobs found
            </h3>
            <p className="text-sm text-gray-500 mb-4" data-oid="p061owc">
              {statusFilter !== "all" || kindFilter !== "all"
                ? "No jobs match your current filters."
                : "Start processing your datasets to see jobs here."}
            </p>
            <Button
              onClick={() => setShowStartJobModal(true)}
              data-oid="2ryvade"
            >
              <Play className="h-4 w-4 mr-2" data-oid="wwbwtmr" />
              Start Your First Job
            </Button>
          </div>
        )}

        {!isLoading &&
          jobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              onViewLogs={handleViewLogs}
              onViewDataset={handleViewDataset}
              data-oid="xbdwvz8"
            />
          ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div
          className="flex items-center justify-between mt-8"
          data-oid="qvo743v"
        >
          <div className="text-sm text-muted-foreground" data-oid="ov:upkc">
            Page {currentPage} of {totalPages}
          </div>

          <div className="flex items-center space-x-2" data-oid="hiq5x9o">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage <= 1 || isLoading}
              data-oid="qng-uzk"
            >
              Previous
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage >= totalPages || isLoading}
              data-oid="9w._8yf"
            >
              Next
            </Button>
          </div>
        </div>
      )}

      {/* Real-time Status Indicator */}
      {statusStats &&
        statusStats.some(
          (s) =>
            s.count > 0 && (s.status === "running" || s.status === "queued"),
        ) && (
          <div className="fixed bottom-4 right-4" data-oid=".r8__j5">
            <Badge
              variant="default"
              className="animate-pulse"
              data-oid="q0_.m5."
            >
              <Loader2
                className="h-3 w-3 mr-1 animate-spin"
                data-oid="-t454gn"
              />
              Jobs Running
            </Badge>
          </div>
        )}

      {/* Modals */}
      <JobLogsModal
        job={selectedJob}
        open={showLogsModal}
        onClose={() => {
          setShowLogsModal(false);
          setSelectedJob(null);
        }}
        data-oid="gv9jr:v"
      />

      <StartJobModal
        open={showStartJobModal}
        onClose={() => setShowStartJobModal(false)}
        data-oid="42uk1z1"
      />
    </div>
  );
}
