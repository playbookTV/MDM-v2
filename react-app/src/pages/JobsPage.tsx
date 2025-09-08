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
      <div className="container mx-auto px-4 py-8" data-oid="yhupvmx">
        <div
          className="flex items-center justify-center min-h-[400px]"
          data-oid="6ipksl4"
        >
          {error && (
            <div className="text-center py-8" data-oid="a3u-7w9">
              <AlertCircle
                className="h-12 w-12 text-destructive mx-auto mb-4"
                data-oid="p-pqvjx"
              />

              <p
                className="text-lg font-medium text-destructive mb-2"
                data-oid="--fxnhw"
              >
                Failed to load jobs
              </p>
              <p className="text-muted-foreground" data-oid="q6jjzk9">
                {error?.message || "An error occurred while loading jobs"}
              </p>
            </div>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8" data-oid="1_j4rym">
      {/* Header */}
      <div
        className="flex items-center justify-between mb-8"
        data-oid="pxnyiqs"
      >
        <div data-oid="swjo8aa">
          <h1 className="text-3xl font-bold tracking-tight" data-oid="7.tomrd">
            Processing Jobs
          </h1>
          <p className="text-muted-foreground mt-1" data-oid=":sc7wi5">
            Monitor and manage dataset processing jobs
          </p>
        </div>

        <div className="flex items-center space-x-2" data-oid=":xeg-_k">
          <Button variant="outline" onClick={refreshJobs} data-oid="i-2l5e1">
            <RefreshCw className="h-4 w-4 mr-2" data-oid="6ujquz7" />
            Refresh
          </Button>
          <Button onClick={() => setShowStartJobModal(true)} data-oid="z_lmbp-">
            <Play className="h-4 w-4 mr-2" data-oid="m-:at.7" />
            Start Job
          </Button>
        </div>
      </div>

      {/* Stats Dashboard */}
      {statusStats && (
        <div
          className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8"
          data-oid="07fc6--"
        >
          {statusStats.map(({ status, count, label, icon: Icon, color }) => (
            <div
              key={status}
              className="bg-card border rounded-lg p-4"
              data-oid="z3l:2u:"
            >
              <div className="flex items-center space-x-2" data-oid="z45t36z">
                <Icon className={`h-5 w-5 ${color}`} data-oid="2sur89x" />
                <span
                  className="text-sm font-medium text-muted-foreground"
                  data-oid="vr69o75"
                >
                  {label}
                </span>
              </div>
              <div className="text-2xl font-bold mt-2" data-oid="9bjipju">
                {count.toLocaleString()}
              </div>
              {status === "succeeded" && jobStats && (
                <div
                  className="text-xs text-muted-foreground mt-1"
                  data-oid="xtx0yk1"
                >
                  {jobStats.success_rate.toFixed(1)}% success rate
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="flex items-center space-x-4 mb-6" data-oid="6m-qzsn">
        <div className="flex items-center space-x-2" data-oid="e70yjon">
          <Filter
            className="h-4 w-4 text-muted-foreground"
            data-oid="433l266"
          />

          <span className="text-sm font-medium" data-oid="9u2.oxx">
            Filters:
          </span>
        </div>

        <Select
          value={statusFilter}
          onValueChange={setStatusFilter}
          data-oid="1xa-:sb"
        >
          <SelectTrigger className="w-40" data-oid="e3e3z3i">
            <SelectValue placeholder="Status" data-oid="s1ra699" />
          </SelectTrigger>
          <SelectContent data-oid="8kgzwqq">
            <SelectItem value="all" data-oid="drpw942">
              All Status
            </SelectItem>
            <SelectItem value="queued" data-oid="4k5:veq">
              Queued
            </SelectItem>
            <SelectItem value="running" data-oid="h5_6d8i">
              Running
            </SelectItem>
            <SelectItem value="succeeded" data-oid="xd:2v15">
              Completed
            </SelectItem>
            <SelectItem value="failed" data-oid="h.dg1f_">
              Failed
            </SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={kindFilter}
          onValueChange={setKindFilter}
          data-oid="iz4wfia"
        >
          <SelectTrigger className="w-40" data-oid="m.7-x0f">
            <SelectValue placeholder="Type" data-oid="8j87j7p" />
          </SelectTrigger>
          <SelectContent data-oid=".-wg2y7">
            <SelectItem value="all" data-oid="f19_u69">
              All Types
            </SelectItem>
            <SelectItem value="ingest" data-oid="wau3qrq">
              Data Ingestion
            </SelectItem>
            <SelectItem value="process" data-oid="sqxrpw7">
              AI Processing
            </SelectItem>
          </SelectContent>
        </Select>

        {jobsPage && (
          <div className="text-sm text-muted-foreground" data-oid="-8dc86a">
            Showing {jobs.length} of {jobsPage.total} job
            {jobsPage.total !== 1 ? "s" : ""}
          </div>
        )}
      </div>

      {/* Jobs List */}
      <div className="space-y-4" data-oid="s:fjmo6">
        {isLoading && (
          <div className="space-y-4" data-oid="j7ywj.1">
            {Array.from({ length: 3 }, (_, i) => (
              <div
                key={i}
                className="h-32 bg-muted animate-pulse rounded-lg"
                data-oid=":_18scz"
              />
            ))}
          </div>
        )}

        {!isLoading && jobs.length === 0 && (
          <div className="text-center py-12" data-oid="bou22zw">
            <Play
              className="mx-auto h-12 w-12 text-muted-foreground mb-4"
              data-oid="00e:0g3"
            />

            <h3
              className="text-lg font-semibold text-gray-900 mb-2"
              data-oid="km:tty1"
            >
              No jobs found
            </h3>
            <p className="text-sm text-gray-500 mb-4" data-oid="1eadtps">
              {statusFilter !== "all" || kindFilter !== "all"
                ? "No jobs match your current filters."
                : "Start processing your datasets to see jobs here."}
            </p>
            <Button
              onClick={() => setShowStartJobModal(true)}
              data-oid="i-q_gfm"
            >
              <Play className="h-4 w-4 mr-2" data-oid="m6py1y3" />
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
              data-oid="d_:kc8m"
            />
          ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div
          className="flex items-center justify-between mt-8"
          data-oid="s369n2k"
        >
          <div className="text-sm text-muted-foreground" data-oid="mpjswhx">
            Page {currentPage} of {totalPages}
          </div>

          <div className="flex items-center space-x-2" data-oid="x-83q5z">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage <= 1 || isLoading}
              data-oid="fg22.69"
            >
              Previous
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={currentPage >= totalPages || isLoading}
              data-oid="-kzh27x"
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
          <div className="fixed bottom-4 right-4" data-oid="19_nwb8">
            <Badge
              variant="default"
              className="animate-pulse"
              data-oid="6_u1s0l"
            >
              <Loader2
                className="h-3 w-3 mr-1 animate-spin"
                data-oid="4f0bctg"
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
        data-oid="earm385"
      />

      <StartJobModal
        open={showStartJobModal}
        onClose={() => setShowStartJobModal(false)}
        data-oid="yf5h570"
      />
    </div>
  );
}
