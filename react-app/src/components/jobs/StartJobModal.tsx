import { useState, useEffect } from "react";
import { Play, Settings, Database, AlertCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useDatasets } from "@/hooks/useDatasets";
import { useCreateJob } from "@/hooks/useJobs";
import type { JobCreate, JobConfig, Dataset } from "@/types/dataset";

interface StartJobModalProps {
  open: boolean;
  onClose: () => void;
  preselectedDataset?: Dataset;
}

const JOB_KINDS = [
  {
    value: "ingest" as const,
    label: "Data Ingestion",
    description: "Download and prepare images from HuggingFace datasets",
  },
  {
    value: "process" as const,
    label: "AI Processing",
    description:
      "Run scene analysis, object detection, and AI models on images",
  },
];

const DEFAULT_CONFIG: JobConfig = {
  scene_classifier_threshold: 0.5,
  style_classifier_threshold: 0.35,
  object_detector_threshold: 0.5,
  material_detector_threshold: 0.35,
  force_reprocess: false,
};

export function StartJobModal({
  open,
  onClose,
  preselectedDataset,
}: StartJobModalProps) {
  const [selectedDatasetId, setSelectedDatasetId] = useState<string>("");
  const [jobKind, setJobKind] = useState<"ingest" | "process">("process");
  const [config, setConfig] = useState<JobConfig>(DEFAULT_CONFIG);
  const [showAdvanced, setShowAdvanced] = useState(false);

  const { data: datasetsPage } = useDatasets({ limit: 100 });
  const createJobMutation = useCreateJob();

  const datasets = datasetsPage?.items || [];
  const selectedDataset = datasets.find((d) => d.id === selectedDatasetId);

  // Set preselected dataset when modal opens
  useEffect(() => {
    if (preselectedDataset && open) {
      setSelectedDatasetId(preselectedDataset.id);
    }
  }, [preselectedDataset, open]);

  const handleSubmit = async () => {
    if (!selectedDatasetId) return;

    const jobData: JobCreate = {
      kind: jobKind,
      dataset_id: selectedDatasetId,
      config: showAdvanced ? config : undefined,
    };

    try {
      await createJobMutation.mutateAsync(jobData);
      handleClose();
    } catch (error) {
      // Error handled by mutation
    }
  };

  const handleClose = () => {
    if (createJobMutation.isPending) return;
    onClose();
    resetForm();
  };

  const resetForm = () => {
    setSelectedDatasetId(preselectedDataset?.id || "");
    setJobKind("process");
    setConfig(DEFAULT_CONFIG);
    setShowAdvanced(false);
  };

  const canSubmit = selectedDatasetId && !createJobMutation.isPending;

  const getJobKindRecommendation = (dataset: Dataset) => {
    if (dataset.source_url) {
      return {
        recommended: "ingest" as const,
        reason: "HuggingFace dataset requires ingestion first",
      };
    }
    return {
      recommended: "process" as const,
      reason: "Local dataset ready for AI processing",
    };
  };

  return (
    <Dialog open={open} onOpenChange={handleClose} data-oid="po.tta7">
      <DialogContent className="max-w-lg" data-oid="q70t1:4">
        <DialogHeader data-oid="y9u5jo3">
          <DialogTitle data-oid="ltv-8:m">Start Processing Job</DialogTitle>
          <DialogDescription data-oid="do5-uxf">
            Configure and launch a dataset processing job.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6" data-oid="o2x6w62">
          {/* Dataset Selection */}
          <div className="space-y-2" data-oid="0.hm9cd">
            <Label htmlFor="dataset" data-oid="805ypxw">
              Select Dataset *
            </Label>
            <Select
              value={selectedDatasetId}
              onValueChange={setSelectedDatasetId}
              disabled={createJobMutation.isPending}
              data-oid="6pdjqu9"
            >
              <SelectTrigger data-oid="gbfvia-">
                <SelectValue
                  placeholder="Choose a dataset to process"
                  data-oid="_:5:byf"
                />
              </SelectTrigger>
              <SelectContent data-oid="kd.d6fs">
                {datasets.map((dataset) => (
                  <SelectItem
                    key={dataset.id}
                    value={dataset.id}
                    data-oid="01ucb3m"
                  >
                    <div
                      className="flex items-center justify-between w-full"
                      data-oid="wcgzbgs"
                    >
                      <div data-oid="bbvh6yj">
                        <div className="font-medium" data-oid="lcfpo94">
                          {dataset.name}
                        </div>
                        <div
                          className="text-xs text-muted-foreground"
                          data-oid="jdzy9z0"
                        >
                          {dataset.source_url ? "HuggingFace" : "Local"} •{" "}
                          {dataset.version}
                        </div>
                      </div>
                    </div>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {selectedDataset && (
              <div className="text-sm text-muted-foreground" data-oid="kv8nr18">
                <Database className="inline h-3 w-3 mr-1" data-oid="xfbc0xu" />
                {selectedDataset.source_url
                  ? "Remote dataset"
                  : "Local dataset"}{" "}
                • Last updated{" "}
                {new Date(selectedDataset.created_at).toLocaleDateString()}
              </div>
            )}
          </div>

          {/* Job Type Selection */}
          <div className="space-y-3" data-oid="m0.i3h.">
            <Label data-oid="ao6_f4i">Job Type *</Label>
            <div className="grid gap-3" data-oid="04-7i69">
              {JOB_KINDS.map((kind) => {
                const isRecommended =
                  selectedDataset &&
                  getJobKindRecommendation(selectedDataset).recommended ===
                    kind.value;

                return (
                  <div
                    key={kind.value}
                    className={`relative rounded-lg border p-4 cursor-pointer transition-colors ${
                      jobKind === kind.value
                        ? "border-primary bg-primary/5"
                        : "border-border hover:bg-muted/50"
                    }`}
                    onClick={() => setJobKind(kind.value)}
                    data-oid=":954kvu"
                  >
                    <div
                      className="flex items-start space-x-3"
                      data-oid="rx1njue"
                    >
                      <div
                        className={`mt-0.5 rounded-full w-4 h-4 border-2 flex items-center justify-center ${
                          jobKind === kind.value
                            ? "border-primary bg-primary"
                            : "border-border"
                        }`}
                        data-oid="75h6hq-"
                      >
                        {jobKind === kind.value && (
                          <div
                            className="w-2 h-2 rounded-full bg-background"
                            data-oid="krm-op-"
                          />
                        )}
                      </div>

                      <div className="flex-1" data-oid="ztr75zh">
                        <div
                          className="flex items-center space-x-2"
                          data-oid="n_btxlk"
                        >
                          <span className="font-medium" data-oid="se2402t">
                            {kind.label}
                          </span>
                          {isRecommended && (
                            <Badge
                              variant="default"
                              className="text-xs"
                              data-oid="kxy3xyc"
                            >
                              Recommended
                            </Badge>
                          )}
                        </div>
                        <p
                          className="text-sm text-muted-foreground mt-1"
                          data-oid="9qo9dfo"
                        >
                          {kind.description}
                        </p>

                        {isRecommended && selectedDataset && (
                          <p
                            className="text-xs text-primary mt-2"
                            data-oid="357xj25"
                          >
                            {getJobKindRecommendation(selectedDataset).reason}
                          </p>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Advanced Configuration */}
          <div className="space-y-3" data-oid="x2nf1uz">
            <div
              className="flex items-center justify-between"
              data-oid="tmwr40j"
            >
              <Label data-oid="y4kcrai">Advanced Configuration</Label>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowAdvanced(!showAdvanced)}
                data-oid="ngvnlwo"
              >
                <Settings className="h-4 w-4 mr-1" data-oid="m:1x1wy" />
                {showAdvanced ? "Hide" : "Show"} Advanced
              </Button>
            </div>

            {showAdvanced && jobKind === "process" && (
              <div
                className="space-y-4 p-4 bg-muted/50 rounded-lg"
                data-oid="wg83-6e"
              >
                <div className="grid grid-cols-2 gap-4" data-oid="u200rcz">
                  <div className="space-y-2" data-oid="t4jo_yh">
                    <Label className="text-sm" data-oid="4byeb_c">
                      Scene Classifier Threshold
                    </Label>
                    <Select
                      value={config.scene_classifier_threshold?.toString()}
                      onValueChange={(value) =>
                        setConfig((prev) => ({
                          ...prev,
                          scene_classifier_threshold: parseFloat(value),
                        }))
                      }
                      data-oid="fp0aruo"
                    >
                      <SelectTrigger data-oid="s:xtf1h">
                        <SelectValue data-oid="6ueaosp" />
                      </SelectTrigger>
                      <SelectContent data-oid="ge7q4xj">
                        <SelectItem value="0.3" data-oid="fmrlg-v">
                          0.3 (Permissive)
                        </SelectItem>
                        <SelectItem value="0.5" data-oid="ex62rwp">
                          0.5 (Balanced)
                        </SelectItem>
                        <SelectItem value="0.7" data-oid="x2yvu81">
                          0.7 (Conservative)
                        </SelectItem>
                        <SelectItem value="0.9" data-oid="hgzdgt8">
                          0.9 (Strict)
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2" data-oid="4nc104p">
                    <Label className="text-sm" data-oid="hvg8hql">
                      Object Detector Threshold
                    </Label>
                    <Select
                      value={config.object_detector_threshold?.toString()}
                      onValueChange={(value) =>
                        setConfig((prev) => ({
                          ...prev,
                          object_detector_threshold: parseFloat(value),
                        }))
                      }
                      data-oid="3wj2:ku"
                    >
                      <SelectTrigger data-oid="la2578x">
                        <SelectValue data-oid="f2spg8r" />
                      </SelectTrigger>
                      <SelectContent data-oid="iabsfe4">
                        <SelectItem value="0.3" data-oid="ubt8pjz">
                          0.3 (Permissive)
                        </SelectItem>
                        <SelectItem value="0.5" data-oid="l4q:vgi">
                          0.5 (Balanced)
                        </SelectItem>
                        <SelectItem value="0.7" data-oid="3vc6qih">
                          0.7 (Conservative)
                        </SelectItem>
                        <SelectItem value="0.9" data-oid="danjl07">
                          0.9 (Strict)
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="flex items-center space-x-2" data-oid="9bud-sl">
                  <input
                    type="checkbox"
                    id="force-reprocess"
                    checked={config.force_reprocess}
                    onChange={(e) =>
                      setConfig((prev) => ({
                        ...prev,
                        force_reprocess: e.target.checked,
                      }))
                    }
                    className="rounded border-border"
                    data-oid=":-xx489"
                  />

                  <Label
                    htmlFor="force-reprocess"
                    className="text-sm"
                    data-oid=".c.fs.u"
                  >
                    Force reprocess (override existing results)
                  </Label>
                </div>
              </div>
            )}
          </div>

          {/* Error Display */}
          {createJobMutation.error && (
            <div
              className="bg-destructive/10 border border-destructive/20 rounded-md p-3"
              data-oid=":ztrm.5"
            >
              <div className="flex items-center space-x-2" data-oid="_nqgw0w">
                <AlertCircle
                  className="h-4 w-4 text-destructive"
                  data-oid="y5scain"
                />
                <span className="text-sm text-destructive" data-oid="knr3w20">
                  {createJobMutation.error?.message ||
                    "An error occurred while creating job"}
                </span>
              </div>
            </div>
          )}
        </div>

        <DialogFooter data-oid="gym9f6p">
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={createJobMutation.isPending}
            data-oid="v6lsz._"
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!canSubmit}
            data-oid="3g6nx0e"
          >
            {createJobMutation.isPending ? (
              <>
                <Loader2
                  className="h-4 w-4 mr-2 animate-spin"
                  data-oid="_ndbgqi"
                />
                Starting Job...
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" data-oid="a66ukpb" />
                Start {JOB_KINDS.find((k) => k.value === jobKind)?.label}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
