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
    <Dialog open={open} onOpenChange={handleClose} data-oid="ayx:_g.">
      <DialogContent className="max-w-lg" data-oid="xnarf3w">
        <DialogHeader data-oid="d9rj280">
          <DialogTitle data-oid="zifv9yc">Start Processing Job</DialogTitle>
          <DialogDescription data-oid="u.5nlj.">
            Configure and launch a dataset processing job.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6" data-oid=":e73vod">
          {/* Dataset Selection */}
          <div className="space-y-2" data-oid="z5nsuj3">
            <Label htmlFor="dataset" data-oid="0:cv.vo">
              Select Dataset *
            </Label>
            <Select
              value={selectedDatasetId}
              onValueChange={setSelectedDatasetId}
              disabled={createJobMutation.isPending}
              data-oid="jhxx6gx"
            >
              <SelectTrigger data-oid="j6vn9di">
                <SelectValue
                  placeholder="Choose a dataset to process"
                  data-oid="2nuh8n:"
                />
              </SelectTrigger>
              <SelectContent data-oid="0u0dmo7">
                {datasets.map((dataset) => (
                  <SelectItem
                    key={dataset.id}
                    value={dataset.id}
                    data-oid="-t10xv_"
                  >
                    <div
                      className="flex items-center justify-between w-full"
                      data-oid="2azss72"
                    >
                      <div data-oid="r7zo9._">
                        <div className="font-medium" data-oid="a16w4wi">
                          {dataset.name}
                        </div>
                        <div
                          className="text-xs text-muted-foreground"
                          data-oid="alk6:6:"
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
              <div className="text-sm text-muted-foreground" data-oid="imf-t3.">
                <Database className="inline h-3 w-3 mr-1" data-oid="fx2dmsv" />
                {selectedDataset.source_url
                  ? "Remote dataset"
                  : "Local dataset"}{" "}
                • Last updated{" "}
                {new Date(selectedDataset.created_at).toLocaleDateString()}
              </div>
            )}
          </div>

          {/* Job Type Selection */}
          <div className="space-y-3" data-oid="emvla14">
            <Label data-oid="ku07j4m">Job Type *</Label>
            <div className="grid gap-3" data-oid="811:ajv">
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
                    data-oid="9vjuawk"
                  >
                    <div
                      className="flex items-start space-x-3"
                      data-oid="k8c33i7"
                    >
                      <div
                        className={`mt-0.5 rounded-full w-4 h-4 border-2 flex items-center justify-center ${
                          jobKind === kind.value
                            ? "border-primary bg-primary"
                            : "border-border"
                        }`}
                        data-oid="bh6q3ha"
                      >
                        {jobKind === kind.value && (
                          <div
                            className="w-2 h-2 rounded-full bg-background"
                            data-oid="7728cts"
                          />
                        )}
                      </div>

                      <div className="flex-1" data-oid="tpdkr4x">
                        <div
                          className="flex items-center space-x-2"
                          data-oid="7cmaf_4"
                        >
                          <span className="font-medium" data-oid="5dt99ef">
                            {kind.label}
                          </span>
                          {isRecommended && (
                            <Badge
                              variant="default"
                              className="text-xs"
                              data-oid="2y_j0m4"
                            >
                              Recommended
                            </Badge>
                          )}
                        </div>
                        <p
                          className="text-sm text-muted-foreground mt-1"
                          data-oid="_f3yatt"
                        >
                          {kind.description}
                        </p>

                        {isRecommended && selectedDataset && (
                          <p
                            className="text-xs text-primary mt-2"
                            data-oid="bv7c82c"
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
          <div className="space-y-3" data-oid="wro03tr">
            <div
              className="flex items-center justify-between"
              data-oid="fh_iunx"
            >
              <Label data-oid="84b9d1m">Advanced Configuration</Label>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowAdvanced(!showAdvanced)}
                data-oid="lf5r4tl"
              >
                <Settings className="h-4 w-4 mr-1" data-oid="_mq0g12" />
                {showAdvanced ? "Hide" : "Show"} Advanced
              </Button>
            </div>

            {showAdvanced && jobKind === "process" && (
              <div
                className="space-y-4 p-4 bg-muted/50 rounded-lg"
                data-oid="cf:btvj"
              >
                <div className="grid grid-cols-2 gap-4" data-oid="nwharee">
                  <div className="space-y-2" data-oid="_r2k3sl">
                    <Label className="text-sm" data-oid="usaowa3">
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
                      data-oid="dxlgug_"
                    >
                      <SelectTrigger data-oid="gacl6ij">
                        <SelectValue data-oid="00fjk5g" />
                      </SelectTrigger>
                      <SelectContent data-oid="1pwixv:">
                        <SelectItem value="0.3" data-oid="cszo8lo">
                          0.3 (Permissive)
                        </SelectItem>
                        <SelectItem value="0.5" data-oid="2jqn4u.">
                          0.5 (Balanced)
                        </SelectItem>
                        <SelectItem value="0.7" data-oid="4lfnveh">
                          0.7 (Conservative)
                        </SelectItem>
                        <SelectItem value="0.9" data-oid="odj3som">
                          0.9 (Strict)
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2" data-oid="b7p6vgt">
                    <Label className="text-sm" data-oid="rjy.o.l">
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
                      data-oid="bv_33.:"
                    >
                      <SelectTrigger data-oid="z5vxoum">
                        <SelectValue data-oid="dquwd34" />
                      </SelectTrigger>
                      <SelectContent data-oid="c7cq7g3">
                        <SelectItem value="0.3" data-oid="z203080">
                          0.3 (Permissive)
                        </SelectItem>
                        <SelectItem value="0.5" data-oid="5l:-yk9">
                          0.5 (Balanced)
                        </SelectItem>
                        <SelectItem value="0.7" data-oid="5fx17t3">
                          0.7 (Conservative)
                        </SelectItem>
                        <SelectItem value="0.9" data-oid=":8xvw4t">
                          0.9 (Strict)
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="flex items-center space-x-2" data-oid="u:h_qqn">
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
                    data-oid="t-xondd"
                  />

                  <Label
                    htmlFor="force-reprocess"
                    className="text-sm"
                    data-oid="aype:i3"
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
              data-oid="9p6m0yx"
            >
              <div className="flex items-center space-x-2" data-oid="n-s9sup">
                <AlertCircle
                  className="h-4 w-4 text-destructive"
                  data-oid="re7lz3l"
                />

                <span className="text-sm text-destructive" data-oid="t81y82u">
                  {createJobMutation.error?.message ||
                    "An error occurred while creating job"}
                </span>
              </div>
            </div>
          )}
        </div>

        <DialogFooter data-oid="7rpwg..">
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={createJobMutation.isPending}
            data-oid="i.tklh9"
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!canSubmit}
            data-oid="e10p0bi"
          >
            {createJobMutation.isPending ? (
              <>
                <Loader2
                  className="h-4 w-4 mr-2 animate-spin"
                  data-oid="62vm9ou"
                />
                Starting Job...
              </>
            ) : (
              <>
                <Play className="h-4 w-4 mr-2" data-oid="7dt9._k" />
                Start {JOB_KINDS.find((k) => k.value === jobKind)?.label}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
