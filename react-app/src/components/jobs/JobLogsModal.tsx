import { useState, useRef, useEffect } from "react";
import {
  Download,
  Trash2,
  Search,
  ChevronDown,
  Bug,
  Info,
  AlertTriangle,
  XCircle,
  Loader2,
  Eye,
  EyeOff,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useJobLogsStream } from "@/hooks/useJobLogs";
import type { Job, JobLogEntry } from "@/types/dataset";

interface JobLogsModalProps {
  job: Job | null;
  open: boolean;
  onClose: () => void;
}

const LOG_LEVEL_CONFIG = {
  DEBUG: {
    icon: Bug,
    color: "text-gray-500",
    bg: "bg-gray-50",
    badge: "outline" as const,
    label: "Debug",
  },
  INFO: {
    icon: Info,
    color: "text-blue-500",
    bg: "bg-blue-50",
    badge: "default" as const,
    label: "Info",
  },
  WARNING: {
    icon: AlertTriangle,
    color: "text-yellow-500",
    bg: "bg-yellow-50",
    badge: "secondary" as const,
    label: "Warning",
  },
  ERROR: {
    icon: XCircle,
    color: "text-red-500",
    bg: "bg-red-50",
    badge: "destructive" as const,
    label: "Error",
  },
};

export function JobLogsModal({ job, open, onClose }: JobLogsModalProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [levelFilter, setLevelFilter] = useState<string[]>([]);
  const [autoScroll, setAutoScroll] = useState(true);
  const [showContext, setShowContext] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);

  const {
    logs,
    isLoading,
    error,
    clearLogs,
    downloadLogs,
    getLogStats,
    hasNewLogs,
  } = useJobLogsStream(job?.id || "", {
    maxLogs: 1000,
    autoScroll,
    levelFilter: levelFilter.length > 0 ? levelFilter : undefined,
  });

  // Scroll to bottom when new logs arrive (if auto-scroll is enabled)
  useEffect(() => {
    if (autoScroll && hasNewLogs && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [hasNewLogs, autoScroll]);

  const filteredLogs = logs.filter((log) => {
    if (searchQuery) {
      return log.message.toLowerCase().includes(searchQuery.toLowerCase());
    }
    return true;
  });

  const logStats = getLogStats();

  const handleLevelFilterChange = (level: string) => {
    setLevelFilter((prev) => {
      if (prev.includes(level)) {
        return prev.filter((l) => l !== level);
      } else {
        return [...prev, level];
      }
    });
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  const renderLogEntry = (log: JobLogEntry, index: number) => {
    const config = LOG_LEVEL_CONFIG[log.level];
    const Icon = config.icon;

    return (
      <div
        key={`${log.timestamp}-${index}`}
        className={`flex items-start space-x-3 p-3 rounded-md border-l-2 border-l-${config.color.split("-")[1]}-500 ${config.bg}`}
        data-oid="a1ovc5w"
      >
        <Icon
          className={`h-4 w-4 mt-0.5 ${config.color} flex-shrink-0`}
          data-oid="azg69f8"
        />

        <div className="flex-1 min-w-0 space-y-1" data-oid="x11j-.f">
          <div className="flex items-center space-x-2" data-oid="ucfuy1_">
            <Badge
              variant={config.badge}
              className="text-xs"
              data-oid="mm1_9e3"
            >
              {config.label}
            </Badge>
            <span
              className="text-xs text-muted-foreground font-mono"
              data-oid="bc_nibe"
            >
              {formatTimestamp(log.timestamp)}
            </span>
          </div>

          <p
            className="text-sm font-mono break-words leading-relaxed"
            data-oid="7c3pc._"
          >
            {log.message}
          </p>

          {showContext &&
            log.context &&
            Object.keys(log.context).length > 0 && (
              <details className="mt-2" data-oid="j7rs9yn">
                <summary
                  className="text-xs text-muted-foreground cursor-pointer hover:text-foreground"
                  data-oid="83d.zck"
                >
                  Context ({Object.keys(log.context).length} fields)
                </summary>
                <pre
                  className="text-xs bg-muted p-2 rounded mt-1 overflow-x-auto"
                  data-oid="5mp:pi7"
                >
                  {JSON.stringify(log.context, null, 2)}
                </pre>
              </details>
            )}
        </div>
      </div>
    );
  };

  if (!job) return null;

  return (
    <Dialog open={open} onOpenChange={onClose} data-oid="46wps_0">
      <DialogContent
        className="max-w-5xl max-h-[80vh] flex flex-col"
        data-oid="5w9x98g"
      >
        <DialogHeader className="flex-shrink-0" data-oid="yuw9g8s">
          <DialogTitle data-oid="mmfrpgg">
            Job Logs - {job.dataset_name || job.dataset_id}
          </DialogTitle>
          <DialogDescription data-oid="lvah08a">
            Real-time logs for job #{job.id.slice(-8)} • {logs.length} entries
          </DialogDescription>
        </DialogHeader>

        {/* Controls Bar */}
        <div
          className="flex-shrink-0 flex items-center justify-between gap-4 py-3 border-b"
          data-oid="x48zw9y"
        >
          {/* Search */}
          <div className="relative flex-1 max-w-sm" data-oid="jxnnfvq">
            <Search
              className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground"
              data-oid="48orcar"
            />

            <Input
              placeholder="Search logs..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9"
              data-oid="he_-7sn"
            />
          </div>

          {/* Level Filter */}
          <div className="flex items-center space-x-2" data-oid=":g18ado">
            {Object.entries(LOG_LEVEL_CONFIG).map(([level, config]) => (
              <Button
                key={level}
                variant={levelFilter.includes(level) ? "default" : "outline"}
                size="sm"
                onClick={() => handleLevelFilterChange(level)}
                className="text-xs"
                data-oid="0t5nm4o"
              >
                <config.icon className="h-3 w-3 mr-1" data-oid="o:lnct2" />
                {config.label} (
                {logStats[level.toLowerCase() as keyof typeof logStats]})
              </Button>
            ))}
          </div>

          {/* Actions */}
          <div className="flex items-center space-x-2" data-oid="zz8fbit">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowContext(!showContext)}
              data-oid="reg6:rd"
            >
              {showContext ? (
                <EyeOff className="h-4 w-4" data-oid="v6lp8ou" />
              ) : (
                <Eye className="h-4 w-4" data-oid="i1emu89" />
              )}
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setAutoScroll(!autoScroll)}
              data-oid="rano5po"
            >
              <ChevronDown
                className={`h-4 w-4 ${autoScroll ? "text-green-500" : ""}`}
                data-oid="ux0nit-"
              />
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={downloadLogs}
              disabled={logs.length === 0}
              data-oid="5vfg.h6"
            >
              <Download className="h-4 w-4" data-oid="yvwnkrb" />
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={clearLogs}
              disabled={logs.length === 0}
              data-oid="fx9csdz"
            >
              <Trash2 className="h-4 w-4" data-oid="hpyok6e" />
            </Button>
          </div>
        </div>

        {/* Logs Content */}
        <div
          className="flex-1 overflow-y-auto space-y-2 p-1"
          data-logs-container
          data-oid="bn7-u4o"
        >
          {isLoading && logs.length === 0 && (
            <div
              className="flex items-center justify-center py-8"
              data-oid="0ixrd60"
            >
              <Loader2
                className="h-6 w-6 animate-spin mr-2"
                data-oid="ob9jck-"
              />

              <span className="text-muted-foreground" data-oid="lu-y9vo">
                Loading logs...
              </span>
            </div>
          )}

          {error && (
            <div
              className="bg-destructive/10 border border-destructive/20 rounded-md p-4"
              data-oid="p-4ub-n"
            >
              <div className="flex items-center space-x-2" data-oid="ailp2id">
                <XCircle
                  className="h-4 w-4 text-destructive"
                  data-oid="385tdwb"
                />

                <span
                  className="text-destructive font-medium"
                  data-oid="xhifvqw"
                >
                  Failed to load logs
                </span>
              </div>
              <p
                className="text-sm text-destructive/80 mt-1"
                data-oid="nmc6:dd"
              >
                {(error as Error)?.message || "An error occurred"}
              </p>
            </div>
          )}

          {!isLoading && !error && logs.length === 0 && (
            <div
              className="text-center py-8 text-muted-foreground"
              data-oid="-5wmlm0"
            >
              <Info className="h-8 w-8 mx-auto mb-2" data-oid="q6.ff5z" />
              <p data-oid="kstemz_">No logs available for this job</p>
            </div>
          )}

          {!isLoading &&
            !error &&
            filteredLogs.length === 0 &&
            logs.length > 0 && (
              <div
                className="text-center py-8 text-muted-foreground"
                data-oid="r7ohmeb"
              >
                <Search className="h-8 w-8 mx-auto mb-2" data-oid="8yb1dm-" />
                <p data-oid="3978_cx">No logs match your search criteria</p>
              </div>
            )}

          {filteredLogs.map(renderLogEntry)}

          <div ref={logsEndRef} data-oid="adh9p4u" />
        </div>

        {/* Status Bar */}
        <div
          className="flex-shrink-0 flex items-center justify-between text-xs text-muted-foreground py-2 border-t"
          data-oid="h:sflkj"
        >
          <div className="flex items-center space-x-4" data-oid="u6xevqp">
            <span data-oid=".khrok.">
              {filteredLogs.length} of {logs.length} logs shown
            </span>
            {searchQuery && (
              <Badge variant="outline" data-oid="br230xq">
                Searching: {searchQuery}
              </Badge>
            )}
            {levelFilter.length > 0 && (
              <Badge variant="outline" data-oid="1jzlw32">
                Filtered: {levelFilter.join(", ")}
              </Badge>
            )}
          </div>

          <div className="flex items-center space-x-2" data-oid="jpm6_n.">
            {autoScroll && (
              <Badge variant="outline" data-oid="k_ld8c8">
                Auto-scroll ON
              </Badge>
            )}
            {hasNewLogs && (
              <Badge variant="default" data-oid="sb9udwk">
                New logs available
              </Badge>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
